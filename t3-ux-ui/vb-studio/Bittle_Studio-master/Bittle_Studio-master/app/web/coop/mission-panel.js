// Mission tab: the state of the mission, the battery, what the detector sees, the metrics, and the settings of the
// patrol route, the behaviour, the detector and the battery.
import { h, clear, fixed, shown, clean, numberField, textField, selectField, toast, withBusy } from './ui.js';
import { get } from './api.js';
import { store, on, touches, applied, batteryLevel } from './store.js';
import { makeSection } from './section.js';
import { downloadFile, missionRunning, toggleMission } from './topbar.js';

const draft = {};
const MIN_WAYPOINTS = 2;
const MAX_WAYPOINTS = 40;
const EXTERNAL_COMMAND = '.venv\\Scripts\\python.exe app\\coop\\examples\\external_detector.py';

// The states a running mission cycles through; off, fallen and flat are shown as a status instead.
const STEPS = ['patrol', 'detect', 'deter', 'return', 'dock', 'charge', 'undock'];
const STATE_TEXT = {
  patrol: 'Patrolling the route.',
  detect: 'Looking at a possible fox, waiting for enough frames in a row.',
  deter: 'Deterrent on: driving the fox away.',
  return: 'Walking back to the dock.',
  dock: 'Docking',
  charge: 'Charging at the dock.',
  undock: 'Backing out of the dock.',
};
const PHASE_TEXT = {
  align: 'turning to face the dock', 'walk-in': 'walking in', back: 'backing out after a miss',
  approach: 'returning to the start of the approach',
};
export const LOCOMOTION_LABEL = { auto: 'Auto', petoi: 'Petoi\'s skills', gait: 'Generated gait' };
export const DETECTOR_LABEL = { 'ground-truth': 'Ground truth', 'colour-blob': 'Colour blobs', external: 'External program' };
const LIGHTING_LABEL = { day: 'Day', night: 'Night, moonlight only', 'night-ir': 'Night, infrared light on' };

const status = { cells: {}, steps: new Map(), pipKey: '' };
const battery = { cells: {} };
const detect = { cells: {}, frameKey: '', signature: '' };
const metrics = { cells: {}, lapKey: '' };

const pretty = key => key.charAt(0).toUpperCase() + key.slice(1).replace(/-/g, ' ');
const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
const grid = (...fields) => h('div', { class: 'grid2' }, fields);
const num = (target, key, label, unit, options) =>
  numberField({ label, unit, value: target[key], onInput: value => { target[key] = value; }, ...options });
/** A number with its unit, or an en dash for what the server has no value for yet (null). */
const amount = (value, digits, unit = '') => (typeof value === 'number' && Number.isFinite(value) ? fixed(value, digits) + unit : '–');
const scaled = (value, factor) => (typeof value === 'number' ? value * factor : null);
const percent = value => amount(scaled(value, 100), 0, ' %');
const seconds = value => amount(value, 1, ' s');
/** Set the text of a node only when it changed: the state arrives about 12 times a second. */
const put = (node, text) => { if (node.textContent !== text) node.textContent = text; };

/** A label and a value cell, registered in `cells` under `id` for the update. */
function metric(cells, id, label, wide = false) {
  cells[id] = h('dd', { text: '–' });
  return h('div', { class: wide ? 'metric wide' : 'metric' }, h('dt', { text: label }), cells[id]);
}

// Status of the mission

function statusBlock() {
  const cells = status.cells;
  for (const name of STEPS) status.steps.set(name, h('li', { class: 'step', 'data-state': name, text: pretty(name) }));
  status.dot = h('span', { class: 'dot' });
  status.text = h('span');
  status.button = h('button', { type: 'button', class: 'primary mission-start', onclick: () => toggleMission() }, 'Start mission');
  status.pips = h('span', { class: 'pips', role: 'img' });
  status.pipText = h('span', { text: '–' });
  return h('section', { class: 'block' },
    h('div', { class: 'toolbar-row' }, h('h3', { text: 'Mission' }), status.button),
    h('ol', { class: 'steps', 'aria-label': 'Mission states' }, [...status.steps.values()]),
    h('p', { class: 'status-line', role: 'status' }, status.dot, status.text),
    h('dl', { class: 'metrics' },
      metric(cells, 'since', 'Time in state'), metric(cells, 'motion', 'Walking motion'),
      metric(cells, 'locomotion', 'Locomotion'), metric(cells, 'laps', 'Laps'),
      metric(cells, 'route', 'Route length'), metric(cells, 'deterrent', 'Deterrent'),
      metric(cells, 'docked', 'Docked'), metric(cells, 'attempts', 'Dock attempts'),
      h('div', { class: 'metric wide' }, h('dt', { text: 'Fox frames in a row' }), h('dd', null, status.pips, status.pipText))));
}

