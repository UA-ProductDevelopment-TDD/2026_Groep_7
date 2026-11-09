"""Chickens, a fox and a farmer: the animals and people that move around the coop.

Every actor is one kinematic Bullet body (mass 0) built from boxes, spheres and cylinders, so the robot's ToF rays hit
it and its camera image shows it; it is moved by setting its pose. Where it goes is decided by a motion model in plain
Python that knows nothing about Bullet: positions, headings and modes advanced by a function of the time step and
seeded random generators. reset() builds the model again and so repeats exactly the same motion, and the self-test runs
fresh models ahead of the live one without touching the bodies.

Actor axes: x forward, y left, z up, the origin on the ground under the middle of the body. Headings are degrees
counter-clockwise from world +x, like the robot's.
"""
import copy
import math
import random
from bisect import bisect_left, bisect_right

import pybullet as p

from coop.hub import Module, check
from coop.world import HOUSE_GAP, POST_SIZE

POSE_PERIOD = 1 / 60      # s of simulation time between two poses of the Bullet bodies
MAX_SLICE = .05           # s: the motion model integrates no longer slice at once, whatever step it is given
EPSILON = 1e-9
HIDDEN_DEPTH = 60.        # m below the ground where a hidden actor waits: out of reach of a 50 m camera looking down
INSIDE_MARGIN = .08       # m between the middle of a chicken in the run and the fence
HOUSE_MARGIN = .08        # m between the middle of a chicken and the house walls
OUTSIDE_NEAR = .15        # m: the band outside the fence where the other chickens walk starts this far from it ...
OUTSIDE_FAR = 1.0         # ... and ends this far from it
DOCK_CLEAR = .45          # m around the dock that outside chickens keep free
EDGE_CLEAR = .3           # m between an outside chicken and the terrain edge
PAUSE = (.5, 3.)          # s a chicken pecks, from - to
PAUSE_CHANCE = .7         # chance that a chicken that reached its target pecks before it walks on
RETRY_PAUSE = .5          # s a chicken waits after a step that would have left its area
WANDER_REACH = 1.         # m: a chicken picks its next target this close to itself first
MIN_WALK = .1             # m: the shortest walk to a new target
PICK_TRIES = 40           # targets tried before a chicken stands still for a moment
PLACE_TRIES = 200         # spots tried for a chicken at the start
SEGMENT_STEP = .03        # m between the points checked along a walk for the fence and the house
CHICKEN_TURN = 200.       # degrees per second
VISITOR_TURN = 300.
FLEE_TURN = 240.
WALK_ANGLE = 35.          # degrees: a walker turns on the spot until its heading is this close to where it is going
FLEE_FACTOR = 3.          # a fox runs this many times as fast as it walks ...
FLEE_MAX = 1.5            # ... but never faster than this many m/s
FLEE_EDGE = .2            # m from the terrain edge at which a fleeing fox is gone
FLEE_BLEND = .3           # below this length of "away + towards the edge" the fox sidesteps instead
TEST_SECONDS = 120.       # self-test: how long the chickens wander
TEST_SLICE = 1 / 30       # s: step of the self-test runs that need no finer timing
TEST_LIMIT = 600.         # s: the longest the self-test follows one visitor

WHITE, COMB, BEAK = '#f2efe6', '#d0302a', '#e8a33a'
ORANGE, DARK, TIP = '#d4661c', '#3a2a20', '#f4f1ea'
TROUSERS, JACKET, SKIN = '#30343a', '#2f5fa8', '#e0b48f'
IDENTITY = (0., 0., 0., 1.)


def _rgba(color):
    return [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)] + [1.]


def _turned_about_y(angle):
    """Quaternion of a turn about the y axis (radians); it takes the z axis to (sin, 0, cos)."""
    return (0., math.sin(angle / 2), 0., math.cos(angle / 2))


def _part(shape, color, position, quaternion, **size):
    return {'shape': shape, **size, 'position': [round(v, 4) for v in position],
            'quaternion': [round(v, 6) for v in quaternion], 'color': color}


def _box(size, position, color):
    return _part('box', color, position, IDENTITY, size=list(size))


def _sphere(radius, position, color):
    return _part('sphere', color, position, IDENTITY, radius=radius)


def _cylinder(radius, length, position, color, quaternion=IDENTITY):
    return _part('cylinder', color, position, quaternion, radius=radius, length=length)


def _fox_tail():
    """The tail slopes 30° down and back from the rear of the body; its white tip sits on the end."""
    back = (-math.cos(math.radians(30)), 0., -math.sin(math.radians(30)))
    start = (-.21, 0., .27)

    def along(length):
        return [s + d * length for s, d in zip(start, back)]

    turn = _turned_about_y(math.atan2(back[0], back[2]))   # takes the cylinder's z axis along the tail
    return [_cylinder(.04, .32, along(.16), ORANGE, turn), _sphere(.045, along(.32), TIP)]


# The first part of each list is the Bullet base, the others are links on fixed joints. Sizes in metres.
PARTS = {
    'chicken': [
        _box([.22, .14, .13], [0, 0, .13], WHITE),
        _sphere(.045, [.12, 0, .21], WHITE),
        _box([.05, .012, .03], [.12, 0, .26], COMB),
        _box([.03, .02, .015], [.175, 0, .2], BEAK),
        _cylinder(.008, .07, [0, .03, .035], BEAK),
        _cylinder(.008, .07, [0, -.03, .035], BEAK),
    ],
    'fox': [
        _box([.45, .14, .16], [0, 0, .25], ORANGE),
        _box([.14, .11, .10], [.275, 0, .30], ORANGE),
        _box([.03, .03, .05], [.25, .03, .375], ORANGE),
        _box([.03, .03, .05], [.25, -.03, .375], ORANGE),
        _box([.06, .05, .045], [.365, 0, .285], DARK),
        *_fox_tail(),
        *[_box([.04, .04, .17], [x, y, .085], DARK) for x in (.17, -.17) for y in (.045, -.045)],
    ],
    'person': [
        _box([.24, .40, .60], [0, 0, 1.15], JACKET),
        _cylinder(.07, .85, [0, .1, .425], TROUSERS),
        _cylinder(.07, .85, [0, -.1, .425], TROUSERS),
        _box([.08, .08, .55], [0, .24, 1.145], JACKET),
        _box([.08, .08, .55], [0, -.24, 1.145], JACKET),
        _sphere(.11, [0, 0, 1.64], SKIN),
        _cylinder(.05, .10, [0, 0, 1.5], SKIN),  # a neck, so the head (top at 1.75 m) does not float
    ],
}


