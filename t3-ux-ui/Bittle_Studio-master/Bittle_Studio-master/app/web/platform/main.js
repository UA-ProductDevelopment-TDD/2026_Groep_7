// Bittle Platform: wires the 3D robot, the real robot, the controls, the motion recorder, the motor layout, the camera
// and the map together. One rule keeps them in step: every pose the 3D robot takes is shown on the sliders, and with
// "Robot volgt" on it is sent to the real robot; Petoi skills are sent as commands and the 3D robot plays them along.
import { $, h, clear, toast, api } from './ui.js';
import { createTwin } from './twin.js';
import { createRobot } from './robot.js';
import { initControl } from './control.js';
import { initMotions } from './motions.js';
import { initMotors } from './motors.js';
import { initCamera } from './camera.js';
import { initScan } from './scan.js';
import { createEnvironment } from './environment.js';

const twin = createTwin($('#twinView'), $('#twinOverlay'));
const robot = createRobot();
const follow = $('#followBox');
const modelSelect = $('#modelSelect');
let models = [], model = 'stock';

const following = () => follow.checked && robot.connected;

function manualPose(pose) {
  control.showPose(pose);
  if (following()) robot.sendPose(pose);
}

/** A Petoi command: the robot plays it itself (when connected), the 3D robot shows the same skill. */
async function playSkill(command, label) {
  if (robot.mirroring) await robot.stopReading();
  if (robot.connected) await robot.command(command);
  try {
    const plan = await api(`/api/skill?command=${encodeURIComponent(command)}&model=${model}`);
    twin.play(plan, { onPose: pose => control.showPose(pose) });
    $('#twinInfo').textContent = `${label}${plan.loop_from !== null ? ' · loopt tot Stop' : ''}`;
  } catch {
    $('#twinInfo').textContent = `${label} (alleen op de echte robot)`;
  }
  if (!robot.connected) toast(`${label}: alleen de 3D-robot (de echte robot is niet verbonden).`);
}

const control = initControl($('#drivePanel'), { twin, robot, playSkill, onManualPose: manualPose });
const motions = initMotions($('#motionsPanel'), { twin, robot, getModel: () => model, onPlayPose: manualPose });
const motors = initMotors($('#motorsPanel'), {
  robot, getModel: () => model, getPose: () => twin.pose(), onLayout: layout => robot.setLayout(layout),
});
let mapEditor = null;
// The scanned surroundings in 3D round the twin, placed by where the robot stands on the map.
const surroundings = createEnvironment(twin);
const showSurroundings = (scans, turned) => surroundings.set(scans, mapEditor?.current()?.robot, turned);
const scan = initScan($('#scanPanel'), { robot, twin, playSkill, onPose: manualPose, mapApi: () => mapEditor, onScans: showSurroundings });
$('#surroundingsBox').addEventListener('change', event => surroundings.show(event.target.checked));
let wide = false;
$('#lookAround').addEventListener('click', () => {
  wide = !wide;
  twin.lookAround(wide);
  $('#lookAround').textContent = wide ? 'Dichtbij' : 'Overzicht';
});

// The real robot's joints, while reading them, drive the 3D robot.
robot.onPose((pose, mirror) => {
  if (!mirror) return;
  twin.stop();
  twin.setPose(pose);
  control.showPose(twin.pose());
});

// Connection
const connectButtons = ['#connectBle', '#connectUsb', '#connectTest'].map(id => $(id));
async function connect(transport) {
  try {
    await robot.link.connect(transport);
    if (following()) robot.sendPose(twin.pose());
  } catch (error) {
    if (error.name !== 'NotFoundError') toast(error.message, true);  // NotFoundError: the picker was closed
  }
}
$('#connectBle').addEventListener('click', () => connect('ble'));
$('#connectUsb').addEventListener('click', () => connect('serial'));
$('#connectTest').addEventListener('click', () => connect('test'));
$('#disconnect').addEventListener('click', () => robot.link.disconnect());
robot.link.addEventListener('state', ({ detail }) => {
  for (const button of connectButtons) button.hidden = detail.connected;
  $('#disconnect').hidden = !detail.connected;
  $('#robotDot').className = 'dot' + (detail.connected ? ' on' : '');
  const via = { ble: 'Bluetooth', serial: 'USB', test: 'test (geen robot)' }[detail.transport] || '';
  $('#robotStatus').textContent = detail.connected ? `Verbonden via ${via}` : (detail.message === 'Connection lost' ? 'Verbinding verbroken' : 'Niet verbonden');
});
follow.addEventListener('change', () => { if (following()) robot.sendPose(twin.pose()); });

