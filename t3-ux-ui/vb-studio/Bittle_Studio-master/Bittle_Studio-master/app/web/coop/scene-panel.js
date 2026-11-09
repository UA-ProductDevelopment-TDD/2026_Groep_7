// Left panel: terrain, mud, stones, coop, dock, day and night, chickens and visitors. Edits stay in a local draft until the
// section's own Apply button; Apply sends the whole scenario (see store.applyScenario) and keeps the draft if the server refuses it.
import { h, clear, clone, numberField, textField, selectField, toast } from './ui.js';
import { store, on, touches } from './store.js';
import { makeSection } from './section.js';

const SAMPLE_LIMIT = 250000;
const MAX_VISITORS = 10;
const MIN_POINTS = 2, MAX_POINTS = 50;  // points in a visitor's path
const ID_PATTERN = /^[a-z0-9][a-z0-9_-]{0,39}$/;  // the same rule as the server's: ids become hub topics
const draft = {};        // scenario key -> local copy being edited
const sections = [];
const auto = new WeakSet();  // visitors added in this draft whose id still follows their name
let view = null;         // the 3D viewport, for picking points on the ground
let picking = null;      // {token, stop} of the point picking that is running

const pretty = key => key.charAt(0).toUpperCase() + key.slice(1).replace(/-/g, ' ');
const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
const round2 = value => Math.round(value * 100) / 100;

const num = (target, key, label, unit, options = {}) =>
  numberField({ label, unit, value: target[key], onInput: value => { target[key] = value; }, ...options });

function section(options) {
  const item = makeSection({ ...options, draft });
  sections.push(item);
  return item.el;
}

const grid = (...fields) => h('div', { class: 'grid2' }, fields);

/** A seed box with a dice button that picks a random seed. */
function seedField(target) {
  const seed = num(target, 'seed', 'Seed', '', { min: 0, max: 2147483647, integer: true });
  const dice = h('button', {
    type: 'button', class: 'icon', title: 'Pick a random seed', 'aria-label': 'Pick a random seed',
    onclick: () => {
      seed.set(Math.floor(Math.random() * 2147483647));
      seed.querySelector('input').dispatchEvent(new Event('input', { bubbles: true }));
    },
  }, '🎲');
  return h('div', { class: 'with-button' }, seed, dice);
}

// Terrain

function terrainForm() {
  const t = draft.terrain;
  const samples = h('p', { class: 'note' });
  const update = () => {
    const nx = Math.round(t.size[0] / t.resolution) + 1, ny = Math.round(t.size[1] / t.resolution) + 1;
    const total = nx * ny;
    samples.textContent = Number.isFinite(total)
      ? `${nx} × ${ny} = ${total.toLocaleString('en')} height samples (at most ${SAMPLE_LIMIT.toLocaleString('en')})` : '';
    samples.classList.toggle('warn', total > SAMPLE_LIMIT);
  };
  const form = h('div', null,
    grid(
      num(t.size, 0, 'Size X', 'm', { min: 2, max: 40 }), num(t.size, 1, 'Size Y', 'm', { min: 2, max: 40 }),
      num(t, 'resolution', 'Resolution', 'cm', { scale: 100, min: 2, max: 50 }),
      num(t, 'roughness', 'Roughness', 'mm', { scale: 1000, min: 0, max: 100 }),
      num(t, 'feature_size', 'Bump size', 'm', { min: .05, max: 5 }),
      seedField(t),
      num(t, 'friction', 'Ground friction', '', { min: 0, max: 3 }),
      num(t, 'flat_margin', 'Flat margin', 'm', { min: 0, max: 3 })),
    samples,
    h('p', { class: 'note', text: 'Roughness is the standard deviation of the bumps; the flat margin keeps the ground level around the fenced run and the dock.' }));
  form.addEventListener('input', update);
  update();
  return form;
}

// Mud

function nextMudId() {
  const used = new Set(draft.mud.map(patch => patch.id));
  let n = 1;
  while (used.has(`mud-${n}`)) n++;
  return `mud-${n}`;
}

