// Sensors tab: one card per sensor with its live reading, an edit form, remove and self-test; add new sensors.
import { h, clear, clone, fixed, numberField, textField, selectField, confirmButton, testResult, toast, withBusy } from './ui.js';
import { post } from './api.js';
import { store, on, touches, applyScenario } from './store.js';

const KIND_LABEL = { camera: 'Camera', tof: 'ToF distance sensor', imu: 'IMU' };
const TOPIC_PREFIX = { camera: 'camera', tof: 'sensors', imu: 'sensors' };
const GROUPED = { post: 'Fence posts', fence: 'Fence panels', roof: 'House roof' };  // many bodies of one kind read as one object
const SELF_WARNING = .1;  // share of the camera image that is the robot itself

const editing = new Map();  // sensor id -> draft being edited (also holds sensors that are not applied yet)
const fresh = new Set();    // ids of sensors that exist only in a draft
const tests = new Map();    // sensor id -> latest self-test result
const cards = new Map();    // sensor id -> {update(reading, status)}
let list = null, panel = null;

const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
const distance = metres => (metres < 1 ? `${fixed(metres * 100, 0)} cm` : `${fixed(metres, 2)} m`);

// Defaults copied from app/coop/config.py

function defaults(type, id, link) {
  if (type === 'camera') {
    return { id, type, name: 'Camera', link, position: [.05, 0, .01], rotation: [0, 0, 0], fov: 60, width: 160, height: 120, range: 5, rate: 4 };
  }
  if (type === 'tof') {
    return { id, type, name: 'ToF sensor', link, position: [.06, 0, 0], rotation: [0, -13, 0], range: 2, cone: 25, rays: 5, noise: .03, rate: 20 };
  }
  return { id, type, name: 'IMU', link, noise: 0, rate: 100 };
}

function addSensor(type) {
  const links = store.model.robot.links;
  const used = new Set([...store.model.scenario.sensors.map(sensor => sensor.id), ...fresh]);
  let n = 1;
  while (used.has(`${type}-${n}`)) n++;
  const wanted = type === 'camera' ? 'head-link' : 'base-frame-link';
  const sensor = defaults(type, `${type}-${n}`, links.includes(wanted) ? wanted : links[0]);
  sensor.name = `${sensor.name} ${n}`;
  editing.set(sensor.id, sensor);
  fresh.add(sensor.id);
  renderList();
  const card = list.querySelector(`[data-id="${sensor.id}"]`);
  if (card) card.scrollIntoView({ block: 'nearest' });
}

// Live readings

const row = (label, value) => h('div', { class: 'metric' }, h('dt', { text: label }), value);

function liveCamera(sensor) {
  const image = h('img', {
    class: 'camera-image', alt: `Live image from ${sensor.name}`, width: sensor.width, height: sensor.height,
  });
  image.style.aspectRatio = `${sensor.width} / ${sensor.height}`;
  const frame = h('dd', { text: '–' }), brightness = h('dd', { text: '–' }), nearest = h('dd', { text: '–' });
  const seen = h('ul', { class: 'seen', 'aria-label': 'Objects in the image' });
  const warning = h('p', { class: 'warning', hidden: true });
  let shown = -1;
  return {
    el: h('div', null, image, h('dl', { class: 'metrics' }, row('Frame', frame), row('Brightness', brightness), row('Nearest', nearest)), seen, warning),
    update(reading) {
      if (reading.frame === shown) return;  // the image and everything derived from it only change with a new frame
      shown = reading.frame;
      image.src = reading.url;
      frame.textContent = reading.frame;
      brightness.textContent = fixed(reading.brightness * 100, 0) + ' %';
      nearest.textContent = reading.nearest === null ? 'nothing in range' : distance(reading.nearest);
      clear(seen, visibleObjects(reading));
      warning.hidden = !(reading.self_pixels > SELF_WARNING);
      warning.textContent = `Warning: Bittle's own body fills ${fixed(reading.self_pixels * 100, 0)} % of this image. Move the camera forward or up.`;
    },
  };
}

