// Robot tab: drive pad with keyboard shortcuts, live telemetry, robot setup, leg design, generated gait with a drawing
// of its walking pattern, servos and the traverse test.
import { h, clear, clone, fixed, numberField, textField, selectField, toast } from './ui.js';
import { get, post, request } from './api.js';
import { store, on, touches, acceptState, applied } from './store.js';
import { makeSection } from './section.js';

const draft = {};
const BUNDLED_BITTLE = '/assets/bittle/bittle.urdf';

// Drive pad layout (3 columns); only keys that the server lists in model.drive are shown, extra ones are appended.
const PAD = [
  ['walk-left', 'Q'], ['walk', 'W'], ['walk-right', 'E'],
  ['spin-left', 'A'], ['stand', 'Space'], ['spin-right', 'D'],
  ['trot', 'T'], ['back', 'S'], ['crawl', ''],
  ['sit', ''], ['rest', ''],
];
const SHORTCUTS = { w: 'walk', s: 'back', a: 'spin-left', d: 'spin-right', q: 'walk-left', e: 'walk-right', t: 'trot', ' ': 'stand' };
// Generated gait: Shift + the same keys.
const GAIT_SHORTCUTS = { w: 'forward', s: 'backward', a: 'spin-left', d: 'spin-right', q: 'left', e: 'right', ' ': 'stance' };
const GAIT_KEYS = Object.fromEntries(Object.entries(GAIT_SHORTCUTS).map(([key, motion]) => [motion, key === ' ' ? '⇧Space' : '⇧' + key.toUpperCase()]));
// Gentle curves on top, sharper arcs in the middle row, spins at the bottom; motions the server adds later are appended.
const GAIT_PAD = ['veer-left', 'forward', 'veer-right', 'left', 'stance', 'right', 'spin-left', 'backward', 'spin-right'];
const GAIT_LABEL = {
  forward: 'Forward', backward: 'Backward', left: 'Arc left', right: 'Arc right', 'veer-left': 'Veer left', 'veer-right': 'Veer right',
  'spin-left': 'Spin left', 'spin-right': 'Spin right', stance: 'Stance',
};
const AXES = [{ value: '+x', label: '+x' }, { value: '-x', label: '-x' }, { value: '+y', label: '+y (Bittle)' }, { value: '-y', label: '-y' }];
const WARN_AT_LIMIT = .2;  // share of the last 2 s at the torque limit above which a servo counts as saturated

const padButtons = new Map();
const gaitButtons = new Map();
const readout = {};
const feet = new Map();
let feetBox = null;
let legsItem = null, gaitItem = null;
let dockNote = null;

const pretty = key => key.charAt(0).toUpperCase() + key.slice(1).replace(/-/g, ' ');
const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
/** The skill name the server reports while a drive command plays: 'kwkF' -> 'wkF', 'd' -> 'rest'. */
const skillOf = command => (command.startsWith('k') ? command.slice(1) : command === 'd' ? 'rest' : command);
const grid = (...fields) => h('div', { class: 'grid2' }, fields);
const num = (target, key, label, unit, options) =>
  numberField({ label, unit, value: target[key], onInput: value => { target[key] = value; }, ...options });

async function command(body) {
  try {
    acceptState(await post('/api/coop/command', body));
  } catch (error) {
    toast(error.message, true);
  }
}

const drive = key => command({ action: 'drive', value: key });
const playGait = motion => command({ action: 'gait', value: motion });

function initKeyboard() {
  document.addEventListener('keydown', event => {
    if (event.ctrlKey || event.metaKey || event.altKey || event.repeat || !store.model) return;
    const target = event.target;
    if (target.closest && target.closest('input, textarea, select, [contenteditable]')) return;
    const letter = event.key.toLowerCase();
    if (letter === ' ' && target.closest && target.closest('button, summary, a')) return;  // Space presses the focused button
    if (event.shiftKey) {
      const motion = GAIT_SHORTCUTS[letter];
      if (!motion || !store.model.robot.gaits || !store.model.gait_motions.includes(motion)) return;
      event.preventDefault();
      playGait(motion);
      return;
    }
    const key = SHORTCUTS[letter];
    if (!key || !(key in store.model.drive)) return;
    event.preventDefault();
    drive(key);
  });
}

// Drive and telemetry

function driveBlock() {
  const pad = h('div', { class: 'pad', id: 'drivePad' });
  on('model', () => {
    const keys = Object.keys(store.model.drive);
    const layout = [...PAD.filter(([key]) => keys.includes(key)), ...keys.filter(key => !PAD.some(([k]) => k === key)).map(key => [key, ''])];
    padButtons.clear();
    clear(pad, layout.map(([key, shortcut]) => {
      const button = h('button', { type: 'button', class: 'pad-button', onclick: () => drive(key) }, pretty(key), shortcut ? h('kbd', { text: shortcut }) : null);
      padButtons.set(key, button);
      return button;
    }));
  });
  return h('section', { class: 'block' },
    h('h3', { text: 'Drive' }),
    pad,
    h('p', { class: 'note', text: 'Keys: W walk, S back, A / D spin, Q / E sidestep, T trot, Space stand. Driving starts the physics if it is paused. These are Petoi\'s own skills, made for the stock legs; for other leg designs use the generated gait (Shift with the same keys).' }));
}

function metric(id, label) {
  readout[id] = h('dd', { text: '–' });
  return h('div', { class: 'metric' }, h('dt', { text: label }), readout[id]);
}

function telemetryBlock() {
  feetBox = h('ul', { class: 'feet', 'aria-label': 'Friction under each foot' });
  return h('section', { class: 'block' },
    h('h3', null, 'Telemetry ', h('span', { class: 'fallen', id: 'fallenBadge', hidden: true, text: 'FALLEN' })),
    h('dl', { class: 'metrics' },
      metric('position', 'Position x, y, z (m)'), metric('heading', 'Heading'),
      metric('tilt', 'Roll / pitch'), metric('height', 'Height above ground'),
      metric('speed', 'Speed'), metric('skill', 'Skill')),
    h('h4', { text: 'Foot friction' }),
    feetBox);
}

