// Experiments tab: batch experiments. The mission is repeated for every variant of the scenario and every seed in
// worker processes (app/coop/experiments.py). This tab sets the variants up, follows the progress and shows the results.
import { h, clear, fixed, numberField, textField, selectField, toast, withBusy } from './ui.js';
import { get, post, request } from './api.js';
import { store, on } from './store.js';
import { DETECTOR_LABEL, LOCOMOTION_LABEL } from './mission-panel.js';

const POLL_MS = 1000;
const MAX_VARIANTS = 8;
const MAX_RUNS = 120;
const PARALLEL_RUNS = 8;         // runs that go at the same time: the server uses up to 8 worker processes
const SPEED_UP = 2;              // about how much faster than real time one run simulates
const CRAB_STOP_DISTANCE = .19;  // m: the crab legs' feet reach 171 mm ahead of the body, so the dock's stop block moves back
const KIND = { experiment: 'Experiment', traverse: 'Traverse test' };
const STATUS = { running: 'running', done: 'done', cancelled: 'cancelled', error: 'failed' };

// How the comparison table shows a column of experiments.py: label, unit, factor from the server's unit, digits.
const COLUMN = {
  distance_m: { label: 'Distance walked', unit: 'm', digits: 1 },
  laps: { label: 'Laps', digits: 1 },
  deviation_m: { label: 'Mean route deviation', unit: 'cm', scale: 100, digits: 1 },
  falls: { label: 'Falls', digits: 1 },
  coverage: { label: 'Coop coverage per lap', unit: '%', scale: 100, digits: 0 },
  time_to_alarm_s: { label: 'Time to fox alarm', unit: 's', digits: 1 },
  alarm_in_view_s: { label: 'Alarm after fox in view', unit: 's', digits: 1 },
  false_alarms: { label: 'False alarms', digits: 1 },
  fox_fled: { label: 'Fox chased off', unit: '% of runs', scale: 100, digits: 0 },
  docking_rate: { label: 'Docking success', unit: '%', scale: 100, digits: 0 },
  docking_lateral_m: { label: 'Docking error beside', unit: 'mm', scale: 1000, digits: 0 },
  energy_wh: { label: 'Energy used', unit: 'Wh', digits: 2 },
  energy_per_lap_wh: { label: 'Energy per lap', unit: 'Wh', digits: 3 },
  battery_end: { label: 'Battery at the end', unit: '%', scale: 100, digits: 0 },
};

const form = { title: '', seeds: 3, seconds: 300, variants: [] };
const view = { jobId: '', runKey: '', resultKey: '' };  // parts of the block that shows the selected job
let variantBox = null, addButton = null, estimate = null, runError = null;
let jobsBox = null, jobsNote = null;
let selected = null;   // {id, job}: the job on show; job is null until it has been fetched
let listKey = '';
let stopPolling = null;

const pretty = key => key.charAt(0).toUpperCase() + key.slice(1).replace(/-/g, ' ');
const grid = (...fields) => h('div', { class: 'grid2' }, fields);
const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const clock = started => new Date(started * 1000).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
const newVariant = (name, legs = 'current') => ({ name, legs, time: 'current', detector: 'current', locomotion: 'current', extra: '' });

function duration(total) {
  const s = Math.round(total);
  if (s < 60) return `${s} s`;
  const minutes = Math.floor(s / 60);
  return minutes < 60 ? `${minutes} min ${s % 60} s` : `${Math.floor(minutes / 60)} h ${minutes % 60} min`;
}

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

// Variants

function uniqueName(base) {
  const used = new Set(form.variants.map(variant => variant.name.trim()));
  let name = base, n = 1;
  while (used.has(name)) name = `${base} ${++n}`;
  return name;
}

/** Objects merge key by key; everything else in `extra` replaces what `base` has (the server merges the same way). */
function mergeChanges(base, extra) {
  const result = { ...base };
  for (const [key, value] of Object.entries(extra)) result[key] = isObject(value) && isObject(result[key]) ? mergeChanges(result[key], value) : value;
  return result;
}