def _top(kind):
    """Height of the highest point of an actor kind above the ground, a little over for tilted parts."""
    reach = {'box': lambda part: part['size'][2] / 2, 'sphere': lambda part: part['radius'],
             'cylinder': lambda part: part['length'] / 2}
    return max(part['position'][2] + reach[part['shape']](part) for part in PARTS[kind])


def _wrap(angle):
    """An angle in degrees brought into [-180, 180)."""
    return (angle + 180.) % 360. - 180.


def _turn(heading, target, limit):
    """heading turned towards target (degrees) by at most limit degrees."""
    return _wrap(heading + max(-limit, min(limit, _wrap(target - heading))))


def _gap_to_path(point, path):
    """Distance in metres from a point to a polyline."""
    best = math.inf
    for a, b in zip(path, path[1:]):
        length2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
        t = 0. if length2 == 0 else max(0., min(1., ((point[0] - a[0]) * (b[0] - a[0])
                                                     + (point[1] - a[1]) * (b[1] - a[1])) / length2))
        best = min(best, math.dist(point, (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)))
    return best


class _Layout:
    """The coop's geometry in world x, y (metres), and where each kind of chicken may stand."""

    def __init__(self, scenario):
        coop = scenario['coop']
        yaw = math.radians(coop['yaw'])
        self.origin = tuple(coop['position'])
        self.cos, self.sin = math.cos(yaw), math.sin(yaw)
        self.hx, self.hy = coop['run_size'][0] / 2, coop['run_size'][1] / 2
        sx, sy, _ = coop['house_size']
        # Where World._build_house puts the house: against the -u fence, pulled in when it is as long as the run.
        u = min(-self.hx + POST_SIZE / 2 + HOUSE_GAP + sx / 2, self.hx - POST_SIZE / 2 - sx / 2)
        self.house = (u - sx / 2, u + sx / 2, -sy / 2, sy / 2)   # u0, u1, v0, v1 in the coop frame
        self.dock = tuple(scenario['dock']['position'])
        self.reach = tuple(s / 2 for s in scenario['terrain']['size'])   # the terrain is centred on the origin

    def to_uv(self, x, y):
        dx, dy = x - self.origin[0], y - self.origin[1]
        return dx * self.cos + dy * self.sin, -dx * self.sin + dy * self.cos

    def to_xy(self, u, v):
        return self.origin[0] + u * self.cos - v * self.sin, self.origin[1] + u * self.sin + v * self.cos

    def edge_gap(self, x, y):
        """Metres to the nearest terrain edge (negative outside the terrain)."""
        return min(self.reach[0] - abs(x), self.reach[1] - abs(y))

    def exit_normal(self, x, y):
        """Unit vector pointing out through the nearest terrain edge."""
        ex, ey = self.reach
        sides = ((ex - x, (1., 0.)), (ex + x, (-1., 0.)), (ey - y, (0., 1.)), (ey + y, (0., -1.)))
        return min(sides, key=lambda side: side[0])[1]

    def allowed(self, zone, x, y):
        """True where a chicken of this zone ('inside' the run or 'outside' it) may stand."""
        u, v = self.to_uv(x, y)
        if zone == 'inside':
            if abs(u) > self.hx - INSIDE_MARGIN or abs(v) > self.hy - INSIDE_MARGIN:
                return False
            u0, u1, v0, v1 = self.house
            return not (u0 - HOUSE_MARGIN < u < u1 + HOUSE_MARGIN and v0 - HOUSE_MARGIN < v < v1 + HOUSE_MARGIN)
        distance = math.hypot(max(abs(u) - self.hx, 0.), max(abs(v) - self.hy, 0.))
        return (OUTSIDE_NEAR <= distance <= OUTSIDE_FAR and math.dist((x, y), self.dock) >= DOCK_CLEAR
                and self.edge_gap(x, y) >= EDGE_CLEAR)

    def draw(self, rng, zone):
        """A random point in the box around a zone; not necessarily inside the zone itself."""
        if zone == 'inside':
            u = rng.uniform(-self.hx + INSIDE_MARGIN, self.hx - INSIDE_MARGIN)
            v = rng.uniform(-self.hy + INSIDE_MARGIN, self.hy - INSIDE_MARGIN)
        else:
            u = rng.uniform(-self.hx - OUTSIDE_FAR, self.hx + OUTSIDE_FAR)
            v = rng.uniform(-self.hy - OUTSIDE_FAR, self.hy + OUTSIDE_FAR)
        return self.to_xy(u, v)


class _Chicken:
    kind = 'chicken'

    def __init__(self, ident, name, zone, rng):
        self.id, self.name, self.zone, self.rng = ident, name, zone, rng
        self.x = self.y = self.heading = 0.
        self.mode = 'gone'    # until it has found a place; then 'wander' or 'peck'
        self.target = None    # (x, y) it is walking to
        self.pause = 0.       # s of pecking left

    @property
    def present(self):
        return self.mode != 'gone'