function showTelemetry(state) {
  const robot = state.robot;
  readout.position.textContent = `${fixed(robot.position[0], 2)}, ${fixed(robot.position[1], 2)}, ${fixed(robot.position[2], 3)}`;
  readout.heading.textContent = fixed(robot.heading, 1) + '°';
  readout.tilt.textContent = `${fixed(robot.roll, 1)}° / ${fixed(robot.pitch, 1)}°`;
  readout.height.textContent = fixed(robot.height * 100, 1) + ' cm';
  readout.speed.textContent = fixed(robot.speed * 100, 1) + ' cm/s';
  readout.skill.textContent = robot.skill || '–';
  document.getElementById('fallenBadge').hidden = !robot.fallen;

  const ground = store.model.world.terrain.friction;
  for (const [name, friction] of Object.entries(robot.feet || {})) {
    if (!feet.has(name)) {
      const value = h('b');
      const node = h('li', null, h('span', { text: name.replace(/-?(knee-)?link$/, '').replace(/[-_]/g, ' ') }), value);
      feet.set(name, { node, value });
      feetBox.append(node);
    }
    const foot = feet.get(name);
    const muddy = friction < ground - 1e-9;
    foot.value.textContent = fixed(friction, 2) + (muddy ? ' mud' : '');
    foot.node.classList.toggle('mud', muddy);
  }
  for (const [key, button] of padButtons) {
    const playing = robot.skill && store.model.drive[key] && skillOf(store.model.drive[key]) === robot.skill;
    button.classList.toggle('active', Boolean(playing));
  }
  const type = applied().robot.gait.type;
  for (const [motion, button] of gaitButtons) button.classList.toggle('active', robot.skill === `gait-${type}-${motion}`);
  showServo(state);
}

// Setup: model, start pose, payload

function nextPayloadId() {
  const used = new Set(draft.setup.payload.map(item => item.id));
  let n = 1;
  while (used.has(`payload-${n}`)) n++;
  return `payload-${n}`;
}

function modelOptions() {
  const models = store.model.robot_models;
  return models.map(model => ({
    value: model.url,
    label: models.filter(other => other.name === model.name).length > 1 ? `${model.name} (${model.url})` : model.name,
  }));
}

function setupForm(item) {
  const robot = draft.setup, links = store.model.robot.links;
  const linkOptions = links.map(link => ({ value: link, label: link }));

  const x = num(robot.start.position, 0, 'Start X', 'm', { min: -20, max: 20 });
  const y = num(robot.start.position, 1, 'Start Y', 'm', { min: -20, max: 20 });
  const heading = num(robot.start, 'heading', 'Start heading', '°', { min: -360, max: 360 });
  const useCurrent = h('button', {
    type: 'button',
    onclick: () => {
      const current = store.state && store.state.robot;
      if (!current) return toast('The robot position is not known yet', true);
      const round = (value, scale) => Math.round(value * scale) / scale;
      robot.start.position[0] = round(current.position[0], 1000);
      robot.start.position[1] = round(current.position[1], 1000);
      robot.start.heading = round(current.heading, 10);
      x.set(robot.start.position[0]);
      y.set(robot.start.position[1]);
      heading.set(robot.start.heading);
      item.markDirty();
    },
  }, 'Use current pose');

  const payload = robot.payload.map(part => h('div', { class: 'item' },
    h('div', { class: 'item-head' },
      textField({ label: 'Name', value: part.name, onInput: value => { part.name = value; } }),
      h('button', {
        type: 'button', 'aria-label': `Remove ${part.name}`,
        onclick: () => { robot.payload.splice(robot.payload.indexOf(part), 1); item.markDirty(); item.render(); },
      }, 'Remove')),
    h('small', { class: 'muted', text: 'id ' + part.id }),
    h('div', { class: 'grid2' },
      num(part, 'mass', 'Mass', 'g', { scale: 1000, min: 0, max: 2000 }),
      selectField({ label: 'Mounted on link', options: linkOptions, value: part.link, onInput: value => { part.link = value; } }))));

  const mass = h('p', { class: 'note' });
  const showMass = () => {
    const grams = robot.payload.reduce((sum, part) => sum + part.mass * 1000, 0);
    mass.textContent = `Total robot mass as applied: ${fixed(store.model.robot.mass, 3)} kg. Payload in this form: ${fixed(grams, 0)} g.`;
  };

  const form = h('div', null,
    selectField({ label: 'Robot model', options: modelOptions(), value: robot.model, onInput: value => { robot.model = value; } }),
    h('p', { class: 'note', text: 'Another model moves payload and sensors whose link it lacks to its base link. Only the bundled Bittle can have other legs and a generated gait.' }),
    selectField({ label: 'Forward axis of the base link', options: AXES, value: robot.forward_axis, onInput: value => { robot.forward_axis = value; } }),
    h('h4', { text: 'Start pose' }),
    h('div', { class: 'grid2' }, x, y, heading, h('div', { class: 'with-button' }, useCurrent)),
    h('h4', { text: 'Payload' }),
    payload.length ? payload : h('p', { class: 'muted', text: 'No payload.' }),
    h('button', {
      type: 'button', class: 'full',
      onclick: () => {
        robot.payload.push({ id: nextPayloadId(), name: 'Extra module', mass: .01, link: links.includes('base-frame-link') ? 'base-frame-link' : links[0] });
        item.markDirty();
        item.render();
      },
    }, '+ Add payload'),
    mass,
    h('p', { class: 'note', text: 'Payload mass is added to its link: a heavier or higher payload changes how Bittle walks and whether it tips.' }));
  form.addEventListener('input', showMass);
  showMass();
  return form;
}