/** Objects in the camera image as rows with their share of the pixels, named through model.bodies. */
function visibleObjects(reading) {
  const total = reading.width * reading.height;
  const bodies = store.model.bodies || {};
  const groups = new Map();
  let counted = 0;
  for (const [id, count] of Object.entries(reading.visible || {})) {
    const body = bodies[id];
    const key = body && GROUPED[body.kind] ? body.kind : id;
    const group = groups.get(key) || { count: 0, bodies: 0, name: body ? body.name : `Body ${id}`, kind: body && body.kind };
    group.count += count;
    group.bodies += 1;
    groups.set(key, group);
    counted += count;
  }
  const items = [...groups.values()].map(group => ({
    label: GROUPED[group.kind] && group.bodies > 1 ? `${GROUPED[group.kind]} (${group.bodies})` : group.name,
    count: group.count,
  }));
  if (total - counted > total * .005) items.push({ label: 'Sky / nothing', count: total - counted, quiet: true });
  items.sort((a, b) => b.count - a.count);
  return items.slice(0, 7).map(item => h('li', { class: item.quiet ? 'quiet' : '' },
    h('span', { class: 'seen-name', text: item.label }),
    h('span', { class: 'bar' }, h('i', { style: `width:${fixed(item.count / total * 100, 1)}%` })),
    h('span', { class: 'seen-percent', text: fixed(item.count / total * 100, 0) + ' %' })));
}

function liveTof(sensor) {
  const big = h('div', { class: 'big', text: '–' });
  const fill = h('i');
  const bar = h('div', { class: 'bar wide', role: 'img', 'aria-label': `Distance on a scale of 0 to ${distance(sensor.range)}` }, fill);
  const hit = h('p', { class: 'muted', text: '' });
  return {
    el: h('div', null, big, bar, h('div', { class: 'scale' }, h('span', { text: '0' }), h('span', { text: distance(sensor.range) })), hit),
    update(reading) {
      const inRange = reading.in_range && reading.distance !== null;
      big.textContent = inRange ? fixed(reading.distance * 100, 1) + ' cm' : 'out of range';
      big.classList.toggle('none', !inRange);
      fill.style.width = inRange ? clamp(reading.distance / sensor.range, 0, 1) * 100 + '%' : '0';
      const body = inRange && reading.hit ? (store.model.bodies || {})[String(reading.hit.body)] : null;
      hit.textContent = inRange ? `Hits: ${body ? body.name : 'body ' + (reading.hit && reading.hit.body)}` : `Nothing within ${distance(sensor.range)}`;
    },
  };
}

function liveImu() {
  const cells = { orientation: [], gyro: [], accel: [] };
  const line = (label, key, unit) => {
    cells[key] = [0, 1, 2].map(() => h('td', { text: '–' }));
    return h('tr', null, h('th', { scope: 'row', text: label }), cells[key], h('td', { class: 'unit', text: unit }));
  };
  const table = h('table', { class: 'imu' },
    h('thead', null, h('tr', null, h('td'), ['x / roll', 'y / pitch', 'z / yaw'].map(text => h('th', { scope: 'col', text })), h('td'))),
    h('tbody', null,
      line('Orientation', 'orientation', '°'), line('Gyro', 'gyro', 'rad/s'), line('Accel', 'accel', 'm/s²')));
  const put = (key, values, scale = 1, digits = 2) => values.forEach((value, n) => { cells[key][n].textContent = fixed(value * scale, digits); });
  return {
    el: table,
    update(reading) {
      put('orientation', reading.orientation, 180 / Math.PI, 1);
      put('gyro', reading.angular_velocity, 1, 3);
      put('accel', reading.linear_acceleration, 1, 2);
    },
  };
}

// Edit form