function statusText(behaviour) {
  const state = behaviour.state;
  if (state === 'off') return 'Mission off: the robot moves only when you drive it.';
  if (state === 'flat') return 'Battery empty: press Reset to start again with a charged battery.';
  if (state === 'fallen') {
    return applied().behaviour.self_right ? 'Fallen: the robot stands up again in a few seconds.'
      : 'Fallen: self-righting is off, so it stays down until it gets up by itself.';
  }
  const phase = state === 'dock' && PHASE_TEXT[behaviour.phase] ? ` (${PHASE_TEXT[behaviour.phase]})` : '';
  return (STATE_TEXT[state] || pretty(state)).replace(/\.$/, '') + phase + '.';
}

function showStatus(state) {
  const behaviour = state.behaviour, cells = status.cells;
  for (const [name, step] of status.steps) {
    const current = name === behaviour.state;
    step.classList.toggle('active', current);
    if (current) step.setAttribute('aria-current', 'step');
    else step.removeAttribute('aria-current');
  }
  const stateName = behaviour.state;
  status.dot.className = 'dot' + (stateName === 'flat' ? ' error' : stateName === 'fallen' ? ' stale' : stateName === 'off' ? '' : ' ok');
  put(status.text, statusText(behaviour));

  const running = missionRunning(state);
  put(status.button, running ? '■ Stop mission' : '▶ Start mission');
  status.button.className = (running ? 'danger' : 'primary') + ' mission-start';
  status.button.disabled = stateName === 'flat';
  status.button.title = stateName === 'flat' ? 'The battery is empty: press Reset first' : '';

  const off = stateName === 'off' || stateName === 'flat';
  put(cells.since, off ? '–' : amount(state.time - behaviour.since, 1, ' s'));
  put(cells.motion, behaviour.motion ? pretty(behaviour.motion) : '–');
  put(cells.locomotion, behaviour.locomotion ? LOCOMOTION_LABEL[behaviour.locomotion] || behaviour.locomotion : '–');
  put(cells.laps, String(behaviour.laps));
  put(cells.route, amount(behaviour.route_length, 1, ' m'));
  put(cells.deterrent, behaviour.deterring ? 'on' : 'off');
  put(cells.docked, behaviour.docked ? 'yes' : 'no');
  put(cells.attempts, String(behaviour.dock_attempts));

  // One box per frame the detector must see the fox in a row, filled as the frames come in.
  const needed = applied().detector.confirm, frames = behaviour.fox_frames;
  const total = Math.min(20, Math.max(needed, frames));
  const key = `${frames}/${total}/${needed}`;
  if (key !== status.pipKey) {
    status.pipKey = key;
    clear(status.pips, Array.from({ length: total }, (_, n) =>
      h('i', { class: 'pip' + (n < frames ? ' on' : '') + (frames >= needed ? ' done' : '') })));
    const text = frames >= needed ? `${frames} · enough for the alarm` : `${frames} of ${needed} needed for the alarm`;
    status.pips.setAttribute('aria-label', text);
    status.pipText.textContent = text;
  }
}

// Battery

function batteryBlock() {
  const cells = battery.cells;
  battery.percent = h('div', { class: 'big', text: '–' });
  battery.fill = h('i');
  battery.bar = h('div', {
    class: 'bar wide', role: 'progressbar', 'aria-label': 'Battery charge', 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-valuenow': 0,
  }, battery.fill);
  battery.charge = h('p', { class: 'muted' });
  return h('section', { class: 'block' },
    h('h3', { text: 'Battery' }),
    battery.percent, battery.bar, battery.charge,
    h('dl', { class: 'metrics spaced' },
      metric(cells, 'power', 'Power draw'), metric(cells, 'used', 'Energy used'),
      metric(cells, 'charged', 'Energy charged'), metric(cells, 'lowest', 'Lowest charge'),
      metric(cells, 'ir', 'Infrared light')));
}

