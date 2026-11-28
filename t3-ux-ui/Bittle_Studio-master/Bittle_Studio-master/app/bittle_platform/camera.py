"""The camera: a Seeed Grove Vision AI V2 (Himax WiseEye2 with a Raspberry Pi camera), on a USB serial port or over wifi.

The board speaks Seeed's SSCMA AT protocol at 921600 baud: commands end in CR, every answer and event is one JSON line.
AT+INVOKE=-1,0,0 runs the loaded AI model on every frame and sends each frame as a base64 JPEG with the boxes found;
without a model AT+SAMPLE=-1 sends frames only. A reader thread keeps the newest frame and its detections, and starts
again by itself when the camera or the board comes back, so plugging the camera in later needs no reconnect.

Over wifi a XIAO ESP32S3 on the board (firmware/bittle-camera) passes the same bytes through a TCP port, so the port
'wifi://bittle-camera.local' reads the board exactly as USB does. Without a Vision AI V2 the XIAO answers the same
commands with its own camera (frames, no AI).
"""
import base64
import binascii
import collections
import json
import re
import threading
import time

import serial
import serial.tools.list_ports

BAUD = 921600
RESOLUTIONS = {'240': 0, '480': 1, '640': 2}  # AT+SENSOR option per image size (square 240/480, or 640x480)
REPLY_S = 2.            # seconds to wait for the answer to one command
STALL_S = 5.            # seconds without a frame before the stream is started again
RETRY_S = 3.            # seconds between attempts while the camera itself does not answer
DISTANCE_STALE_S = 1.   # a distance reading older than this is no longer shown or used
VISION_AI_USB = (0x1A86, 0x55D3)  # the CH343 USB serial chip of the Grove Vision AI V2
XIAO_USB = (0x303A, 0x1001)       # the XIAO ESP32S3 on the board (firmware/bittle-camera passes the board through)
WIFI = 'wifi://'
WIFI_HOST = 'bittle-camera.local'  # the mDNS name the XIAO firmware announces
WIFI_PORT = 3333
HOST = re.compile(r'^[A-Za-z0-9][A-Za-z0-9.-]{0,252}(:\d{1,5})?$')


def wifi_address(port):
    """(host, tcp port) of a 'wifi://host[:port]' camera port, or None for a serial port. Raises ValueError if bad."""
    if not port.startswith(WIFI):
        return None
    address = port[len(WIFI):].strip().rstrip('/')
    if not HOST.match(address):
        raise ValueError('Geef het adres van de wifi-camera, bijvoorbeeld bittle-camera.local of 192.168.1.42')
    host, _, number = address.partition(':')
    number = int(number or WIFI_PORT)
    if not 0 < number < 65536:
        raise ValueError('Poortnummer van de wifi-camera moet tussen 1 en 65535 liggen')
    return host, number


def open_link(port, baud):
    """A serial-like link: a USB serial port, or a TCP connection to the wifi camera."""
    address = wifi_address(port)
    if address:
        return serial.serial_for_url(f'socket://{address[0]}:{address[1]}', timeout=.05, write_timeout=2)
    link = serial.Serial(None, baud, timeout=.05, write_timeout=1)
    link.dtr = link.rts = False  # opening must not reset the board (the XIAO restarts on these lines)
    link.port = port
    link.open()
    return link


def ports():
    """Serial ports and the wifi camera; a port that looks like a Grove Vision AI V2 first, then the wifi camera."""
    found = []
    for port in serial.tools.list_ports.comports():
        usb = (port.vid, port.pid)
        description = 'XIAO op de Vision AI' if usb == XIAO_USB else port.description or port.device
        found.append({'device': port.device, 'description': description, 'likely': usb in (VISION_AI_USB, XIAO_USB)})
    found.sort(key=lambda p: (not p['likely'], p['device']))
    wifi = {'device': WIFI + WIFI_HOST, 'description': 'Wifi-camera (XIAO)', 'likely': False, 'wifi': True}
    found.insert(sum(p['likely'] for p in found), wifi)
    return found


def model_info(encoded):
    """Model name and classes from the base64 JSON that AT+INFO? returns (SenseCraft models carry it)."""
    try:
        info = json.loads(base64.b64decode(encoded))
    except (ValueError, binascii.Error, TypeError):
        return {'name': None, 'classes': []}
    classes = info.get('classes') if isinstance(info.get('classes'), list) else []
    return {'name': info.get('model_name'), 'classes': [str(c) for c in classes]}


