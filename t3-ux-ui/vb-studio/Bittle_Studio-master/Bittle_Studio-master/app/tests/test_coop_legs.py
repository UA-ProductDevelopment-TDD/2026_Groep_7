"""Leg designs, generated gaits, servo limits and the traverse test."""
import math
import unittest

import numpy as np
import pybullet as p
from fastapi.testclient import TestClient

import coop_server
from coop import config, gaits, legs, traverse
from coop.robot import CoopRobot


def flat_world():
    client = p.connect(p.DIRECT)
    p.setGravity(0, 0, -9.81, physicsClientId=client)
    p.setTimeStep(1 / 240, physicsClientId=client)
    p.setPhysicsEngineParameter(numSolverIterations=80, physicsClientId=client)
    plane = p.createMultiBody(0, p.createCollisionShape(p.GEOM_PLANE, physicsClientId=client), physicsClientId=client)
    p.changeDynamics(plane, -1, lateralFriction=1.0, physicsClientId=client)
    return client


def robot_settings(preset, **changes):
    scenario = config.default()
    scenario['robot'].update(config.LEG_PRESETS[preset])
    scenario['robot'].update(changes)
    return config.validate(scenario)['robot']


class LegDesignTest(unittest.TestCase):
    def setUp(self):
        self.client = flat_world()

    def tearDown(self):
        p.disconnect(self.client)

    def test_stock_lengths_are_measured_from_the_model(self):
        for name, leg in legs.stock().items():
            self.assertAlmostEqual(leg['upper'], .0495, delta=.001, msg=name)
            self.assertAlmostEqual(leg['lower'], .0545, delta=.0015, msg=name)
        stock = config.validate(config.default())['robot']['legs']
        self.assertTrue(legs.is_stock(stock))
        self.assertEqual(legs.generate(stock), legs.BITTLE / 'bittle.urdf')
        self.assertFalse(legs.is_stock({**stock, 'splay': 5}))

    def test_spider_is_built_as_designed(self):
        stock = CoopRobot(self.client, robot_settings('stock'))
        spider = CoopRobot(self.client, robot_settings('spider'))
        design = config.LEG_PRESETS['spider']['legs']
        self.assertTrue(legs.generate(design).is_file())
        for leg in gaits.LEGS:
            built, before = spider.gait_legs[leg], stock.gait_legs[leg]
            self.assertAlmostEqual(built['upper'], design['upper'], delta=.001, msg=leg)
            self.assertAlmostEqual(built['lower'], design['lower'], delta=.001, msg=leg)
            shift = design['front_offset'] if 'front' in leg else 0
            self.assertAlmostEqual(built['hip'][0] - before['hip'][0], shift, delta=.001, msg=leg)
            # The leg swings in a plane tilted outward by the splay: its "across" direction leans from vertical.
            tilt = math.degrees(math.atan2(abs(built['across'][1]), abs(built['across'][2])))
            self.assertAlmostEqual(tilt, design['splay'], delta=1, msg=leg)
        self.assertGreater(spider.mass(), stock.mass() + .03)  # longer printed legs weigh more
        self.assertEqual(len(spider.joints), 9)

    def test_inverse_kinematics_puts_the_feet_on_target(self):
        for preset in ('stock', 'spider'):
            settings = robot_settings(preset)
            robot = CoopRobot(self.client, settings)
            gait = settings['gait']
            for motion, phase in (('stance', 0), ('forward', .3), ('spin-left', .8)):
                pose, unreachable = gaits.frame(robot.gait_legs, gait, motion, phase)
                self.assertEqual(unreachable, [])
                robot.pose(pose)
                feet = gaits.foot_positions(robot)
                left, right = gaits.MOTIONS[motion]
                for leg in gaits.LEGS:
                    stride = gait['stride'] * (left if leg.startswith('left') else right)
                    forward, up = gaits.foot_path(gait, (phase - gaits.PHASE[gait['type']][leg]) % 1, stride) \
                        if motion != 'stance' else (0, 0)
                    target = gaits.neutral(robot.gait_legs, gait, leg) + [forward, 0, up]
                    error = feet[leg] - target
                    self.assertLess(abs(error[0]), .001, f'{preset} {motion} {leg} x')
                    self.assertLess(abs(error[2]), .001, f'{preset} {motion} {leg} z')

    def test_both_designs_crawl_forward(self):
        for preset in ('stock', 'spider'):
            settings = robot_settings(preset)
            robot = CoopRobot(self.client, settings)
            robot.place([0, 0], 0)
            robot.running = True
            plan = gaits.plan(robot, settings['gait'], 'forward')
            self.assertEqual(plan['loop_from'], 1)
            self.assertEqual(plan['warnings'], [])
            robot.play_skill(plan)
            for _ in range(240 * 6):
                robot.advance_skill(1 / 240)
                robot.drive_motors()
                p.stepSimulation(physicsClientId=self.client)
            state = robot.body_state()
            self.assertFalse(state['fallen'], preset)
            self.assertGreater(state['position'][0], .05, preset)
            torques = robot.torques()
            self.assertEqual(set(torques), {j['name'] for j in robot.joints})
            self.assertTrue(all(abs(v) <= settings['servo']['torque'] + 1e-6 for v in torques.values()))
            p.removeBody(robot.robot, physicsClientId=self.client)

    def test_unreachable_stance_is_refused(self):
        settings = robot_settings('stock')
        robot = CoopRobot(self.client, settings)
        with self.assertRaisesRegex(ValueError, 'out of\\s+reach'):
            gaits.plan(robot, {**settings['gait'], 'hip_height': .2}, 'forward')
        with self.assertRaisesRegex(ValueError, 'motion'):
            gaits.plan(robot, settings['gait'], 'moonwalk')

    def test_servo_limits_reach_the_motors(self):
        robot = CoopRobot(self.client, robot_settings('stock', servo={'torque': .4, 'speed': 200}))
        self.assertTrue(all(j['effort'] == .4 and abs(j['velocity'] - math.radians(200)) < 1e-9 for j in robot.joints))
        robot.apply_servo(None)
        self.assertTrue(all(j['effort'] == 1.0 for j in robot.joints))  # the URDF's own limits


