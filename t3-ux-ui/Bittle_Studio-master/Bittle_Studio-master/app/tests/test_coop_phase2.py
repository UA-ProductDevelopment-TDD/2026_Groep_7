"""Phase 2 and 3: crab legs, animals and visitors, the detector at day and night, the behaviour (patrol, alarm,
deterring, docking), battery, metrics, batch experiments and their API."""
import math
import time
import unittest

import numpy as np
import pybullet as p
from fastapi.testclient import TestClient

import coop_server
from coop import config, experiments, gaits, legs, png
from coop.actors import Actors
from coop.detector import Detector, colour_blobs
from coop.energy import Battery
from coop.hub import Hub
from coop.jobs import Jobs
from coop.metrics import fence_points, visible_points
from coop.patrol import Route
from coop.robot import CoopRobot
from coop.session import CoopSession
from coop.world import World
from tests.test_coop_legs import flat_world, robot_settings
from tests.test_coop_sensors import SensorTestCase

FOX, FENCE, HOUSE, JACKET = (.83, .4, .11, 1), (.73, .76, .78, 1), (.78, .64, .42, 1), (.18, .37, .66, 1)


def quiet(scenario, **sections):
    """A default scenario without animals or visitors unless given, with sections replaced."""
    scenario['chickens'] = {**scenario['chickens'], 'inside': 0, 'outside': 0}
    scenario['visitors'] = []
    scenario.update(sections)
    return scenario


class CrabLegsTest(unittest.TestCase):
    def setUp(self):
        self.client = flat_world()

    def tearDown(self):
        p.disconnect(self.client)

    def test_front_knees_point_forward_and_rear_knees_backward(self):
        settings = robot_settings('crab')
        robot = CoopRobot(self.client, settings)
        stance = gaits.plan(robot, settings['gait'], 'stance')['segments'][0][1]
        preview = gaits.preview(robot, settings['gait'], 'stance')
        self.assertEqual(preview['knees'], {'left-front': 'forward', 'right-front': 'forward',
                                            'left-back': 'backward', 'right-back': 'backward'})
        robot.pose(stance)
        feet = gaits.foot_positions(robot)
        for leg, drawn in preview['frames'][0]['legs'].items():
            hip, knee, foot = drawn['hip'], drawn['knee_point'], drawn['foot']
            # The knee lies ahead of (front legs) or behind (rear legs) the line from shoulder to foot.
            t = (knee[1] - hip[1]) / (foot[1] - hip[1])
            ahead = knee[0] - (hip[0] + t * (foot[0] - hip[0]))
            self.assertGreater(ahead if 'front' in leg else -ahead, .03, leg)
            self.assertAlmostEqual(foot[0], feet[leg][0], delta=.001, msg=leg)  # the drawing is where Bullet has it
            self.assertAlmostEqual(foot[1], feet[leg][2], delta=.001, msg=leg)
        # A mirrored knee folds the other way: its limits swap sides.
        stock = {j['name']: (j['lower'], j['upper']) for j in CoopRobot(self.client, robot_settings('stock')).joints}
        crab = {j['name']: (j['lower'], j['upper']) for j in robot.joints}
        lower, upper = stock['left-front-knee-joint']
        for got, want in zip(crab['left-front-knee-joint'], (-upper, -lower)):
            self.assertAlmostEqual(got, want, delta=1e-3)
        self.assertEqual(crab['left-back-knee-joint'], stock['left-back-knee-joint'])

    def test_fan_turns_the_swing_planes_outward(self):
        robot = CoopRobot(self.client, robot_settings('crab', legs={**config.LEG_PRESETS['crab']['legs'], 'fan': 30}))
        for leg, g in robot.gait_legs.items():
            # The swing plane's forward direction points outward: left legs to +y, right legs to -y, rear legs mirrored.
            outward = (1 if leg.startswith('left') else -1) * (1 if 'front' in leg else -1)
            # (a little under 30°: the plane also leans out by the splay, which tilts its level direction)
            self.assertAlmostEqual(math.degrees(math.atan2(g['forward'][1], g['forward'][0])) * outward, 28, delta=2,
                                   msg=leg)
        pose, unreachable = gaits.frame(robot.gait_legs, robot.settings['gait'], 'forward', .3)
        self.assertEqual(unreachable, [])
        self.assertFalse(legs.is_stock({**config.STOCK_LEGS, 'fan': 10}))
        self.assertFalse(legs.is_stock({**config.STOCK_LEGS, 'front_knees': 'forward'}))

    def test_crab_foot_lifts_straight_up_and_sets_down_straight(self):
        gait = config.LEG_PRESETS['crab']['gait']
        duty, stride = gaits.DUTY['crab'], gait['stride']
        lift = duty + (1 - duty) * gaits.LIFT / 2          # halfway through lifting
        forward, up = gaits.foot_path(gait, lift, stride)
        self.assertAlmostEqual(forward, -stride / 2, delta=1e-9)  # still above the spot where it left the ground
        self.assertGreater(up, gait['step_height'] / 3)
        top = gaits.foot_path(gait, duty + (1 - duty) / 2, stride)
        self.assertAlmostEqual(top[1], gait['step_height'], delta=1e-9)
        setting = gaits.foot_path(gait, 1 - (1 - duty) * gaits.LIFT / 2, stride)
        self.assertAlmostEqual(setting[0], stride / 2, delta=1e-9)

    def test_crab_walks_and_turns_on_level_ground(self):
        settings = robot_settings('crab')
        robot = CoopRobot(self.client, settings)
        robot.place([0, 0], 0)
        robot.running = True
        for motion, check in (('forward', lambda a, b: b['position'][0] - a['position'][0] > .25),
                              ('spin-left', lambda a, b: (b['heading'] - a['heading']) % 360 > 20)):
            robot.play_skill(gaits.plan(robot, settings['gait'], motion))
            before = robot.body_state()
            for _ in range(240 * 7):
                robot.advance_skill(1 / 240)
                robot.drive_motors()
                p.stepSimulation(physicsClientId=self.client)
            after = robot.body_state()
            self.assertFalse(after['fallen'], motion)
            self.assertTrue(check(before, after), motion)