// Leg design

function builtText() {
  const legs = store.model.robot.legs || {};
  const names = Object.keys(legs);
  if (!names.length) return 'This robot has no legs the leg design can describe.';
  const mean = (list, pick) => (list.length ? list.reduce((sum, name) => sum + pick(legs[name]), 0) / list.length : NaN);
  const mm = value => fixed(value * 1000, 1);
  const front = names.filter(name => name.includes('front')), rear = names.filter(name => name.includes('back'));
  return `As built: upper ${mm(mean(names, leg => leg.upper))} mm, lower ${mm(mean(names, leg => leg.lower))} mm; ` +
    `shoulders at x = ${mm(mean(front, leg => leg.hip[0]))} mm (front) and ${mm(mean(rear, leg => leg.hip[0]))} mm (rear), ` +
    `y = ±${mm(mean(names, leg => Math.abs(leg.hip[1])))} mm, measured from the body origin (x forward, y left).`;
}

const PRESET_HINT = {
  stock: 'Bittle as shipped, with a gait that suits it',
  spider: 'Longer legs, shoulders splayed outward, front shoulders moved forward, with a low wide gait to match',
  crab: 'Long legs, front knees forward and rear knees back, with a crab gait: diagonal pairs of legs, feet lifted straight up and down',
};
const CRAB_REACH = 171;   // mm the crab legs reach ahead of the body centre while walking
const STOP_ENOUGH = .18;  // m: a dock stop block nearer than this stops the crab legs before the capture zone
const STOP_ADVICE = 190;  // mm

function usePreset(name, item) {
  const preset = store.model.leg_presets[name];
  draft['robot.legs'] = clone(preset.legs);
  draft['robot.gait'] = clone(preset.gait);
  item.render();
  item.markDirty();
  gaitItem.render();
  gaitItem.markDirty();
}

/** The crab design reaches further ahead of the body than the stock Bittle: the dock's stop block has to move back. */
function showDockNote() {
  const legs = draft['robot.legs'], gait = draft['robot.gait'];
  if (!dockNote || !legs || !gait) return;  // the gait draft is made right after the legs draft when a model arrives
  const stop = applied().dock.stop_distance;
  const crab = gait.type === 'crab' || legs.front_knees === 'forward' || legs.rear_knees === 'forward';
  dockNote.hidden = !(crab && stop < STOP_ENOUGH);
  dockNote.textContent = dockNote.hidden ? '' : `The crab design reaches about ${CRAB_REACH} mm ahead of the body centre while walking, but the dock's stop block stands `
    + `${fixed(stop * 1000, 0)} mm from the dock position, so the robot would be stopped before it reaches the capture zone. Move the block: Scene → Dock → Stop block distance, about ${STOP_ADVICE} mm.`;
}

function legsForm(item) {
  const legs = draft['robot.legs'], stock = store.model.leg_presets.stock.legs;
  const bundled = applied().robot.model === BUNDLED_BITTLE;
  const field = (key, label, unit, options) => num(legs, key, label, unit, { stock: stock[key], scale: 1000, ...options });
  const names = Object.keys(store.model.leg_presets);
  const presets = names.map(name => h('button', {
    type: 'button', title: PRESET_HINT[name] || '', disabled: !bundled && name !== 'stock',
    onclick: () => usePreset(name, item),
  }, pretty(name)));
  const knees = store.model.choices.knee_directions.map(value => ({ value, label: pretty(value) }));
  dockNote = h('p', { class: 'warning', role: 'status', hidden: true });
  const form = h('div', null,
    h('div', { class: 'preset-row' }, h('span', { class: 'muted', text: 'Preset (legs and gait)' }), presets),
    h('ul', { class: 'limits', style: 'margin-bottom:10px' },
      names.map(name => h('li', null, h('b', { text: pretty(name) }), ' – ' + (PRESET_HINT[name] || 'legs and gait set together')))),
    bundled ? null : h('p', { class: 'warning', text: 'Only the bundled Bittle can have other legs. Choose it in Robot setup first.' }),
    grid(
      field('upper', 'Upper leg', 'mm', { min: 30, max: 150 }), field('lower', 'Lower leg', 'mm', { min: 30, max: 150 }),
      field('splay', 'Shoulder splay', '°', { scale: 1, min: 0, max: 45 }), field('fan', 'Fan angle', '°', { scale: 1, min: 0, max: 45 }),
      field('front_offset', 'Front shoulders forward', 'mm', { min: -30, max: 60 }),
      field('rear_offset', 'Rear shoulders back', 'mm', { min: -30, max: 60 }),
      selectField({ label: 'Front knees', options: knees, value: legs.front_knees, onInput: value => { legs.front_knees = value; showDockNote(); } }),
      selectField({ label: 'Rear knees', options: knees, value: legs.rear_knees, onInput: value => { legs.rear_knees = value; showDockNote(); } })),
    h('p', { class: 'note', text: 'Upper leg: shoulder to knee, lower leg: knee to foot tip, both in the leg plane. Splay tilts the legs outward seen from the front, fan turns them outward seen from above. Positive offsets move the front shoulders forward and the rear shoulders backward.' }),
    h('p', { class: 'note', text: 'Knees: the stock Bittle\'s knees all point backward. "Forward" mounts the lower leg half a turn round, the mirror image, so the knee points ahead.' }),
    dockNote,
    h('p', { class: 'note', text: builtText() }),
    h('p', { class: 'note', text: 'Petoi\'s own gaits are made for stock legs; use the generated gait for other designs. Applying rebuilds the robot (legs and gait are sent together).' }));
  showDockNote();
  return form;
}

// Gait

