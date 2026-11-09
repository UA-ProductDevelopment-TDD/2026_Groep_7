"""The world: rough ground with mud patches, the fenced coop run with its house, and the charging dock.

Everything is static and built once in the Bullet client. The ground is a heightfield on a regular grid; height_at()
interpolates the same samples, so what the robot, the sensors and the browser see agree. Mud is a shallow dip plus a
lower foot friction (update_foot_friction), not soft ground.
"""
import math

import numpy as np
import pybullet as p

from coop.hub import Module, check

FLAT_BLEND = .3          # metres over which the bumps fade in outside the flattened areas
DOCK_FLAT_RADIUS = .25   # metres around the dock position that stay level (plus the scenario's flat margin)
START_FLAT_RADIUS = .2   # metres around the robot's start position that stay level
POST_SIZE = .03
PANEL_THICKNESS = .01
HOUSE_GAP = .05          # metres between the house and the fence post faces on its -x side
ROOF_PITCH = math.radians(25)
ROOF_THICKNESS = .015
ROOF_OVERHANG = .04
DOCK_PLATE = (.22, .16, .003)   # length along the heading (made to reach the stop block), width, height
DOCK_PLATE_REAR = .10           # metres of plate behind the dock position
DOCK_STOP = (.03, .16, .06)     # thickness along the heading, width, height
DOCK_STOP_FACE = .12            # metres from the dock position to the stop block's near face, unless the scenario sets it
SURFACE_FRICTION = .8           # static boxes
STONE_COLORS = ('#7d7f7a', '#8b857c', '#6f6a63', '#9a958c')
STONE_TRIES = 100               # places tried for one stone before it is skipped
STONE_EDGE = .05                # metres a stone's centre stays inside the terrain edge
STONE_RUN_MARGIN = .05          # metres around the fenced run kept free of stones (plus half the stone's size)
STONE_CLEAR = .25               # metres around the dock and the robot start kept free (plus the stone's size)
STONE_SINK = .3                 # fraction of a stone's height that lies below the ground
STONE_TILT = 10.                # degrees of random roll and pitch at most
GROUND_COLOR = [.45, .55, .32, 1.]
COLORS = {'post': '#8a6a4a', 'fence': '#b9c2c8', 'house': '#c8a26b', 'roof': '#7a3b2e', 'dock': '#2f6f9f',
          'dock-stop': '#24547a'}


def _quaternion(axis, angle):
    s = math.sin(angle / 2)
    return [axis[0] * s, axis[1] * s, axis[2] * s, math.cos(angle / 2)]


def _yaw(degrees):
    return _quaternion((0, 0, 1), math.radians(degrees))


def _multiply(a, b):
    """Hamilton product of two xyzw quaternions: b is applied first, then a."""
    x1, y1, z1, w1 = a
    x2, y2, z2, w2 = b
    return [w1 * x2 + w2 * x1 + y1 * z2 - z1 * y2, w1 * y2 + w2 * y1 + z1 * x2 - x1 * z2,
            w1 * z2 + w2 * z1 + x1 * y2 - y1 * x2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]


def _rgba(color):
    return [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)] + [1.]


def _lattice_noise(rng, gx, gy):
    """Smooth random values: one normal sample per unit lattice point, blended with a quintic fade."""
    i, j = np.floor(gx).astype(int), np.floor(gy).astype(int)
    lattice = rng.standard_normal((j.max() + 2, i.max() + 2))
    fx, fy = gx - i, gy - j
    fx, fy = fx ** 3 * (fx * (fx * 6 - 15) + 10), fy ** 3 * (fy * (fy * 6 - 15) + 10)
    wx, wy = fx[None, :], fy[:, None]
    low = lattice[np.ix_(j, i)] * (1 - wx) + lattice[np.ix_(j, i + 1)] * wx
    high = lattice[np.ix_(j + 1, i)] * (1 - wx) + lattice[np.ix_(j + 1, i + 1)] * wx
    return low * (1 - wy) + high * wy


