// Bewegingen: record leg movements as a row of poses, play them on the 3D robot (and the real one), keep them.
// A pose comes from the sliders, or from the real robot: read its legs once, or keep reading while you move the legs
// by hand (the servos go soft). Saved motions are JSON files in platform-data/motions/.
import { h, clear, toast, api, round } from './ui.js';

const DEFAULT_SECONDS = .5;

export function initMotions(root, { twin, robot, getModel, onPlayPose }) {
  let motion = blank();
  let current = -1;          // index of the pose shown, or -1
  let dirty = false;

  function blank() {
    return { name: '', model: getModel(), loop: false, notes: '', frames: [] };
  }

  const name = h('input', { type: 'text', maxlength: 60, placeholder: 'bv. stap-over-steen', 'aria-label': 'Naam van de beweging' });
  name.addEventListener('input', () => { motion.name = name.value; markDirty(); });
  const loop = h('input', { type: 'checkbox' });
  loop.addEventListener('change', () => { motion.loop = loop.checked; markDirty(); });
  const list = h('ol', { class: 'frames', 'aria-label': 'Houdingen van de beweging' });
  const summary = h('p', { class: 'note' });
  const saved = h('ul', { class: 'saved' });
  const liveButton = h('button', { type: 'button', 'aria-pressed': 'false', onclick: toggleLive,
    title: 'De servo\'s worden slap: beweeg de poten met de hand, de 3D-robot doet mee' }, 'Live meelezen');
  const playButton = h('button', { type: 'button', class: 'primary', onclick: play }, '▶ Afspelen');
  const stopButton = h('button', { type: 'button', onclick: () => twin.stop(), disabled: true }, '■ Stop');
  const saveButton = h('button', { type: 'button', class: 'primary', onclick: save }, 'Opslaan');

  function markDirty() {
    dirty = true;
    saveButton.textContent = 'Opslaan ●';
  }

  function pose() {
    return Object.fromEntries(Object.entries(twin.pose()).map(([joint, angle]) => [joint, round(angle, 1)]));
  }

  function render() {
    name.value = motion.name;
    loop.checked = motion.loop;
    clear(list, motion.frames.length ? motion.frames.map(frameRow) : h('li', null, h('span'), h('span', { class: 'note', text: 'Nog geen houdingen. Zet de robot in een houding en klik op "Houding toevoegen".' }), h('span')));
    const total = motion.frames.reduce((sum, frame) => sum + frame.seconds, 0);
    summary.textContent = motion.frames.length ? `${motion.frames.length} houdingen · ${total.toFixed(1)} s${motion.loop ? ' · herhaalt' : ''}` : '';
  }

  function frameRow(frame, index) {
    const seconds = h('input', { type: 'number', min: .05, max: 10, step: .05, value: frame.seconds, 'aria-label': `Tijd naar houding ${index + 1} (s)`, title: 'Seconden om naar deze houding te gaan' });
    seconds.addEventListener('change', () => {
      const value = Number(seconds.value);
      if (value >= .02 && value <= 10) { frame.seconds = value; markDirty(); render(); } else seconds.value = frame.seconds;
    });
    const button = (label, title, action, disabled = false) => h('button', { type: 'button', title, 'aria-label': `${title}, houding ${index + 1}`, onclick: action, disabled }, label);
    return h('li', { class: index === current ? 'current' : '' },
      h('span', { class: 'num', text: index + 1 }),
      h('span', { class: 'row' }, seconds, h('span', { class: 'note', text: 's' })),
      h('span', { class: 'buttons' },
        button('👁', 'Toon', () => show(index)),
        button('⟳', 'Vervang door de huidige houding', () => { frame.pose = pose(); markDirty(); show(index); }),
        button('↑', 'Omhoog', () => move(index, -1), index === 0),
        button('↓', 'Omlaag', () => move(index, 1), index === motion.frames.length - 1),
        button('✕', 'Verwijder', () => { motion.frames.splice(index, 1); current = -1; markDirty(); render(); })));
  }

  function show(index) {
    current = index;
    twin.stop();
    twin.setPose(motion.frames[index].pose);
    onPlayPose(twin.pose());
    render();
  }

  function move(index, delta) {
    motion.frames.splice(index + delta, 0, motion.frames.splice(index, 1)[0]);
    current = index + delta;
    markDirty();
    render();
  }

  function add() {
    if (motion.frames.length >= 500) return toast('Een beweging heeft hoogstens 500 houdingen.', true);
    motion.frames.push({ pose: pose(), seconds: DEFAULT_SECONDS });
    current = motion.frames.length - 1;
    markDirty();
    render();
    list.lastElementChild?.scrollIntoView({ block: 'nearest' });
  }

  async function readOnce() {
    if (!robot.connected) return toast('Verbind eerst de robot om zijn poten te lezen.', true);
    try {
      await robot.readOnce();
      toast('Poten gelezen: de 3D-robot staat nu zoals de echte.');
    } catch (error) {
      toast(error.message, true);
    }
  }

  async function toggleLive() {
    if (!robot.connected) return toast('Verbind eerst de robot.', true);
    try {
      if (robot.mirroring) {
        await robot.stopReading();
        liveButton.setAttribute('aria-pressed', 'false');
        toast('Live meelezen gestopt: de servo\'s houden deze houding vast.');
      } else {
        await robot.readLive();
        liveButton.setAttribute('aria-pressed', 'true');
        toast('Beweeg de poten met de hand; klik "Houding toevoegen" bij elke houding die je wilt bewaren.');
      }
    } catch (error) {
      toast(error.message, true);
    }
  }

  function play() {
    if (!motion.frames.length) return toast('Voeg eerst houdingen toe.', true);
    if (robot.mirroring) toggleLive();
    const plan = { segments: motion.frames.map(frame => [frame.seconds, frame.pose]), loop_from: motion.loop ? 0 : null, ease: true };
    playButton.disabled = true;
    stopButton.disabled = false;
    twin.play(plan, {
      onPose: onPlayPose,
      onEnd: () => { playButton.disabled = false; stopButton.disabled = true; },
    });
  }

  async function save() {
    const label = motion.name.trim();
    if (!label) { name.focus(); return toast('Geef de beweging eerst een naam.', true); }
    try {
      motion = await api(`/api/motions/${encodeURIComponent(label)}`, 'PUT', { ...motion, model: getModel() });
      dirty = false;
      saveButton.textContent = 'Opslaan';
      toast(`Beweging "${motion.name}" opgeslagen.`);
      render();
      refresh();
    } catch (error) {
      toast(error.message, true);
    }
  }

  async function open(label) {
    if (dirty && !confirm('De huidige beweging is niet opgeslagen. Toch een andere openen?')) return;
    try {
      motion = await api(`/api/motions/${encodeURIComponent(label)}`);
      current = -1;
      dirty = false;
      saveButton.textContent = 'Opslaan';
      render();
      if (motion.model !== getModel()) toast(`Let op: deze beweging is gemaakt voor het model "${motion.model}".`);
    } catch (error) {
      toast(error.message, true);
    }
  }

  async function remove(label) {
    if (!confirm(`Beweging "${label}" verwijderen?`)) return;
    try {
      await api(`/api/motions/${encodeURIComponent(label)}`, 'DELETE');
      refresh();
    } catch (error) {
      toast(error.message, true);
    }
  }

  async function refresh() {
    try {
      const motions = await api('/api/motions');
      clear(saved, motions.length ? motions.map(item => h('li', null,
        h('span', null, item.name, h('small', { text: `${item.frames} houdingen · ${item.model}` })),
        h('span', { class: 'row' },
          h('button', { type: 'button', onclick: () => open(item.name) }, 'Openen'),
          h('button', { type: 'button', class: 'danger', 'aria-label': `Verwijder ${item.name}`, onclick: () => remove(item.name) }, '✕'))))
        : h('li', { class: 'note', text: 'Nog geen bewaarde bewegingen.' }));
    } catch (error) {
      clear(saved, h('li', { class: 'error-text', text: error.message }));
    }
  }

  function download() {
    const blob = new Blob([JSON.stringify({ ...motion, format: 'bittle-motion', version: 1 }, null, 1)], { type: 'application/json' });
    const link = h('a', { href: URL.createObjectURL(blob), download: `${motion.name || 'beweging'}.json` });
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  clear(root,
    h('h3', { text: 'Beweging' }),
    h('div', { class: 'row' }, name, saveButton,
      h('button', { type: 'button', onclick: () => { if (!dirty || confirm('Niet opgeslagen wijzigingen weggooien?')) { motion = blank(); current = -1; dirty = false; saveButton.textContent = 'Opslaan'; render(); } } }, 'Nieuw')),
    h('h3', { text: 'Houding opnemen' }),
    h('div', { class: 'grid2' },
      h('button', { type: 'button', class: 'primary', onclick: add }, '+ Houding toevoegen'),
      h('button', { type: 'button', onclick: readOnce, title: 'Leest de hoeken van de echte poten één keer' }, 'Lees echte poten'),
      liveButton),
    h('p', { class: 'note', text: 'Zet de houding met de schuiven (Besturen), of lees de echte robot: met "Live meelezen" zijn de servo\'s slap en beweeg je de poten met de hand.' }),
    h('h3', { text: 'Houdingen' }),
    list, summary,
    h('div', { class: 'row' }, playButton, stopButton, h('label', { class: 'check' }, loop, 'Herhalen'),
      h('button', { type: 'button', onclick: download, title: 'Download als JSON-bestand' }, 'Download')),
    h('p', { class: 'note', text: 'Afspelen beweegt de 3D-robot; met "Robot volgt" aan beweegt de echte robot mee.' }),
    h('h3', { text: 'Bewaarde bewegingen' }), saved);

  robot.onPose(() => {
    if (current >= 0 && robot.mirroring) { current = -1; render(); }
  });
  render();
  refresh();
  return { refresh };
}
