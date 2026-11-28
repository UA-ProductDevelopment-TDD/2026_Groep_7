// 2D map editor for the Bittle Platform page. Plain ES module, no dependencies.
// World units are metres, x to the east, y to the north; angles in degrees, 0 = east, counter-clockwise.
// The map document follows validate_map() in app/bittle_platform/storage.py.

const API = '/api';
const SNAP = 0.05;                 // 5 cm placement grid
const ANGLE_SNAP = 5;
const MAX_ITEMS = 500, MAX_POINTS = 200, UNDO_LIMIT = 30, TRAIL_LIMIT = 200;
const BG_TYPES = ['image/png', 'image/jpeg', 'image/webp'];
const NAME_RE = /^[A-Za-z0-9][A-Za-z0-9 _-]{0,59}$/;

const NAMES = { wall: 'Muur', fence: 'Omheining', coop: 'Hok', house: 'Huisje', obstacle: 'Obstakel', zone: 'Zone',
  dock: 'Dock', marker: 'Marker', label: 'Tekst', robot: 'Robot' };
const RECTS = new Set(['coop', 'house', 'obstacle', 'zone']);
const HEADINGS = new Set(['dock', 'marker', 'robot']);
const DEFAULT_SIZE = { coop: [1.2, 0.8], house: [1, 1], obstacle: [0.3, 0.3], zone: [1, 1] };
// [tool id, label, glyph, shortcut key]
const TOOLS = [
  ['select', 'Selecteren', '↖', 'v'], ['wall', 'Muur', '▬', 'w'], ['fence', 'Omheining', '┅', 'f'],
  ['coop', 'Hok', '▭', 'c'], ['house', 'Huisje', '⌂', 'h'], ['obstacle', 'Obstakel', '■', 'o'],
  ['zone', 'Zone', '▨', 'z'], ['dock', 'Dock', '◎', 'd'], ['marker', 'Marker', '▣', 'm'],
  ['label', 'Tekst', 'T', 't'], ['robot', 'Robot', '▲', 'r'],
];

const COLORS = {
  wall: '#c9d1d9', fence: '#c8a46a', coop: '#f0883e', coopFill: 'rgba(240,136,62,.14)', house: '#8a4b3b',
  houseLine: '#c0705a', obstacle: '#6e7681', obstacleLine: '#9aa4af', zoneFill: 'rgba(56,139,253,.2)',
  zone: '#58a6ff', dock: '#2f81f7', robot: '#3fb950', select: '#ffd33d',
};

const r4 = v => Math.round(v * 1e4) / 1e4;
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const rad = d => d * Math.PI / 180;
const deg = r => r * 180 / Math.PI;
const normAngle = a => { a = ((a + 180) % 360 + 360) % 360 - 180; return a === -180 ? 180 : a; };
const fmt = v => (typeof v === 'number' && Number.isFinite(v)) ? String(r4(v)) : '';
const clone = v => JSON.parse(JSON.stringify(v));

function el(tag, props = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === 'class') node.className = v;
    else if (k === 'text') node.textContent = v;
    else if (v === true) node.setAttribute(k, '');
    else if (v !== false && v != null) node.setAttribute(k, v);
  }
  for (const kid of kids) if (kid != null) node.append(kid);
  return node;
}

function emptyMap() {
  return { format: 'bittle-map', version: 1, name: '', notes: '', size: [10, 10], items: [], robot: null, background: null };
}

// Make a loaded document safe to use in the editor (the server already validated it, this is belt and braces).
function normalize(data) {
  const m = emptyMap();
  if (!data || typeof data !== 'object') return m;
  m.name = String(data.name || '');
  m.notes = String(data.notes || '');
  if (Array.isArray(data.size) && data.size.length === 2) m.size = [Number(data.size[0]) || 10, Number(data.size[1]) || 10];
  m.items = Array.isArray(data.items) ? data.items.filter(i => i && typeof i === 'object') : [];
  m.robot = data.robot && typeof data.robot === 'object'
    ? { x: Number(data.robot.x) || 0, y: Number(data.robot.y) || 0, heading: Number(data.robot.heading) || 0 } : null;
  const b = data.background;
  if (b && typeof b === 'object' && b.file) {
    m.background = { file: String(b.file), scale: Number(b.scale) || 0.01,
      origin: Array.isArray(b.origin) && b.origin.length === 2 ? [Number(b.origin[0]) || 0, Number(b.origin[1]) || 0] : [0, 0],
      opacity: Number.isFinite(Number(b.opacity)) ? Number(b.opacity) : 0.6 };
  }
  return m;
}

