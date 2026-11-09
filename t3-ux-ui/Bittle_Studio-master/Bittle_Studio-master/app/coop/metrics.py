"""What the simulation measures (proposal section 7): route deviation, falls, coop coverage per lap, time to recognise
the fox, false alarms, docking success and accuracy, energy per lap.

Coverage: points every POINT_SPACING metres along the outside of the fence, halfway up. A point counts as seen in a
lap when a camera frame shows it: inside the image, not hidden behind something nearer (depth buffer), within the
camera's range and bright enough for the detector (at night that is what the infrared light reaches).
"""
import math

import numpy as np

from coop import frames
from coop.hub import Module, check

POINT_SPACING = .25   # metres between coverage points along the fence
POINT_OUTSIDE = .03   # metres outside the fence panels, so the depth test sees the panel face
DEPTH_SLACK = .08     # metres a depth-buffer value may differ from the point's depth and still show it
DISTANCE_EVERY = 1.   # seconds between the positions that add up to the distance walked


def fence_points(coop, height_at=lambda x, y: 0.):
    """Coverage points around the fenced run, halfway up the fence, in world coordinates [[x, y, z], ...]."""
    (cx, cy), yaw = coop['position'], math.radians(coop['yaw'])
    half_u, half_v = coop['run_size'][0] / 2 + POINT_OUTSIDE, coop['run_size'][1] / 2 + POINT_OUTSIDE
    corners = [(half_u, -half_v), (half_u, half_v), (-half_u, half_v), (-half_u, -half_v)]
    points = []
    for (u0, v0), (u1, v1) in zip(corners, corners[1:] + corners[:1]):
        count = max(1, round(math.hypot(u1 - u0, v1 - v0) / POINT_SPACING))
        for k in range(count):
            u, v = u0 + (u1 - u0) * (k + .5) / count, v0 + (v1 - v0) * (k + .5) / count
            x, y = cx + u * math.cos(yaw) - v * math.sin(yaw), cy + u * math.sin(yaw) + v * math.cos(yaw)
            points.append([x, y, height_at(x, y) + coop['fence_height'] / 2])
    return points


def visible_points(points, shot, settings, min_brightness):
    """Indices of world points that one camera shot shows (see the module docstring)."""
    position, quaternion = shot['position'], shot['quaternion']
    to_camera = frames.inverse(quaternion)
    relative = np.asarray(points, float) - np.asarray(position, float)
    local = np.array([frames.rotate(to_camera, v) for v in relative])   # x forward, y left, z up
    depth = local[:, 0]
    height, width = shot['depth'].shape
    tan_v = math.tan(math.radians(settings['fov']) / 2)
    tan_h = tan_v * width / height
    seen = []
    for i, (x, y, z) in enumerate(local):
        if x <= .02 or x > settings['range']:
            continue
        column = int((1 - y / (x * tan_h)) * width / 2)
        row = int((1 - z / (x * tan_v)) * height / 2)
        if not (0 <= column < width and 0 <= row < height):
            continue
        if abs(float(shot['depth'][row, column]) - depth[i]) > DEPTH_SLACK:
            continue
        if 'brightness' in shot and shot['brightness'][row, column] < min_brightness:
            continue
        seen.append(i)
    return seen