function showBattery(state) {
  const b = state.battery, cells = battery.cells;
  const level = batteryLevel(b.state_of_charge), width = Math.round(b.state_of_charge * 100);
  put(battery.percent, width + ' %');
  battery.percent.className = ('big ' + level).trim();
  battery.fill.style.width = width + '%';
  battery.bar.className = ('bar wide ' + level).trim();
  battery.bar.setAttribute('aria-valuenow', width);
  put(battery.charge, `${amount(b.charge_wh, 2)} of ${amount(applied().energy.battery_wh, 1)} Wh`);
  put(cells.power, amount(b.power_w, 2, ' W'));
  put(cells.used, amount(b.used_wh, 3, ' Wh'));
  put(cells.charged, amount(b.charged_wh, 3, ' Wh'));
  put(cells.lowest, percent(b.lowest));
  put(cells.ir, b.ir_on ? 'on' : 'off');
}

// What the detector sees: the camera's latest image with the detections drawn over it

function detectionBlock() {
  detect.image = h('img', { class: 'camera-image', alt: '' });
  detect.boxes = h('div', { class: 'det-boxes' });
  detect.stage = h('div', { class: 'detect-stage', hidden: true }, detect.image, detect.boxes);
  detect.message = h('p', { class: 'muted' });
  detect.list = h('ul', { class: 'detections', 'aria-label': 'Detected objects' });
  return h('section', { class: 'block' },
    h('h3', { text: 'What the detector sees' }),
    detect.message, detect.stage, detect.list,
    h('dl', { class: 'metrics spaced' },
      metric(detect.cells, 'lighting', 'Lighting'), metric(detect.cells, 'type', 'Detector'),
      metric(detect.cells, 'frame', 'Frame'), metric(detect.cells, 'age', 'Detection age')));
}

/** A box over the image, in percent of the image so that it follows the displayed size. */
function detectionBox(object, width, height, old) {
  const [x0, y0, x1, y1] = object.bbox;
  const left = clamp(x0 / width * 100, 0, 100), top = clamp(y0 / height * 100, 0, 100);
  const across = Math.min(clamp((x1 - x0) / width * 100, 0, 100), 100 - left);
  const down = Math.min(clamp((y1 - y0) / height * 100, 0, 100), 100 - top);
  const text = `${object.label} ${fixed(object.confidence * 100, 0)} %`;
  return h('div', {
    class: old ? 'det-box old' : 'det-box', 'data-label': object.label, title: text,
    style: `left:${fixed(left, 2)}%;top:${fixed(top, 2)}%;width:${fixed(across, 2)}%;height:${fixed(down, 2)}%`,
  }, h('span', { text }));
}

function detectionItem(object) {
  const metres = object.distance;
  const bearing = object.bearing;
  const where = [
    typeof metres === 'number' ? (metres < 1 ? `${fixed(metres * 100, 0)} cm` : `${fixed(metres, 2)} m`) : null,
    typeof bearing === 'number' ? (Math.abs(bearing) < .5 ? 'ahead' : `${fixed(Math.abs(bearing), 0)}° ${bearing > 0 ? 'left' : 'right'}`) : null,
  ].filter(Boolean);
  return h('li', { 'data-label': object.label },
    h('i', { class: 'swatch', 'aria-hidden': 'true' }),
    h('span', { text: `${pretty(object.label)} · ${fixed(object.confidence * 100, 0)} %` }),
    h('span', { class: 'muted', text: where.join(' · ') }));
}

