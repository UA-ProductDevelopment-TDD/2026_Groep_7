"""Turn-and-scan: turn estimates from the pictures, closing the circle, field-of-view measurement, placing recognised
things and measured distances on the map, and the scan API with a pretend camera."""
import io
import math
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

import platform_server
from bittle_platform import distance, scan as scanning
from bittle_platform.storage import Store, validate_settings

SIZE = 240


class Scene:
    """A 360-degree scene, and what a pinhole camera with a given field of view sees of it at a heading."""

    def __init__(self, hfov, seed=1):
        self.f = SIZE / 2 / math.tan(math.radians(hfov) / 2)
        rng = np.random.default_rng(seed)
        self.columns = int(round(2 * math.pi * self.f))
        noise = rng.normal(size=(SIZE // 8, self.columns // 8 + 1))
        scene = np.kron(noise, np.ones((8, 8)))[:SIZE, :self.columns]
        scene = (scene - scene.min()) / (scene.max() - scene.min())
        for post in rng.integers(0, self.columns, 25):
            scene[:, post:post + 6] = rng.uniform(0, 1)
        self.scene = scene
        self.rng = rng

    def frame(self, heading):
        cx = cy = (SIZE - 1) / 2
        bearing = np.arctan((cx - np.arange(SIZE)) / self.f)
        world = math.radians(heading) + bearing
        u = np.round((-world % (2 * math.pi)) / (2 * math.pi) * self.columns).astype(int) % self.columns
        rows = np.clip(np.round(cy + (np.arange(SIZE)[:, None] - cy) * np.cos(bearing)[None, :]).astype(int), 0, SIZE - 1)
        image = np.clip(self.scene[rows, u[None, :]] + self.rng.normal(0, .02, (SIZE, SIZE)), 0, 1)
        grey = (image * 255).astype(np.uint8)
        buffer = io.BytesIO()
        Image.fromarray(np.stack([grey] * 3, -1)).save(buffer, 'JPEG', quality=85)
        return buffer.getvalue()


def walk_round(store, scan_id, scene, step=15., seed=2):
    """Turn like Bittle (never exactly what was asked) until the scan recognises the start; returns true headings."""
    rng = np.random.default_rng(seed)
    truth, heading = [0.], 0.
    store.step(scan_id, scene.frame(0), commanded=0)
    for _ in range(45):
        heading += rng.uniform(.65, 1.4) * step
        truth.append(heading)
        result = store.step(scan_id, scene.frame(heading), commanded=step)
        last = result['steps'][-1]
        if last['to_start'] is not None and last['to_start'] <= .75 * step:
            break
    return truth


class ScanGeometryTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.store = scanning.Scans(self.folder)

    def tearDown(self):
        shutil.rmtree(self.folder)

    def test_turns_come_from_the_pictures_and_the_circle_closes(self):
        for true_hfov in (45, 60, 75):
            with self.subTest(true_hfov=true_hfov):
                scene = Scene(true_hfov)
                scan = self.store.create('erf', {'x': 1, 'y': 2, 'heading': 90}, {'hfov': 53.}, {'source': 'none'})
                truth = walk_round(self.store, scan['id'], scene)
                steps = self.store.load(scan['id'])['steps']
                self.assertTrue(all(s['method'] in ('start', 'image') for s in steps), [s['method'] for s in steps])
                self.assertGreater(truth[-1], 330)
                done = self.store.finish(scan['id'])
                self.assertTrue(done['closure']['closed'], done['closure'])
                worst = max(abs(s['heading'] - t) for s, t in zip(done['steps'], truth))
                self.assertLess(worst, 1.5)
                self.assertAlmostEqual(done['hfov_measured'], true_hfov, delta=3)
                self.assertEqual(done['panorama'], 'panorama.jpg')
                with Image.open(self.store.file(scan['id'], 'panorama.jpg')) as panorama:
                    self.assertEqual(panorama.height, SIZE)
                self.assertTrue((self.folder / scan['id'] / 'ground.png').is_file())
                self.assertEqual(done['ground']['x0'], round(1 - scanning.GROUND_RANGE, 3))

    def test_the_tilted_neck_looks_less_far_sideways(self):
        self.assertEqual(scanning.neck_view(0), (0., 0.))
        yaw, pitch = scanning.neck_view(90)
        self.assertAlmostEqual(yaw, 73.9, delta=.1)    # the axis leans 30 degrees forward
        self.assertAlmostEqual(pitch, 25.7, delta=.1)  # and the head looks up a little
        self.assertAlmostEqual(scanning.neck_view(-90)[0], -yaw)

    def test_a_neck_scan_sweeps_the_head_and_turns_the_body_in_between(self):
        """As the page does it: neck from -90 to 90 in 15 degree stops, then the body turns (never exactly as asked)
        so the next sweep starts where the last ended, until the camera sees the start again."""
        scene, rng = Scene(53), np.random.default_rng(4)
        angles = list(range(-90, 91, 15))
        yaw = lambda neck: scanning.neck_view(neck)[0]
        step_yaw = yaw(angles[1]) - yaw(angles[0])
        body_target = 2 * yaw(90) - step_yaw
        scan = self.store.create('', {'x': 0, 'y': 0, 'heading': 0}, {'hfov': 53.}, {'source': 'none'})
        body, truth, done = 0., [], False
        self.store.step(scan['id'], scene.frame(body + yaw(angles[0])), commanded=0, neck=angles[0])
        truth.append(body + yaw(angles[0]))
        while not done and len(truth) < 60:
            for neck in angles[1:]:
                result = self.store.step(scan['id'], scene.frame(body + yaw(neck)), commanded=0, neck=neck)
                truth.append(body + yaw(neck))
                last = result['steps'][-1]
                if last['to_start'] is not None and last['to_start'] <= .75 * step_yaw:
                    done = True
                    break
            if done:
                break
            body += body_target * rng.uniform(.8, 1.25)
            result = self.store.step(scan['id'], scene.frame(body + yaw(angles[0])), commanded=body_target, neck=angles[0])
            truth.append(body + yaw(angles[0]))
        self.assertTrue(done)
        steps = self.store.load(scan['id'])['steps']
        self.assertTrue(all(s['method'] in ('start', 'image', 'neck') for s in steps), [s['method'] for s in steps])
        self.assertLess(len(steps), 45)  # three sweeps or so
        worst = max(abs(s['heading'] - t) for s, t in zip(steps, truth))
        self.assertLess(worst, 2.)
        finished = self.store.finish(scan['id'])
        self.assertTrue(finished['closure']['closed'], finished['closure'])
        self.assertIsNone(finished['hfov_measured'])  # a tilted neck does not measure the lens
        worst = max(abs(s['heading'] - t) for s, t in zip(finished['steps'], truth))
        self.assertLess(worst, 2.)
        self.assertAlmostEqual(finished['steps'][-1]['body'], body, delta=2.)

    def test_a_bare_view_falls_back_to_the_commanded_turn(self):
        flat = io.BytesIO()
        Image.new('RGB', (SIZE, SIZE), (90, 90, 90)).save(flat, 'JPEG')
        scan = self.store.create('', {'x': 0, 'y': 0, 'heading': 0}, {}, {'source': 'none'})
        self.store.step(scan['id'], flat.getvalue(), commanded=0)
        result = self.store.step(scan['id'], flat.getvalue(), commanded=17)
        self.assertEqual((result['steps'][-1]['method'], result['steps'][-1]['turn']), ('command', 17))
        result = self.store.step(scan['id'], None, commanded=None, gyro=21.5)  # no camera at all: the gyro counts
        self.assertEqual((result['steps'][-1]['method'], result['steps'][-1]['heading']), ('gyro', 38.5))
        with self.assertRaisesRegex(ValueError, 'Geen draaihoek'):
            self.store.step(scan['id'], None)
        done = self.store.finish(scan['id'])
        self.assertFalse(done['closure']['closed'])
        with self.assertRaisesRegex(ValueError, 'afgerond'):
            self.store.step(scan['id'], flat.getvalue(), commanded=10)

    def test_recognised_things_are_placed_on_the_map(self):
        scan = {'x': 1., 'y': 1., 'heading': 90., 'camera': {'height': .1, 'tilt': 0., 'hfov': 60., 'forward': 0.},
                'steps': []}
        step = {'heading': 0., 'size': [SIZE, SIZE]}
        f = scanning.focal(SIZE, 60)
        cy = (SIZE - 1) / 2
        foot = cy + f * math.tan(math.atan(.1 / 1.))  # a box whose foot touches the ground 1 m ahead
        box = {'label': 'chicken', 'score': 90, 'x': (SIZE - 1) / 2, 'y': foot - 10, 'w': 20, 'h': 20}
        place = scanning.locate(scan, step, box, f)
        self.assertAlmostEqual(place['distance'], 1., delta=.01)
        self.assertAlmostEqual(place['x'], 1., delta=.01)   # heading 90: straight north
        self.assertAlmostEqual(place['y'], 2., delta=.01)
        left = {**box, 'x': (SIZE - 1) / 2 - f * math.tan(math.radians(30))}  # 30 degrees to the left
        self.assertAlmostEqual(scanning.locate(scan, step, left, f)['bearing'], 120, delta=.5)
        tall = {'label': 'person', 'score': 80, 'x': 120, 'y': 60, 'w': 30, 'h': 100}  # foot above the horizon
        self.assertAlmostEqual(scanning.locate(scan, step, tall, f)['distance'], 1.7 * f / 100, delta=.01)
        self.assertIsNone(scanning.locate(scan, step, {**tall, 'label': 'kite'}, f))
        merged = scanning.merge([{'label': 'fox', 'score': 80, 'x': 1, 'y': 1}, {'label': 'fox', 'score': 60, 'x': 1.2, 'y': 1},
                                 {'label': 'fox', 'score': 70, 'x': 3, 'y': 1}])
        self.assertEqual([(m['x'], m['seen']) for m in merged], [(1.1, 2), (3, 1)])

    def test_the_camera_srf05_gives_one_reading_per_step(self):
        settings = distance.validate_settings({'source': 'camera', 'forward': 0})
        reading = distance.read(settings, {'x': 0, 'y': 0, 'heading': 0}, None, [64.8, 65.0, None, 65.3, 65.1])
        self.assertAlmostEqual(reading[0]['distance'], .65, delta=.002)  # the median; one missed echo is ignored
        self.assertEqual(reading[0]['samples'], 4)
        self.assertEqual(distance.read(settings, {}, None, [None, None, 80.]), [])  # mostly no echo: nothing in reach
        self.assertEqual(distance.read(settings, {}, None, []), [])                 # no sensor readings at all
        self.assertEqual(distance.read(settings, {}, None, [500.] * 5), [])         # beyond its reach (4 m)
        scan = self.store.create('', {'x': 2, 'y': 2, 'heading': 0}, {}, {'source': 'camera', 'forward': 0})
        result = self.store.step(scan['id'], None, commanded=0, samples=[100.] * 7)
        self.assertEqual((result['steps'][0]['distance'], result['steps'][0]['samples']), (1., 7))
        self.assertEqual([(p['x'], p['y']) for p in result['points']], [(3., 2.)])
        result = self.store.step(scan['id'], None, commanded=15, samples=[])
        self.assertEqual((result['steps'][1]['distance'], result['steps'][1]['samples']), (None, 0))

    def test_a_measured_distance_places_what_the_camera_recognised(self):
        scan = {'x': 0., 'y': 0., 'heading': 0., 'camera': {'height': .1, 'tilt': 0., 'hfov': 60., 'forward': 0.},
                'sensor': {'forward': 0.}, 'steps': []}
        f = scanning.focal(SIZE, 60)
        foot = (SIZE - 1) / 2 + f * .1  # the picture puts the box's foot 1 m ahead
        box = {'label': 'chicken', 'score': 90, 'x': (SIZE - 1) / 2, 'y': foot - 10, 'w': 20, 'h': 20}
        step = {'heading': 0., 'size': [SIZE, SIZE], 'ranges': [{'bearing': 0., 'distance': 1.4}]}
        place = scanning.locate(scan, step, box, f)
        self.assertEqual((place['distance'], place['measured']), (1.4, True))   # in the beam: the echo counts
        left = {**box, 'x': (SIZE - 1) / 2 - f * math.tan(math.radians(30))}
        self.assertFalse(scanning.locate(scan, step, left, f)['measured'])       # outside the beam
        far = {**step, 'ranges': [{'bearing': 0., 'distance': 3.}]}
        place = scanning.locate(scan, far, box, f)
        self.assertEqual((round(place['distance'], 2), place['measured']), (1., False))  # an echo from something else

    def test_the_test_sensor_measures_the_drawn_map_and_the_outline_closes(self):
        room = {'items': [{'kind': 'wall', 'points': [[0, 0], [4, 0], [4, 4], [0, 4]], 'closed': True},
                          {'kind': 'obstacle', 'x': 3, 'y': 2, 'w': .4, 'h': .4, 'angle': 0},
                          {'kind': 'label', 'x': 1, 'y': 1, 'label': 'niet massief'}]}
        settings = distance.validate_settings({'source': 'test', 'forward': 0})
        self.assertEqual(distance.read(settings, {'x': 2, 'y': 2, 'heading': 0}, room), [{'bearing': 0, 'distance': .8}])
        self.assertEqual(distance.read(settings, {'x': 2, 'y': 2, 'heading': 90}, room)[0]['distance'], 2.)
        self.assertEqual(distance.read({**settings, 'max_range': 1.5}, {'x': 2, 'y': 2, 'heading': 90}, room), [])
        self.assertEqual(distance.read(distance.validate_settings({}), {'x': 2, 'y': 2, 'heading': 0}, room), [])
        with self.assertRaisesRegex(ValueError, 'afstandssensor'):
            distance.validate_settings({'source': 'radar'})
        scan = self.store.create('kamer', {'x': 2, 'y': 2, 'heading': 0}, {}, {'source': 'test', 'forward': 0})
        heading = 0.
        self.store.step(scan['id'], None, commanded=0, map_doc=room)
        while heading < 350:
            heading += 10
            result = self.store.step(scan['id'], None, commanded=10, map_doc=room)
        self.assertEqual(len(result['points']), 36)
        distances = sorted(p['distance'] for p in result['points'])
        self.assertAlmostEqual(distances[0], .8, delta=.01)            # the obstacle
        self.assertAlmostEqual(distances[-1], 2 / math.cos(math.radians(40)), delta=.01)  # nearest a corner
        self.assertTrue(result['outline'])
        self.assertTrue(all(len(line) >= 2 for line in result['outline']))


class ScanApiTest(unittest.TestCase):
    """The scan endpoints with a pretend camera that shows a synthetic scene at the heading the test sets."""

    class Camera:
        def __init__(self, scene):
            self.scene, self.heading, self.number, self.port = scene, 0., 0, 'COM9'

        def status(self):
            return {'state': 'streaming', 'detections': [{'label': 'chicken', 'score': 88, 'x': 119.5, 'y': 160, 'w': 30, 'h': 30}]}

        def latest(self):
            return self.scene.frame(self.heading), self.number

        def wait_frame(self, after, timeout):
            self.number = after + 1
            return self.scene.frame(self.heading), self.number

        def distance_since(self, start):
            return [60.] * 3

        def disconnect(self):
            pass

    @classmethod
    def setUpClass(cls):
        cls.folder = Path(tempfile.mkdtemp())
        cls.saved = platform_server.store, platform_server.camera
        platform_server.store = Store(cls.folder)
        cls.camera = platform_server.camera = cls.Camera(Scene(53))
        cls.client = TestClient(platform_server.app)

    @classmethod
    def tearDownClass(cls):
        platform_server.store, platform_server.camera = cls.saved
        shutil.rmtree(cls.folder)

    def test_settings(self):
        c = self.client
        settings = c.get('/api/settings').json()
        self.assertEqual(settings['camera']['hfov'], 53)
        self.assertIn('test', settings['distance_sources'])
        changed = c.put('/api/settings', json={'camera': {'height': .12, 'hfov': 60}, 'scan': {'step': 20, 'turn': 'motion:draai'},
                                               'distance': {'source': 'test'}}).json()
        self.assertEqual((changed['camera']['height'], changed['scan']['turn'], changed['distance']['source']), (.12, 'motion:draai', 'test'))
        self.assertEqual(c.put('/api/settings', json={'scan': {'turn': 'fly'}}).status_code, 400)
        self.assertEqual(c.put('/api/settings', json={'camera': {'hfov': 5}}).status_code, 400)
        c.put('/api/settings', json={}).raise_for_status()
        self.assertEqual(validate_settings({})['scan']['step'], 15)

    def test_a_scan_from_start_to_map(self):
        c = self.client
        c.put('/api/maps/erf', json={'items': [{'kind': 'wall', 'points': [[-2, -2], [2, -2], [2, 2], [-2, 2]], 'closed': True}],
                                     'robot': {'x': 0, 'y': 0, 'heading': 0}}).raise_for_status()
        c.put('/api/settings', json={'distance': {'source': 'test', 'forward': 0}}).raise_for_status()
        self.assertEqual(c.post('/api/scans', json={'map': 'erf'}).status_code, 400)  # no robot pose
        scan = c.post('/api/scans', json={'map': 'erf', 'x': 0, 'y': 0, 'heading': 0}).json()
        rng = np.random.default_rng(5)
        self.camera.heading = 0.
        result = c.post(f"/api/scans/{scan['id']}/step", json={'commanded': 0}).json()
        for _ in range(40):
            self.camera.heading += rng.uniform(10, 20)
            result = c.post(f"/api/scans/{scan['id']}/step", json={'commanded': 15}).json()
            last = result['steps'][-1]
            if last['to_start'] is not None and last['to_start'] <= 11:
                break
        self.assertEqual(last['method'], 'image')
        done = c.post(f"/api/scans/{scan['id']}/finish").json()
        self.assertTrue(done['closure']['closed'], done['closure'])
        self.assertEqual(len(done['points']), len(done['steps']))
        self.assertTrue(all(1.99 <= p['distance'] <= 2.84 for p in done['points']))  # the walls of the 4 m room
        self.assertTrue(done['objects'])
        self.assertEqual(done['objects'][0]['label'], 'chicken')
        self.assertEqual([s['id'] for s in c.get('/api/scans', params={'map': 'erf'}).json()], [scan['id']])
        self.assertEqual(c.get('/api/scans', params={'map': 'ander'}).json(), [])
        self.assertEqual(c.get(f"/api/scans/{scan['id']}/files/panorama.jpg").headers['content-type'], 'image/jpeg')
        self.assertEqual(c.get(f"/api/scans/{scan['id']}/files/frame-01.jpg").status_code, 200)
        self.assertEqual(c.get(f"/api/scans/{scan['id']}/files/scan.json").status_code, 404)
        self.assertEqual(c.get('/api/scans/../../motor-layout').status_code, 404)
        self.assertEqual(c.post(f"/api/scans/{scan['id']}/step", json={}).status_code, 400)  # finished
        c.delete(f"/api/scans/{scan['id']}").raise_for_status()

    def test_a_scan_with_the_camera_srf05(self):
        c = self.client
        c.put('/api/settings', json={'distance': {'source': 'camera', 'forward': 0}}).raise_for_status()
        self.assertIn('camera', c.get('/api/settings').json()['distance_sources'])
        scan = c.post('/api/scans', json={'map': '', 'x': 0, 'y': 0, 'heading': 0}).json()
        result = c.post(f"/api/scans/{scan['id']}/step", json={'commanded': 0}).json()
        self.assertEqual(result['steps'][0]['distance'], .6)
        self.assertEqual([(p['x'], p['y']) for p in result['points']], [(.6, 0.)])
        self.assertTrue(result['objects'][0]['measured'])  # the chicken straight ahead gets the echo's distance
        view = result['steps'][0]['view']  # for the 3D surroundings: where the photo was taken and how deep it looks
        self.assertEqual((view['x'], view['y'], view['z'], view['heading'], view['tilt']), (.1, 0., .1, 0., 0.))
        self.assertEqual(view['depth'], [[.5]])  # 0.6 m from the sensor at the centre, the camera 10 cm ahead
        self.assertEqual(view['size'], [SIZE, SIZE])
        c.delete(f"/api/scans/{scan['id']}").raise_for_status()
        self.assertEqual(c.get(f"/api/scans/{scan['id']}").status_code, 404)


if __name__ == '__main__':
    unittest.main()