// Log
const logBox = h('div', { class: 'log', role: 'log', 'aria-live': 'off' });
const commandInput = h('input', { type: 'text', maxlength: 64, placeholder: 'bv. kbalance, ksit, m 0 30, j', 'aria-label': 'Commando voor de robot' });
const sendForm = h('form', { class: 'row', onsubmit: async event => {
  event.preventDefault();
  if (!robot.connected) return toast('Verbind eerst de robot.', true);
  try {
    await robot.command(commandInput.value.trim());
    commandInput.select();
  } catch (error) {
    toast(error.message, true);
  }
} }, commandInput, h('button', { type: 'submit', class: 'primary' }, 'Stuur'));
clear($('#logPanel'), h('h3', { text: 'Commando sturen' }), sendForm,
  h('p', { class: 'note', text: 'Petoi-commando\'s: k + vaardigheid (kwkF, ksit…), m servo hoek, j = gewrichten lezen, d = motoren uit.' }),
  h('h3', { text: 'Logboek' }), logBox);
robot.link.addEventListener('log', ({ detail }) => {
  const line = h('div', { class: detail.kind, text: `${new Date().toLocaleTimeString()}  ${detail.kind}  ${detail.message}` });
  logBox.append(line);
  while (logBox.childElementCount > 400) logBox.firstElementChild.remove();
  logBox.scrollTop = logBox.scrollHeight;
});

// Tabs
const tabButtons = [...document.querySelectorAll('#tabList [role=tab]')];
function selectTab(name, focus = false) {
  for (const button of tabButtons) {
    const on = button.dataset.tab === name;
    button.setAttribute('aria-selected', on);
    button.tabIndex = on ? 0 : -1;
    if (on && focus) button.focus();
  }
  for (const panel of document.querySelectorAll('[role=tabpanel]')) panel.hidden = panel.dataset.tab !== name;
}
tabButtons.forEach((button, index) => {
  button.addEventListener('click', () => selectTab(button.dataset.tab));
  button.addEventListener('keydown', event => {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (step) selectTab(tabButtons[(index + step + tabButtons.length) % tabButtons.length].dataset.tab, true);
  });
});

// Camera
initCamera({
  onStatus(status) {
    const live = status.state === 'streaming' && status.frame > 0;
    $('#cameraDot').className = 'dot' + (live ? ' on' : status.state === 'off' ? '' : status.state === 'connecting' ? ' wait' : ' bad');
    $('#cameraBadge').textContent = live ? `aan · ${status.fps} beelden/s` : { off: 'uit', connecting: 'starten…', 'no-camera': 'geen camera op het bordje', error: 'probleem', streaming: 'starten…' }[status.state] || status.state;
  },
});

// Robot model
async function chooseModel(id) {
  model = id;
  const entry = models.find(m => m.id === id);
  try {
    await twin.load(entry.urdf);
  } catch (error) {
    $('#twinOverlay').hidden = false;
    $('#twinOverlay').textContent = error.message;
    $('#twinOverlay').classList.add('error');
  }
  robot.setLayout(motors.modelChanged());
  control.setLimits(twin.limits());
  control.showPose(twin.pose());
  $('#twinInfo').textContent = entry.description;
  try { localStorage.setItem('platform-model', id); } catch { /* private mode */ }
}
modelSelect.addEventListener('change', () => chooseModel(modelSelect.value));

async function boot() {
  [models] = await Promise.all([api('/api/models'), motors.load()]);
  clear(modelSelect, models.map(m => h('option', { value: m.id, text: m.name })));
  let saved = 'stock';
  try { saved = localStorage.getItem('platform-model') || 'stock'; } catch { /* private mode */ }
  modelSelect.value = models.some(m => m.id === saved) ? saved : 'stock';
  await chooseModel(modelSelect.value);
  const info = await api('/api/info');
  // The map is its own module: if it fails to load, everything else still works.
  try {
    const { createMap } = await import('./map.js');
    mapEditor = createMap($('#mapPanel'), { canEdit: info.can_edit, toast, onChange: map => scan.mapChanged(map) });
    scan.mapChanged(mapEditor.current());
  } catch (error) {
    clear($('#mapPanel'), h('p', { class: 'error-text', text: 'De kaart kon niet laden: ' + error.message }));
  }
  if (!navigator.bluetooth) $('#connectBle').title = 'Bluetooth vanuit de browser werkt alleen in Chrome of Edge, op deze computer';
}

boot().catch(error => toast(error.message, true));