function mudForm(item) {
  const patches = draft.mud;
  const cards = patches.map(patch => h('div', { class: 'item' },
    h('div', { class: 'item-head' },
      textField({ label: 'Name', value: patch.name, onInput: value => { patch.name = value; } }),
      h('button', {
        type: 'button', 'aria-label': `Remove ${patch.name}`,
        onclick: () => { patches.splice(patches.indexOf(patch), 1); item.markDirty(); item.render(); },
      }, 'Remove')),
    h('small', { class: 'muted', text: 'id ' + patch.id }),
    grid(
      num(patch.center, 0, 'Centre X', 'm', { min: -20, max: 20 }), num(patch.center, 1, 'Centre Y', 'm', { min: -20, max: 20 }),
      num(patch, 'radius', 'Radius', 'm', { min: .05, max: 10 }), num(patch, 'friction', 'Friction', '', { min: 0, max: 3 }),
      num(patch, 'depth', 'Depth', 'mm', { scale: 1000, min: 0, max: 100 }))));
  return h('div', null,
    cards.length ? cards : h('p', { class: 'muted', text: 'No mud patches.' }),
    h('button', {
      type: 'button', class: 'full',
      onclick: () => {
        const id = nextMudId();
        patches.push({ id, name: 'Mud patch ' + id.slice(4), center: [1, -1], radius: .4, friction: .35, depth: .01 });
        item.markDirty();
        item.render();
      },
    }, '+ Add mud patch'),
    h('p', { class: 'note', text: 'Friction replaces the ground friction under the feet. Depth is how far the patch dips below the ground.' }));
}

// Stones

let stonesNote = null;

/** How many of the applied stones found a free place; the terrain, coop or dock can change that without touching stones. */
function stonesText() {
  const placed = store.model.world.boxes.filter(box => box.kind === 'stone').length;
  return `Loose stones, sunk a third into the ground. They are scattered outside the fenced run and kept clear of the dock and the robot's start. Placed now: ${placed} of ${store.model.scenario.stones.count}.`;
}

const STONE_AREA = [-2, -2.6, 2.2, -1.1];  // a band along the patrol line south of the fence, offered when "Whole terrain" is unticked

function stonesForm(item) {
  const s = draft.stones;
  stonesNote = h('p', { class: 'note', text: stonesText() });
  const whole = h('input', { type: 'checkbox', checked: !s.area });  // area stays null while ticked
  whole.addEventListener('change', () => {
    s.area = whole.checked ? null : clone(STONE_AREA);
    item.render();
  });
  return h('div', null,
    grid(
      num(s, 'count', 'Number of stones', '', { min: 0, max: 500, integer: true }), seedField(s),
      num(s, 'min_size', 'Smallest stone', 'mm', { scale: 1000, min: 5, max: 200 }),
      num(s, 'max_size', 'Largest stone', 'mm', { scale: 1000, min: 5, max: 200 })),
    h('label', { class: 'check' }, whole, 'Whole terrain'),
    s.area ? grid(
      num(s.area, 0, 'Area x from', 'm', { min: -20, max: 20 }), num(s.area, 1, 'Area y from', 'm', { min: -20, max: 20 }),
      num(s.area, 2, 'Area x to', 'm', { min: -20, max: 20 }), num(s.area, 3, 'Area y to', 'm', { min: -20, max: 20 })) : null,
    s.area ? h('p', { class: 'note', text: 'Stones stay inside this rectangle (x from < x to, y from < y to), clipped to the terrain.' }) : null,
    stonesNote);
}

// Coop and dock

function coopForm() {
  const c = draft.coop;
  return h('div', null,
    grid(
      num(c.position, 0, 'Position X', 'm', { min: -20, max: 20 }), num(c.position, 1, 'Position Y', 'm', { min: -20, max: 20 }),
      num(c, 'yaw', 'Yaw', '°', { min: -360, max: 360 }), h('span'),
      num(c.run_size, 0, 'Run size X', 'm', { min: .5, max: 20 }), num(c.run_size, 1, 'Run size Y', 'm', { min: .5, max: 20 }),
      num(c, 'fence_height', 'Fence height', 'm', { min: .05, max: 3 }), num(c, 'post_spacing', 'Post spacing', 'm', { min: .1, max: 5 }),
      num(c.house_size, 0, 'House size X', 'm', { min: .1, max: 10 }), num(c.house_size, 1, 'House size Y', 'm', { min: .1, max: 10 }),
      num(c.house_size, 2, 'House size Z', 'm', { min: .1, max: 10 })),
    h('p', { class: 'note', text: 'The house stands inside the run against its -x fence and must fit in it.' }));
}

