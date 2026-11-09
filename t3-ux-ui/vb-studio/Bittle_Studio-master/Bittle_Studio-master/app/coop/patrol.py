"""Patrol route and steering: following a closed loop of waypoints, walking to a point, lining up with the dock.

The route is a closed polyline. The robot follows it like a pure-pursuit controller: it finds the closest point on the
route near where it was last, and walks toward a point a little further along (the carrot). Steering only picks one
of a few walking motions (straight, arc left/right, turn on the spot), because a walking gait cannot steer smoothly:
Petoi's skills for stock legs, or the generated gait's motions for any other leg design.
"""
import math

import numpy as np

import skills
from coop import gaits
from coop import legs as leg_design

LOOK_AHEAD = .4           # metres from the closest route point to the carrot
SEARCH_BACK, SEARCH_AHEAD = .3, 1.  # metres of route searched around the last position (no jumping across the run)
DECIDE_S = .05            # seconds between steering decisions
DWELL_S = .6              # shortest time a walking motion runs before steering may change it
# Heading errors (degrees) at which the robot starts / stops turning on the spot, and walking an arc. Measured on
# level ground: Petoi's arcs turn about 3°/s at half speed, its turn on the spot 9°/s. The generated gaits hardly
# turn when one side takes shorter steps (the crab: under 1°/s), so they only turn on the spot (about 9°/s).
STEERING = {'petoi': {'spin': (40., 20.), 'arc': (10., 4.)},
            'gait': {'spin': (8., 2.), 'arc': None}}
SMOOTHING_S = .6          # time constant of the heading-error filter: the body sways within every step
PETOI = {'forward': 'kwkF', 'backward': 'kbk', 'left': 'kwkL', 'right': 'kwkR', 'spin-left': 'kvtL',
         'spin-right': 'kvtR', 'stance': 'kbalance', 'rest': 'd'}


def wrap(angle):
    """Degrees into -180..180."""
    return (angle + 180.) % 360. - 180.


def bearing(origin, target):
    return math.degrees(math.atan2(target[1] - origin[1], target[0] - origin[0]))


class Route:
    """A closed loop of waypoints with arc-length positions along it."""

    def __init__(self, points):
        self.points = np.asarray(points, float)
        ends = np.roll(self.points, -1, axis=0)
        self.vectors = ends - self.points
        self.lengths = np.hypot(self.vectors[:, 0], self.vectors[:, 1])
        if not self.lengths.all():
            raise ValueError('Two patrol waypoints in a row are at the same place')
        self.starts = np.concatenate([[0.], np.cumsum(self.lengths)[:-1]])
        self.length = float(self.lengths.sum())

    def at(self, s):
        """The route point at arc length s (any value: the loop repeats)."""
        s %= self.length
        i = int(np.searchsorted(self.starts, s, side='right') - 1)
        return self.points[i] + self.vectors[i] * ((s - self.starts[i]) / self.lengths[i])

    def project(self, xy, near=None):
        """(arc length, distance) of the closest route point; near limits the search to the route around it."""
        xy = np.asarray(xy[:2], float)
        t = np.clip(((xy - self.points) * self.vectors).sum(1) / self.lengths ** 2, 0, 1)
        closest = self.points + self.vectors * t[:, None]
        distances = np.hypot(*(closest - xy).T)
        positions = self.starts + t * self.lengths
        if near is not None:
            # Arc length relative to `near`, unwrapped into -length/2..length/2, and only the window around it.
            relative = (positions - near + self.length / 2) % self.length - self.length / 2
            allowed = (relative >= -SEARCH_BACK) & (relative <= SEARCH_AHEAD)
            if allowed.any():
                distances = np.where(allowed, distances, np.inf)
                i = int(np.argmin(distances))
                return near + float(relative[i]), float(distances[i])
        i = int(np.argmin(distances))
        return float(positions[i]), float(distances[i])


class Navigator:
    """Turns "go this way" into walking motions for one robot, switching motions as seldom as possible."""

    def __init__(self, robot, locomotion='auto'):
        self.robot = robot
        legs = robot.settings.get('legs')
        stock = not legs or leg_design.is_stock(legs)
        if locomotion == 'auto':
            locomotion = 'petoi' if stock and robot.gait_legs is not None else 'gait'
        if locomotion == 'gait' and robot.gait_legs is None:
            locomotion = 'petoi'  # a robot without Bittle's legs can only replay Petoi skills
        self.locomotion = locomotion
        self.plans = {}
        self.reset()

    def plan(self, motion):
        if motion not in self.plans:
            if self.locomotion == 'petoi':
                self.plans[motion] = skills.plan(PETOI[motion], self.robot.mapping)
            else:
                gait = self.robot.settings['gait']
                self.plans[motion] = gaits.plan(self.robot, gait, 'stance' if motion == 'rest' else motion)
        return self.plans[motion]

    def drive(self, motion, time, force=False):
        """Play a motion unless it is already playing; a walking motion runs at least DWELL_S first."""
        if motion == self.motion and self.robot.skill is not None:
            return
        if not force and motion not in ('stance', 'rest') and time - self.since < DWELL_S and self.robot.skill:
            return
        playing = self.robot.skill
        self.robot.play_skill(self.plan(motion))
        walking = ('stance', 'rest')
        if (self.locomotion == 'gait' and playing and playing.get('loop_from') and playing['index'] >= 1
                and motion not in walking and self.motion not in walking):
            # Generated walking motions share one cycle of frames: carry on at the same point of the cycle instead
            # of easing into the first frame again, so steering does not interrupt the step rhythm.
            self.robot.skill.update(index=playing['index'], elapsed=playing['elapsed'])
        self.motion, self.since = motion, time

    def steer(self, error, time, spin=True):
        """Walk to reduce a heading error (degrees, positive = target to the left)."""
        # Low-pass the error: the body yaws back and forth within each step, which is no reason to steer.
        if self.smoothed is None or time - self.smoothed_at > 1:
            self.smoothed = error
        else:
            weight = min(1., (time - self.smoothed_at) / SMOOTHING_S)
            self.smoothed += wrap(error - self.smoothed) * weight
        self.smoothed_at = time
        if abs(error) < 90:  # a big error (a new target) needs no filtering
            error = self.smoothed
        current, size = self.motion, abs(error)
        steering = STEERING[self.locomotion]
        (spin_on, spin_off), arc = steering['spin'], steering['arc']
        # Without arcs (or where turning on the spot is not allowed) the generated gaits veer: shorter steps on one side.
        left, right = ('left', 'right') if self.locomotion == 'petoi' else ('veer-left', 'veer-right')
        arc_on, arc_off = arc or (spin_on, spin_off)
        turning = current in ('spin-left', 'spin-right')
        arcing = current in (left, right)
        if spin and (size > spin_on or (turning and size > spin_off)):
            motion = 'spin-left' if error > 0 else 'spin-right'
        elif (arc or not spin) and (size > arc_on or (arcing and size > arc_off) or (turning and size > arc_off)):
            motion = left if error > 0 else right
        else:
            motion = 'forward'
        self.drive(motion, time)
        return motion

    def stop(self, time):
        self.drive('stance', time, force=True)

    def reset(self):
        self.motion, self.since = None, -math.inf
        self.smoothed, self.smoothed_at = None, -math.inf
