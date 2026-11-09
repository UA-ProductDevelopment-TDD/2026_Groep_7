"""Checks for the coop world: ground alignment, fence, house, dock, mud, stones and the robot standing on it."""
import json
import math
import unittest
from unittest import mock

import numpy as np
import pybullet as p

from coop import config
from coop.hub import Hub
from coop.robot import CoopRobot
from coop.world import World


def make(**sections):
    """A validated scenario: the default with some sections changed (a mud list replaces the default list)."""
    raw = config.default()
    for key, value in sections.items():
        raw[key] = value if isinstance(value, list) else {**raw[key], **value}
    return config.validate(raw)


def twist(world, x, y):
    """How far the four samples around a point are from one plane; Bullet's triangles differ from bilinear by up to a
    quarter of it."""
    i = min(max(int((x - world.origin[0]) / world.res), 0), world.nx - 2)
    j = min(max(int((y - world.origin[1]) / world.res), 0), world.ny - 2)
    h = world.heights
    return abs(h[j, i] - h[j, i + 1] - h[j + 1, i] + h[j + 1, i + 1])


def signed_area(corners):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(corners, corners[1:] + corners[:1])) / 2


class WorldCase(unittest.TestCase):
    def setUp(self):
        self.client = p.connect(p.DIRECT)
        p.setGravity(0, 0, -9.81, physicsClientId=self.client)
        p.setTimeStep(1 / 240, physicsClientId=self.client)
        p.setPhysicsEngineParameter(numSolverIterations=80, physicsClientId=self.client)

    def tearDown(self):
        p.disconnect(self.client)

    def build(self, **sections):
        self.scenario = make(**sections)
        self.world = World(self.client, self.scenario)
        return self.world

    def ray(self, start, end):
        """(body id, hit position) of the first thing a ray meets; the body id is -1 for a miss."""
        hit = p.rayTest(start, end, physicsClientId=self.client)[0]
        return hit[0], hit[3]

    def kind(self, body):
        return self.world.bodies[body]['kind'] if body in self.world.bodies else None

    def open_samples(self, count, seed=1):
        """Random height samples away from the edge, the run and the dock, where a ray from above reaches the ground."""
        w, s = self.world, self.scenario
        rng = np.random.default_rng(seed)
        yaw = math.radians(s['coop']['yaw'])
        points = []
        while len(points) < count:
            i, j = int(rng.integers(1, w.nx - 1)), int(rng.integers(1, w.ny - 1))
            x, y = w.origin[0] + i * w.res, w.origin[1] + j * w.res
            dx, dy = x - s['coop']['position'][0], y - s['coop']['position'][1]
            u, v = dx * math.cos(yaw) + dy * math.sin(yaw), -dx * math.sin(yaw) + dy * math.cos(yaw)
            near_run = abs(u) < s['coop']['run_size'][0] / 2 + .3 and abs(v) < s['coop']['run_size'][1] / 2 + .3
            if not near_run and math.hypot(x - s['dock']['position'][0], y - s['dock']['position'][1]) > .6:
                points.append((i, j, x, y))
        return points

    def fence_rays(self, fractions=(.11, .29, .5, .67, .89)):
        """(side, outside xy, inside xy) 0.3 m either side of the fence at several spots on each of its four sides."""
        c, run = self.scenario['coop'], self.scenario['coop']['run_size']
        yaw = math.radians(c['yaw'])
        hx, hy = run[0] / 2, run[1] / 2
        corners = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]

        def world(u, v):
            return (c['position'][0] + u * math.cos(yaw) - v * math.sin(yaw),
                    c['position'][1] + u * math.sin(yaw) + v * math.cos(yaw))

        rays = []
        for k in range(4):
            (u0, v0), (u1, v1) = corners[k], corners[(k + 1) % 4]
            length = math.hypot(u1 - u0, v1 - v0)
            nu, nv = (v1 - v0) / length, -(u1 - u0) / length  # outward for a counter-clockwise run
            for t in fractions:
                u, v = u0 + (u1 - u0) * t, v0 + (v1 - v0) * t
                rays.append((k, world(u + .3 * nu, v + .3 * nv), world(u - .3 * nu, v - .3 * nv)))
        return rays