/** The changes of one variant: its quick choices, with the extra JSON merged over them. */
function changesOf(variant, name) {
  const changes = {};
  const preset = store.model.leg_presets[variant.legs];
  if (preset) {
    changes.robot = { legs: JSON.parse(JSON.stringify(preset.legs)), gait: JSON.parse(JSON.stringify(preset.gait)) };
    if (variant.legs === 'crab') changes.dock = { stop_distance: CRAB_STOP_DISTANCE };
  }
  if (variant.time !== 'current') changes.environment = { time_of_day: variant.time };
  if (variant.detector !== 'current') changes.detector = { type: variant.detector };
  if (variant.locomotion !== 'current') changes.patrol = { locomotion: variant.locomotion };
  const text = variant.extra.trim();
  if (!text) return changes;
  let extra;
  try {
    extra = JSON.parse(text);
  } catch (error) {
    throw new Error(`${name}: the extra changes are not valid JSON (${error.message})`);
  }
  if (!isObject(extra)) throw new Error(`${name}: the extra changes must be a JSON object such as {"patrol": {"tolerance": 0.3}}`);
  return mergeChanges(changes, extra);
}

function buildRequest() {
  const names = new Set();
  const variants = form.variants.map((variant, index) => {
    const name = variant.name.trim() || `Variant ${index + 1}`;
    if (names.has(name)) throw new Error(`Two variants are called "${name}": give each variant its own name`);
    names.add(name);
    return { name, changes: changesOf(variant, name) };
  });
  return { title: form.title.trim(), variants, seeds: form.seeds, seconds: form.seconds };
}

function showEstimate() {
  const runs = form.variants.length * form.seeds;
  if (!Number.isFinite(runs) || !(form.seconds > 0)) {
    estimate.textContent = 'Enter the seeds per variant and the mission length to see the number of runs.';
    estimate.classList.remove('warn');
    return;
  }
  const wall = Math.ceil(runs / PARALLEL_RUNS) * form.seconds / SPEED_UP;
  estimate.textContent = `${runs} runs (${form.variants.length} variants × ${form.seeds} seeds), roughly ${duration(wall)} in all. ` +
    `This is an estimate: it assumes one run simulates about ${SPEED_UP}× faster than real time and ${PARALLEL_RUNS} runs go at the same time.` +
    (runs > MAX_RUNS ? ` An experiment has at most ${MAX_RUNS} runs.` : '');
  estimate.classList.toggle('warn', runs > MAX_RUNS);
}

const focusName = index => {
  const input = variantBox.children[index] && variantBox.children[index].querySelector('input');
  if (input) input.focus();
};

function addVariant() {
  if (form.variants.length >= MAX_VARIANTS) return;
  form.variants.push(newVariant(uniqueName(`Variant ${form.variants.length + 1}`)));
  renderVariants();
  focusName(form.variants.length - 1);
}

function duplicateVariant(index) {
  if (form.variants.length >= MAX_VARIANTS) return;
  const variant = form.variants[index];
  form.variants.splice(index + 1, 0, { ...variant, name: uniqueName(`${variant.name.trim() || 'Variant'} copy`) });
  renderVariants();
  focusName(index + 1);
}

function removeVariant(index) {
  if (form.variants.length <= 1) return;
  form.variants.splice(index, 1);
  renderVariants();
  addButton.focus();
}

function variantCard(variant, index) {
  const model = store.model;
  const crab = h('p', { class: 'note', text: 'Crab legs reach 171 mm ahead of the body while walking, so this variant also moves the dock\'s stop block back to 190 mm (dock stop distance).' });
  const outside = h('p', { class: 'warning', text: 'Batch runs have no outside program, so this variant would never see the fox.' });
  const toggles = () => {
    crab.hidden = variant.legs !== 'crab';
    outside.hidden = variant.detector !== 'external';
  };
  const current = { value: 'current', label: 'Current' };
  const choice = (label, key, options) => selectField({
    label, options: [current, ...options], value: variant[key], onInput: value => { variant[key] = value; toggles(); },
  });
  const extra = h('textarea', {
    rows: 3, spellcheck: 'false', placeholder: '{"patrol": {"tolerance": 0.3}}', value: variant.extra,
    'aria-label': `Extra changes of variant ${index + 1} as JSON`,
  });
  extra.addEventListener('input', () => { variant.extra = extra.value; });
  toggles();
  return h('div', { class: 'item', role: 'group', 'aria-label': `Variant ${index + 1}` },
    textField({ label: `Variant ${index + 1} name`, value: variant.name, maxlength: 60, onInput: value => { variant.name = value; } }),
    grid(
      choice('Legs', 'legs', Object.keys(model.leg_presets).map(name => ({ value: name, label: pretty(name) }))),
      choice('Time of day', 'time', model.choices.times_of_day.map(name => ({ value: name, label: pretty(name) }))),
      choice('Detector', 'detector', model.choices.detector_types.map(name => ({ value: name, label: DETECTOR_LABEL[name] || name }))),
      choice('Locomotion', 'locomotion', model.choices.locomotion.map(name => ({ value: name, label: LOCOMOTION_LABEL[name] || name })))),
    crab, outside,
    h('details', { class: 'extra', open: variant.extra.trim() !== '' },
      h('summary', { text: 'Extra changes (JSON)' }),
      h('p', { class: 'note', text: 'Any settings of the scenario to change in this variant, merged over the choices above.' }),
      extra),
    h('div', { class: 'item-actions' },
      h('button', { type: 'button', disabled: form.variants.length >= MAX_VARIANTS, onclick: () => duplicateVariant(index) }, 'Duplicate'),
      h('button', { type: 'button', disabled: form.variants.length <= 1, onclick: () => removeVariant(index) }, 'Remove')));
}

