"""One coop simulation: the Bullet world, the robot, its sensors, and the hub that connects them.

A scenario (config.py) describes everything. apply() rebuilds only what changed and always starts the run again
from the robot's start position; tick() advances one physics step; worker() runs ticks at the chosen speed.
Phase 2 adds the animals and visitors (actors.py), the detector, the behaviour (state machine), the battery and the
metrics; a mission runs the behaviour.
"""
import math
import threading
import time
from collections import deque

import pybullet as p

import skills
from coop import config, gaits, traverse
from coop import legs as leg_design
from coop.actors import Actors
from coop.behaviour import STATES, Behaviour
from coop.detector import Detector
from coop.energy import Battery
from coop.frames import link_frame
from coop.hub import Hub, Module, check
from coop.metrics import Metrics
from coop.robot import CoopRobot, RobotModule
from coop.sensors import SensorSuite
from coop.world import World
from engine import ASSETS, DATA, asset_url

GRAVITY = -9.81
SOLVER_ITERATIONS = 80
STATE_HZ = 20  # robot/state messages per simulated second
EDGE = .15     # metres from the terrain edge at which the run pauses, before the robot walks off the height map
TORQUE_EVERY = 4      # physics steps between torque samples
TORQUE_WINDOW = 120   # samples kept per joint: 2 s at 240 Hz physics
SATURATED = .98       # share of the servo torque counted as "at the limit"
# Dashboard drive buttons: Petoi console commands played through skills.py, like the Studio's robot console.
DRIVE = {'stand': 'kbalance', 'walk': 'kwkF', 'trot': 'ktrF', 'crawl': 'kcrF', 'back': 'kbk',
         'walk-left': 'kwkL', 'walk-right': 'kwkR', 'spin-left': 'kvtL', 'spin-right': 'kvtR', 'sit': 'ksit',
         'rest': 'd'}


def robot_models():
    """URDF/Xacro robots that can be chosen: the bundled ones and those imported through the Studio."""
    found = []
    for base in (ASSETS, DATA):
        for path in sorted(base.glob('*/**/*')):
            if path.is_relative_to(leg_design.GENERATED):
                continue  # leg designs are chosen with the leg settings, not as models
            if path.is_file() and path.suffix.lower() in ('.urdf', '.xacro') and len(path.relative_to(base).parts) <= 4:
                found.append({'url': asset_url(path), 'name': path.stem + ('' if base == ASSETS else ' (imported)')})
    return found


class PhysicsModule(Module):
    kind = 'physics'
    limitations = (
        'Rigid bodies only: nothing bends, sinks or deforms.',
        'Contacts use Bullet\'s simplified friction model; real feet can slip, bounce or stick differently.',
        'A fixed time step; very fast impacts can be missed at low physics rates.',
    )

    def __init__(self, session):
        self.session = session
        super().__init__('physics', 'Physics engine (PyBullet)')

    def config(self):
        s = self.session
        return {'engine': 'PyBullet 3.2.7 (DIRECT, CPU)', 'physics_hz': s.scenario['simulation']['physics_hz'],
                'solver_iterations': SOLVER_ITERATIONS, 'gravity': GRAVITY,
                'speed': s.scenario['simulation']['speed'], 'measured_speed': round(s.measured_speed, 2)}

    def self_test(self):
        s = self.session
        params = p.getPhysicsEngineParameters(physicsClientId=s.client)
        hz = s.scenario['simulation']['physics_hz']
        checks = [
            check('Time step matches physics Hz', abs(params['fixedTimeStep'] - 1 / hz) < 1e-9,
                  f"{params['fixedTimeStep'] * 1000:.3f} ms"),
            check('Gravity points down at 9.81 m/s²', abs(params['gravityAccelerationZ'] - GRAVITY) < 1e-9,
                  f"{params['gravityAccelerationZ']:.2f} m/s²"),
            check('Solver iterations', params['numSolverIterations'] == SOLVER_ITERATIONS, params['numSolverIterations']),
        ]
        started = time.perf_counter()
        state = p.saveState(physicsClientId=s.client)
        try:
            for _ in range(24):
                p.stepSimulation(physicsClientId=s.client)
        finally:
            p.restoreState(state, physicsClientId=s.client)
            p.removeState(state, physicsClientId=s.client)
        factor = 24 / hz / (time.perf_counter() - started)
        checks.append(check('Physics runs faster than real time (without sensors)', factor > 1, f'{factor:.1f}× real time'))
        return checks