function showDetection(state) {
  const settings = applied().detector, cells = detect.cells;
  const reading = settings.camera ? state.sensors[settings.camera] : null;
  const usable = Boolean(reading) && reading.type === 'camera';
  detect.stage.hidden = !usable;
  detect.message.hidden = usable;
  if (!usable) {
    put(detect.message, settings.camera ? `The camera "${settings.camera}" is not in the scenario. Choose another one in the detector settings below.`
      : 'No camera is chosen for the detector. Choose one in the detector settings below.');
    detect.frameKey = detect.signature = '';
    clear(detect.boxes);
    clear(detect.list);
    for (const cell of Object.values(cells)) put(cell, '–');
    return;
  }
  const result = state.detection;
  // The picture changes with a new frame (and after a restart, which counts frames from 1 again).
  const frameKey = `${state.revision}:${reading.frame}`;
  if (frameKey !== detect.frameKey) {
    detect.frameKey = frameKey;
    detect.image.src = reading.url;
    detect.image.alt = `Latest image of the detector camera ${settings.camera}`;
    detect.stage.style.aspectRatio = `${reading.width} / ${reading.height}`;
  }
  // The detections belong to the frame they were made from; one from an older frame is drawn faded.
  const old = Boolean(result) && typeof result.frame === 'number' && result.frame !== reading.frame;
  const signature = JSON.stringify([reading.frame, reading.width, reading.height, result]);
  if (signature !== detect.signature) {
    detect.signature = signature;
    const objects = result ? result.objects : [];
    clear(detect.boxes, objects.map(object => detectionBox(object, reading.width, reading.height, old)));
    clear(detect.list, objects.length ? objects.map(detectionItem)
      : h('li', { class: 'muted', text: result ? 'Nothing recognised in this frame.'
        : settings.type === 'external' ? 'Waiting for the outside program: no fresh detection.' : 'No fresh detection yet.' }));
  }
  put(cells.lighting, LIGHTING_LABEL[reading.lighting] || String(reading.lighting));
  put(cells.type, DETECTOR_LABEL[settings.type] || settings.type);
  put(cells.frame, String(reading.frame) + (old ? ` · boxes from frame ${result.frame}` : ''));
  put(cells.age, result ? amount(state.time - result.time, 1, ' s') : '–');
}

// Metrics. Each entry: key of the cell, label, text from the summary (state.metrics, see metrics.py).

const pair = (a, b, factor, digits, unit) => (typeof a === 'number' || typeof b === 'number'
  ? `${amount(scaled(a, factor), digits)} / ${amount(scaled(b, factor), digits)}${unit}` : '–');

const METRIC_GROUPS = [
  ['Walking', [
    ['distance', 'Distance walked', m => amount(m.distance_m, 2, ' m')],
    ['laps', 'Laps', m => String(m.laps)],
    ['deviation', 'Route deviation, mean / max', m => pair(m.route_deviation_m.mean, m.route_deviation_m.max, 100, 1, ' cm')],
    ['falls', 'Falls', m => String(m.falls)],
    ['selfRights', 'Self-rights', m => String(m.self_rights)],
    ['stops', 'Obstacle stops', m => String(m.obstacle_stops)],
  ]],
  ['Fence coverage', [
    ['coverage', 'This lap', m => percent(m.coverage.current_lap)],
    ['coverageMean', 'Finished laps, mean', m => percent(m.coverage.mean)],
  ]],
  ['Fox', [
    ['appeared', 'Appeared at', m => seconds(m.fox.appeared_at)],
    ['inView', 'In view at', m => seconds(m.fox.in_view_at)],
    ['alarmAt', 'Alarm at', m => seconds(m.fox.alarm_at)],
    ['fled', 'Fled at', m => seconds(m.fox.fled_at)],
    ['toAlarm', 'Alarm after it appeared', m => seconds(m.fox.time_to_alarm_s)],
    ['toAlarmView', 'Alarm after it was in view', m => seconds(m.fox.time_to_alarm_in_view_s)],
    ['toFlee', 'Fled after the alarm', m => seconds(m.fox.time_to_flee_s)],
  ]],
  ['Alarms', [
    ['alarmsTrue', 'True alarms', m => String(m.alarms.true)],
    ['alarmsFalse', 'False alarms', m => String(m.alarms.false)],
    ['unconfirmed', 'Unconfirmed', m => String(m.alarms.unconfirmed)],
  ]],
  ['Docking', [
    ['dockAttempts', 'Attempts', m => String(m.docking.attempts)],
    ['dockSuccesses', 'Successes', m => `${m.docking.successes} of ${m.docking.dockings}`],
    ['dockRate', 'Success rate', m => percent(m.docking.success_rate)],
    ['dockBeside', 'Mean error beside', m => amount(scaled(m.docking.mean_lateral_m, 1000), 0, ' mm')],
    ['dockHeading', 'Mean heading error', m => amount(m.docking.mean_heading_deg, 1, '°')],
  ]],
  ['Energy', [
    ['energyUsed', 'Used', m => amount(m.energy.used_wh, 3, ' Wh')],
    ['energyLap', 'Per lap, mean', m => amount(m.energy.mean_per_lap_wh, 3, ' Wh')],
  ]],
];