class TerrainTest(WorldCase):
    def test_default_scenario_self_test(self):
        results = self.build().self_test()
        self.assertGreaterEqual(len(results), 6)
        for result in results:
            self.assertTrue(result['ok'], f"{result['name']}: {result['detail']}")
        hub = Hub()
        hub.register(self.world)
        self.assertTrue(hub.run_test('world')['ok'])
        self.assertEqual(hub.modules()[0]['id'], 'world')

    def test_variants_pass_self_test(self):
        variants = {
            'coarse and rough': dict(terrain={'resolution': .1, 'roughness': .03, 'feature_size': .3}),
            'no mud': dict(mud=[]),
            'three patches, one over another': dict(mud=[
                {'id': 'a', 'center': [1.5, -1.5], 'radius': .5, 'friction': .3, 'depth': .01},
                {'id': 'b', 'center': [1.6, -1.5], 'radius': .3, 'friction': .5, 'depth': .02},
                {'id': 'c', 'center': [-2.5, 2.5], 'radius': .4, 'friction': .2, 'depth': 0}]),
            'no flat margin': dict(terrain={'flat_margin': 0}),
            'turned coop, wide terrain': dict(coop={'yaw': -45.}, terrain={'size': [10.0, 6.0]}),
            'dock facing +x': dict(dock={'yaw': 0.}),
            'tall house along y, long spacing': dict(coop={'house_size': [.6, 1.2, .9], 'post_spacing': 1.3}),
            'almost all ground kept level': dict(terrain={'size': [4.0, 4.0], 'flat_margin': 1.0}),
        }
        for name, sections in variants.items():
            with self.subTest(name):
                world = self.build(**sections)
                for result in world.self_test():
                    self.assertTrue(result['ok'], f"{result['name']}: {result['detail']}")
                world.remove()

    def test_heights_match_the_collision_surface(self):
        # A non-square terrain with strong bumps: a swapped axis or a half-sample shift would show at once.
        world = self.build(terrain={'size': [6.0, 4.0], 'roughness': .03, 'feature_size': .3, 'seed': 3})
        self.assertEqual((world.nx, world.ny), (121, 81))
        self.assertGreater(world.heights.max() - world.heights.min(), .05)
        for i, j, x, y in self.open_samples(40):
            body, hit = self.ray([x, y, 2], [x, y, -2])
            self.assertEqual(body, world.terrain_body)
            self.assertAlmostEqual(hit[2], world.heights[j, i], delta=1e-3)
            self.assertAlmostEqual(hit[2], world.height_at(x, y), delta=1e-3)
        rng = np.random.default_rng(5)
        for x, y in zip(rng.uniform(-2.9, -1.8, 40), rng.uniform(-1.9, 1.9, 40)):  # between samples, clear of the coop
            body, hit = self.ray([x, y, 2], [x, y, -2])
            self.assertEqual(body, world.terrain_body)
            self.assertAlmostEqual(hit[2], world.height_at(x, y), delta=1e-3 + twist(world, x, y) / 4)

    def test_height_at_outside_the_terrain_is_the_edge(self):
        world = self.build()
        for x, y in ((-50, 0), (50, 0), (0, -50), (0, 50), (50, 50)):
            edge = min(max(x, -4), 4), min(max(y, -4), 4)
            self.assertAlmostEqual(world.height_at(x, y), world.height_at(*edge), places=9)
        self.assertAlmostEqual(world.height_at(-4, -4), world.heights[0, 0], places=9)
        self.assertAlmostEqual(world.height_at(4, 4), world.heights[-1, -1], places=9)

    def test_ground_is_level_in_the_run_and_at_the_dock(self):
        for yaw in (0., 30.):
            with self.subTest(coop_yaw=yaw):
                world = self.build(coop={'yaw': yaw})
                d = self.scenario['dock']
                a = math.radians(yaw)
                for u in np.linspace(-1.5, 1.5, 13):  # the fenced run itself; the default mud patch overlaps the margin
                    for v in np.linspace(-1, 1, 9):
                        self.assertEqual(world.height_at(u * math.cos(a) - v * math.sin(a),
                                                         u * math.sin(a) + v * math.cos(a)), 0)
                for angle in np.linspace(0, 2 * math.pi, 12, endpoint=False):
                    for r in (0, .25, .25 + self.scenario['terrain']['flat_margin'] - .08):
                        self.assertEqual(world.height_at(d['position'][0] + r * math.cos(angle),
                                                         d['position'][1] + r * math.sin(angle)), 0)
                self.assertGreater(world.heights.std(), .005)  # but the rest of the ground is bumpy
                world.remove()

    def test_same_seed_same_ground_and_other_seeds_differ(self):
        first = self.build(terrain={'seed': 11}).heights.copy()
        self.world.remove()
        again = self.build(terrain={'seed': 11}).heights.copy()
        self.world.remove()
        other = self.build(terrain={'seed': 12}).heights.copy()
        self.assertTrue(np.array_equal(first, again))
        self.assertFalse(np.allclose(first, other, atol=1e-3))

    def test_roughness_zero_is_flat(self):
        world = self.build(terrain={'roughness': 0.})
        mud = self.scenario['mud'][0]
        self.assertTrue(np.all(world.heights[world.materials == 0] == 0))
        self.assertAlmostEqual(world.height_at(*mud['center']), -mud['depth'], places=6)  # only the mud dips
        world.remove()
        flat = self.build(terrain={'roughness': 0.}, mud=[])
        self.assertEqual((flat.heights.min(), flat.heights.max()), (0, 0))
        for x, y in ((0, 3), (-3.3, 2.1), (2.5, -3.2)):
            body, hit = self.ray([x, y, 1], [x, y, -1])
            self.assertEqual(body, flat.terrain_body)
            self.assertAlmostEqual(hit[2], 0, places=6)

    def test_roughness_sets_the_spread(self):
        for roughness in (.005, .02):
            with self.subTest(roughness=roughness):
                world = self.build(terrain={'roughness': roughness, 'seed': 4}, mud=[])
                free = world.flat_weight >= 1
                self.assertGreater(free.sum(), 5000)
                self.assertAlmostEqual(world.heights[free].std() / roughness, 1, delta=.25)
                world.remove()

    def test_mud_is_a_smooth_dip(self):
        world = self.build()
        mud = self.scenario['mud'][0]
        x, y = mud['center']
        plain = World(self.client, make(mud=[]))
        dip = {offset: world.height_at(x + offset, y) - plain.height_at(x + offset, y) for offset in (0, .25, .45, .5)}
        plain.remove()
        self.assertAlmostEqual(dip[0], -mud['depth'], places=6)
        self.assertAlmostEqual(dip[.25], -mud['depth'] * (.5 + .5 * math.cos(math.pi * .25 / mud['radius'])), places=6)
        self.assertAlmostEqual(dip[.45], 0, places=6)
        self.assertAlmostEqual(dip[.5], 0, places=6)


