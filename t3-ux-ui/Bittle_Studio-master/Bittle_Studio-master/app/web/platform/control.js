// Besturen: drive pad and postures (Petoi's own skills, played by the robot and shown by the 3D robot), and a slider
// per joint. Sliders move the 3D robot; with "Robot volgt" on, the real robot takes the same pose.
import { h, clear, toast, JOINT_NAMES, LEGS } from './ui.js';

const GAITS = [['wk', 'Wandelen'], ['tr', 'Draven'], ['cr', 'Kruipen'], ['vt', 'Ter plaatse']];
// [label, icon, command builder]: the gait code goes in where it differs per gait; turns and stop are fixed.
const PAD = [
  ['Vooruit links', '↖', g => `k${g}L`], ['Vooruit', '↑', g => `k${g}F`], ['Vooruit rechts', '↗', g => `k${g}R`],
  ['Draai links', '⟲', () => 'kvtL'], ['Stop', '■', () => 'kbalance'], ['Draai rechts', '⟳', () => 'kvtR'],
  ['Achteruit links', '↙', () => 'kbkL'], ['Achteruit', '↓', () => 'kbk'], ['Achteruit rechts', '↘', () => 'kbkR'],
];
const KEYS = { ArrowUp: 1, w: 1, ArrowDown: 7, s: 7, ArrowLeft: 3, a: 3, ArrowRight: 5, d: 5, ' ': 4, q: 0, e: 2 };
const POSTURES = [['kbalance', 'Balans'], ['kup', 'Rechtop'], ['ksit', 'Zitten'], ['krest', 'Rusten'], ['kstr', 'Strekken'],
  ['kbuttUp', 'Achterwerk op'], ['kzero', 'Nulstand'], ['kcalib', 'Kalibratie'], ['khi', 'Hallo']];

export function initControl(root, { twin, robot, playSkill, onManualPose }) {
  let gait = 'wk';
  const sliders = {};

  async function run(command, label) {
    try {
      await playSkill(command, label);
    } catch (error) {
      toast(error.message, true);
    }
  }

  const pad = h('div', { class: 'pad' }, PAD.map(([label, icon, build], index) => h('button', {
    type: 'button', title: label, 'aria-label': label, 'data-index': index,
    onclick: () => run(build(gait), label),
  }, icon, h('small', { text: label.replace('Vooruit ', '').replace('Achteruit ', 'achter ') }))));
  const gaitSelect = h('select', { 'aria-label': 'Gang', onchange: () => { gait = gaitSelect.value; } },
    GAITS.map(([code, label]) => h('option', { value: code, text: label })));

  document.addEventListener('keydown', event => {
    // Not while typing, and not while working on the map (its own keys move and delete items there).
    if (event.target.closest('input, select, textarea, [contenteditable], #mapPanel') || event.ctrlKey || event.metaKey || event.altKey) return;
    const index = KEYS[event.key];
    if (index === undefined || root.closest('[role=tabpanel]')?.hidden) return;
    event.preventDefault();
    pad.querySelector(`[data-index="${index}"]`).click();
  });

  const postures = h('div', { class: 'grid3' }, POSTURES.map(([command, label]) => h('button', {
    type: 'button', onclick: () => run(command, label),
  }, label)));

  const motors = h('div', { class: 'grid2' },
    h('button', { type: 'button', title: 'Servo\'s weer aan, in de laatst gelezen houding', onclick: () => robotOnly('#on', 'Motoren aan') }, 'Motoren aan'),
    h('button', { type: 'button', class: 'danger', title: 'Rusthouding en daarna alle servo\'s uit (slap)', onclick: () => robotOnly('d', 'Motoren uit') }, 'Motoren uit'));

  async function robotOnly(command, label) {
    if (!robot.connected) return toast('Verbind eerst de robot.', true);
    try {
      await robot.command(command);
      toast(label);
    } catch (error) {
      toast(error.message, true);
    }
  }

  // Sliders, grouped per leg.
  const sliderBox = h('div');
  function slider(joint, [lower, upper]) {
    const value = h('b', { text: '0°' });
    const input = h('input', { type: 'range', min: Math.ceil(lower), max: Math.floor(upper), step: 1, value: 0, 'aria-label': JOINT_NAMES[joint] });
    const number = h('input', { type: 'number', min: Math.ceil(lower), max: Math.floor(upper), step: 1, value: 0, 'aria-label': JOINT_NAMES[joint] + ' (graden)' });
    const set = angle => {
      twin.stop();
      twin.setPose({ [joint]: angle });
      onManualPose(twin.pose());
    };
    input.addEventListener('input', () => set(Number(input.value)));
    number.addEventListener('change', () => set(Number(number.value)));
    sliders[joint] = angle => {
      const rounded = Math.round(angle);
      input.value = rounded;
      if (document.activeElement !== number) number.value = rounded;
      value.textContent = `${rounded}°`;
    };
    const short = JOINT_NAMES[joint].split(' · ').pop();
    return h('div', { class: 'joint' }, h('label', null, short, value), input, number);
  }

  function buildSliders(limits) {
    const legs = LEGS.map(([key, label]) => h('fieldset', { class: 'leg' }, h('legend', { text: label }),
      ['shoulder', 'knee'].map(part => `${key}-${part}-joint`).filter(joint => limits[joint]).map(joint => slider(joint, limits[joint]))));
    const neck = limits['neck-joint'] ? h('fieldset', { class: 'leg' }, h('legend', { text: 'Hoofd' }), slider('neck-joint', limits['neck-joint'])) : null;
    clear(sliderBox, neck, ...legs);
  }

  const zero = h('button', {
    type: 'button', onclick: () => {
      twin.stop();
      twin.setPose(Object.fromEntries(Object.keys(sliders).map(joint => [joint, 0])));
      onManualPose(twin.pose());
    },
  }, 'Alles op 0°');

  clear(root,
    h('h3', { text: 'Rijden' }),
    h('div', { class: 'row spread' }, h('span', { class: 'note', text: 'Gang' }), gaitSelect),
    pad,
    h('p', { class: 'note', text: 'Toetsen: pijlen of W A S D, spatie = stop, Q en E schuin vooruit.' }),
    h('h3', { text: 'Houdingen' }), postures,
    h('h3', { text: 'Motoren' }), motors,
    h('div', { class: 'row spread' }, h('h3', { text: 'Gewrichten' }), zero),
    h('p', { class: 'note', text: 'Elke schuif zet één gewricht van de 3D-robot. Met "Robot volgt" aan neemt de echte robot dezelfde houding aan.' }),
    sliderBox);

  return {
    setLimits: buildSliders,
    showPose(pose) {
      for (const [joint, angle] of Object.entries(pose)) sliders[joint]?.(angle);
    },
  };
}
