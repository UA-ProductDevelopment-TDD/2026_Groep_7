"""Simulated sensors of the coop robot: an ESP32-S3 camera, VL53L0X time-of-flight distance sensors, an MPU6050 IMU.

Each sensor is a hub module fixed to one robot link (frames.Mount), measures in simulation time at its own rate and
publishes a JSON-safe reading. Every reading has 'type', 'time' (simulation seconds) and 'pose' (where the sensor is
and which way it looks). The SensorSuite builds the sensors of a scenario and drives them from the physics loop.
"""
import copy
import math
import zlib
from time import perf_counter

import numpy as np
import pybullet as p

from coop import frames, png
from coop.hub import TOPIC, Module, check

EPSILON = 1e-9         # seconds of tolerance when comparing simulation times
RECASTS = 3            # how often a ray that hit the robot itself is cast again from just past the hit
SKIN = .002            # metres past an own-body hit where the next cast starts
LIGHT = [.4, -.3, 1]   # camera light direction: from above, so surfaces facing differently get different shades
NEAR = .01             # camera near plane, metres
FAR_DEPTH = 1 - 1e-6   # depth-buffer values from here up are the far plane: nothing was hit
MAX_SELF = .3          # largest share of a camera image that may show the robot itself
POSE_SLACK = .05       # metres a ToF origin may lie outside the body of the link it is mounted on


def vec(values, digits=5):
    return [round(float(v), digits) for v in values]


class Sensor(Module):
    """Base of all sensors: schedule, mounting, publishing. Subclasses implement measure()."""
    kind = 'sensor'
    type = ''
    prefix = 'sensors'

    def __init__(self, definition, robot, hub, rng):
        super().__init__(definition['id'], definition['name'])
        if definition['link'] not in robot.links:
            raise ValueError(f"Sensor {definition['name']}: link {definition['link']} is not part of this robot")
        self.topic = f'{self.prefix}/{self.id}'
        if not TOPIC.fullmatch(self.topic):
            raise ValueError(f"Sensor {definition['name']}: the id {self.id} needs lower-case letters, digits, - or _")
        self.definition, self.robot, self.hub, self.rng = definition, robot, hub, rng
        self.client = robot.client
        self.mount = frames.Mount(robot, definition['link'], definition.get('position', (0, 0, 0)),
                                  definition.get('rotation', (0, 0, 0)))
        self.period = 1 / definition['rate']
        self.publishes = (self.topic,)
        self.reading = {}
        self.error = None  # what went wrong in the latest measurement made by a SensorSuite, if anything
        self.next = None   # simulation time of the next scheduled measurement; None until the first one
        self.last = None   # simulation time of the latest measurement

    def status(self):
        return 'error' if self.error else 'ok'

    def config(self):
        return copy.deepcopy(self.definition)

    def due(self, time):
        """Rates count simulation seconds. The first call is always due, and so is one after time was reset."""
        return self.next is None or time >= self.next - EPSILON or time < self.last - EPSILON

    def schedule(self, time):
        if self.next is None or time < self.last - EPSILON or time - self.next > self.period:
            self.next = time + self.period  # first measurement, time went back, or the caller fell behind
        else:
            self.next += self.period        # a fixed grid, so late steps do not make the rate drift

    def update(self, time, dt):
        """Measure now, keep the reading and publish it. dt is None when physics is not stepping.

        A measurement that was due moves the schedule on; an extra one (a refresh while paused) leaves it alone.
        """
        if self.due(time):
            self.schedule(time)  # before measuring, so a failing sensor is not retried at every physics step
        self.last = time
        reading = {'type': self.type, 'time': round(float(time), 6), **self.measure(time, dt), 'pose': self.pose()}
        self.reading = reading
        self.store(reading)
        self.hub.publish(self.topic, reading, self.id)
        return reading

    def measure(self, time, dt):
        raise NotImplementedError

    def store(self, reading):
        """Hook for data too big for a message (camera frames)."""

    def pose(self):
        position, forward, _, up = self.mount.axes()
        return {'position': vec(position), 'forward': vec(forward), 'up': vec(up)}