class FenceHouseDockTest(WorldCase):
    def test_fence_is_closed_on_every_side_and_follows_the_yaw(self):
        for yaw in (0., 30., -75.):
            with self.subTest(coop_yaw=yaw):
                world = self.build(coop={'yaw': yaw})
                rays = self.fence_rays()
                self.assertEqual(len(rays), 20)
                for side, outside, inside in rays:
                    body, _ = self.ray([*outside, .3], [*inside, .3])
                    self.assertIn(self.kind(body), ('post', 'fence'), f'side {side} lets a ray through')
                world.remove()

    def test_fence_height_posts_and_colours(self):
        world = self.build()
        height = self.scenario['coop']['fence_height']
        side, outside, inside = self.fence_rays((.3,))[2]  # the +y side: nothing stands just inside it
        self.assertIn(self.kind(self.ray([*outside, height - .02], [*inside, height - .02])[0]), ('post', 'fence'))
        self.assertEqual(self.ray([*outside, height + .03], [*inside, height + .03])[0], -1)
        boxes = world.scene()['boxes']
        self.assertEqual({b['color'] for b in boxes if b['kind'] == 'post'}, {'#8a6a4a'})
        self.assertEqual({b['color'] for b in boxes if b['kind'] == 'fence'}, {'#b9c2c8'})
        self.assertEqual(sum(b['kind'] == 'post' for b in boxes), 2 * (6 + 4))  # 0.5 m spacing, corners shared
        self.assertEqual(sum(b['kind'] == 'fence' for b in boxes), 2 * (6 + 4))
        for b in boxes:
            if b['kind'] == 'post':
                self.assertEqual(b['size'], [.03, .03, height])
            if b['kind'] == 'fence':
                self.assertEqual(b['size'][1:], [.01, height])

    def test_house_and_roof(self):
        world = self.build(coop={'yaw': 20.})
        boxes = {b['id']: b for b in world.scene()['boxes'] if b['kind'] in ('house', 'roof')}
        house = boxes['house']
        c, run = self.scenario['coop'], self.scenario['coop']['run_size']
        a = math.radians(c['yaw'])
        dx, dy = house['position'][0] - c['position'][0], house['position'][1] - c['position'][1]
        u, v = dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)
        gap = (u - house['size'][0] / 2) - (-run[0] / 2)
        self.assertTrue(.04 < gap < .1, f'gap to the -x fence line {gap:.3f} m')
        self.assertLess(abs(v), 1e-3)
        self.assertEqual(house['size'], c['house_size'])
        self.assertEqual(house['color'], '#c8a26b')
        self.assertEqual({b['color'] for b in boxes.values() if b['kind'] == 'roof'}, {'#7a3b2e'})
        # A ray down onto the house meets the roof, above the walls; a ray into the wall meets the house.
        x, y = house['position'][:2]
        body, hit = self.ray([x, y, 3], [x, y, 0])
        self.assertEqual(self.kind(body), 'roof')
        self.assertGreater(hit[2], house['size'][2])
        body, _ = self.ray([x + math.cos(a) * 1.5, y + math.sin(a) * 1.5, .3], [x, y, .3])
        self.assertEqual(self.kind(body), 'house')

    def test_dock_geometry(self):
        world = self.build()
        d = self.scenario['dock']
        boxes = {b['kind']: b for b in world.scene()['boxes'] if b['kind'].startswith('dock')}
        a = math.radians(d['yaw'])
        heading = (math.cos(a), math.sin(a))
        plate, stop = boxes['dock'], boxes['dock-stop']
        self.assertEqual(plate['size'], [.22, .16, .003])  # from 10 cm behind the dock point to the stop block
        self.assertEqual(stop['size'], [.03, .16, .06])
        self.assertEqual((plate['color'], stop['color']), ('#2f6f9f', '#24547a'))
        gap = (stop['position'][0] - d['position'][0], stop['position'][1] - d['position'][1])
        ahead = gap[0] * heading[0] + gap[1] * heading[1]
        self.assertAlmostEqual(ahead - .015, .12, delta=.002)  # the stop block's near face
        start = (d['position'][0] - heading[0] * .08, d['position'][1] - heading[1] * .08, .03)
        body, hit = self.ray(start, [d['position'][0] + heading[0] * .3, d['position'][1] + heading[1] * .3, .03])
        self.assertEqual(self.kind(body), 'dock-stop')
        self.assertAlmostEqual(math.hypot(hit[0] - d['position'][0], hit[1] - d['position'][1]), .12, delta=.002)
        body, hit = self.ray([d['position'][0], d['position'][1], 1], [d['position'][0], d['position'][1], -1])
        self.assertEqual(self.kind(body), 'dock')
        self.assertAlmostEqual(hit[2], .003, delta=1e-4)  # a 3 mm step: 6 mm made the stock walk stumble
        self.assertAlmostEqual(world.scene()['dock']['position'][2], world.height_at(*d['position']), delta=1e-4)


