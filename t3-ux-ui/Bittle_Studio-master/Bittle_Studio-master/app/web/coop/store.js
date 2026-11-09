// Shared state and a tiny event bus. 'model' fires when the server's model was replaced (with the scenario keys whose
// local drafts must be reset), 'state' after every poll.
import { get, put } from './api.js';

export const ALL = ['name', 'simulation', 'terrain', 'mud', 'stones', 'coop', 'dock', 'robot', 'sensors',
  'environment', 'chickens', 'visitors', 'patrol', 'detector', 'behaviour', 'energy'];

export const store = {
  model: null,
  state: null,
  draftName: null,  // scenario name typed in the top bar, sent with the next Apply
  pending: 0,       // requests in flight that replace the model; the poll leaves the model alone meanwhile
};

const handlers = {};

export function on(name, handler) {
  (handlers[name] = handlers[name] || []).push(handler);
}

export function emit(name, data) {
  for (const handler of handlers[name] || []) {
    try {
      handler(data);
    } catch (error) {
      console.error(`Handler of "${name}" failed`, error);
    }
  }
}

/** Paths into the scenario, such as 'robot.legs'. */
export const getPath = (object, path) => path.split('.').reduce((value, part) => value[part], object);

export function setPath(object, path, value) {
  const parts = path.split('.');
  const last = parts.pop();
  parts.reduce((target, part) => target[part], object)[last] = value;
}

/** True when one of the applied keys is `key`, lies inside it ('robot' covers 'robot.legs') or contains it. */
export const touches = (applied, key) => applied.some(k => k === key || key.startsWith(k + '.') || k.startsWith(key + '.'));

export function acceptModel(model, keys = ALL) {
  store.model = model;
  emit('model', keys);
}

export async function loadModel() {
  acceptModel(await get('/api/coop/model'));
}

/** Accept the model that `request()` returns. While it is in flight the poll does not reload the model on its own. */
export async function changeModel(request, keys = ALL) {
  store.pending++;
  try {
    const model = await request();
    acceptModel(model, keys);
    return model;
  } finally {
    store.pending--;
  }
}

export function acceptState(state) {
  store.state = state;
  emit('state', state);
}

/**
 * Apply scenario changes: the scenario as the server holds it now (its speed may have changed since the model was
 * loaded) with `change` put over it, an object of sections or a function that edits the scenario. `keys` names the
 * sections that were applied.
 */
export function applyScenario(change, keys) {
  return changeModel(async () => {
    const scenario = await get('/api/coop/scenario');
    if (typeof change === 'function') change(scenario);
    else Object.assign(scenario, change);
    if (store.draftName) scenario.name = store.draftName;
    return put('/api/coop/scenario', scenario);
  }, keys);
}

/** Model of the scenario that is applied now, so panels can show what the simulation really uses. */
export const applied = () => store.model.scenario;

/** '' while the battery is fine, 'low' below the level at which the robot goes to the dock, 'critical' below half of it. */
export function batteryLevel(charge) {
  const low = applied().behaviour.low_battery;
  return charge < low / 2 ? 'critical' : charge < low ? 'low' : '';
}
