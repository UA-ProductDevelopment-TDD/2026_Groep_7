// Scannen: turn on the spot in steps and let every step's photo, recognised things and distance land on the map.
// The page drives the robot (turn, stand still, wait); the server takes the frame, works out how far the robot
// really turned and places everything. Without a connected robot you turn the robot (or the camera) by hand.
import { h, clear, toast, api } from './ui.js';

const START_RATE = 25;       // degrees per second assumed for Petoi's turn on the spot until a step measures it
const MAX_STEPS = 60;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const NECK_AXIS_TILT = 30 * Math.PI / 180;  // Bittle's neck axis leans forward (as in app/bittle_platform/scan.py)

/** Degrees a camera on the head looks left when the neck is at `neck` degrees (less than the neck turns). */
function neckYaw(neck) {
  const t = neck * Math.PI / 180, a = NECK_AXIS_TILT;
  return Math.atan2(Math.sin(t) * Math.cos(a), Math.sin(a) ** 2 + Math.cos(t) * Math.cos(a) ** 2) * 180 / Math.PI;
}

export function initScan(root, { robot, twin, playSkill, onPose, mapApi, onScans }) {
  let settings = null, scans = [], selected = null, running = null, mapName = '';
  let bodyTurn = 0;            // degrees the body turned in this page's last scan (the 3D surroundings turn with it)
  let nextPhoto = null;        // resolves the wait for "Volgende foto" in hand mode

  const where = h('p', { class: 'note' });
  const startButton = h('button', { type: 'button', class: 'primary', onclick: () => run().catch(failed) }, 'Scan hier');
  const stopButton = h('button', { type: 'button', hidden: true, onclick: stop }, '■ Stop');
  const photoButton = h('button', { type: 'button', class: 'primary', hidden: true, onclick: () => nextPhoto?.() }, 'Volgende foto');
  const progress = h('p', { class: 'note', role: 'status' });
  const strip = h('div', { class: 'scan-strip', 'aria-label': 'Foto\'s van de scan' });
  const settingsBox = h('div');
  const list = h('ul', { class: 'saved' });
  const result = h('div', { class: 'scan-result' });

  function failed(error) {
    toast(error.message, true);
    finishUi();
  }

  // Where the scan happens: the robot as placed on the saved map.
  function place() {
    const map = mapApi()?.current();
    if (!map) return { error: 'De kaart is nog niet geladen.' };
    if (!map.name) return { error: 'Bewaar de kaart eerst: een scan hoort bij een bewaarde kaart.' };
    if (!map.robot) return { error: 'Zet de robot op de kaart met het gereedschap Robot (plaats en richting).' };
    return { map: map.name, ...map.robot };
  }
  function showWhere() {
    const p = place();
    where.textContent = p.error || `Kaart "${p.map}" · robot op x ${p.x.toFixed(2)} m, y ${p.y.toFixed(2)} m, richting ${Math.round(p.heading)}°`;
    where.className = p.error ? 'note warn-text' : 'note';
    startButton.disabled = !!p.error || !!running;
  }

  // Turning one step
  async function turn(seconds) {
    const how = settings.scan.turn;
    if (how.startsWith('motion:')) {
      const motion = await api(`/api/motions/${encodeURIComponent(how.slice(7))}`);
      const plan = { segments: motion.frames.map(frame => [frame.seconds, frame.pose]), loop_from: 0, ease: true };
      twin.play(plan, { onPose });
      await sleep(seconds * 1000);
      twin.stop();
      return;
    }
    await playSkill('kvtL', 'Scan: draaien');
    await sleep(seconds * 1000);
    await playSkill('kbalance', 'Scan: stilstaan');
  }

  // The head: a neck scan turns it from one side to the other and takes a photo and distance at every stop.
  function setNeck(angle) {
    twin.stop();
    const pose = { ...twin.pose(), 'neck-joint': angle };
    twin.setPose(pose);
    onPose(pose);
    robot.sendPose(pose);  // the robot always follows during a scan
  }

  const done = (scan, stepDegrees) => {
    const last = scan.steps[scan.steps.length - 1], turned = last.heading - scan.steps[0].heading;
    // Done when the camera sees the start again within the next step, or (without pictures) after a full turn.
    return (last.to_start !== null && last.to_start <= .75 * stepDegrees) || (!last.frame && turned >= 360) || turned >= 540;
  };

  async function waitForPhotoClick(text) {
    progress.textContent = text;
    await new Promise(resolve => { nextPhoto = resolve; });
    nextPhoto = null;
  }

  async function run() {
    const p = place();
    if (p.error) return toast(p.error, true);
    settings = await api('/api/settings');
    const neck = settings.scan.mode === 'neck' && robot.connected;
    const byHand = settings.scan.turn === 'manual' || !robot.connected;
    if (!robot.connected) toast(settings.scan.mode === 'neck'
      ? 'De robot is niet verbonden: zonder robot kan het hoofd niet zwaaien. Draai de camera met de hand, telkens een stukje naar links.'
      : 'De robot is niet verbonden: draai hem (of de camera) met de hand, telkens een stukje naar links.');
    running = { stopped: false, byHand, started: performance.now() };
    startButton.disabled = true;
    stopButton.hidden = false;
    photoButton.hidden = !byHand;
    clear(strip);
    clear(result);
    let scan = await api('/api/scans', 'POST', p);
    scan = neck ? await neckScan(scan) : await bodyScan(scan, byHand);
    if (neck) setNeck(0);
    progress.textContent = 'Scan afronden: rondom-foto en kaart maken…';
    scan = await api(`/api/scans/${scan.id}/finish`, 'POST');
    const seconds = Math.round((performance.now() - running.started) / 1000);
    finishUi();
    await refresh();
    select(scan.id);
    toast(`${scan.closure?.closed ? `Scan klaar: de cirkel sluit (fout ${scan.closure.error_deg}° rechtgezet)` : 'Scan klaar'} · ${scan.steps.length} stappen in ${seconds} s.`);
  }

  // Neck scan: the robot stands still and sweeps its head; between sweeps the body turns so the next sweep starts
  // where the last one ended. The neck angles are known, so every photo lands on the map at once.
  async function neckScan(scan) {
    const { neck_range: range, neck_step: step, neck_settle: settle } = settings.scan;
    const angles = [];
    for (let a = -range; a < range - .01; a += step) angles.push(a);
    angles.push(range);
    const stepYaw = neckYaw(angles[1]) - neckYaw(angles[0]);
    const bodyTarget = 2 * neckYaw(range) - stepYaw;  // the next sweep's first photo overlaps the last one
    let rate = START_RATE, sweeps = 0;
    const take = async (body) => {
      scan = await api(`/api/scans/${scan.id}/step`, 'POST', body);
      show(scan);
      return scan;
    };
    if (robot.connected) await playSkill('kbalance', 'Scan: stilstaan');
    await sleep(600);
    setNeck(angles[0]);
    await sleep(400 + settle * 1000);  // the long way from straight ahead to the side
    await take({ commanded: 0, neck: angles[0] });
    while (!running.stopped) {
      sweeps += 1;
      for (const angle of angles.slice(1)) {
        if (running.stopped) return scan;
        setNeck(angle);
        progress.textContent = `Zwaai ${sweeps}: nek ${Math.round(angle)}°…`;
        await sleep(settle * 1000);
        await take({ commanded: 0, neck: angle });
        if (done(scan, stepYaw)) return scan;
      }
      // Turn the body for the next sweep (the head swings back meanwhile).
      let commanded = bodyTarget, seconds = 0;
      if (running.byHand) {
        await waitForPhotoClick(`Draai de robot ongeveer ${Math.round(bodyTarget)}° naar links en klik "Volgende foto".`);
      } else {
        seconds = Math.min(10, Math.max(.3, bodyTarget / rate));
        progress.textContent = `Draaien voor zwaai ${sweeps + 1}…`;
        await turn(seconds);
        await sleep(settings.scan.settle * 1000);
        commanded = rate * seconds;
      }
      if (running.stopped) return scan;
      const bodyBefore = scan.steps[scan.steps.length - 1].body;
      setNeck(angles[0]);
      await sleep(400 + settle * 1000);
      await take({ commanded, neck: angles[0] });
      const last = scan.steps[scan.steps.length - 1];
      if (seconds && last.method === 'image') rate = Math.min(120, Math.max(3, (rate + (last.body - bodyBefore) / seconds) / 2));
      if (done(scan, stepYaw)) return scan;
    }
    return scan;
  }

  // Body scan: the whole robot turns a step at a time (or is turned by hand).
  async function bodyScan(scan, byHand) {
    scan = await api(`/api/scans/${scan.id}/step`, 'POST', { commanded: 0 });
    show(scan);
    const target = settings.scan.step;
    let rate = START_RATE;
    while (!running.stopped && scan.steps.length < MAX_STEPS) {
      let commanded = target, seconds = 0;
      if (byHand) {
        await waitForPhotoClick(`Draai ongeveer ${target}° naar links en klik "Volgende foto".`);
      } else {
        seconds = Math.min(4, Math.max(.2, target / rate));
        progress.textContent = `Stap ${scan.steps.length}: draaien…`;
        await turn(seconds);
        await sleep(settings.scan.settle * 1000);
        commanded = rate * seconds;
      }
      if (running.stopped) break;
      progress.textContent = `Stap ${scan.steps.length}: foto en meting…`;
      scan = await api(`/api/scans/${scan.id}/step`, 'POST', { commanded });
      const last = scan.steps[scan.steps.length - 1];
      if (!byHand && last.method === 'image' && seconds) rate = Math.min(120, Math.max(3, (rate + last.turn / seconds) / 2));
      show(scan);
      if (done(scan, target)) break;
    }
    return scan;
  }

  function stop() {
    if (!running) return;
    running.stopped = true;
    nextPhoto?.();
    if (robot.connected && !running.byHand) playSkill('kbalance', 'Scan gestopt').catch(() => {});
  }

  function finishUi() {
    running = null;
    stopButton.hidden = true;
    photoButton.hidden = true;
    progress.textContent = '';
    showWhere();
  }

  function show(scan) {
    const last = scan.steps[scan.steps.length - 1];
    const srf05 = scan.sensor.source === 'camera';
    const measuredText = !srf05 ? '' : last.samples === 0 ? ' · ⚠ geen metingen van de SRF05 (camera verbonden?)'
      : last.distance == null ? ' · 📏 niets binnen bereik' : ` · 📏 ${Math.round(last.distance * 100)} cm`;
    progress.textContent = `${scan.steps.length} stappen · ${Math.round(scan.turned)}° gedraaid${last.method !== 'start' ? ` · laatste stap ${last.turn.toFixed(1)}° (${METHOD[last.method]})` : ''}${measuredText}`;
    const caption = step => `${Math.round(((step.heading % 360) + 360) % 360)}°${step.distance != null ? ` · ${Math.round(step.distance * 100)} cm` : ''}`;
    clear(strip, scan.steps.map(step => step.frame
      ? h('figure', null, h('img', { src: `/api/scans/${scan.id}/files/${step.frame}`, alt: `Foto bij ${Math.round(step.heading)}°`, loading: 'lazy' }),
        h('figcaption', { text: caption(step) }))
      : h('figure', { class: 'empty' }, h('span', { text: 'geen beeld' }), h('figcaption', { text: caption(step) }))));
    strip.scrollLeft = strip.scrollWidth;
    bodyTurn = last.body ?? last.heading;  // the real robot now faces this far from where the scan started
    const current = [...scans.filter(s => s.id !== scan.id), scan];
    mapApi()?.setScans(current);
    onScans?.(current, bodyTurn);
  }

  const METHOD = { image: 'uit de beelden', gyro: 'gyroscoop', command: 'geschat uit de draaitijd', neck: 'nekhoek', start: 'start' };

  // Scans of the current map
  async function refresh() {
    if (!mapName) {
      scans = [];
    } else {
      try {
        scans = await api(`/api/scans?map=${encodeURIComponent(mapName)}`);
      } catch (error) {
        scans = [];
        toast(error.message, true);
      }
    }
    mapApi()?.setScans(scans);
    onScans?.(scans, bodyTurn);
    clear(list, scans.length ? scans.map((scan, index) => h('li', null,
      h('span', null, `Scan ${index + 1}`, h('small', { text: `${scan.steps.length} stappen, ${scan.steps.filter(s => s.frame).length} foto's · ${Math.round(scan.turned)}° · ${scan.objects.length} herkend · ${scan.points.length} afstanden` })),
      h('button', { type: 'button', onclick: () => select(scan.id) }, 'Bekijken')))
      : h('li', { class: 'note', text: mapName ? 'Nog geen scans op deze kaart.' : 'Laad of bewaar een kaart om te scannen.' }));
    if (selected && !scans.some(s => s.id === selected)) { selected = null; clear(result); }
  }

  function select(id) {
    const scan = scans.find(s => s.id === id);
    if (!scan) return;
    selected = id;
    const closure = scan.closure?.closed
      ? `De cirkel sluit: ${scan.closure.error_deg}° fout rechtgezet over alle stappen.`
      : `De cirkel is niet gesloten (${scan.closure?.reason || 'scan niet afgerond'}); de richtingen kunnen wat afwijken.`;
    const lens = scan.hfov_measured
      ? h('p', { class: 'note' }, `Gemeten kijkhoek van de camera: ${scan.hfov_measured}° (ingesteld: ${scan.camera.hfov}°). `,
        h('button', { type: 'button', onclick: () => saveSettings({ camera: { ...settings.camera, hfov: scan.hfov_measured } }) }, 'Gebruik deze kijkhoek'))
      : null;
    clear(result,
      h('h3', { text: `Scan ${scans.indexOf(scan) + 1}` }),
      scan.panorama ? h('img', { class: 'panorama', src: `/api/scans/${scan.id}/files/${scan.panorama}?v=${scan.created}`, alt: 'Rondom-foto: van links naar rechts is rechtsom draaien' }) : null,
      h('p', { class: 'note', text: closure }), lens,
      scan.objects.length ? h('ul', { class: 'saved' }, scan.objects.map(o => h('li', null,
        h('span', null, `${o.label} · ${Math.round(o.score)}%`, h('small', { text: `${o.distance.toFixed(2)} m${o.measured ? ' (gemeten)' : ' (geschat)'} · richting ${Math.round(o.bearing)}°${o.seen > 1 ? ` · ${o.seen}× gezien` : ''}` })))))
        : h('p', { class: 'note', text: 'Niets herkend in deze scan.' }),
      h('p', { class: 'note', text: scan.points.length ? `${scan.points.length} afstanden gemeten, ${scan.outline.length} stuk(ken) omtrek.` : scan.sensor.source === 'none' ? 'Geen afstanden gemeten (geen afstandssensor gekozen).' : 'Geen afstanden gemeten: de sensor hoorde niets binnen bereik of stuurde geen metingen.' }),
      h('div', { class: 'row' },
        h('button', { type: 'button', disabled: !scan.outline.length, onclick: () => {
          const count = mapApi()?.addWalls(scan.outline) || 0;
          toast(count ? `${count} muur/muren toegevoegd. Controleer ze en bewaar de kaart.` : 'Er is geen omtrek om muren van te maken.', !count);
        } }, 'Muren maken van de omtrek'),
        h('button', { type: 'button', class: 'danger', onclick: () => remove(scan.id) }, 'Verwijder scan')));
  }

  async function remove(id) {
    if (!confirm('Deze scan verwijderen (foto\'s en metingen)?')) return;
    try {
      await api(`/api/scans/${id}`, 'DELETE');
      await refresh();
    } catch (error) {
      toast(error.message, true);
    }
  }

  // Settings: camera mounting, how to turn, distance sensor
  async function saveSettings(changes) {
    try {
      const sources = settings.distance_sources;
      settings = { ...await api('/api/settings', 'PUT', { ...settings, ...changes }), distance_sources: sources };
      renderSettings();
      toast('Instellingen opgeslagen.');
    } catch (error) {
      toast(error.message, true);
    }
  }

  async function renderSettings() {
    const motions = await api('/api/motions').catch(() => []);
    const draft = structuredClone(settings);
    const num = (label, unit, get, set, scale, min, max, step = 1) => {
      const input = h('input', { type: 'number', min, max, step, value: +(get() * scale).toFixed(2) });
      input.addEventListener('change', () => set(Number(input.value) / scale));
      return h('label', { class: 'field' }, h('span', null, label, h('em', { text: ` ${unit}` })), input);
    };
    const turnSelect = h('select', { 'aria-label': 'Hoe de robot draait' },
      h('option', { value: 'kvtL', text: 'Petoi: draaien op de plaats (kvtL)' }),
      h('option', { value: 'manual', text: 'Met de hand draaien' }),
      motions.map(m => h('option', { value: `motion:${m.name}`, text: `Eigen beweging: ${m.name}` })));
    turnSelect.value = draft.scan.turn;
    const modeSelect = h('select', { 'aria-label': 'Scanmanier' },
      h('option', { value: 'neck', text: 'Nek-scan: hoofd zwaait, robot staat stil (snel)' }),
      h('option', { value: 'body', text: 'Lijf-scan: hele robot draait stap voor stap' }));
    modeSelect.value = draft.scan.mode;
    modeSelect.addEventListener('change', () => { draft.scan.mode = modeSelect.value; });
    turnSelect.addEventListener('change', () => { draft.scan.turn = turnSelect.value; });
    const sourceSelect = h('select', { 'aria-label': 'Afstandssensor' },
      Object.entries(settings.distance_sources).map(([value, label]) => h('option', { value, text: label })));
    sourceSelect.value = draft.distance.source;
    sourceSelect.addEventListener('change', () => { draft.distance.source = sourceSelect.value; });
    clear(settingsBox,
      h('h3', { text: 'Camera op de robot' }),
      h('div', { class: 'grid2' },
        num('Hoogte boven de grond', 'cm', () => draft.camera.height, v => { draft.camera.height = v; }, 100, 1, 200),
        num('Kanteling omlaag', '°', () => draft.camera.tilt, v => { draft.camera.tilt = v; }, 1, -60, 60),
        num('Kijkhoek (breedte)', '°', () => draft.camera.hfov, v => { draft.camera.hfov = v; }, 1, 20, 160),
        num('Vóór het midden', 'cm', () => draft.camera.forward, v => { draft.camera.forward = v; }, 100, -30, 50)),
      h('p', { class: 'note', text: 'De kijkhoek wordt bij elke volledige scan gemeten; die meting kun je daarna overnemen.' }),
      h('h3', { text: 'Scannen' }),
      modeSelect,
      h('div', { class: 'grid2' },
        num('Nek tot', '°', () => draft.scan.neck_range, v => { draft.scan.neck_range = v; }, 1, 20, 90),
        num('Nekstap', '°', () => draft.scan.neck_step, v => { draft.scan.neck_step = v; }, 1, 5, 45),
        num('Wachten na een nekstap', 's', () => draft.scan.neck_settle, v => { draft.scan.neck_settle = v; }, 1, 0, 2, .05)),
      h('p', { class: 'note', text: 'Nek-scan: de robot staat stil en zwaait zijn hoofd (met camera en sensor) van rechts naar links; tussen twee zwaaien draait het lijf. Elke foto komt meteen op de kaart. Een nek van 90° kijkt maar ongeveer 74° opzij: de nekas staat schuin.' }),
      h('h3', { text: 'Lijf draaien' }),
      turnSelect,
      h('div', { class: 'grid2' },
        num('Stap', '°', () => draft.scan.step, v => { draft.scan.step = v; }, 1, 5, 45),
        num('Wachten na draaien', 's', () => draft.scan.settle, v => { draft.scan.settle = v; }, 1, .2, 5, .1)),
      h('p', { class: 'note', text: 'Kleinere stappen geven meer overlap tussen de foto\'s en dus een betere hoekmeting (houd de stap onder ongeveer een derde van de kijkhoek).' }),
      h('h3', { text: 'Afstandssensor' }),
      sourceSelect,
      h('div', { class: 'grid2' },
        num('Richting van de sensor', '°', () => draft.distance.bearing, v => { draft.distance.bearing = v; }, 1, -180, 180),
        num('Vóór het midden', 'cm', () => draft.distance.forward, v => { draft.distance.forward = v; }, 100, -50, 50),
        num('Bereik', 'm', () => draft.distance.max_range, v => { draft.distance.max_range = v; }, 1, .1, 40, .1)),
      h('p', { class: 'note', text: 'SRF05 op de camera: de camera moet verbonden zijn (USB of wifi). Bij elke stap neemt het platform een halve seconde metingen en houdt de middelste; wat de camera recht voor de sensor herkent, krijgt die gemeten afstand. De nagebootste sensor meet wat op de kaart getekend is, om alles zonder robot uit te proberen.' }),
      h('button', { type: 'button', class: 'primary', onclick: () => saveSettings({ camera: draft.camera, scan: draft.scan, distance: draft.distance }) }, 'Instellingen opslaan'));
  }

  clear(root,
    h('h3', { text: 'Rondom scannen' }),
    where,
    h('div', { class: 'row' }, startButton, photoButton, stopButton),
    progress, strip,
    h('p', { class: 'note', text: 'De robot draait in stapjes naar links en neemt telkens een foto. Uit de foto\'s volgt hoeveel hij echt draaide; ziet hij het beginbeeld terug, dan is de scan rond. Herkende dingen, gemeten afstanden en de vloer rondom komen op de kaart.' }),
    h('h3', { text: 'Scans op deze kaart' }), list, result,
    h('details', null, h('summary', { text: 'Instellingen' }), settingsBox));

  (async () => {
    settings = await api('/api/settings');
    renderSettings();
  })().catch(error => toast(error.message, true));

  return {
    /** The map changed (loaded, saved, edited): follow its name and its robot. */
    mapChanged(map) {
      showWhere();
      if ((map?.name || '') !== mapName) {
        mapName = map?.name || '';
        bodyTurn = 0;
        refresh();
      } else {
        onScans?.(scans, bodyTurn);  // the robot may have been moved on the map
      }
    },
    refreshMotions: () => settings && renderSettings(),
  };
}