function dockForm() {
  const d = draft.dock;
  return h('div', null,
    grid(
      num(d.position, 0, 'Position X', 'm', { min: -20, max: 20 }), num(d.position, 1, 'Position Y', 'm', { min: -20, max: 20 }),
      num(d, 'yaw', 'Yaw', '°', { min: -360, max: 360 }), h('span'),
      num(d, 'capture_distance', 'Capture distance', 'mm', { scale: 1000, min: 1, max: 500 }),
      num(d, 'capture_angle', 'Capture angle', '°', { min: .1, max: 90 }),
      num(d, 'stop_distance', 'Stop block distance', 'mm', { scale: 1000, min: 30, max: 500 })),
    h('p', { class: 'note', text: 'Yaw is the heading of the docked robot (0° faces +x, 90° faces +y). The robot latches when its origin is within the capture distance and its heading within the capture angle.' }),
    h('p', { class: 'note', text: 'The stop block distance (from the dock position) must be more than the robot reaches ahead of its body centre: 113 mm for the stock Bittle, 171 mm for the crab legs while walking. Otherwise the block stops the robot before it is in the capture zone. The behaviour self-test checks it.' }));
}

// Day and night

function environmentForm() {
  const e = draft.environment;
  const ir = h('input', { type: 'checkbox', checked: e.ir_light });
  ir.addEventListener('change', () => { e.ir_light = ir.checked; });
  return h('div', null,
    grid(
      selectField({
        label: 'Time of day', options: store.model.choices.times_of_day.map(value => ({ value, label: pretty(value) })),
        value: e.time_of_day, onInput: value => { e.time_of_day = value; },
      }),
      num(e, 'moonlight', 'Moonlight', '%', { scale: 100, min: 0, max: 100 }),
      num(e, 'ir_range', 'Infrared range', 'm', { min: .1, max: 20 })),
    h('label', { class: 'check' }, ir, 'Infrared light next to the camera'),
    h('p', { class: 'note', text: 'At night the camera sees moonlight only (a share of daylight), plus what the infrared LEDs light up within their range. The colour-blob detector needs colour, so it fails in infrared light. The LEDs use extra power while they are on.' }));
}

// Chickens

function chickensForm() {
  const c = draft.chickens;
  return h('div', null,
    grid(
      num(c, 'inside', 'Chickens inside the run', '', { min: 0, max: 30, integer: true }),
      num(c, 'outside', 'Chickens outside the run', '', { min: 0, max: 30, integer: true }),
      num(c, 'speed', 'Speed', 'cm/s', { scale: 100, min: 0, max: 200 }),
      seedField(c)),
    h('p', { class: 'note', text: 'Chickens wander on their own and never push the robot. Those inside peck about the run; the others walk a band 15 cm to 1 m outside the fence, away from the dock, and get in the robot\'s way. Speed 0 keeps them standing. The same seed gives the same walk.' }));
}

// Visitors

/** An id from a name: lower case, other characters turned into "-", and not one that another visitor has. */
function idFromName(name, taken, fallback) {
  const base = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+/, '').slice(0, 36).replace(/-+$/, '') || fallback;
  let id = base, n = 2;
  while (taken.includes(id)) id = `${base}-${n++}`;
  return id;
}

function nextName(kind) {
  const base = pretty(kind), used = new Set(draft.visitors.map(visitor => visitor.name));
  let name = base, n = 2;
  while (used.has(name)) name = `${base} ${n++}`;
  return name;
}