const LAP_COLUMNS = [['Lap', ''], ['Duration', 's'], ['Energy', 'Wh'], ['Coverage', '%'], ['Deviation', 'mean / max cm'], ['Falls', '']];

function metricsBlock() {
  metrics.laps = h('tbody');
  const groups = METRIC_GROUPS.flatMap(([title, entries]) => [
    h('h4', { text: title }),
    h('dl', { class: 'metrics' }, entries.map(([id, label]) => metric(metrics.cells, id, label))),
  ]);
  return h('section', { class: 'block' },
    h('div', { class: 'toolbar-row' },
      h('h3', { text: 'Metrics' }),
      h('button', { type: 'button', onclick: event => downloadMetrics(event.currentTarget) }, 'Download metrics (JSON)')),
    groups,
    h('h4', { text: 'Finished laps' }),
    h('div', { class: 'table-wrap tall' },
      h('table', { class: 'laps' },
        h('caption', { class: 'sr-only', text: 'Finished laps' }),
        h('thead', null, h('tr', null, LAP_COLUMNS.map(([name, unit]) =>
          h('th', { scope: 'col' }, name, unit ? h('small', { text: unit }) : null)))),
        metrics.laps)),
    h('p', { class: 'note', text: 'Times are simulated seconds since the run started. The fox alarm is timed from when the fox appeared and from when it first came into view, bright enough to be recognised. Coverage is the share of the points along the fence that the camera has shown in the lap.' }));
}

function lapRow(lap) {
  const cell = text => h('td', { class: 'num', text });
  return h('tr', null,
    h('th', { scope: 'row', text: String(lap.lap) }),
    cell(fixed(lap.seconds, 1)), cell(fixed(lap.energy_wh, 3)), cell(fixed(lap.coverage * 100, 0)),
    cell(`${fixed(lap.mean_deviation * 100, 1)} / ${fixed(lap.max_deviation * 100, 1)}`), cell(String(lap.falls)));
}

function showMetrics(state) {
  const m = state.metrics;
  for (const [, entries] of METRIC_GROUPS) for (const [id, , format] of entries) put(metrics.cells[id], format(m));
  const key = JSON.stringify(m.lap_list);
  if (key === metrics.lapKey) return;
  metrics.lapKey = key;
  clear(metrics.laps, m.lap_list.length ? m.lap_list.map(lapRow)
    : h('tr', null, h('td', { colspan: LAP_COLUMNS.length, class: 'muted', text: 'No finished laps yet.' })));
}

async function downloadMetrics(button) {
  try {
    const data = await withBusy(button, () => get('/api/coop/metrics'));
    const base = String(data.scenario).replace(/[^A-Za-z0-9 _-]+/g, '').trim().replace(/\s+/g, '-') || 'coop';
    downloadFile(`${base}-metrics-${Math.round(data.time)}s.json`, JSON.stringify(data, null, 2));
  } catch (error) {
    toast(error.message, true);
  }
}

// Patrol route and walking

let viewport = null;
let patrolItem = null;
let stopPick = null;           // ends the 3D view's pick mode while waypoints are added on the ground
let refreshRoute = () => {};   // redraws the waypoint table of the form that is open
let refreshPick = () => {};    // sets the label of that form's pick button

function endPick() {
  if (!stopPick) return;
  const stop = stopPick;
  stopPick = null;
  stop();
  refreshPick();
}

function addWaypoint(point) {
  const route = draft.patrol.route;
  route.push([Math.round(point[0] * 100) / 100, Math.round(point[1] * 100) / 100]);
  patrolItem.markDirty();
  refreshRoute();
  if (route.length >= MAX_WAYPOINTS) {
    toast(`A route has at most ${MAX_WAYPOINTS} waypoints`, true);
    endPick();
  }
}

/** Length of the closed loop through the waypoints, in metres. */
const loopLength = route => route.reduce((sum, point, index) => {
  const next = route[(index + 1) % route.length];
  return sum + Math.hypot(next[0] - point[0], next[1] - point[1]);
}, 0);

