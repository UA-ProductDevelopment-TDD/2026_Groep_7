// Hub tab: every module with status, settings, limitations and self-test; the latest message per topic.
import { h, clear, fixed, testResult, toast, withBusy } from './ui.js';
import { get, post } from './api.js';

const COMMAND = '.venv\\Scripts\\python.exe app\\coop\\examples\\external_monitor.py';
const MODULE_POLL_MS = 2000;
const TOPIC_POLL_MS = 1000;

const items = new Map();  // module id -> {el, update(module)}
let moduleBox = null, topicsBody = null, summary = null, moduleNote = null, topicNote = null;
let stopModules = null, stopTopics = null;

/** Run `task` again a moment after it finished, until the returned function is called. */
function repeat(task, delay) {
  let stopped = false, timer = 0;
  const run = async () => {
    await task();
    if (!stopped) timer = setTimeout(run, delay);
  };
  run();
  return () => { stopped = true; clearTimeout(timer); };
}

function formatValue(value) {
  if (value === null || value === undefined) return '–';
  if (Array.isArray(value)) return value.map(formatValue).join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  if (typeof value === 'number') return String(+value.toPrecision(6));
  return String(value);
}

// Modules

function moduleItem(first) {
  let current = first, signature = '';
  const dot = h('span', { class: 'dot' });
  const name = h('span', { class: 'module-name' });
  const kind = h('span', { class: 'chip' });
  const outside = h('span', { class: 'badge', text: 'outside', title: 'Runs outside the simulator and joined over HTTP', hidden: true });
  const verdict = h('span', { class: 'verdict' });
  const body = h('div', { class: 'module-body', hidden: true });
  const statusText = h('span', { class: 'status-text' });
  const toggle = h('button', { type: 'button', class: 'disclose', 'aria-expanded': 'false' }, dot, name, statusText, kind, outside, verdict);
  const test = h('button', { type: 'button' }, 'Run self-test');
  const el = h('li', { class: 'module' }, h('div', { class: 'module-row' }, toggle, test), body);

  const setOpen = open => {
    body.hidden = !open;
    toggle.setAttribute('aria-expanded', open);
    if (open) fill();
  };
  toggle.addEventListener('click', () => setOpen(body.hidden));
  test.addEventListener('click', async () => {
    try {
      await withBusy(test, () => post(`/api/hub/modules/${encodeURIComponent(current.id)}/test`));
      setOpen(true);
      await refreshModules();
    } catch (error) {
      toast(error.message, true);
    }
  });

  function fill() {
    const next = JSON.stringify(current);
    if (next === signature) return;
    signature = next;
    const config = Object.entries(current.config || {});
    clear(body,
      h('p', { class: 'muted' },
        `Status: ${current.status}`, current.external ? ` · last heard from ${fixed(current.last_seen_s, 1)} s ago` : ''),
      h('h4', { text: 'Settings' }),
      config.length ? h('dl', { class: 'config' }, config.map(([key, value]) =>
        h('div', null, h('dt', { text: key.replace(/_/g, ' ') }), h('dd', { text: formatValue(value) })))) : h('p', { class: 'muted', text: 'None reported.' }),
      h('h4', { text: 'Does not model' }),
      current.limitations.length ? h('ul', { class: 'limits' }, current.limitations.map(text => h('li', { text }))) : h('p', { class: 'muted', text: 'Nothing listed.' }),
      h('h4', { text: 'Topics' }),
      h('p', null, h('span', { class: 'muted', text: 'Publishes ' }), topicChips(current.publishes),
        h('span', { class: 'muted', text: ' Subscribes ' }), topicChips(current.subscribes)),
      h('h4', { text: 'Last self-test' }),
      current.last_test ? testResult(current.last_test) : h('p', { class: 'muted', text: 'Not run yet.' }));
  }

  return {
    el,
    update(module) {
      current = module;
      const status = module.status || 'ok';
      dot.className = 'dot ' + status;
      dot.title = status;
      statusText.textContent = status;
      statusText.className = 'status-text ' + status;
      name.textContent = module.name;
      kind.textContent = module.kind;
      outside.hidden = !module.external;
      const last = module.last_test;
      verdict.textContent = last ? (last.ok ? '✓ test passed' : '✗ test failed') : '';
      verdict.className = 'verdict ' + (last ? (last.ok ? 'pass' : 'fail') : '');
      if (!body.hidden) fill();
    },
  };
}

const topicChips = topics => (topics.length
  ? h('span', { class: 'chips' }, topics.map(topic => h('code', { text: topic })))
  : h('span', { class: 'muted', text: 'none' }));

