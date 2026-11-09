// Small DOM helpers shared by the panels. Text always goes in through textContent: names can come from outside modules.

export const $ = (selector, root = document) => root.querySelector(selector);

const PROPERTIES = new Set(['value', 'checked', 'disabled', 'selected', 'hidden']);

function append(node, children) {
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

/** h('button', {class: 'primary', onclick: fn}, 'Text', childNode) */
export function h(tag, props, ...children) {
  const node = document.createElement(tag);
  const later = [];
  for (const [key, value] of Object.entries(props || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === 'class') node.className = value;
    else if (key === 'text') node.textContent = value;
    else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else if (PROPERTIES.has(key)) later.push([key, value]);
    else node.setAttribute(key, value === true ? '' : value);
  }
  append(node, children);
  for (const [key, value] of later) node[key] = value;  // after the children: a select needs its options first
  return node;
}

export const clear = (node, ...children) => { node.replaceChildren(); append(node, children); return node; };

export function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

// Numbers

/** Fixed digits, or an en dash for anything that is not a number. */
export function fixed(value, digits = 2) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '–';
  const text = value.toFixed(digits);
  return /^-0(\.0*)?$/.test(text) ? text.slice(1) : text;  // not "-0" for a tiny negative number
}

/** A value for an input box without floating point noise (0.012 * 1000 shows as 12). */
export const shown = value => (typeof value === 'number' && Number.isFinite(value) ? String(+value.toPrecision(12)) : '');

export const clean = value => +value.toPrecision(12);

// Messages

let toastTimer = 0;

export function toast(message, isError = false) {
  const node = $('#toast');
  node.textContent = message;
  node.className = 'show' + (isError ? ' error' : '');
  node.setAttribute('role', isError ? 'alert' : 'status');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { node.className = ''; }, isError ? 8000 : 3200);
}

/** Run a task with the button disabled meanwhile. */
export async function withBusy(button, task) {
  button.disabled = true;
  try {
    return await task();
  } finally {
    button.disabled = false;
  }
}

/** A button that must be pressed twice within three seconds. */
export function confirmButton(label, confirmLabel, onConfirm, props = {}) {
  let timer = 0;
  const button = h('button', {
    type: 'button', class: props.class || 'danger', title: props.title,
    onclick: () => {
      if (timer) {
        clearTimeout(timer);
        timer = 0;
        button.textContent = label;
        onConfirm(button);
      } else {
        button.textContent = confirmLabel;
        timer = setTimeout(() => { timer = 0; button.textContent = label; }, 3000);
      }
    },
  }, label);
  return button;
}

/** A self-test result from the hub: verdict, duration and one line per check. */
export function testResult(result) {
  return h('div', { class: 'test-result ' + (result.ok ? 'pass' : 'fail') },
    h('p', { class: 'test-summary' }, result.ok ? '✓ Self-test passed' : '✗ Self-test failed', ` · ${fixed(result.duration_ms, 1)} ms`),
    h('ul', { class: 'checks' }, result.checks.map(check => h('li', { class: check.ok ? 'pass' : 'fail' },
      h('span', { class: 'mark', 'aria-hidden': 'true', text: check.ok ? '✓' : '✗' }),
      h('span', { class: 'sr-only', text: check.ok ? 'passed: ' : 'failed: ' }),
      h('span', null, check.name, check.detail ? h('small', { text: check.detail }) : null)))));
}

// Form fields. Each returns a <label> with .set(value) to change the shown value from outside.

/**
 * A number field. The scenario holds metres, degrees and kilograms; `scale` converts to the unit shown
 * (cm: 100, mm: 1000, g: 1000) and min/max are given in the shown unit. `stock` (scenario units) adds the stock
 * value to the hint under the box.
 */
export function numberField({ label, unit, value, scale = 1, min, max, step = 'any', integer = false, onInput, hint = true, stock }) {
  const input = h('input', { type: 'number', step: integer ? 1 : step, min, max, inputmode: 'decimal' });
  const range = min !== undefined && max !== undefined ? `${min} – ${max}` : '';
  const note = [stock === undefined ? '' : `stock ${shown(stock * scale)}`, range].filter(Boolean).join(' · ');
  const field = h('label', { class: 'field' },
    h('span', { class: 'field-label' }, label, unit ? h('em', { text: unit }) : null),
    input,
    hint && note ? h('small', { text: note }) : null);
  field.set = v => { input.value = shown(v * scale); };
  field.set(value);
  input.addEventListener('input', () => {
    // An empty or half-typed box becomes NaN, which the server rejects by name ("... must be a number").
    onInput(input.value.trim() === '' ? NaN : clean(Number(input.value) / scale));
  });
  return field;
}

export function textField({ label, value, onInput, maxlength = 80, readonly = false, placeholder }) {
  const input = h('input', { type: 'text', maxlength, value, readonly, placeholder, spellcheck: 'false' });
  input.addEventListener('input', () => onInput(input.value));
  const field = h('label', { class: 'field' }, h('span', { class: 'field-label' }, label), input);
  field.set = v => { input.value = v; };
  return field;
}

/** options: [{value, label}]; a current value that is not listed is added so that nothing is silently changed. */
export function selectField({ label, options, value, onInput }) {
  const list = options.some(option => option.value === value) ? options : [...options, { value, label: String(value) }];
  const select = h('select', { value }, list.map(option => h('option', { value: option.value, text: option.label })));
  select.value = value;
  select.addEventListener('change', () => onInput(select.value));
  const field = h('label', { class: 'field' }, h('span', { class: 'field-label' }, label), select);
  field.set = v => { select.value = v; };
  return field;
}

/** Tabs and panels: role/aria wiring, arrow keys, calls onChange(name). */
export function tabs(list, panels, onChange) {
  const buttons = [...list.querySelectorAll('[role=tab]')];
  const select = (name, focus = false) => {
    for (const button of buttons) {
      const on = button.dataset.tab === name;
      button.setAttribute('aria-selected', on);
      button.tabIndex = on ? 0 : -1;
      if (on && focus) button.focus();
    }
    for (const panel of panels) panel.hidden = panel.dataset.tab !== name;
    onChange(name);
  };
  buttons.forEach((button, index) => {
    button.addEventListener('click', () => select(button.dataset.tab));
    button.addEventListener('keydown', event => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
      if (step) select(buttons[(index + step + buttons.length) % buttons.length].dataset.tab, true);
    });
  });
  select(buttons[0].dataset.tab);
  return select;
}