class ActorsTest(unittest.TestCase):
    def setUp(self):
        self.client = p.connect(p.DIRECT)
        self.scenario = config.validate(config.default())
        self.world = World(self.client, self.scenario)
        self.actors = Actors(self.client, self.scenario, self.world)

    def tearDown(self):
        p.disconnect(self.client)

    def run_for(self, seconds, robot=None, start=0.):
        t = start
        for _ in range(round(seconds * 60)):
            t += 1 / 60
            self.actors.step(t, 1 / 60, robot(self.actors) if robot else None)
        return t

    def test_bodies_kinds_and_visitors_hidden_until_they_appear(self):
        kinds = sorted(info['kind'] for info in self.actors.bodies.values())
        self.assertEqual(kinds, ['chicken'] * 6 + ['fox', 'person'])
        fox = next(b for b, info in self.actors.bodies.items() if info['kind'] == 'fox')
        self.assertLess(p.getBasePositionAndOrientation(fox, physicsClientId=self.client)[0][2], -50)
        scene = self.actors.scene()
        self.assertEqual({part['color'] for a in scene['actors'] if a['kind'] == 'fox' for part in a['parts']},
                         {'#d4661c', '#3a2a20', '#f4f1ea'})
        self.assertEqual(len(scene['paths']), 2)
        self.run_for(41)
        self.assertTrue(self.actors.fox()['present'])
        self.assertGreater(p.getBasePositionAndOrientation(fox, physicsClientId=self.client)[0][2], -1)
        self.assertTrue(any('Fox appeared' in text for _, text in self.actors.pop_events()))

    def test_fox_runs_from_a_deterring_robot_and_reset_repeats_everything(self):
        t = self.run_for(45)
        fox = next(s for s in self.actors.states() if s['kind'] == 'fox')
        near = {'position': [fox['position'][0] + .5, fox['position'][1], 0], 'heading': 0, 'deterring': True}
        self.run_for(30, lambda actors: near, t)
        record = self.actors.fox()
        self.assertIsNotNone(record['fled_at'])
        self.assertEqual(record['mode'], 'gone')
        before = self.actors.states()
        self.actors.reset()
        self.run_for(10)
        again = self.actors.states()
        self.actors.reset()
        self.run_for(10)
        self.assertEqual(again, self.actors.states())
        self.assertNotEqual(before, again)

    def test_the_robot_is_never_pushed_but_rays_and_the_self_test_see_them(self):
        result = self.actors.self_test()
        self.assertTrue(all(c['ok'] for c in result), [c for c in result if not c['ok']])
        chicken = next(b for b, info in self.actors.bodies.items() if info['kind'] == 'chicken')
        where = p.getBasePositionAndOrientation(chicken, physicsClientId=self.client)[0]
        box = p.createMultiBody(1, p.createCollisionShape(p.GEOM_BOX, halfExtents=[.1, .1, .1],
                                                          physicsClientId=self.client),
                                basePosition=[where[0], where[1], where[2] + .1], physicsClientId=self.client)
        self.actors.ignore_collisions_with(box)
        p.stepSimulation(physicsClientId=self.client)
        self.assertEqual(p.getContactPoints(box, chicken, physicsClientId=self.client), ())
        hit = p.rayTest([where[0], where[1], where[2] + 1], [where[0], where[1], where[2] - .1],
                        physicsClientId=self.client)
        self.assertEqual(hit[0][0], box)  # the box sits around the chicken: the ray meets it first ...
        p.removeBody(box, physicsClientId=self.client)
        hit = p.rayTest([where[0], where[1], where[2] + 1], [where[0], where[1], where[2] - .1],
                        physicsClientId=self.client)
        self.assertEqual(hit[0][0], chicken)  # ... and without it the chicken: rays still see actors