function editForm(draft, isFresh, close) {
  const links = store.model.robot.links.map(link => ({ value: link, label: link }));
  const num = (target, key, label, unit, options) =>
    numberField({ label, unit, value: target[key], onInput: value => { target[key] = value; }, ...options });
  const grid = (...fields) => h('div', { class: 'grid2' }, fields);
  const error = h('p', { class: 'form-error', role: 'alert' });
  const parts = [
    textField({ label: 'Name', value: draft.name, onInput: value => { draft.name = value; } }),
    selectField({ label: 'Attached to link', options: links, value: draft.link, onInput: value => { draft.link = value; } }),
  ];
  if (draft.type !== 'imu') {
    parts.push(
      h('h4', { text: 'Mounting' }),
      grid(num(draft.position, 0, 'Position x', 'cm', { scale: 100, min: -50, max: 50 }),
        num(draft.position, 1, 'Position y', 'cm', { scale: 100, min: -50, max: 50 }),
        num(draft.position, 2, 'Position z', 'cm', { scale: 100, min: -50, max: 50 }), h('span'),
        num(draft.rotation, 0, 'Roll', '°', { min: -360, max: 360 }),
        num(draft.rotation, 1, 'Pitch', '°', { min: -360, max: 360 }),
        num(draft.rotation, 2, 'Yaw', '°', { min: -360, max: 360 })),
      h('p', { class: 'note', text: 'Body axes, measured from the origin of the link: x forward, y left, z up. A sensor on the head turns with the neck. A negative pitch tilts the sensor up.' }));
  }
  parts.push(h('h4', { text: 'Settings' }));
  if (draft.type === 'camera') {
    parts.push(grid(
      num(draft, 'fov', 'Field of view (vertical)', '°', { min: 10, max: 170 }),
      num(draft, 'range', 'Range', 'm', { min: .1, max: 50 }),
      num(draft, 'width', 'Width', 'px', { min: 32, max: 640, integer: true }),
      num(draft, 'height', 'Height', 'px', { min: 24, max: 480, integer: true }),
      num(draft, 'rate', 'Frame rate', 'Hz', { min: .2, max: 30 })));
  } else if (draft.type === 'tof') {
    parts.push(grid(
      num(draft, 'range', 'Range', 'm', { min: .01, max: 10 }),
      num(draft, 'cone', 'Cone angle', '°', { min: 0, max: 90 }),
      num(draft, 'rays', 'Rays', '', { min: 1, max: 25, integer: true }),
      num(draft, 'noise', 'Noise', '% of distance', { scale: 100, min: 0, max: 50 }),
      num(draft, 'rate', 'Rate', 'Hz', { min: 1, max: 200 })));
  } else {
    parts.push(
      grid(num(draft, 'noise', 'Noise (σ)', '', { min: 0, max: 1 }), num(draft, 'rate', 'Rate', 'Hz', { min: 1, max: 500 })),
      h('p', { class: 'note', text: 'The IMU sits at the origin of its link. Noise is the standard deviation of the gyro in rad/s; the accelerometer scatters by noise × 9.81 m/s².' }));
  }
  const apply = h('button', { type: 'button', class: 'primary' }, isFresh ? 'Add sensor' : 'Apply sensor');
  apply.addEventListener('click', async () => {
    error.textContent = '';
    const sensors = clone(store.model.scenario.sensors);
    const at = sensors.findIndex(sensor => sensor.id === draft.id);
    if (at >= 0) sensors[at] = clone(draft); else sensors.push(clone(draft));
    try {
      await withBusy(apply, () => applyScenario({ sensors }, ['sensors']));
      editing.delete(draft.id);
      fresh.delete(draft.id);
      tests.delete(draft.id);
      renderList();
      toast(`${draft.name} ${isFresh ? 'added' : 'applied'}. The run restarted from the start position.`);
    } catch (failure) {  // the draft stays
      error.textContent = failure.message;
      toast(failure.message, true);
    }
  });
  return h('form', { class: 'edit', onsubmit: event => event.preventDefault() },
    h('p', { class: 'muted', text: `id ${draft.id} · topic ${TOPIC_PREFIX[draft.type]}/${draft.id}` }),
    parts,
    h('div', { class: 'actions' }, apply, h('button', { type: 'button', onclick: close }, 'Cancel')),
    error,
    h('p', { class: 'note', text: 'Applying restarts the run from the start position.' }));
}

// Cards