class CameraSensor(Sensor):
    """ESP32-S3 camera, rendered by Bullet's software renderer. 'fov' is the vertical field of view.

    By day the picture is the render. At night it is darkened to moonlight and, with the infrared LEDs on, lit by
    them instead, falling off with distance. The latest picture with its depth and segmentation is kept in `shot`.
    """
    type = 'camera'
    prefix = 'camera'
    NIGHT_NOISE = .02  # standard deviation of the sensor noise at night, as a share of full brightness
    # Share of its brightness that a surface shows when it is ir_range metres away. The render shades surfaces to
    # about .55 (a white surface facing the camera), so .3 puts such a surface at .17: just above the detector's
    # default minimum brightness (.15). At 1.5 times that distance the light is 2.25 times weaker: well below it.
    IR_AT_RANGE = .3
    VISIBLE = .15      # brightness from which the detector's default settings see a pixel (config: min_brightness)
    LUMA = np.array([.299, .587, .114], np.float32)  # weights of red, green and blue in the brightness of a pixel
    limitations = (
        "Bullet's software renderer: flat colours, no textures, shadows, motion blur, rolling shutter or lens "
        'distortion.',
        'Night: moonlight is a plain factor on the daylight image, and noise is added at night only.',
        'Infrared: two LEDs next to the lens are one point source, with no beam pattern, hot spot, glare or '
        'overexposure; surfaces reflect infrared like visible light (real grass and fur do not), and the image '
        'is grey.',
        'Recognising a fox, chicken or human is not part of the camera: a separate detector module reads its frames.',
    )

    def __init__(self, definition, robot, hub, rng, environment=None):
        super().__init__(definition, robot, hub, rng)
        self.projection = p.computeProjectionMatrixFOV(definition['fov'], definition['width'] / definition['height'],
                                                       NEAR, definition['range'])
        self.environment = copy.copy(environment)  # the scenario's 'environment'; None means day
        self.frame = 0
        self.png = b''
        self.shot = None  # the latest frame as processed: see develop()
        tan_up = math.tan(math.radians(definition['fov']) / 2)
        tan_left = tan_up * definition['width'] / definition['height']
        across = ((np.arange(definition['width']) + .5) / definition['width'] * 2 - 1) * tan_left
        down = ((np.arange(definition['height']) + .5) / definition['height'] * 2 - 1) * tan_up
        # Metres along a pixel's ray per metre of depth: the infrared LEDs light by distance, the depth is along the axis.
        self.stretch = np.sqrt(1 + across[None, :] ** 2 + down[:, None] ** 2).astype(np.float32)

    def lighting(self):
        """'day', 'night' (moonlight only) or 'night-ir' (infrared LEDs on)."""
        environment = self.environment
        if not environment or environment.get('time_of_day', 'day') != 'night':
            return 'day'
        return 'night-ir' if environment.get('ir_light') else 'night'

    def develop(self, shot, rng=None):
        """What the camera outputs for a raw render: rgb, depth, segmentation, brightness (luma 0-1) and lighting.

        Day: the render. Night: its colours times the moonlight, or with infrared a grey image whose brightness
        falls with the squared distance. Gaussian noise is added, and pixels that hit nothing stay black.
        """
        lighting, rgb = self.lighting(), shot['rgb']
        if lighting != 'day':
            rng, e = rng or self.rng, self.environment
            colour = rgb.astype(np.float32) / 255
            if lighting == 'night-ir':
                reach = e['ir_range'] / np.maximum(shot['depth'] * self.stretch, NEAR)  # no hit: infinite depth, zero
                light = np.minimum(1., e['moonlight'] + self.IR_AT_RANGE * reach * reach)
                picture = ((colour @ self.LUMA) * light)[:, :, None]  # one grey value per pixel, noise included
            else:
                picture = colour * e['moonlight']
            picture = np.clip(picture + rng.standard_normal(picture.shape, np.float32) * self.NIGHT_NOISE, 0, 1)
            picture = np.where(np.isfinite(shot['depth'])[:, :, None], picture, 0)
            rgb = np.ascontiguousarray(np.broadcast_to((picture * 255 + .5).astype(np.uint8), colour.shape))
        brightness = (rgb.astype(np.float32) @ self.LUMA) / 255
        return {'rgb': rgb, 'depth': shot['depth'], 'segmentation': shot['segmentation'], 'brightness': brightness,
                'lighting': lighting}

    def capture(self):
        """Render one image now: rgb uint8 HxWx3, depth float32 metres (inf = nothing hit), segmentation int32."""
        d = self.definition
        position, quaternion = self.mount.frame()
        forward, up = frames.rotate(quaternion, [1, 0, 0]), frames.rotate(quaternion, [0, 0, 1])
        view = p.computeViewMatrix(position, [position[i] + forward[i] for i in range(3)], up)
        width, height, rgba, depth, mask = p.getCameraImage(d['width'], d['height'], view, self.projection,
                                                            lightDirection=LIGHT, renderer=p.ER_TINY_RENDERER,
                                                            physicsClientId=self.client)
        rgb = np.ascontiguousarray(np.asarray(rgba, np.uint8).reshape(height, width, 4)[:, :, :3])
        buffer = np.asarray(depth, np.float64).reshape(height, width)
        far = d['range']
        metres = far * NEAR / (far - (far - NEAR) * buffer)
        metres[buffer >= FAR_DEPTH] = np.inf
        return {'rgb': rgb, 'depth': metres.astype(np.float32),
                'segmentation': np.asarray(mask, np.int32).reshape(height, width),
                'position': list(position), 'quaternion': list(quaternion)}

    def measure(self, time, dt):
        raw = self.capture()
        shot = self.develop(raw)
        self.frame += 1
        # The camera pose goes with the frame, so what it shows can be traced back to the world (coverage metric).
        self.shot = {'frame': self.frame, **shot, 'position': raw['position'], 'quaternion': raw['quaternion']}
        self.png = png.encode(shot['rgb'])  # the picture people and outside programs see is the processed one
        mask, depth = shot['segmentation'], shot['depth']
        bodies, counts = np.unique(mask[mask >= 0], return_counts=True)
        finite = depth[np.isfinite(depth)]
        d = self.definition
        return {'frame': self.frame, 'width': d['width'], 'height': d['height'], 'fov': d['fov'], 'range': d['range'],
                'lighting': shot['lighting'], 'brightness': round(float(shot['rgb'].mean()) / 255, 4),
                'nearest': round(float(finite.min()), 4) if finite.size else None,
                'visible': {str(int(body)): int(count) for body, count in zip(bodies, counts)},
                'self_pixels': round(float((mask == self.robot.robot).mean()), 4),
                'url': f'/api/hub/frame/{self.id}.png?f={self.frame}'}

    def store(self, reading):
        self.hub.store_frame(self.id, self.png, reading)

    def self_test(self):
        d = self.definition
        started = perf_counter()
        try:
            shot = self.capture()
        except Exception as error:
            return [check('Renders a frame now', False, f'{type(error).__name__}: {error}')]
        milliseconds = (perf_counter() - started) * 1000
        rgb, depth, mask = shot['rgb'], shot['depth'], shot['segmentation']  # the render, before day or night
        own, finite = float((mask == self.robot.robot).mean()), float(np.isfinite(depth).mean())
        colours = len(np.unique(rgb.reshape(-1, 3), axis=0))
        advice = '' if own < MAX_SELF else ': move the camera forward or up, out of the body'
        checks = [
            check('Renders a frame now', True, f'{milliseconds:.0f} ms for {d["width"]}x{d["height"]} pixels'),
            check('Image has the configured size', rgb.shape[:2] == (d['height'], d['width']),
                  f'{rgb.shape[1]}x{rgb.shape[0]}, configured {d["width"]}x{d["height"]}'),
            check('Image is not a single flat colour', colours > 1, f'{colours} different colours'),
            check('Some pixel has a finite depth', finite > 0, f'{finite:.0%} of the pixels hit something'),
            check('Own robot fills less than 30 % of the image', own < MAX_SELF,
                  f'{own:.0%} of the pixels show the robot' + advice),
        ]
        picture = self.develop(shot, np.random.default_rng(0))  # its own noise, so a test does not change later frames
        if picture['lighting'] != 'day':
            lit = float((picture['brightness'] >= self.VISIBLE).mean())
            advice = '' if lit > 0 else ': switch the infrared light on or raise the moonlight'
            checks.append(check('Night image is bright enough to see by', lit > 0,
                                f"{lit:.0%} of the pixels reach {self.VISIBLE} ({picture['lighting']}){advice}"))
        return checks