class MaterialTest(WorldCase):
    def test_mud_lookup(self):
        world = self.build()
        mud = self.scenario['mud'][0]
        self.assertEqual(world.material_at(*mud['center']),
                         {'material': 'mud', 'id': 'mud-1', 'name': mud['name'], 'friction': .35})
        self.assertEqual(world.friction_at(*mud['center']), .35)
        self.assertEqual(world.friction_at(mud['center'][0] + mud['radius'] * .9, mud['center'][1]), .35)
        self.assertEqual(world.friction_at(mud['center'][0] + mud['radius'] * 1.1, mud['center'][1]), .8)
        self.assertEqual(world.material_at(-3, 3), {'material': 'ground', 'id': None, 'name': 'Ground', 'friction': .8})
        self.assertEqual(world.friction_at(-3, 3), self.scenario['terrain']['friction'])

    def test_later_patch_wins_and_the_material_map_agrees(self):
        world = self.build(mud=[
            {'id': 'a', 'name': 'A', 'center': [1.5, -1.5], 'radius': .5, 'friction': .3, 'depth': .01},
            {'id': 'b', 'name': 'B', 'center': [1.6, -1.5], 'radius': .3, 'friction': .5, 'depth': .02}])
        self.assertEqual(world.material_at(1.5, -1.5)['id'], 'b')  # a's centre lies inside b
        self.assertEqual(world.friction_at(1.5, -1.5), .5)
        self.assertEqual(world.material_at(1.15, -1.5)['id'], 'a')
        terrain = world.scene()['terrain']
        self.assertEqual(terrain['friction'], .8)
        self.assertEqual(terrain['mud'], self.scenario['mud'])
        for (x, y), expected in (((1.5, -1.5), 2), ((1.15, -1.5), 1), ((-3, 3), 0), ((1.6, -1.5), 2)):
            i = round((x - terrain['origin'][0]) / terrain['resolution'])
            j = round((y - terrain['origin'][1]) / terrain['resolution'])
            self.assertEqual(terrain['materials'][i + j * terrain['rows']], expected)

    def test_no_mud(self):
        world = self.build(mud=[])
        self.assertEqual(world.material_at(0, 0)['material'], 'ground')
        self.assertFalse(world.materials.any())
        self.assertEqual(world.config()['mud_patches'], 0)