class _Visitor:
    def __init__(self, spec):
        self.id, self.kind, self.name = spec['id'], spec['kind'], spec['name']
        self.appear, self.speed, self.loop = spec['appear'], spec['speed'], spec['loop']
        self.flee_distance = spec['flee_distance']
        self.path = []
        for point in spec['path']:   # a repeated point would make a segment with no direction
            if not self.path or math.dist(point, self.path[-1]) > EPSILON:
                self.path.append(tuple(point))
        self.cum = [0.]              # arc length at each point of the path
        for a, b in zip(self.path, self.path[1:]):
            self.cum.append(self.cum[-1] + math.dist(a, b))
        self.total = self.cum[-1]
        self.s, self.direction = 0., 1   # arc length walked, and +1 out along the path or -1 back
        self.x, self.y = self.path[0]
        self.heading = 0.
        self.heading = self.course()
        self.mode = 'waiting'
        self.appeared_at = self.fled_at = self.gone_at = None
        self.flee_from = self.edge_normal = None

    @property
    def present(self):
        return self.mode in ('walk', 'pace', 'flee')

    def segment(self):
        """Index of the path segment under the walker; at a corner, the one it is walking along."""
        index = (bisect_right(self.cum, self.s) if self.direction > 0 else bisect_left(self.cum, self.s)) - 1
        return min(max(index, 0), len(self.cum) - 2)

    def course(self):
        """Heading of the segment under the walker, turned round when walking back."""
        if self.total <= 0:
            return self.heading
        i = self.segment()
        (x0, y0), (x1, y1) = self.path[i], self.path[i + 1]
        return math.degrees(math.atan2(y1 - y0, x1 - x0)) + (0. if self.direction > 0 else 180.)

    def point(self):
        if self.total <= 0:
            return self.path[0]
        i = self.segment()
        t = (self.s - self.cum[i]) / (self.cum[i + 1] - self.cum[i])
        (x0, y0), (x1, y1) = self.path[i], self.path[i + 1]
        return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t