class CoopSession:
    def __init__(self, scenario=None):
        self.lock = threading.RLock()
        self.client = p.connect(p.DIRECT)
        self.time = 0.
        self.running = False
        self.closed = False
        self.measured_speed = 0.
        self.scenario = None
        self.world = self.robot = self.sensors = None
        self.actors = self.detector = self.behaviour = self.battery = self.metrics = None
        self.world_description = None
        self.body = None             # the robot's latest body state (STATE_HZ)
        self._camera_frame = None    # the detector camera's frame number the metrics saw last
        self.events = deque(maxlen=200)
        self._next_state = self._next_summary = 0.
        self._fallen = False
        self._ticks = 0
        self.torque_samples = {}  # joint: recent |torque| samples, for the servo readout
        self.revision = 0  # counts applied scenarios, so every open dashboard notices a change made elsewhere
        self.hub = Hub(clock=lambda: self.time)
        self.hub.register(PhysicsModule(self))
        self.hub.register(RobotModule(self))
        self.apply(scenario or config.default())

    def log(self, text):
        event = {'time': round(self.time, 3), 'text': text}
        self.events.append(event)
        self.hub.publish('session/event', event, 'session')

    # Building

    def _build(self, scenario, refit=False):
        """Empty the Bullet world and build terrain, robot and sensors from scratch.

        refit (after choosing another robot model) moves payload and sensors whose link the new robot lacks to its
        base link, and returns what was moved; otherwise a missing link is an error.
        """
        if self.sensors:
            self.sensors.remove()
        self.sensors = None
        if self.behaviour:
            self.behaviour.latched = None  # resetSimulation removes the dock latch with everything else
        self.actors = None                 # and the actors' bodies, whose ids the new bodies will reuse
        p.resetSimulation(physicsClientId=self.client)
        p.setGravity(0, 0, GRAVITY, physicsClientId=self.client)
        p.setPhysicsEngineParameter(numSolverIterations=SOLVER_ITERATIONS, physicsClientId=self.client)
        self.world = World(self.client, scenario)
        self.hub.register(self.world)
        self.world_description = self.world.scene()
        self.robot = CoopRobot(self.client, {**scenario['robot'], 'payload': []})
        moved = []
        if refit:
            base = next(name for name, index in self.robot.links.items() if index < 0)
            for item in scenario['robot']['payload'] + scenario['sensors']:
                if item['link'] not in self.robot.links:
                    moved.append(f"{item['name']} moved from {item['link']} to {base}")
                    item['link'] = base
        self.robot.apply_payload(scenario['robot']['payload'])
        self.robot.settings = scenario['robot']
        self._build_actors(scenario)
        self.sensors = self._sensors(scenario)
        self._build_brain(scenario)
        return moved

    def _sensors(self, scenario):
        return SensorSuite(self.robot, scenario['sensors'], self.hub, seed=scenario['terrain']['seed'],
                           gravity=GRAVITY, environment=scenario['environment'])

    def _build_actors(self, scenario):
        """Chickens and visitors: kinematic bodies that the camera and the ToF sensors see, but that never push."""
        if self.actors:
            self.actors.remove()
        self.actors = Actors(self.client, scenario, self.world)
        self.actors.ignore_collisions_with(self.robot.robot)
        self.hub.register(self.actors)

    def _build_brain(self, scenario):
        """Detector, battery, metrics and behaviour for a freshly built robot."""
        self.detector = Detector(self.hub, scenario['detector'], self.camera, self.labels)
        self.battery = Battery(scenario['energy'], scenario['environment'], len(self.robot.joints))
        self.metrics = Metrics(scenario, self.world.height_at, self.robot.robot)
        self.behaviour = Behaviour(self, scenario)
        for module in (self.detector, self.battery, self.metrics, self.behaviour):
            self.hub.register(module)

    def _configure_brain(self, scenario):
        """Settings of detector, battery, metrics and behaviour that change without rebuilding anything."""
        self.detector.set_settings(scenario['detector'])
        self.battery.configure(scenario['energy'], scenario['environment'])
        self.metrics.configure(scenario)
        self.behaviour.configure(scenario)

    def camera(self, camera_id):
        return self.sensors.sensors.get(camera_id) if self.sensors else None

    def labels(self):
        return {uid: info['kind'] for uid, info in self.actors.bodies.items()} if self.actors else {}

    def apply(self, scenario):
        """Use a new scenario, rebuilding only what changed; the run starts again from the robot's start."""
        new = config.validate(scenario)
        with self.lock:
            old = self.scenario
            self.running = False
            changed = lambda *keys: old is None or any(new[k] != old[k] for k in keys)
            moved = []
            try:
                other_model = old is not None and new['robot']['model'] != old['robot']['model']
                if changed('terrain', 'mud', 'stones', 'coop', 'dock') or other_model \
                        or any(new['robot'][k] != old['robot'][k] for k in ('forward_axis', 'legs')):
                    moved = self._build(new, refit=other_model)
                else:
                    if new['robot']['payload'] != old['robot']['payload']:
                        self.robot.apply_payload(new['robot']['payload'])
                    self.robot.apply_servo(new['robot']['servo'])
                    self.robot.settings = new['robot']  # gait and start take effect at the reset below
                    if changed('chickens', 'visitors'):
                        self._build_actors(new)
                    if changed('sensors'):
                        self.sensors.remove()
                        self.sensors = self._sensors(new)
                    elif changed('environment'):
                        self.sensors.set_environment(new['environment'])
                    self._configure_brain(new)
            except Exception:
                if old is not None:  # keep a working world when the new model or sensor cannot be built
                    self._build(old)
                    self.scenario = old
                    self.reset()
                raise
            self.scenario = new
            self.revision += 1
            p.setTimeStep(1 / new['simulation']['physics_hz'], physicsClientId=self.client)
            self.reset()
            self.log('Scenario applied: ' + new['name'])
            for note in moved:
                self.log('Robot model changed: ' + note)
            return new

    # Running

    def reset(self):
        with self.lock:
            self.running = self.robot.running = self._fallen = False
            self.time = self._next_state = self._next_summary = 0.
            self.torque_samples = {j['name']: deque(maxlen=TORQUE_WINDOW) for j in self.robot.joints}
            self.behaviour.reset()
            self.battery.reset()
            self.metrics.reset()
            self.actors.reset()
            self._camera_frame = None
            start = self.scenario['robot']['start']
            self.robot.place(start['position'], start['heading'], self.world.height_at)
            self.world.update_foot_friction(self.robot.robot, self.robot.feet)
            self.sensors.refresh(self.time)
            self.detector.update(self.time)
            self._publish_state()

    def set_running(self, value):
        with self.lock:
            self.running = self.robot.running = bool(value)

    def tick(self):
        dt = 1 / self.scenario['simulation']['physics_hz']
        robot = self.robot
        robot.advance_skill(dt)
        robot.drive_motors()
        self.world.update_foot_friction(robot.robot, robot.feet)
        p.stepSimulation(physicsClientId=self.client)
        self.time += dt
        self._ticks += 1
        if self._ticks % TORQUE_EVERY == 0:
            torques = robot.torques()
            for name, value in torques.items():
                self.torque_samples[name].append(abs(value))
            if self.behaviour.state != 'charge':  # docked, the dock powers the robot
                self.battery.drain(dt * TORQUE_EVERY, torques.values(), robot.servo['torque'] if robot.servo else 1.)
        self.sensors.step(self.time, dt)
        self.detector.update(self.time)
        self._observe()
        self.behaviour.tick(self.time, dt)
        body = self.body
        self.actors.step(self.time, dt, body and {'position': body['position'], 'heading': body['heading'],
                                                  'deterring': self.behaviour.deterring})
        happened = self.actors.pop_events()
        for when, text in happened:
            self.log(text)
        if happened:
            self.metrics.fox_events(self.actors.fox())
        if self.time >= self._next_state:
            self._next_state = self.time + 1 / STATE_HZ
            state = self._publish_state()
            self.metrics.tick(self.time, 1 / STATE_HZ, self.behaviour.state, state['position'][:2])
            if self.time >= self._next_summary:  # battery and metrics once per simulated second, for outside programs
                self._next_summary = self.time + 1
                self.hub.publish('energy/battery', self.battery.reading(), 'energy')
                self.hub.publish('metrics/summary', self.metrics.summary(self.battery.used), 'metrics')
            if state['fallen'] and not self._fallen:
                self.log(f"Robot fell over (roll {state['roll']:.0f}°, pitch {state['pitch']:.0f}°)")
            self._fallen = state['fallen']
            x, y = state['position'][:2]
            half_x, half_y = (v / 2 - EDGE for v in self.scenario['terrain']['size'])
            if abs(x) > half_x or abs(y) > half_y:  # beyond the height map there is no ground at all
                self.set_running(False)
                self.robot.skill = None
                self.log(f'Robot reached the edge of the terrain at ({x:.2f}, {y:.2f}) m: paused. Press Reset.')

    def _publish_state(self):
        state = self.robot.body_state(self.world.height_at)
        state['skill'] = self.robot.skill['name'] if self.robot.skill else None
        self.body = state
        self.hub.publish('robot/state', state, 'robot')
        return state

    def _observe(self):
        """Once per new frame of the detector's camera: coverage and the true view, for the metrics."""
        camera = self.camera(self.scenario['detector']['camera'])
        if camera is None or getattr(camera, 'frame', None) == self._camera_frame:
            return
        self._camera_frame = camera.frame
        self.metrics.camera_frame(self.time, getattr(camera, 'shot', None), camera.definition, self.detector.truth())

    def worker(self):
        """Run ticks at the scenario speed (0 = as fast as possible), releasing the lock often for the API."""
        last = time.perf_counter()
        budget = sim_counted = 0.
        window = last
        while not self.closed:
            now = time.perf_counter()
            elapsed, last = min(now - last, .1), now
            with self.lock:
                if self.running:
                    dt = 1 / self.scenario['simulation']['physics_hz']
                    speed = self.scenario['simulation']['speed']
                    deadline = now + .02
                    if speed:
                        budget = min(budget + elapsed * speed, .25)  # never try to catch up more than 0.25 s
                    while self.running and (budget >= dt if speed else True) and time.perf_counter() < deadline:
                        self.tick()
                        sim_counted += dt
                        if speed:
                            budget -= dt
                else:
                    budget = 0.
            if now - window >= 1:
                self.measured_speed, sim_counted, window = sim_counted / (now - window), 0., now
            time.sleep(.001 if self.running else .01)

    def command(self, body):
        action = body.get('action')
        with self.lock:
            if action == 'run':
                self.set_running(body.get('value', True))
                self.log('Physics running' if self.running else 'Physics paused')
            elif action == 'reset':
                self.reset()
                self.log('Reset to the start position')
            elif action == 'speed':
                if body.get('value') not in config.SPEEDS:
                    raise ValueError('Speed must be one of ' + ', '.join(map(str, config.SPEEDS)))
                self.scenario['simulation']['speed'] = body['value']
            elif action == 'mission':
                if body.get('value', True):
                    if self.behaviour.state == 'flat':
                        raise ValueError('The battery is empty: press Reset to start again with a charged battery')
                    self.set_running(True)
                    if not self.behaviour.active:
                        self.behaviour.start(self.time)
                        self.log('Mission started')
                elif self.behaviour.active:
                    self.behaviour.stop(self.time)
                    self.log('Mission stopped: manual control')
            elif action == 'drive':
                command = DRIVE.get(body.get('value'), body.get('value'))
                plan = skills.plan(command, self.robot.mapping)
                if plan is None:
                    raise ValueError(f'{command} is not a movement command')
                self._manual()
                self.robot.play_skill(plan)
                if not self.running:
                    self.set_running(True)
                self.log(f'Drive: {command}')
            elif action == 'gait':
                plan = gaits.plan(self.robot, self.scenario['robot']['gait'], str(body.get('value')))
                self._manual()
                self.robot.play_skill(plan)
                if not self.running:
                    self.set_running(True)
                self.log(f"Generated gait: {self.scenario['robot']['gait']['type']} {body.get('value')}")
                for warning in plan['warnings']:
                    self.log('Gait warning: ' + warning)
            elif action == 'refresh-sensors':
                self.sensors.refresh(self.time)
            else:
                raise ValueError('Unknown action: ' + str(action))
            return self.state()

    def _manual(self):
        """A drive or gait button takes over from the mission."""
        if self.behaviour.active:
            self.behaviour.stop(self.time)
            self.log('Mission stopped: manual control')

    # Reading

    def transforms(self):
        """World pose of every robot link frame, for drawing the URDF visuals in the browser."""
        return {name: link_frame(self.client, self.robot.robot, index) for name, index in self.robot.links.items()}

    def state(self):
        with self.lock:
            body, client = self.robot.robot, self.client
            robot = self.robot.body_state(self.world.height_at)
            robot.update(skill=self.robot.skill['name'] if self.robot.skill else None, transforms=self.transforms(),
                         angles={j['name']: round(math.degrees(p.getJointState(body, j['id'], physicsClientId=client)[0]), 2)
                                 for j in self.robot.joints},
                         feet={name: self.world.friction_at(*p.getLinkState(body, index, physicsClientId=client)[0][:2])
                               for name, index in self.robot.feet.items()},
                         servo=self.servo_load())
            return {'time': self.time, 'revision': self.revision, 'running': self.running,
                    'speed': self.scenario['simulation']['speed'],
                    'measured_speed': round(self.measured_speed, 2), 'robot': robot,
                    'sensors': self.sensors.readings(), 'hub_sequence': self.hub.sequence,
                    'modules': {m['id']: m['status'] for m in self.hub.modules()}, 'events': list(self.events)[-30:],
                    'behaviour': self.behaviour.reading(), 'battery': self.battery.reading(),
                    'actors': self.actors.states(), 'detection': self.detector.latest(self.time),
                    'metrics': self.metrics.summary(self.battery.used),
                    'coverage_seen': sorted(self.metrics.seen)}  # indices into the model's coverage_points

    def servo_load(self):
        """Per joint over the last 2 s of physics: the latest and mean torque (Nm) and the share of time at the limit."""
        limit = self.robot.servo['torque'] if self.robot.servo else None
        joints = {}
        for name, samples in self.torque_samples.items():
            if not samples:
                continue
            latest, mean = samples[-1], sum(samples) / len(samples)
            at_limit = sum(v >= SATURATED * limit for v in samples) / len(samples) if limit else 0.
            joints[name] = {'torque': round(latest, 4), 'mean': round(mean, 4), 'at_limit': round(at_limit, 3)}
        return {'limit': limit, 'joints': joints}

    def model(self):
        with self.lock:
            robot = self.robot
            legs = robot.gait_legs or {}
            return {'revision': self.revision, 'scenario': self.scenario, 'world': self.world_description,
                    'robot': {'visuals': robot.visuals, 'joints': robot.joints, 'links': list(robot.links),
                              'feet': sorted(robot.feet), 'warnings': robot.warnings, 'mass': robot.mass(),
                              'forward_axis': robot.forward_axis, 'gaits': robot.gait_legs is not None,
                              # as built: in-plane leg lengths (m) and shoulder positions in body axes (m)
                              'legs': {name: {'upper': round(g['upper'], 4), 'lower': round(g['lower'], 4),
                                              'hip': [round(float(v), 4) for v in g['hip']]}
                                       for name, g in legs.items()}},
                    'sensors': self.sensors.describe(), 'drive': DRIVE, 'speeds': list(config.SPEEDS),
                    'gait_motions': list(gaits.MOTIONS), 'gait_types': list(config.GAIT_TYPES),
                    'leg_presets': config.LEG_PRESETS, 'robot_models': robot_models(), 'bodies': self.bodies(),
                    'actors': self.actors.scene(), 'coverage_points': self.metrics.points,
                    'choices': {'knee_directions': list(config.KNEE_DIRECTIONS),
                                'times_of_day': list(config.TIMES_OF_DAY), 'visitor_kinds': list(config.VISITOR_KINDS),
                                'locomotion': list(config.LOCOMOTION), 'detector_types': list(config.DETECTOR_TYPES),
                                'behaviour_states': list(STATES)},
                    'locomotion': self.behaviour.navigator.locomotion if self.behaviour.navigator else None}

    def traverse_test(self, seconds=30.):
        """Stock and spider legs (and the current design) walk the same course in separate worlds; see traverse.py."""
        with self.lock:
            scenario = config.validate(self.scenario)
        return self.traverse_done(traverse.run(scenario, seconds))

    def traverse_done(self, results):
        """Publish a finished traverse test and name the furthest design in the log."""
        self.hub.publish('tests/traverse', results, 'session')
        with self.lock:
            best = max(results['runs'], key=lambda run: run.get('distance', 0.))
            self.log(f"Traverse test ({results['seconds']:.0f} s): furthest was {best['name']} with "
                     f"{best.get('distance', 0.):.2f} m")
        return results

    def bodies(self):
        """Names for the Bullet body ids that camera and ToF readings report."""
        named = {str(uid): {'name': item['name'], 'kind': item['kind']}
                 for uid, item in {**self.world.bodies, **self.actors.bodies}.items()}
        named[str(self.robot.robot)] = {'name': 'Bittle (itself)', 'kind': 'robot'}
        return named

    def run_test(self, module_id=None):
        with self.lock:
            return self.hub.run_all_tests() if module_id is None else self.hub.run_test(module_id)

    def close(self):
        self.closed = True
        with self.hub.changed:
            self.hub.changed.notify_all()
        with self.lock:
            p.disconnect(self.client)
