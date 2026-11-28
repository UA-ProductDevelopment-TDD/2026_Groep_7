// Small DOM and HTTP helpers. Text always goes in through textContent.

export const $ = (selector, root = document) => root.querySelector(selector);

const PROPERTIES = new Set(['value', 'checked', 'disabled', 'selected', 'hidden']);

/** h('button', {class: 'primary', onclick: fn}, 'Tekst', childNode) */
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
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  for (const [key, value] of later) node[key] = value;  // after the children: a select needs its options first
  return node;
}

export const clear = (node, ...children) => { node.replaceChildren(); node.append(...children.flat(Infinity).filter(Boolean)); return node; };

let toastTimer = 0;
export function toast(message, isError = false) {
  const node = $('#toast');
  node.textContent = message;
  node.className = 'show' + (isError ? ' error' : '');
  node.setAttribute('role', isError ? 'alert' : 'status');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { node.className = ''; }, isError ? 7000 : 3000);
}

/** fetch with JSON in and out; errors carry the server's Dutch `detail`. */
export async function api(path, method = 'GET', body) {
  const options = { method };
  if (body !== undefined) {
    options.headers = { 'Content-Type': 'application/json' };
    options.body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new Error('Het platform antwoordt niet. Draait het nog?');
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail || `Fout ${response.status}`);
  return data;
}

export const round = (value, digits = 0) => Number(value.toFixed(digits));

/** Dutch names of the joints, in the order of the sliders. */
export const JOINT_NAMES = {
  'neck-joint': 'Nek',
  'left-front-shoulder-joint': 'Linksvoor · schouder', 'left-front-knee-joint': 'Linksvoor · knie',
  'right-front-shoulder-joint': 'Rechtsvoor · schouder', 'right-front-knee-joint': 'Rechtsvoor · knie',
  'left-back-shoulder-joint': 'Linksachter · schouder', 'left-back-knee-joint': 'Linksachter · knie',
  'right-back-shoulder-joint': 'Rechtsachter · schouder', 'right-back-knee-joint': 'Rechtsachter · knie',
};
export const JOINTS = Object.keys(JOINT_NAMES);
export const LEGS = [['left-front', 'Linksvoor'], ['right-front', 'Rechtsvoor'], ['left-back', 'Linksachter'], ['right-back', 'Rechtsachter']];
