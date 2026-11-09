'use strict';
const C = BittleCore,
  $ = s => document.querySelector(s),
  esc = s => String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  } [c]));
const icons = {
  grid: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  home: 'M3 10l9-7 9 7v11H3z M9 21v-8h6v8',
  route: 'M5 5h10a5 5 0 0 1 0 10H9 M5 2v6 M2 5h6 M9 12l-3 3 3 3',
  pin: 'M12 22s8-8 8-14a8 8 0 1 0-16 0c0 6 8 14 8 14z M9 8a3 3 0 1 0 6 0a3 3 0 1 0-6 0',
  clock: 'M12 7v5l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
  leaf: 'M20 3C8 1 2 9 6 16s14 2 14-13z M4 21l11-12',
  stop: 'M6 6h12v12H6z',
  arrow: 'M5 12h14 M14 7l5 5-5 5',
  plus: 'M12 5v14 M5 12h14',
  pause: 'M8 5v14 M16 5v14',
  play: 'M7 4l14 8-14 8z',
  battery: 'M2 6h17v12H2z M22 10v4 M5 9h10v6H5z',
  wifi: 'M3 8a15 15 0 0 1 18 0 M6 12a10 10 0 0 1 12 0 M9 16a5 5 0 0 1 6 0 M12 20h.01',
  egg: 'M20 15c0 10-16 10-16 0C4 8 9 2 12 2s8 6 8 13z',
  water: 'M12 2S4 11 4 16a8 8 0 0 0 16 0c0-5-8-14-8-14z',
  door: 'M5 21V3h14v18 M3 21h18 M14 12h1',
  fence: 'M5 3v18 M12 3v18 M19 3v18 M3 8h18 M3 16h18',
  select: 'M5 3l15 9-7 2-3 7z',
  undo: 'M8 4L3 9l5 5 M3 9h12a6 6 0 0 1 0 12',
  redo: 'M16 4l5 5-5 5 M21 9H9a6 6 0 0 0 0 12',
  trash: 'M3 6h18 M9 6V3h6v3 M6 6l1 15h10l1-15 M10 10v7 M14 10v7',
  download: 'M12 3v12 M7 10l5 5 5-5 M4 16v5h16v-5',
  upload: 'M12 16V3 M7 8l5-5 5 5 M4 16v5h16v-5',
  check: 'M4 12l5 5L20 6',
  edit: 'M4 16L16 4l4 4L8 20H4z',
  camera: 'M3 7h5l2-3h4l2 3h5v14H3z M8 14a4 4 0 1 0 8 0a4 4 0 1 0-8 0',
  zone: 'M3 3h18v18H3z M3 3l18 18 M3 11l10 10 M11 3l10 10',
  reset: 'M3 10a9 9 0 1 1 1 9 M3 3v7h7'
};

function icon(name, cls = '') {
  return `<svg class="icon ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${icons[name]||icons.grid}"/></svg>`;
}
document.querySelectorAll('[data-icon]').forEach(e => e.innerHTML = icon(e.dataset.icon));
const navs = [
  ['overzicht', 'grid', 'Overzicht'],
  ['terrein', 'home', 'Mijn kippenhok'],
  ['patrouilles', 'route', 'Patrouilles'],
  ['buurt', 'pin', 'In de buurt'],
  ['activiteit', 'clock', 'Activiteit'],
  ['techniek', 'select', 'Techniek']
];
$('#nav').innerHTML = navs.map(([id, i, n]) => `<a href="#${id}" data-page="${id}">${icon(i)}<span>${n}</span>${id==='buurt'?'<b class="nav-count">2</b>':''}</a>`).join('');
let data = {
    ...LocalApp.project,
    events: LocalApp.events
  },
  storageOK = true;
let page = 'overzicht',
  view = null,
  selection = null,
  tool = 'select',
  draft = [],
  undo = [],
  redo = [],
  drag = null,
  toastTimer, zoom = 1;
let robot = {
    x: 300,
    y: 420,
    heading: 0,
    moving: false
  },
  last = performance.now();