function renderVariants() {
  clear(variantBox, form.variants.map(variantCard));
  addButton.disabled = form.variants.length >= MAX_VARIANTS;
  showEstimate();
}

async function start(button) {
  runError.textContent = '';
  try {
    const body = buildRequest();
    const { job } = await withBusy(button, () => post('/api/coop/jobs/experiment', body));
    toast(`Experiment started: ${body.variants.length * body.seeds} runs`);
    await select(job);
  } catch (failure) {
    runError.textContent = failure.message;
    toast(failure.message, true);
  }
}

// The job on show: progress while it runs, then the results

function jobBlock() {
  view.title = h('h3');
  view.status = h('p', { class: 'muted' });
  view.fill = h('i');
  view.bar = h('div', {
    class: 'bar wide', role: 'progressbar', 'aria-label': 'Runs done', 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-valuenow': 0,
  }, view.fill);
  view.cancel = h('button', { type: 'button', class: 'danger', onclick: event => cancel(event.currentTarget) }, 'Cancel');
  view.error = h('p', { class: 'form-error' });
  view.runs = h('ul', { class: 'runs' });
  view.runsSummary = h('summary');
  view.results = h('div', { class: 'results', 'aria-live': 'polite' });
  view.block = h('section', { class: 'block', hidden: true },
    h('div', { class: 'toolbar-row' }, view.title, view.cancel),
    view.status, view.bar, view.error,
    h('details', { class: 'runs-box', open: true }, view.runsSummary, view.runs),
    view.results);
  view.runsBox = view.block.querySelector('details');
}

const settled = job => job.finished !== null && (job.result !== null || job.error !== null);

function statusLine(job) {
  const runs = `${job.done} of ${job.total} runs`;
  if (job.status === 'running') return `Running: ${runs} done · ${duration(job.elapsed)} so far`;
  if (job.status === 'cancelled') return `Cancelled after ${duration(job.elapsed)}: ${runs} were done.` + (job.finished === null ? ' Runs that had started are finishing.' : '');
  if (job.status === 'error') return `Failed after ${duration(job.elapsed)}: the runs could not be summarised.`;
  return `Finished in ${duration(job.elapsed)}` + (job.failed ? `, ${job.failed} of ${job.total} runs failed.` : '.');
}

function runItem(run) {
  const result = run.result;
  const detail = run.status === 'done' && result
    ? `${fixed(result.seconds, 0)} s simulated in ${fixed(result.wall_seconds, 0)} s, ended in ${result.final_state}, battery ${fixed(result.battery_end * 100, 0)} %`
    : run.status === 'error' ? run.error : run.status;
  const dot = { done: 'ok', error: 'error', cancelled: 'stale' }[run.status] || '';
  return h('li', null,
    h('span', { class: ('dot ' + dot).trim(), 'aria-hidden': 'true' }),
    h('span', null, run.label, h('small', { text: detail })));
}