class DetectorTest(SensorTestCase):
    def detector(self, kind='ground-truth', environment=None, labels=None, **settings):
        camera = self.definition('head-cam')
        suite = self.suite(camera, environment=environment)
        detector = Detector(self.hub, {**config.validate(config.default())['detector'], 'type': kind, **settings},
                            suite.sensors.get, lambda: labels or {})
        return suite, detector

    def look(self, suite, detector):
        self.time += .25
        suite.refresh(self.time)
        detector.update(self.time)
        return detector.latest(self.time)

    def test_ground_truth_finds_a_fox_with_its_bearing_and_distance(self):
        fox = self.box(1.2, [.2, .07, .16], FOX, side=.25)
        suite, detector = self.detector(labels={fox: 'fox'})
        result = self.look(suite, detector)
        self.assertEqual([o['label'] for o in result['objects']], ['fox'])
        found = result['objects'][0]
        self.assertGreater(found['bearing'], 5)               # to the left of the image centre
        self.assertAlmostEqual(found['distance'], .9, delta=.1)  # the near face, seen from the head camera
        self.assertEqual(detector.truth()['objects']['fox']['lit_pixels'], found['pixels'])
        topic = self.hub.latest('detections/')
        self.assertIn('detections/head-cam', topic)

    def test_at_night_only_the_infrared_light_shows_the_fox(self):
        night = {**config.validate(config.default())['environment'], 'time_of_day': 'night', 'ir_light': False}
        fox = self.box(1.5, [.2, .07, .16], FOX)
        labels = {fox: 'fox'}
        suite, detector = self.detector(environment=night, labels=labels)
        self.assertEqual(self.look(suite, detector)['objects'], [])
        self.assertEqual(self.look(suite, detector)['lighting'], 'night')
        suite.set_environment({**night, 'ir_light': True})
        found = self.look(suite, detector)
        self.assertEqual([o['label'] for o in found['objects']], ['fox'])
        self.assertEqual(found['lighting'], 'night-ir')
        p.resetBasePositionAndOrientation(fox, (self.ahead(4.6)[0], self.ahead(4.6)[1], .16), (0, 0, 0, 1),
                                          physicsClientId=self.client)
        self.assertEqual(self.look(suite, detector)['objects'], [])  # far beyond the infrared range

    def test_colour_blobs_find_the_fox_but_not_fence_or_house(self):
        self.box(1.0, [.2, .07, .16], FOX)
        self.box(1.6, [.02, .5, .3], FENCE, side=.6)
        self.box(1.8, [.3, .3, .3], HOUSE, side=-.7)
        suite, detector = self.detector('colour-blob')
        labels = [o['label'] for o in self.look(suite, detector)['objects']]
        self.assertIn('fox', labels)
        self.assertNotIn('chicken', labels)
        self.assertEqual(labels.count('fox'), 1)
        picture = np.zeros((20, 30, 3), np.uint8)
        picture[5:15, 5:15] = (127, 61, 16)
        self.assertEqual([o['label'] for o in colour_blobs(picture, 20)], ['fox'])

    def test_outside_detections_are_checked_and_go_stale(self):
        suite, detector = self.detector('external', stale=2.)
        self.time = 10.
        self.hub.clock = lambda: self.time
        self.hub.publish('detections/external', {'frame': 3, 'objects': [
            {'label': 'fox', 'confidence': .8, 'bbox': [10, 20, 40, 50]}, {'label': 'wolf', 'confidence': 1,
                                                                          'bbox': [0, 0, 1, 1]}]}, 'ai-camera')
        result = detector.latest(11.)
        self.assertEqual([o['label'] for o in result['objects']], ['fox'])
        self.assertGreater(result['objects'][0]['bearing'], 0)  # a box left of the centre
        self.assertEqual(detector.skipped, 1)
        self.assertIsNone(detector.latest(12.5))
        self.assertEqual(detector.status(), 'waiting')

    def test_png_round_trip(self):
        image = np.random.default_rng(3).integers(0, 256, (9, 13, 3), dtype=np.uint8)
        self.assertTrue((png.decode(png.encode(image)) == image).all())


