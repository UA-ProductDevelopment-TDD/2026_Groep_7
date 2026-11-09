"""Checks for the coop sensors: PNG encoding, camera, ToF, IMU, rate scheduling, the sensor suite and the hub client."""
import copy
import json
import math
import struct
import threading
import unittest
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import pybullet as p

from coop import config, frames, png
from coop.hub import Hub
from coop.hub_client import HubClient, HubError
from coop.robot import CoopRobot
from coop.sensors import SensorSuite

STEP = 1 / 240
# The default head camera position [.03, 0, .01] lies inside the head's collision shape; this one is clear of it.
HEAD_CAMERA = [.05, 0, .01]


def chunks(data):
    """The (type, payload) chunks of a PNG, with every CRC checked."""
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    result, position = [], 8
    while position < len(data):
        length, kind = struct.unpack('>I4s', data[position:position + 8])
        payload = data[position + 8:position + 8 + length]
        crc, = struct.unpack('>I', data[position + 8 + length:position + 12 + length])
        assert crc == zlib.crc32(kind + payload) & 0xffffffff
        result.append((kind, payload))
        position += 12 + length
    return result


class PngTest(unittest.TestCase):
    def decode(self, data):
        parts = chunks(data)
        self.assertEqual([kind for kind, _ in parts], [b'IHDR', b'IDAT', b'IEND'])
        width, height, depth, colour, *_ = struct.unpack('>IIBBBBB', parts[0][1])
        return width, height, depth, colour, zlib.decompress(parts[1][1])

    def test_grey_rgb_and_rgba(self):
        rng = np.random.default_rng(1)
        for shape, colour in (((7, 11), 0), ((7, 11, 3), 2), ((7, 11, 4), 6)):
            image = rng.integers(0, 256, shape, dtype=np.uint8)
            data = png.encode(image)
            self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))
            width, height, depth, kind, raw = self.decode(data)
            channels = 1 if image.ndim == 2 else shape[2]
            self.assertEqual((width, height, depth, kind), (11, 7, 8, colour))
            self.assertEqual(len(raw), height * (width * channels + 1))
            rows = np.frombuffer(raw, np.uint8).reshape(height, width * channels + 1)
            self.assertTrue((rows[:, 0] == 0).all())  # filter type none
            self.assertTrue((rows[:, 1:] == image.reshape(height, -1)).all())

    def test_rejects_unsuitable_arrays(self):
        for bad in (np.zeros((4, 4), np.float32), np.zeros((4, 4, 2), np.uint8), np.zeros(4, np.uint8),
                    np.zeros((0, 4), np.uint8)):
            with self.assertRaises(ValueError):
                png.encode(bad)


class SensorTestCase(unittest.TestCase):
    """A Bullet client with flat ground, the coop robot standing at its scenario start, and a hub."""

    def setUp(self):
        self.client = p.connect(p.DIRECT)
        p.setGravity(0, 0, -9.81, physicsClientId=self.client)
        p.setTimeStep(STEP, physicsClientId=self.client)
        p.setPhysicsEngineParameter(numSolverIterations=80, physicsClientId=self.client)
        self.ground = p.createMultiBody(0, p.createCollisionShape(p.GEOM_PLANE, physicsClientId=self.client),
                                        physicsClientId=self.client)
        self.scenario = config.validate(config.default())
        self.robot = CoopRobot(self.client, self.scenario['robot'])
        start = self.scenario['robot']['start']
        self.start, self.heading = start['position'], math.radians(start['heading'])
        self.forward = [math.cos(self.heading), math.sin(self.heading)]
        self.robot.place(start['position'], start['heading'], lambda x, y: 0.)
        self.hub = Hub()
        self.time = 0.

    def tearDown(self):
        p.disconnect(self.client)

    def definition(self, sensor_id, **changes):
        found = next(d for d in self.scenario['sensors'] if d['id'] == sensor_id)
        return {**copy.deepcopy(found), **changes}

    def suite(self, *definitions, **options):
        return SensorSuite(self.robot, list(definitions), self.hub, **options)

    def box(self, distance, half, colour=(.8, .1, .1, 1), side=0.):
        """A fixed box whose centre is `distance` metres ahead of the robot start, sitting on the ground."""
        x = self.start[0] + self.forward[0] * distance - self.forward[1] * side
        y = self.start[1] + self.forward[1] * distance + self.forward[0] * side
        quaternion = p.getQuaternionFromEuler([0, 0, self.heading])
        shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=half, physicsClientId=self.client)
        look = p.createVisualShape(p.GEOM_BOX, halfExtents=half, rgbaColor=colour, physicsClientId=self.client)
        return p.createMultiBody(0, shape, look, [x, y, half[2]], quaternion, physicsClientId=self.client)

    def ahead(self, distance):
        """Point on the ground `distance` metres ahead of the robot start."""
        return np.array([self.start[0] + self.forward[0] * distance, self.start[1] + self.forward[1] * distance, 0.])

    def simulate(self, seconds, suite=None):
        self.robot.running = True
        for _ in range(round(seconds * 240)):
            self.robot.drive_motors()
            p.stepSimulation(physicsClientId=self.client)
            self.time += STEP
            if suite:
                suite.step(self.time, STEP)