function showJob() {
  view.block.hidden = !selected;
  if (!selected) return;
  const job = selected.job;
  if (!job) {
    view.title.textContent = 'Loading…';
    view.status.textContent = '';
    view.cancel.hidden = true;
    return;
  }
  if (view.jobId !== job.id) {  // another job: start with its run list open while it runs
    view.jobId = job.id;
    view.runKey = view.resultKey = '';
    view.runsBox.open = job.status === 'running';
  }
  view.title.textContent = job.title;
  view.status.textContent = statusLine(job);
  view.cancel.hidden = job.status !== 'running';
  const share = Math.round(job.progress * 100);
  view.fill.style.width = share + '%';
  view.bar.setAttribute('aria-valuenow', share);

  view.runsSummary.textContent = `Runs (${job.done} of ${job.total} done)`;
  const runKey = job.runs.map(run => run.status).join();
  if (runKey !== view.runKey) {
    view.runKey = runKey;
    clear(view.runs, job.runs.map(runItem));
  }
  const resultKey = `${job.result ? 'result' : ''}|${job.error || ''}`;
  if (resultKey !== view.resultKey) {
    view.resultKey = resultKey;
    clear(view.results, job.error ? h('pre', { class: 'trace', text: job.error }) : job.result ? resultsView(job) : null);
  }
}

/** "Distance walked (m)" for a column the table above does not know. */
function columnSpec(column) {
  if (COLUMN[column.key]) return COLUMN[column.key];
  const match = /^(.*?)\s*\(([^)]*)\)$/.exec(column.label);
  return match ? { label: match[1], unit: match[2], digits: 2 } : { label: column.label, digits: 2 };
}

/** "mean ± sd" over the seeds of one variant, or an en dash when no run had a value. */
function resultCell(entry, spec) {
  if (!entry || !entry.n || typeof entry.mean !== 'number') return h('td', { class: 'num', text: '–' });
  const scale = spec.scale || 1, digits = spec.digits === undefined ? 2 : spec.digits;
  const mean = fixed(entry.mean * scale, digits);
  return h('td', {
    class: 'num', title: `Mean of ${entry.n} run${entry.n === 1 ? '' : 's'}`,
    text: typeof entry.sd === 'number' ? `${mean} ± ${fixed(entry.sd * scale, digits)}` : mean,
  });
}

function resultsView(job) {
  const result = job.result, info = job.info || {};
  const specs = result.columns.map(columnSpec);
  const failures = result.failures || [];
  return h('div', null,
    h('h4', { text: 'Results' }),
    h('p', { class: 'muted', text: `${(info.variants || []).length} variants × ${info.seeds} seeds, ${fixed(info.seconds, 0)} s each, from the scenario "${info.scenario}". Each cell is the mean ± the standard deviation over the seeds; hover for the number of runs.` }),
    h('div', { class: 'table-wrap' },
      h('table', { class: 'compare' },
        h('caption', { class: 'sr-only', text: 'Mean and standard deviation per variant' }),
        h('thead', null, h('tr', null,
          h('th', { scope: 'col', text: 'Variant' }),
          specs.map(spec => h('th', { scope: 'col' }, spec.label, spec.unit ? h('small', { text: spec.unit }) : null)))),
        h('tbody', null, result.table.map(row => h('tr', null,
          h('th', { scope: 'row' }, row.variant, h('small', { text: `${row.runs} run${row.runs === 1 ? '' : 's'}` })),
          result.columns.map((column, index) => resultCell(row[column.key], specs[index]))))))),
    failures.length ? h('div', null,
      h('p', { class: 'warn', text: `${failures.length} run${failures.length === 1 ? '' : 's'} did not finish:` }),
      h('ul', { class: 'warnings' }, failures.map(failure => h('li', { text: `${failure.label}: ${failure.error}` })))) : null,
    h('div', { class: 'button-row' },
      h('a', { class: 'button', href: `/api/coop/jobs/${encodeURIComponent(job.id)}/csv`, download: `experiment-${job.id}.csv` }, 'Download CSV')),
    h('p', { class: 'note', text: 'More seeds give firmer conclusions: with only a few seeds a difference between two variants can be chance. Compare the difference of the means with the spread (±) before you trust it.' }));
}

async function cancel(button) {
  if (!selected) return;
  const id = selected.id;
  try {
    const job = await withBusy(button, () => request(`/api/coop/jobs/${encodeURIComponent(id)}`, 'DELETE'));
    if (selected && selected.id === id) {
      selected.job = job;
      showJob();
    }
    toast('Experiment cancelled. Runs that had already started finish first.');
  } catch (error) {
    toast(error.message, true);
  }
}

async function select(id) {
  selected = { id, job: null };
  listKey = '';  // draw the list again to mark this job
  showJob();
  await refresh();
}