def session_for(scenario):
    return CoopSession(config.validate(scenario))


def run(session, seconds, until=None):
    for _ in range(round(seconds * 240)):
        session.tick()
        if until and until(session):
            break


class BehaviourTest(unittest.TestCase):
    def test_the_fox_raises_the_alarm_and_is_chased_off(self):
        scenario = quiet(config.default())
        scenario['visitors'] = [{'id': 'fox', 'kind': 'fox', 'name': 'Fox', 'appear': .5, 'speed': .1, 'loop': True,
                                 'flee_distance': 1.0, 'path': [[1.6, -1.45], [1.3, -1.45]]}]
        session = session_for(scenario)
        try:
            session.command({'action': 'mission', 'value': True})
            run(session, 25, lambda s: s.actors.fox()['fled_at'] is not None)
            metrics = session.metrics.summary()
            self.assertEqual(metrics['alarms']['true'], 1)
            self.assertEqual(metrics['alarms']['false'], 0)
            self.assertLess(metrics['fox']['time_to_alarm_s'], 3)
            self.assertIsNotNone(metrics['fox']['fled_at'])
            self.assertEqual(session.behaviour.state, 'deter')
            self.assertTrue(session.behaviour.deterring)
            texts = [e['text'] for e in session.events]
            self.assertIn('ALARM: fox', texts)
        finally:
            session.close()

    def test_docking_latches_and_charging_fills_the_battery(self):
        scenario = quiet(config.default())
        dock = scenario['dock']
        scenario['robot']['start'] = {'position': [dock['position'][0] - .3, dock['position'][1] + .6], 'heading': 0.}
        scenario['energy'] = {**scenario['energy'], 'start_charge': .25, 'charge_power': 400.}
        scenario['behaviour'] = {**scenario['behaviour'], 'resume_battery': .5}
        session = session_for(scenario)
        try:
            session.command({'action': 'mission', 'value': True})
            run(session, 1)
            self.assertEqual(session.behaviour.state, 'return')  # 25 % is below the low battery level
            run(session, 90, lambda s: s.behaviour.state == 'undock')
            docking = session.metrics.summary()['docking']
            self.assertEqual(docking['successes'], 1, session.events)
            self.assertLessEqual(abs(docking['list'][0]['lateral']), dock['capture_distance'])
            self.assertGreaterEqual(session.battery.state_of_charge(), .5)
            self.assertEqual(session.behaviour.state, 'undock')
        finally:
            session.close()

    def test_an_obstacle_in_front_stops_the_patrol(self):
        session = session_for(quiet(config.default()))
        try:
            start = session.scenario['robot']['start']['position']
            shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=[.03, .2, .15], physicsClientId=session.client)
            p.createMultiBody(0, shape, basePosition=[start[0] + .19, start[1], .15], physicsClientId=session.client)
            session.command({'action': 'mission', 'value': True})
            run(session, 2.5)
            self.assertEqual(session.metrics.obstacle_stops, 1)
            self.assertLess(session.robot.body_state()['position'][0] - start[0], .05)
            self.assertEqual(session.behaviour.navigator.motion, 'stance')
        finally:
            session.close()

    def test_manual_driving_stops_the_mission_and_reset_restores_everything(self):
        session = session_for(quiet(config.default()))
        try:
            session.command({'action': 'mission', 'value': True})
            run(session, 1)
            self.assertEqual(session.behaviour.state, 'patrol')
            session.command({'action': 'drive', 'value': 'stand'})
            self.assertEqual(session.behaviour.state, 'off')
            used = session.battery.used
            self.assertGreater(used, 0)
            session.reset()
            self.assertEqual((session.battery.used, session.metrics.summary()['distance_m']), (0, 0))
            self.assertTrue(all(r['ok'] for r in session.run_test()), [
                (r['module'], [c for c in r['checks'] if not c['ok']]) for r in session.run_test() if not r['ok']])
        finally:
            session.close()