class World(Module):
    kind = 'world'
    limitations = (
        'The ground is rigid: Bittle never sinks into mud. Mud is a shallow dip with a lower foot friction.',
        'Each material has one friction value: there is no grass and no wet or dry patches that change.',
        'Stones are fixed boxes: they never roll, tip over or sink further, and they keep the ground\'s friction.',
        'Fence panels are solid and closed; real chicken wire is see-through and has gaps. The house is a closed box.',
        'The dock is a static block. Its magnet and charging contacts are modelled elsewhere as a capture zone.',
        'Only the feet take the friction of the material under them; the rest of the body keeps its own friction.',
        'Bullet\'s own camera image draws the ground in one colour, so mud shows only in the browser view.',
    )

    def __init__(self, client, scenario):
        super().__init__('world', 'Terrain & coop')
        self.client = client
        self.terrain = scenario['terrain']
        self.mud = scenario['mud']
        self.coop = scenario['coop']
        self.dock = scenario['dock']
        self.stones = scenario.get('stones') or {'count': 0}
        self.start = scenario['robot']['start']['position']
        self.bodies = {}            # Bullet body id -> {'id', 'name', 'kind'}; kind 'terrain' for the ground
        self._boxes = []            # scene() entries for the static boxes
        self._foot_friction = {}    # (body, link) -> friction last set
        self._stones = []           # one dict per placed stone: body, x, y, reach
        self._stone_bodies = set()
        self.stones_requested = self.stones['count']
        self._scene = None
        yaw = math.radians(self.coop['yaw'])
        self._cos, self._sin = math.cos(yaw), math.sin(yaw)
        try:
            self._build_terrain()
            self._build_run()
            self._build_house()
            self._build_dock()
            self._build_stones()
        except Exception:
            self.remove()
            raise

    # Terrain

    def _flat_weight(self, x, y):
        """0 inside the areas kept level, 1 on free ground, with a smooth blend between."""
        margin = self.terrain['flat_margin']
        dx, dy = x - self.coop['position'][0], y - self.coop['position'][1]
        u, v = dx * self._cos + dy * self._sin, -dx * self._sin + dy * self._cos
        qx = np.abs(u) - (self.coop['run_size'][0] / 2 + margin)
        qy = np.abs(v) - (self.coop['run_size'][1] / 2 + margin)
        run = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
        dock = np.maximum(np.hypot(x - self.dock['position'][0], y - self.dock['position'][1])
                          - (DOCK_FLAT_RADIUS + margin), 0)
        # The robot is set down at its start, so that spot is level too: on a slope a narrow robot can tip over
        # before it takes a step, which says more about placing it than about walking.
        start = np.maximum(np.hypot(x - self.start[0], y - self.start[1]) - START_FLAT_RADIUS, 0)
        t = np.clip(np.minimum(np.minimum(run, dock), start) / FLAT_BLEND, 0, 1)
        return t * t * (3 - 2 * t)

    def _bumps(self):
        """Smooth noise with bumps about feature_size wide and a standard deviation of exactly roughness."""
        t = self.terrain
        field = np.zeros((self.ny, self.nx))
        if t['roughness'] <= 0:
            return field
        rng = np.random.default_rng(t['seed'])
        for cell, amplitude in ((t['feature_size'], 1.), (t['feature_size'] / 2, .5)):
            field += amplitude * _lattice_noise(rng, np.arange(self.nx) * t['resolution'] / cell,
                                                np.arange(self.ny) * t['resolution'] / cell)
        field -= field.mean()
        spread = field.std()
        return field * (t['roughness'] / spread) if spread > 0 else field

    def _build_terrain(self):
        t, c = self.terrain, self.client
        self.res = t['resolution']
        self.nx, self.ny = round(t['size'][0] / self.res) + 1, round(t['size'][1] / self.res) + 1
        self.origin = (-t['size'][0] / 2, -t['size'][1] / 2)
        x, y = np.meshgrid(self.origin[0] + self.res * np.arange(self.nx),
                           self.origin[1] + self.res * np.arange(self.ny))
        self.flat_weight = self._flat_weight(x, y)
        heights = self._bumps() * self.flat_weight
        self.materials = np.zeros((self.ny, self.nx), dtype=int)
        for k, patch in enumerate(self.mud, 1):
            distance = np.hypot(x - patch['center'][0], y - patch['center'][1])
            heights -= patch['depth'] * np.where(distance < patch['radius'],
                                                 .5 + .5 * np.cos(math.pi * distance / patch['radius']), 0)
            self.materials[distance <= patch['radius']] = k
        self.heights = heights + 0.  # array [j, i]; adding 0 turns -0.0 into 0.0
        # Bullet centres a heightfield on the middle of its height range, so the body sits at that height.
        self.low, self.high = float(np.float32(self.heights.min())), float(np.float32(self.heights.max()))
        shape = p.createCollisionShape(p.GEOM_HEIGHTFIELD, meshScale=[self.res, self.res, 1],
                                       heightfieldData=self.heights.ravel().tolist(), numHeightfieldRows=self.nx,
                                       numHeightfieldColumns=self.ny, physicsClientId=c)
        centre = [self.origin[0] + (self.nx - 1) * self.res / 2, self.origin[1] + (self.ny - 1) * self.res / 2,
                  (self.low + self.high) / 2]
        self.terrain_body = p.createMultiBody(0, shape, basePosition=centre, physicsClientId=c)
        self.bodies[self.terrain_body] = {'id': 'terrain', 'name': 'Ground', 'kind': 'terrain'}
        # Bullet multiplies the two contact frictions, so 1.0 here lets a foot's own value be the material's.
        p.changeDynamics(self.terrain_body, -1, lateralFriction=1., restitution=0., physicsClientId=c)
        p.changeVisualShape(self.terrain_body, -1, rgbaColor=GROUND_COLOR, physicsClientId=c)

    def height_at(self, x, y):
        """World z of the terrain surface (bilinear between samples); outside the terrain the edge height."""
        fx = min(max((x - self.origin[0]) / self.res, 0.), self.nx - 1.)
        fy = min(max((y - self.origin[1]) / self.res, 0.), self.ny - 1.)
        i, j = min(int(fx), self.nx - 2), min(int(fy), self.ny - 2)
        u, v = fx - i, fy - j
        h = self.heights
        near = h[j, i] * (1 - u) + h[j, i + 1] * u
        far = h[j + 1, i] * (1 - u) + h[j + 1, i + 1] * u
        return float(near * (1 - v) + far * v)

    def _patch_index(self, x, y):
        """Index of the mud patch under a point (later patches win), or -1 for plain ground."""
        for k in range(len(self.mud) - 1, -1, -1):
            patch = self.mud[k]
            if math.hypot(x - patch['center'][0], y - patch['center'][1]) <= patch['radius']:
                return k
        return -1

    def material_at(self, x, y):
        k = self._patch_index(x, y)
        if k < 0:
            return {'material': 'ground', 'id': None, 'name': 'Ground', 'friction': self.terrain['friction']}
        patch = self.mud[k]
        return {'material': 'mud', 'id': patch['id'], 'name': patch['name'], 'friction': patch['friction']}

    def friction_at(self, x, y):
        k = self._patch_index(x, y)
        return self.terrain['friction'] if k < 0 else self.mud[k]['friction']

    def update_foot_friction(self, body, feet):
        """Give each foot link the friction of the material under it; changeDynamics only runs on a change."""
        result = {}
        for name, link in feet.items():
            state = p.getLinkState(body, link, computeForwardKinematics=1, physicsClientId=self.client)
            friction = self.friction_at(state[0][0], state[0][1])
            if self._foot_friction.get((body, link)) != friction:
                p.changeDynamics(body, link, lateralFriction=friction, physicsClientId=self.client)
                self._foot_friction[(body, link)] = friction
            result[name] = friction
        return result

    def forget_feet(self, body=None):
        """Drop the friction cache; call it when a robot body is rebuilt, since Bullet may reuse its id."""
        for key in [key for key in self._foot_friction if body is None or key[0] == body]:
            del self._foot_friction[key]

    # Static boxes

    def _world_xy(self, u, v):
        """Coop frame (metres from the coop position along its axes) to world x, y."""
        position = self.coop['position']
        return position[0] + u * self._cos - v * self._sin, position[1] + u * self._sin + v * self._cos

    def _add_box(self, kind, ident, name, size, position, quaternion, color=None):
        c = self.client
        half = [s / 2 for s in size]
        color = color or COLORS[kind]
        shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=half, physicsClientId=c)
        visual = p.createVisualShape(p.GEOM_BOX, halfExtents=half, rgbaColor=_rgba(color), physicsClientId=c)
        body = p.createMultiBody(0, shape, visual, position, quaternion, physicsClientId=c)
        p.changeDynamics(body, -1, lateralFriction=SURFACE_FRICTION, restitution=0., physicsClientId=c)
        self.bodies[body] = {'id': ident, 'name': name, 'kind': kind}
        self._boxes.append({'id': ident, 'name': name, 'kind': kind, 'size': [round(s, 4) for s in size],
                            'position': [round(v, 4) for v in position],
                            'quaternion': [round(v, 6) for v in quaternion], 'color': color})
        return body

    def _build_run(self):
        """Posts every post_spacing along the four sides (corners included) with a thin panel between neighbours."""
        run, height, spacing = self.coop['run_size'], self.coop['fence_height'], self.coop['post_spacing']
        hx, hy = run[0] / 2, run[1] / 2
        corners = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
        points = []   # (u, v) of every post in order around the run
        panels = []   # (index of first post, index of next post, side angle in degrees)
        for k in range(4):
            (u0, v0), (u1, v1) = corners[k], corners[(k + 1) % 4]
            count = max(1, math.ceil(math.hypot(u1 - u0, v1 - v0) / spacing - 1e-9))
            first = len(points)
            points += [(u0 + (u1 - u0) * s / count, v0 + (v1 - v0) * s / count) for s in range(count)]
            panels += [(first + s, first + s + 1, 90. * k) for s in range(count)]
        for n, (u, v) in enumerate(points, 1):
            x, y = self._world_xy(u, v)
            self._add_box('post', f'post-{n}', f'Fence post {n}', [POST_SIZE, POST_SIZE, height],
                          [x, y, self.height_at(x, y) + height / 2], _yaw(self.coop['yaw']))
        self._fence_probes = []   # (side, panel centre x, y, z, outward x, y): the self-test shoots rays through these
        for n, (a, b, side) in enumerate(panels, 1):
            (u0, v0), (u1, v1) = points[a], points[b % len(points)]
            (x0, y0), (x1, y1) = self._world_xy(u0, v0), self._world_xy(u1, v1)
            x, y = (x0 + x1) / 2, (y0 + y1) / 2
            base = min(self.height_at(x0, y0), self.height_at(x, y), self.height_at(x1, y1))
            length = math.hypot(u1 - u0, v1 - v0)
            self._add_box('fence', f'fence-{n}', f'Fence panel {n}', [length, PANEL_THICKNESS, height],
                          [x, y, base + height / 2], _yaw(self.coop['yaw'] + side))
            ox, oy = math.sin(math.radians(side)), -math.cos(math.radians(side))  # outward normal in the coop frame
            self._fence_probes.append((round(side / 90), x, y, base + height / 2,
                                       ox * self._cos - oy * self._sin, ox * self._sin + oy * self._cos))
        self.run_corners = [list(self._world_xy(u, v)) for u, v in corners]

    def _build_house(self):
        """A closed box against the run's -x fence with a gable roof (two tilted slabs) on top."""
        run, (sx, sy, sz) = self.coop['run_size'], self.coop['house_size']
        yaw = self.coop['yaw']
        u = min(-run[0] / 2 + POST_SIZE / 2 + HOUSE_GAP + sx / 2, run[0] / 2 - POST_SIZE / 2 - sx / 2)
        x, y = self._world_xy(u, 0)
        base = min(self.height_at(*self._world_xy(u + du * sx / 2, dv * sy / 2))
                   for du in (-1, 0, 1) for dv in (-1, 0, 1))
        self._add_box('house', 'house', 'Chicken house', [sx, sy, sz], [x, y, base + sz / 2], _yaw(yaw))
        # The ridge runs along the longer side; each slab spans from the ridge to an eave that overhangs the wall.
        ridge_turn = 0. if sx >= sy else 90.
        long, short = max(sx, sy), min(sx, sy)
        reach = short / 2 + ROOF_OVERHANG
        slope = math.tan(ROOF_PITCH)
        top = base + sz
        ridge = top + (short / 2) * slope + ROOF_THICKNESS / (2 * math.cos(ROOF_PITCH))
        for side in (1, -1):
            offset = side * reach / 2
            du, dv = (0, offset) if ridge_turn == 0 else (-offset, 0)
            rx, ry = self._world_xy(u + du, dv)
            tilt = _quaternion((1, 0, 0), -side * ROOF_PITCH)
            self._add_box('roof', f'roof-{1 if side > 0 else 2}', 'Chicken house roof',
                          [long + 2 * ROOF_OVERHANG, reach / math.cos(ROOF_PITCH), ROOF_THICKNESS],
                          [rx, ry, ridge - reach / 2 * slope], _multiply(_yaw(yaw + ridge_turn), tilt))

    def _build_dock(self):
        x, y = self.dock['position']
        yaw = self.dock['yaw']
        fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        self.dock_z = self.height_at(x, y)
        stop = self.dock.get('stop_distance', DOCK_STOP_FACE)
        plate = [DOCK_PLATE_REAR + stop, DOCK_PLATE[1], DOCK_PLATE[2]]  # from behind the dock point to the stop block
        reach = plate[0] / 2 - DOCK_PLATE_REAR
        px, py = x + fx * reach, y + fy * reach
        self._add_box('dock', 'dock', 'Charging dock', plate,
                      [px, py, self.height_at(px, py) + DOCK_PLATE[2] / 2], _yaw(yaw))
        reach = stop + DOCK_STOP[0] / 2
        sx, sy = x + fx * reach, y + fy * reach
        self._add_box('dock-stop', 'dock-stop', 'Dock stop block', list(DOCK_STOP),
                      [sx, sy, self.height_at(sx, sy) + DOCK_STOP[2] / 2], _yaw(yaw))

    # Stones

    def _stone_allowed(self, x, y, reach):
        """True when a stone of this longest extent may stand at (x, y): clear of the run, the dock and the start."""
        dx, dy = x - self.coop['position'][0], y - self.coop['position'][1]
        u, v = dx * self._cos + dy * self._sin, -dx * self._sin + dy * self._cos
        grown = STONE_RUN_MARGIN + reach / 2
        if abs(u) < self.coop['run_size'][0] / 2 + grown and abs(v) < self.coop['run_size'][1] / 2 + grown:
            return False
        return all(math.hypot(x - px, y - py) >= STONE_CLEAR + reach for px, py in (self.dock['position'], self.start))

    def _build_stones(self):
        """Loose stones: static boxes sunk about a third into the ground, placed by rejection sampling.

        A stone that finds no free place in STONE_TRIES goes unplaced; stones_requested keeps the shortfall visible.
        """
        s = self.stones
        if not s['count']:
            return
        rng = np.random.default_rng(s['seed'])  # its own generator: the layout does not depend on the terrain seed
        reach_x = self.terrain['size'][0] / 2 - STONE_EDGE
        reach_y = self.terrain['size'][1] / 2 - STONE_EDGE
        # An optional area [x0, y0, x1, y1] concentrates the stones, e.g. on the patrol path; clipped to the terrain.
        x0, y0, x1, y1 = s.get('area') or (-reach_x, -reach_y, reach_x, reach_y)
        x0, x1 = max(x0, -reach_x), min(x1, reach_x)
        y0, y1 = max(y0, -reach_y), min(y1, reach_y)
        for _ in range(s['count']):
            sx, sy = map(float, rng.uniform(s['min_size'], s['max_size'], 2))  # plain floats keep the scene JSON-clean
            height = float(rng.uniform(.4, .8)) * min(sx, sy)
            yaw = float(rng.uniform(0, 360))
            roll, pitch = map(float, rng.uniform(-STONE_TILT, STONE_TILT, 2))
            color = STONE_COLORS[int(rng.integers(len(STONE_COLORS)))]
            reach = math.hypot(sx, sy)
            spot = next(((x, y) for x, y in zip(rng.uniform(x0, x1, STONE_TRIES), rng.uniform(y0, y1, STONE_TRIES))
                         if self._stone_allowed(x, y, reach)), None)
            if spot is None:
                continue
            x, y = float(spot[0]), float(spot[1])
            c, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            ground = min(self.height_at(x + a * sx / 2 * c - b * sy / 2 * sn, y + a * sx / 2 * sn + b * sy / 2 * c)
                         for a, b in ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)))
            tilt = _multiply(_quaternion((0, 1, 0), math.radians(pitch)), _quaternion((1, 0, 0), math.radians(roll)))
            n = len(self._stones) + 1
            body = self._add_box('stone', f'stone-{n}', f'Stone {n}', [sx, sy, height],
                                 [x, y, ground + height * (.5 - STONE_SINK)], _multiply(_yaw(yaw), tilt), color)
            self._stones.append({'body': body, 'x': x, 'y': y, 'reach': reach})
            self._stone_bodies.add(body)

    # Reporting

    def scene(self):
        """The static scene for the browser: terrain samples, materials, boxes, the run and the dock."""
        if self._scene is None:
            t = self.terrain
            self._scene = {
                'terrain': {'size': list(t['size']), 'resolution': self.res, 'rows': self.nx, 'cols': self.ny,
                            'origin': list(self.origin), 'heights': (np.round(self.heights, 4) + 0.).ravel().tolist(),
                            'materials': self.materials.ravel().tolist(), 'mud': [dict(m) for m in self.mud],
                            'friction': t['friction']},
                'boxes': self._boxes,
                'run': {'corners': [[round(v, 4) for v in corner] for corner in self.run_corners],
                        'position': list(self.coop['position']), 'yaw': self.coop['yaw'],
                        'size': list(self.coop['run_size'])},
                'dock': {'position': [round(self.dock['position'][0], 4), round(self.dock['position'][1], 4),
                                      round(self.dock_z, 4)], 'yaw': self.dock['yaw'],
                         'capture_distance': self.dock['capture_distance'],
                         'capture_angle': self.dock['capture_angle']},
            }
        return self._scene

    def config(self):
        t = self.terrain
        return {'size': list(t['size']), 'resolution': self.res, 'samples': self.nx * self.ny, 'rows': self.nx,
                'cols': self.ny, 'roughness': t['roughness'], 'seed': t['seed'], 'mud_patches': len(self.mud),
                'stones': len(self._stones), 'stones_requested': self.stones_requested, 'bodies': len(self.bodies)}

    def remove(self):
        """Remove every body this world created. (Bullet keeps the collision shapes: it refuses to free them.)"""
        for body in list(self.bodies):
            try:
                p.removeBody(body, physicsClientId=self.client)
            except p.error:
                pass
        self.bodies.clear()
        self._boxes = []
        self._stones = []
        self._stone_bodies = set()
        self._scene = None
        self._foot_friction.clear()

    # Self-test

    def _near_structures(self, x, y):
        """True close to the run or the dock, where a ray from above would hit a fence, the house or the dock."""
        dx, dy = x - self.coop['position'][0], y - self.coop['position'][1]
        u, v = dx * self._cos + dy * self._sin, -dx * self._sin + dy * self._cos
        run = self.coop['run_size']
        return (abs(u) < run[0] / 2 + .2 and abs(v) < run[1] / 2 + .2
                or math.hypot(x - self.dock['position'][0], y - self.dock['position'][1]) < .4)

    def _open_points(self, rng, count, on_samples):
        """Random points on open ground, away from the terrain edge (a ray exactly on the edge can miss)."""
        points = []
        for _ in range(count * 100):
            if on_samples:
                x = self.origin[0] + int(rng.integers(1, self.nx - 1)) * self.res
                y = self.origin[1] + int(rng.integers(1, self.ny - 1)) * self.res
            else:
                x = rng.uniform(self.origin[0] + self.res, self.origin[0] + (self.nx - 2) * self.res)
                y = rng.uniform(self.origin[1] + self.res, self.origin[1] + (self.ny - 2) * self.res)
            under_stone = any(math.hypot(x - st['x'], y - st['y']) < st['reach'] / 2 + .01 for st in self._stones)
            if not self._near_structures(x, y) and not under_stone:
                points.append((x, y))
            if len(points) == count:
                break
        return points

    def _twist(self, x, y):
        """How far the four samples around a point are from one plane; bilinear and Bullet's triangles differ by up to a
        quarter of it."""
        i = min(max(int((x - self.origin[0]) / self.res), 0), self.nx - 2)
        j = min(max(int((y - self.origin[1]) / self.res), 0), self.ny - 2)
        h = self.heights
        return abs(h[j, i] - h[j, i + 1] - h[j + 1, i] + h[j + 1, i + 1])

    def _check_surface(self):
        rng = np.random.default_rng(2024)
        errors = []
        for on_samples, count in ((True, 12), (False, 16)):
            points = self._open_points(rng, count, on_samples)
            rays = p.rayTestBatch([[x, y, self.high + 1] for x, y in points], [[x, y, self.low - 1] for x, y in points],
                                  physicsClientId=self.client)
            for (x, y), ray in zip(points, rays):
                limit = 1e-3 if on_samples else 2e-3 + self._twist(x, y) / 4
                error = abs(ray[3][2] - self.height_at(x, y)) if ray[0] == self.terrain_body else float('inf')
                errors.append((error, limit))
        worst = max((error for error, _ in errors), default=0.)
        few = ' (the run and the dock leave little open ground to test)' if len(errors) < 20 else ''
        return check('Terrain heights match the collision surface', all(error <= limit for error, limit in errors),
                     f'{len(errors)} rays, largest difference {worst * 1000:.2f} mm '
                     f'(limit 1 mm at samples, 2 mm between){few}')

    def _check_level(self):
        run = self.coop['run_size']
        x, y = self.dock['position']
        points = [self._world_xy(run[0] * (a / 6 - .5), run[1] * (b / 4 - .5)) for a in range(7) for b in range(5)]
        points += [(px + r * math.cos(a * math.pi / 4), py + r * math.sin(a * math.pi / 4))
                   for px, py, reach in ((x, y, .2), (*self.start, START_FLAT_RADIUS * .9))
                   for r in (0., reach) for a in range(8)]
        # A mud patch may lie on a level area on purpose; its dip is not a fault.
        heights = [self.height_at(*point) for point in points if self.material_at(*point)['material'] != 'mud']
        worst = max((abs(h) for h in heights), default=0.)
        return check('Ground is level in the run, at the dock and at the start', worst < .002,
                     f'largest height {worst * 1000:.2f} mm at {len(heights)} points')

    def _first_hit_past_stones(self, start, end):
        """Body a ray meets first when loose stones are ignored (they are no part of the fence)."""
        length = math.dist(start, end)
        step = [(e - s) / length * .002 for s, e in zip(start, end)]
        for _ in range(int(length / .002)):
            hit = p.rayTest(start, end, physicsClientId=self.client)[0]
            if hit[0] not in self._stone_bodies:
                return hit[0]
            start = [h + d for h, d in zip(hit[3], step)]  # carry on 2 mm beyond the stone's face
        return -1

    def _check_fence(self):
        """A ray from 0.3 m outside to 0.3 m inside every panel must stop at a post or a panel."""
        fence = {body for body, info in self.bodies.items() if info['kind'] in ('post', 'fence')}
        probes = self._fence_probes
        hits = [self._first_hit_past_stones([x + .3 * ox, y + .3 * oy, z], [x - .3 * ox, y - .3 * oy, z])
                for _, x, y, z, ox, oy in probes]
        closed = {side: all(hit in fence for (s, *_), hit in zip(probes, hits) if s == side) for side in range(4)}
        return check('Fence blocks a ray on all four sides', all(closed.values()),
                     f'{sum(closed.values())} of 4 sides closed, {len(probes)} panels tested')

    def _check_materials(self):
        t = self.terrain
        wrong = []
        for k, patch in enumerate(self.mud):
            x, y = patch['center']
            owner = self.mud[self._patch_index(x, y)]  # the centre itself lies in at least this patch
            found = self.material_at(x, y)
            i = min(max(round((x - self.origin[0]) / self.res), 0), self.nx - 1)
            j = min(max(round((y - self.origin[1]) / self.res), 0), self.ny - 1)
            sample = self.origin[0] + i * self.res, self.origin[1] + j * self.res
            lookup = (found['material'], found['id'], found['friction'], self.friction_at(x, y))
            if lookup != ('mud', owner['id'], owner['friction'], owner['friction']) \
                    or self.materials[j, i] != self._patch_index(*sample) + 1:
                wrong.append(patch['id'])
        far = next(((x, y) for x in np.linspace(-t['size'][0] / 2, t['size'][0] / 2, 9)
                    for y in np.linspace(-t['size'][1] / 2, t['size'][1] / 2, 9)
                    if all(math.hypot(x - m['center'][0], y - m['center'][1]) > m['radius'] + .5
                           for m in self.mud)), None)
        if far is not None and (self.material_at(*far)['material'] != 'ground'
                                or self.friction_at(*far) != t['friction']):
            wrong.append('ground')
        return check('Mud and ground lookup', not wrong,
                     f'{len(self.mud)} mud patches' + (', wrong: ' + ', '.join(wrong) if wrong else '')
                     + ('' if far else '; no mud-free ground to test'))

    def _check_roughness(self):
        t = self.terrain
        if t['roughness'] <= 0:
            flat = float(np.abs(self.heights[self.materials == 0]).max())
            return check('Terrain roughness', flat < 1e-9, 'flat ground asked for')
        bumpy = (self.flat_weight >= 1) & (self.materials == 0)
        if bumpy.sum() < 100:
            return check('Terrain roughness', True, 'skipped: almost all ground is kept level')
        spread = float(self.heights[bumpy].std())
        return check('Terrain roughness', abs(spread - t['roughness']) <= t['roughness'] / 2,
                     f"{spread * 1000:.1f} mm measured on {int(bumpy.sum())} samples, "
                     f"{t['roughness'] * 1000:.1f} mm asked")

    def _position(self, body):
        """Where Bullet has a body, or None when it no longer exists."""
        try:
            return p.getBasePositionAndOrientation(body, physicsClientId=self.client)[0]
        except p.error:
            return None

    def _check_bodies(self):
        """The ground and the structures (stones have their own check)."""
        bodies = [body for body in self.bodies if body not in self._stone_bodies]
        alive = sum(self._position(body) is not None for body in bodies)
        return check('Bodies exist in Bullet', alive > 0 and alive == len(bodies), f'{alive} of {len(bodies)} bodies')

    def _check_stones(self):
        asked, placed = self.stones_requested, len(self._stones)
        misplaced = []
        for n, stone in enumerate(self._stones, 1):
            position = self._position(stone['body'])
            if position is None or not self._stone_allowed(position[0], position[1], stone['reach']):
                misplaced.append(n)
        if misplaced:
            return check('Stones are placed as asked', False,
                         f"{len(misplaced)} of {placed} stones missing or inside the run or near the dock or the start "
                         f"(first: stone {misplaced[0]})")
        if placed < asked:
            return check('Stones are placed as asked', False,
                         f'{asked - placed} of {asked} stones could not be placed: no free spot after {STONE_TRIES} '
                         'tries each, so the ground outside the run, the dock and the start is too small')
        detail = f'{placed} stones, none in the run or near the dock or the start' if placed else 'no stones asked for'
        return check('Stones are placed as asked', True, detail)

    def self_test(self):
        return [self._check_surface(), self._check_level(), self._check_fence(), self._check_materials(),
                self._check_roughness(), self._check_bodies(), self._check_stones()]