class _Model:
    """Where every chicken and visitor is and what it is doing; advance() is the only thing that changes it."""

    def __init__(self, scenario, layout):
        self.layout = layout
        chickens = scenario['chickens']
        self.speed = chickens['speed']
        self.events = []        # (time, text) not yet collected
        self.chickens = []
        for zone, count, offset in (('inside', chickens['inside'], 0), ('outside', chickens['outside'], 1000)):
            for k in range(count):   # one generator per chicken: adding a chicken does not change the others
                n = len(self.chickens) + 1
                rng = random.Random(chickens['seed'] * 2003 + offset + k)
                self.chickens.append(_Chicken(f'chicken-{n}', f'Chicken {n}', zone, rng))
                self._place(self.chickens[-1])
        self.unplaced = sum(c.mode == 'gone' for c in self.chickens)
        self.visitors = [_Visitor(spec) for spec in scenario['visitors']]
        self.actors = self.chickens + self.visitors

    # Chickens

    def _place(self, c):
        """A start spot and heading, and a first pause so the chickens do not all set off together."""
        for _ in range(PLACE_TRIES):
            x, y = self.layout.draw(c.rng, c.zone)
            if self.layout.allowed(c.zone, x, y):
                c.x, c.y, c.heading = x, y, c.rng.uniform(-180., 180.)
                c.mode, c.pause = 'peck', c.rng.uniform(0., PAUSE[1])
                return

    def _clear(self, zone, a, b):
        """True when the straight walk from a to b stays where the chicken may be (checked every few centimetres)."""
        n = max(1, math.ceil(math.dist(a, b) / SEGMENT_STEP))
        return all(self.layout.allowed(zone, a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)
                   for k in range(1, n))

    def _pick(self, c):
        """A new target: near the chicken at first, so it ambles, then anywhere in its zone. None if boxed in."""
        for attempt in range(PICK_TRIES):
            if attempt < PICK_TRIES // 2:
                reach, angle = c.rng.uniform(MIN_WALK, WANDER_REACH), c.rng.uniform(0., 2 * math.pi)
                x, y = c.x + reach * math.cos(angle), c.y + reach * math.sin(angle)
            else:
                x, y = self.layout.draw(c.rng, c.zone)
            if self.layout.allowed(c.zone, x, y) and self._clear(c.zone, (c.x, c.y), (x, y)):
                return x, y
        return None

    def _chicken(self, c, dt):
        if c.mode == 'peck':
            c.pause -= dt
            if c.pause > 0:
                return
            c.mode, c.target = 'wander', None
        if c.mode != 'wander':
            return
        if c.target is None:
            c.target = self._pick(c)
            if c.target is None:
                c.mode, c.pause = 'peck', RETRY_PAUSE
                return
        tx, ty = c.target
        left = math.hypot(tx - c.x, ty - c.y)
        if left > EPSILON:
            want = math.degrees(math.atan2(ty - c.y, tx - c.x))
            c.heading = _turn(c.heading, want, CHICKEN_TURN * dt)
            if abs(_wrap(want - c.heading)) > WALK_ANGLE:
                return   # still turning on the spot
            move = self.speed * dt
            x, y = (tx, ty) if move >= left else (c.x + (tx - c.x) * move / left, c.y + (ty - c.y) * move / left)
            if not self.layout.allowed(c.zone, x, y):   # a corner cut by a turn: stay put and choose again
                c.mode, c.pause, c.target = 'peck', RETRY_PAUSE, None
                return
            c.x, c.y = x, y
            left = math.hypot(tx - x, ty - y)
        if left <= EPSILON:
            c.target = None
            if c.rng.random() < PAUSE_CHANCE:
                c.mode, c.pause = 'peck', c.rng.uniform(*PAUSE)

    # Visitors

    def _appear(self, v, now):
        v.mode, v.appeared_at, v.s, v.direction = 'walk', now, 0., 1
        v.x, v.y = v.path[0]
        v.heading = v.course()
        where = f' at ({v.x:.1f}, {v.y:.1f})' if v.kind == 'fox' else ''
        self.events.append((now, f'{v.name} appeared{where}'))

    def _leave(self, v, now, text):
        v.mode, v.gone_at = 'gone', now
        self.events.append((now, text))

    def _walk(self, v, now, dt):
        if v.total > 0:
            want = v.course()
            v.heading = _turn(v.heading, want, VISITOR_TURN * dt)
            if abs(_wrap(want - v.heading)) > WALK_ANGLE:
                return   # turning at a corner or at the end of the path
            v.s += v.direction * v.speed * dt
        leaving = False
        if v.direction > 0 and v.s >= v.total:
            v.s = v.total
            if v.loop:
                v.direction, v.mode = -1, 'pace'
            else:
                leaving = True
        elif v.direction < 0 and v.s <= 0:
            v.s, v.direction = 0., 1
        v.x, v.y = v.point()
        if leaving:
            self._leave(v, now, f'{v.name} left')

    def _start_flee(self, v, now, robot):
        v.mode, v.fled_at, v.flee_from = 'flee', now, robot
        v.edge_normal = self.layout.exit_normal(v.x, v.y)   # the way out: through the nearest terrain edge
        self.events.append((now, f'{v.name} runs off'))

    def _flee(self, v, now, dt, robot):
        """Run away from the robot, bending towards the nearest edge; slow down while still facing the wrong way."""
        if robot is not None:
            v.flee_from = robot
        ax, ay = v.x - v.flee_from[0], v.y - v.flee_from[1]
        gap = math.hypot(ax, ay)
        heading = math.radians(v.heading)
        away = (ax / gap, ay / gap) if gap > EPSILON else (math.cos(heading), math.sin(heading))
        nx, ny = v.edge_normal
        sx, sy = away[0] + nx, away[1] + ny
        if math.hypot(sx, sy) < FLEE_BLEND:   # the robot stands between the fox and its edge: sidestep, edge side first
            sx, sy = -away[1], away[0]
            if sx * nx + sy * ny < 0:
                sx, sy = -sx, -sy
        want = math.degrees(math.atan2(sy, sx))
        v.heading = _turn(v.heading, want, FLEE_TURN * dt)
        run = min(FLEE_FACTOR * v.speed, FLEE_MAX) * dt * max(0., math.cos(math.radians(_wrap(want - v.heading))))
        v.x += run * math.cos(math.radians(v.heading))
        v.y += run * math.sin(math.radians(v.heading))
        if self.layout.edge_gap(v.x, v.y) <= FLEE_EDGE:
            self._leave(v, now, f'{v.name} left the terrain')

    def _visitor(self, v, now, dt, robot, scaring):
        if v.mode == 'gone':
            return
        if v.mode == 'waiting':
            if now >= v.appear - EPSILON:
                self._appear(v, now)
            return
        if (v.kind == 'fox' and v.mode != 'flee' and scaring and v.flee_distance > 0
                and math.dist((v.x, v.y), robot) <= v.flee_distance):
            self._start_flee(v, now, robot)   # a person never does: only foxes are afraid
        if v.mode == 'flee':
            self._flee(v, now, dt, robot)
        else:
            self._walk(v, now, dt)

    def advance(self, time, dt, robot=None):
        """Move everything on by dt seconds; time is the simulation time at the end of the slice.

        robot is {'position': [x, y, ...], 'deterring': bool} or None. A long dt is cut into slices of MAX_SLICE.
        """
        where = None if robot is None else (float(robot['position'][0]), float(robot['position'][1]))
        scaring = where is not None and bool(robot.get('deterring'))
        slices = max(1, math.ceil(dt / MAX_SLICE - EPSILON))
        for k in range(slices):
            now = time - dt + dt * (k + 1) / slices
            if self.speed > 0:
                for chicken in self.chickens:
                    self._chicken(chicken, dt / slices)
            for visitor in self.visitors:
                self._visitor(visitor, now, dt / slices, where, scaring)


