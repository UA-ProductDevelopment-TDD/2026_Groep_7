/* Local transport, save queue and development reload. No hardware protocol here. */
(async function() {
  const listeners = new Set();
  const app = {
    project: null,
    revision: 0,
    telemetry: null,
    events: [],
    connected: false,
    pending: false,
    error: null,
    conflict: false
  };
  let token = '',
    socket, latest = null,
    saving = false,
    saveTimer, assetVersion, backoff = 500,
    lastMessage = 0,
    fetching = false;
  const emit = (type, value) => listeners.forEach(fn => fn(type, value));
  app.subscribe = fn => {
    listeners.add(fn);
    return () => listeners.delete(fn);
  };
  async function request(path, options = {}) {
    const response = await fetch(path, {
      cache: 'no-store',
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-Local-Token': token,
        ...options.headers
      },
      signal: AbortSignal.timeout(6000)
    });
    let result;
    try {
      result = await response.json();
    } catch {
      throw Error('Ongeldig antwoord van de lokale server.');
    }
    if (!response.ok) {
      const error = new Error(typeof result.detail === 'string' ? result.detail : response.status === 422 ? 'Ongeldige invoer. Controleer je kaart.' : 'Lokale server geeft een fout.');
      error.status = response.status;
      throw error;
    }
    return result;
  }
  app.request = request;
  app.save = project => {
    latest = JSON.parse(JSON.stringify(project));
    app.pending = true;
    app.error = null;
    emit('saving');
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => drain(), 250);
  };
  async function drain() {
    if (saving || !latest || app.conflict) return;
    saving = true;
    while (latest && !app.conflict) {
      const current = latest;
      latest = null;
      try {
        const result = await request('/api/project', {
          method: 'PUT',
          body: JSON.stringify({
            revision: app.revision,
            project: current
          })
        });
        app.revision = result.revision;
        app.project = current;
        app.events = result.events;
        app.error = null;
      } catch (e) {
        latest = latest || current;
        app.error = e.message;
        app.conflict = e.status === 409;
        emit('save-error', e.message);
        break;
      }
    }
    saving = false;
    app.pending = !!latest;
    emit(app.pending ? 'save-error' : 'saved', app.error);
  }
  app.flush = async () => {
    clearTimeout(saveTimer);
    await drain();
    while (saving) await new Promise(resolve => setTimeout(resolve, 40));
    return !app.pending;
  };
  app.command = async (action, routeId) => {
    if (!app.connected) throw Error('Lokale server niet bereikbaar. Opdracht niet verstuurd.');
    if (!await app.flush()) throw Error('Sla eerst je kaart op of los het opslagconflict op.');
    const result = await request('/api/commands', {
      method: 'POST',
      body: JSON.stringify({
        id: crypto.randomUUID(),
        action,
        route_id: routeId || null
      })
    });
    emit('command', result);
    if (result.status === 'failed') throw Error(result.message);
    return result;
  };
  app.scenario = async name => {
    const result = await request('/api/simulator/scenario', {
      method: 'POST',
      body: JSON.stringify({
        name
      })
    });
    app.telemetry = result;
    emit('telemetry', result);
  };
  app.reloadProject = async () => {
    const b = await request('/api/bootstrap');
    token = b.token;
    app.project = b.project;
    app.revision = b.revision;
    app.events = b.events;
    app.conflict = false;
    app.pending = false;
    app.error = null;
    latest = null;
    emit('project', b.project);
  };

  function connect() {
    socket = new WebSocket(`${location.protocol==='https:'?'wss:':'ws:'}//${location.host}/api/telemetry`);
    socket.onmessage = async e => {
      const message = JSON.parse(e.data);
      if (message.type !== 'telemetry') return;
      lastMessage = Date.now();
      const recovered = !app.connected;
      app.connected = true;
      backoff = 500;
      if (recovered && latest && !app.conflict && !saving) drain();
      app.telemetry = message.data;
      app.events = message.events;
      emit('telemetry', message.data);
      if (message.revision !== app.revision && !saving && !app.pending && !fetching) {
        fetching = true;
        try {
          const b = await request('/api/project');
          if (!app.pending && !saving) {
            app.project = b.project;
            app.revision = b.revision;
            app.events = b.events;
            emit('project', b.project);
          }
        } catch {} finally {
          fetching = false;
        }
      }
    };
    socket.onclose = () => {
      app.connected = false;
      emit('offline');
      setTimeout(async () => {
        try {
          const b = await request('/api/bootstrap');
          token = b.token;
        } catch {}
        connect();
      }, backoff);
      backoff = Math.min(backoff * 2, 4000);
    };
    socket.onerror = () => socket.close();
  }
  setInterval(() => {
    if (app.connected && Date.now() - lastMessage > 3000) {
      app.connected = false;
      emit('offline');
      socket?.close();
    }
  }, 1000);
  window.addEventListener('beforeunload', e => {
    if (app.pending || window.hasUnsavedDrawing?.()) {
      e.preventDefault();
      e.returnValue = '';
    }
  });
  async function watch() {
    try {
      const next = await request('/api/dev/revision');
      if (next.css !== assetVersion.css) {
        document.querySelectorAll('link[rel=stylesheet]').forEach(link => {
          const url = new URL(link.href);
          url.searchParams.set('v', next.css);
          link.href = url.href;
        });
        assetVersion.css = next.css;
        emit('style-reloaded');
      }
      if (next.js !== assetVersion.js || next.html !== assetVersion.html) {
        if (window.hasUnsavedDrawing?.()) {
          emit('reload-waiting');
          return;
        }
        if (await app.flush()) {
          location.reload();
          return;
        }
      }
    } catch {}
  }
  try {
    const bootstrap = await request('/api/bootstrap');
    Object.assign(app, {
      project: bootstrap.project,
      revision: bootstrap.revision,
      events: bootstrap.events,
      telemetry: bootstrap.telemetry,
      connected: true
    });
    token = bootstrap.token;
    assetVersion = bootstrap.assets;
    window.LocalApp = app;
    const script = document.createElement('script');
    script.src = 'dashboard.js';
    script.onload = () => {
      connect();
      setInterval(watch, 1000);
    };
    document.body.append(script);
  } catch (e) {
    document.querySelector('#page').innerHTML = '<section class="panel"><h2>Lokale server niet bereikbaar</h2><p>Open start-dashboard.cmd en vernieuw deze pagina.</p><button class="button" onclick="location.reload()">Opnieuw proberen</button></section>';
  }
})();