function sensorOptions(type, none) {
  const sensors = applied().sensors.filter(sensor => sensor.type === type);
  const label = sensor => (sensors.filter(other => other.name === sensor.name).length > 1 ? `${sensor.name} (${sensor.id})` : sensor.name);
  return [...(none ? [{ value: '', label: none }] : []), ...sensors.map(sensor => ({ value: sensor.id, label: label(sensor) }))];
}

function patrolForm(item) {
  const patrol = draft.patrol, route = patrol.route;
  const body = h('tbody');
  const length = h('p', { class: 'note' });
  const hint = h('p', { class: 'note', role: 'status', hidden: true, text: 'Click the ground in the 3D view to add waypoints. They are drawn there once you apply. Press Esc or Done to finish.' });
  const pick = h('button', { type: 'button' });
  const clearButton = h('button', { type: 'button' }, 'Clear');

  const showLength = () => {
    length.textContent = route.length < MIN_WAYPOINTS ? `Add at least ${MIN_WAYPOINTS} waypoints.`
      : `${route.length} waypoints, a loop of ${amount(loopLength(route), 1)} m: after the last one the robot walks back to the first.`;
  };
  const showPick = () => {
    pick.textContent = stopPick ? 'Done adding waypoints' : 'Add waypoints on the ground';
    hint.hidden = !stopPick;
  };
  /** Focus the enabled button of this kind in a row, or any enabled one: the table is rebuilt after every change. */
  const focusRow = (index, kind) => {
    const buttons = [...body.querySelectorAll(`button[data-row="${index}"]`)].filter(button => !button.disabled);
    const target = buttons.find(button => button.dataset.kind === kind) || buttons[0];
    if (target) target.focus();
  };

  function waypointRow(point, index) {
    const axis = (which, name) => {
      const input = h('input', {
        type: 'number', step: 'any', min: -20, max: 20, inputmode: 'decimal', value: shown(point[which]),
        'aria-label': `Waypoint ${index + 1} ${name} (m)`,
      });
      input.addEventListener('input', () => {
        point[which] = input.value.trim() === '' ? NaN : clean(Number(input.value));
        showLength();
      });
      return h('td', null, input);
    };
    const button = (kind, symbol, label, disabled, action) => h('button', {
      type: 'button', class: 'icon', 'data-row': index, 'data-kind': kind, title: label,
      'aria-label': `${label}, waypoint ${index + 1}`, disabled, onclick: action,
    }, symbol);
    const move = delta => {
      route.splice(index + delta, 0, route.splice(index, 1)[0]);
      item.markDirty();
      fill();
      focusRow(index + delta, delta < 0 ? 'up' : 'down');
    };
    return h('tr', null,
      h('th', { scope: 'row', text: String(index + 1) }),
      axis(0, 'x'), axis(1, 'y'),
      h('td', { class: 'row-buttons' },
        button('up', '↑', 'Move up', index === 0, () => move(-1)),
        button('down', '↓', 'Move down', index === route.length - 1, () => move(1)),
        button('remove', '✕', route.length <= MIN_WAYPOINTS ? 'Remove (a route needs at least 2 waypoints)' : 'Remove', route.length <= MIN_WAYPOINTS, () => {
          route.splice(index, 1);
          item.markDirty();
          fill();
          if (route.length) focusRow(Math.min(index, route.length - 1), 'remove');
          else pick.focus();
        })));
  }

  function fill() {
    clear(body, route.length ? route.map(waypointRow)
      : h('tr', null, h('td', { colspan: 4, class: 'muted', text: 'No waypoints yet.' })));
    showLength();
  }

  pick.addEventListener('click', () => {
    if (stopPick) {
      endPick();
    } else if (!viewport || typeof viewport.pick !== 'function') {
      toast('The 3D view is not available here. Type the waypoints into the table instead.', true);
    } else if (draft.patrol.route.length >= MAX_WAYPOINTS) {
      toast(`A route has at most ${MAX_WAYPOINTS} waypoints`, true);
    } else {
      // The third argument runs however picking ends (Esc in the 3D view too), so the button never stays on "Done".
      const stop = viewport.pick(addWaypoint, 'Click the ground to add patrol waypoints · Esc to finish', () => {
        stopPick = null;
        refreshPick();
      });
      stopPick = typeof stop === 'function' ? stop : null;
      showPick();
    }
  });
  clearButton.addEventListener('click', () => {
    route.splice(0, route.length);
    item.markDirty();
    fill();
    pick.focus();
  });
  refreshRoute = fill;
  refreshPick = showPick;
  fill();
  showPick();

  return h('div', null,
    h('div', { class: 'table-wrap' },
      h('table', { class: 'route' },
        h('caption', { class: 'sr-only', text: 'Patrol waypoints' }),
        h('thead', null, h('tr', null,
          h('th', { scope: 'col', text: '#' }), h('th', { scope: 'col', text: 'x (m)' }), h('th', { scope: 'col', text: 'y (m)' }),
          h('th', { scope: 'col' }, h('span', { class: 'sr-only', text: 'Actions' })))),
        body)),
    length,
    h('div', { class: 'button-row' }, pick, clearButton),
    hint,
    grid(
      num(patrol, 'tolerance', 'Waypoint tolerance', 'cm', { scale: 100, min: 5, max: 200 }),
      num(patrol, 'obstacle_distance', 'Obstacle distance', 'cm', { scale: 100, min: 0, max: 100 })),
    selectField({
      label: 'Locomotion', value: patrol.locomotion, onInput: value => { patrol.locomotion = value; },
      options: store.model.choices.locomotion.map(name => ({ value: name, label: LOCOMOTION_LABEL[name] || name })),
    }),
    selectField({
      label: 'Obstacle sensor', value: patrol.obstacle_sensor, onInput: value => { patrol.obstacle_sensor = value; },
      options: sensorOptions('tof', 'None: never stops for obstacles'),
    }),
    h('p', { class: 'note', text: `The route is a closed loop of ${MIN_WAYPOINTS} to ${MAX_WAYPOINTS} waypoints in metres. The waypoint tolerance is how close counts as reaching one. The robot stops when the obstacle sensor sees something nearer than the obstacle distance, and turns away if it stays blocked.` }),
    h('p', { class: 'note', text: 'Auto walks with Petoi\'s skills on the stock legs and with the generated gait on any other leg design. Petoi\'s skills only fit the stock legs.' }));
}

