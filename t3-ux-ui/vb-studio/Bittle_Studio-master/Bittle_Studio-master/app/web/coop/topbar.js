// Top bar: scenario name and menu, run / pause / reset / speed, the mission button and the status read-out.
import { $, h, clear, toast, withBusy, fixed } from './ui.js';
import { get, post, put } from './api.js';
import { store, on, changeModel, acceptState } from './store.js';

const NAME_PATTERN = /^[A-Za-z0-9 _-]{1,60}$/;
const WARN_AFTER_MS = 2500;  // the measured speed needs a moment to settle after Run

let runningSince = 0;

async function command(body) {
  try {
    acceptState(await post('/api/coop/command', body));
  } catch (error) {
    toast(error.message, true);
  }
}

/** True while a mission runs: the behaviour is in any state but off (manual control) and flat (battery empty). */
export const missionRunning = state => !['off', 'flat'].includes(state.behaviour.state);

/** Start the mission (which also starts the physics), or stop it when it runs. */
export const toggleMission = () => command({ action: 'mission', value: !(store.state && missionRunning(store.state)) });

/** Run a menu action; failures show up as a toast. */
async function act(button, task) {
  try {
    await withBusy(button, task);
  } catch (error) {
    toast(error.message, true);
  }
}

export function downloadFile(filename, text, type = 'application/json') {
  const link = h('a', { href: URL.createObjectURL(new Blob([text], { type })), download: filename });
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

function initMenu() {
  const menu = $('#scenarioMenu');
  const list = $('#scenarioList');
  const saveName = $('#saveName');
  const fileInput = $('#openFile');
  const close = () => { menu.open = false; };

  function showList(scenarios) {
    clear(list, scenarios.length ? scenarios.map(item => h('li', null,
      h('button', {
        type: 'button', class: 'link',
        onclick: event => act(event.currentTarget, async () => {
          await changeModel(() => post('/api/coop/scenarios/load', { name: item.file }));
          toast(`Loaded "${item.name}"`);
          close();
        }),
      }, item.name),
      item.name === item.file ? null : h('small', { text: item.file + '.json' }))) : h('li', { class: 'muted', text: 'No saved scenarios yet.' }));
  }

  async function refresh() {
    try {
      showList(await get('/api/coop/scenarios'));
    } catch (error) {
      clear(list, h('li', { class: 'error-text', text: error.message }));
    }
  }

  menu.addEventListener('toggle', () => { if (menu.open) refresh(); });
  document.addEventListener('click', event => { if (menu.open && !menu.contains(event.target)) close(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && menu.open) { close(); menu.querySelector('summary').focus(); } });

  $('#saveButton').addEventListener('click', event => act(event.currentTarget, async () => {
    const name = saveName.value.trim();
    if (!NAME_PATTERN.test(name)) throw new Error('Scenario names may use letters, digits, spaces, - and _ (up to 60 characters)');
    const result = await post('/api/coop/scenarios/save', { name });
    showList(result.scenarios);
    saveName.value = '';
    toast(`Saved as "${result.saved.file}"`);
  }));

  $('#newButton').addEventListener('click', event => act(event.currentTarget, async () => {
    await changeModel(async () => put('/api/coop/scenario', await get('/api/coop/default-scenario')));
    toast('New scenario with the default settings');
    close();
  }));

  $('#downloadButton').addEventListener('click', event => act(event.currentTarget, async () => {
    const scenario = await get('/api/coop/scenario');
    const base = scenario.name.replace(/[^A-Za-z0-9 _-]+/g, '').trim() || 'scenario';
    downloadFile(base.replace(/\s+/g, '-') + '.json', JSON.stringify(scenario, null, 2));
    close();
  }));

  $('#openButton').addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', async () => {
    const file = fileInput.files[0];
    fileInput.value = '';
    if (!file) return;
    try {
      let scenario;
      try {
        scenario = JSON.parse(await file.text());
      } catch (error) {
        throw new Error(`${file.name} is not a JSON file`);
      }
      await changeModel(() => put('/api/coop/scenario', scenario));
      toast(`Opened ${file.name}`);
      close();
    } catch (error) {
      toast(error.message, true);
    }
  });
}

function speedLabel(value) {
  return value === 0 ? 'Max' : value + '×';
}

export function initTopbar() {
  const nameInput = $('#scenarioName');
  const speedSelect = $('#speedSelect');
  const runButton = $('#runButton');
  const missionButton = $('#missionButton');

  nameInput.addEventListener('input', () => { store.draftName = nameInput.value.trim() || null; });
  runButton.addEventListener('click', () => command({ action: 'run', value: !(store.state && store.state.running) }));
  missionButton.addEventListener('click', () => toggleMission());
  $('#resetButton').addEventListener('click', () => command({ action: 'reset' }));
  speedSelect.addEventListener('change', () => command({ action: 'speed', value: Number(speedSelect.value) }));
  initMenu();

  on('model', () => {
    const model = store.model;
    nameInput.value = model.scenario.name;
    store.draftName = null;
    clear(speedSelect, model.speeds.map(value => h('option', { value: String(value), text: speedLabel(value) })));
    speedSelect.value = String(model.scenario.simulation.speed);
  });

  on('state', state => {
    $('#statusTime').textContent = fixed(state.time, 2) + ' s';
    runButton.textContent = state.running ? '❚❚ Pause' : '▶ Run';
    const mission = missionRunning(state), flat = state.behaviour.state === 'flat';
    missionButton.textContent = mission ? '■ Stop mission' : '▶ Mission';
    missionButton.classList.toggle('on', mission);
    missionButton.disabled = flat;
    missionButton.title = flat ? 'The battery is empty: press Reset to start again with a charged battery'
      : mission ? 'Stop the mission: the robot waits for your commands'
        : 'Start the mission: the robot patrols, watches for the fox and charges at the dock (also starts the physics)';
    if (document.activeElement !== speedSelect && speedSelect.value !== String(state.speed)) speedSelect.value = String(state.speed);

    runningSince = state.running ? runningSince || performance.now() : 0;
    const speed = $('#statusSpeed');
    const slow = state.running && state.speed > 0 && performance.now() - runningSince > WARN_AFTER_MS
      && state.measured_speed < .9 * state.speed;
    speed.textContent = state.running ? `${fixed(state.measured_speed, 1)}× real time` : 'Paused';
    speed.classList.toggle('warn', slow);
    speed.title = slow ? `Slower than the chosen ${speedLabel(state.speed)}: this computer cannot keep up. Choose a lower speed.`
      : `Measured over the last second; chosen speed ${speedLabel(state.speed)}`;
  });
}

export function showConnection(connected) {
  const node = $('#statusConnection');
  node.textContent = connected ? 'Connected' : 'Disconnected · retrying';
  node.dataset.state = connected ? 'ok' : 'bad';
}