function gaitForm() {
  const gait = draft['robot.gait'], model = store.model;
  const enabled = model.robot.gaits;
  gaitButtons.clear();
  const buttons = [...GAIT_PAD, ...model.gait_motions.filter(motion => !GAIT_PAD.includes(motion))].map(motion => {
    if (!motion || !model.gait_motions.includes(motion)) return h('span');
    const button = h('button', {
      type: 'button', class: 'pad-button', disabled: !enabled, onclick: () => playGait(motion),
    }, GAIT_LABEL[motion] || pretty(motion), GAIT_KEYS[motion] ? h('kbd', { text: GAIT_KEYS[motion] }) : null);  // veers have no key
    gaitButtons.set(motion, button);
    return button;
  });
  return h('div', null,
    h('div', { class: 'pad' }, buttons),
    h('p', { class: enabled ? 'note' : 'warning', text: enabled
      ? 'Plays the generated gait with the applied settings, so Apply first. Shift with W S A D Q E, and Shift Space for the stance. A veer steers gently, an arc more sharply, a spin turns on the spot. Warnings (for example feet out of reach) appear in the event log.'
      : 'Generated gaits need the bundled Bittle (or a robot with Bittle\'s four legs). They are not available for this model.' }),
    grid(
      selectField({
        label: 'Gait type', options: model.gait_types.map(type => ({ value: type, label: pretty(type) })),
        value: gait.type, onInput: value => { gait.type = value; showDockNote(); },
      }),
      num(gait, 'cycle', 'Cycle', 's', { min: .3, max: 6 }),
      num(gait, 'hip_height', 'Hip height', 'mm', { scale: 1000, min: 20, max: 250 }),
      num(gait, 'stride', 'Stride', 'mm', { scale: 1000, min: 0, max: 150 }),
      num(gait, 'step_height', 'Step height', 'mm', { scale: 1000, min: 0, max: 80 }),
      h('span'),
      num(gait, 'front_reach', 'Front foot reach', 'mm', { scale: 1000, min: -80, max: 120 }),
      num(gait, 'rear_reach', 'Rear foot reach', 'mm', { scale: 1000, min: -80, max: 120 })),
    h('p', { class: 'note', text: 'Hip height: how far the feet stand below the shoulders. Reach moves the standing feet ahead of (+) or behind (-) the shoulders. The crawl lifts one foot at a time, the trot two diagonal feet in an arc, the crab two diagonal feet straight up and straight down.' }));
}

// Walking pattern: the applied gait drawn from the side and animated, with each joint's range against its limits

const SVG_NS = 'http://www.w3.org/2000/svg';
const LEG_COLOR = { front: '#c0e581', rear: '#5ec2ff' };  // the accent and the dock colour of the 3D view
const FOOT_IN_AIR = '#111a22';  // the drawing's background: a foot in the air is drawn hollow
const NEAR_LIMIT = 5;           // degrees from a joint limit that count as close to it
const MM = 1000;

function svgNode(tag, attributes, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attributes || {})) {
    if (value !== null && value !== undefined && value !== false) node.setAttribute(key, value);
  }
  node.append(...children);
  return node;
}

const tenth = value => Math.round(value * 10) / 10;
/** A point [x, z] in body metres (x forward, z up) as "x,y" in the drawing: millimetres, y pointing down. */
const toDrawing = ([x, z]) => `${tenth(x * MM)},${tenth(-z * MM)}`;
const legName = leg => leg.replace(/-/g, ' ');

/** The extent in millimetres (z up) of everything drawn over the whole cycle, and the height of the lowest foot. */
function patternBounds(frames) {
  const bounds = { x0: Infinity, x1: -Infinity, z0: Infinity, z1: -Infinity, ground: Infinity };
  for (const frame of frames) {
    for (const leg of Object.values(frame.legs)) {
      for (const [x, z] of [leg.hip, leg.knee_point, leg.foot]) {
        bounds.x0 = Math.min(bounds.x0, x * MM);
        bounds.x1 = Math.max(bounds.x1, x * MM);
        bounds.z0 = Math.min(bounds.z0, z * MM);
        bounds.z1 = Math.max(bounds.z1, z * MM);
      }
      bounds.ground = Math.min(bounds.ground, leg.foot[1] * MM);
    }
  }
  return bounds;
}