// Behaviour

function behaviourForm() {
  const b = draft.behaviour;
  const selfRight = h('input', { type: 'checkbox', checked: b.self_right });
  selfRight.addEventListener('change', () => { b.self_right = selfRight.checked; });
  return h('div', null,
    grid(
      num(b, 'laps_before_charging', 'Laps before charging', '', { min: 0, max: 100, integer: true }),
      num(b, 'dock_attempts', 'Docking attempts', '', { min: 1, max: 20, integer: true }),
      num(b, 'low_battery', 'Low battery', '%', { scale: 100, min: 0, max: 100 }),
      num(b, 'resume_battery', 'Resume at', '%', { scale: 100, min: 0, max: 100 }),
      num(b, 'deter_time', 'Deter time', 's', { min: 0, max: 600 }),
      num(b, 'chase_distance', 'Chase distance', 'm', { min: .1, max: 5 })),
    h('label', { class: 'check' }, selfRight, 'Self-righting after a fall'),
    h('p', { class: 'note', text: 'Laps before charging: the robot also goes to the dock after this many laps (0 = only when the battery is low or after a fox). It goes below the low battery level and charges up to the resume level, which must be higher. Docking attempts: approaches before docking counts as failed.' }),
    h('p', { class: 'note', text: 'Deter time: how long the deterrent stays on after the fox was last seen. Chase distance: how close the deterring robot comes to the fox. Self-righting: after a fall the robot stands up again where it lies, as Bittle\'s firmware can.' }));
}

// Detector