class RobotOnWorldTest(WorldCase):
    def robot(self):
        return CoopRobot(self.client, self.scenario['robot'])

    def friction_of(self, robot):
        return {name: p.getDynamicsInfo(robot.robot, link, physicsClientId=self.client)[1]
                for name, link in robot.feet.items()}

    def test_feet_take_the_friction_under_them(self):
        world = self.build()
        robot = self.robot()
        mud = self.scenario['mud'][0]
        ground = self.scenario['terrain']['friction']
        self.assertEqual(len(robot.feet), 4)
        robot.place(mud['center'], 0, world.height_at)
        result = world.update_foot_friction(robot.robot, robot.feet)
        self.assertEqual(result, {name: mud['friction'] for name in robot.feet})
        self.assertEqual(self.friction_of(robot), result)
        robot.place([-2.5, 2.5], 20, world.height_at)
        result = world.update_foot_friction(robot.robot, robot.feet)
        self.assertEqual(result, {name: ground for name in robot.feet})
        self.assertEqual(self.friction_of(robot), result)
        # Straddling the rim: each foot follows its own position.
        robot.place([mud['center'][0] - mud['radius'] + .02, mud['center'][1]], 0, world.height_at)
        result = world.update_foot_friction(robot.robot, robot.feet)
        self.assertEqual(set(result.values()), {ground, mud['friction']})
        for name, link in robot.feet.items():
            x, y = p.getLinkState(robot.robot, link, computeForwardKinematics=1, physicsClientId=self.client)[0][:2]
            self.assertEqual(result[name], world.friction_at(x, y))
        self.assertEqual(self.friction_of(robot), result)

    def test_friction_is_only_changed_when_it_changes(self):
        world = self.build()
        robot = self.robot()
        robot.place(self.scenario['mud'][0]['center'], 0, world.height_at)
        with mock.patch.object(p, 'changeDynamics', wraps=p.changeDynamics) as change:
            world.update_foot_friction(robot.robot, robot.feet)
            self.assertEqual(change.call_count, 4)
            world.update_foot_friction(robot.robot, robot.feet)
            world.update_foot_friction(robot.robot, robot.feet)
            self.assertEqual(change.call_count, 4)
            robot.place([-2.5, 2.5], 0, world.height_at)
            world.update_foot_friction(robot.robot, robot.feet)
            self.assertEqual(change.call_count, 8)
            world.update_foot_friction(robot.robot, robot.feet)
            self.assertEqual(change.call_count, 8)
            world.forget_feet(robot.robot)
            world.update_foot_friction(robot.robot, robot.feet)
            self.assertEqual(change.call_count, 12)

    def stand(self, world, robot, position, heading, seconds=2.):
        robot.place(position, heading, world.height_at)
        robot.running = True
        world.update_foot_friction(robot.robot, robot.feet)
        for _ in range(int(seconds * 240)):
            robot.drive_motors()
            p.stepSimulation(physicsClientId=self.client)
        return robot.body_state(world.height_at)

    def test_robot_stands_on_the_default_terrain(self):
        world = self.build()
        robot = self.robot()
        start, dock, mud = self.scenario['robot']['start'], self.scenario['dock'], self.scenario['mud'][0]
        places = {'start': (start['position'], start['heading']), 'dock': (dock['position'], dock['yaw']),
                  'mud': (mud['center'], 0.), 'bumps': ([-2.5, 2.5], 30.)}
        for name, (position, heading) in places.items():
            with self.subTest(name):
                state = self.stand(world, robot, position, heading)
                self.assertFalse(state['fallen'], f"roll {state['roll']:.0f}, pitch {state['pitch']:.0f}")
                self.assertTrue(.05 < state['height'] < .13, f"body {state['height'] * 100:.1f} cm above the ground")
                self.assertLess(state['speed'], .05)
                self.assertLess(math.hypot(state['position'][0] - position[0], state['position'][1] - position[1]), .15)

    def test_robot_stands_on_flat_terrain(self):
        world = self.build(terrain={'roughness': 0.}, mud=[])
        state = self.stand(world, self.robot(), [-2.5, 2.5], 30.)
        self.assertFalse(state['fallen'])
        self.assertTrue(.05 < state['height'] < .13)