class CameraTest(SensorTestCase):
    def camera(self, **changes):
        suite = self.suite(self.definition('head-cam', **{'position': HEAD_CAMERA, **changes}))
        return suite, suite.sensors['head-cam']

    def test_capture_shapes_and_types(self):
        _, camera = self.camera()
        shot = camera.capture()
        self.assertEqual(shot['rgb'].shape, (120, 160, 3))
        self.assertEqual(shot['rgb'].dtype, np.uint8)
        self.assertEqual(shot['depth'].shape, (120, 160))
        self.assertEqual(shot['depth'].dtype, np.float32)
        self.assertEqual(shot['segmentation'].shape, (120, 160))
        self.assertEqual(shot['segmentation'].dtype, np.int32)
        self.assertEqual(len(shot['position']), 3)
        self.assertEqual(len(shot['quaternion']), 4)
        # Looking along the horizon: sky at the top has no hit, ground below has a finite depth.
        self.assertTrue(np.isinf(shot['depth'][0]).all())
        self.assertTrue((shot['segmentation'][0] == -1).all())
        self.assertTrue(np.isfinite(shot['depth'][-1]).all())
        self.assertEqual(shot['segmentation'][-1, 0], self.ground)

    def test_sees_a_red_box_in_front(self):
        suite, camera = self.camera()
        box = self.box(.7, [.05, .1, .1])
        reading = suite.refresh(0.) or suite.readings()['head-cam']
        self.assertIn(str(box), reading['visible'])
        self.assertGreater(reading['visible'][str(box)], 400)
        shot = camera.capture()
        red, green, blue = (int(v) for v in shot['rgb'][60, 80])
        self.assertTrue(red > 100 and green < 40 and blue < 40, (red, green, blue))
        self.assertEqual(shot['segmentation'][60, 80], box)
        eye = np.array(reading['pose']['position'])
        expected = float(np.dot(self.ahead(.65) - eye, [*self.forward, 0.]))  # the box's near face
        self.assertAlmostEqual(float(shot['depth'][60, 80]), expected, delta=.02)
        self.assertLess(reading['nearest'], expected + .05)

    def test_reading_frame_and_message(self):
        suite, camera = self.camera()
        suite.refresh(0.)
        reading = suite.readings()['head-cam']
        json.dumps(reading)
        self.assertEqual((reading['type'], reading['frame'], reading['width'], reading['height']),
                         ('camera', 1, 160, 120))
        self.assertTrue(0 <= reading['brightness'] <= 1)
        self.assertGreater(reading['brightness'], 0)
        self.assertLess(reading['self_pixels'], .3)
        self.assertEqual(reading['url'], '/api/hub/frame/head-cam.png?f=1')
        self.assertEqual(set(reading['pose']), {'position', 'forward', 'up'})
        stored, meta = self.hub.frame('head-cam')
        self.assertTrue(stored.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertEqual(meta['frame'], 1)
        width, height = struct.unpack('>II', chunks(stored)[0][1][:8])
        self.assertEqual((width, height), (160, 120))
        message = self.hub.latest('camera/')['camera/head-cam']
        self.assertEqual((message['source'], message['value']), ('head-cam', reading))
        suite.refresh(0.)
        self.assertEqual(self.hub.latest('camera/head-cam')['camera/head-cam']['value']['frame'], 2)
        self.assertEqual(camera.reading['url'], '/api/hub/frame/head-cam.png?f=2')

    def test_camera_inside_the_head_fails_its_self_test(self):
        _, camera = self.camera(position=[.03, 0, .01])
        own = next(c for c in camera.self_test() if c['name'].startswith('Own robot'))
        self.assertFalse(own['ok'])
        self.assertIn('move the camera', own['detail'])

    def test_head_camera_turns_with_the_neck(self):
        suite, _ = self.camera()
        suite.refresh(0.)
        before = np.array(suite.readings()['head-cam']['pose']['forward'])
        self.robot.pose({'neck-joint': 45})
        suite.refresh(0.)
        after = np.array(suite.readings()['head-cam']['pose']['forward'])
        yaw = lambda v: math.degrees(math.atan2(v[1], v[0]))
        self.assertAlmostEqual(float(before[2]), 0, delta=.02)
        # Positive turns the head left. The URDF's neck axis leans 30 deg, so the head also tilts a little as it turns:
        # 45 deg of servo angle moves the view direction by 38.7 deg.
        self.assertAlmostEqual((yaw(after) - yaw(before) + 180) % 360 - 180, 35, delta=8)
        self.assertAlmostEqual(math.degrees(math.acos(float(np.dot(before, after)))), 38.7, delta=1)


class TofTest(SensorTestCase):
    def tof(self, sensor_id='tof-front', **changes):
        # Level mounting, so the geometry below is simple (the default tilts the sensor 13° up).
        suite = self.suite(self.definition(sensor_id, noise=0., **{'rotation': [0, 0, 0], **changes}))
        return suite, suite.sensors[sensor_id]

    def test_measures_a_wall_at_a_known_distance(self):
        suite, _ = self.tof()
        wall = self.box(.41, [.01, 1., .3])  # its near face is .40 m from the robot start, closer than the ground hit
        suite.refresh(0.)
        reading = suite.readings()['tof-front']
        json.dumps(reading)
        origin, direction = np.array(reading['origin']), np.array(reading['direction'])
        self.assertAlmostEqual(float(np.dot(direction, [*self.forward, 0.])), 1, places=4)
        expected = float(np.dot(self.ahead(.40) - origin, direction))
        self.assertAlmostEqual(reading['distance'], expected, delta=.005)
        self.assertTrue(reading['in_range'])
        self.assertEqual(reading['hit']['body'], wall)
        along = float(np.dot(np.array(reading['hit']['point']) - self.ahead(.40), [*self.forward, 0.]))
        self.assertAlmostEqual(along, 0, delta=.005)  # the hit point lies on the wall's face
        self.assertEqual(len(reading['rays']), 5)
        self.assertEqual(reading['type'], 'tof')

    def test_nothing_beyond_the_range(self):
        suite, _ = self.tof(rays=1)  # a single horizontal ray never reaches the ground
        self.box(3.0, [.01, 1., .3])
        suite.refresh(0.)
        reading = suite.readings()['tof-front']
        self.assertIsNone(reading['distance'])
        self.assertFalse(reading['in_range'])
        self.assertIsNone(reading['hit'])
        end = np.array(reading['rays'][0])
        self.assertAlmostEqual(float(np.linalg.norm(end - np.array(reading['origin']))), 2.0, delta=.001)

    def test_cone_rays_find_the_ground(self):
        suite, _ = self.tof()
        suite.refresh(0.)
        reading = suite.readings()['tof-front']
        half = math.radians(self.definition('tof-front')['cone'] / 2)
        self.assertAlmostEqual(reading['distance'], reading['origin'][2] / math.sin(half), delta=.005)
        self.assertEqual(reading['hit']['body'], self.ground)

    def test_noise_is_proportional_and_seeded(self):
        self.box(1.01, [.01, 1., .3])
        definition = self.definition('tof-front', rays=1, noise=.05)
        sensor = self.suite(definition, seed=3).sensors['tof-front']
        true = sensor.scan()['nearest'][2]
        samples = np.array([sensor.measure(0., None)['distance'] for _ in range(400)])
        self.assertAlmostEqual(float(samples.mean()), true, delta=.02)
        self.assertAlmostEqual(float(samples.std()), .05 * true, delta=.012)
        again = self.suite(definition, seed=3).sensors['tof-front']  # the same seed gives the same noise
        self.assertEqual([again.measure(0., None)['distance'] for _ in range(5)], samples[:5].tolist())

    def test_never_measures_its_own_robot(self):
        wall = self.box(1.0, [.01, 1., .3])
        height = frames.link_frame(self.client, self.robot.robot, -1)[0][2]
        # A sensor buried in the middle of the body, looking forward, back, left, right, down and up; with a single ray
        # and with a cone of rays.
        looking = {(0, 0, 0): wall, (0, 0, 180): None, (0, 0, 90): None, (0, 0, -90): None, (0, 90, 0): self.ground,
                   (0, -90, 0): None}
        for rotation, expected in looking.items():
            for rays in (1, 9):
                with self.subTest(rotation=rotation, rays=rays):
                    definition = {**self.definition('tof-front'), 'id': 'inside', 'name': 'Inside', 'noise': 0.,
                                  'position': [0, 0, 0], 'rotation': list(rotation), 'rays': rays}
                    sensor = self.suite(definition).sensors['inside']
                    scan, reading = sensor.scan(), sensor.measure(0., None)
                    self.assertTrue(scan['nearest'] is None or scan['nearest'][0] != self.robot.robot)
                    if reading['hit']:
                        self.assertIn(reading['hit']['body'], (wall, self.ground))
                    if rays == 1:
                        self.assertEqual(reading['hit'] and reading['hit']['body'], expected)
                    if rays == 1 and rotation == (0, 0, 0):
                        self.assertAlmostEqual(reading['distance'], float(np.dot(self.ahead(.99) - reading['origin'],
                                                                                 [*self.forward, 0.])), delta=.01)
                    if rays == 1 and rotation == (0, 90, 0):  # straight down through the legs to the ground
                        self.assertAlmostEqual(reading['distance'], height, delta=.02)
                    self.hub.unregister('inside')


    def test_looks_past_the_robot_when_it_is_in_the_way(self):
        wall = self.box(-.8, [.01, 1., .3])  # behind the robot
        # Mounted ahead of the robot and looking back at it: the ray enters the head or body first.
        definition = self.definition('tof-front', noise=0., rays=1, position=[.3, 0, .05], rotation=[0, 0, 180])
        sensor = self.suite(definition).sensors['tof-front']
        scan, reading = sensor.scan(), sensor.measure(0., None)
        self.assertGreater(scan['recast'], 0)
        self.assertEqual(reading['hit']['body'], wall)
        self.assertAlmostEqual(reading['distance'], .3 + .79, delta=.01)

    def test_gives_up_rather_than_report_the_robot(self):
        self.box(-.8, [.01, 1., .3])
        # At body height the ray crosses more than three of the robot's collision shapes: it is dropped.
        definition = self.definition('tof-front', noise=0., rays=1, position=[.3, 0, 0], rotation=[0, 0, 180])
        sensor = self.suite(definition).sensors['tof-front']
        scan = sensor.scan()
        self.assertEqual((scan['recast'], scan['blocked'], scan['nearest']), (3, 1, None))
        self.assertIsNone(sensor.measure(0., None)['distance'])
        self.assertFalse(next(c for c in sensor.self_test() if c['name'].startswith('No ray'))['ok'])


class ImuTest(SensorTestCase):
    def imu(self, **changes):
        suite = self.suite(self.definition('imu', **changes))
        return suite, suite.sensors['imu']

    def test_standing_still_reads_one_g_upwards(self):
        suite, _ = self.imu()
        self.simulate(1.0, suite)
        recent = [m['value']['linear_acceleration'] for m in self.hub.since(0, 'sensors/imu')][-50:]
        mean = np.mean(recent, axis=0)
        self.assertAlmostEqual(float(mean[2]), 9.81, delta=.3)
        self.assertLess(abs(float(mean[0])), .3)
        self.assertLess(abs(float(mean[1])), .3)
        reading = suite.readings()['imu']
        self.assertEqual(reading['type'], 'imu')
        self.assertAlmostEqual(math.degrees(reading['orientation'][0]), 0, delta=3)
        self.assertAlmostEqual(math.degrees(reading['orientation'][1]), 0, delta=3)
        self.assertLess(max(abs(v) for v in reading['angular_velocity']), .1)
        json.dumps(reading)

    def test_orientation_and_gravity_follow_the_body(self):
        suite, _ = self.imu()
        wanted = p.getQuaternionFromEuler([.3, -.2, .5])  # roll about forward, pitch about left, then yaw
        position = p.getBasePositionAndOrientation(self.robot.robot, physicsClientId=self.client)[0]
        base = frames.multiply(wanted, frames.inverse(self.robot.alignment))  # base link orientation giving that frame
        p.resetBasePositionAndOrientation(self.robot.robot, position, base, physicsClientId=self.client)
        suite.refresh(0.)
        reading = suite.readings()['imu']
        for value, truth in zip(reading['orientation'], (.3, -.2, .5)):
            self.assertAlmostEqual(value, truth, places=4)
        down = np.array(p.getMatrixFromQuaternion(wanted)).reshape(3, 3).T @ [0, 0, 9.81]
        for value, truth in zip(reading['linear_acceleration'], down):
            self.assertAlmostEqual(value, float(truth), places=3)

    def test_free_fall_reads_zero(self):
        suite, _ = self.imu()
        position, quaternion = p.getBasePositionAndOrientation(self.robot.robot, physicsClientId=self.client)
        p.resetBasePositionAndOrientation(self.robot.robot, [position[0], position[1], 5.], quaternion,
                                          physicsClientId=self.client)
        suite.refresh(0.)
        self.simulate(.2, suite)
        accel = suite.readings()['imu']['linear_acceleration']
        self.assertLess(math.sqrt(sum(v * v for v in accel)), .5)

    def test_noise_levels(self):
        suite, imu = self.imu(noise=.1)
        readings = [imu.measure(0., None) for _ in range(500)]
        gyro = np.array([r['angular_velocity'] for r in readings])
        accel = np.array([r['linear_acceleration'] for r in readings])
        self.assertAlmostEqual(float(gyro.std()), .1, delta=.015)
        self.assertAlmostEqual(float(accel[:, 0].std()), .981, delta=.15)
        self.assertAlmostEqual(float(accel[:, 2].mean()), 9.81, delta=.2)
        self.assertEqual(readings[0]['orientation'], readings[-1]['orientation'])  # orientation stays exact


class ScheduleTest(SensorTestCase):
    def test_rates_count_simulation_time(self):
        suite = self.suite(self.definition('head-cam', position=HEAD_CAMERA, width=32, height=24),
                           self.definition('tof-front'), self.definition('imu'))
        self.assertTrue(all(sensor.due(0.) for sensor in suite.sensors.values()))
        self.simulate(1.0, suite)
        count = lambda topic: len(self.hub.since(0, topic))
        self.assertEqual(count('sensors/tof-front'), 20)  # 20 Hz
        self.assertEqual(count('camera/head-cam'), 4)     # 4 Hz
        self.assertEqual(count('sensors/imu'), 100)       # 100 Hz, although physics runs at 240 Hz
        self.assertEqual(suite.sensors['head-cam'].reading['frame'], 4)
        times = [m['value']['time'] for m in self.hub.since(0, 'sensors/tof-front')]
        self.assertTrue(all(abs(b - a - .05) < .005 for a, b in zip(times, times[1:])))

    def test_refresh_ignores_the_rate_and_keeps_the_schedule(self):
        suite = self.suite(self.definition('tof-front'))
        sensor = suite.sensors['tof-front']
        suite.refresh(0.)
        due_at = sensor.next
        for _ in range(3):
            suite.refresh(0.)
        self.assertEqual(sensor.next, due_at)
        self.assertEqual(len(self.hub.since(0, 'sensors/tof-front')), 4)
        self.assertFalse(sensor.due(.01))
        self.assertTrue(sensor.due(due_at))
        suite.refresh(2.)  # later, and due: the schedule moves on from here
        self.assertTrue(sensor.due(1.))  # time went back (a reset): measure again at once
        suite.step(1., STEP)
        self.assertEqual(len(self.hub.since(0, 'sensors/tof-front')), 6)
        self.assertAlmostEqual(sensor.next, 1. + sensor.period)


class SuiteTest(SensorTestCase):
    def sane(self):
        definitions = copy.deepcopy(self.scenario['sensors'])
        next(d for d in definitions if d['id'] == 'head-cam')['position'] = HEAD_CAMERA
        return definitions

    def test_registers_and_removes_modules(self):
        definitions = self.sane()
        suite = self.suite(*definitions)
        ids = [d['id'] for d in definitions]
        self.assertEqual([m.id for m in self.hub.list('sensor')], ids)
        for definition in definitions:
            module = self.hub.module(definition['id'])
            self.assertEqual((module.name, module.kind), (definition['name'], 'sensor'))
            self.assertEqual(module.config(), definition)
            self.assertTrue(module.limitations)
        self.assertEqual(self.hub.module('head-cam').publishes, ('camera/head-cam',))
        self.assertEqual(self.hub.module('tof-left').describe()['publishes'], ['sensors/tof-left'])
        self.assertEqual(suite.describe(), [{**d, 'module': d['id']} for d in definitions])
        self.assertEqual(suite.readings(), {})
        suite.refresh(0.)
        self.assertEqual(list(suite.readings()), ids)
        for sensor_id, reading in suite.readings().items():
            self.assertTrue(set(reading) >= {'type', 'time', 'pose'}, sensor_id)
        self.assertIsNotNone(self.hub.frame('head-cam'))
        suite.remove()
        self.assertEqual(self.hub.modules(), [])
        self.assertIsNone(self.hub.frame('head-cam'))

    def test_bad_definitions_name_the_sensor(self):
        with self.assertRaisesRegex(ValueError, 'Head camera'):
            self.suite(self.definition('head-cam', link='no-such-link'))
        with self.assertRaisesRegex(ValueError, 'ToF left'):
            self.suite(self.definition('imu'), self.definition('tof-left', link='nope'))
        self.assertEqual(self.hub.modules(), [])  # nothing registered by a failed build
        for reserved in ('robot', 'world'):
            with self.assertRaisesRegex(ValueError, 'Body IMU'):
                self.suite(self.definition('imu', id=reserved))
        with self.assertRaisesRegex(ValueError, 'lower-case'):
            self.suite(self.definition('imu', id='Body-IMU'))
        with self.assertRaisesRegex(ValueError, 'twice'):
            self.suite(self.definition('imu'), self.definition('imu'))
        self.assertEqual(self.hub.modules(), [])

    def test_every_self_test_passes_in_a_sane_setup(self):
        self.box(.9, [.01, 1., .3])
        suite = self.suite(*self.sane())
        self.simulate(.5, suite)
        results = self.hub.run_all_tests()
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertTrue(result['ok'], result)
            self.assertGreaterEqual(len(result['checks']), 2)
        camera = next(r for r in results if r['module'] == 'head-cam')
        self.assertIn('ms for 160x120', camera['checks'][0]['detail'])
        self.assertEqual(self.hub.latest('hub/self-test')['hub/self-test']['value']['module'], results[-1]['module'])

    def test_a_failing_sensor_does_not_stop_the_others(self):
        suite = self.suite(self.definition('imu'), self.definition('tof-front'))
        broken = suite.sensors['tof-front']
        broken.measure = lambda time, dt: 1 / 0
        suite.step(0., STEP)
        self.assertEqual(broken.status(), 'error')
        self.assertIn('ZeroDivisionError', broken.error)
        self.assertEqual(self.hub.modules()[1]['status'], 'error')
        self.assertEqual(list(suite.readings()), ['imu'])
        self.assertFalse(broken.due(.01))  # not retried at every step
        del broken.measure
        suite.step(.06, STEP)
        self.assertEqual((broken.status(), broken.error), ('ok', None))
        self.assertEqual(list(suite.readings()), ['imu', 'tof-front'])

    def test_a_tof_far_from_its_link_fails_its_self_test(self):
        self.suite(self.definition('tof-front', position=[.4, 0, 0]))
        result = self.hub.run_test('tof-front')
        self.assertFalse(result['ok'])
        failed = [c['name'] for c in result['checks'] if not c['ok']]
        self.assertEqual(failed, ['Ray origin is on the link it is mounted on'])


class FakeHub(BaseHTTPRequestHandler):
    """Just enough of the coordinator's /api/hub routes to check what HubClient sends and how it reads answers."""
    calls = []

    def log_message(self, *args):
        pass

    def answer(self, status, body, kind='application/json'):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_any(self):
        length = int(self.headers.get('Content-Length') or 0)
        body = json.loads(self.rfile.read(length)) if length else None
        self.calls.append((self.command, self.path, body))
        path = self.path.split('?')[0]
        if path == '/api/hub/register':
            return self.answer(200, {**body, 'status': 'ok'})
        if path.endswith('/heartbeat'):
            return self.answer(200, {'id': path.split('/')[-2]})
        if path == '/api/hub/publish':
            return self.answer(200, {'seq': 7, 'topic': body['topic'], 'source': body['module'], 'time': 0.,
                                     'value': body['value']})
        if path == '/api/hub/topics':
            return self.answer(200, {'camera/head-cam': {'seq': 1, 'value': {'frame': 3}}})
        if path == '/api/hub/frame/head-cam.png':
            return self.answer(200, png.encode(np.zeros((2, 2), np.uint8)), 'image/png')
        if path.startswith('/api/hub/frame/'):
            return self.answer(404, {'detail': 'No frame yet from that camera'})
        if path == '/api/hub/modules':
            return self.answer(200, [{'id': 'imu'}])
        if path == '/api/hub/stream':
            # a comment, one event, and one event split over two data lines
            events = (b': hello\n\ndata: {"seq": 1, "topic": "a/b"}\n\n'
                      b'id: 2\ndata: {"seq": 2,\ndata: "topic": "a/c"}\n\n')
            return self.answer(200, events, 'text/event-stream')
        if self.command == 'DELETE':
            return self.answer(200, {'removed': path.split('/')[-1]})
        self.answer(422, {'detail': [{'msg': 'bad request'}]})

    do_GET = do_POST = do_DELETE = handle_any


class HubClientTest(unittest.TestCase):
    def setUp(self):
        FakeHub.calls = []
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), FakeHub)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f'http://127.0.0.1:{self.server.server_address[1]}'
        self.client = HubClient('detector', 'Detector', kind='detector', publishes=['vision/detections'],
                                subscribes=['camera/head-cam'], limitations=['Toy'], info={'v': 1},
                                base_url=self.url + '/')

    def tearDown(self):
        self.client.close()
        self.server.shutdown()
        self.server.server_close()

    def test_calls_match_the_api(self):
        c = self.client
        description = c.register()
        self.assertEqual(description['id'], 'detector')
        self.assertEqual(FakeHub.calls[-1], ('POST', '/api/hub/register', {
            'id': 'detector', 'name': 'Detector', 'kind': 'detector', 'publishes': ['vision/detections'],
            'subscribes': ['camera/head-cam'], 'limitations': ['Toy'], 'info': {'v': 1}}))
        c.heartbeat()
        self.assertEqual(FakeHub.calls[-1][:2], ('POST', '/api/hub/modules/detector/heartbeat'))
        message = c.publish('vision/detections', {'fox': .5})
        self.assertEqual(FakeHub.calls[-1], ('POST', '/api/hub/publish', {
            'module': 'detector', 'topic': 'vision/detections', 'value': {'fox': .5}}))
        self.assertEqual(message['seq'], 7)
        self.assertEqual(c.latest('camera/')['camera/head-cam']['value']['frame'], 3)
        self.assertEqual(FakeHub.calls[-1][1], '/api/hub/topics?prefix=camera%2F')
        self.assertTrue(c.frame('head-cam').startswith(b'\x89PNG'))
        self.assertEqual(c.modules(), [{'id': 'imu'}])

    def test_errors_carry_the_servers_detail(self):
        with self.assertRaisesRegex(HubError, 'No frame yet from that camera') as caught:
            self.client.frame('nope')
        self.assertEqual(caught.exception.status, 404)
        with self.assertRaisesRegex(HubError, 'bad request'):
            self.client.request('GET', '/api/hub/unknown')
        dead = HubClient('x', 'X', base_url='http://127.0.0.1:1')
        with self.assertRaisesRegex(HubError, 'Cannot reach.*running') as caught:
            dead.modules()
        self.assertIsNone(caught.exception.status)
        dead.close()  # unregistering a hub that is gone is not an error

    def test_stream_yields_message_dicts(self):
        messages = list(self.client.stream('a/', since=0))
        self.assertEqual([m['seq'] for m in messages], [1, 2])
        self.assertEqual(messages[1]['topic'], 'a/c')
        self.assertEqual(FakeHub.calls[-1][1], '/api/hub/stream?prefix=a%2F&since=0')

    def test_heartbeat_thread_and_close(self):
        self.client.register()
        self.client.start_heartbeat(interval=.05)
        self.client.start_heartbeat(interval=.05)  # a second call does not start a second thread
        thread = self.client.thread
        self.assertTrue(thread.daemon)
        threading.Event().wait(.4)
        beats = [c for c in FakeHub.calls if c[1].endswith('/heartbeat')]
        self.assertGreaterEqual(len(beats), 3)
        self.client.close()
        self.assertFalse(thread.is_alive())
        self.assertEqual(FakeHub.calls[-1][:2], ('DELETE', '/api/hub/modules/detector'))
        settled = len(FakeHub.calls)
        threading.Event().wait(.2)
        self.assertEqual(len(FakeHub.calls), settled)


if __name__ == '__main__':
    unittest.main()
