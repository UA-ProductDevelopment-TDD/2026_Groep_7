"""The robot's behaviour (proposal section 6): patrol -> detect -> deter -> back to the dock -> charge -> patrol.

States:
- patrol: follow the route; stop for an obstacle in front of the obstacle ToF sensor.
- detect: a fox was seen; stand and look until enough frames in a row confirm it (the alarm), or it is gone.
- deter: deterrent on (light and sound, not modelled further); walk toward the fox, keep the chase distance.
- return: walk to the approach point behind the dock (also when the battery is low or after the set laps).
- dock: line up with the dock and walk in; the magnet latches inside the capture zone, else back off and retry.
- charge: latched to the dock until the battery is charged; undock: back out to the route.
- fallen: after a fall the robot stands up again where it lies (if self-righting is on); flat: battery empty.
The behaviour sees the world through the detector and the ToF sensor only, plus its own pose (odometry is assumed
perfect: the real robot would need to estimate where it is).
"""
import math

import pybullet as p

from coop.hub import Module, check
from coop.patrol import DECIDE_S, LOOK_AHEAD, Navigator, Route, bearing, wrap

APPROACH = .4         # metres behind the dock where the final approach starts
APPROACH_REACHED = .06  # metres from the approach point that count as there
ALIGNED = 6.           # degrees of heading error at which the robot stops turning and walks into the dock
AIM_AHEAD = .25        # metres ahead along the dock axis that the robot steers at while walking in
BACK_OFF = .3          # metres back along the dock axis after a missed docking
NO_PROGRESS_S = 4.     # seconds without getting closer before a docking attempt counts as missed
OFF_AXIS = .15         # metres beside the dock axis at which an attempt is given up
LOST_S = 2.            # seconds without a fox before detect gives up
SELF_RIGHT_S = 3.      # seconds lying on its side before the robot stands up again
BLOCKED_S = 4.         # seconds waiting for an obstacle before turning away from it
TURN_AWAY_S = 2.       # seconds of turning on the spot to get round an obstacle
FACE_FOX = 20.         # degrees of bearing at which the robot turns toward the fox while confirming or deterring
DETER_LIMIT_S = 90.    # seconds of deterring at most: a detector that keeps seeing a "fox" in a roof must not stall it
COOLDOWN_S = 60.       # seconds of patrol after a failed docking before trying again
STATES = ('off', 'patrol', 'detect', 'deter', 'return', 'dock', 'charge', 'undock', 'fallen', 'flat')