class ReportTest(WorldCase):
    def test_describe_is_json_and_complete(self):
        world = self.build()
        description = world.scene()
        self.assertEqual(json.loads(json.dumps(description)), description)
        terrain = description['terrain']
        self.assertEqual((terrain['rows'], terrain['cols']), (161, 161))
        self.assertEqual(len(terrain['heights']), terrain['rows'] * terrain['cols'])
        self.assertEqual(len(terrain['materials']), terrain['rows'] * terrain['cols'])
        self.assertEqual(terrain['origin'], [-4.0, -4.0])
        self.assertEqual((terrain['size'], terrain['resolution']), ([8.0, 8.0], .05))
        self.assertTrue(all(h == round(h, 4) for h in terrain['heights']))
        self.assertTrue(set(terrain['materials']) == {0, 1})
        for i, j in ((3, 90), (150, 12), (80, 80)):  # x runs fastest
            self.assertAlmostEqual(terrain['heights'][i + j * terrain['rows']], world.heights[j, i], delta=5e-5)
        self.assertEqual(terrain['friction'], .8)
        self.assertEqual(terrain['mud'], self.scenario['mud'])
        boxes = description['boxes']
        self.assertEqual({b['kind'] for b in boxes}, {'post', 'fence', 'house', 'roof', 'dock', 'dock-stop'})
        self.assertEqual(len({b['id'] for b in boxes}), len(boxes))
        self.assertEqual(len(boxes), len(world.bodies) - 1)
        for box in boxes:
            self.assertEqual(set(box), {'id', 'name', 'kind', 'size', 'position', 'quaternion', 'color'})
            self.assertAlmostEqual(sum(q * q for q in box['quaternion']), 1, places=5)
            self.assertRegex(box['color'], r'^#[0-9a-f]{6}$')
            self.assertTrue(all(s > 0 for s in box['size']))
        run = description['run']
        self.assertAlmostEqual(signed_area(run['corners']), 6.0, places=3)  # counter-clockwise, 3 x 2 m
        self.assertEqual((run['position'], run['yaw'], run['size']), ([0.0, 0.0], 0.0, [3.0, 2.0]))
        dock, shown = self.scenario['dock'], description['dock']
        self.assertEqual(shown['position'][:2], dock['position'])
        self.assertEqual((shown['yaw'], shown['capture_distance'], shown['capture_angle']),
                         (dock['yaw'], dock['capture_distance'], dock['capture_angle']))
        self.assertEqual(description.keys(), {'terrain', 'boxes', 'run', 'dock'})
        # The hub's module listing stays small: the scene is only in scene().
        module = world.describe()
        self.assertEqual((module['id'], module['name'], module['kind']), ('world', 'Terrain & coop', 'world'))
        self.assertEqual(module['limitations'], list(World.limitations))
        self.assertNotIn('terrain', module)

    def test_rotated_run_corners(self):
        world = self.build(coop={'yaw': 30., 'position': [.5, .25]})
        corners = world.scene()['run']['corners']
        a = math.radians(30)
        self.assertAlmostEqual(corners[0][0], .5 - 1.5 * math.cos(a) + math.sin(a), places=3)
        self.assertAlmostEqual(corners[0][1], .25 - 1.5 * math.sin(a) - math.cos(a), places=3)
        self.assertAlmostEqual(signed_area(corners), 6.0, places=3)

    def test_identity_limitations_and_config(self):
        world = self.build()
        self.assertEqual((world.id, world.name, world.kind), ('world', 'Terrain & coop', 'world'))
        self.assertGreaterEqual(len(World.limitations), 4)
        self.assertTrue(all(isinstance(s, str) and s.endswith('.') for s in World.limitations))
        text = ' '.join(World.limitations).lower()
        for word in ('rigid', 'friction', 'fence', 'dock'):
            self.assertIn(word, text)
        summary = world.config()
        self.assertEqual((summary['samples'], summary['mud_patches'], summary['bodies']),
                         (161 * 161, 1, len(world.bodies)))
        json.dumps(summary)

    def test_remove_leaves_only_what_was_there_before(self):
        box = p.createCollisionShape(p.GEOM_BOX, halfExtents=[.1, .1, .1], physicsClientId=self.client)
        keep = p.createMultiBody(0, box, basePosition=[9, 9, 9], physicsClientId=self.client)
        before = p.getNumBodies(physicsClientId=self.client)
        world = self.build()
        self.assertGreater(len(world.bodies), 30)
        self.assertEqual(p.getNumBodies(physicsClientId=self.client), before + len(world.bodies))
        world.remove()
        self.assertEqual(p.getNumBodies(physicsClientId=self.client), before)
        self.assertEqual(p.getBasePositionAndOrientation(keep, physicsClientId=self.client)[0], (9, 9, 9))
        world.remove()  # twice is harmless
        self.assertEqual(world.config()['bodies'], 0)
        self.assertFalse(all(r['ok'] for r in world.self_test()))  # a removed world fails its checks without crashing

    def test_a_world_can_be_rebuilt_over_and_over(self):
        before = p.getNumBodies(physicsClientId=self.client)
        for seed in (1, 2, 3):
            self.build(terrain={'seed': seed}).remove()
        self.assertEqual(p.getNumBodies(physicsClientId=self.client), before)


def box_corners(box):
    """World positions of a scene box's eight corners, and its rotation matrix."""
    x, y, z, w = box['quaternion']
    rotation = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    signs = np.array([[a, b, c] for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)])
    return np.array(box['position']) + (signs * np.array(box['size']) / 2) @ rotation.T, rotation


def stones_in(world):
    return [box for box in world.scene()['boxes'] if box['kind'] == 'stone']


