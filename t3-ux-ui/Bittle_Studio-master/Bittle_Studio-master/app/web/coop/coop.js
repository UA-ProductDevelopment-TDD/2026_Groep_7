// Coop Guard dashboard: starts the panels, loads the model and polls the simulation state.
import { $, h, clear, fixed, tabs } from './ui.js';
import { get } from './api.js';
import { store, on, loadModel, acceptState, batteryLevel } from './store.js';
import { createViewport } from './viewport.js';
import { initTopbar, showConnection } from './topbar.js';
import { initScenePanel } from './scene-panel.js';
import { initMissionPanel } from './mission-panel.js';
import { initRobotPanel } from './robot-panel.js';
import { initSensorsPanel, setSensorsActive } from './sensors-panel.js';
import { initExperimentsPanel, setExperimentsActive } from './experiments-panel.js';
import { initHubPanel, setHubActive } from './hub-panel.js';

const POLL_MS = 80;
const RETRY_MS = [250, 500, 1000, 2000];  // waits after the 1st, 2nd, ... failed poll

function initViewControls(viewport) {
  for (const box of document.querySelectorAll('[data-overlay]')) {
    viewport.setOverlay(box.dataset.overlay, box.checked);
    box.addEventListener('change', () => viewport.setOverlay(box.dataset.overlay, box.checked));
  }
  const shadows = $('#shadowsBox');
  viewport.setShadows(shadows.checked);
  shadows.addEventListener('change', () => viewport.setShadows(shadows.checked));

  const follow = $('#followButton');
  const setFollow = value => {
    follow.setAttribute('aria-pressed', value);
    viewport.setFollow(value);
  };
  follow.addEventListener('click', () => setFollow(follow.getAttribute('aria-pressed') !== 'true'));
  $('#topButton').addEventListener('click', () => viewport.topView());
  $('#resetViewButton').addEventListener('click', () => {
    setFollow(false);
    viewport.resetView();
  });
}

function initHud() {
  on('state', state => {
    const robot = state.robot;
    $('#hudHeading').textContent = fixed(robot.heading, 0) + '°';
    $('#hudSpeed').textContent = fixed(robot.speed * 100, 1) + ' cm/s';
    $('#hudTilt').textContent = `${fixed(robot.roll, 0)}° / ${fixed(robot.pitch, 0)}°`;
    $('#hudSkill').textContent = robot.skill || 'idle';
    $('#hudFallen').hidden = !robot.fallen;

    const { battery, behaviour } = state;
    const percent = Math.round(battery.state_of_charge * 100);
    $('#hudBattery').textContent = percent + ' %';
    $('#hudBatteryFill').style.width = percent + '%';
    $('#hudBatteryBar').className = ('bar ' + batteryLevel(battery.state_of_charge)).trim();
    $('#hudMode').textContent = behaviour.state + (behaviour.state === 'dock' && behaviour.phase ? ' · ' + behaviour.phase : '');
    // Red while the deterrent is on (the alarm was confirmed); amber while a fox is being checked.
    const alarm = $('#hudAlarm');
    const checking = (behaviour.state === 'detect' || behaviour.state === 'deter') && behaviour.fox_frames > 0;
    const label = behaviour.deterring ? 'ALARM' : 'FOX SEEN';
    alarm.hidden = !(behaviour.deterring || checking);
    if (alarm.textContent !== label) alarm.textContent = label;  // it is a live region: only announce a real change
    alarm.classList.toggle('pending', !behaviour.deterring);
  });
}

function initLog() {
  const list = $('#logList');
  let shown = '';
  on('state', state => {
    const events = state.events || [];
    const key = events.length + JSON.stringify(events[0]) + JSON.stringify(events[events.length - 1]);
    if (key === shown) return;
    shown = key;
    $('#logCount').textContent = `(${events.length})`;
    clear(list, [...events].reverse().map(event => h('li', null, h('time', { text: fixed(event.time, 2) + ' s' }), h('span', { text: event.text }))));
  });
}

let connected = false;
let failures = 0;

async function poll() {
  let delay = POLL_MS;
  try {
    const state = await get('/api/coop/state');
    // A restarted simulator, or a scenario applied in another tab or by a script, means the model is out of date.
    // Not while this page itself is applying a scenario (it takes that model from the answer to its own request),
    // and never for an older state that was still on its way when the model arrived.
    if (failures || (state.revision > (store.model?.revision ?? 0) && !store.pending)) await loadModel();
    failures = 0;
    if (!connected) showConnection(connected = true);
    acceptState(state);
  } catch (error) {
    failures++;
    if (connected || failures === 1) showConnection(connected = false);
    delay = RETRY_MS[Math.min(failures, RETRY_MS.length) - 1];
  }
  setTimeout(poll, delay);
}

async function loadFirstModel() {
  for (;;) {
    try {
      await loadModel();
      return;
    } catch (error) {
      showConnection(connected = false);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
}

const tabPanel = name => $(`[data-tab=${name}][role=tabpanel]`);

async function boot() {
  initTopbar();
  const viewport = createViewport($('#viewport'), $('#viewportOverlay'));  // before the panels that pick points in it
  initScenePanel($('#scenePanel'), viewport);
  initMissionPanel(tabPanel('mission'), viewport);
  initRobotPanel(tabPanel('robot'));
  initSensorsPanel(tabPanel('sensors'));
  initExperimentsPanel(tabPanel('experiments'));
  initHubPanel(tabPanel('hub'));
  on('model', () => viewport.setModel(store.model));
  on('state', state => viewport.update(state));
  initViewControls(viewport);
  initHud();
  initLog();
  tabs($('#tabList'), [...document.querySelectorAll('[role=tabpanel]')], name => {
    setHubActive(name === 'hub');
    setSensorsActive(name === 'sensors');
    setExperimentsActive(name === 'experiments');
  });
  await loadFirstModel();
  poll();
}

boot().catch(error => {
  console.error(error);
  $('#statusConnection').textContent = 'Startup failed: ' + error.message;
});