/** A fox or a person with a short path along the north or north-east side of the run, to be edited. */
function newVisitor(kind) {
  const { terrain, coop } = store.model.scenario;
  const [ex, ey] = terrain.size.map(size => size / 2 - .3);
  const [cx, cy] = coop.position, [hx, hy] = coop.run_size.map(size => size / 2);
  const pin = (x, y) => [round2(clamp(x, -ex, ex)), round2(clamp(y, -ey, ey))];
  const name = nextName(kind), fox = kind === 'fox';
  return {
    id: idFromName(name, draft.visitors.map(visitor => visitor.id), kind), kind, name, appear: fox ? 40 : 120, speed: fox ? .3 : .9,
    loop: fox, flee_distance: fox ? 1 : 0,
    path: fox ? [pin(cx + hx + 2, cy + hy + 2), pin(cx + hx + .5, cy + hy + .5)] : [pin(cx - hx - 2, cy + hy + 1), pin(cx + hx + 2, cy + hy + 1)],
  };
}

const stopPick = () => { if (picking) picking.stop(); };

/** The points of one visitor's path: x and y boxes per point, add and remove, and picking points on the ground. */
function pathEditor(visitor, item) {
  const path = visitor.path;
  const rows = h('div');
  const add = h('button', { type: 'button' }, '+ Add point');
  const pick = h('button', { type: 'button', 'aria-pressed': 'false', disabled: !view || !view.pick }, 'Pick points on the ground');
  const done = h('button', { type: 'button', hidden: true }, 'Done');

  const draw = () => {
    clear(rows, path.map((point, n) => h('div', { class: 'with-button', role: 'group', 'aria-label': `Point ${n + 1}` },
      h('span', { class: 'muted', text: n + 1 }),
      num(point, 0, 'x', 'm', { min: -20, max: 20, hint: false }), num(point, 1, 'y', 'm', { min: -20, max: 20, hint: false }),
      h('button', {
        type: 'button', 'aria-label': `Remove point ${n + 1}`, title: path.length <= MIN_POINTS ? 'A path needs at least 2 points' : 'Remove this point',
        disabled: path.length <= MIN_POINTS,
        onclick: () => { path.splice(n, 1); item.markDirty(); draw(); },
      }, '✕'))));
    add.disabled = path.length >= MAX_POINTS;
  };
  const showPicking = on => {
    pick.setAttribute('aria-pressed', on);
    done.hidden = !on;
  };

  add.addEventListener('click', () => {
    const last = path[path.length - 1] || [0, 0];
    path.push([clamp(round2(last[0] + .5), -20, 20), round2(last[1])]);
    item.markDirty();
    draw();
  });
  pick.addEventListener('click', () => {
    stopPick();
    const token = {};
    const stop = view.pick(point => {
      if (path.length >= MAX_POINTS) {
        toast(`A path has at most ${MAX_POINTS} points`, true);
        stop();
        return;
      }
      path.push(point);
      item.markDirty();
      draw();
    }, `Click the ground to add points to the path of ${visitor.name || 'this visitor'} · Esc or Done to stop`, () => {
      if (picking && picking.token === token) picking = null;
      showPicking(false);
    });
    picking = { token, stop };
    showPicking(true);
  });
  done.addEventListener('click', stopPick);

  draw();
  return h('div', null,
    rows,
    h('div', { class: 'preset-row' }, add, pick, done),
    h('p', { class: 'note', text: `World x and y in metres, ${MIN_POINTS} to ${MAX_POINTS} points. The visitor appears at the first point and walks them in order. Points you click show in the 3D view while you pick; they count once you apply the visitors.` }));
}