/** The side view: ground, body, the traced foot paths and one hip-knee-foot line per leg (moved later by showFrame). */
function drawPattern(data) {
  const b = patternBounds(data.frames);
  const left = b.x0 - 14, right = b.x1 + 14, top = b.z1 + 12, bottom = Math.min(b.ground - 18, b.z0 - 4);
  const first = data.frames[0].legs, names = Object.keys(first);
  const hips = names.map(name => first[name].hip);
  const svg = svgNode('svg', {
    viewBox: `${tenth(left)} ${tenth(-top)} ${tenth(right - left)} ${tenth(top - bottom)}`, role: 'img',
    'aria-label': `Side view of the ${data.type} gait, motion ${legName(data.motion)}, front to the right. The joint table below gives the same information as numbers.`,
  });
  svg.style.cssText = 'display:block;width:100%;height:auto;background:var(--input);border:1px solid var(--line);border-radius:6px';
  const label = (content, x, y, anchor) => svgNode('text', {
    x: tenth(x), y: tenth(y), 'text-anchor': anchor, fill: '#95a5b2', 'font-size': 7.5, 'font-family': 'Segoe UI, sans-serif',
  }, content);
  const hipX = hips.map(point => point[0] * MM), hipY = -hips[0][1] * MM;
  svg.append(
    svgNode('rect', { x: tenth(left), y: tenth(-b.ground), width: tenth(right - left), height: tenth(b.ground - bottom), fill: '#22303a' }),
    svgNode('line', { x1: tenth(left), y1: tenth(-b.ground), x2: tenth(right), y2: tenth(-b.ground), stroke: '#4f606c', 'stroke-width': 1 }),
    label('ground', right - 4, -b.ground + 10, 'end'),
    label('front →', right - 4, -top + 9, 'end'),
    svgNode('line', { x1: tenth(left + 6), y1: tenth(-bottom - 5), x2: tenth(left + 56), y2: tenth(-bottom - 5), stroke: '#95a5b2', 'stroke-width': 1 }),
    label('50 mm', left + 6, -bottom - 8, 'start'),
    svgNode('line', {
      x1: tenth(Math.min(...hipX)), y1: tenth(hipY), x2: tenth(Math.max(...hipX)), y2: tenth(hipY),
      stroke: '#4a5a66', 'stroke-width': 8, 'stroke-linecap': 'round',
    }));

  const parts = new Map();
  const traces = [], lines = [], dots = [];
  const order = [...names].sort((a, c) => Number(c.startsWith('right')) - Number(a.startsWith('right')));  // right legs under the left ones
  for (const name of order) {
    const color = name.includes('front') ? LEG_COLOR.front : LEG_COLOR.rear, onRight = name.startsWith('right');
    if (data.frames.length > 1) {
      const path = data.frames.map(frame => toDrawing(frame.legs[name].foot));
      traces.push(svgNode('polyline', {
        points: [...path, path[0]].join(' '), fill: 'none', stroke: color, 'stroke-opacity': .35, 'stroke-width': 1, 'stroke-dasharray': onRight ? '2 2' : null,
      }));
    }
    const leg = svgNode('polyline', {
      fill: 'none', stroke: color, 'stroke-width': 2.4, 'stroke-linecap': 'round', 'stroke-linejoin': 'round',
      'stroke-opacity': onRight ? .65 : 1, 'stroke-dasharray': onRight ? '5 3' : null,
    });
    const knee = svgNode('circle', { r: 1.8, fill: color });
    const foot = svgNode('circle', { r: 3.2, stroke: color, 'stroke-width': 1.4, 'stroke-opacity': onRight ? .75 : 1 });
    lines.push(leg);
    dots.push(knee, foot);
    parts.set(name, { leg, knee, foot, color });
  }
  const shoulders = [...new Set(hips.map(toDrawing))].map(point => {
    const [x, y] = point.split(',');
    return svgNode('circle', { cx: x, cy: y, r: 2.4, fill: '#d3dde4' });
  });
  svg.append(...traces, ...lines, ...dots, ...shoulders);
  return { svg, parts };
}

/** Angle range over the cycle against the limits, one row per joint; rows within NEAR_LIMIT degrees of a limit are flagged. */
function rangeTable(data) {
  const rows = Object.entries(data.ranges).map(([joint, [low, high]]) => {
    const [lower, upper] = data.limits[joint] || [-Infinity, Infinity];
    const beyond = low < lower - 1e-6 || high > upper + 1e-6;
    const flag = beyond ? 'beyond its limit' : low - lower < NEAR_LIMIT || upper - high < NEAR_LIMIT ? `within ${NEAR_LIMIT}° of its limit` : '';
    return h('tr', { class: flag ? 'warn' : '', title: flag ? `This joint is ${flag}` : '' },
      h('th', { scope: 'row' }, flag ? h('span', { 'aria-hidden': 'true', text: '⚠ ' }) : null, legName(joint.replace(/-joint$/, '')),
        flag ? h('span', { class: 'sr-only', text: ` (${flag})` }) : null),
      h('td', { class: 'num', text: `${fixed(low, 1)} to ${fixed(high, 1)}` }),
      h('td', { class: 'num', text: `${fixed(lower, 0)} to ${fixed(upper, 0)}` }));
  });
  return h('div', { class: 'table-wrap' },
    h('table', { class: 'servo pattern' },
      h('caption', { class: 'sr-only', text: 'Angle of each joint over one step cycle, against its limits, in degrees' }),
      h('thead', null, h('tr', null, h('th', { scope: 'col', text: 'Joint' }), h('th', { scope: 'col', text: 'Range (°)' }), h('th', { scope: 'col', text: 'Limits (°)' }))),
      h('tbody', null, rows)));
}