function buildCard(sensor, isFresh) {
  const live = isFresh ? null : { camera: liveCamera, tof: liveTof, imu: liveImu }[sensor.type](sensor);
  const dot = h('span', { class: 'dot ok', title: 'ok' });
  const testBox = h('div', { class: 'test' });
  const form = h('div');
  const showTest = () => { clear(testBox, tests.has(sensor.id) ? testResult(tests.get(sensor.id)) : null); };

  const closeForm = () => {
    editing.delete(sensor.id);
    fresh.delete(sensor.id);
    renderList();
  };
  const openForm = () => {
    if (!editing.has(sensor.id)) editing.set(sensor.id, clone(sensor));
    renderList();
  };

  const meta = sensor.type === 'imu'
    ? `at the origin of ${sensor.link} · ${sensor.rate} Hz`
    : `on ${sensor.link} at (${sensor.position.map(v => fixed(v * 100, 1)).join(', ')}) cm · ${sensor.type === 'camera'
      ? `${sensor.width}×${sensor.height}, ${sensor.fov}° field of view, ${sensor.rate} Hz`
      : `range ${distance(sensor.range)}, cone ${sensor.cone}°, ${sensor.rays} rays, ${sensor.rate} Hz`}`;

  const buttons = isFresh ? [] : [
    h('button', { type: 'button', onclick: openForm }, 'Edit'),
    confirmButton('Remove', 'Confirm remove', async () => {
      try {
        await applyScenario({ sensors: store.model.scenario.sensors.filter(other => other.id !== sensor.id) }, ['sensors']);
        toast(`${sensor.name} removed. The run restarted from the start position.`);
      } catch (failure) {
        toast(failure.message, true);
      }
    }),
    h('button', {
      type: 'button',
      onclick: async event => {
        try {
          const result = await withBusy(event.currentTarget, () => post(`/api/hub/modules/${encodeURIComponent(sensor.id)}/test`));
          tests.set(sensor.id, result);
          showTest();
        } catch (failure) {
          toast(failure.message, true);
        }
      },
    }, 'Self-test'),
  ];

  if (editing.has(sensor.id)) clear(form, editForm(editing.get(sensor.id), isFresh, closeForm));
  showTest();
  const el = h('article', { class: 'card', 'data-id': sensor.id },
    h('div', { class: 'card-head' }, dot, h('h4', { text: sensor.name }), h('span', { class: 'chip', text: KIND_LABEL[sensor.type] || sensor.type })),
    h('p', { class: 'meta', text: isFresh ? `${sensor.type} · id ${sensor.id}` : meta }),
    live ? live.el : h('p', { class: 'muted', text: 'Not applied yet: nothing is simulated until you add it.' }),
    buttons.length ? h('div', { class: 'actions' }, buttons) : null,
    testBox,
    form);

  return {
    el,
    update(reading, status) {
      dot.className = 'dot ' + (status === 'error' ? 'error' : 'ok');
      dot.title = status || 'ok';
      if (live && reading) live.update(reading);
    },
  };
}

function renderList() {
  const sensors = store.model.scenario.sensors;
  const ids = new Set(sensors.map(sensor => sensor.id));
  for (const id of [...editing.keys()]) if (!ids.has(id) && !fresh.has(id)) editing.delete(id);
  for (const id of [...tests.keys()]) if (!ids.has(id)) tests.delete(id);
  cards.clear();
  const nodes = sensors.map(sensor => {
    const card = buildCard(sensor, false);
    cards.set(sensor.id, card);
    return card.el;
  });
  for (const id of fresh) nodes.push(buildCard(editing.get(id), true).el);
  clear(list, nodes.length ? nodes : h('p', { class: 'muted', text: 'No sensors.' }));
  if (store.state) showReadings(store.state);
}

function showReadings(state) {
  for (const [id, card] of cards) card.update(state.sensors[id], state.modules && state.modules[id]);
}

export function setSensorsActive(active) {
  if (active && store.state && store.model) showReadings(store.state);
}

export function initSensorsPanel(root) {
  panel = root;
  list = h('div', { class: 'cards' });
  const add = type => h('button', { type: 'button', onclick: () => addSensor(type), 'aria-label': `Add ${KIND_LABEL[type]}` }, `+ ${{ camera: 'Camera', tof: 'ToF', imu: 'IMU' }[type]}`);
  clear(root,
    h('div', { class: 'toolbar-row' }, h('span', { class: 'muted', text: 'Add sensor' }), add('camera'), add('tof'), add('imu')),
    list);
  on('model', keys => { if (touches(keys, 'sensors') || touches(keys, 'robot.model')) renderList(); });
  on('state', state => { if (!panel.hidden) showReadings(state); });
}