function visitorCard(visitor, item) {
  const others = () => draft.visitors.filter(other => other !== visitor).map(other => other.id);
  const idNote = h('small', { class: 'muted', text: 'Lower-case letters, digits, - and _' });
  const checkId = () => {
    const problem = !ID_PATTERN.test(visitor.id) ? 'Use 1-40 lower-case letters, digits, - or _' : others().includes(visitor.id) ? 'Another visitor already has this id' : '';
    idNote.textContent = problem || 'Lower-case letters, digits, - and _';
    idNote.className = problem ? 'error-text' : 'muted';
    idNote.setAttribute('role', problem ? 'alert' : 'note');
  };
  const idField = textField({
    label: 'Id', value: visitor.id, maxlength: 40,
    onInput: value => { visitor.id = value; auto.delete(visitor); checkId(); },
  });
  const flee = num(visitor, 'flee_distance', 'Flee distance', 'm', { min: 0, max: 10 });
  flee.hidden = visitor.kind !== 'fox';  // a person never runs off
  const loop = h('input', { type: 'checkbox', checked: visitor.loop });
  loop.addEventListener('change', () => { visitor.loop = loop.checked; });
  checkId();

  return h('div', { class: 'item' },
    h('div', { class: 'item-head' },
      textField({
        label: 'Name', value: visitor.name,
        onInput: value => {
          visitor.name = value;
          if (auto.has(visitor)) {
            visitor.id = idFromName(value, others(), visitor.kind);
            idField.set(visitor.id);
            checkId();
          }
        },
      }),
      h('button', {
        type: 'button', 'aria-label': `Remove ${visitor.name}`,
        onclick: () => { draft.visitors.splice(draft.visitors.indexOf(visitor), 1); item.markDirty(); item.render(); },
      }, 'Remove')),
    grid(
      selectField({
        label: 'Kind', options: store.model.choices.visitor_kinds.map(kind => ({ value: kind, label: pretty(kind) })), value: visitor.kind,
        onInput: value => {
          visitor.kind = value;
          if (value !== 'fox') visitor.flee_distance = 0;
          else if (!(visitor.flee_distance > 0)) { visitor.flee_distance = 1; flee.set(1); }
          flee.hidden = value !== 'fox';
        },
      }),
      idField),
    idNote,
    grid(
      num(visitor, 'appear', 'Appears at', 's', { min: 0, max: 86400 }),
      num(visitor, 'speed', 'Speed', 'cm/s', { scale: 100, min: 2, max: 500 }),
      flee),
    h('label', { class: 'check' }, loop, 'Walks back and forth'),
    h('h4', { text: 'Path' }),
    pathEditor(visitor, item));
}

function visitorsForm(item) {
  stopPick();  // the cards are about to be replaced, and a pick would add points to the old ones
  const visitors = draft.visitors;
  const full = visitors.length >= MAX_VISITORS;
  const add = kind => {
    const visitor = newVisitor(kind);
    auto.add(visitor);
    visitors.push(visitor);
    item.markDirty();
    item.render();
  };
  return h('div', null,
    visitors.length ? visitors.map(visitor => visitorCard(visitor, item)) : h('p', { class: 'muted', text: 'No visitors.' }),
    h('div', { class: 'preset-row' },
      h('button', { type: 'button', disabled: full, title: full ? `At most ${MAX_VISITORS} visitors` : '', onclick: () => add('fox') }, '+ Add fox'),
      h('button', { type: 'button', disabled: full, title: full ? `At most ${MAX_VISITORS} visitors` : '', onclick: () => add('person') }, '+ Add person')),
    h('p', { class: 'note', text: `Foxes and people walk their path from their appear time (simulated seconds). A fox runs off when the robot, deterring, comes within its flee distance; a person never does. Without "walks back and forth" a visitor leaves at the end of its path. ${visitors.length} of ${MAX_VISITORS} visitors.` }));
}

export function initScenePanel(root, viewport) {
  view = viewport;
  clear(root,
    h('div', { class: 'panel-heading' }, h('h2', { text: 'Scene' }), h('span', { class: 'caption', text: 'METRES · DEGREES' })),
    section({ title: 'Terrain', name: 'terrain', open: true, build: terrainForm }),
    section({ title: 'Mud patches', name: 'mud', open: true, build: mudForm }),
    section({ title: 'Stones', name: 'stones', build: stonesForm }),
    section({ title: 'Coop', name: 'coop', build: coopForm }),
    section({ title: 'Dock', name: 'dock', build: dockForm }),
    section({ title: 'Day and night', name: 'environment', build: environmentForm }),
    section({ title: 'Chickens', name: 'chickens', build: chickensForm }),
    section({ title: 'Visitors', name: 'visitors', build: visitorsForm }));
  on('model', applied => {
    for (const item of sections) if (item.keys.some(key => touches(applied, key))) item.reset();
    if (stonesNote) stonesNote.textContent = stonesText();
  });
}