function patternBlock() {
  const view = {
    motion: 'forward', data: null, error: null, phase: 0, token: 0,
    playing: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,  // no moving picture for those who ask for none
  };
  let parts = new Map(), shown = -1, motionKey = '';
  const motionBox = h('div');
  const message = h('p', { class: 'muted', hidden: true });
  const info = h('p', { class: 'muted' });
  const drawing = h('div');
  const play = h('button', { type: 'button' });
  const slider = h('input', { type: 'range', min: 0, max: 0, step: 1, value: 0 });
  const phaseValue = h('em', { text: ' 0 %' });
  const warning = h('p', { class: 'warning', role: 'status', hidden: true });
  const tables = h('div');
  const content = h('div', { hidden: true },
    info, drawing,
    h('div', { class: 'with-button' }, play, h('label', { class: 'field' }, h('span', { class: 'field-label' }, 'Phase', phaseValue), slider)),
    h('p', { class: 'note', text: 'Seen from the left, front to the right, in millimetres. Left legs are solid, right legs dashed; front legs green, rear legs blue. A filled foot is on the ground, a hollow one in the air; the faint loops are the paths of the feet.' }),
    warning, tables);
  const el = h('details', { class: 'group', open: true },
    h('summary', { text: 'Walking pattern' }),
    h('div', { class: 'group-body' },
      motionBox, message, content,
      h('p', { class: 'note', text: 'Shows the gait as applied, to try other angles and strides: change the settings above, press Apply, and the drawing follows. It plays at the real speed of one step cycle.' })));

  const syncPlay = () => { play.textContent = view.playing ? '❚❚ Pause' : '▶ Play'; };

  /** Move the legs to the frame at the current phase (nothing happens while the frame is the one already shown). */
  function showFrame() {
    const data = view.data;
    if (!data) return;
    const count = data.frames.length, index = Math.min(count - 1, Math.floor(view.phase * count));
    if (index === shown) return;
    shown = index;
    const frame = data.frames[index];
    for (const [name, part] of parts) {
      const leg = frame.legs[name];
      part.leg.setAttribute('points', [leg.hip, leg.knee_point, leg.foot].map(toDrawing).join(' '));
      for (const [circle, point] of [[part.knee, leg.knee_point], [part.foot, leg.foot]]) {
        circle.setAttribute('cx', tenth(point[0] * MM));
        circle.setAttribute('cy', tenth(-point[1] * MM));
      }
      part.foot.setAttribute('fill', leg.stance ? part.color : FOOT_IN_AIR);
    }
    slider.value = index;
    phaseValue.textContent = ` ${Math.round(index / count * 100)} %`;
  }

  function render() {
    const { data, error } = view;
    content.hidden = !data;
    message.hidden = !error;
    if (error) {
      message.className = error.status === 400 ? 'muted' : 'error-text';
      message.textContent = error.status === 400 ? error.message : 'Could not load the walking pattern: ' + error.message;
    }
    if (!data) return;
    const drawn = drawPattern(data);
    parts = drawn.parts;
    shown = -1;
    clear(drawing, drawn.svg);
    const still = data.frames.length < 2;  // the stance is one frame
    if (still) view.phase = 0;
    slider.max = data.frames.length - 1;
    slider.disabled = play.disabled = still;
    info.textContent = still ? `${pretty(data.type)} gait · standing still`
      : `${pretty(data.type)} gait · one step cycle takes ${fixed(data.cycle, 2)} s · each foot is on the ground for ${Math.round(data.duty * 100)} % of it`;
    warning.hidden = !data.unreachable.length;
    warning.textContent = data.unreachable.length
      ? `Out of reach during the step: ${data.unreachable.map(legName).join(', ')}. Shorten the stride or the step height, or change the hip height or the reach.` : '';
    clear(tables,
      h('h4', { text: 'Joint angles' }),
      rangeTable(data),
      h('h4', { text: 'Knees point' }),
      h('dl', { class: 'metrics' }, Object.keys(data.frames[0].legs).map(leg => h('div', { class: 'metric' },
        h('dt', { text: legName(leg) }), h('dd', { text: data.knees[leg] || '–' })))));
    showFrame();
  }

  async function load() {
    const token = ++view.token;  // an answer to an older request must not replace a newer one
    try {
      const data = await get('/api/coop/gait-preview?motion=' + encodeURIComponent(view.motion));
      if (token !== view.token) return;
      view.data = data;
      view.error = null;
    } catch (failure) {  // for example a robot without Bittle's legs: HTTP 400
      if (token !== view.token) return;
      view.data = null;
      view.error = failure;
    }
    render();
  }

  play.addEventListener('click', () => {
    view.playing = !view.playing;
    syncPlay();
  });
  slider.addEventListener('input', () => {
    if (!view.data) return;
    view.playing = false;  // scrubbing takes over from the animation
    syncPlay();
    view.phase = (Number(slider.value) + .5) / view.data.frames.length;
    showFrame();
  });
  syncPlay();

  let last = 0;
  const tick = now => {
    requestAnimationFrame(tick);
    const dt = Math.min((now - last) / 1000, .1);
    last = now;
    const data = view.data;
    if (!view.playing || !data || data.frames.length < 2 || !el.open || !el.offsetParent) return;  // closed or on a hidden tab: idle
    view.phase = (view.phase + dt / data.cycle) % 1;
    showFrame();
  };
  requestAnimationFrame(tick);

  on('model', () => {  // other legs or another gait may have been applied
    const motions = store.model.gait_motions;
    if (motions.join(',') !== motionKey) {
      motionKey = motions.join(',');
      if (!motions.includes(view.motion)) view.motion = motions[0];
      clear(motionBox, selectField({
        label: 'Motion', options: motions.map(motion => ({ value: motion, label: GAIT_LABEL[motion] || pretty(motion) })),
        value: view.motion, onInput: value => { view.motion = value; load(); },
      }));
    }
    load();
  });
  return el;
}

// Servos

let servoBody = null, servoLimit = null, servoEmpty = null;
let servoRows = new Map();

function servoForm() {
  const servo = draft['robot.servo'];
  servoRows = new Map();
  servoBody = h('tbody');
  servoLimit = h('p', { class: 'muted' });
  servoEmpty = h('tr', null, h('td', { colspan: 4, class: 'muted', text: 'No readings yet: press Run or drive.' }));
  servoBody.append(servoEmpty);
  const form = h('div', null,
    grid(num(servo, 'torque', 'Torque limit', 'Nm', { min: .02, max: 5, step: .01 }), num(servo, 'speed', 'Speed', '°/s', { min: 30, max: 2000 })),
    h('p', { class: 'warning', text: 'The default torque, 0.29 Nm (3 kg·cm), is a retailer figure for Bittle\'s servos that Petoi does not confirm. Treat it as an assumption and try other values.' }),
    h('h4', { text: 'Load on each joint' }),
    servoLimit,
    h('div', { class: 'table-wrap' },
      h('table', { class: 'servo' },
        h('thead', null, h('tr', null, h('th', { scope: 'col', text: 'Joint' }), h('th', { scope: 'col', text: 'Torque now (Nm)' }), h('th', { scope: 'col', text: 'Mean (Nm)' }), h('th', { scope: 'col', text: 'At limit' }))),
        servoBody)));
  if (store.state) showServo(store.state);
  return form;
}

function servoRow(name) {
  const fill = h('i'), latest = h('span'), mean = h('td', { class: 'num' }), limit = h('td', { class: 'num' });
  const row = h('tr', null,
    h('th', { scope: 'row', text: name.replace(/-joint$/, '').replace(/[-_]/g, ' ') }),
    h('td', null, h('span', { class: 'bar' }, fill), latest), mean, limit);
  servoBody.append(row);
  return { row, fill, latest, mean, limit };
}

