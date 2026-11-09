// A collapsible form group with its own Apply button. The form edits a local draft; Apply sends the whole scenario
// (store.applyScenario) and keeps the draft when the server refuses it, so no typing is lost.
import { h, clear, clone, toast, withBusy } from './ui.js';
import { store, applyScenario, getPath, setPath } from './store.js';

/**
 * title: heading; draft: object that holds a local copy of each section's part of the scenario;
 * name: the draft entry, and by default the scenario path it copies ('terrain', 'robot.legs');
 * keys: scenario keys that reset the draft when the model is replaced (default [name]);
 * send: keys reported as applied (default keys); extraSend(): more keys, computed at Apply time;
 * read(scenario) / write(scenario, copy): override the path copy for parts that are not one scenario path;
 * build(item): the form content from the current draft; note: text under the buttons.
 */
export function makeSection({ title, draft, name, keys = [name], send = keys, extraSend, read, write, build, open = false, note }) {
  const copyOut = read || (scenario => clone(getPath(scenario, name)));
  const copyIn = write || ((scenario, value) => setPath(scenario, name, value));
  const body = h('div', { class: 'group-body' });
  const error = h('p', { class: 'form-error', role: 'alert' });
  const apply = h('button', { type: 'button', class: 'primary' }, `Apply ${title.toLowerCase()}`);
  const el = h('details', { class: 'group', open },
    h('summary', null, title, h('span', { class: 'dirty-mark', text: '● unapplied edits' })),
    body,
    h('div', { class: 'actions' }, apply),
    error,
    h('p', { class: 'note', text: note || 'Applying restarts the run from the start position.' }));
  const item = {
    el,
    keys,
    markDirty: () => el.classList.add('dirty'),
    render: () => clear(body, build(item)),
    reset() {
      draft[name] = copyOut(store.model.scenario);
      error.textContent = '';
      el.classList.remove('dirty');
      item.render();
    },
  };
  el.addEventListener('input', item.markDirty);
  el.addEventListener('change', item.markDirty);
  apply.addEventListener('click', async () => {
    error.textContent = '';
    try {
      const applied = [...send, ...(extraSend ? extraSend() : [])];
      await withBusy(apply, () => applyScenario(scenario => copyIn(scenario, clone(draft[name])), applied));
      toast('Applied. The run restarted from the start position.');
    } catch (failure) {  // the draft stays as it is
      error.textContent = failure.message;
      toast(failure.message, true);
    }
  });
  return item;
}