def ray_layout(rays, cone):
    """Unit directions in sensor axes (x forward, y left, z up): the centre ray, then rings up to half the cone."""
    directions = [[1., 0., 0.]]
    others = rays - 1
    if others:
        rings = math.ceil((-1 + math.sqrt(1 + 2 * others)) / 2)  # rings of 4, 8, 12... rays are enough for the others
        weights = rings * (rings + 1) // 2
        counts = [others * i // weights for i in range(1, rings + 1)]  # rays per ring grow with its circumference
        for i in range(others - sum(counts)):
            counts[-1 - i] += 1
        for ring, count in enumerate(counts, 1):
            angle = math.radians(cone) / 2 * ring / rings
            for j in range(count):
                azimuth = 2 * math.pi * (j + (.5 if ring % 2 == 0 else 0)) / count  # azimuth 0 = left, 90 = up
                directions.append([math.cos(angle), math.sin(angle) * math.cos(azimuth),
                                   math.sin(angle) * math.sin(azimuth)])
    return np.array(directions)


class TofSensor(Sensor):
    """VL53L0X: a cone of rays from one point. Reports the nearest hit within range, or None."""
    type = 'tof'
    limitations = (
        'A cone of perfect rays: no surface reflectivity, sunlight interference or multipath.',
        'Gaussian noise proportional to the distance.',
        'Nothing is reported beyond the range (the real sensor returns an out-of-range code).',
    )

    def __init__(self, definition, robot, hub, rng):
        super().__init__(definition, robot, hub, rng)
        self.layout = ray_layout(definition['rays'], definition['cone'])

    def trace(self, origin, directions):
        """(nearest hit per ray as (body, link, distance, point) or None, rays cast again, rays that gave up).

        A ray that hits the robot's own body starts again from just past the hit, so the sensor never measures its own
        robot; after RECASTS tries the ray is dropped rather than reported.
        """
        reach = self.definition['range']
        hits = [None] * len(directions)
        travelled = np.zeros(len(directions))
        pending, recast, blocked = list(range(len(directions))), 0, 0
        for attempt in range(RECASTS + 1):
            starts = origin + directions[pending] * travelled[pending, None]
            ends = origin + directions[pending] * reach
            results = p.rayTestBatch(starts.tolist(), ends.tolist(), physicsClientId=self.client)
            again = []
            for index, (body, link, _, point, _) in zip(pending, results):
                if body < 0:
                    continue
                distance = float(np.linalg.norm(np.array(point) - origin))
                if body != self.robot.robot:
                    hits[index] = (body, link, distance, list(point))
                elif attempt < RECASTS and distance + SKIN < reach:
                    travelled[index] = distance + SKIN
                    again.append(index)
                    recast += 1
                else:
                    blocked += 1
            pending = again
            if not pending:
                break
        return hits, recast, blocked

    def scan(self):
        """The geometry of one measurement, without noise."""
        position, quaternion = self.mount.frame()
        origin = np.array(position)
        directions = self.layout @ np.array(p.getMatrixFromQuaternion(quaternion)).reshape(3, 3).T
        hits, recast, blocked = self.trace(origin, directions)
        ends = [hit[3] if hit else (origin + direction * self.definition['range']).tolist()
                for hit, direction in zip(hits, directions)]
        found = [hit for hit in hits if hit]
        return {'origin': origin, 'direction': directions[0], 'ends': ends, 'recast': recast, 'blocked': blocked,
                'nearest': min(found, key=lambda hit: hit[2]) if found else None}

    def measure(self, time, dt):
        scan, d = self.scan(), self.definition
        nearest, distance = scan['nearest'], None
        if nearest:
            true = nearest[2]
            distance = min(d['range'], max(0., true + float(self.rng.normal(0., d['noise'] * true))))
        return {'distance': None if distance is None else round(distance, 4), 'in_range': distance is not None,
                'hit': {'body': int(nearest[0]), 'point': vec(nearest[3])} if nearest else None,
                'origin': vec(scan['origin']), 'direction': vec(scan['direction']),
                'rays': [vec(end) for end in scan['ends']]}

    def self_test(self):
        scan, reach = self.scan(), self.definition['range']
        nearest, origin = scan['nearest'], scan['origin']
        body = p.getAABB(self.robot.robot, self.mount.index, physicsClientId=self.client)
        low, high = np.array(body[0]), np.array(body[1])
        gap = float(np.linalg.norm(np.maximum(0., np.maximum(low - origin, origin - high))))
        stuck = f", {scan['blocked']} could not get out: move the sensor out of the body" if scan['blocked'] else ''
        seen = 'nothing within range' if nearest is None else f'{nearest[2]:.3f} m of {reach:.2f} m (without noise)'
        return [
            check('Distance is nothing or between 0 and the range', nearest is None or 0 < nearest[2] <= reach, seen),
            check('Ray origin is on the link it is mounted on', gap <= POSE_SLACK,
                  f'{gap * 1000:.0f} mm from the body of {self.definition["link"]}'),
            check('No ray measures the robot itself', scan['blocked'] == 0,
                  f"{scan['recast']} casts hit the robot itself and went on past it ({len(self.layout)} rays)" + stuck),
        ]


class ImuSensor(Sensor):
    """MPU6050 at the origin of its link, in body axes. Orientation is exact; rates and acceleration may be noisy."""
    type = 'imu'
    limitations = (
        'Ideal sensor plus optional white noise: no bias, drift or temperature effects.',
        "Orientation is exact (the MPU6050's on-chip fusion is not modelled).",
        'Acceleration comes from the change of the link velocity, taken at its centre of mass: no lever-arm effects.',
    )

    def __init__(self, definition, robot, hub, rng, gravity=-9.81):
        super().__init__(definition, robot, hub, rng)
        self.gravity = gravity
        self.previous = None  # (time, world velocity) at the last measurement

    def sample(self, interval, noisy=True):
        """(orientation rad, angular velocity rad/s, acceleration m/s², world velocity) over `interval` seconds."""
        _, quaternion = self.mount.frame()
        linear, angular = frames.link_velocity(self.client, self.robot.robot, self.mount.index)
        acceleration = [0., 0., -self.gravity]  # the reaction to gravity: a resting sensor reads +9.81 up
        if interval:
            for axis in range(3):
                acceleration[axis] += (linear[axis] - self.previous[1][axis]) / interval
        inverse = frames.inverse(quaternion)
        gyro, accel = frames.rotate(inverse, angular), frames.rotate(inverse, acceleration)
        if noisy and self.definition['noise']:
            gyro = [v + float(self.rng.normal(0., self.definition['noise'])) for v in gyro]
            accel = [v + float(self.rng.normal(0., self.definition['noise'] * abs(self.gravity))) for v in accel]
        return list(p.getEulerFromQuaternion(quaternion)), gyro, accel, linear

    def measure(self, time, dt):
        interval = None
        if dt is not None and self.previous is not None and time - self.previous[0] > EPSILON:
            interval = time - self.previous[0]  # the IMU runs slower than physics: use the time since its last sample
        orientation, gyro, accel, linear = self.sample(interval)
        self.previous = (time, linear)
        return {'orientation': vec(orientation, 6), 'angular_velocity': vec(gyro, 5),
                'linear_acceleration': vec(accel, 4)}

    def self_test(self):
        orientation, gyro, accel, linear = self.sample(None)
        roll, pitch = math.degrees(orientation[0]), math.degrees(orientation[1])
        speed = math.sqrt(sum(v * v for v in linear))
        finite = all(math.isfinite(v) for v in orientation + gyro + accel)
        name, one_g = 'Level and still: accelerometer reads 1 g', abs(self.gravity)
        checks = [check('Reading is finite', finite, 'orientation, angular velocity and acceleration')]
        if abs(roll) < 5 and abs(pitch) < 5 and speed < .01:
            magnitude = math.sqrt(sum(v * v for v in accel))
            tolerance = max(.5, 4 * self.definition['noise'] * one_g)  # a noisy sensor may scatter more
            checks.append(check(name, abs(magnitude - one_g) <= tolerance,
                                f'{magnitude:.2f} m/s² (up {accel[2]:+.2f}), expected {one_g:.2f} ± {tolerance:.2f}'))
        else:
            checks.append(check(name, True, f'skipped: roll {roll:.0f}°, pitch {pitch:.0f}°, speed {speed:.2f} m/s'))
        return checks


SENSOR_CLASSES = {'camera': CameraSensor, 'tof': TofSensor, 'imu': ImuSensor}
RESERVED = ('robot', 'world')  # ids of built-in hub modules


class SensorSuite:
    """All sensors of a scenario on one robot, registered in the hub."""

    def __init__(self, robot, definitions, hub, seed=0, gravity=-9.81, environment=None):
        self.robot, self.hub = robot, hub
        sensors = {}
        for definition in definitions:
            name, sensor_id = definition['name'], definition['id']
            if sensor_id in RESERVED:
                raise ValueError(f'Sensor {name}: the id {sensor_id} belongs to a built-in module; choose another')
            if sensor_id in sensors:
                raise ValueError(f'Sensor {name}: the id {sensor_id} is used twice')
            if definition['type'] not in SENSOR_CLASSES:
                raise ValueError(f"Sensor {name}: unknown type {definition['type']}")
            rng = np.random.default_rng([seed, zlib.crc32(sensor_id.encode())])  # each sensor has its own noise stream
            extra = {'imu': {'gravity': gravity}, 'camera': {'environment': environment}}.get(definition['type'], {})
            sensors[sensor_id] = SENSOR_CLASSES[definition['type']](definition, robot, hub, rng, **extra)
        self.sensors = sensors  # built completely before registering, so a bad definition leaves the hub untouched
        for sensor in sensors.values():
            hub.register(sensor)

    def set_environment(self, environment):
        """Light every camera by a new scenario 'environment' (None = day) from its next frame on; nothing is rebuilt."""
        for sensor in self.sensors.values():
            if isinstance(sensor, CameraSensor):
                sensor.environment = copy.copy(environment)

    def step(self, time, dt):
        """Call after every physics step: each sensor measures when its rate says so."""
        for sensor in self.sensors.values():
            if sensor.due(time):
                self.update(sensor, time, dt)

    def refresh(self, time):
        """Measure every sensor now, whatever its rate (paused physics, edited pose)."""
        for sensor in self.sensors.values():
            self.update(sensor, time, None)

    @staticmethod
    def update(sensor, time, dt):
        try:
            sensor.update(time, dt)
            sensor.error = None
        except Exception as error:  # one broken sensor must not stop the physics loop; its status shows 'error'
            sensor.error = f'{type(error).__name__}: {error}'

    def readings(self):
        return {sensor_id: sensor.reading for sensor_id, sensor in self.sensors.items() if sensor.reading}

    def describe(self):
        return [{**sensor.config(), 'module': sensor.id} for sensor in self.sensors.values()]

    def remove(self):
        for sensor_id in self.sensors:
            self.hub.unregister(sensor_id)