function showServo(state) {
  const servo = state.robot.servo;
  if (!servoBody || !servo) return;
  servoLimit.textContent = `Limit ${fixed(servo.limit, 3)} Nm per joint. "At limit" is the share of the last 2 s spent at 98 % of it or more; above ${Math.round(WARN_AT_LIMIT * 100)} % the servo is saturated.`;
  const joints = Object.entries(servo.joints || {});
  servoEmpty.hidden = joints.length > 0;
  for (const [name, load] of joints) {
    if (!servoRows.has(name)) servoRows.set(name, servoRow(name));
    const cells = servoRows.get(name);
    const share = load.at_limit * 100;
    cells.fill.style.width = clamp(load.torque / servo.limit, 0, 1) * 100 + '%';
    cells.latest.textContent = fixed(load.torque, 3);
    cells.mean.textContent = fixed(load.mean, 3);
    cells.limit.textContent = (load.at_limit > WARN_AT_LIMIT ? '⚠ ' : '') + fixed(share, 0) + ' %';
    cells.row.classList.toggle('warn', load.at_limit > WARN_AT_LIMIT);
  }
}

// Traverse test

const TRAVERSE_COLUMNS = [
  ['Dist.', 'cm', run => fixed(run.distance * 100, 1)],
  ['Speed', 'cm/s', run => fixed(run.speed * 100, 1)],
  ['Side', 'cm', run => fixed(run.sideways * 100, 1)],
  ['Turn', '°', run => fixed(run.turned, 0)],
  ['Falls', '', run => String(run.falls)],
  ['At limit', '%', run => fixed(run.at_limit_share * 100, 0)],
  ['Mud', '%', run => fixed(run.mud_share * 100, 0)],
  ['Stone', '%', run => fixed(run.stone_share * 100, 0)],
  ['Mass', 'g', run => fixed(run.mass * 1000, 0)],
];

function courseText(results) {
  const course = results.course;
  const patches = course.mud_patches;
  return `Course: ${results.seconds} s from (${fixed(results.start[0], 2)}, ${fixed(results.start[1], 2)}) m along heading ${fixed(results.heading, 0)}°; ` +
    `roughness ${fixed(course.roughness * 1000, 0)} mm, ${patches} mud patch${patches === 1 ? '' : 'es'}, ${course.stones} stone${course.stones === 1 ? '' : 's'}, ` +
    `servo torque ${fixed(course.servo.torque, 2)} Nm.`;
}

function resultsTable(results) {
  const runs = results.runs.filter(run => !run.error);
  const best = runs.length ? runs.reduce((a, b) => (b.distance > a.distance ? b : a)) : null;
  const rows = results.runs.map(run => {
    if (run.error) {
      return h('tr', { class: 'failed' }, h('th', { scope: 'row', text: run.name }), h('td', { colspan: TRAVERSE_COLUMNS.length, class: 'error-text', text: 'Could not run: ' + run.error }));
    }
    const isBest = run === best;
    return h('tr', { class: isBest ? 'best' : '' },
      h('th', { scope: 'row' }, isBest ? h('span', { class: 'star', title: 'furthest', text: '★ ' }) : null, run.name,
        isBest ? h('span', { class: 'sr-only', text: ' (furthest)' }) : null,
        run.stopped_at_edge ? h('small', { text: 'stopped at the terrain edge' }) : null),
      TRAVERSE_COLUMNS.map(([, , value]) => h('td', { class: 'num', title: run.fallen_share ? `Down for ${fixed(run.fallen_share * 100, 0)} % of the run` : '', text: value(run) })));
  });
  const warnings = results.runs.flatMap(run => (run.warnings || []).map(text => `${run.name}: ${text}`));
  return h('div', null,
    h('div', { class: 'table-wrap' },
      h('table', { class: 'traverse' },
        h('thead', null, h('tr', null, h('th', { scope: 'col', text: 'Design' }),
          TRAVERSE_COLUMNS.map(([name, unit]) => h('th', { scope: 'col' }, name, unit ? h('small', { text: unit }) : null)))),
        h('tbody', null, rows))),
    warnings.length ? h('ul', { class: 'warnings' }, warnings.map(text => h('li', { text }))) : null);
}

const JOB_POLL_MS = 1000;
const JOB_POLL_FAILURES = 5;  // unanswered polls in a row before the page stops asking
const JOB_RESULT_POLLS = 30;  // polls to wait for the result of a job whose runs are all in
const CANCELLED = 'The traverse test was cancelled. Designs that had already started walking finish in the background.';

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
/** The last line of a Python traceback is the error itself. */
const lastLine = text => String(text || '').trim().split('\n').pop();