class VisionCamera:
    """One Grove Vision AI V2. opener(port, baud) returns a serial-like object (tests pass a fake device)."""

    def __init__(self, opener=None):
        self.opener = opener or open_link
        self.lock = threading.Condition()
        self.thread = None
        self.stop_event = threading.Event()
        self.port = None
        self.resolution = '240'
        self._reset()

    def _reset(self):
        self.state, self.message = 'off', 'Niet verbonden'
        self.device, self.model = {}, {'name': None, 'classes': []}
        self.jpeg, self.frame_number, self.frame_time = None, 0, None
        self.detections, self.image_size = [], None
        self.fps, self._times = 0., []
        self.distance, self.distance_time = None, None  # newest SRF05 reading from the XIAO: {'cm', 'sensor'}
        self.distance_log = collections.deque(maxlen=300)  # (time, cm or None): the last 20 s or so

    # Control

    def connect(self, port, resolution='240'):
        if resolution not in RESOLUTIONS:
            raise ValueError('Beeldgrootte moet een van deze zijn: ' + ', '.join(RESOLUTIONS))
        wifi_address(port)  # a bad wifi address fails here, not in the reader thread
        self.disconnect()
        with self.lock:
            self._reset()
            self.port, self.resolution = port, resolution
            self.state, self.message = 'connecting', f'{port} openen'
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, args=(self.stop_event,), daemon=True)
        self.thread.start()

    def disconnect(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(3)
        self.thread = None
        with self.lock:
            self._reset()
            self.port = None
            self.lock.notify_all()

    # Reading

    def status(self):
        with self.lock:
            now = time.monotonic()
            age = None if self.frame_time is None else round(now - self.frame_time, 2)
            distance = None
            if self.distance is not None and now - self.distance_time < DISTANCE_STALE_S:
                distance = {**self.distance, 'age_s': round(now - self.distance_time, 2)}
            return {'state': self.state, 'message': self.message, 'port': self.port, 'resolution': self.resolution,
                    'device': self.device, 'model': self.model, 'frame': self.frame_number, 'frame_age_s': age,
                    'fps': round(self.fps, 1), 'image_size': self.image_size, 'detections': self.detections,
                    'distance': distance}

    def distance_since(self, start, minimum=3, timeout=.4):
        """The distance readings (cm, None for no echo) that came after `start` (time.monotonic()), waiting up to
        `timeout` seconds until there are at least `minimum`; [] when the camera sends none."""
        def readings():
            return [cm for t, cm in self.distance_log if t > start]
        with self.lock:
            if self.port is None:
                return []
            self.lock.wait_for(lambda: self.stop_event.is_set() or len(readings()) >= minimum, timeout)
            return readings()

    def latest(self):
        with self.lock:
            return self.jpeg, self.frame_number

    def wait_frame(self, after, timeout=2.):
        """The newest JPEG once its frame number is past `after` (or None after the timeout)."""
        with self.lock:
            self.lock.wait_for(lambda: self.frame_number > after or self.stop_event.is_set(), timeout)
            return self.jpeg if self.frame_number > after else None, self.frame_number

    # The reader thread

    def _set(self, state, message):
        with self.lock:
            self.state, self.message = state, message
            self.lock.notify_all()

    def _run(self, stop):
        while not stop.is_set():
            try:
                link = self.opener(self.port, BAUD)
            except (serial.SerialException, OSError) as error:
                self._set('error', f'Kan {self.port} niet openen: {error}')
                stop.wait(RETRY_S)
                continue
            try:
                self._session(link, stop)
            except (serial.SerialException, OSError) as error:
                self._set('error', f'Verbinding met {self.port} verbroken: {error}')
            finally:
                try:
                    link.write(b'AT+BREAK\r')
                except (serial.SerialException, OSError):
                    pass
                link.close()
            stop.wait(RETRY_S)

    def _session(self, link, stop):
        reader = Lines(link)
        self.command(link, reader, 'AT+BREAK')
        name = self.command(link, reader, 'AT+NAME?')
        version = self.command(link, reader, 'AT+VER?')
        if name is None:
            raise OSError('geen antwoord: is dit een Grove Vision AI V2 (921600 baud)?')
        info = self.command(link, reader, 'AT+INFO?')
        with self.lock:
            self.device = {'name': name.get('data'), 'version': (version or {}).get('data', {}).get('software')}
            if info and isinstance(info.get('data'), dict):
                self.model = model_info(info['data'].get('info', ''))
        while not stop.is_set():
            sensor = self.command(link, reader, f'AT+SENSOR=1,1,{RESOLUTIONS[self.resolution]}', wait=4.)
            if not sensor or sensor.get('code') != 0:
                self._set('no-camera', 'Het bordje antwoordt, maar de camera niet: controleer de lintkabel van de camera')
                wait = time.monotonic() + RETRY_S
                while time.monotonic() < wait and not stop.is_set():
                    self._event(reader.next(.2))  # distance readings keep coming meanwhile
                if stop.is_set():
                    return
                continue
            # With a model, run it on every frame; without one, just send frames.
            start = 'AT+INVOKE=-1,0,0' if self.model.get('name') else 'AT+SAMPLE=-1'
            answer = self.command(link, reader, start)
            if not answer or answer.get('code') != 0:
                start = 'AT+SAMPLE=-1'
                self.command(link, reader, start)
            self._set('streaming', 'Wachten op het eerste beeld' if not self.jpeg else 'Beeld komt binnen')
            last = time.monotonic()
            while not stop.is_set():
                if self._event(reader.next(.5)):
                    last = time.monotonic()
                if time.monotonic() - last > STALL_S:
                    self._set('error', 'Al 5 s geen beeld: de camera wordt opnieuw gestart')
                    self.command(link, reader, 'AT+BREAK')
                    break

    def command(self, link, reader, text, wait=REPLY_S):
        """Send one AT command and return its answer (the JSON with the same name, type 0), or None."""
        link.write(text.encode('ascii') + b'\r')
        name = text[3:].split('=')[0]  # 'AT+SENSOR=1,1,0' -> 'SENSOR', 'AT+NAME?' -> 'NAME?'
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline:
            message = reader.next(deadline - time.monotonic())
            if message is None:
                continue
            if message.get('type') == 0 and message.get('name') == name:
                return message
            self._event(message)  # a frame still on its way from before, or a distance reading
        return None

    def _event(self, message):
        """Keep an event: a frame (returns True when it carried an image) or a distance reading from the XIAO."""
        if not isinstance(message, dict) or message.get('type') != 1 or not isinstance(message.get('data'), dict):
            return False
        if message.get('name') == 'DISTANCE':
            cm = message['data'].get('cm')
            cm = cm if isinstance(cm, (int, float)) and not isinstance(cm, bool) else None
            with self.lock:
                self.distance = {'cm': cm, 'sensor': str(message['data'].get('sensor') or 'afstandssensor')}
                self.distance_time = time.monotonic()
                self.distance_log.append((self.distance_time, cm))
                self.lock.notify_all()
            return False
        return self._frame(message['data'])

    def _frame(self, data):
        """Keep a frame event's JPEG and detections. Returns True when it carried an image."""
        encoded = data.get('image')
        if not encoded:
            return False
        try:
            jpeg = base64.b64decode(encoded)
        except (ValueError, binascii.Error):
            return False
        classes = self.model.get('classes') or []
        size = data.get('resolution') if isinstance(data.get('resolution'), list) else None
        detections = []
        for box in data.get('boxes') or []:
            if isinstance(box, list) and len(box) >= 6:
                x, y, w, h, score, target = box[:6]
                label = classes[target] if isinstance(target, int) and 0 <= target < len(classes) else str(target)
                # SSCMA boxes give the centre of the box, its width and height, in image pixels.
                detections.append({'label': label, 'score': score, 'x': x, 'y': y, 'w': w, 'h': h})
        now = time.monotonic()
        with self.lock:
            self.jpeg, self.frame_number, self.frame_time = jpeg, self.frame_number + 1, now
            self.detections, self.image_size = detections, size or self.image_size
            self._times = [t for t in self._times if now - t < 2.] + [now]
            self.fps = (len(self._times) - 1) / (now - self._times[0]) if len(self._times) > 1 else 0.
            self.state, self.message = 'streaming', 'Beeld komt binnen'
            self.lock.notify_all()
        return True


class Lines:
    """JSON lines from the board; log lines and broken lines in between are skipped."""

    def __init__(self, link, limit=2_000_000):
        self.link, self.buffer, self.limit = link, bytearray(), limit

    def next(self, timeout):
        deadline = time.monotonic() + max(0., timeout)
        while True:
            end = self.buffer.find(b'\n')
            while end >= 0:
                line, self.buffer = bytes(self.buffer[:end]).strip(), self.buffer[end + 1:]
                if line.startswith(b'{') and line.endswith(b'}'):
                    try:
                        return json.loads(line)
                    except ValueError:
                        pass
                end = self.buffer.find(b'\n')
            if time.monotonic() >= deadline:
                return None
            chunk = self.link.read(max(1, self.link.in_waiting))
            if chunk:
                self.buffer += chunk
                if len(self.buffer) > self.limit:  # never a frame this long: drop the garbage
                    self.buffer = self.buffer[-self.limit // 2:]