export function createMap(root, options = {}) {
  const { onChange, toast, apiBase = '' } = options;
  let editable = options.canEdit !== false;

  // ---- state
  let map = emptyMap();
  let dirty = false;
  let undoStack = [];
  let sel = null;                 // item id, 'robot' or null
  let tool = 'select';
  const view = { cx: 5, cy: 5, s: 60 };   // world centre of the canvas, pixels per metre
  let W = 0, H = 0, dpr = 1, needFit = true, raf = 0;
  let draft = null;               // polyline being drawn: {kind, points: [[x, y]]}
  let drag = null;
  let calib = null;               // points clicked while calibrating the background
  let hover = null;               // last pointer position {sx, sy, x, y} (x, y snapped)
  let live = null;
  const trail = [];
  let bgImg = null, bgFile = null, bgVersion = 0, pendingFit = false;
  let savedNames = [];
  let busy = false;
  let sliderFresh = true;
  let scans = [];                 // turn-and-scan results drawn under the items (setScans)
  const scanImages = new Map();   // floor pictures of the scans, by URL

  function notify(message, isError = false) {
    try {
      if (typeof toast === 'function') toast(message, isError);
      else (isError ? console.error : console.log)('[kaart] ' + message);
    } catch (e) { console.error(e); }
  }

  // ---- DOM
  root.textContent = '';
  root.classList.add('map-editor');

  const select = el('select', { class: 'me-select', 'aria-label': 'Kaart kiezen' });
  const btnNew = el('button', { type: 'button', text: 'Nieuw' });
  const dot = el('span', { class: 'me-dot', 'aria-hidden': 'true', hidden: true });
  const btnSave = el('button', { type: 'button', class: 'me-primary', title: 'Opslaan (Ctrl+S)' }, 'Opslaan', dot);
  const btnDel = el('button', { type: 'button', class: 'me-danger', text: 'Verwijderen' });
  const btnUndo = el('button', { type: 'button', text: 'Ongedaan', title: 'Laatste wijziging ongedaan maken (Ctrl+Z)' });
  const bar = el('div', { class: 'me-bar' }, select, btnNew, btnSave, btnDel, el('span', { class: 'me-spacer' }), btnUndo);

  const toolsBar = el('div', { class: 'me-tools', role: 'toolbar', 'aria-label': 'Gereedschap' });
  const pressables = [];          // [button, tool id] kept in sync with aria-pressed
  for (const [id, label, glyph, key] of TOOLS) {
    const b = el('button', { type: 'button', 'aria-pressed': 'false', title: `${label} (${key.toUpperCase()})` },
      el('span', { class: 'me-ico', 'aria-hidden': 'true', text: glyph }), label);
    b.addEventListener('click', () => setTool(id));
    pressables.push([b, id]);
    toolsBar.append(b);
  }
  const fileInput = el('input', { type: 'file', accept: BG_TYPES.join(','), hidden: true, 'aria-label': 'Achtergrondafbeelding kiezen' });
  const btnBg = el('button', { type: 'button', title: 'Foto, plattegrond of schets als achtergrond' },
    el('span', { class: 'me-ico', 'aria-hidden': 'true', text: '▧' }), 'Achtergrond');
  btnBg.addEventListener('click', () => fileInput.click());
  toolsBar.append(btnBg, fileInput);

  const hint = el('div', { class: 'me-hint', 'aria-live': 'polite' });
  const canvas = el('canvas', { class: 'me-canvas', tabindex: '0', role: 'img', 'aria-label': 'Plattegrond van de kaart' });
  const coords = el('div', { class: 'me-coords', 'aria-hidden': 'true' });
  const btnFit = el('button', { type: 'button', class: 'me-fit', text: 'Passend', title: 'Hele kaart in beeld' });
  const stage = el('div', { class: 'me-stage' }, canvas, btnFit, coords);

  const mapBox = el('fieldset', { class: 'me-box' });
  const itemBox = el('fieldset', { class: 'me-box' });
  const bgBox = el('fieldset', { class: 'me-box' });
  const side = el('div', { class: 'me-side' },
    el('details', { open: true }, el('summary', { text: 'Kaart' }), mapBox),
    el('details', { open: true }, el('summary', { text: 'Onderdeel' }), itemBox),
    el('details', {}, el('summary', { text: 'Achtergrond' }), bgBox));
  root.append(bar, toolsBar, hint, stage, side);

  const ctx = canvas.getContext('2d');
  const editOnly = [toolsBar, btnNew, btnSave, btnDel, btnUndo];
  let staticSync = [];            // refreshers for the Kaart and Achtergrond forms
  let itemSync = [];              // refreshers for the selected-item form

  // ---- world <-> screen
  const X = x => (x - view.cx) * view.s + W / 2;
  const Y = y => H / 2 - (y - view.cy) * view.s;

  function eventPos(e) {
    const r = canvas.getBoundingClientRect();
    const sx = e.clientX - r.left, sy = e.clientY - r.top;
    return { sx, sy, x: view.cx + (sx - W / 2) / view.s, y: view.cy - (sy - H / 2) / view.s };
  }
  const snapV = v => r4(Math.round(v / SNAP) * SNAP);
  const snapPt = (p, on) => on ? { x: snapV(p.x), y: snapV(p.y) } : { x: r4(p.x), y: r4(p.y) };
  const snapAng = (a, on) => on ? Math.round(a / ANGLE_SNAP) * ANGLE_SNAP : Math.round(a * 10) / 10;
  const toLocal = (o, px, py) => {
    const a = rad(o.angle || 0), c = Math.cos(a), s = Math.sin(a), dx = px - o.x, dy = py - o.y;
    return { x: dx * c + dy * s, y: -dx * s + dy * c };
  };
  const toWorld = (o, lx, ly) => {
    const a = rad(o.angle || 0), c = Math.cos(a), s = Math.sin(a);
    return { x: o.x + lx * c - ly * s, y: o.y + lx * s + ly * c };
  };

  // ---- selection helpers
  const selObj = () => sel === 'robot' ? map.robot : (map.items.find(i => i.id === sel) || null);
  const selKind = () => { const o = selObj(); return !o ? null : (sel === 'robot' ? 'robot' : o.kind); };

  // ---- change tracking
  function updateDirtyUI() {
    dot.hidden = !dirty;
    btnSave.title = dirty ? 'Opslaan (er zijn niet-opgeslagen wijzigingen)' : 'Opslaan (Ctrl+S)';
    btnUndo.disabled = !undoStack.length;
  }
  function pushUndoText(text) {
    undoStack.push(text);
    if (undoStack.length > UNDO_LIMIT) undoStack.shift();
    updateDirtyUI();
  }
  function touch() { dirty = true; updateDirtyUI(); }
  function fire() {
    if (typeof onChange !== 'function') return;
    try { onChange(clone(map)); } catch (e) { console.error(e); }
  }
  function changed() { touch(); fire(); syncForms(); requestDraw(); }
  // Run a mutation as one undoable step.
  function edit(fn) {
    if (!editable) return;
    pushUndoText(JSON.stringify(map));
    fn();
    changed();
  }
  function undo() {
    if (!editable || !undoStack.length) return;
    const prev = JSON.parse(undoStack.pop());
    prev.name = map.name;
    map = prev;
    if (!selObj()) sel = null;
    touch();
    ensureBackground();
    renderAllForms();
    fire();
    requestDraw();
  }

  // ---- server
  async function api(path, init) {
    let res;
    try { res = await fetch(apiBase + API + path, init); }
    catch (e) { throw new Error('De server is niet bereikbaar'); }
    const raw = await res.text();
    let body = null;
    try { body = raw ? JSON.parse(raw) : null; } catch (e) { body = null; }
    if (!res.ok) {
      const d = body && body.detail;
      throw new Error(typeof d === 'string' ? d : (d ? JSON.stringify(d) : `Fout ${res.status}`));
    }
    return body;
  }

  async function refreshList() {
    try { savedNames = await api('/maps'); }
    catch (e) { notify(e.message, true); savedNames = []; }
    updateSelect();
  }
  function updateSelect() {
    select.textContent = '';
    if (!map.name) select.append(el('option', { value: '', text: '(nieuwe kaart)' }));
    for (const m of savedNames) select.append(el('option', { value: m.name, text: m.name }));
    if (map.name && !savedNames.some(m => m.name === map.name)) select.append(el('option', { value: map.name, text: map.name }));
    select.value = map.name;
  }

  function askName() {
    let suggestion = '';
    for (;;) {
      const answer = window.prompt('Naam van de kaart (letters, cijfers, spaties, - en _):', suggestion);
      if (answer === null) return null;
      const name = answer.trim();
      if (NAME_RE.test(name)) return name;
      suggestion = name;
      notify('Een naam bestaat uit letters, cijfers, spaties, - en _ (hoogstens 60) en begint met een letter of cijfer', true);
    }
  }

  async function save() {
    if (!editable || busy) return false;
    let name = map.name;
    if (!name) {
      name = askName();
      if (!name) return false;
      if (savedNames.some(m => m.name.toLowerCase() === name.toLowerCase())
        && !window.confirm(`De kaart "${name}" bestaat al. Overschrijven?`)) return false;
    }
    busy = true;
    try {
      const saved = await api('/maps/' + encodeURIComponent(name), {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...map, name }),
      });
      map.name = (saved && saved.name) || name;
      dirty = false;
      updateDirtyUI();
      notify(`Kaart "${map.name}" opgeslagen`);
      await refreshList();
      fire();  // the name may be new: whoever follows the map (the scans) must know
      return true;
    } catch (e) {
      notify(e.message, true);
      return false;
    } finally { busy = false; }
  }

  function confirmDiscard() {
    return !dirty || window.confirm('Er zijn niet-opgeslagen wijzigingen. Toch doorgaan?');
  }

  function resetState() {
    sel = null; draft = null; drag = null; calib = null; undoStack = []; dirty = false;
    pendingFit = false; hover = null;
    if (tool !== 'select') tool = 'select';
    ensureBackground();
    needFit = true;
    updateSelect(); updateDirtyUI(); updateTools();
    renderAllForms();
    fit();
    fire();
  }
  function newMap() { map = emptyMap(); resetState(); }

  async function load(name) {
    if (!name) { newMap(); return clone(map); }
    try {
      map = normalize(await api('/maps/' + encodeURIComponent(name)));
      resetState();
      return clone(map);
    } catch (e) {
      notify(e.message, true);
      updateSelect();
      return null;
    }
  }

  async function deleteMap() {
    if (!editable || !map.name) { notify('Deze kaart is nog niet opgeslagen', true); return; }
    if (!window.confirm(`Kaart "${map.name}" echt verwijderen? Dit kan niet ongedaan worden gemaakt.`)) return;
    try {
      await api('/maps/' + encodeURIComponent(map.name), { method: 'DELETE' });
      notify(`Kaart "${map.name}" verwijderd`);
      newMap();
      await refreshList();
    } catch (e) { notify(e.message, true); }
  }

  // ---- background image
  function ensureBackground() {
    const file = map.background && map.background.file;
    if (!file) { bgImg = null; bgFile = null; return; }
    if (file === bgFile && bgImg) return;
    bgFile = file;
    const img = new Image();
    bgImg = img;
    img.onload = () => {
      if (bgImg !== img) return;
      if (pendingFit && map.background) {
        // First view of a fresh upload: fit the picture to the map width, then ask for the real scale.
        pendingFit = false;
        map.background.scale = clamp(Math.round(map.size[0] / img.naturalWidth * 1e6) / 1e6, 1e-5, 10);
        map.background.origin = [0, r4(map.size[1])];
        syncForms();
        setTool('calibrate');
      }
      requestDraw();
    };
    img.onerror = () => { if (bgImg === img) { bgImg = null; notify('De achtergrondafbeelding kon niet worden geladen', true); requestDraw(); } };
    img.src = `${apiBase}${API}/backgrounds/${encodeURIComponent(file)}?v=${bgVersion}`;
  }

  async function chooseBackground(file) {
    if (!editable || !file) return;
    if (!BG_TYPES.includes(file.type)) { notify('Kies een PNG-, JPEG- of WebP-afbeelding', true); return; }
    if (file.size > 8 * 1024 * 1024) { notify('De afbeelding mag hoogstens 8 MB zijn', true); return; }
    if (!map.name && !(await save())) return;   // the image is stored under the map's name
    try {
      const res = await api('/maps/' + encodeURIComponent(map.name) + '/background', {
        method: 'PUT', headers: { 'Content-Type': file.type }, body: file,
      });
      const had = map.background;
      pushUndoText(JSON.stringify(map));
      bgVersion++; bgFile = null;
      map.background = { file: res.file, scale: had ? had.scale : 0.01, origin: had ? had.origin.slice() : [0, map.size[1]],
        opacity: had ? had.opacity : 0.6 };
      pendingFit = !had;
      ensureBackground();
      renderBgForm();
      changed();
      if (had) setTool('calibrate');
    } catch (e) { notify(e.message, true); }
  }
  fileInput.addEventListener('change', () => {
    const file = fileInput.files && fileInput.files[0];
    fileInput.value = '';
    chooseBackground(file);
  });

  function finishCalibration(a, b) {
    const d = Math.hypot(a.x - b.x, a.y - b.y);
    if (d < 1e-6 || !map.background) { notify('Kies twee verschillende punten', true); calib = []; return; }
    const answer = window.prompt('Hoeveel meter liggen deze twee punten uit elkaar?', '');
    if (answer === null) { setTool('select'); return; }
    const meters = parseFloat(answer.replace(',', '.'));
    if (!Number.isFinite(meters) || meters <= 0 || meters > 1000) {
      notify('Vul een afstand in meters in, bijvoorbeeld 2,5', true);
      calib = [];
      updateHint();
      return;
    }
    const k = meters / d;
    edit(() => {
      const bg = map.background;
      // Scale about the first clicked point so that spot stays where it is.
      bg.scale = clamp(Math.round(bg.scale * k * 1e6) / 1e6, 1e-5, 10);
      bg.origin = [clamp(r4(a.x + (bg.origin[0] - a.x) * k), -500, 500), clamp(r4(a.y + (bg.origin[1] - a.y) * k), -500, 500)];
    });
    setTool('select');
    notify('Schaal ingesteld. Vergeet niet op te slaan.');
  }

  // ---- tools
  function setTool(id) {
    if (!editable && id !== 'select') id = 'select';
    if (id === 'calibrate' && !(map.background && map.background.file)) return;
    tool = id;
    draft = null; drag = null;
    calib = id === 'calibrate' ? [] : null;
    updateTools();
    requestDraw();
  }
  function updateTools() {
    for (const [b, id] of pressables) b.setAttribute('aria-pressed', String(id === tool));
    updateHint();
    canvas.style.cursor = tool === 'select' ? 'default' : (tool === 'bgmove' ? 'move' : 'crosshair');
  }
  function updateHint() {
    let text;
    if (!editable) text = 'Alleen bekijken. Sleep om te schuiven, scroll om te zoomen, klik een onderdeel voor de getallen.';
    else if (tool === 'select') text = 'Klik een onderdeel om het te kiezen en sleep het om te verplaatsen. Sleep de lege ruimte om te schuiven, scroll om te zoomen.';
    else if (tool === 'wall' || tool === 'fence') text = 'Klik om punten te zetten. Dubbelklik of Enter maakt af, Esc stopt. Klik op het eerste punt om te sluiten.';
    else if (RECTS.has(tool)) text = 'Sleep een rechthoek, of klik voor een standaardmaat.';
    else if (tool === 'dock' || tool === 'marker' || tool === 'robot') text = 'Klik om te plaatsen; sleep om de kijkrichting in te stellen.';
    else if (tool === 'label') text = 'Klik waar de tekst moet komen en typ hem in het formulier.';
    else if (tool === 'calibrate') text = calib && calib.length === 1 ? 'Klik nu het tweede punt.' : 'Klik twee punten op de afbeelding waarvan je de afstand kent.';
    else if (tool === 'bgmove') text = 'Sleep om de achtergrondafbeelding te verplaatsen.';
    else text = '';
    if (editable && tool !== 'select' && tool !== 'calibrate' && tool !== 'bgmove') text += ' Houd Alt ingedrukt om niet vast te klikken op 5 cm.';
    hint.textContent = text;
  }

  // ---- adding and removing items
  function nextId(kind) {
    let n = map.items.length + 1;
    while (map.items.some(i => i.id === `${kind}-${n}`)) n++;
    return `${kind}-${n}`;
  }
  function nextMarker() {
    const used = new Set(map.items.filter(i => i.kind === 'marker').map(i => i.marker_id));
    let n = 0;
    while (used.has(n) && n < 999) n++;
    return n;
  }
  function addItem(item) {
    if (map.items.length >= MAX_ITEMS) { notify(`Een kaart heeft hoogstens ${MAX_ITEMS} onderdelen`, true); return; }
    edit(() => { map.items.push(item); });
    select_(item.id);
  }
  function select_(id) {
    sel = id;
    renderItemForm();
    requestDraw();
  }
  function removeSelection() {
    if (!editable || !sel) return;
    const id = sel;
    edit(() => {
      if (id === 'robot') map.robot = null;
      else map.items = map.items.filter(i => i.id !== id);
    });
    select_(null);
  }

  function finishDraft(fromDouble) {
    const d = draft;
    if (!d) return;
    draft = null;
    const pts = d.points.slice();
    // A double click delivers two presses; drop the second one when it landed next to the first.
    if (fromDouble && pts.length >= 2) {
      const a = pts[pts.length - 2], b = pts[pts.length - 1];
      if (Math.hypot(X(a[0]) - X(b[0]), Y(a[1]) - Y(b[1])) < 10) pts.pop();
    }
    if (pts.length < 2) { requestDraw(); return; }
    addItem({ id: nextId(d.kind), kind: d.kind, label: '', points: pts, closed: !!d.closed });
  }

  // ---- hit testing
  function segDist(p, a, b) {
    const vx = b[0] - a[0], vy = b[1] - a[1], len2 = vx * vx + vy * vy;
    let t = len2 ? ((p.x - a[0]) * vx + (p.y - a[1]) * vy) / len2 : 0;
    t = clamp(t, 0, 1);
    const x = a[0] + vx * t, y = a[1] + vy * t;
    return { d: Math.hypot(p.x - x, p.y - y), x, y };
  }
  function segments(pts, closed) {
    const out = [];
    for (let i = 0; i + 1 < pts.length; i++) out.push([i, pts[i], pts[i + 1]]);
    if (closed && pts.length > 2) out.push([pts.length - 1, pts[pts.length - 1], pts[0]]);
    return out;
  }
  function hitItem(it, p, ps, tol) {
    if (it.points) {
      if (it.points.length === 1) return Math.hypot(p.x - it.points[0][0], p.y - it.points[0][1]) <= Math.max(tol, 0.1);
      return segments(it.points, it.closed).some(([, a, b]) => segDist(p, a, b).d <= Math.max(tol, 0.05));
    }
    if (RECTS.has(it.kind)) {
      const l = toLocal(it, p.x, p.y);
      return Math.abs(l.x) <= (it.w || 0) / 2 + tol * 0.5 && Math.abs(l.y) <= (it.h || 0) / 2 + tol * 0.5;
    }
    if (it.kind === 'label') {
      ctx.font = '14px system-ui, sans-serif';
      const w = ctx.measureText(it.label || 'Tekst').width;
      return Math.abs(ps.sx - X(it.x)) <= w / 2 + 4 && Math.abs(ps.sy - Y(it.y)) <= 11;
    }
    return Math.hypot(p.x - it.x, p.y - it.y) <= Math.max(tol, it.kind === 'marker' ? 0.15 : 0.2);
  }
  function hitTest(p, ps) {
    const tol = 8 / view.s;
    if (map.robot && Math.hypot(p.x - map.robot.x, p.y - map.robot.y) <= Math.max(0.2, tol)) return 'robot';
    const order = map.items.slice().reverse();
    for (let pass = 0; pass < 2; pass++) {       // zones last: they are big and often cover other things
      for (const it of order) {
        if ((it.kind === 'zone') !== (pass === 1)) continue;
        if (hitItem(it, p, ps, tol)) return it.id;
      }
    }
    return null;
  }

  function handlesFor() {
    const o = selObj();
    if (!o || !editable) return [];
    const kind = selKind(), hs = [];
    if (o.points) o.points.forEach((pt, i) => hs.push({ t: 'vertex', i, x: pt[0], y: pt[1] }));
    else if (RECTS.has(kind)) {
      for (const [sx, sy] of [[1, 1], [-1, 1], [-1, -1], [1, -1]]) {
        const w = toWorld(o, sx * o.w / 2, sy * o.h / 2);
        hs.push({ t: 'corner', sx, sy, x: w.x, y: w.y });
      }
      const r = toWorld(o, 0, o.h / 2 + 24 / view.s);
      hs.push({ t: 'rotate', x: r.x, y: r.y });
    }
    if (HEADINGS.has(kind)) {
      const h = rad(o.heading || 0), d = 40 / view.s;
      hs.push({ t: 'heading', x: o.x + Math.cos(h) * d, y: o.y + Math.sin(h) * d });
    }
    return hs;
  }
  function hitHandle(ps, touch_) {
    const r = touch_ ? 14 : 9;
    let best = null, bestD = r;
    for (const h of handlesFor()) {
      const d = Math.hypot(X(h.x) - ps.sx, Y(h.y) - ps.sy);
      if (d <= bestD) { best = h; bestD = d; }
    }
    return best;
  }

  // ---- pointer input
  function beginChange(d) {
    if (d.moved) return;
    d.moved = true;
    if (d.before) pushUndoText(d.before);
  }

  canvas.addEventListener('contextmenu', e => e.preventDefault());

  canvas.addEventListener('pointerdown', e => {
    canvas.focus({ preventScroll: true });
    if (drag) return;                              // ignore a second finger
    const ps = eventPos(e);
    const snapOn = !e.altKey;
    const p = snapPt(ps, snapOn);
    const base = { pid: e.pointerId, sx: ps.sx, sy: ps.sy, x0: ps.x, y0: ps.y, moved: false };
    if (e.button === 1 || e.button === 2 || (e.button === 0 && !editable)) {
      e.preventDefault();
      drag = { ...base, type: 'pan', cx: view.cx, cy: view.cy, clearSel: e.button === 0 };
      if (!editable && e.button === 0) {          // view only: a click still selects
        const id = hitTest(ps, ps);
        if (id) { select_(id); drag = null; return; }
      }
      canvas.setPointerCapture(e.pointerId);
      return;
    }
    if (e.button !== 0) return;
    canvas.setPointerCapture(e.pointerId);

    if (tool === 'select') {
      const h = hitHandle(ps, e.pointerType === 'touch');
      if (h) {
        drag = { ...base, type: 'handle', h, orig: clone(selObj()), before: JSON.stringify(map) };
        return;
      }
      const id = hitTest(ps, ps);
      if (id) {
        if (id !== sel) select_(id);
        drag = { ...base, type: 'move', orig: clone(selObj()), before: JSON.stringify(map) };
      } else {
        drag = { ...base, type: 'pan', cx: view.cx, cy: view.cy, clearSel: true };
      }
    } else if (tool === 'wall' || tool === 'fence') {
      if (!draft) draft = { kind: tool, points: [], closed: false };
      const first = draft.points[0];
      if (first && draft.points.length >= 3 && Math.hypot(X(first[0]) - ps.sx, Y(first[1]) - ps.sy) < 10) {
        draft.closed = true;
        finishDraft(false);
        return;
      }
      const last = draft.points[draft.points.length - 1];
      if (!last || last[0] !== p.x || last[1] !== p.y) {
        if (draft.points.length >= MAX_POINTS) notify(`Hoogstens ${MAX_POINTS} punten per lijn`, true);
        else draft.points.push([p.x, p.y]);
      }
      requestDraw();
    } else if (RECTS.has(tool)) {
      drag = { ...base, type: 'rect', kind: tool, a: p, b: p };
    } else if (tool === 'dock' || tool === 'marker' || tool === 'robot') {
      drag = { ...base, type: 'place', kind: tool, pos: p, heading: 0 };
    } else if (tool === 'label') {
      addItem({ id: nextId('label'), kind: 'label', label: 'Tekst', x: p.x, y: p.y });
      const input = itemBox.querySelector('input[type="text"]');
      if (input) { input.focus(); input.select(); }
    } else if (tool === 'calibrate') {
      calib.push({ x: r4(ps.x), y: r4(ps.y) });
      updateHint();
      requestDraw();
      if (calib.length === 2) {
        const [a, b] = calib;
        finishCalibration(a, b);
      }
    } else if (tool === 'bgmove' && map.background) {
      drag = { ...base, type: 'bgmove', orig: map.background.origin.slice(), before: JSON.stringify(map) };
    }
  });

  canvas.addEventListener('pointermove', e => {
    const ps = eventPos(e);
    const sp = snapPt(ps, !e.altKey);
    hover = { sx: ps.sx, sy: ps.sy, x: sp.x, y: sp.y };
    coords.textContent = `x ${sp.x.toFixed(2)} m   y ${sp.y.toFixed(2)} m`;
    if (drag) { if (e.pointerId === drag.pid) dragMove(e, ps, sp); }
    else if (draft) requestDraw();
  });

  function dragMove(e, ps, p) {
    const d = drag, snapOn = !e.altKey;
    const far = Math.hypot(ps.sx - d.sx, ps.sy - d.sy) > 3;
    switch (d.type) {
      case 'pan':
        if (!far && !d.moved) return;
        d.moved = true;
        view.cx = d.cx - (ps.sx - d.sx) / view.s;
        view.cy = d.cy + (ps.sy - d.sy) / view.s;
        break;
      case 'move': {
        if (!far && !d.moved) return;
        const o = selObj();
        if (!o) return;
        beginChange(d);
        let dx = ps.x - d.x0, dy = ps.y - d.y0;
        if (snapOn) { dx = Math.round(dx / SNAP) * SNAP; dy = Math.round(dy / SNAP) * SNAP; }
        if (d.orig.points) o.points = d.orig.points.map(([x, y]) => [clamp(r4(x + dx), -500, 500), clamp(r4(y + dy), -500, 500)]);
        else { o.x = clamp(r4(d.orig.x + dx), -500, 500); o.y = clamp(r4(d.orig.y + dy), -500, 500); }
        liveChange();
        break;
      }
      case 'handle': {
        if (!far && !d.moved) return;
        const o = selObj();
        if (!o) return;
        beginChange(d);
        const h = d.h, orig = d.orig;
        if (h.t === 'vertex') {
          o.points[h.i] = [clamp(p.x, -500, 500), clamp(p.y, -500, 500)];
        } else if (h.t === 'corner') {
          const l = toLocal(orig, ps.x, ps.y);
          const ox = -h.sx * orig.w / 2, oy = -h.sy * orig.h / 2;   // the opposite corner stays put
          let nw = Math.max(0.05, (l.x - ox) * h.sx), nh = Math.max(0.05, (l.y - oy) * h.sy);
          if (snapOn) { nw = Math.max(SNAP, Math.round(nw / SNAP) * SNAP); nh = Math.max(SNAP, Math.round(nh / SNAP) * SNAP); }
          nw = Math.min(nw, 500); nh = Math.min(nh, 500);
          const c = toWorld(orig, ox + h.sx * nw / 2, oy + h.sy * nh / 2);
          o.w = r4(nw); o.h = r4(nh); o.x = clamp(r4(c.x), -500, 500); o.y = clamp(r4(c.y), -500, 500);
        } else if (h.t === 'rotate') {
          o.angle = normAngle(snapAng(deg(Math.atan2(ps.y - o.y, ps.x - o.x)) - 90, snapOn));
        } else if (h.t === 'heading') {
          o.heading = normAngle(snapAng(deg(Math.atan2(ps.y - o.y, ps.x - o.x)), snapOn));
        }
        liveChange();
        break;
      }
      case 'rect':
        d.b = p;
        requestDraw();
        break;
      case 'place':
        if (Math.hypot(ps.sx - d.sx, ps.sy - d.sy) > 8) d.heading = normAngle(snapAng(deg(Math.atan2(ps.y - d.pos.y, ps.x - d.pos.x)), snapOn));
        requestDraw();
        break;
      case 'bgmove': {
        if (!far && !d.moved) return;
        beginChange(d);
        map.background.origin = [clamp(r4(d.orig[0] + ps.x - d.x0), -500, 500), clamp(r4(d.orig[1] + ps.y - d.y0), -500, 500)];
        liveChange();
        break;
      }
      default: break;
    }
    requestDraw();
  }
  // Cheap update while dragging: the page is told once, when the drag ends.
  function liveChange() { touch(); syncForms(); }

  function endDrag(e) {
    const d = drag;
    if (!d || e.pointerId !== d.pid) return;
    drag = null;
    if (e.type === 'pointercancel') { requestDraw(); return; }
    switch (d.type) {
      case 'pan':
        if (!d.moved && d.clearSel) select_(null);
        break;
      case 'move': case 'handle': case 'bgmove':
        if (d.moved) fire();
        break;
      case 'rect': {
        const w = Math.abs(d.b.x - d.a.x), h = Math.abs(d.b.y - d.a.y);
        const item = { id: nextId(d.kind), kind: d.kind, label: '', angle: 0 };
        if (w < 0.1 || h < 0.1) { const [dw, dh] = DEFAULT_SIZE[d.kind]; Object.assign(item, { x: d.a.x, y: d.a.y, w: dw, h: dh }); }
        else Object.assign(item, { x: r4((d.a.x + d.b.x) / 2), y: r4((d.a.y + d.b.y) / 2), w: r4(w), h: r4(h) });
        addItem(item);
        break;
      }
      case 'place': {
        const pose = { x: d.pos.x, y: d.pos.y, heading: d.heading };
        if (d.kind === 'robot') {
          edit(() => { map.robot = pose; });
          select_('robot');
          setTool('select');
        } else {
          const item = { id: nextId(d.kind), kind: d.kind, label: d.kind === 'dock' ? 'Dock' : '', ...pose };
          if (d.kind === 'marker') item.marker_id = nextMarker();
          addItem(item);
        }
        break;
      }
      default: break;
    }
    requestDraw();
  }
  canvas.addEventListener('pointerup', endDrag);
  canvas.addEventListener('pointercancel', endDrag);

  canvas.addEventListener('pointerleave', () => { if (!drag) { hover = null; coords.textContent = ''; requestDraw(); } });

  canvas.addEventListener('dblclick', e => {
    if (!editable) return;
    if (draft) { finishDraft(true); return; }
    if (tool !== 'select') return;
    const o = selObj();
    if (!o || !o.points) return;
    const ps = eventPos(e);
    const vi = o.points.findIndex(pt => Math.hypot(X(pt[0]) - ps.sx, Y(pt[1]) - ps.sy) <= 9);
    if (vi >= 0) {                                 // double click on a point removes it
      if (o.points.length > (o.closed ? 3 : 2)) edit(() => { o.points.splice(vi, 1); });
      return;
    }
    if (o.points.length >= MAX_POINTS) return;
    let best = null;                               // double click on a line adds a point
    for (const [i, a, b] of segments(o.points, o.closed)) {
      const r = segDist(ps, a, b);
      if (r.d * view.s <= 8 && (!best || r.d < best.d)) best = { ...r, i };
    }
    if (best) edit(() => { o.points.splice(best.i + 1, 0, [r4(best.x), r4(best.y)]); });
  });

  canvas.addEventListener('wheel', e => {
    e.preventDefault();
    const ps = eventPos(e);
    const f = Math.exp(-e.deltaY * (e.deltaMode === 1 ? 0.05 : 0.0015));
    const ns = clamp(view.s * f, 3, 3000);
    view.cx = ps.x - (ps.sx - W / 2) / ns;        // keep the world point under the cursor fixed
    view.cy = ps.y + (ps.sy - H / 2) / ns;
    view.s = ns;
    requestDraw();
  }, { passive: false });

  // ---- keyboard (only while focus is inside the editor, never while typing)
  root.addEventListener('keydown', e => {
    const t = e.target;
    if (t && t.closest && t.closest('input, textarea, select, [contenteditable="true"]')) return;
    const ctrl = e.ctrlKey || e.metaKey;
    const key = e.key;
    if (ctrl && !e.shiftKey && (key === 'z' || key === 'Z')) { e.preventDefault(); undo(); return; }
    if (ctrl && (key === 's' || key === 'S')) { e.preventDefault(); save(); return; }
    if (ctrl || e.altKey) return;
    const onCanvas = t === canvas;
    if (key === 'Escape') {
      if (draft || drag || tool === 'calibrate' || tool === 'bgmove') { draft = null; drag = null; setTool('select'); }
      else if (tool !== 'select') setTool('select');
      else select_(null);
      e.preventDefault();
    } else if (!editable) {
      return;
    } else if (key === 'Enter' && onCanvas && draft) {
      e.preventDefault(); finishDraft(false);
    } else if ((key === 'Delete' || key === 'Backspace') && sel && !draft) {
      e.preventDefault(); removeSelection();
    } else if (key.startsWith('Arrow') && sel && onCanvas && tool === 'select') {
      e.preventDefault();
      const step = e.shiftKey ? 0.25 : SNAP;
      const dx = key === 'ArrowLeft' ? -step : key === 'ArrowRight' ? step : 0;
      const dy = key === 'ArrowDown' ? -step : key === 'ArrowUp' ? step : 0;
      const o = selObj();
      if (o) edit(() => {
        if (o.points) o.points = o.points.map(([x, y]) => [clamp(r4(x + dx), -500, 500), clamp(r4(y + dy), -500, 500)]);
        else { o.x = clamp(r4(o.x + dx), -500, 500); o.y = clamp(r4(o.y + dy), -500, 500); }
      });
    } else if (key.length === 1) {
      const hit = TOOLS.find(tl => tl[3] === key.toLowerCase());
      if (hit) setTool(hit[0]);
    }
  });

  window.addEventListener('beforeunload', e => {
    if (dirty && editable) { e.preventDefault(); e.returnValue = ''; }
  });

  // ---- forms
  function syncForms() {
    for (const f of staticSync) f();
    for (const f of itemSync) f();
  }
  function renderAllForms() { renderMapForm(); renderBgForm(); renderItemForm(); }

  function field(labelText, input, cls = '') {
    return el('label', { class: 'me-field ' + cls }, el('span', { text: labelText }), input);
  }
  // A number input committing on change; get/set work on the live data, so undo and re-render stay correct.
  function numInput(opt, sink) {
    const input = el('input', { type: 'number', step: opt.step || 0.05, 'aria-label': opt.label });
    input.addEventListener('change', () => {
      let v = parseFloat(String(input.value).replace(',', '.'));
      if (!Number.isFinite(v)) { input.value = fmt(opt.get()); return; }
      v = clamp(v, opt.min ?? -500, opt.max ?? 500);
      v = opt.int ? Math.round(v) : r4(v);
      if (opt.angle) v = r4(normAngle(v));
      edit(() => opt.set(v));
      input.value = fmt(opt.get());
    });
    sink.push(() => { if (document.activeElement !== input) input.value = fmt(opt.get()); });
    input.value = fmt(opt.get());
    return field(opt.label, input);
  }

  function renderMapForm() {
    mapBox.textContent = '';
    staticSync = staticSync.filter(f => !f.isMap);
    const sync = [];
    mapBox.append(el('legend', { class: 'me-legend', text: 'Kaart' }));
    const grid = el('div', { class: 'me-grid' });
    grid.append(
      numInput({ label: 'Breedte (m)', min: 1, max: 500, step: 0.5, get: () => map.size[0], set: v => { map.size[0] = v; } }, sync),
      numInput({ label: 'Hoogte (m)', min: 1, max: 500, step: 0.5, get: () => map.size[1], set: v => { map.size[1] = v; } }, sync));
    const notes = el('textarea', { rows: '2', maxlength: '1000', 'aria-label': 'Notities' });
    notes.value = map.notes;
    notes.addEventListener('change', () => edit(() => { map.notes = notes.value; }));
    sync.push(() => { if (document.activeElement !== notes) notes.value = map.notes; });
    grid.append(field('Notities', notes, 'me-wide'));
    mapBox.append(grid);
    sync.forEach(f => { f.isMap = true; });
    staticSync.push(...sync);
    mapBox.disabled = !editable;
  }

  function renderBgForm() {
    bgBox.textContent = '';
    staticSync = staticSync.filter(f => !f.isBg);
    const sync = [];
    bgBox.append(el('legend', { class: 'me-legend', text: 'Achtergrond' }));
    const bg = map.background;
    if (!bg || !bg.file) {
      bgBox.append(el('p', { class: 'me-info', text: 'Nog geen afbeelding. Kies een foto van de tuin van boven, een plattegrond of een schets.' }));
    } else {
      const grid = el('div', { class: 'me-grid' });
      grid.append(
        numInput({ label: 'Schaal (m per pixel)', min: 1e-5, max: 10, step: 0.001, get: () => map.background && map.background.scale, set: v => { map.background.scale = v; } }, sync),
        numInput({ label: 'Links boven x (m)', get: () => map.background && map.background.origin[0], set: v => { map.background.origin[0] = v; } }, sync),
        numInput({ label: 'Links boven y (m)', get: () => map.background && map.background.origin[1], set: v => { map.background.origin[1] = v; } }, sync));
      const slider = el('input', { type: 'range', min: '0', max: '1', step: '0.05', 'aria-label': 'Doorzichtigheid van de achtergrond' });
      slider.value = String(bg.opacity);
      slider.addEventListener('input', () => {
        if (!map.background) return;
        if (sliderFresh) { pushUndoText(JSON.stringify(map)); sliderFresh = false; }
        map.background.opacity = Number(slider.value);
        touch(); requestDraw();
      });
      slider.addEventListener('change', () => { sliderFresh = true; fire(); });
      sync.push(() => { if (map.background && document.activeElement !== slider) slider.value = String(map.background.opacity); });
      grid.append(field('Zichtbaarheid', slider));
      bgBox.append(grid);
      const calBtn = el('button', { type: 'button', 'aria-pressed': 'false', text: 'Schaal instellen' });
      calBtn.addEventListener('click', () => setTool(tool === 'calibrate' ? 'select' : 'calibrate'));
      const moveBtn = el('button', { type: 'button', 'aria-pressed': 'false', text: 'Verplaatsen' });
      moveBtn.addEventListener('click', () => setTool(tool === 'bgmove' ? 'select' : 'bgmove'));
      pressables.push([calBtn, 'calibrate'], [moveBtn, 'bgmove']);
      const other = el('button', { type: 'button', text: 'Andere afbeelding' });
      other.addEventListener('click', () => fileInput.click());
      const remove = el('button', { type: 'button', class: 'me-danger', text: 'Achtergrond weghalen' });
      remove.addEventListener('click', () => { edit(() => { map.background = null; }); ensureBackground(); renderBgForm(); setTool('select'); });
      bgBox.append(el('div', { class: 'me-row' }, calBtn, moveBtn, other, remove));
      updateTools();
    }
    if (!bg || !bg.file) {
      const pick = el('button', { type: 'button', text: 'Afbeelding kiezen' });
      pick.addEventListener('click', () => fileInput.click());
      bgBox.append(el('div', { class: 'me-row' }, pick));
    }
    sync.forEach(f => { f.isBg = true; });
    staticSync.push(...sync);
    bgBox.disabled = !editable;
    // forget buttons of earlier renders
    for (let i = pressables.length - 1; i >= TOOLS.length; i--) if (!bgBox.contains(pressables[i][0])) pressables.splice(i, 1);
  }

  function renderItemForm() {
    itemBox.textContent = '';
    itemSync = [];
    const legend = el('legend', { class: 'me-legend', text: 'Onderdeel' });
    itemBox.append(legend);
    itemBox.disabled = !editable;
    const o = selObj();
    if (!o) {
      itemBox.append(el('p', { class: 'me-empty', text: 'Klik een onderdeel op de kaart om de getallen te zien en te wijzigen.' }));
      return;
    }
    const kind = selKind();
    legend.textContent = NAMES[kind] || kind;
    const key = k => () => { const cur = selObj(); return cur ? cur[k] : undefined; };
    const setKey = k => v => { const cur = selObj(); if (cur) cur[k] = v; };
    const grid = el('div', { class: 'me-grid' });
    itemBox.append(grid);

    if (kind !== 'robot') {
      const input = el('input', { type: 'text', maxlength: '60', 'aria-label': kind === 'label' ? 'Tekst' : 'Naam' });
      input.value = o.label || '';
      input.addEventListener('change', () => edit(() => setKey('label')(input.value.slice(0, 60))));
      itemSync.push(() => { const cur = selObj(); if (cur && document.activeElement !== input) input.value = cur.label || ''; });
      grid.append(field(kind === 'label' ? 'Tekst' : 'Naam', input, 'me-wide'));
    }
    if (o.points) {
      const closed = el('input', { type: 'checkbox', 'aria-label': 'Gesloten vorm' });
      closed.checked = !!o.closed;
      closed.addEventListener('change', () => edit(() => setKey('closed')(closed.checked)));
      itemSync.push(() => { const cur = selObj(); if (cur) closed.checked = !!cur.closed; });
      grid.append(field('Gesloten vorm', closed, 'me-check me-wide'));
      const info = el('p', { class: 'me-info me-wide' });
      itemSync.push(() => {
        const cur = selObj();
        if (!cur || !cur.points) return;
        let len = 0;
        for (const [, a, b] of segments(cur.points, cur.closed)) len += Math.hypot(a[0] - b[0], a[1] - b[1]);
        info.textContent = `${cur.points.length} punten, ${len.toFixed(2)} m lang. Sleep de punten op de kaart; dubbelklik op een lijn voegt een punt toe, dubbelklik op een punt haalt het weg.`;
      });
      grid.append(info);
    } else {
      grid.append(numInput({ label: 'x (m)', get: key('x'), set: setKey('x') }, itemSync),
        numInput({ label: 'y (m)', get: key('y'), set: setKey('y') }, itemSync));
      if (RECTS.has(kind)) {
        grid.append(numInput({ label: 'Breedte (m)', min: 0.05, max: 500, get: key('w'), set: setKey('w') }, itemSync),
          numInput({ label: 'Hoogte (m)', min: 0.05, max: 500, get: key('h'), set: setKey('h') }, itemSync),
          numInput({ label: 'Hoek (graden)', step: 1, angle: true, get: key('angle'), set: setKey('angle') }, itemSync));
      }
    }
    if (HEADINGS.has(kind)) {
      grid.append(numInput({ label: 'Kijkrichting (graden)', step: 5, angle: true, get: key('heading'), set: setKey('heading') }, itemSync));
      grid.append(el('p', { class: 'me-info me-wide', text: '0 = naar rechts (oost), 90 = omhoog (noord), tegen de klok in.' }));
    }
    if (kind === 'marker') {
      grid.append(numInput({ label: 'Markernummer', min: 0, max: 999, step: 1, int: true, get: key('marker_id'), set: setKey('marker_id') }, itemSync));
    }
    const row = el('div', { class: 'me-row' });
    if (kind !== 'robot') {
      const dup = el('button', { type: 'button', text: 'Dupliceren' });
      dup.addEventListener('click', () => {
        const cur = selObj();
        if (!cur) return;
        const copy = clone(cur);
        copy.id = nextId(cur.kind);
        if (copy.points) copy.points = copy.points.map(([x, y]) => [clamp(r4(x + 0.3), -500, 500), clamp(r4(y - 0.3), -500, 500)]);
        else { copy.x = clamp(r4(copy.x + 0.3), -500, 500); copy.y = clamp(r4(copy.y - 0.3), -500, 500); }
        if (copy.kind === 'marker') copy.marker_id = nextMarker();
        addItem(copy);
      });
      row.append(dup);
    }
    const del = el('button', { type: 'button', class: 'me-danger', text: 'Verwijderen' });
    del.addEventListener('click', removeSelection);
    row.append(del);
    itemBox.append(row);
    syncForms();
  }

  // ---- toolbar actions
  btnNew.addEventListener('click', () => { if (confirmDiscard()) newMap(); });
  btnSave.addEventListener('click', save);
  btnDel.addEventListener('click', deleteMap);
  btnUndo.addEventListener('click', undo);
  btnFit.addEventListener('click', fit);
  select.addEventListener('change', async () => {
    const name = select.value;
    if (!confirmDiscard()) { updateSelect(); return; }
    if (name) await load(name); else newMap();
  });

  // ---- drawing
  function requestDraw() {
    if (!raf) raf = requestAnimationFrame(draw);
  }

  function fit() {
    if (!W || !H) { needFit = true; return; }
    const pad = 28;
    view.s = clamp(Math.min((W - pad * 2) / map.size[0], (H - pad * 2) / map.size[1]), 3, 3000);
    view.cx = map.size[0] / 2;
    view.cy = map.size[1] / 2;
    needFit = false;
    requestDraw();
  }

  function resize() {
    const r = stage.getBoundingClientRect();
    const w = Math.floor(r.width), h = Math.floor(r.height);
    const ratio = window.devicePixelRatio || 1;
    if (w === W && h === H && ratio === dpr) return;
    W = w; H = h; dpr = ratio;
    canvas.width = Math.max(1, Math.round(W * dpr));
    canvas.height = Math.max(1, Math.round(H * dpr));
    if (needFit && W && H) fit();
    requestDraw();
  }

  function drawGrid() {
    const s = view.s;
    const x0 = view.cx - W / 2 / s, x1 = view.cx + W / 2 / s, y0 = view.cy - H / 2 / s, y1 = view.cy + H / 2 / s;
    const steps = [1, 2, 5, 10, 20, 50, 100, 200];
    const strong = s >= 14 ? 1 : (steps.find(m => m * s >= 14) || 500);
    const labelStep = steps.find(m => m * s >= 45) || 500;
    const lines = (step, color, width) => {
      ctx.beginPath();
      for (let i = Math.ceil(x0 / step); i <= Math.floor(x1 / step); i++) {
        const px = Math.round(X(i * step)) + 0.5; ctx.moveTo(px, 0); ctx.lineTo(px, H);
      }
      for (let i = Math.ceil(y0 / step); i <= Math.floor(y1 / step); i++) {
        const py = Math.round(Y(i * step)) + 0.5; ctx.moveTo(0, py); ctx.lineTo(W, py);
      }
      ctx.strokeStyle = color; ctx.lineWidth = width; ctx.stroke();
    };
    if (0.5 * s >= 7) lines(0.5, 'rgba(120,150,180,.10)', 1);
    lines(strong, 'rgba(120,150,180,.26)', 1);
    ctx.fillStyle = 'rgba(160,180,200,.8)';
    ctx.font = '10px system-ui, sans-serif';
    ctx.textBaseline = 'alphabetic';
    ctx.textAlign = 'left';
    for (let i = Math.ceil(x0 / labelStep); i <= Math.floor(x1 / labelStep); i++) ctx.fillText(String(i * labelStep), X(i * labelStep) + 3, H - 4);
    for (let i = Math.ceil(y0 / labelStep); i <= Math.floor(y1 / labelStep); i++) ctx.fillText(String(i * labelStep), 3, Y(i * labelStep) - 3);
  }

  function arrow(x, y, headingDeg, len, color, width) {
    const px = X(x), py = Y(y), a = rad(headingDeg);
    const ex = px + Math.cos(a) * len, ey = py - Math.sin(a) * len;
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = width; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(ex, ey); ctx.stroke();
    const hl = Math.min(10, len * 0.5), b = Math.PI / 7;
    ctx.beginPath();
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - Math.cos(a - b) * hl, ey + Math.sin(a - b) * hl);
    ctx.lineTo(ex - Math.cos(a + b) * hl, ey + Math.sin(a + b) * hl);
    ctx.closePath(); ctx.fill();
  }

  function itemText(text, px, py, color = 'rgba(230,237,243,.85)') {
    if (!text) return;
    ctx.font = '11px system-ui, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(11,17,24,.8)'; ctx.strokeText(text, px, py);
    ctx.fillStyle = color; ctx.fillText(text, px, py);
  }

  function rectPath(o, w, h) {
    ctx.translate(X(o.x), Y(o.y));
    ctx.rotate(-rad(o.angle || 0));
    ctx.beginPath(); ctx.rect(-w / 2, -h / 2, w, h);
  }

  function drawItem(it, selected) {
    const s = view.s, k = it.kind;
    if (it.points) {
      const pts = it.points;
      if (!pts.length) return;
      ctx.beginPath();
      pts.forEach(([x, y], i) => { if (i) ctx.lineTo(X(x), Y(y)); else ctx.moveTo(X(x), Y(y)); });
      if (it.closed && pts.length > 2) ctx.closePath();
      ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      const lw = Math.max(2, 0.08 * s);
      if (selected) { ctx.strokeStyle = 'rgba(255,211,61,.5)'; ctx.lineWidth = lw + 6; ctx.stroke(); }
      ctx.strokeStyle = k === 'fence' ? COLORS.fence : COLORS.wall;
      ctx.lineWidth = lw;
      ctx.setLineDash(k === 'fence' ? [lw * 2.4, lw * 1.6] : []);
      ctx.stroke(); ctx.setLineDash([]);
      if (pts.length === 1) { ctx.beginPath(); ctx.arc(X(pts[0][0]), Y(pts[0][1]), lw, 0, 7); ctx.fillStyle = ctx.strokeStyle; ctx.fill(); }
      itemText(it.label, X(pts[0][0]), Y(pts[0][1]) - 10);
      return;
    }
    if (RECTS.has(k)) {
      const w = (it.w || 0) * s, h = (it.h || 0) * s;
      ctx.save();
      rectPath(it, w, h);
      if (k === 'coop') { ctx.fillStyle = COLORS.coopFill; ctx.fill(); ctx.strokeStyle = COLORS.coop; ctx.lineWidth = 2.5; }
      else if (k === 'house') { ctx.fillStyle = COLORS.house; ctx.fill(); ctx.strokeStyle = COLORS.houseLine; ctx.lineWidth = 2; }
      else if (k === 'obstacle') { ctx.fillStyle = COLORS.obstacle; ctx.fill(); ctx.strokeStyle = COLORS.obstacleLine; ctx.lineWidth = 1.5; }
      else { ctx.fillStyle = COLORS.zoneFill; ctx.fill(); ctx.strokeStyle = COLORS.zone; ctx.lineWidth = 1.5; ctx.setLineDash([6, 4]); }
      ctx.stroke(); ctx.setLineDash([]);
      if (selected) { ctx.strokeStyle = COLORS.select; ctx.lineWidth = 2; ctx.setLineDash([]); ctx.strokeRect(-w / 2 - 3, -h / 2 - 3, w + 6, h + 6); }
      ctx.restore();
      itemText(it.label, X(it.x), Y(it.y));
      return;
    }
    const px = X(it.x), py = Y(it.y);
    if (k === 'dock') {
      const r = Math.max(9, 0.18 * s);
      ctx.beginPath(); ctx.arc(px, py, r, 0, 7);
      ctx.fillStyle = 'rgba(47,129,247,.25)'; ctx.fill();
      ctx.strokeStyle = selected ? COLORS.select : COLORS.dock; ctx.lineWidth = 2.5; ctx.stroke();
      arrow(it.x, it.y, it.heading || 0, Math.max(r + 8, 0.4 * s), COLORS.dock, 2.5);
      itemText(it.label, px, py + r + 9);
    } else if (k === 'marker') {
      const size = Math.max(16, 0.25 * s), half = size / 2;
      const a = rad(it.heading || 0);
      ctx.fillStyle = '#fff'; ctx.fillRect(px - half, py - half, size, size);
      const m = size * 0.16;
      ctx.fillStyle = '#000'; ctx.fillRect(px - half + m, py - half + m, size - 2 * m, size - 2 * m);
      ctx.strokeStyle = selected ? COLORS.select : '#888'; ctx.lineWidth = selected ? 2.5 : 1; ctx.strokeRect(px - half, py - half, size, size);
      ctx.fillStyle = '#fff'; ctx.font = `bold ${Math.max(8, Math.min(14, size * 0.4))}px system-ui, sans-serif`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(String(it.marker_id ?? ''), px, py + 0.5);
      // facing direction: a short tick leaving the square
      ctx.strokeStyle = '#f0883e'; ctx.lineWidth = 2.5; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(px + Math.cos(a) * half, py - Math.sin(a) * half);
      ctx.lineTo(px + Math.cos(a) * (half + 9), py - Math.sin(a) * (half + 9)); ctx.stroke();
      itemText(it.label, px, py + half + 10);
    } else if (k === 'label') {
      ctx.font = '14px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      const text = it.label || 'Tekst';
      ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(11,17,24,.85)'; ctx.lineJoin = 'round'; ctx.strokeText(text, px, py);
      ctx.fillStyle = '#fff'; ctx.fillText(text, px, py);
      if (selected) {
        const w = ctx.measureText(text).width;
        ctx.strokeStyle = COLORS.select; ctx.lineWidth = 1.5; ctx.strokeRect(px - w / 2 - 4, py - 11, w + 8, 22);
      }
    }
    if (selected && k !== 'label' && k !== 'dock' && k !== 'marker') {
      ctx.beginPath(); ctx.arc(px, py, 10, 0, 7); ctx.strokeStyle = COLORS.select; ctx.lineWidth = 2; ctx.stroke();
    }
  }

  // Filled triangle of about 0.3 m: tip forward.
  function drawRobot(pose, solid, selected) {
    const len = Math.max(16, 0.3 * view.s), halfW = len * 0.36;
    ctx.save();
    ctx.translate(X(pose.x), Y(pose.y));
    ctx.rotate(-rad(pose.heading || 0));
    ctx.beginPath();
    ctx.moveTo(len / 2, 0); ctx.lineTo(-len / 2, halfW); ctx.lineTo(-len / 2 + len * 0.2, 0); ctx.lineTo(-len / 2, -halfW);
    ctx.closePath();
    if (solid) { ctx.fillStyle = COLORS.robot; ctx.fill(); ctx.strokeStyle = '#0b1118'; ctx.lineWidth = 1.5; }
    else { ctx.fillStyle = 'rgba(63,185,80,.22)'; ctx.fill(); ctx.strokeStyle = COLORS.robot; ctx.lineWidth = 2; ctx.setLineDash([5, 3]); }
    ctx.stroke();
    ctx.setLineDash([]);
    if (selected) { ctx.beginPath(); ctx.arc(0, 0, len * 0.7, 0, 7); ctx.strokeStyle = COLORS.select; ctx.lineWidth = 2; ctx.stroke(); }
    ctx.restore();
  }

  function drawHandles() {
    const o = selObj();
    if (!o) return;
    const hs = handlesFor();
    const rot = hs.find(h => h.t === 'rotate');
    if (rot) {
      const top = toWorld(o, 0, o.h / 2);
      ctx.strokeStyle = COLORS.select; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(X(top.x), Y(top.y)); ctx.lineTo(X(rot.x), Y(rot.y)); ctx.stroke();
    }
    for (const h of hs) {
      const px = X(h.x), py = Y(h.y);
      if (h.t === 'heading') {
        ctx.strokeStyle = COLORS.select; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(X(o.x), Y(o.y)); ctx.lineTo(px, py); ctx.stroke();
      }
      ctx.beginPath();
      if (h.t === 'rotate' || h.t === 'heading') ctx.arc(px, py, 5.5, 0, 7); else ctx.rect(px - 4.5, py - 4.5, 9, 9);
      ctx.fillStyle = h.t === 'heading' || h.t === 'rotate' ? COLORS.select : '#fff';
      ctx.fill(); ctx.strokeStyle = '#0b1118'; ctx.lineWidth = 1.5; ctx.stroke();
    }
  }

  function drawDraft() {
    if (draft && draft.points.length) {
      const lw = Math.max(2, 0.08 * view.s);
      ctx.beginPath();
      draft.points.forEach(([x, y], i) => { if (i) ctx.lineTo(X(x), Y(y)); else ctx.moveTo(X(x), Y(y)); });
      if (hover) ctx.lineTo(X(hover.x), Y(hover.y));
      ctx.strokeStyle = draft.kind === 'fence' ? COLORS.fence : COLORS.wall;
      ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.setLineDash(draft.kind === 'fence' ? [lw * 2.4, lw * 1.6] : [8, 6]); ctx.stroke(); ctx.setLineDash([]);
      draft.points.forEach(([x, y], i) => {
        ctx.beginPath(); ctx.arc(X(x), Y(y), i === 0 ? 5 : 3.5, 0, 7);
        ctx.fillStyle = i === 0 ? COLORS.select : '#fff'; ctx.fill();
      });
      if (hover) {
        const last = draft.points[draft.points.length - 1];
        const len = Math.hypot(hover.x - last[0], hover.y - last[1]);
        itemText(`${len.toFixed(2)} m`, X(hover.x) + 30, Y(hover.y) - 12, '#fff');
      }
    }
    if (drag && drag.type === 'rect') {
      const a = drag.a, b = drag.b;
      const x = Math.min(X(a.x), X(b.x)), y = Math.min(Y(a.y), Y(b.y));
      const w = Math.abs(X(b.x) - X(a.x)), h = Math.abs(Y(b.y) - Y(a.y));
      ctx.fillStyle = 'rgba(255,255,255,.08)'; ctx.fillRect(x, y, w, h);
      ctx.strokeStyle = COLORS.select; ctx.lineWidth = 1.5; ctx.setLineDash([6, 4]); ctx.strokeRect(x, y, w, h); ctx.setLineDash([]);
      itemText(`${Math.abs(b.x - a.x).toFixed(2)} × ${Math.abs(b.y - a.y).toFixed(2)} m`, x + w / 2, y + h / 2, '#fff');
    }
    if (drag && drag.type === 'place') {
      if (drag.kind === 'robot') drawRobot({ ...drag.pos, heading: drag.heading }, false, false);
      else drawItem({ kind: drag.kind, x: drag.pos.x, y: drag.pos.y, heading: drag.heading, marker_id: drag.kind === 'marker' ? nextMarker() : 0, label: '' }, true);
      arrow(drag.pos.x, drag.pos.y, drag.heading, 44, COLORS.select, 1.5);
    }
    if (calib) {
      ctx.strokeStyle = '#ff7b72'; ctx.fillStyle = '#ff7b72'; ctx.lineWidth = 1.5;
      if (calib.length === 1 && hover) {
        ctx.setLineDash([5, 4]); ctx.beginPath(); ctx.moveTo(X(calib[0].x), Y(calib[0].y)); ctx.lineTo(hover.sx, hover.sy); ctx.stroke(); ctx.setLineDash([]);
      }
      for (const c of calib) {
        const px = X(c.x), py = Y(c.y);
        ctx.beginPath(); ctx.moveTo(px - 8, py); ctx.lineTo(px + 8, py); ctx.moveTo(px, py - 8); ctx.lineTo(px, py + 8); ctx.stroke();
        ctx.beginPath(); ctx.arc(px, py, 4, 0, 7); ctx.stroke();
      }
    }
  }

  function drawScaleBar() {
    const nice = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200];
    let len = nice[0];
    for (const n of nice) if (n * view.s <= 140) len = n;
    const px = len * view.s, x = 12, y = H - 16;
    ctx.strokeStyle = '#e6edf3'; ctx.lineWidth = 2; ctx.lineCap = 'butt';
    ctx.beginPath(); ctx.moveTo(x, y - 4); ctx.lineTo(x, y); ctx.lineTo(x + px, y); ctx.lineTo(x + px, y - 4); ctx.stroke();
    ctx.fillStyle = '#e6edf3'; ctx.font = '11px system-ui, sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
    ctx.fillText(`${len} m`, x, y - 8);
  }

  function draw() {
    raf = 0;
    if (!W || !H) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = '#0b1118'; ctx.fillRect(0, 0, W, H);
    // map area
    const [mw, mh] = map.size;
    ctx.fillStyle = '#121c26';
    ctx.fillRect(X(0), Y(mh), mw * view.s, mh * view.s);
    // background picture below everything else
    const bg = map.background;
    if (bg && bgImg && bgImg.complete && bgImg.naturalWidth) {
      ctx.save();
      ctx.globalAlpha = clamp(bg.opacity, 0, 1);
      ctx.imageSmoothingEnabled = true;
      ctx.drawImage(bgImg, X(bg.origin[0]), Y(bg.origin[1]), bgImg.naturalWidth * bg.scale * view.s, bgImg.naturalHeight * bg.scale * view.s);
      ctx.restore();
    }
    drawGrid();
    ctx.strokeStyle = 'rgba(88,166,255,.7)'; ctx.lineWidth = 1.5; ctx.setLineDash([]);
    ctx.strokeRect(X(0), Y(mh), mw * view.s, mh * view.s);

    drawScans();
    for (const it of map.items) drawItem(it, it.id === sel);
    if (map.robot) drawRobot(map.robot, false, sel === 'robot');
    drawHandles();
    drawDraft();

    // live robot with fading trail
    if (trail.length > 1) {
      ctx.lineWidth = 2.5; ctx.lineCap = 'round';
      for (let i = 1; i < trail.length; i++) {
        ctx.strokeStyle = `rgba(63,185,80,${(0.08 + 0.7 * i / trail.length).toFixed(3)})`;
        ctx.beginPath(); ctx.moveTo(X(trail[i - 1].x), Y(trail[i - 1].y)); ctx.lineTo(X(trail[i].x), Y(trail[i].y)); ctx.stroke();
      }
    }
    if (live) drawRobot(live, true, false);
    drawScaleBar();
  }

  // ---- turn-and-scan layers: floor picture, viewing directions, measured outline, recognised things
  const OBJECT_COLORS = { fox: '#f0883e', chicken: '#f5f5f0', hen: '#f5f5f0', person: '#58a6ff', face: '#58a6ff' };
  function scanImage(url) {
    if (!scanImages.has(url)) {
      const img = new Image();
      img.onload = requestDraw;
      img.src = url;
      scanImages.set(url, img);
    }
    return scanImages.get(url);
  }
  function drawScans() {
    for (const s of scans) {
      if (s.hidden) continue;
      const g = s.ground;
      if (g) {
        const img = scanImage(`${apiBase}${API}/scans/${encodeURIComponent(s.id)}/files/${g.file}?v=${s.created}`);
        if (img.complete && img.naturalWidth) {
          ctx.save(); ctx.globalAlpha = .9; ctx.imageSmoothingEnabled = true;
          ctx.drawImage(img, X(g.x0), Y(g.y0), g.size * view.s, g.size * view.s);
          ctx.restore();
        }
      }
      // A short ray per photo: where the camera looked.
      ctx.strokeStyle = 'rgba(210,153,255,.55)'; ctx.lineWidth = 1;
      for (const step of s.steps || []) {
        if (!step.frame) continue;
        const a = rad(s.heading + step.heading);
        ctx.beginPath(); ctx.moveTo(X(s.x), Y(s.y));
        ctx.lineTo(X(s.x + Math.cos(a) * .35), Y(s.y + Math.sin(a) * .35)); ctx.stroke();
      }
      ctx.beginPath(); ctx.arc(X(s.x), Y(s.y), 6, 0, 7);
      ctx.fillStyle = '#d299ff'; ctx.fill(); ctx.strokeStyle = '#0b1118'; ctx.lineWidth = 1.5; ctx.stroke();
      // Measured distances: dots, joined into the outline.
      ctx.strokeStyle = '#ff9e3d'; ctx.lineWidth = Math.max(2, .03 * view.s); ctx.lineJoin = 'round';
      for (const line of s.outline || []) {
        ctx.beginPath();
        line.forEach(([x, y], i) => (i ? ctx.lineTo(X(x), Y(y)) : ctx.moveTo(X(x), Y(y))));
        ctx.stroke();
      }
      ctx.fillStyle = '#ff9e3d';
      for (const p of s.points || []) { ctx.beginPath(); ctx.arc(X(p.x), Y(p.y), 2.5, 0, 7); ctx.fill(); }
      for (const o of s.objects || []) {
        const px = X(o.x), py = Y(o.y);
        ctx.beginPath(); ctx.arc(px, py, 7, 0, 7);
        ctx.fillStyle = OBJECT_COLORS[String(o.label).toLowerCase()] || '#3fb950'; ctx.fill();
        ctx.strokeStyle = '#0b1118'; ctx.lineWidth = 1.5; ctx.stroke();
        itemText(`${o.label} ${Math.round(o.score)}%`, px, py - 14, '#fff');
      }
    }
  }
  function setScans(list) {
    scans = Array.isArray(list) ? list : [];
    requestDraw();
  }
  /** Walls from measured outlines ([[x, y], ...] each): one undoable step. */
  function addWalls(lines) {
    if (!editable) return 0;
    const usable = (lines || []).filter(line => Array.isArray(line) && line.length >= 2).slice(0, MAX_ITEMS - map.items.length);
    if (!usable.length) return 0;
    edit(() => {
      for (const line of usable) {
        map.items.push({ id: nextId('wall'), kind: 'wall', label: 'Gescand', closed: false,
          points: line.slice(0, MAX_POINTS).map(([x, y]) => [r4(x), r4(y)]) });
      }
    });
    return usable.length;
  }

  // ---- public API
  function setRobotPose(pose) {
    const x = pose ? Number(pose.x) : NaN, y = pose ? Number(pose.y) : NaN;
    if (!Number.isFinite(x) || !Number.isFinite(y)) { live = null; trail.length = 0; }
    else {
      const heading = Number(pose.heading);
      live = { x, y, heading: Number.isFinite(heading) ? heading : 0 };
      const last = trail[trail.length - 1];
      if (!last || Math.hypot(last.x - x, last.y - y) > 0.01) {
        trail.push({ x, y });
        if (trail.length > TRAIL_LIMIT) trail.shift();
      }
    }
    requestDraw();
  }

  function setEditable(value) {
    editable = !!value && options.canEdit !== false;
    root.classList.toggle('me-readonly', !editable);
    for (const node of editOnly) node.hidden = !editable;
    if (!editable) { draft = null; drag = null; calib = null; tool = 'select'; }
    mapBox.disabled = itemBox.disabled = bgBox.disabled = !editable;
    updateTools();
    updateDirtyUI();
    requestDraw();
  }

  new ResizeObserver(resize).observe(stage);
  window.addEventListener('resize', resize);

  // initial state
  setEditable(editable);
  renderAllForms();
  updateSelect();
  updateDirtyUI();
  updateTools();
  resize();
  refreshList();
  api('/info').then(info => { if (info && info.can_edit === false) setEditable(false); }).catch(() => {});

  return {
    load,
    current: () => clone(map),
    get dirty() { return dirty; },
    setRobotPose,
    setScans,
    addWalls,
    resize,
  };
}