class Metrics(Module):
    kind = 'metrics'
    publishes = ('metrics/summary',)
    limitations = (
        'Coverage counts fence points the camera showed; whether a fox there would have been recognised depends on '
        'the detector, which is measured separately (time to recognise, false alarms).',
        'Route deviation is measured only while patrolling, not while chasing a fox or docking.',
        'Energy per lap includes everything drawn during that lap, also standing still for an obstacle or a fox.',
    )

    def __init__(self, scenario, height_at, robot_body=None):
        super().__init__('metrics', 'Metrics')
        self.height_at, self.robot_body = height_at, robot_body
        self.configure(scenario)
        self.reset()

    def configure(self, scenario):
        self.points = fence_points(scenario['coop'], self.height_at)
        self.min_brightness = scenario['detector']['min_brightness']
        self.min_pixels = scenario['detector']['min_pixels']

    def reset(self):
        self.time = 0.
        self.state_time = {}
        self.route_errors = []          # cross-track errors while patrolling, one per decision
        self.laps = []                  # {'time', 'seconds', 'energy_wh', 'coverage', 'mean_deviation', 'max_deviation', 'falls'}
        self.lap_started, self.lap_energy, self.lap_errors, self.lap_falls = 0., 0., [], 0
        self.seen = set()               # fence points seen in the current lap
        self.seen_all = set()           # fence points seen at all since the start
        self.own_view = []              # share of each camera frame that shows the robot itself
        self.falls = self.self_rights = self.obstacle_stops = 0
        self.alarms = []                # {'time', 'true', 'detector'}
        self.unconfirmed = 0
        self.fox = {'appeared_at': None, 'in_view_at': None, 'alarm_at': None, 'fled_at': None}
        self.docking = []               # {'time', 'success', 'attempts', 'lateral', 'longitudinal', 'heading'}
        self.distance, self._last_xy = 0., None
        self.energy_used = 0.

    # Recording

    def tick(self, time, dt, state, xy):
        self.time = time
        self.state_time[state] = self.state_time.get(state, 0.) + dt
        # Distance from positions a second apart: the body sways sideways within every step, which is no distance.
        if self._last_xy is None or time - self._last_xy[2] >= DISTANCE_EVERY:
            if self._last_xy is not None:
                self.distance += math.hypot(xy[0] - self._last_xy[0], xy[1] - self._last_xy[1])
            self._last_xy = [xy[0], xy[1], time]

    def route_error(self, distance):
        self.route_errors.append(distance)
        self.lap_errors.append(distance)

    def camera_frame(self, time, shot, settings, truth):
        """A new camera frame: fence coverage, and whether the fox is really in view (for the detection times)."""
        if shot is not None and 'position' in shot:
            seen = visible_points(self.points, shot, settings, self.min_brightness)
            self.seen.update(seen)
            self.seen_all.update(seen)
        if shot is not None and self.robot_body is not None and 'segmentation' in shot:
            self.own_view.append(float((shot['segmentation'] == self.robot_body).mean()))  # legs in the picture
        fox = (truth or {}).get('objects', {}).get('fox')
        if fox and fox.get('lit_pixels', 0) >= self.min_pixels and self.fox['in_view_at'] is None:
            self.fox['in_view_at'] = time

    def lap(self, time, energy_used):
        errors = self.lap_errors or [0.]
        self.laps.append({'lap': len(self.laps) + 1, 'time': round(time, 2), 'seconds': round(time - self.lap_started, 2),
                          'energy_wh': round(energy_used - self.lap_energy, 4),
                          'coverage': round(len(self.seen) / len(self.points), 3),
                          'mean_deviation': round(float(np.mean(errors)), 4),
                          'max_deviation': round(float(np.max(errors)), 4), 'falls': self.lap_falls})
        self.lap_started, self.lap_energy, self.lap_errors, self.lap_falls = time, energy_used, [], 0
        self.seen = set()

    def fall(self):
        self.falls += 1
        self.lap_falls += 1

    def alarm(self, time, true, detector):
        self.alarms.append({'time': round(time, 2), 'true': bool(true), 'detector': detector})
        if true and self.fox['alarm_at'] is None:
            self.fox['alarm_at'] = time

    def dock(self, time, success, attempts, errors):
        self.docking.append({'time': round(time, 2), 'success': bool(success), 'attempts': attempts,
                             **{k: round(v, 4) for k, v in errors.items()}})

    def fox_events(self, fox):
        """Copy appear and flee times from the actors' fox record."""
        if fox:
            for key in ('appeared_at', 'fled_at'):
                if fox.get(key) is not None and self.fox[key] is None:
                    self.fox[key] = fox[key]

    # Reading

    def summary(self, energy_used=None):
        if energy_used is not None:
            self.energy_used = energy_used
        fox = self.fox
        since = lambda a, b: round(fox[a] - fox[b], 2) if fox[a] is not None and fox[b] is not None else None
        docked = [d for d in self.docking if d['success']]
        mean = lambda values: round(float(np.mean(values)), 4) if values else None
        laps = self.laps
        return {
            'time': round(self.time, 2), 'distance_m': round(self.distance, 3), 'laps': len(laps),
            'route_deviation_m': {'mean': mean(self.route_errors), 'max': round(max(self.route_errors), 4)
                                  if self.route_errors else None},
            'falls': self.falls, 'self_rights': self.self_rights, 'obstacle_stops': self.obstacle_stops,
            'coverage': {'per_lap': [lap['coverage'] for lap in laps], 'mean': mean([lap['coverage'] for lap in laps]),
                         'current_lap': round(len(self.seen) / len(self.points), 3),
                         'run': round(len(self.seen_all) / len(self.points), 3), 'points': len(self.points)},
            'fox': {**{k: (round(v, 2) if v is not None else None) for k, v in fox.items()},
                    'time_to_alarm_s': since('alarm_at', 'appeared_at'),
                    'time_to_alarm_in_view_s': since('alarm_at', 'in_view_at'),
                    'time_to_flee_s': since('fled_at', 'alarm_at')},
            'alarms': {'true': sum(a['true'] for a in self.alarms), 'false': sum(not a['true'] for a in self.alarms),
                       'unconfirmed': self.unconfirmed, 'list': self.alarms[-20:]},
            'docking': {'attempts': sum(d['attempts'] for d in self.docking), 'dockings': len(self.docking),
                        'successes': len(docked),
                        'success_rate': round(len(docked) / len(self.docking), 3) if self.docking else None,
                        'mean_lateral_m': mean([abs(d['lateral']) for d in docked]),
                        'mean_heading_deg': mean([abs(d['heading']) for d in docked]), 'list': self.docking[-20:]},
            'energy': {'used_wh': round(self.energy_used, 4),
                       'per_lap_wh': [lap['energy_wh'] for lap in laps],
                       'mean_per_lap_wh': mean([lap['energy_wh'] for lap in laps])},
            'lap_list': laps[-50:],
            'camera': {'own_share_mean': mean(self.own_view), 'own_share_max': round(max(self.own_view), 4)
                       if self.own_view else None, 'frames': len(self.own_view)},
            'state_time_s': {k: round(v, 2) for k, v in self.state_time.items()},
        }

    def config(self):
        return {'coverage_points': len(self.points), 'point_spacing_m': POINT_SPACING}

    def self_test(self):
        points = self.points
        spacing = [math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(points, points[1:])]
        return [
            check('Coverage points surround the run', len(points) >= 8, f'{len(points)} points'),
            check('Coverage points are evenly spaced', spacing and max(spacing) < 2 * POINT_SPACING,
                  f'largest gap {max(spacing):.2f} m' if spacing else 'no points'),
            check('Coverage of the current lap is a share', 0 <= len(self.seen) <= len(points),
                  f'{len(self.seen)} of {len(points)} seen this lap'),
        ]