class StoneTest(WorldCase):
    STONES = {'count': 200, 'min_size': .02, 'max_size': .05, 'seed': 3}

    def test_no_stones_by_default(self):
        world = self.build()
        boxes = world.scene()['boxes']
        self.assertEqual(stones_in(world), [])
        self.assertEqual((len(boxes), len(world.bodies)), (45, 46))
        self.assertEqual((world.config()['stones'], world.config()['stones_requested']), (0, 0))
        self.assertNotIn('stone', {info['kind'] for info in world.bodies.values()})
        world.remove()
        # The seed alone adds nothing.
        self.assertEqual(self.build(stones={'count': 0, 'seed': 99}).scene()['boxes'], boxes)

    def test_all_stones_are_placed_and_registered(self):
        world = self.build(stones=self.STONES)
        stones = stones_in(world)
        self.assertEqual(len(stones), 200)
        summary = world.config()
        self.assertEqual((summary['stones'], summary['stones_requested']), (200, 200))
        self.assertEqual(summary['bodies'], 46 + 200)
        self.assertEqual([s['name'] for s in stones], [f'Stone {n}' for n in range(1, 201)])
        self.assertEqual(len({s['id'] for s in stones}), 200)
        named = [info for info in world.bodies.values() if info['kind'] == 'stone']
        self.assertEqual([info['name'] for info in named], [s['name'] for s in stones])
        self.assertEqual(len(world.scene()['boxes']), len(world.bodies) - 1)
        for result in world.self_test():
            self.assertTrue(result['ok'], f"{result['name']}: {result['detail']}")
        self.assertIn('stones', ' '.join(World.limitations).lower())

    def test_layout_follows_the_stone_seed_only(self):
        first = stones_in(self.build(stones=self.STONES))
        self.world.remove()
        again = stones_in(self.build(stones=self.STONES))
        self.world.remove()
        other = stones_in(self.build(stones={**self.STONES, 'seed': 4}))
        self.world.remove()
        bumpier = stones_in(self.build(stones=self.STONES, terrain={'seed': 8}))
        self.assertEqual(first, again)
        self.assertNotEqual([s['position'][:2] for s in first], [s['position'][:2] for s in other])
        self.assertNotEqual([s['size'] for s in first], [s['size'] for s in other])
        # Another ground changes how deep the stones sit, never where they are or how big.
        self.assertEqual([(s['size'], s['position'][:2], s['quaternion']) for s in first],
                         [(s['size'], s['position'][:2], s['quaternion']) for s in bumpier])

    def test_stones_keep_out_of_the_run_the_dock_and_the_start(self):
        # Many stones on a small terrain, with the coop turned: the zones must stay empty while the rest fills up.
        world = self.build(stones={'count': 500, 'min_size': .03, 'max_size': .08, 'seed': 5},
                           terrain={'size': [5.0, 5.0]}, coop={'yaw': 30.})
        stones = stones_in(world)
        self.assertEqual(len(stones), 500)
        c, s = self.scenario['coop'], self.scenario
        a = math.radians(c['yaw'])
        edge = s['terrain']['size'][0] / 2 - .05
        for stone in stones:
            x, y = stone['position'][:2]
            size = max(stone['size'][:2])
            self.assertTrue(abs(x) <= edge + 1e-9 and abs(y) <= edge + 1e-9, f'{stone["name"]} too near the edge')
            u, v = x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)
            self.assertFalse(abs(u) < c['run_size'][0] / 2 + .05 and abs(v) < c['run_size'][1] / 2 + .05,
                             f'{stone["name"]} inside the run')
            for label, point in (('dock', s['dock']['position']), ('start', s['robot']['start']['position'])):
                self.assertGreaterEqual(math.hypot(x - point[0], y - point[1]), .25 + size,
                                        f'{stone["name"]} by the {label}')
        # And they really do spread over the free ground, including up to the zones' borders.
        xs, ys = [st['position'][0] for st in stones], [st['position'][1] for st in stones]
        self.assertLess(min(xs), -2.2)
        self.assertGreater(max(xs), 2.2)
        self.assertLess(min(ys), -2.2)
        self.assertGreater(max(ys), 2.2)

    def test_each_stone_sinks_into_the_ground_and_stands_above_it(self):
        world = self.build(stones=self.STONES)
        palette = {'#7d7f7a', '#8b857c', '#6f6a63', '#9a958c'}
        tilts = []
        for stone in stones_in(world):
            corners, rotation = box_corners(stone)
            ground = world.height_at(*stone['position'][:2])
            self.assertLess(corners[:, 2].min(), ground, f'{stone["name"]} does not reach into the ground')
            self.assertGreater(corners[:, 2].max(), ground, f'{stone["name"]} does not stand above the ground')
            sx, sy, height = stone['size']
            self.assertTrue(.02 - 1e-4 <= sx <= .05 + 1e-4 and .02 - 1e-4 <= sy <= .05 + 1e-4)
            self.assertTrue(.4 * min(sx, sy) - 2e-4 <= height <= .8 * min(sx, sy) + 2e-4)
            self.assertIn(stone['color'], palette)
            tilts.append(math.degrees(math.acos(rotation[2, 2])))
        self.assertLess(max(tilts), 10 * math.sqrt(2) + .1)  # roll and pitch of up to 10 degrees each
        self.assertGreater(max(tilts), 5)  # but they are not all lying flat
        self.assertGreater(len({s['color'] for s in stones_in(world)}), 1)
        # A ray from above meets a stone (or one lying over it) above the ground at its middle.
        for stone in stones_in(world)[:40]:
            x, y = stone['position'][:2]
            body, hit = self.ray([x, y, 1], [x, y, -1])
            self.assertEqual(self.kind(body), 'stone')
            self.assertGreater(hit[2], world.height_at(x, y))

    def test_stone_scene_is_json_safe(self):
        world = self.build(stones=self.STONES)
        scene = world.scene()
        self.assertEqual(json.loads(json.dumps(scene)), scene)
        for stone in stones_in(world):
            self.assertEqual(set(stone), {'id', 'name', 'kind', 'size', 'position', 'quaternion', 'color'})
            for value in stone['size'] + stone['position'] + stone['quaternion']:
                self.assertIs(type(value), float)
            self.assertAlmostEqual(sum(q * q for q in stone['quaternion']), 1, places=5)
            self.assertRegex(stone['color'], r'^#[0-9a-f]{6}$')

    def test_a_shortfall_is_counted_and_explained(self):
        # A 2 x 2 m terrain lies wholly inside the 3 x 2 m run, so no stone has anywhere to go.
        world = self.build(stones={'count': 30, 'min_size': .02, 'max_size': .05, 'seed': 1},
                           terrain={'size': [2.0, 2.0]}, dock={'position': [.9, .9]},
                           robot={'start': {'position': [-.9, .9], 'heading': 0.}})
        summary = world.config()
        self.assertEqual((summary['stones'], summary['stones_requested']), (0, 30))
        self.assertEqual(stones_in(world), [])
        results = {r['name']: r for r in world.self_test()}
        self.assertEqual([name for name, r in results.items() if not r['ok']], ['Stones are placed as asked'])
        detail = results['Stones are placed as asked']['detail']
        self.assertIn('30 of 30', detail)
        self.assertIn('could not be placed', detail)

    def test_stones_do_not_confuse_the_self_test(self):
        # A low fence and big stones: many fence rays meet a stone first and must carry on to the fence.
        world = self.build(stones={'count': 500, 'min_size': .1, 'max_size': .2, 'seed': 2},
                           coop={'fence_height': .1, 'yaw': 20.})
        blocked = 0
        for side, outside, inside in self.fence_rays():
            blocked += self.kind(self.ray([*outside, .05], [*inside, .05])[0]) == 'stone'
        self.assertGreater(blocked, 0, 'no stone stands in the way of a fence ray; the test proves nothing')
        for result in world.self_test():
            self.assertTrue(result['ok'], f"{result['name']}: {result['detail']}")

    def test_stones_are_removed_with_the_world(self):
        before = p.getNumBodies(physicsClientId=self.client)
        world = self.build(stones=self.STONES)
        self.assertEqual(p.getNumBodies(physicsClientId=self.client), before + 246)
        world.remove()
        self.assertEqual(p.getNumBodies(physicsClientId=self.client), before)
        self.assertEqual(world.config()['stones'], 0)

    def test_robot_stands_on_stony_ground(self):
        # Dense stones, and the robot put right on top of one of them.
        world = self.build(stones={'count': 500, 'min_size': .03, 'max_size': .06, 'seed': 6},
                           terrain={'size': [4.0, 4.0]})
        stone = next(s for s in stones_in(world) if s['position'][1] > 1.4 and abs(s['position'][0]) < 1.2)
        robot = CoopRobot(self.client, self.scenario['robot'])
        robot.place(stone['position'][:2], 0., world.height_at)
        robot.running = True
        world.update_foot_friction(robot.robot, robot.feet)
        for _ in range(240):
            robot.drive_motors()
            p.stepSimulation(physicsClientId=self.client)
        state = robot.body_state(world.height_at)
        self.assertTrue(all(math.isfinite(v) for v in state['position']))
        self.assertFalse(state['fallen'], f"roll {state['roll']:.0f}, pitch {state['pitch']:.0f}")
        self.assertLess(state['speed'], .1)


if __name__ == '__main__':
    unittest.main()