function detectorForm() {
  const d = draft.detector;
  const outside = h('div', { hidden: d.type !== 'external' });
  const showOutside = () => { outside.hidden = d.type !== 'external'; };
  const copy = h('button', {
    type: 'button',
    onclick: async () => {
      try {
        await navigator.clipboard.writeText(EXTERNAL_COMMAND);
        toast('Command copied');
      } catch (error) {
        toast('Select the command and copy it by hand', true);
      }
    },
  }, 'Copy');
  clear(outside,
    h('p', { class: 'note', text: 'An outside program, such as the AI camera module, sends the detections. While the simulator runs, start the example in a second terminal from the project folder, and keep the simulation speed at 1×:' }),
    h('div', { class: 'command' }, h('code', { text: EXTERNAL_COMMAND }), copy));
  return h('div', null,
    selectField({
      label: 'Type', value: d.type, onInput: value => { d.type = value; showOutside(); },
      options: store.model.choices.detector_types.map(name => ({ value: name, label: DETECTOR_LABEL[name] || name })),
    }),
    selectField({
      label: 'Camera', value: d.camera, onInput: value => { d.camera = value; },
      options: sensorOptions('camera'),
    }),
    grid(
      num(d, 'min_pixels', 'Minimum pixels', 'px', { min: 1, max: 10000, integer: true }),
      num(d, 'min_brightness', 'Minimum brightness', '%', { scale: 100, min: 0, max: 100 }),
      num(d, 'confirm', 'Confirm frames', '', { min: 1, max: 20, integer: true }),
      num(d, 'stale', 'Stale time', 's', { min: .1, max: 60 })),
    textField({ label: 'External topic', value: d.external_topic, onInput: value => { d.external_topic = value; } }),
    outside,
    h('p', { class: 'note', text: 'Ground truth is an ideal detector that reads from the renderer what each pixel shows. Colour blobs is a simple colour classifier: fox orange, chicken white, person blue. External takes the detections of an outside program from the external topic.' }),
    h('p', { class: 'note', text: 'Minimum pixels: the smallest object that counts. Minimum brightness: darker pixels show nothing (night without enough light). Confirm frames: frames in a row with a fox before the alarm goes off. Stale time: how old a detection may be and still count.' }));
}

// Energy

function energyForm() {
  const e = draft.energy;
  return h('div', null,
    grid(
      num(e, 'battery_wh', 'Battery capacity', 'Wh', { min: .1, max: 1000 }),
      num(e, 'voltage', 'Voltage', 'V', { min: 1, max: 48 }),
      num(e, 'base_power', 'Base power', 'W', { min: 0, max: 100 }),
      num(e, 'ir_power', 'Infrared power', 'W', { min: 0, max: 100 }),
      num(e, 'servo_idle_current', 'Servo idle current', 'mA', { scale: 1000, min: 0, max: 5000 }),
      num(e, 'servo_stall_current', 'Servo stall current', 'A', { min: 0, max: 20 }),
      num(e, 'charge_power', 'Charging power', 'W', { min: 0, max: 1000 }),
      num(e, 'start_charge', 'Start charge', '%', { scale: 100, min: 0, max: 100 })),
    h('p', { class: 'warning', text: 'These are assumptions, not measurements. Replace them with values you measured: the battery label, and the current of the boards and the servos with a meter.' }),
    h('p', { class: 'note', text: 'Base power: the boards, camera and ToF sensors. Infrared power: the camera\'s infrared LEDs, on at night. A servo draws its idle current plus up to the stall current in proportion to its torque. Charging power goes into the battery while the robot is docked.' }));
}

// Panel

export function initMissionPanel(root, view) {
  viewport = view;
  patrolItem = makeSection({ title: 'Patrol route', draft, name: 'patrol', build: patrolForm });
  const behaviour = makeSection({ title: 'Behaviour', draft, name: 'behaviour', build: behaviourForm });
  const detector = makeSection({ title: 'Detector', draft, name: 'detector', build: detectorForm });
  const energy = makeSection({ title: 'Energy', draft, name: 'energy', build: energyForm });
  const sections = [patrolItem, behaviour, detector, energy];

  clear(root, statusBlock(), batteryBlock(), detectionBlock(), metricsBlock(), sections.map(item => item.el));
  on('model', keys => {
    endPick();  // the world was rebuilt
    detect.frameKey = detect.signature = '';
    for (const item of sections) {
      if (item.keys.some(key => touches(keys, key))) item.reset();
      else if (touches(keys, 'sensors') && (item === patrolItem || item === detector)) item.render();  // their sensor lists
    }
  });
  on('state', state => {
    if (root.hidden) return;
    showStatus(state);
    showBattery(state);
    showDetection(state);
    showMetrics(state);
  });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') endPick(); });
}