// Earlier jobs

function jobItem(job) {
  const meta = `${KIND[job.kind] || job.kind} · ${STATUS[job.status] || job.status} · ${job.done} of ${job.total} runs · ${clock(job.started)}`;
  const title = job.kind === 'experiment'
    ? h('button', {
      type: 'button', class: 'link', 'data-job': job.id, 'aria-current': selected && selected.id === job.id ? 'true' : null,
      onclick: () => select(job.id),
    }, job.title)
    : h('span', { text: job.title });
  return h('li', null, title, h('small', { class: 'muted', text: meta }));
}

function showList(list) {
  const marked = selected ? selected.id : '';
  const key = marked + JSON.stringify(list.map(job => [job.id, job.title, job.status, job.done, job.total]));
  if (key === listKey) return;
  listKey = key;
  const focused = document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.job : undefined;
  clear(jobsBox, list.length ? list.map(jobItem) : h('li', { class: 'muted', text: 'No experiments yet.' }));
  if (focused) {  // the list is drawn again while a run finishes: keep the keyboard where it was
    const again = [...jobsBox.querySelectorAll('[data-job]')].find(node => node.dataset.job === focused);
    if (again) again.focus();
  }
}

async function refresh() {
  try {
    showList(await get('/api/coop/jobs'));
    jobsNote.textContent = '';
  } catch (error) {
    jobsNote.textContent = 'Cannot read the jobs: ' + error.message;
  }
  if (!selected || (selected.job && settled(selected.job))) return;
  const id = selected.id;
  try {
    const job = await get(`/api/coop/jobs/${encodeURIComponent(id)}`);
    if (selected && selected.id === id) {
      selected.job = job;
      view.error.textContent = '';
      showJob();
    }
  } catch (error) {
    if (selected && selected.id === id) view.error.textContent = error.message;
  }
}

/** Poll the jobs once a second while the tab is on show. */
export function setExperimentsActive(active) {
  if (active && !stopPolling) {
    stopPolling = repeat(refresh, POLL_MS);
  } else if (!active && stopPolling) {
    stopPolling();
    stopPolling = null;
  }
}

// Panel

export function initExperimentsPanel(root) {
  form.variants = [newVariant('Stock legs', 'stock'), newVariant('Crab legs', 'crab')];
  variantBox = h('div', { class: 'variants' });
  addButton = h('button', { type: 'button', class: 'full', onclick: addVariant }, '+ Add variant');
  estimate = h('p', { class: 'note' });
  runError = h('p', { class: 'form-error', role: 'alert' });
  jobsBox = h('ul', { class: 'jobs' });
  jobsNote = h('p', { class: 'form-error' });
  jobBlock();

  const seeds = numberField({
    label: 'Seeds per variant', value: form.seeds, min: 1, max: 20, integer: true,
    onInput: value => { form.seeds = value; showEstimate(); },
  });
  const length = numberField({
    label: 'Mission length', unit: 's', value: form.seconds, min: 10, max: 3600,
    onInput: value => { form.seconds = value; showEstimate(); },
  });
  clear(root,
    h('section', { class: 'block' },
      h('h3', { text: 'Batch experiment' }),
      h('p', { class: 'note', text: 'Repeats the mission for each variant and several seeds, in background processes, so the simulation above stays usable. A variant changes some settings of the scenario as it is applied now; everything else stays the same. Then the variants are compared side by side.' }),
      h('h4', { text: 'Variants' }),
      variantBox, addButton,
      h('h4', { text: 'Runs' }),
      grid(seeds, length),
      h('p', { class: 'note', text: 'Each seed changes the terrain bumps, the stones and the chickens, so a result does not hang on one lucky layout. The mission starts at 0 s and runs for the mission length, or until the battery is empty.' }),
      textField({ label: 'Title (optional)', value: form.title, maxlength: 120, placeholder: 'Defaults to the variant names', onInput: value => { form.title = value; } }),
      estimate, runError,
      h('button', { type: 'button', class: 'primary full', onclick: event => start(event.currentTarget) }, 'Run experiment')),
    view.block,
    h('section', { class: 'block' },
      h('h3', { text: 'Earlier jobs' }),
      h('p', { class: 'muted', text: 'Click an experiment to see its results.' }),
      jobsNote, jobsBox));
  showEstimate();
  on('model', renderVariants);  // the choices come from the model
}
