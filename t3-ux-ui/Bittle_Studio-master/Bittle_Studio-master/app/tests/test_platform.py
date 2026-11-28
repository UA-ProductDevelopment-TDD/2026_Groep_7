"""Bittle Platform: saved motions, maps and motor layout, the camera reader (with a pretend Grove Vision AI V2) and
the server's API."""
import base64
import json
import shutil
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import platform_server
from bittle_platform import camera as vision
from bittle_platform.storage import JOINTS, Store, default_layout, validate_layout, validate_map, validate_motion

JPEG = b'\xff\xd8\xff\xe0fake-jpeg\xff\xd9'
MODEL_INFO = base64.b64encode(json.dumps({'model_name': 'Face Detection', 'classes': ['face']}).encode()).decode()


class FakeVisionAI:
    """Answers like a Grove Vision AI V2 running SenseCraft firmware; camera=False makes its camera missing."""

    def __init__(self, camera=True):
        self.camera, self.streaming, self.out, self.lock = camera, False, bytearray(), threading.Lock()
        self.commands, self.closed, self.last_frame = [], False, 0.

    def reply(self, name, code=0, data=None, kind=0):
        line = json.dumps({'type': kind, 'name': name, 'code': code, 'data': data}).encode() + b'\r\n'
        with self.lock:
            self.out += line

    def write(self, data):
        for command in data.decode().split('\r'):
            if not command:
                continue
            self.commands.append(command)
            name = command[3:].split('=')[0]
            with self.lock:
                self.out += b'dw_iic_write err_state:2 \r\n'  # log lines like the real board's come in between
            if name == 'NAME?':
                self.reply(name, data='Grove Vision AI V2')
            elif name == 'VER?':
                self.reply(name, data={'software': '2025.01.02'})
            elif name == 'INFO?':
                self.reply(name, data={'info': MODEL_INFO})
            elif name == 'SENSOR':
                self.reply(name, code=0 if self.camera else 4, data={'sensor': {'id': 1}})
            elif name in ('INVOKE', 'SAMPLE'):
                self.reply(name, data={})
                self.streaming = self.camera
            elif name == 'BREAK':
                self.streaming = False
                self.reply(name)
        return len(data)

    @property
    def in_waiting(self):
        now = time.monotonic()
        if self.streaming and now - self.last_frame > .02:
            self.last_frame = now
            self.reply('INVOKE', kind=1, data={'count': 1, 'boxes': [[120, 100, 40, 50, 87, 0]],
                                               'resolution': [240, 240], 'image': base64.b64encode(JPEG).decode()})
        with self.lock:
            return len(self.out)

    def read(self, size):
        if not self.out:
            time.sleep(.005)
        with self.lock:
            chunk, self.out[:] = bytes(self.out[:size]), self.out[size:]
        return chunk

    def close(self):
        self.closed = True


def wait_for(predicate, seconds=5.):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(.05)
    return False