class PartsTest(unittest.TestCase):
    def test_route_positions_and_laps(self):
        route = Route([[0, 0], [2, 0], [2, 1], [0, 1]])
        self.assertEqual(route.length, 6)
        self.assertEqual(list(route.at(2.5)), [2, .5])
        self.assertEqual(list(route.at(6.5)), [.5, 0])
        position, distance = route.project([1, -.2])
        self.assertAlmostEqual(position, 1)
        self.assertAlmostEqual(distance, .2)
        position, _ = route.project([.1, .05], near=5.9)  # just past the start: arc length keeps counting
        self.assertAlmostEqual(position, 6.1)

    def test_battery_draws_more_under_load_and_charges(self):
        settings = config.validate(config.default())
        battery = Battery(settings['energy'], settings['environment'], 9)
        idle = battery.drain(3600, [0.] * 9, .29)
        self.assertAlmostEqual(idle, 1.5 + 9 * 7.4 * .01)
        self.assertAlmostEqual(battery.state_of_charge(), 1 - idle / 7.4)
        loaded = battery.drain(3600, [.29] * 9, .29)
        self.assertAlmostEqual(loaded, 1.5 + 9 * 7.4 * 1.01)
        self.assertTrue(battery.empty())
        battery.charge_for(3600)
        self.assertAlmostEqual(battery.charge, 7.0)
        night = {**settings['environment'], 'time_of_day': 'night'}
        self.assertAlmostEqual(Battery(settings['energy'], night, 9).base_power(), 2.5)

    def test_coverage_sees_fence_points_in_front_of_the_camera(self):
        coop = config.default()['coop']
        points = fence_points(coop)
        self.assertEqual(len(points), 40)
        # A camera 1 m south of the fence's middle, looking north at a flat wall standing where the fence is.
        depth = np.full((120, 160), 1.03, np.float32)
        shot = {'position': [0, -2.0, .3], 'quaternion': list(p.getQuaternionFromEuler([0, 0, math.pi / 2])),
                'depth': depth, 'brightness': np.ones((120, 160), np.float32)}
        seen = visible_points(points, shot, {'fov': 60, 'range': 5}, .15)
        xs = sorted(points[i][0] for i in seen)
        self.assertTrue(seen)
        self.assertTrue(all(abs(points[i][1] + 1.03) < 1e-6 for i in seen))  # only the south side
        self.assertLess(xs[-1] - xs[0], 1.8)                                 # within the field of view
        shot['brightness'][:] = 0
        self.assertEqual(visible_points(points, shot, {'fov': 60, 'range': 5}, .15), [])

    def test_experiment_plan_and_table(self):
        scenario = config.validate(config.default())
        runs, seconds = experiments.plan(scenario, [{'name': 'Stock'}, {'name': 'Crab', 'changes': {
            'robot': config.LEG_PRESETS['crab'], 'dock': {'stop_distance': .19}}}], 2, 60)
        self.assertEqual(len(runs), 4)
        self.assertNotEqual(runs[0]['scenario']['terrain']['seed'], runs[1]['scenario']['terrain']['seed'])
        self.assertEqual(runs[2]['scenario']['robot']['legs']['front_knees'], 'forward')
        self.assertEqual(runs[2]['scenario']['dock']['capture_distance'], .03)  # merged, not replaced
        with self.assertRaisesRegex(ValueError, 'Broken: leg splay'):
            experiments.plan(scenario, [{'name': 'Broken', 'changes': {'robot': {'legs': {'splay': 90}}}}], 1, 60)
        fake = {'variant': 'Stock', 'seed': 0, 'seconds': 60, 'final_state': 'patrol', 'battery_end': .9,
                'metrics': {'distance_m': 2.0, 'laps': 0, 'falls': 1, 'fox': {'fled_at': 40.}, 'energy': {'used_wh': .1}}}
        job = {'runs': [{'label': 'a', 'status': 'done'}, {'label': 'b', 'status': 'done'},
                        {'label': 'c', 'status': 'error', 'error': 'boom'}], 'info': {'variants': ['Stock']}}
        result = experiments.summarise(job, [fake, {**fake, 'seed': 1, 'metrics': {**fake['metrics'], 'falls': 3}},
                                             None])
        row = result['table'][0]
        self.assertEqual((row['runs'], row['falls']['mean'], row['fox_fled']['mean']), (2, 2, 1))
        self.assertEqual(result['failures'], [{'label': 'c', 'error': 'boom'}])
        self.assertEqual(len(experiments.to_csv(result).strip().splitlines()), 3)


