// Camera: the Grove Vision AI V2, on a USB port of this computer or over wifi through the XIAO ESP32S3 on it
// (firmware/bittle-camera), read by the platform server. The page shows its live Motion JPEG stream with the boxes of
// what the board's AI model recognises (SSCMA boxes: centre, width, height).
import { $, h, clear, toast, api } from './ui.js';

const POLL_MS = 500;
const WIFI = 'wifi://', HOST_KEY = 'bittle-platform.camera-host', DEFAULT_HOST = 'bittle-camera.local';

function remembered(key, fallback) {
  try {
    return localStorage.getItem(key) || fallback;
  } catch {
    return fallback;
  }
}

function remember(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // private window: the address is simply not remembered
  }
}

export function initCamera({ onStatus }) {
  const port = $('#cameraPort'), host = $('#cameraHost'), resolution = $('#cameraResolution');
  const connect = $('#cameraConnect'), disconnect = $('#cameraDisconnect');
  const image = $('#cameraImage'), boxes = $('#cameraBoxes'), empty = $('#cameraEmpty'), info = $('#cameraInfo');
  const distanceBadge = $('#cameraDistance');
  let status = { state: 'off' }, streaming = false;
  host.value = remembered(HOST_KEY, DEFAULT_HOST);

  const wifiChosen = () => port.value.startsWith(WIFI);
  const showHost = () => { host.hidden = !wifiChosen() || status.state !== 'off'; };

  async function listPorts() {
    try {
      const ports = await api('/api/camera/ports');
      const chosen = port.value;
      clear(port, ...ports.map(p => h('option', {
        value: p.device,
        text: p.wifi ? `📶 ${p.description}` : `${p.device}${p.likely ? ' · Vision AI' : ''} · ${p.description}`,
      })));
      if (ports.some(p => p.device === chosen)) port.value = chosen;
      showHost();
    } catch (error) {
      toast(error.message, true);
    }
  }

  async function start() {
    if (!port.value) return toast('Sluit het camerabordje aan met USB en zoek de poorten opnieuw (⟳).', true);
    let chosen = port.value;
    if (wifiChosen()) {
      const address = host.value.trim().replace(/^[a-z]+:\/\//i, '').replace(/\/.*$/, '') || DEFAULT_HOST;
      host.value = address;
      remember(HOST_KEY, address);
      chosen = WIFI + address;
    }
    try {
      status = await api('/api/camera/connect', 'POST', { port: chosen, resolution: resolution.value });
      show();
    } catch (error) {
      toast(error.message, true);
    }
  }

  async function stop() {
    try {
      status = await api('/api/camera/disconnect', 'POST');
      show();
    } catch (error) {
      toast(error.message, true);
    }
  }

  function placeholder() {
    if (status.state === 'no-camera') {
      return [h('b', { text: 'Het camerabordje antwoordt, maar ziet geen camera.' }), h('br'),
        'Steek de lintkabel van de Raspberry Pi-camera in de aansluiting van de Grove Vision AI V2: klepje open, lint er helemaal in met de metalen contacten naar de contacten van de aansluiting, klepje dicht. Het beeld start dan vanzelf.'];
    }
    if (status.state === 'error') {
      const wifi = status.port?.startsWith(WIFI) ? [h('br'), h('br'),
        'Wifi-camera: staat ze aan (oranje lampje brandt) en zit deze computer op hetzelfde wifi-netwerk? Lukt de naam niet, typ dan het IP-adres van de camera (te zien op haar statuspagina of in de router).'] : [];
      return [h('b', { text: 'Camera: probleem' }), h('br'), status.message, ...wifi];
    }
    if (status.state === 'connecting' || (status.state === 'streaming' && !status.frame)) return ['Camera starten…'];
    return [h('b', { text: 'Geen camerabeeld' }), h('br'),
      'Sluit de Grove Vision AI V2 (met de camera erop) met USB aan en kies zijn poort, of kies 📶 Wifi-camera. Klik dan Verbind.'];
  }

  function show() {
    const live = status.state === 'streaming' && status.frame > 0;
    if (live && !streaming) {
      image.src = `/api/camera/stream?t=${Date.now()}`;  // a new URL: the stream starts again after a reconnect
      streaming = true;
    }
    if (!live && streaming) {
      image.removeAttribute('src');
      streaming = false;
    }
    image.hidden = !live;
    empty.hidden = live;
    if (!live) clear(empty, ...placeholder());
    connect.hidden = status.state !== 'off';
    disconnect.hidden = status.state === 'off';
    showHost();
    const model = status.model?.name ? ` · model: ${status.model.name}` : '';
    info.textContent = status.state === 'off' ? '' : `${status.message}${live ? ` · ${status.fps} beelden/s` : ''}${model}`;
    drawBoxes(live ? status.detections || [] : []);
    const distance = status.state === 'off' ? null : status.distance;
    distanceBadge.hidden = !distance;
    if (distance) distanceBadge.textContent = `📏 ${distance.cm == null ? 'niets binnen bereik' : `${Math.round(distance.cm)} cm`}`;
    onStatus(status);
  }

  function drawBoxes(detections) {
    const width = boxes.clientWidth, height = boxes.clientHeight;
    boxes.width = width * devicePixelRatio;
    boxes.height = height * devicePixelRatio;
    const g = boxes.getContext('2d');
    g.scale(devicePixelRatio, devicePixelRatio);
    if (!detections.length || !image.naturalWidth) return;
    // The image is drawn "contain": work out where it lies inside the view.
    const scale = Math.min(width / image.naturalWidth, height / image.naturalHeight);
    const left = (width - image.naturalWidth * scale) / 2, top = (height - image.naturalHeight * scale) / 2;
    const [imageWidth, imageHeight] = status.image_size || [image.naturalWidth, image.naturalHeight];
    const sx = image.naturalWidth / imageWidth * scale, sy = image.naturalHeight / imageHeight * scale;
    g.lineWidth = 2;
    g.font = '12px system-ui';
    for (const d of detections) {
      const x = left + (d.x - d.w / 2) * sx, y = top + (d.y - d.h / 2) * sy;
      g.strokeStyle = g.fillStyle = '#6ad08a';
      g.strokeRect(x, y, d.w * sx, d.h * sy);
      const label = `${d.label} ${Math.round(d.score)}%`;
      g.fillRect(x, y - 16, g.measureText(label).width + 8, 16);
      g.fillStyle = '#062033';
      g.fillText(label, x + 4, y - 4);
    }
  }

  async function poll() {
    try {
      status = await api('/api/camera/status');
      show();
    } catch {
      // the server is restarting: try again
    }
    setTimeout(poll, POLL_MS);
  }

  port.addEventListener('change', showHost);
  host.addEventListener('keydown', event => { if (event.key === 'Enter') start(); });
  connect.addEventListener('click', start);
  disconnect.addEventListener('click', stop);
  $('#cameraRefresh').addEventListener('click', listPorts);
  listPorts();
  poll();
}