class CameraTest(unittest.TestCase):
    def test_frames_and_detections_arrive(self):
        device = FakeVisionAI()
        camera = vision.VisionCamera(opener=lambda port, baud: device)
        camera.connect('COM9', '240')
        try:
            self.assertTrue(wait_for(lambda: camera.status()['frame'] >= 3), camera.status())
            status = camera.status()
            self.assertEqual(status['state'], 'streaming')
            self.assertEqual(status['device'], {'name': 'Grove Vision AI V2', 'version': '2025.01.02'})
            self.assertEqual(status['model'], {'name': 'Face Detection', 'classes': ['face']})
            self.assertEqual(status['detections'], [{'label': 'face', 'score': 87, 'x': 120, 'y': 100, 'w': 40, 'h': 50}])
            self.assertEqual(status['image_size'], [240, 240])
            self.assertEqual(camera.latest()[0], JPEG)
            jpeg, number = camera.wait_frame(camera.latest()[1], 2)
            self.assertEqual(jpeg, JPEG)
            self.assertIn('AT+SENSOR=1,1,0', device.commands)
            self.assertIn('AT+INVOKE=-1,0,0', device.commands)  # a model is loaded: it runs on every frame
        finally:
            camera.disconnect()
        self.assertTrue(device.closed)
        self.assertEqual(camera.status()['state'], 'off')

    def test_a_missing_camera_is_reported_and_retried(self):
        device = FakeVisionAI(camera=False)
        camera = vision.VisionCamera(opener=lambda port, baud: device)
        camera.connect('COM9', '480')
        try:
            self.assertTrue(wait_for(lambda: camera.status()['state'] == 'no-camera'))
            self.assertIn('lintkabel', camera.status()['message'])
            self.assertIn('AT+SENSOR=1,1,1', device.commands)
            device.camera = True  # plugged in: the reader starts the stream by itself
            self.assertTrue(wait_for(lambda: camera.status()['frame'] > 0, 8), camera.status())
        finally:
            camera.disconnect()

    def test_a_port_that_does_not_open_is_an_error(self):
        def refuse(port, baud):
            raise vision.serial.SerialException('access denied')
        camera = vision.VisionCamera(opener=refuse)
        camera.connect('COM9')
        try:
            self.assertTrue(wait_for(lambda: camera.status()['state'] == 'error'))
            self.assertIn('COM9', camera.status()['message'])
        finally:
            camera.disconnect()
        with self.assertRaises(ValueError):
            camera.connect('COM9', '1080')

    def test_the_wifi_camera_streams_through_a_tcp_bridge(self):
        """The XIAO firmware passes the board's bytes through TCP port 3333; here a local socket plays the XIAO."""
        device = FakeVisionAI()
        server = socket.create_server(('127.0.0.1', 0))
        address = server.getsockname()

        def bridge():
            link, _ = server.accept()
            link.settimeout(.01)
            with link:
                while not device.closed:
                    try:
                        data = link.recv(4096)
                        if not data:
                            return
                        device.write(data)
                    except TimeoutError:
                        pass
                    except OSError:  # the platform hung up
                        return
                    if device.in_waiting:
                        link.sendall(device.read(65536))
        threading.Thread(target=bridge, daemon=True).start()
        camera = vision.VisionCamera()  # the real opener: pyserial's socket:// link
        camera.connect(f'wifi://{address[0]}:{address[1]}', '240')
        try:
            self.assertTrue(wait_for(lambda: camera.status()['frame'] >= 3), camera.status())
            self.assertEqual(camera.status()['model']['name'], 'Face Detection')
            self.assertEqual(camera.latest()[0], JPEG)
            self.assertEqual(camera.status()['detections'][0]['label'], 'face')
        finally:
            camera.disconnect()
            device.closed = True
            server.close()

    def test_distance_readings_from_the_xiao(self):
        """The XIAO puts SRF05 readings between the board's lines; they arrive even while the camera is missing."""
        device = FakeVisionAI(camera=False)
        camera = vision.VisionCamera(opener=lambda port, baud: device)
        camera.connect('COM5', '240')
        try:
            self.assertTrue(wait_for(lambda: camera.status()['state'] == 'no-camera'))
            self.assertIsNone(camera.status()['distance'])
            device.reply('DISTANCE', kind=1, data={'cm': 65.2, 'sensor': 'srf05'})
            self.assertTrue(wait_for(lambda: (camera.status()['distance'] or {}).get('cm') == 65.2), camera.status())
            device.reply('DISTANCE', kind=1, data={'cm': None, 'sensor': 'srf05'})  # nothing in reach
            self.assertTrue(wait_for(lambda: camera.status()['distance']['cm'] is None))
            self.assertTrue(wait_for(lambda: camera.status()['distance'] is None, 3))  # no fresh reading: gone
        finally:
            camera.disconnect()

    def test_wifi_addresses(self):
        self.assertIsNone(vision.wifi_address('COM6'))
        self.assertEqual(vision.wifi_address('wifi://bittle-camera.local'), ('bittle-camera.local', 3333))
        self.assertEqual(vision.wifi_address('wifi://192.168.1.42:4000/'), ('192.168.1.42', 4000))
        for bad in ('wifi://', 'wifi://a b', 'wifi://host:0', 'wifi://-x', 'wifi://x/../y'):
            with self.assertRaises(ValueError, msg=bad):
                vision.wifi_address(bad)
        self.assertTrue(any(p.get('wifi') for p in vision.ports()))

    def test_model_info_and_lines(self):
        self.assertEqual(vision.model_info(MODEL_INFO), {'name': 'Face Detection', 'classes': ['face']})
        self.assertEqual(vision.model_info('not base64!'), {'name': None, 'classes': []})
        device = FakeVisionAI()
        device.out += b'garbage {"broken": \r\nlog line\r\n{"type": 0, "name": "X", "code": 0}\r\n'
        self.assertEqual(vision.Lines(device).next(1), {'type': 0, 'name': 'X', 'code': 0})


class StorageTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.store = Store(self.folder)

    def tearDown(self):
        shutil.rmtree(self.folder)

    def test_motor_layout(self):
        layout = default_layout()
        self.assertEqual(layout['right-front-knee-joint'], {'servo': 13, 'sign': -1, 'offset': 0.})
        self.assertEqual(layout['neck-joint']['servo'], 0)
        self.assertEqual(sorted(entry['servo'] for entry in layout.values()), [0, 8, 9, 10, 11, 12, 13, 14, 15])
        changed = self.store.put_layout('crab', {'left-front-knee-joint': {'servo': 12, 'sign': -1, 'offset': 5}})
        self.assertEqual(changed['left-front-knee-joint'], {'servo': 12, 'sign': -1, 'offset': 5.})
        self.assertEqual(self.store.layouts()['crab'], changed)
        self.assertEqual(self.store.layouts()['stock'], default_layout())
        with self.assertRaisesRegex(ValueError, 'hetzelfde servonummer'):
            validate_layout({'neck-joint': {'servo': 8}})
        with self.assertRaisesRegex(ValueError, 'richting'):
            validate_layout({'neck-joint': {'sign': 2}})
        with self.assertRaisesRegex(ValueError, 'model'):
            self.store.put_layout('wolf', {})

    def test_motions(self):
        motion = {'model': 'crab', 'loop': True, 'frames': [{'pose': {'neck-joint': 10, 'left-front-knee-joint': -30.123}, 'seconds': .3}]}
        saved = self.store.motions.put('stap over steen', motion)
        self.assertEqual(saved['frames'][0]['pose'], {'neck-joint': 10., 'left-front-knee-joint': -30.12})
        self.assertEqual(self.store.motions.get('stap over steen'), saved)
        self.assertEqual([m['name'] for m in self.store.motions.list()], ['stap over steen'])
        for bad, message in (({'frames': []}, '1 tot 500'), ({'frames': [{'pose': {'tail': 3}}]}, 'onbekend gewricht'),
                             ({'frames': [{'pose': {'neck-joint': 3}, 'seconds': 99}]}, 'tijd'),
                             ({'model': 'dog', 'frames': [{'pose': {'neck-joint': 0}}]}, 'model')):
            with self.assertRaisesRegex(ValueError, message):
                validate_motion(bad, 'x')
        with self.assertRaisesRegex(ValueError, 'naam'):
            self.store.motions.put('../geheim', motion)
        self.store.motions.delete('stap over steen')
        with self.assertRaises(KeyError):
            self.store.motions.get('stap over steen')

    def test_maps_and_backgrounds(self):
        data = {'size': [8, 6], 'items': [
            {'kind': 'fence', 'points': [[0, 0], [3, 0], [3, 2]], 'closed': True},
            {'kind': 'coop', 'x': 1.5, 'y': 1, 'w': 1, 'h': .8, 'angle': 0},
            {'kind': 'marker', 'x': 3, 'y': 1, 'marker_id': 7, 'heading': 180},
            {'kind': 'dock', 'x': -1, 'y': -1, 'heading': 90}],
            'robot': {'x': .3, 'y': -1.5, 'heading': 0}, 'background': {'file': 'erf-background.png', 'scale': .01}}
        saved = self.store.maps.put('erf', data)
        self.assertEqual([item['kind'] for item in saved['items']], ['fence', 'coop', 'marker', 'dock'])
        self.assertEqual(saved['items'][2]['marker_id'], 7)
        self.assertEqual(saved['background']['origin'], [0, 0])
        for bad, message in (({'items': [{'kind': 'lava', 'x': 0, 'y': 0}]}, 'soort'),
                             ({'items': [{'kind': 'wall'}]}, 'punten of x en y'),
                             ({'items': [{'kind': 'marker', 'x': 0, 'y': 0, 'marker_id': 5000}]}, 'markernummer'),
                             ({'background': {'file': '../x.png'}}, 'bestandsnaam')):
            with self.assertRaisesRegex(ValueError, message):
                validate_map(bad, 'x')
        name = self.store.put_background('erf', 'image/png', b'\x89PNG...')
        self.assertEqual(self.store.get_background(name).read_bytes(), b'\x89PNG...')
        self.store.put_background('erf', 'image/jpeg', b'\xff\xd8')  # a new image replaces the old one
        self.assertFalse((self.folder / 'maps' / name).exists())
        with self.assertRaisesRegex(ValueError, 'PNG'):
            self.store.put_background('erf', 'text/html', b'<script>')
        with self.assertRaises(KeyError):
            self.store.get_background('../motor-layout.json')
        self.store.delete_map('erf')
        self.assertEqual(list((self.folder / 'maps').iterdir()), [])


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = Path(tempfile.mkdtemp())
        cls.saved_store, platform_server.store = platform_server.store, Store(cls.folder)
        cls.client = TestClient(platform_server.app)

    @classmethod
    def tearDownClass(cls):
        platform_server.store = cls.saved_store
        shutil.rmtree(cls.folder)

    def test_models_layout_and_skills(self):
        c = self.client
        models = {m['id']: m for m in c.get('/api/models').json()}
        self.assertEqual(models['stock']['urdf'], '/assets/bittle/bittle.urdf')
        self.assertTrue(models['crab']['urdf'].startswith('/assets/bittle/generated/'))
        self.assertEqual(c.get(models['crab']['urdf']).status_code, 200)
        self.assertEqual(set(c.get('/api/layouts').json()['stock']), set(JOINTS))
        plan = c.get('/api/skill', params={'command': 'ksit'}).json()
        self.assertEqual(plan['name'], 'sit')
        self.assertIsNone(plan['loop_from'])
        self.assertEqual(set(plan['segments'][0][1]), set(JOINTS))
        flipped = {joint: {'sign': -entry['sign']} for joint, entry in default_layout().items()}
        c.put('/api/layouts/stock', json=flipped).raise_for_status()
        again = c.get('/api/skill', params={'command': 'ksit'}).json()
        joint = 'left-front-shoulder-joint'
        self.assertAlmostEqual(again['segments'][0][1][joint], -plan['segments'][0][1][joint])  # the layout is used
        self.assertEqual(c.get('/api/skill', params={'command': 'kmoonwalkX'}).status_code, 404)
        self.assertEqual(c.put('/api/layouts/stock', json={'neck-joint': {'servo': 99}}).json()['detail'][:11], 'neck-joint:')

    def test_motions_maps_and_camera_api(self):
        c = self.client
        motion = {'frames': [{'pose': {'neck-joint': 20}, 'seconds': .5}]}
        self.assertEqual(c.put('/api/motions/zwaai', json=motion).json()['name'], 'zwaai')
        self.assertEqual([m['name'] for m in c.get('/api/motions').json()], ['zwaai'])
        self.assertEqual(c.get('/api/motions/onbekend').status_code, 404)
        self.assertEqual(c.put('/api/motions/zwaai', json={'frames': []}).status_code, 400)
        c.delete('/api/motions/zwaai').raise_for_status()
        c.put('/api/maps/erf', json={'items': [{'kind': 'label', 'x': 1, 'y': 1, 'label': 'Hok'}]}).raise_for_status()
        file = c.put('/api/maps/erf/background', content=b'\x89PNG', headers={'Content-Type': 'image/png'}).json()['file']
        self.assertEqual(c.get(f'/api/backgrounds/{file}').content, b'\x89PNG')
        c.delete('/api/maps/erf').raise_for_status()
        self.assertEqual(c.get(f'/api/backgrounds/{file}').status_code, 404)
        self.assertEqual(c.get('/api/camera/status').json()['state'], 'off')
        self.assertIsInstance(c.get('/api/camera/ports').json(), list)
        self.assertEqual(c.get('/api/camera/frame.jpg').status_code, 404)
        self.assertEqual(c.post('/api/camera/connect', json={}).status_code, 400)
        self.assertTrue(c.get('/api/info').json()['can_edit'])
        self.assertIn('Bittle Platform', c.get('/').text)

    def test_only_this_computer_may_change_things(self):
        self.assertTrue(platform_server.local('127.0.0.1'))
        self.assertTrue(platform_server.local('::1'))
        self.assertFalse(platform_server.local('192.168.1.20'))


if __name__ == '__main__':
    unittest.main()
