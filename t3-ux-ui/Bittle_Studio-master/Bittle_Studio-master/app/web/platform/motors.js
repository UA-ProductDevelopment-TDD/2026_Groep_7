// Motoren: which servo drives which joint, which way it turns and where its zero is, per robot model.
// The crab legs have their lower front legs mounted the other way round, so their knees may need the other direction:
// "Test" wiggles one servo so you can see which leg moves and which way.
import { h, clear, toast, api, JOINT_NAMES, JOINTS } from './ui.js';

const WIGGLE = 15;  // degrees a test moves a servo, there and back

export function initMotors(root, { robot, getModel, getPose, onLayout }) {
  let layouts = {}, draft = null, dirty = false;
  const table = h('tbody');
  const saveButton = h('button', { type: 'button', class: 'primary', onclick: save }, 'Opslaan');
  const title = h('p', { class: 'note' });

  function markDirty() {
    dirty = true;
    saveButton.textContent = 'Opslaan ●';
    onLayout(draft);  // try it at once; Opslaan keeps it
  }

  function row(joint) {
    const entry = draft[joint];
    const servo = h('select', { 'aria-label': `Servo van ${JOINT_NAMES[joint]}` },
      Array.from({ length: 16 }, (_, i) => h('option', { value: i, text: i })));
    servo.value = entry.servo;
    servo.addEventListener('change', () => { entry.servo = Number(servo.value); markDirty(); });
    const sign = h('button', { type: 'button', title: 'Draairichting omkeren', 'aria-label': `Richting van ${JOINT_NAMES[joint]}`, text: entry.sign > 0 ? '+' : '−' });
    sign.addEventListener('click', () => { entry.sign = -entry.sign; sign.textContent = entry.sign > 0 ? '+' : '−'; markDirty(); });
    const offset = h('input', { type: 'number', min: -90, max: 90, step: 1, value: entry.offset, 'aria-label': `Nulpunt van ${JOINT_NAMES[joint]} (graden)` });
    offset.addEventListener('change', () => {
      const value = Number(offset.value);
      if (Number.isFinite(value) && value >= -90 && value <= 90) { entry.offset = value; markDirty(); } else offset.value = entry.offset;
    });
    const test = h('button', { type: 'button', title: 'Beweegt alleen deze servo even heen en terug', onclick: () => wiggle(joint) }, 'Test');
    return h('tr', null, h('th', { scope: 'row', text: JOINT_NAMES[joint] }), h('td', null, servo), h('td', null, sign), h('td', null, offset), h('td', null, test));
  }

  async function wiggle(joint) {
    if (!robot.connected) return toast('Verbind eerst de robot.', true);
    const entry = draft[joint];
    const base = robot.toServo(joint, getPose()[joint] ?? 0) ?? 0;
    try {
      await robot.command(`i ${entry.servo} ${base + WIGGLE}`);
      await new Promise(resolve => setTimeout(resolve, 450));
      await robot.command(`i ${entry.servo} ${base}`);
    } catch (error) {
      toast(error.message, true);
    }
  }

  function render() {
    draft = structuredClone(layouts[getModel()]);
    dirty = false;
    saveButton.textContent = 'Opslaan';
    title.textContent = `Model: ${getModel() === 'crab' ? 'krabpoten' : 'Bittle (standaard)'}. Servo = gewrichtshoek × richting + nulpunt.`;
    clear(table, JOINTS.filter(joint => draft[joint]).map(row));
  }

  async function save() {
    try {
      layouts[getModel()] = await api(`/api/layouts/${getModel()}`, 'PUT', draft);
      toast('Motor-indeling opgeslagen.');
      render();
      onLayout(layouts[getModel()]);
    } catch (error) {
      toast(error.message, true);
    }
  }

  clear(root,
    h('h3', { text: 'Motor-indeling' }), title,
    h('table', { class: 'layout-table' },
      h('thead', null, h('tr', null, ['Gewricht', 'Servo', 'Richting', 'Nulpunt °', ''].map(text => h('th', { scope: 'col', text })))),
      table),
    h('div', { class: 'row' }, saveButton,
      h('button', { type: 'button', onclick: () => { render(); onLayout(draft); } }, 'Ongedaan maken')),
    h('p', { class: 'note', text: 'Werkwijze: verbind de robot, klik "Test" bij een gewricht en kijk welke poot beweegt. Klopt de poot niet, kies dan een ander servonummer. Draait hij de verkeerde kant op ten opzichte van de 3D-robot, keer de richting om. Staat de poot in de nulstand (Besturen → Nulstand) niet recht, pas dan het nulpunt aan.' }),
    h('p', { class: 'note', text: 'Bittle\'s nummers: 0 = nek, 8-11 = schouders (linksvoor, rechtsvoor, rechtsachter, linksachter), 12-15 = knieën in dezelfde volgorde.' }));

  return {
    async load() {
      layouts = await api('/api/layouts');
      render();
      return layouts;
    },
    modelChanged: () => { render(); return draft; },
    current: () => draft,
  };
}