class Actors(Module):
    kind = 'actors'
    limitations = (
        'Animals and people glide along the ground at a set speed: no legs, wings or arms move, and a pecking chicken '
        'just stands still.',
        'They never collide with or push the robot or each other.',
        'Fences and the house do not stop them: a path that crosses one goes through it, and a chicken facing the fence '
        '(its middle stays 8 cm away) can poke its head through.',
        'Chickens do not react to the robot, the fox or the farmer.',
        "The fox's behaviour is a script, not a model of a real fox: it follows its path, runs off when the deterring "
        'robot comes close and never returns.',
        'The farmer follows his path at a steady pace and ignores the robot.',
        'Each actor stands on the ground under its middle, so on uneven ground a foot can float or sink a few '
        'millimetres.',
        'Poses are updated 60 times a second, and a visitor appears and vanishes instantly: hidden, it is parked 60 m '
        'below the ground.',
        'Shapes are simple blocks, balls and cylinders in flat colours: no fur, feathers or textures, and no infrared '
        'reflection of a real animal.',
    )

    def __init__(self, client, scenario, world):
        super().__init__('actors', 'Chickens & visitors')
        self.client = client
        self.world = world
        self.scenario = {key: copy.deepcopy(scenario[key])
                         for key in ('coop', 'dock', 'terrain', 'chickens', 'visitors')}
        self.layout = _Layout(self.scenario)
        self.bodies = {}        # Bullet body id -> {'id', 'name', 'kind'}
        self._body_of = {}      # actor id -> Bullet body id
        self._shapes = {}       # (kind, part index) -> (collision shape, visual shape)
        self._shown = {}        # actor id -> what its body was last posed to
        self._scene = None
        self._pending = 0.      # s of simulation time since the model was last advanced
        self._posed = None      # simulation time of that
        self._model = self._fresh()
        try:
            for actor in self._model.actors:
                self._build(actor)
        except Exception:
            self.remove()
            raise

    def _fresh(self, chickens=True, visitors=None):
        """A model at its start state (the same seeded places as the live one); the self-test can leave out the
        chickens or choose which visitors take part."""
        scenario = dict(self.scenario)
        if not chickens:
            scenario['chickens'] = {**scenario['chickens'], 'inside': 0, 'outside': 0}
        if visitors is not None:
            scenario['visitors'] = visitors
        return _Model(scenario, self.layout)

    # Bullet bodies

    def _shape(self, kind, index):
        """The collision and visual shape of one part of an actor kind, made once and shared by all actors of it."""
        if (kind, index) not in self._shapes:
            part, c = PARTS[kind][index], self.client
            colour = _rgba(part['color'])
            collision, visual = {}, {}
            if index == 0:   # the base shape sits off the base frame, which is the actor's origin on the ground
                collision = {'collisionFramePosition': part['position'], 'collisionFrameOrientation': part['quaternion']}
                visual = {'visualFramePosition': part['position'], 'visualFrameOrientation': part['quaternion']}
            if part['shape'] == 'box':
                half = [s / 2 for s in part['size']]
                shapes = (p.createCollisionShape(p.GEOM_BOX, halfExtents=half, **collision, physicsClientId=c),
                          p.createVisualShape(p.GEOM_BOX, halfExtents=half, rgbaColor=colour, **visual,
                                              physicsClientId=c))
            elif part['shape'] == 'sphere':
                shapes = (p.createCollisionShape(p.GEOM_SPHERE, radius=part['radius'], **collision, physicsClientId=c),
                          p.createVisualShape(p.GEOM_SPHERE, radius=part['radius'], rgbaColor=colour, **visual,
                                              physicsClientId=c))
            else:
                shapes = (p.createCollisionShape(p.GEOM_CYLINDER, radius=part['radius'], height=part['length'],
                                                 **collision, physicsClientId=c),
                          p.createVisualShape(p.GEOM_CYLINDER, radius=part['radius'], length=part['length'],
                                              rgbaColor=colour, **visual, physicsClientId=c))
            self._shapes[(kind, index)] = shapes
        return self._shapes[(kind, index)]

    @staticmethod
    def _key(actor):
        return actor.x, actor.y, actor.heading, actor.present

    def _pose(self, actor):
        """World position and xyzw quaternion for a body: on the ground, or parked far below it when hidden."""
        z = self.world.height_at(actor.x, actor.y) - (0. if actor.present else HIDDEN_DEPTH)
        half = math.radians(actor.heading) / 2
        return [actor.x, actor.y, z], [0., 0., math.sin(half), math.cos(half)]

    def _build(self, actor):
        """One multibody of mass 0: a base and a fixed-joint link for every other part, each with its own shapes."""
        shapes = [self._shape(actor.kind, i) for i in range(len(PARTS[actor.kind]))]
        links = PARTS[actor.kind][1:]
        position, quaternion = self._pose(actor)
        body = p.createMultiBody(
            0, shapes[0][0], shapes[0][1], position, quaternion,
            linkMasses=[0.] * len(links), linkCollisionShapeIndices=[s[0] for s in shapes[1:]],
            linkVisualShapeIndices=[s[1] for s in shapes[1:]], linkPositions=[part['position'] for part in links],
            linkOrientations=[part['quaternion'] for part in links],
            linkInertialFramePositions=[[0., 0., 0.]] * len(links),
            linkInertialFrameOrientations=[list(IDENTITY)] * len(links), linkParentIndices=[0] * len(links),
            linkJointTypes=[p.JOINT_FIXED] * len(links), linkJointAxis=[[0., 0., 1.]] * len(links),
            physicsClientId=self.client)
        self.bodies[body] = {'id': actor.id, 'name': actor.name, 'kind': actor.kind}
        self._body_of[actor.id] = body
        self._shown[actor.id] = self._key(actor)

    def _apply(self):
        """Pose the Bullet body of every actor that has moved, turned, appeared or left since it was last posed."""
        for actor in self._model.actors:
            body, key = self._body_of.get(actor.id), self._key(actor)
            if body is None or self._shown.get(actor.id) == key:
                continue
            self._shown[actor.id] = key
            position, quaternion = self._pose(actor)
            p.resetBasePositionAndOrientation(body, position, quaternion, physicsClientId=self.client)

    def ignore_collisions_with(self, body):
        """Switch off contacts between every part of every actor and every part of another body (the robot).

        Rays and the camera still see the actors: only the contact solver skips the pairs, so the robot is never pushed.
        """
        others = [-1] + list(range(p.getNumJoints(body, physicsClientId=self.client)))
        for mine in self.bodies:
            for link in [-1] + list(range(p.getNumJoints(mine, physicsClientId=self.client))):
                for other in others:
                    p.setCollisionFilterPair(mine, body, link, other, 0, physicsClientId=self.client)

    # Running

    def reset(self):
        """Back to the start: the same seeded places and modes, visitors hidden until their appear time."""
        self._model = self._fresh()
        self._pending, self._posed = 0., None
        self._shown.clear()
        self._apply()

    def step(self, time, dt, robot=None):
        """Call at every physics step with the simulation time. The model moves on at most every POSE_PERIOD.

        robot is {'position': [x, y, z], 'heading': degrees, 'deterring': bool} or None.
        """
        self._pending += dt
        if self._posed is not None and self._posed - EPSILON <= time < self._posed + POSE_PERIOD - EPSILON:
            return
        self._model.advance(time, self._pending, robot)
        self._pending, self._posed = 0., time
        self._apply()

    def pop_events(self):
        """(time, text) of what happened since the last call, oldest first."""
        events, self._model.events = self._model.events, []
        return [(round(time, 4), text) for time, text in events]

    # Reporting

    def states(self):
        """Where every actor is now. A hidden one keeps its place on the ground but has present False."""
        return [{'id': a.id, 'kind': a.kind, 'name': a.name,
                 'position': [round(a.x, 4), round(a.y, 4), round(self.world.height_at(a.x, a.y), 4)],
                 'heading': round(a.heading, 2), 'mode': a.mode, 'present': a.present} for a in self._model.actors]

    def fox(self):
        """The first fox's record, or None when the scenario has no fox. Times are simulation seconds or None."""
        v = next((v for v in self._model.visitors if v.kind == 'fox'), None)
        if v is None:
            return None

        def rounded(t):
            return None if t is None else round(t, 4)

        return {'id': v.id, 'present': v.present, 'mode': v.mode, 'appeared_at': rounded(v.appeared_at),
                'fled_at': rounded(v.fled_at), 'gone_at': rounded(v.gone_at)}

    def scene(self):
        """The figures and the visitors' paths for the browser; part positions are relative to the actor's origin."""
        if self._scene is None:
            height = self.world.height_at
            self._scene = {
                'actors': [{'id': a.id, 'kind': a.kind, 'name': a.name, 'parts': copy.deepcopy(PARTS[a.kind])}
                           for a in self._model.actors],
                'paths': [{'id': v['id'], 'kind': v['kind'], 'loop': v['loop'],
                           'points': [[round(x, 4), round(y, 4), round(height(x, y), 4)] for x, y in v['path']]}
                          for v in self.scenario['visitors']],
            }
        return self._scene

    def config(self):
        c = self.scenario['chickens']
        return {'chickens_inside': c['inside'], 'chickens_outside': c['outside'],
                'chickens_unplaced': self._model.unplaced, 'chicken_speed': c['speed'], 'seed': c['seed'],
                'visitors': len(self._model.visitors), 'bodies': len(self.bodies)}

    def remove(self):
        """Remove every body this module created. (Bullet keeps the collision shapes: it refuses to free them.)"""
        for body in list(self.bodies):
            try:
                p.removeBody(body, physicsClientId=self.client)
            except p.error:
                pass
        self.bodies.clear()
        self._body_of.clear()
        self._shown.clear()

    # Self-test

    def _position(self, body):
        """Where Bullet has a body, or None when it no longer exists."""
        if body is None:
            return None
        try:
            return p.getBasePositionAndOrientation(body, physicsClientId=self.client)[0]
        except p.error:
            return None

    @staticmethod
    def _simulate(model, start, seconds, observe=None, robot=None, until=None, dt=TEST_SLICE):
        """Advance a model from simulation time `start`. observe(time) runs after each slice, robot(model) gives the
        robot for the next one, and the run ends early once until() is true. Returns the end time."""
        time = start
        for _ in range(round(seconds / dt)):
            time += dt
            model.advance(time, dt, robot(model) if robot else None)
            if observe:
                observe(time)
            if until and until():
                break
        return time

    def _check_bodies(self):
        actors = self._model.actors
        alive = sum(self._position(self._body_of.get(a.id)) is not None for a in actors)
        return check('Every actor has a body in Bullet', alive == len(actors),
                     f'{alive} of {len(actors)} actors' if actors else 'no chickens or visitors in this scenario')

    def _check_house(self):
        """The footprint chickens keep out of is the house the world built."""
        body = next((b for b, info in getattr(self.world, 'bodies', {}).items() if info['kind'] == 'house'), None)
        position = self._position(body)
        name = "House footprint matches the world's house"
        if position is None:
            return check(name, True, 'skipped: the world has no house')
        u, v = self.layout.to_uv(position[0], position[1])
        u0, u1, v0, v1 = self.layout.house
        error = max(abs(u - (u0 + u1) / 2), abs(v - (v0 + v1) / 2))
        return check(name, error < .001, f'centres {error * 1000:.2f} mm apart')

    def _check_chickens(self):
        """One long run of fresh chickens: where they walk, how fast, and that they walk at all."""
        model, layout = self._fresh(visitors=[]), self.layout
        placed = [c for c in model.chickens if c.present]
        inside = [c for c in placed if c.zone == 'inside']
        outside = [c for c in placed if c.zone == 'outside']
        u0, u1, v0, v1 = layout.house
        worst = {'fence': math.inf, 'house': math.inf, 'near': math.inf, 'far': 0., 'dock': math.inf,
                 'edge': math.inf, 'speed': 0.}
        last = {c.id: (c.x, c.y) for c in placed}
        walked = {c.id: 0. for c in placed}

        def observe(time):
            for c in placed:
                step = math.dist((c.x, c.y), last[c.id])
                worst['speed'] = max(worst['speed'], step / POSE_PERIOD)
                walked[c.id] += step
                last[c.id] = c.x, c.y
                u, v = layout.to_uv(c.x, c.y)
                if c.zone == 'inside':
                    worst['fence'] = min(worst['fence'], layout.hx - abs(u), layout.hy - abs(v))
                    worst['house'] = min(worst['house'], max(u0 - u, u - u1, v0 - v, v - v1))
                else:
                    gap = math.hypot(max(abs(u) - layout.hx, 0.), max(abs(v) - layout.hy, 0.))
                    worst['near'], worst['far'] = min(worst['near'], gap), max(worst['far'], gap)
                    worst['dock'] = min(worst['dock'], math.dist((c.x, c.y), layout.dock))
                    worst['edge'] = min(worst['edge'], layout.edge_gap(c.x, c.y))

        self._simulate(model, 0., TEST_SECONDS, observe, dt=POSE_PERIOD)
        tol, speed, asked = 1e-9, model.speed, len(model.chickens)
        idle = [n for n, metres in walked.items() if metres < .1 * speed * TEST_SECONDS]
        cm = lambda metres: f'{metres * 100:.0f}'
        why = '' if len(placed) == asked else ': no free spot in the run beside the house, or in the band outside it'
        return [
            check('Every chicken finds a place to stand', len(placed) == asked, f'{len(placed)} of {asked} chickens{why}'),
            check('Chickens inside stay in the run and out of the house',
                  worst['fence'] >= INSIDE_MARGIN - tol and worst['house'] >= HOUSE_MARGIN - tol,
                  f'{len(inside)} chickens for {TEST_SECONDS:.0f} s: closest to the fence {cm(worst["fence"])} cm, to '
                  f'the house {cm(worst["house"])} cm' if inside else 'skipped: no chickens inside the run'),
            check('Chickens outside stay outside the run and away from the dock',
                  OUTSIDE_NEAR - tol <= worst['near'] and worst['far'] <= OUTSIDE_FAR + tol
                  and worst['dock'] >= DOCK_CLEAR - tol and worst['edge'] >= EDGE_CLEAR - tol,
                  f'{len(outside)} chickens for {TEST_SECONDS:.0f} s: {cm(worst["near"])}-{cm(worst["far"])} cm from '
                  f'the fence, {cm(worst["dock"])} cm from the dock, {cm(worst["edge"])} cm from the terrain edge'
                  if outside else 'skipped: no chickens outside the run'),
            check('Chickens walk no faster than their speed', worst['speed'] <= speed + tol,
                  f'fastest {worst["speed"]:.3f} m/s of {speed:.3f} m/s'),
            check('Chickens keep wandering', not idle,
                  f'every chicken walked at least a tenth of the way it could ({TEST_SECONDS:.0f} s at {speed} m/s)'
                  if not idle else f'{len(idle)} of {len(placed)} chickens hardly moved: boxed in?'),
        ]

    def _check_appear(self):
        """A visitor is hidden until its appear time, then stands at the start of its path."""
        late, hidden = [], 0
        for spec in self.scenario['visitors']:
            model = self._fresh(False, [spec])
            v, log = model.visitors[0], []
            first = spec['path'][0]
            self._simulate(model, max(0., spec['appear'] - 3 * TEST_SLICE), 6 * TEST_SLICE,
                           lambda time: log.append((time, v.present, v.x, v.y)))
            before = [entry for entry in log if entry[0] < spec['appear'] - EPSILON]
            after = [entry for entry in log if entry[0] >= spec['appear'] - EPSILON]
            hidden += bool(before)
            # The first slice at or after the appear time shows it, exactly on the first point of its path.
            if (any(entry[1] for entry in before) or not after or not after[0][1]
                    or math.dist(after[0][2:], first) > 1e-6
                    or not spec['appear'] - EPSILON <= v.appeared_at <= after[0][0] + EPSILON):
                late.append(spec['name'])
        return check('Visitors stay hidden until they appear', not late,
                     f'{len(self.scenario["visitors"])} visitors, {hidden} of them hidden at the start' if not late
                     else 'wrong for ' + ', '.join(late))

    def _check_paths(self):
        """Every visitor stays on its path, never walks faster than its speed and ends as its loop setting says."""
        off, fastest, capped, wrong = 0., 0., False, []
        for spec in self.scenario['visitors']:
            model = self._fresh(False, [spec])
            v = model.visitors[0]
            # The walk plus half a second to turn at every corner, and the way back for a visitor that paces.
            span = (v.total / spec['speed'] + .5 * len(spec['path']) + 2.) * (2 if spec['loop'] else 1)
            capped = capped or span > TEST_LIMIT
            seen = {'off': 0., 'speed': 0., 'back': False, 'count': 0, 'last': (v.x, v.y)}

            def observe(time):
                seen['count'] += 1
                seen['speed'] = max(seen['speed'], math.dist((v.x, v.y), seen['last']) / TEST_SLICE)
                seen['last'] = v.x, v.y
                seen['back'] = seen['back'] or v.direction < 0
                if seen['count'] % 4 == 0:   # an exact walk is on the path to rounding error: a sample is enough
                    seen['off'] = max(seen['off'], _gap_to_path((v.x, v.y), spec['path']))

            self._simulate(model, spec['appear'] - TEST_SLICE, min(span, TEST_LIMIT), observe)
            off, fastest = max(off, seen['off']), max(fastest, seen['speed'] / spec['speed'])
            ended = (v.mode == 'pace' and seen['back'] if spec['loop']
                     else v.mode == 'gone' and math.dist((v.x, v.y), spec['path'][-1]) < 1e-6)
            if seen['off'] > 1e-6 or seen['speed'] > spec['speed'] + 1e-6 or (not ended and span <= TEST_LIMIT):
                wrong.append(spec['name'])
        note = f' (only the first {TEST_LIMIT:.0f} s of a long path were followed)' if capped else ''
        return check('Visitors follow their paths', not wrong,
                     f'{len(self.scenario["visitors"])} visitors, never more than {off * 1000:.3f} mm off the path, '
                     f'at most {fastest:.0%} of their speed{note}' if not wrong else 'wrong for ' + ', '.join(wrong))

    def _check_fox(self):
        """A deterring robot beside the fox sends it off the terrain; one that is idle or far away does not."""
        foxes = [spec for spec in self.scenario['visitors'] if spec['kind'] == 'fox']
        ran, calm = 'A deterring robot next to the fox makes it run off the terrain', 'The fox ignores a robot that is idle or far away'
        if not foxes:
            return [check(ran, True, 'skipped: no fox in this scenario'), check(calm, True, 'skipped: no fox in this scenario')]
        failed, scared, notes, times = [], [], [], []
        for spec in foxes:
            model = self._fresh(False, [spec])
            v, fd = model.visitors[0], spec['flee_distance']
            if fd <= 0:
                notes.append(f'{spec["name"]} is never scared (flee distance 0)')
                continue
            time = self._simulate(model, spec['appear'] - TEST_SLICE, 3 * TEST_SLICE)   # it appears, then walks a second
            time = self._simulate(model, time, 1.)
            # An idle robot right beside the fox, then a deterring one just outside its flee distance (both follow it).
            time = self._simulate(model, time, 2., robot=lambda m: {'position': (v.x + .1, v.y), 'deterring': False})
            time = self._simulate(model, time, 2., robot=lambda m: {'position': (v.x + fd + 1., v.y), 'deterring': True})
            if v.mode == 'flee' or v.fled_at is not None:
                scared.append(spec['name'])
            if not v.present:
                notes.append(f'{spec["name"]} left before the robot came close')
                continue
            normal = self.layout.exit_normal(v.x, v.y)   # worst case: the robot stands in the way out
            point = (v.x + normal[0] * fd / 2, v.y + normal[1] * fd / 2)
            fast = min(FLEE_FACTOR * spec['speed'], FLEE_MAX)
            seen = {'speed': 0., 'last': (v.x, v.y)}

            def observe(time):
                seen['speed'] = max(seen['speed'], math.dist((v.x, v.y), seen['last']) / TEST_SLICE)
                seen['last'] = v.x, v.y

            limit = min(TEST_LIMIT, 4 * math.hypot(*self.layout.reach) / fast + 10.)
            time = self._simulate(model, time, limit, observe, lambda m: {'position': point, 'deterring': True},
                                  lambda: v.mode == 'gone')
            gone = v.mode == 'gone' and v.fled_at is not None
            self._simulate(model, time, 5., robot=lambda m: {'position': (v.x, v.y), 'deterring': True})
            if not (gone and v.gone_at >= v.fled_at and self.layout.edge_gap(v.x, v.y) <= FLEE_EDGE + 1e-9
                    and seen['speed'] <= fast + 1e-6 and v.mode == 'gone' and not v.present):
                failed.append(spec['name'])
            elif gone:
                times.append(v.gone_at - v.fled_at)
        detail = '; '.join(notes) or ''
        return [
            check(ran, not failed, ('wrong for ' + ', '.join(failed) if failed else
                                    f'gone {max(times):.1f} s after it ran off' if times else 'skipped') + (f' ({detail})' if detail else '')),
            check(calm, not scared, 'wrong for ' + ', '.join(scared) if scared else 'no flee without a deterring robot '
                  'within its flee distance'),
        ]

    def _check_person(self):
        """A person never runs off, even when the robot deterring beside it would send a fox away."""
        people = [spec for spec in self.scenario['visitors'] if spec['kind'] == 'person']
        name = 'A person does not flee from a deterring robot'
        if not people:
            return check(name, True, 'skipped: no person in this scenario')
        ran = []
        for spec in people:
            model = self._fresh(False, [{**spec, 'flee_distance': 5.}])
            v = model.visitors[0]
            time = self._simulate(model, spec['appear'] - TEST_SLICE, 3 * TEST_SLICE)
            self._simulate(model, time, 10., robot=lambda m: {'position': (v.x + .2, v.y), 'deterring': True})
            if v.fled_at is not None or v.mode == 'flee':
                ran.append(spec['name'])
        return check(name, not ran, 'wrong for ' + ', '.join(ran) if ran else f'{len(people)} people, 10 s with a '
                     'deterring robot 20 cm away')

    def _check_repeat(self):
        """Two fresh models given the same steps end in exactly the same state."""
        ends = []
        for _ in range(2):
            model = self._fresh()
            self._simulate(model, 0., 30.)
            ends.append([(a.x, a.y, a.heading, a.mode) for a in model.actors])
        return check('The same seed gives the same motion', ends[0] == ends[1], f'{len(ends[0])} actors after 30 s')

    def _check_poses(self):
        """The live bodies stand where the live model puts them (on the ground, or parked below it)."""
        off = []
        for actor in self._model.actors:
            at, want = self._position(self._body_of.get(actor.id)), self._pose(actor)[0]
            if at is None or max(abs(a - b) for a, b in zip(at, want)) > 1e-6:
                off.append(actor.name)
        return check('Bullet bodies stand where the motion model puts them', not off,
                     f'{len(self._model.actors)} actors' if not off else 'wrong for ' + ', '.join(off))

    def _check_rays(self):
        """A ray from just above each visible actor, straight down its middle, hits that actor's body."""
        name = 'Rays hit the actors that are present'
        live = [a for a in self._model.actors if a.present and self._position(self._body_of.get(a.id)) is not None]
        if not live:
            return check(name, True, 'skipped: nobody is present right now')
        missed = []
        for a in live:
            ground = self.world.height_at(a.x, a.y)
            hit = p.rayTest([a.x, a.y, ground + _top(a.kind) + .05], [a.x, a.y, ground - .3],
                            physicsClientId=self.client)[0][0]
            if hit != self._body_of[a.id]:
                missed.append(a.name)
        return check(name, not missed, f'{len(live)} actors' if not missed else 'missed: ' + ', '.join(missed))

    def self_test(self):
        return [self._check_bodies(), self._check_house(), *self._check_chickens(), self._check_appear(),
                self._check_paths(), *self._check_fox(), self._check_person(), self._check_repeat(),
                self._check_poses(), self._check_rays()]