class Behaviour(Module):
    kind = 'behaviour'
    publishes = ('behaviour/state', 'behaviour/alarm')
    limitations = (
        'The robot knows its own position and heading exactly (perfect odometry); the real robot must estimate them.',
        'Steering picks one of a few walking motions (straight, arcs, turning on the spot); there is no smooth '
        'speed control.',
        'The deterrent (light, sound) has no model of its own: the scripted fox runs off when the deterring robot '
        'comes within its flee distance.',
        'Docking latches the robot in place when it is inside the capture zone: no magnet force, no contacts.',
        'Self-righting puts the robot back on its feet after a few seconds, as Bittle\'s firmware can; how it gets '
        'up is not simulated.',
    )

    def __init__(self, session, scenario):
        super().__init__('behaviour', 'Behaviour (state machine)')
        self.session = session
        self.configure(scenario)
        self.reset()

    def configure(self, scenario):
        s = self.scenario = scenario
        self.settings, self.patrol, self.detector_settings = s['behaviour'], s['patrol'], s['detector']
        self.route = Route(self.patrol['route'])
        dock = s['dock']
        yaw = math.radians(dock['yaw'])
        self.dock_point, self.dock_yaw, self.dock_axis = dock['position'], dock['yaw'], (math.cos(yaw), math.sin(yaw))
        self.approach = [dock['position'][i] - APPROACH * self.dock_axis[i] for i in range(2)]
        self.capture = (dock['capture_distance'], dock['capture_angle'])

    def reset(self):
        self.unlatch()
        self.state, self.since, self.previous, self.resume = 'off', 0., None, 'patrol'
        self.navigator = None
        self.progress = self.lap_start = None
        self.laps = self.laps_since_charge = 0
        self.last_frame, self.fox_frames, self.fox_seen_at, self.fox_estimate = None, 0, None, None
        self.deterring = False
        self.phase, self.phase_since, self.attempts, self.best = None, 0., 0, None
        self.best_longitudinal, self.progress_at = None, 0.
        self.blocked_since = self.turning_until = None
        self.miss = ''
        self.next_decision = 0.
        self.cooldown_until = 0.
        self.latched = None
        self.charge_dt = 0.

    @property
    def active(self):
        return self.state not in ('off', 'flat')

    # Starting and stopping

    def start(self, time):
        s = self.session
        self.navigator = Navigator(s.robot, self.patrol['locomotion'])  # the robot or its gait may have changed
        self.progress = None
        self.rejoin(s.robot.body_state(s.world.height_at))
        self.enter('charge' if self.latched else 'patrol', time)

    def rejoin(self, body):
        """Take up the route again at the point closest to the robot (after a chase, the dock or a detour)."""
        position = self.route.project(body['position'])[0]
        if self.progress is None:
            self.progress = self.lap_start = position
        else:  # keep counting laps: the same point, as close as possible to where the robot left the route
            length = self.route.length
            self.progress += (position - self.progress + length / 2) % length - length / 2

    def stop(self, time):
        self.unlatch()
        self.deterring = False
        if self.navigator:
            self.navigator.stop(time)
        self.enter('off', time)

    def enter(self, state, time, note=None):
        if state != self.state:
            self.previous, self.state, self.since = self.state, state, time
            self.phase, self.phase_since = None, time
            self.session.hub.publish('behaviour/state', {'state': state, 'previous': self.previous, 'note': note},
                                     'behaviour')
            if state not in ('off',):
                self.session.log(f'Behaviour: {state}' + (f' ({note})' if note else ''))

    # The dock

    def dock_errors(self, body):
        """(lateral, longitudinal, heading) of the robot relative to the dock: metres, metres, degrees."""
        dx, dy = (body['position'][i] - self.dock_point[i] for i in range(2))
        ax, ay = self.dock_axis
        return -dx * ay + dy * ax, dx * ax + dy * ay, wrap(body['heading'] - self.dock_yaw)

    def latch(self, body):
        s = self.session
        position, quaternion = p.getBasePositionAndOrientation(s.robot.robot, physicsClientId=s.client)
        self.latched = p.createConstraint(s.robot.robot, -1, -1, -1, p.JOINT_FIXED, [0, 0, 0], [0, 0, 0], position,
                                          childFrameOrientation=quaternion, physicsClientId=s.client)

    def unlatch(self):
        if getattr(self, 'latched', None) is not None:
            try:
                p.removeConstraint(self.latched, physicsClientId=self.session.client)
            except p.error:
                pass  # the world was rebuilt and took the constraint with it
        self.latched = None

    # Every physics step

    def tick(self, time, dt):
        if not self.active:
            return
        if self.state == 'charge':
            self.charge_dt += dt
        if time < self.next_decision:
            return
        self.next_decision = time + DECIDE_S
        s = self.session
        body = s.robot.body_state(s.world.height_at)
        if s.battery.empty() and self.state != 'charge':
            self.unlatch()
            self.navigator.drive('rest', time, force=True)
            self.enter('flat', time, 'battery empty')
            return
        if body['fallen'] and not self.latched:
            if self.state != 'fallen':
                resume = self.state
                self.enter('fallen', time, f"roll {body['roll']:.0f}°, pitch {body['pitch']:.0f}°")
                self.resume = resume
                s.metrics.fall()
                self.navigator.stop(time)
            elif self.settings['self_right'] and time - self.since >= SELF_RIGHT_S:
                s.robot.place(body['position'][:2], body['heading'], s.world.height_at)
                s.robot.running = True
                s.metrics.self_rights += 1
                self.navigator.reset()
                self.enter(self.resume, time, 'stood up again')
            return
        if self.state == 'fallen':  # it got up by itself
            self.navigator.reset()
            self.enter(self.resume, time)
        self.look(time)
        getattr(self, '_' + self.state)(time, body)

    # Seeing

    def look(self, time):
        """Read the detector's newest result once per camera frame and keep track of the fox."""
        result = self.session.detector.latest(time) if self.session.detector else None
        key = None if not result else (result.get('frame'), result.get('time'))  # outside programs may send no frame
        if key is None or key == self.last_frame:
            return
        self.last_frame = key
        foxes = [o for o in result.get('objects', []) if o.get('label') == 'fox' and o.get('confidence', 1) >= .5]
        if not foxes:
            self.fox_frames = 0
            return
        fox = max(foxes, key=lambda o: o.get('pixels') or o.get('confidence', 0))
        self.fox_frames += 1
        self.fox_seen_at = time
        body = self.session.robot.body_state(self.session.world.height_at)
        heading = body['heading'] + (fox.get('bearing') or 0.)
        distance = fox.get('distance') or 1.
        self.fox_estimate = [body['position'][0] + distance * math.cos(math.radians(heading)),
                             body['position'][1] + distance * math.sin(math.radians(heading))]

    def fox_seen_now(self, time):
        return self.fox_seen_at is not None and time - self.fox_seen_at < .6

    # States

    def _patrol(self, time, body):
        s, xy = self.session, body['position']
        if self.fox_frames and self.fox_seen_now(time):
            self.navigator.stop(time)
            self.enter('detect', time)
            return
        soc = s.battery.state_of_charge()
        laps = self.settings['laps_before_charging']
        if time >= self.cooldown_until and (soc < self.settings['low_battery']
                                           or (laps and self.laps_since_charge >= laps)):
            self.enter('return', time, f'battery {soc:.0%}' if soc < self.settings['low_battery'] else f'{laps} laps')
            return
        self.progress, distance = self.route.project(xy, near=self.progress)
        s.metrics.route_error(distance)
        while self.progress - self.lap_start >= self.route.length:
            self.lap_start += self.route.length
            self.laps += 1
            self.laps_since_charge += 1
            s.metrics.lap(time, s.battery.used)
            s.log(f'Lap {self.laps} done')
        if self.avoid(time):
            return
        carrot = self.route.at(self.progress + LOOK_AHEAD)
        self.navigator.steer(wrap(bearing(xy, carrot) - body['heading']), time)

    def avoid(self, time):
        """Stop for an obstacle the obstacle ToF sees; after a while turn away from it. True while busy with it."""
        sensor_id, limit = self.patrol['obstacle_sensor'], self.patrol['obstacle_distance']
        if self.turning_until is not None:
            if time < self.turning_until:
                self.navigator.drive('spin-left', time, force=True)
                return True
            self.turning_until = None
            self.navigator.drive('forward', time, force=True)
        reading = self.session.sensors.readings().get(sensor_id, {}) if sensor_id and limit else {}
        if reading.get('distance') is not None and reading['distance'] < limit:
            if self.blocked_since is None:
                self.blocked_since = time
                self.session.metrics.obstacle_stops += 1
            if time - self.blocked_since >= BLOCKED_S:
                self.blocked_since, self.turning_until = None, time + TURN_AWAY_S
                self.navigator.drive('spin-left', time, force=True)
            else:
                self.navigator.stop(time)
            return True
        self.blocked_since = None
        return False

    def _detect(self, time, body):
        s = self.session
        if self.fox_frames >= self.detector_settings['confirm']:
            truth = s.detector.truth() if s.detector else {}
            fox = (truth or {}).get('objects', {}).get('fox') or {}
            true = fox.get('lit_pixels', 0) >= self.detector_settings['min_pixels']
            s.metrics.alarm(time, true, self.detector_settings['type'])
            s.hub.publish('behaviour/alarm', {'label': 'fox', 'true': true, 'estimate': self.fox_estimate},
                          'behaviour')
            s.log('ALARM: fox' + ('' if true else ' (false alarm: no fox in view)'))
            self.enter('deter', time)
            return
        if not self.fox_seen_now(time) and time - (self.fox_seen_at or self.since) > LOST_S:
            s.metrics.unconfirmed += 1
            self.rejoin(body)
            self.enter(self.previous if self.previous in ('patrol', 'return') else 'patrol', time, 'not confirmed')
            return
        self.face_fox(time, body)

    def face_fox(self, time, body):
        if self.fox_estimate is None:
            self.navigator.stop(time)
            return None
        error = wrap(bearing(body['position'], self.fox_estimate) - body['heading'])
        if abs(error) > FACE_FOX:
            self.navigator.drive('spin-left' if error > 0 else 'spin-right', time)
        else:
            self.navigator.stop(time)
        return error

    def _deter(self, time, body):
        self.deterring = True
        gone = time - (self.fox_seen_at or self.since) > self.settings['deter_time']
        if gone or time - self.since > DETER_LIMIT_S:
            self.deterring = False
            self.session.log('Deterrent off: ' + ('no fox for {:.0f} s'.format(self.settings['deter_time']) if gone else
                                                  f'still a "fox" in view after {DETER_LIMIT_S:.0f} s'))
            self.enter('return', time, 'after the fox')
            return
        if self.fox_estimate is None:
            self.navigator.stop(time)
            return
        distance = math.hypot(self.fox_estimate[0] - body['position'][0], self.fox_estimate[1] - body['position'][1])
        error = wrap(bearing(body['position'], self.fox_estimate) - body['heading'])
        if distance > self.settings['chase_distance'] and self.fox_seen_now(time):
            self.navigator.steer(error, time)
        else:
            self.face_fox(time, body)

    def _return(self, time, body):
        if self.fox_frames and self.fox_seen_now(time):
            self.navigator.stop(time)
            self.enter('detect', time)
            return
        xy = body['position']
        if math.hypot(self.approach[0] - xy[0], self.approach[1] - xy[1]) < APPROACH_REACHED:
            self.attempts, self.best = 0, None
            self.enter('dock', time)
            return
        self.navigator.steer(wrap(bearing(xy, self.approach) - body['heading']), time)

    def _dock(self, time, body):
        s = self.session
        lateral, longitudinal, heading = self.dock_errors(body)
        distance, angle = self.capture
        phase = self.phase or 'align'
        if phase in ('align', 'walk-in') and math.hypot(lateral, longitudinal) <= distance and abs(heading) <= angle:
            self.navigator.stop(time)
            self.latch(body)
            s.metrics.dock(time, True, self.attempts + 1,
                           {'lateral': lateral, 'longitudinal': longitudinal, 'heading': heading})
            s.log(f'Docked: {lateral * 1000:+.0f} mm beside, {longitudinal * 1000:+.0f} mm along, {heading:+.1f}°')
            self.laps_since_charge = 0
            self.enter('charge', time)
            return
        if phase == 'approach':  # back at the start of the final approach before another attempt
            if math.hypot(self.approach[0] - body['position'][0], self.approach[1] - body['position'][1]) \
                    < APPROACH_REACHED or time - self.phase_since > 30:
                self.set_phase('align', time)
            else:
                self.navigator.steer(wrap(bearing(body['position'], self.approach) - body['heading']), time)
            return
        if phase == 'align':
            error = wrap(self.dock_yaw - body['heading'])
            if abs(error) <= ALIGNED:
                self.set_phase('walk-in', time)
                self.best_longitudinal, self.progress_at = longitudinal, time
            else:
                self.navigator.drive('spin-left' if error > 0 else 'spin-right', time)
            return
        if phase == 'walk-in':
            score = math.hypot(lateral, longitudinal)
            if self.best is None or score < self.best[0]:
                self.best = (score, {'lateral': lateral, 'longitudinal': longitudinal, 'heading': heading})
            if longitudinal > self.best_longitudinal + .01:
                self.best_longitudinal, self.progress_at = longitudinal, time
            missed = ('went past the capture zone' if longitudinal > distance + .02 else
                      f'{abs(lateral) * 100:.0f} cm beside the dock' if abs(lateral) > OFF_AXIS else
                      'stuck' if time - self.progress_at > NO_PROGRESS_S else None)
            if missed:
                self.miss = (f'{missed}: {lateral * 1000:+.0f} mm beside, {longitudinal * 1000:+.0f} mm along, '
                             f'{heading:+.1f}°')
                self.set_phase('back', time)
                return
            # Follow the dock axis like the route: aim at the point of the axis a little ahead of the robot.
            ahead = min(longitudinal + AIM_AHEAD, AIM_AHEAD)
            aim = [self.dock_point[i] + ahead * self.dock_axis[i] for i in range(2)]
            self.navigator.steer(wrap(bearing(body['position'], aim) - body['heading']), time)
            return
        # back: walk backward out of the dock, then walk to the approach point again or give up
        if longitudinal < -BACK_OFF or time - self.phase_since > 10:
            self.attempts += 1
            if self.attempts >= self.settings['dock_attempts']:
                s.metrics.dock(time, False, self.attempts, self.best[1] if self.best else
                               {'lateral': lateral, 'longitudinal': longitudinal, 'heading': heading})
                s.log(f'Docking failed after {self.attempts} attempts ({self.miss})')
                self.cooldown_until = time + COOLDOWN_S
                self.rejoin(body)
                self.enter('patrol', time, 'docking failed')
            else:
                s.log(f'Docking attempt {self.attempts} missed ({self.miss}): trying again')
                self.set_phase('approach', time)
            return
        self.navigator.drive('backward', time)

    def set_phase(self, phase, time):
        self.phase, self.phase_since = phase, time

    def _charge(self, time, body):
        s = self.session
        self.navigator.stop(time)
        s.battery.charge_for(self.charge_dt)
        self.charge_dt = 0.
        if s.battery.state_of_charge() >= self.settings['resume_battery']:
            self.unlatch()
            self.enter('undock', time, f'battery {s.battery.state_of_charge():.0%}')

    def _undock(self, time, body):
        lateral, longitudinal, heading = self.dock_errors(body)
        if longitudinal < -BACK_OFF or time - self.since > 15:
            self.rejoin(body)
            self.navigator.reset()
            self.enter('patrol', time)
            return
        self.navigator.drive('backward', time)

    def _fallen(self, time, body):
        pass

    # Hub

    def reading(self):
        return {'state': self.state, 'since': round(self.since, 2), 'phase': self.phase, 'laps': self.laps,
                'deterring': self.deterring, 'fox_frames': self.fox_frames,
                'fox_estimate': [round(v, 3) for v in self.fox_estimate] if self.fox_estimate else None,
                'motion': self.navigator.motion if self.navigator else None,
                'locomotion': self.navigator.locomotion if self.navigator else None,
                'progress': round(self.progress, 3) if self.progress is not None else None,
                'route_length': round(self.route.length, 3), 'approach': [round(v, 3) for v in self.approach],
                'docked': self.latched is not None, 'dock_attempts': self.attempts}

    def config(self):
        return {**self.settings, 'route_length_m': round(self.route.length, 2), 'waypoints': len(self.patrol['route']),
                'locomotion': self.patrol['locomotion']}

    def reach_ahead(self, height=.06):
        """Metres the robot reaches ahead of its origin with parts lower than the stop block (corners of every
        link's box, along its heading)."""
        s = self.session
        robot, client = s.robot.robot, s.client
        body = s.robot.body_state(s.world.height_at)
        origin, heading = body['position'], math.radians(body['heading'])
        ahead, ground = (math.cos(heading), math.sin(heading)), s.world.height_at(*origin[:2])
        reach = 0.
        for link in range(-1, p.getNumJoints(robot, physicsClientId=client)):
            low, high = p.getAABB(robot, link, physicsClientId=client)
            if low[2] - ground > height:
                continue
            for x in (low[0], high[0]):
                for y in (low[1], high[1]):
                    reach = max(reach, (x - origin[0]) * ahead[0] + (y - origin[1]) * ahead[1])
        return reach

    def self_test(self):
        s = self.session
        navigator = Navigator(s.robot, self.patrol['locomotion'])
        plans = {}
        for motion in ('forward', 'left', 'right', 'spin-left', 'spin-right', 'backward', 'stance'):
            try:
                plans[motion] = navigator.plan(motion) is not None
            except ValueError as error:
                plans[motion] = str(error)
        missing = [m for m, ok in plans.items() if ok is not True]
        start = self.scenario['robot']['start']['position']
        _, off_route = self.route.project(start)
        dock_ground = abs(s.world.height_at(*self.approach) - s.world.height_at(*self.dock_point))
        reach, stop = self.reach_ahead(), self.scenario['dock']['stop_distance']
        half = [v / 2 - .3 for v in self.scenario['terrain']['size']]
        outside = [i + 1 for i, (x, y) in enumerate(self.patrol['route']) if abs(x) > half[0] or abs(y) > half[1]]
        sensor = self.patrol['obstacle_sensor']
        sensors = s.sensors.sensors if s.sensors else {}
        return [
            check('Every waypoint lies on the terrain', not outside,
                  f"{len(self.patrol['route'])} waypoints at least 0.3 m from the edge" if not outside else
                  'waypoints ' + ', '.join(map(str, outside)) + ' are too close to the edge or beyond it'),
            check('The obstacle sensor exists', not sensor or sensor in sensors,
                  sensor or 'none chosen: the robot does not stop for obstacles'),
            check("The dock's stop block leaves room for the robot", reach < stop + self.capture[0],
                  f'the robot reaches {reach * 1000:.0f} mm ahead of its origin (low parts, as it stands now), the '
                  f'stop block is {stop * 1000:.0f} mm ahead of the dock point'
                  + ('' if reach < stop + self.capture[0] else ': move the stop block further (dock stop distance)')),
            check('Every walking motion can be played', not missing,
                  f'{navigator.locomotion}: ' + (', '.join(missing) + ' missing' if missing else 'all 7 motions')),
            check('The route is a loop of at least 1 m', self.route.length >= 1, f'{self.route.length:.1f} m'),
            check('The start lies near the route', off_route < 1, f'{off_route:.2f} m from the route'),
            check('The dock approach is on level ground', dock_ground < .02, f'{dock_ground * 1000:.0f} mm step'),
            check('A known state', self.state in STATES, self.state),
        ]