class LegConfigTest(unittest.TestCase):
    def test_leg_settings_are_checked(self):
        scenario = config.default()
        scenario['robot']['legs'] = {**scenario['robot']['legs'], 'splay': 60}
        with self.assertRaisesRegex(ValueError, 'leg splay'):
            config.validate(scenario)
        scenario = config.default()
        scenario['robot'].update(model='/data/somewhere/robot.urdf', legs=config.LEG_PRESETS['spider']['legs'])
        with self.assertRaisesRegex(ValueError, 'bundled Bittle'):
            config.validate(scenario)
        for gait, message in (({'type': 'gallop'}, 'gait type'), ({'cycle': 10}, 'gait cycle')):
            scenario = config.default()
            scenario['robot']['gait'] = {**scenario['robot']['gait'], **gait}
            with self.assertRaisesRegex(ValueError, message):
                config.validate(scenario)
        scenario = config.default()
        scenario['stones'] = {'count': 5, 'area': [1, 0, 0, 1]}
        with self.assertRaisesRegex(ValueError, 'stone area'):
            config.validate(scenario)
        old = config.default()
        for key in ('legs', 'servo', 'gait'):
            del old['robot'][key]
        del old['stones']
        self.assertEqual(config.validate(old), config.validate(config.default()))  # phase 1 files still load


class LegSessionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(coop_server.app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def setUp(self):
        self.client.put('/api/coop/scenario', json=config.default()).raise_for_status()

    def test_spider_gait_servo_and_readout(self):
        c, session = self.client, coop_server.session
        scenario = config.default()
        scenario['robot'].update(config.LEG_PRESETS['spider'])
        model = c.put('/api/coop/scenario', json=scenario).json()
        self.assertTrue(model['robot']['gaits'])
        self.assertAlmostEqual(model['robot']['legs']['left-front']['upper'], .075, delta=.001)
        self.assertEqual(model['leg_presets'], config.LEG_PRESETS)
        self.assertNotIn('generated', ' '.join(m['url'] for m in model['robot_models']))
        state = c.post('/api/coop/command', json={'action': 'gait', 'value': 'forward'}).json()
        self.assertEqual(state['robot']['skill'], 'gait-crawl-forward')
        with session.lock:
            for _ in range(240):
                session.tick()
            session.set_running(False)
        servo = c.get('/api/coop/state').json()['robot']['servo']
        self.assertEqual(servo['limit'], .29)
        self.assertEqual(len(servo['joints']), 9)
        self.assertTrue(all(0 <= j['at_limit'] <= 1 for j in servo['joints'].values()))
        self.assertEqual(c.post('/api/coop/command', json={'action': 'gait', 'value': 'nope'}).status_code, 400)
        robot, world = session.robot, session.world
        scenario['robot']['servo'] = {'torque': .5, 'speed': 300}
        scenario['robot']['gait'] = {**scenario['robot']['gait'], 'stride': .04}
        c.put('/api/coop/scenario', json=scenario).raise_for_status()
        self.assertIs(session.robot, robot)  # servo and gait changes need no rebuild
        self.assertIs(session.world, world)
        self.assertTrue(all(j['effort'] == .5 for j in session.robot.joints))
        modules = {m['id']: m for m in c.get('/api/hub/modules').json()}
        self.assertTrue(any('stretched' in line for line in modules['robot']['limitations']))
        self.assertTrue(c.post('/api/hub/modules/robot/test').json()['ok'])

    def test_traverse_test_compares_the_designs(self):
        scenario = config.default()
        scenario['robot']['gait'] = {**scenario['robot']['gait'], 'stride': .025}  # a third, "current" design
        self.client.put('/api/coop/scenario', json=scenario).raise_for_status()
        result = self.client.post('/api/coop/traverse-test', json={'seconds': 5}).json()
        names = [run['name'] for run in result['runs']]
        self.assertEqual(names[:4], ['Stock legs · Petoi walk', 'Stock legs · generated crawl',
                                     'Spider legs · generated crawl', 'Crab legs · crab gait'])
        self.assertEqual(len(names), 5)
        for run in result['runs']:
            self.assertNotIn('error', run, run['name'])
            self.assertEqual(run['falls'], 0, run['name'])
            self.assertGreater(run['distance'], .01, run['name'])
            self.assertAlmostEqual(run['seconds'], 5, delta=.1)
        self.assertEqual(result['course']['servo'], scenario['robot']['servo'])
        self.assertEqual(self.client.post('/api/coop/traverse-test', json={'seconds': 1}).status_code, 400)
        self.assertEqual(coop_server.session.time, 0)  # the running simulation was not touched
        topics = self.client.get('/api/hub/topics', params={'prefix': 'tests/'}).json()
        self.assertIn('tests/traverse', topics)


class TraverseTest(unittest.TestCase):
    def test_lying_down_is_not_a_fall_and_presets_add_no_extra_run(self):
        scenario = config.validate(config.default())
        name, settings, _ = traverse.variants(scenario)[0]
        result = traverse.run_one(scenario, name, settings, ('petoi', 'krest'), 5)
        self.assertNotIn('error', result)
        self.assertEqual(result['falls'], 0)
        self.assertLess(abs(result['distance']), .03)
        self.assertEqual(len(traverse.variants(scenario)), 4)  # the default design is the stock preset


if __name__ == '__main__':
    unittest.main()