/** The test runs as a job on the server (one worker process per design); the block polls it once a second. */
function traverseBlock() {
  let seconds = 30;
  let results = null;
  let job = null;  // the test being followed: {id}
  const output = h('div', { class: 'traverse-output', 'aria-live': 'polite' });
  const error = h('p', { class: 'form-error' });
  const outcome = h('p', { class: 'muted', role: 'status' });
  const status = h('p', { class: 'muted' });
  const fill = h('i');
  const bar = h('span', {
    class: 'bar wide', role: 'progressbar', 'aria-label': 'Traverse test progress', 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-valuenow': 0,
  }, fill);
  const cancel = h('button', { type: 'button' }, 'Cancel');
  const progress = h('div', { hidden: true }, status, bar, h('div', { style: 'margin-top:8px' }, cancel));
  const run = h('button', { type: 'button', class: 'primary' }, 'Run traverse test');
  const showResults = () => clear(output, results ? [h('p', { class: 'muted', text: courseText(results) }), resultsTable(results)] : null);

  const setBusy = busy => {
    run.disabled = busy;
    run.textContent = busy ? 'Running…' : 'Run traverse test';
    progress.hidden = !busy;
    cancel.disabled = false;
  };
  const showProgress = state => {
    const share = Math.round((state.progress || 0) * 100);
    status.textContent = `${state.done} of ${state.total} runs done · ${fixed(state.elapsed, 0)} s`;
    fill.style.width = share + '%';
    bar.setAttribute('aria-valuenow', share);
  };
  /** The test is over or lost: back to idle, with the problem if there was one. */
  const end = (mine, problem) => {
    if (job !== mine) return;
    job = null;
    setBusy(false);
    if (problem) {
      error.textContent = problem;
      toast(problem, true);
    }
  };

  async function follow(id) {
    const mine = job = { id };
    setBusy(true);
    let failures = 0, waited = 0;
    while (job === mine) {
      let state = null;
      try {
        state = await get('/api/coop/jobs/' + id);
        failures = 0;
      } catch (failure) {
        if (failure.status === 400 || ++failures >= JOB_POLL_FAILURES) return end(mine, failure.message);  // 400: the job is gone
      }
      if (job !== mine) return;
      if (state) {
        showProgress(state);
        if (state.status === 'error') return end(mine, 'The traverse test failed: ' + lastLine(state.error));
        if (state.status === 'cancelled') {
          outcome.textContent = CANCELLED;
          return end(mine);
        }
        if (state.status === 'done') {
          if (state.result) {  // the status turns to done a moment before the server has put the result together
            try {
              results = state.result;
              showResults();
            } catch (failure) {
              return end(mine, 'The result could not be shown: ' + failure.message);
            }
            return end(mine);
          }
          if (++waited > JOB_RESULT_POLLS) return end(mine, 'The test finished, but the server returned no result');
        }
      }
      await sleep(JOB_POLL_MS);
    }
  }

  run.addEventListener('click', async () => {
    if (!(seconds >= 5 && seconds <= 120)) {
      error.textContent = 'A traverse test lasts 5 to 120 simulated seconds.';
      return;
    }
    error.textContent = '';
    outcome.textContent = '';
    setBusy(true);
    status.textContent = 'Starting…';
    fill.style.width = '0%';
    try {
      follow((await post('/api/coop/jobs/traverse', { seconds })).job);
    } catch (failure) {
      setBusy(false);
      error.textContent = failure.message;
      toast(failure.message, true);
    }
  });
  cancel.addEventListener('click', async () => {
    const mine = job;
    if (!mine) return;
    cancel.disabled = true;
    try {
      await request('/api/coop/jobs/' + mine.id, 'DELETE');
    } catch (failure) {
      cancel.disabled = false;
      toast(failure.message, true);
      return;
    }
    outcome.textContent = CANCELLED;
    end(mine);
  });

  // A page opened (or reloaded) while a test runs follows it instead of letting a second one start.
  get('/api/coop/jobs').then(list => {
    const running = list.find(item => item.kind === 'traverse' && item.status === 'running');
    if (running && !job) follow(running.id);
  }).catch(() => {});  // the server may not be up yet: then there is nothing to follow

  return h('details', { class: 'group' },
    h('summary', { text: 'Traverse test' }),
    h('div', { class: 'group-body' },
      h('p', { class: 'note', text: 'Stock legs with Petoi\'s walk, stock legs and spider legs with the generated crawl, crab legs with the crab gait, and the current design if it is none of these presets, walk the same course: your terrain, mud and stones, from the start pose along the start heading. Each design runs in a worker process of its own, side by side, in a separate world: the simulation above is not disturbed.' }),
      h('div', { class: 'with-button' },
        numberField({ label: 'Simulated seconds', unit: 's', value: seconds, min: 5, max: 120, onInput: value => { seconds = value; } }), run),
      progress, outcome, error, output,
      h('p', { class: 'note', text: 'Results depend on how well each gait is tuned: try a few gait settings before concluding that a design is better or worse.' })));
}

// Panel

export function initRobotPanel(root) {
  const setup = makeSection({
    title: 'Robot setup', draft, name: 'setup', build: setupForm,
    keys: ['robot.model', 'robot.forward_axis', 'robot.start', 'robot.payload'],
    extraSend: () => (draft.setup.model !== applied().robot.model ? ['sensors'] : []),  // a new model can move sensors to another link
    read: scenario => { const r = scenario.robot; return clone({ model: r.model, forward_axis: r.forward_axis, start: r.start, payload: r.payload }); },
    write: (scenario, value) => Object.assign(scenario.robot, value),
  });
  legsItem = makeSection({
    title: 'Leg design', draft, name: 'robot.legs', open: true, build: legsForm,
    send: ['robot.legs', 'robot.gait'],  // a preset fills both, so both go together
    write: (scenario, value) => { scenario.robot.legs = value; scenario.robot.gait = clone(draft['robot.gait']); },
    note: 'Applying rebuilds the robot and restarts the run from the start position.',
  });
  gaitItem = makeSection({ title: 'Gait', draft, name: 'robot.gait', open: true, build: gaitForm });
  const servos = makeSection({ title: 'Servos', draft, name: 'robot.servo', build: servoForm });
  const sections = [setup, legsItem, gaitItem, servos];

  clear(root, driveBlock(), telemetryBlock(), legsItem.el, gaitItem.el, patternBlock(), servos.el, traverseBlock(), setup.el);
  on('model', keys => {
    const otherRobot = touches(keys, 'robot.model');
    if (otherRobot) {  // other joints and feet; the generated gait may no longer exist
      feet.clear();
      feetBox.replaceChildren();
      servoRows.clear();
      if (servoBody) servoBody.replaceChildren(servoEmpty);
    }
    for (const item of sections) {
      if (item.keys.some(key => touches(keys, key))) item.reset();
      else if (otherRobot && (item === legsItem || item === gaitItem)) item.render();  // keep the edits, refresh what depends on the model
    }
    showDockNote();  // the dock's stop block may have moved
  });
  on('state', showTelemetry);
  initKeyboard();
}