function status() {
  const t = LocalApp.telemetry;
  if (!LocalApp.connected) return 'Server offline';
  if (!t?.connected) return 'Verbinding verloren';
  return t.mode === 'patrol' ? `Patrouille · ${t.route_name||'Tuin'}` : ({
    paused: 'Gepauzeerd',
    stopped: 'Gestopt',
    docked: 'Bij het dock',
    dock: 'Terug naar dock',
    eggs: 'Naar het legnest',
    water: 'Naar de drinkbak',
    checking: 'Controle bezig',
    done: 'Controlebezoek afgerond',
    blocked: 'Route geblokkeerd'
  } [t.mode] || 'Gereed');
}

function notify(message) {
  $('#toast').textContent = message;
  $('#toast').hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $('#toast').hidden = true, 3600);
}

function persist() {
  LocalApp.save(data);
}

function snapshot() {
  undo.push(JSON.stringify(data));
  if (undo.length > 40) undo.shift();
  redo = [];
}

function log() {
  persist();
}

function age(t) {
  const n = Math.max(0, Math.floor((Date.now() - t) / 60000));
  return n < 1 ? 'nu' : n < 60 ? `${n} min` : `${Math.floor(n/60)} u`;
}

function stamp(t) {
  return `<span class="freshness" title="Bijgewerkt ${age(t)} geleden" aria-label="Bijgewerkt ${age(t)} geleden">${icon('clock')}${age(t)}</span>`;
}

function eggs() {
  const shapes = Array.from({length: Math.min(data.eggs,6)}, (_,i) => '<span class="egg" style="--turn:'+[-12,5,16,-5,10,-10][i]+'deg;--i:'+i+'"></span>').join('');
  const extra = data.eggs===0 ? '<span class="empty-nest">Leeg nest</span>' : data.eggs>6 ? '<span class="egg-more">+'+(data.eggs-6)+'</span>' : '';
  return '<div class="eggs-visual" aria-label="'+data.eggs+' eieren">'+shapes+extra+'</div>';
}