class JobsTest(unittest.TestCase):
    def test_a_mission_runs_in_a_worker_process(self):
        jobs = Jobs(workers=1)
        try:
            scenario = config.validate(quiet(config.default()))
            planned, seconds = experiments.plan(scenario, [{'name': 'Quiet'}], 1, 10)
            job_id = jobs.submit('experiment', 'test', [('quiet', experiments.run_mission,
                                                         (planned[0]['scenario'], seconds, 'Quiet', 0))],
                                 experiments.summarise, {'variants': ['Quiet']})
            deadline = time.time() + 180
            while jobs.get(job_id)['status'] == 'running' and time.time() < deadline:
                time.sleep(.5)
            job = jobs.get(job_id)
            self.assertEqual(job['status'], 'done', job)
            self.assertEqual(job['progress'], 1)
            row = job['result']['table'][0]
            self.assertEqual(row['runs'], 1)
            self.assertGreater(row['distance_m']['mean'], .1)
            self.assertAlmostEqual(job['result']['runs'][0]['seconds'], 10, delta=.1)
        finally:
            jobs.close()


class Phase2ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(coop_server.app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def setUp(self):
        self.client.put('/api/coop/scenario', json=config.default()).raise_for_status()

    def test_mission_state_preview_and_metrics(self):
        c = self.client
        model = c.get('/api/coop/model').json()
        self.assertEqual(len(model['actors']['actors']), 8)
        self.assertIn('crab', model['gait_types'])
        self.assertEqual(model['choices']['knee_directions'], ['backward', 'forward'])
        state = c.post('/api/coop/command', json={'action': 'mission', 'value': True}).json()
        self.assertEqual(state['behaviour']['state'], 'patrol')
        self.assertTrue(state['running'])
        for key in ('battery', 'actors', 'metrics'):
            self.assertIn(key, state)
        state = c.post('/api/coop/command', json={'action': 'mission', 'value': False}).json()
        self.assertEqual(state['behaviour']['state'], 'off')
        preview = c.get('/api/coop/gait-preview', params={'motion': 'forward'}).json()
        self.assertEqual(len(preview['frames']), round(config.default()['robot']['gait']['cycle'] / gaits.FRAME_S))
        self.assertEqual(c.get('/api/coop/gait-preview', params={'motion': 'moonwalk'}).status_code, 400)
        self.assertIn('metrics', c.get('/api/coop/metrics').json())
        night = config.default()
        night['environment']['time_of_day'] = 'night'
        session = coop_server.session
        world = session.world
        c.put('/api/coop/scenario', json=night).raise_for_status()
        self.assertIs(session.world, world)  # night needs no rebuild
        c.post('/api/coop/command', json={'action': 'refresh-sensors'}).raise_for_status()
        self.assertEqual(c.get('/api/coop/state').json()['sensors']['head-cam']['lighting'], 'night-ir')

    def test_traverse_and_experiment_jobs(self):
        c = self.client
        job = c.post('/api/coop/jobs/traverse', json={'seconds': 5}).json()['job']
        experiment = c.post('/api/coop/jobs/experiment', json={'variants': [{'name': 'Default'}], 'seeds': 1,
                                                               'seconds': 10}).json()['job']
        self.assertEqual(c.post('/api/coop/jobs/experiment', json={'variants': [], 'seeds': 1}).status_code, 400)
        deadline = time.time() + 240
        while time.time() < deadline and any(c.get(f'/api/coop/jobs/{j}').json()['status'] == 'running'
                                             for j in (job, experiment)):
            time.sleep(.5)
        traverse = c.get(f'/api/coop/jobs/{job}').json()
        self.assertEqual(traverse['status'], 'done', traverse)
        self.assertEqual(len(traverse['result']['runs']), 4)
        self.assertIn('tests/traverse', c.get('/api/hub/topics', params={'prefix': 'tests/'}).json())
        done = c.get(f'/api/coop/jobs/{experiment}').json()
        self.assertEqual(done['status'], 'done', done)
        csv = c.get(f'/api/coop/jobs/{experiment}/csv')
        self.assertEqual(csv.status_code, 200)
        self.assertIn('Distance walked (m)', csv.text)
        self.assertEqual(c.get(f'/api/coop/jobs/{job}/csv').status_code, 400)
        self.assertTrue(any(j['id'] == experiment for j in c.get('/api/coop/jobs').json()))


if __name__ == '__main__':
    unittest.main()