async function refreshModules() {
  try {
    const modules = await get('/api/hub/modules');
    moduleNote.textContent = '';
    const ids = modules.map(module => module.id);
    for (const id of [...items.keys()]) if (!ids.includes(id)) items.delete(id);
    for (const module of modules) {
      if (!items.has(module.id)) items.set(module.id, moduleItem(module));
      items.get(module.id).update(module);
    }
    const order = ids.map(id => items.get(id).el);
    if (order.length !== moduleBox.children.length || order.some((node, n) => moduleBox.children[n] !== node)) clear(moduleBox, order);
  } catch (error) {
    moduleNote.textContent = 'Cannot read the module list: ' + error.message;
  }
}

async function runAll(button) {
  try {
    const results = await withBusy(button, () => post('/api/hub/test-all'));
    const failed = results.filter(result => !result.ok);
    summary.textContent = `${results.length - failed.length} of ${results.length} modules pass` +
      (failed.length ? `. Failed: ${failed.map(result => result.module).join(', ')}` : '');
    summary.className = 'summary ' + (failed.length ? 'fail' : 'pass');
    await refreshModules();
  } catch (error) {
    toast(error.message, true);
  }
}

// Topics

function compact(value, depth = 0) {
  if (value === null || value === undefined) return 'null';
  if (typeof value === 'number') return String(+value.toPrecision(4));
  if (typeof value === 'string') return value.length > 60 ? value.slice(0, 57) + '…' : value;
  if (typeof value !== 'object') return String(value);
  if (Array.isArray(value)) {
    return '[' + value.slice(0, 4).map(item => compact(item, depth + 1)).join(', ') + (value.length > 4 ? `, … ${value.length} items` : '') + ']';
  }
  if (depth > 0) return '{…}';
  const keys = Object.keys(value);
  return keys.slice(0, 6).map(key => `${key}: ${compact(value[key], depth + 1)}`).join(', ') + (keys.length > 6 ? ', …' : '');
}

function preview(message) {
  const { topic, value } = message;
  if (value && typeof value === 'object') {
    if (topic.startsWith('camera/') && 'frame' in value) return `frame ${value.frame}`;
    if (topic === 'session/event' && value.text) return value.text;
    if (topic === 'hub/self-test') return `${value.name}: ${value.ok ? 'passed' : 'FAILED'}`;
  }
  return compact(value);
}

async function refreshTopics() {
  try {
    const topics = Object.values(await get('/api/hub/topics'));
    topicNote.textContent = '';
    clear(topicsBody, topics.length ? topics.map(message => h('tr', null,
      h('td', null, h('code', { text: message.topic })),
      h('td', { text: message.source }),
      h('td', { class: 'num', text: fixed(message.time, 2) + ' s' }),
      h('td', { class: 'preview', title: JSON.stringify(message.value).slice(0, 600), text: preview(message) }))) : h('tr', null, h('td', { colspan: 4, class: 'muted', text: 'No messages yet.' })));
  } catch (error) {
    topicNote.textContent = 'Cannot read the topics: ' + error.message;
  }
}

// Panel

export function setHubActive(active) {
  if (active && !stopModules) {
    stopModules = repeat(refreshModules, MODULE_POLL_MS);
    stopTopics = repeat(refreshTopics, TOPIC_POLL_MS);
  } else if (!active && stopModules) {
    stopModules();
    stopTopics();
    stopModules = stopTopics = null;
  }
}

export function initHubPanel(root) {
  moduleBox = h('ul', { class: 'modules' });
  topicsBody = h('tbody');
  summary = h('p', { class: 'summary', role: 'status' });
  moduleNote = h('p', { class: 'form-error' });
  topicNote = h('p', { class: 'form-error' });
  const all = h('button', { type: 'button', class: 'primary', onclick: event => runAll(event.currentTarget) }, 'Run all self-tests');
  const copy = h('button', {
    type: 'button',
    onclick: async () => {
      try {
        await navigator.clipboard.writeText(COMMAND);
        toast('Command copied');
      } catch (error) {
        toast('Select the command and copy it by hand', true);
      }
    },
  }, 'Copy');
  clear(root,
    h('section', { class: 'block' },
      h('div', { class: 'toolbar-row' }, h('h3', { text: 'Modules' }), all),
      summary, moduleNote, moduleBox),
    h('section', { class: 'block' },
      h('h3', { text: 'Topics' }),
      h('p', { class: 'muted', text: 'The latest message on each topic.' }),
      topicNote,
      h('div', { class: 'table-wrap' },
        h('table', { class: 'topics' },
          h('thead', null, h('tr', null, ['Topic', 'Source', 'Sim time', 'Latest value'].map(text => h('th', { scope: 'col', text })))),
          topicsBody))),
    h('details', { class: 'block help' },
      h('summary', { text: 'Connect an outside module' }),
      h('p', { text: 'A program outside the simulator, such as an AI camera model, can join the hub over HTTP. With the simulator running, start the example in a second terminal from the project folder:' }),
      h('div', { class: 'command' }, h('code', { text: COMMAND }), copy),
      h('p', { text: 'It appears in the module list above, marked "outside", and turns stale if its heartbeat stops. The API is described in docs/coop-simulation.md.' })));
}