function render() {
    view?.destroy();
    page = navs.some(n => n[0] === location.hash.slice(1)) ? location.hash.slice(1) : 'overzicht';
    if (page === 'terrein' && LocalApp.telemetry?.moving) sendCommand('pause');
    selection = null;
    tool = 'select';
    draft = [];
    zoom = 1;
    const name = navs.find(n => n[0] === page)[2];
    $('#page-title').textContent = name;
    $('#crumb').textContent = name;
    document.title = `Bittle — ${name}`;
    document.querySelectorAll('#nav a').forEach(a => {
      a.classList.toggle('active', a.dataset.page === page);
      if (a.dataset.page === page) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    $('#page').innerHTML = page === 'overzicht' ? dashboard() : page === 'terrein' ? editor() : page === 'patrouilles' ? missions() : page === 'buurt' ? buurt() : page === 'techniek' ? technical() : `<section class="panel activity-page"><div class="section-heading"><h2>Vandaag</h2><span>${(data.events||[]).length} gebeurtenissen</span></div><ol class="event-list">${events(80)}</ol></section>`;
    const canvas = $('#terrain-canvas');
    if (canvas) {
      view = new TerrainView(canvas, () => data, {
        editor: page === 'terrein',
        robot: () => robot
      });
      view.samples = trailHistory;
      if (page === 'terrein') bindEditor(canvas);
    }
    if (page === 'terrein') inspector();
    syncStatus();
  }

  function syncStatus() {
    document.querySelectorAll('.robot-status').forEach(e => e.textContent = status());
    const t = LocalApp.telemetry || {},
      connected = LocalApp.connected && t.connected;
    const b = $('#toggle-motion');
    if (b) {
      b.innerHTML = icon(robot.moving ? 'pause' : 'play');
      b.setAttribute('aria-label', robot.moving ? 'Pauzeren' : 'Patrouille starten');
    }
    if ($('#battery-value')) $('#battery-value').textContent = connected && t.battery_percent != null ? t.battery_percent + '%' : '—';
    if ($('#battery-status')) $('#battery-status').classList.toggle('warning', connected && t.battery_percent < 20);
    if ($('#door-state')) $('#door-state').textContent = !connected ? 'Onbekend' : t.door === 'closed' ? 'Gesloten' : t.door === 'open' ? 'Open' : 'Onbekend';
    $('.door-card')?.classList.toggle('door-open', connected && t.door === 'open');
    if ($('#door-freshness')) $('#door-freshness').innerHTML = stamp(t.observed_at || Date.now());
    $('.sidebar-bottom').classList.toggle('warning', !connected);
    document.querySelectorAll('[data-action="patrol"],[data-action="dock"],[data-action="eggs"],[data-action="water"],[data-action="toggle"],[data-route-start]').forEach(e => e.disabled = !connected);
    const badge = $('#connection-notice');
    if (badge) {
      badge.hidden = connected;
      badge.textContent = LocalApp.connected ? 'Simulatorverbinding verloren' : 'Lokale server offline';
    }
    updateTechnical();
  }
  async function sendCommand(action, routeId) {
    try {
      const result = await LocalApp.command(action, routeId);
      if (result.status === 'accepted') notify('Opdracht geaccepteerd');
    } catch (e) {
      notify(e.message);
    }
  }

  function startPatrol(id) {
    sendCommand('patrol', id || data.routes[0]?.id);
  }

  function task(kind) {
    sendCommand(kind);
  }
  let trailHistory = [];

  function tick(now) {
    const dt = Math.min((now - last) / 1000, .1);
    last = now;
    const t = LocalApp.telemetry;
    const connected = LocalApp.connected && t?.connected;
    robot.moving = !!(connected && t.moving);
    if (connected && t.pose) {
      const blend = Math.min(1, dt * 14);
      robot.x += (t.pose.x - robot.x) * blend;
      robot.y += (t.pose.y - robot.y) * blend;
      let a = t.pose.heading - robot.heading;
      while (a > Math.PI) a -= Math.PI * 2;
      while (a < -Math.PI) a += Math.PI * 2;
      robot.heading += a * blend;
    }
    trailHistory = trailHistory.filter(p => now - p.t < 120000);
    if (view) view.samples = trailHistory;
    requestAnimationFrame(tick);
  }

  function updateTechnical() {
    const t = LocalApp.telemetry;
    if ($('#raw-telemetry')) $('#raw-telemetry').textContent = JSON.stringify(t, null, 2);
    if ($('#command-list')) $('#command-list').innerHTML = (t?.commands || []).map(c => `<div class="command-row"><span>${esc(c.action)}<small>${esc(c.message)}</small></span><b class="command-${esc(c.status)}">${esc({accepted:'Bezig',completed:'Uitgevoerd',failed:'Mislukt',cancelled:'Afgebroken'}[c.status]||c.status)}</b></div>`).join('') || '<p class="muted">Nog geen opdrachten verstuurd.</p>';
  }

  function inspector() {
    const o = data.objects.find(o => o.id === selection),
      r = data.routes.find(r => r.id === selection) || data.zones.find(r => r.id === selection);
    $('#inspector-content').innerHTML = o ? `<span class="eyebrow">EIGENSCHAPPEN</span><h2>${C.TYPES[o.type].name}</h2><label>Naam<input id="object-name" value="${esc(o.name)}" maxlength="60"></label><div class="field-pair"><label>X<input type="number" id="object-x" min="30" max="930" value="${Math.round(o.x)}"></label><label>Y<input type="number" id="object-y" min="30" max="570" value="${Math.round(o.y)}"></label></div><div class="field-pair"><label>Breedte<input type="number" id="object-w" min="10" max="400" value="${o.w}"></label><label>Diepte<input type="number" id="object-h" min="8" max="300" value="${o.h}"></label></div><label>Rotatie <span>${o.rotation}°</span><input type="range" id="object-rotation" min="0" max="360" step="5" value="${o.rotation}"></label><div class="inspector-actions"><button class="button" data-action="duplicate">${icon('plus')} Kopie</button><button class="icon-button danger" data-action="delete" aria-label="Onderdeel verwijderen">${icon('trash')}</button></div>` : r ? `<span class="eyebrow">ROUTE / ZONE</span><h2>${esc(r.name)}</h2><label>Naam<input id="route-name" value="${esc(r.name)}" maxlength="60"></label><p class="muted">${r.points.length} punten. Versleep de punten op de kaart.</p><button class="button danger" data-action="delete">${icon('trash')} Verwijderen</button>` : `<span class="eyebrow">JOUW TERREIN</span><h2>Alles op zijn plek.</h2><p class="muted">Plaats een onderdeel, versleep het op de kaart en verfijn de afmetingen hier.</p><div class="inspector-illustration">${icon('home')}${icon('leaf')}</div><span class="mapping-note">Robotmapping nog niet gekoppeld</span>`;
    $('#object-list').innerHTML = [...data.objects, ...data.routes, ...data.zones].map(o => `<button class="object-row ${selection===o.id?'selected':''}" data-select="${esc(o.id)}">${icon(o.type?{coop:'home',nest:'egg',water:'water',plant:'leaf',door:'door',fence:'fence',dock:'battery'}[o.type]:'route')}<span>${esc(o.name)}</span></button>`).join('');
    if (o)
      for (const key of ['name', 'x', 'y', 'w', 'h', 'rotation']) $('#object-' + key).onchange = e => {
        let v = key === 'name' ? e.target.value.trim() : Number(e.target.value);
        if (key === 'name' && !v) v = C.TYPES[o.type].name;
        if (key !== 'name' && (!Number.isFinite(v) || v < Number(e.target.min) || v > Number(e.target.max))) {
          notify('Kies een waarde binnen het bereik.');
          inspector();
          return;
        }
        snapshot();
        o[key] = v;
        changed();
        inspector();
      };
    if (r) $('#route-name').onchange = e => {
      snapshot();
      r.name = e.target.value.trim() || 'Route';
      changed();
      inspector();
    };
    if (view) view.selected = selection;
  }

  function changed() {
    trailHistory = [];
    persist();
    view?.invalidate();
  }

  function select(id) {
    selection = id;
    tool = 'select';
    setToolUI();
    inspector();
  }

  function setToolUI() {
    document.querySelectorAll('[data-tool]').forEach(b => b.classList.toggle('selected', b.dataset.tool === tool));
    if ($('#drawing-controls')) $('#drawing-controls').hidden = !['route', 'zone'].includes(tool);
    if ($('#tool-hint')) $('#tool-hint').textContent = tool === 'select' ? 'Selecteer en versleep een onderdeel' : tool === 'route' ? 'Klik de punten van je route · Opslaan om af te ronden' : tool === 'zone' ? 'Klik de hoeken van een verboden zone' : `Klik op de kaart om ${C.TYPES[tool]?.name.toLowerCase()} te plaatsen`;
    if (view) view.draft = draft;
    if ($('#point-count')) $('#point-count').textContent = `${draft.length} punten`;
  }

  function hit(p, o) {
    const a = -o.rotation * Math.PI / 180,
      dx = p.x - o.x,
      dy = p.y - o.y;
    return Math.abs(dx * Math.cos(a) - dy * Math.sin(a)) < o.w / 2 + 8 && Math.abs(dx * Math.sin(a) + dy * Math.cos(a)) < o.h / 2 + 8;
  }

  function bindEditor(canvas) {
    canvas.onpointerdown = e => {
      const p = view.point(e);
      if (p.x < 35 || p.x > 925 || p.y < 35 || p.y > 565) return;
      canvas.focus();
      if (tool === 'route' || tool === 'zone') {
        draft.push(p);
        setToolUI();
        return;
      }
      if (C.TYPES[tool]) {
        snapshot();
        const type = tool,
          d = C.TYPES[type],
          o = {
            id: crypto.randomUUID(),
            type,
            name: d.name,
            x: p.x,
            y: p.y,
            w: d.w,
            h: d.h,
            rotation: 0
          };
        data.objects.push(o);
        changed();
        select(o.id);
        return;
      }
      const route = [...data.routes, ...data.zones].find(r => r.id === selection);
      if (route) {
        const i = route.points.findIndex(q => Math.hypot(q.x - p.x, q.y - p.y) < 14);
        if (i >= 0) {
          snapshot();
          drag = {
            route,
            index: i
          };
          canvas.setPointerCapture(e.pointerId);
          return;
        }
      }
      const o = [...data.objects].reverse().find(o => hit(p, o));
      if (o) {
        select(o.id);
        snapshot();
        drag = {
          object: o,
          dx: p.x - o.x,
          dy: p.y - o.y
        };
        canvas.setPointerCapture(e.pointerId);
      } else {
        selection = null;
        inspector();
      }
    };
    canvas.onpointermove = e => {
      if (!drag) return;
      const p = view.point(e);
      if (drag.object) {
        drag.object.x = Math.max(40, Math.min(920, p.x - drag.dx));
        drag.object.y = Math.max(40, Math.min(560, p.y - drag.dy));
      } else drag.route.points[drag.index] = {
        x: Math.max(40, Math.min(920, p.x)),
        y: Math.max(40, Math.min(560, p.y))
      };
      view.invalidate();
    };
    const end = () => {
      if (drag) {
        drag = null;
        changed();
        inspector();
      }
    };
    canvas.onpointerup = end;
    canvas.onpointercancel = end;
    canvas.onkeydown = e => {
      if (e.key === 'Escape') {
        draft = [];
        tool = 'select';
        setToolUI();
      }
      if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
        const o = data.objects.find(o => o.id === selection);
        if (o) {
          e.preventDefault();
          snapshot();
          const axis = e.key.includes('Left') || e.key.includes('Right') ? 'x' : 'y',
            sign = e.key.includes('Left') || e.key.includes('Up') ? -1 : 1;
          o[axis] = Math.max(40, Math.min(axis === 'x' ? 920 : 560, o[axis] + sign * (e.shiftKey ? 10 : 2)));
          changed();
          inspector();
        }
      }
    };
  }

  function finishDrawing() {
    const minimum = tool === 'zone' ? 3 : 2;
    if (draft.length < minimum) {
      notify(`Plaats minstens ${minimum} punten.`);
      return;
    }
    if (draft.length > 150) {
      notify('Gebruik maximaal 150 punten.');
      return;
    }
    snapshot();
    const item = {
      id: crypto.randomUUID(),
      name: tool === 'zone' ? `Verboden zone ${data.zones.length+1}` : `Patrouille ${data.routes.length+1}`,
      points: C.clone(draft),
      closed: tool === 'zone' || $('#route-closed').checked
    };
    (tool === 'zone' ? data.zones : data.routes).push(item);
    draft = [];
    changed();
    select(item.id);
    notify('Opgeslagen');
  }

  function action(a) {
    switch (a) {
      case 'toggle':
        if (LocalApp.telemetry?.moving) sendCommand('pause');
        else if (LocalApp.telemetry?.can_resume) sendCommand('resume');
        else startPatrol();
        break;
      case 'patrol':
        startPatrol();
        break;
      case 'dock':
      case 'eggs':
      case 'water':
        task(a);
        break;
      case 'edit-eggs':
        $('#egg-count').value = data.eggs;
        $('#egg-dialog').showModal();
        break;
      case 'collect':
        data.eggs = 0;
        data.eggTime = Date.now();
        log('Eieren verzameld', 'Handmatig');
        render();
        break;
      case 'zoom-in':
      case 'zoom-out':
      case 'zoom-reset':
        zoom = a === 'zoom-reset' ? 1 : Math.max(.8, Math.min(2, zoom + (a === 'zoom-in' ? .2 : -.2)));
        if (view) view.zoom = zoom;
        break;
      case 'undo':
      case 'redo': {
        const from = a === 'undo' ? undo : redo,
          to = a === 'undo' ? redo : undo;
        if (!from.length) {
          notify('Geen wijzigingen om terug te zetten.');
          return;
        }
        to.push(JSON.stringify(data));
        data = JSON.parse(from.pop());
        selection = null;
        changed();
        inspector();
        break;
      }
      case 'delete':
        snapshot();
        data.objects = data.objects.filter(o => o.id !== selection);
        data.routes = data.routes.filter(o => o.id !== selection);
        data.zones = data.zones.filter(o => o.id !== selection);
        selection = null;
        changed();
        inspector();
        break;
      case 'duplicate': {
        const o = data.objects.find(o => o.id === selection);
        if (!o) return;
        snapshot();
        const copy = {
          ...o,
          id: crypto.randomUUID(),
          name: (o.name + ' kopie').slice(0, 60),
          x: Math.min(920, o.x + 40),
          y: Math.min(560, o.y + 35)
        };
        data.objects.push(copy);
        changed();
        select(copy.id);
        break;
      }
      case 'finish-drawing':
        finishDrawing();
        break;
      case 'remove-point':
        draft.pop();
        setToolUI();
        break;
      case 'cancel-drawing':
        draft = [];
        tool = 'select';
        setToolUI();
        break;
      case 'export': {
        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: 'application/json'
          }),
          url = URL.createObjectURL(blob),
          a = document.createElement('a');
        a.href = url;
        a.download = 'bittle-mijn-tuin.json';
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        break;
      }
      case 'import':
        $('#import-file').click();
        break;
    }
  }
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-action],[data-tool],[data-select],[data-route-start]');
    if (!b) return;
    if (b.dataset.action) action(b.dataset.action);
    if (b.dataset.tool) {
      tool = b.dataset.tool;
      draft = [];
      setToolUI();
    }
    if (b.dataset.select) select(b.dataset.select);
    if (b.dataset.routeStart) startPatrol(b.dataset.routeStart);
  });
  $('#stop-button').onclick = () => sendCommand('stop');
  $('#save-eggs').onclick = e => {
    const n = Number($('#egg-count').value);
    if (!Number.isInteger(n) || n < 0 || n > 24) {
      e.preventDefault();
      notify('Kies een aantal van 0 tot 24.');
      return;
    }
    data.eggs = n;
    data.eggTime = Date.now();
    log('Eieren bijgewerkt', `${n} eieren · handmatig`);
    render();
  };
  $('#import-file').onchange = async e => {
    const f = e.target.files[0];
    if (!f) return;
    try {
      if (f.size > 250000) throw Error('Bestand is te groot.');
      const v = C.validate(JSON.parse(await f.text()));
      snapshot();
      data = v;
      robot.moving = false;
      changed();
      render();
      notify('Kaart geïmporteerd');
    } catch (err) {
      notify(err.message);
    }
    e.target.value = '';
  };
  window.addEventListener('hashchange', render);
  window.hasUnsavedDrawing = () => draft.length > 0;
  let lastTrailSample = 0,
    lastEventSignature = '',
    lastCamera = 0;
  LocalApp.subscribe((type, value) => {
    if (type === 'telemetry') {
      const t = value,
        now = performance.now();
      if (t.connected && t.pose && t.moving && now - lastTrailSample > 80) {
        trailHistory.push({
          ...t.pose,
          t: now
        });
        lastTrailSample = now;
      }
      data.events = LocalApp.events;
      const signature = JSON.stringify(data.events);
      if (signature !== lastEventSignature) {
        lastEventSignature = signature;
        document.querySelectorAll('.event-list').forEach(e => e.innerHTML = events(page === 'activiteit' ? 80 : 3));
      }
      syncStatus();
    } else if (type === 'offline') {
      robot.moving = false;
      syncStatus();
    } else if (type === 'project') {
      data = {
        ...value,
        events: LocalApp.events
      };
      render();
    } else if (type === 'saving') {
      $('#save-status').textContent = 'Opslaan…';
    } else if (type === 'saved') {
      $('#save-status').innerHTML = icon('check') + ' Opgeslagen';
    } else if (type === 'save-error') {
      $('#save-status').textContent = 'Niet opgeslagen';
      notify(value || LocalApp.error || 'Opslaan niet gelukt.');
    } else if (type === 'reload-waiting') {
      $('#save-status').textContent = 'Sla je getekende route op om te verversen';
    } else if (type === 'style-reloaded') {
      $('#save-status').textContent = 'Stijl bijgewerkt';
    }
  });
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-scenario]');
    if (b) LocalApp.scenario(b.dataset.scenario).catch(e => notify(e.message));
  });
  setInterval(() => {
    const t = LocalApp.telemetry,
      available = LocalApp.connected && t?.camera?.status === 'test' && t.connected;
    document.querySelectorAll('.camera-frame').forEach(img => {
      img.hidden = !available;
      if (available) img.src = '/api/camera/frame?t=' + Date.now();
    });
    document.querySelectorAll('.camera-unavailable').forEach(e => e.hidden = available);
  }, 750);
  render();
  requestAnimationFrame(tick);
