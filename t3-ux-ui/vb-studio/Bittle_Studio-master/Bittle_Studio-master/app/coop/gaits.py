"""Generated gaits: foot paths turned into joint angles by inverse kinematics, for any Bittle leg design.

Petoi's own skills are joint-angle tables made for the stock legs; longer or splayed legs need angles worked out
from where the feet should go. Each leg swings in one plane (shoulder and knee turn about parallel axes), so a foot
target in that plane gives the two joint angles directly (two-link inverse kinematics).

Body axes as everywhere in the coop simulator: x forward, y left, z up, from the base link origin. A plan has the
skills.py format, so robot.play_skill() plays it like a Petoi gait.
"""
import math

import numpy as np
import pybullet as p

from coop import frames
from coop import legs as leg_design

LEGS = leg_design.LEGS
FRAME_S = .02       # one gait frame per 20 ms, like Petoi's gaits in skills.py
POSTURE_S = .4      # easing into the first frame
DUTY = {'crawl': .75, 'trot': .5, 'crab': .6}  # share of the cycle a foot is on the ground
# When each leg starts its stance within the cycle. Crawl: one foot at a time, hind then front on each side.
# Trot and crab: diagonal pairs. The crab's longer stance gives a moment with all four feet down at each change.
PHASE = {'crawl': {'left-back': 0., 'left-front': .25, 'right-back': .5, 'right-front': .75},
         'trot': {'left-front': 0., 'right-back': 0., 'right-front': .5, 'left-back': .5},
         'crab': {'left-front': 0., 'right-back': 0., 'right-front': .5, 'left-back': .5}}
LIFT = .25          # crab swing: share spent lifting straight up, and again setting the foot straight down
# Stride per side for each motion (1 = the full stride forward, negative = backward).
MOTIONS = {'forward': (1, 1), 'backward': (-1, -1), 'left': (.3, 1), 'right': (1, .3),
           'veer-left': (.6, 1), 'veer-right': (1, .6), 'spin-left': (-1, 1), 'spin-right': (1, -1), 'stance': (0, 0)}
LIMITATIONS = (
    'Gaits are open-loop: foot paths assume level ground and nothing reacts to bumps, slips or tilting.',
    'There is no body sway: in the crawl the centre of mass may leave the triangle of the three standing feet.',
)


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def measure(robot):
    """Leg geometry in body axes at the zero pose, or None when the robot does not have Bittle's four leg names.

    Call it right after loading, while every joint is at zero.
    """
    names = [f'{leg}-{part}' for leg in LEGS for part in ('shoulder', 'knee')]
    if not all(name + '-link' in robot.links for name in names):
        return None
    client, body = robot.client, robot.robot
    base_position, base_quaternion = frames.link_frame(client, body, -1)
    to_body = frames.inverse(frames.multiply(base_quaternion, robot.alignment))
    point = lambda world: np.array(frames.rotate(to_body, [world[i] - base_position[i] for i in range(3)]))
    direction = lambda world: np.array(frames.rotate(to_body, world))
    joints = {j['name']: j for j in robot.joints}
    standing = robot.petoi_balance()  # only to choose which way the knees bend
    legs = robot.settings.get('legs') or leg_design.stock_design()
    geometry = {}
    for leg in LEGS:
        shoulder, knee = robot.links[f'{leg}-shoulder-link'], robot.links[f'{leg}-knee-link']
        hip_position, hip_quaternion = frames.link_frame(client, body, shoulder)
        knee_position, knee_quaternion = frames.link_frame(client, body, knee)
        axis = _unit(direction(frames.rotate(hip_quaternion, p.getJointInfo(body, shoulder, physicsClientId=client)[13])))
        knee_axis = _unit(direction(frames.rotate(knee_quaternion, p.getJointInfo(body, knee, physicsClientId=client)[13])))
        hip, knee_point = point(hip_position), point(knee_position)
        tip = p.multiplyTransforms(knee_position, knee_quaternion, leg_design.foot_tip(leg, legs), frames.IDENTITY)[0]
        foot = point(tip)
        forward = _unit(np.array([1., 0, 0]) - axis[0] * axis)  # body forward, laid into the leg's plane
        across = np.cross(axis, forward)  # turning about +axis takes forward towards across
        flat = lambda v: np.array([v @ forward, v @ across])
        thigh, shin = flat(knee_point - hip), flat(foot - knee_point)
        geometry[leg] = {
            'shoulder': f'{leg}-shoulder-joint', 'knee': f'{leg}-knee-joint', 'hip': hip, 'forward': forward,
            'across': across, 'axis': axis, 'axial': float((foot - hip) @ axis),
            'upper': float(np.hypot(*thigh)), 'lower': float(np.hypot(*shin)),
            'thigh_angle': float(math.atan2(thigh[1], thigh[0])), 'shin_angle': float(math.atan2(shin[1], shin[0])),
            'knee_sign': 1. if knee_axis @ axis > 0 else -1.,
            'limits': {name: (joints[name]['lower'], joints[name]['upper'])
                       for name in (f'{leg}-shoulder-joint', f'{leg}-knee-joint')},
            'standing_knee': standing.get(f'{leg}-knee-joint', 0.),
            'knee_forward': leg_design.knee_forward(leg, legs),
        }
    return geometry


def solve(leg, target, points=None):
    """Shoulder and knee angles (degrees) that put the foot on target (body axes), and whether it was reachable.

    Out of reach, the leg stretches or folds as far as it can towards the target. A dict passed as points gets the
    knee and the foot of the chosen solution, in body axes.
    """
    # The foot sits a fixed distance along the shoulder axis from the hip; the rest of it moves in the leg's plane.
    offset = np.asarray(target, float) - leg['hip'] - leg['axial'] * leg['axis']
    # In that plane (spanned by forward and across) take the point with the target's forward position and height.
    # With splayed legs the foot's sideways position then follows from the tilt.
    flat = np.linalg.solve(np.array([[leg['forward'][0], leg['across'][0]], [leg['forward'][2], leg['across'][2]]]),
                           offset[[0, 2]])
    distance = float(np.hypot(*flat))
    upper, lower = leg['upper'], leg['lower']
    cosine = (distance ** 2 - upper ** 2 - lower ** 2) / (2 * upper * lower)
    reachable = -1 <= cosine <= 1
    best = None
    for bend in (1, -1):
        relative = bend * math.acos(min(1., max(-1., cosine)))  # angle from thigh to shin
        thigh = math.atan2(flat[1], flat[0]) - math.atan2(lower * math.sin(relative), upper + lower * math.cos(relative))
        shoulder = math.degrees(_wrap(thigh - leg['thigh_angle']))
        knee = math.degrees(_wrap(leg['knee_sign'] * (relative - leg['shin_angle'] + leg['thigh_angle'])))
        (s_lo, s_hi), (k_lo, k_hi) = leg['limits'][leg['shoulder']], leg['limits'][leg['knee']]
        inside = s_lo <= shoulder <= s_hi and k_lo <= knee <= k_hi
        # Which side of the line from the shoulder to the foot the knee is on (body x and z, seen from the side).
        knee_point = upper * (math.cos(thigh) * leg['forward'] + math.sin(thigh) * leg['across'])
        foot = flat[0] * leg['forward'] + flat[1] * leg['across']
        ahead = foot[0] * knee_point[2] - foot[2] * knee_point[0] > 0
        # Prefer a solution inside the joint limits whose knee points the way the design says, then the one closest
        # to the standing posture's knee.
        score = (not inside, ahead != leg.get('knee_forward', False), abs(knee - leg['standing_knee']))
        if best is None or score < best[0]:
            best = (score, shoulder, knee, inside, knee_point, thigh, relative)
    _, shoulder, knee, inside, knee_point, thigh, relative = best
    if points is not None:
        shin = thigh + relative
        foot = knee_point + lower * (math.cos(shin) * leg['forward'] + math.sin(shin) * leg['across'])
        points.update(knee=leg['hip'] + knee_point, foot=leg['hip'] + leg['axial'] * leg['axis'] + foot)
    return {leg['shoulder']: shoulder, leg['knee']: knee}, reachable and inside


def _wrap(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


def neutral(geometry, settings, leg):
    """Where a leg's foot stands in the stance (body axes)."""
    g = geometry[leg]
    reach = settings['front_reach'] if 'front' in leg else -settings['rear_reach']
    return g['hip'] + np.array([reach, 0., -settings['hip_height']])


def foot_path(settings, phase, stride):
    """Foot offset (forward, up) in metres at one point of the cycle: back along the ground, then lifted forward.

    Crawl and trot swing the foot in an arc. The crab lifts it straight up, carries it forward at full height and sets
    it straight down, so it neither drags through mud nor catches the edge of a stone.
    """
    duty = DUTY[settings['type']]
    if phase < duty:  # on the ground: the foot moves back as the body moves forward
        return stride * (.5 - phase / duty), 0.
    swing = (phase - duty) / (1 - duty)
    if settings['type'] == 'crab':
        ease = lambda t: (1 - math.cos(math.pi * min(1., max(0., t)))) / 2
        carry = ease((swing - LIFT) / (1 - 2 * LIFT))
        height = ease(swing / LIFT) if swing < .5 else ease((1 - swing) / LIFT)
        return stride * (-.5 + carry), settings['step_height'] * height
    return stride * (-.5 + (1 - math.cos(math.pi * swing)) / 2), settings['step_height'] * math.sin(math.pi * swing)


def frame(geometry, settings, motion, phase):
    """Joint angles for every leg at one point of the cycle, plus the legs whose foot target was out of reach."""
    left, right = MOTIONS[motion]
    pose, unreachable = {}, []
    for leg in LEGS:
        stride = settings['stride'] * (left if leg.startswith('left') else right)
        leg_phase = (phase - PHASE[settings['type']][leg]) % 1
        forward, up = foot_path(settings, leg_phase, stride) if motion != 'stance' else (0., 0.)
        angles, ok = solve(geometry[leg], neutral(geometry, settings, leg) + np.array([forward, 0., up]))
        pose.update(angles)
        if not ok:
            unreachable.append(leg)
    return pose, unreachable


def plan(robot, settings, motion='forward'):
    """A skills.py plan: ease into the first frame, then loop the cycle (the stance just holds)."""
    geometry = robot.gait_legs
    if geometry is None:
        raise ValueError('Generated gaits need a robot with Bittle\'s four legs (left/right-front/back shoulder and knee)')
    if motion not in MOTIONS:
        raise ValueError('Gait motion must be one of ' + ', '.join(MOTIONS))
    start, unreachable = frame(geometry, settings, motion, 0.)
    if unreachable:
        hint = (f"{', '.join(unreachable)}: feet {settings['hip_height'] * 1000:.0f} mm below the shoulders are out of "
                f"reach for these legs; change the hip height or the reach")
        raise ValueError('The stance cannot be reached. ' + hint)
    name = f"gait-{settings['type']}-{motion}"
    if motion == 'stance':
        return {'name': name, 'segments': [(POSTURE_S, start)], 'loop_from': None, 'ease': True, 'warnings': []}
    count = max(4, round(settings['cycle'] / FRAME_S))
    poses, warned = [], set()
    for i in range(count):
        pose, unreachable = frame(geometry, settings, motion, i / count)
        poses.append(pose)
        warned.update(unreachable)
    warnings = [f'Out of reach during the step: {", ".join(sorted(warned))}; shorten the stride or the step height']
    return {'name': name, 'segments': [(POSTURE_S, poses[0])] + [(settings['cycle'] / count, pose) for pose in poses],
            'loop_from': 1, 'warnings': warnings if warned else []}


def preview(robot, settings, motion='forward'):
    """The gait as a side view: per frame and leg the joint angles and where hip, knee and foot are (body x and z,
    metres), whether the foot is on the ground, plus each joint's range over the cycle. For the dashboard."""
    geometry = robot.gait_legs
    if geometry is None:
        raise ValueError('Generated gaits need a robot with Bittle\'s four legs')
    if motion not in MOTIONS:
        raise ValueError('Gait motion must be one of ' + ', '.join(MOTIONS))
    count = max(4, round(settings['cycle'] / FRAME_S))
    side = lambda v: [round(float(v[0]), 4), round(float(v[2]), 4)]
    left, right = MOTIONS[motion]
    frames, ranges, unreachable = [], {}, set()
    for i in range(count if motion != 'stance' else 1):
        phase, legs = i / count, {}
        for leg in LEGS:
            stride = settings['stride'] * (left if leg.startswith('left') else right)
            leg_phase = (phase - PHASE[settings['type']][leg]) % 1
            forward, up = foot_path(settings, leg_phase, stride) if motion != 'stance' else (0., 0.)
            points = {}
            angles, ok = solve(geometry[leg], neutral(geometry, settings, leg) + np.array([forward, 0., up]), points)
            if not ok:
                unreachable.add(leg)
            shoulder, knee = angles[geometry[leg]['shoulder']], angles[geometry[leg]['knee']]
            for joint, value in ((geometry[leg]['shoulder'], shoulder), (geometry[leg]['knee'], knee)):
                low, high = ranges.get(joint, (value, value))
                ranges[joint] = (min(low, value), max(high, value))
            legs[leg] = {'shoulder': round(shoulder, 2), 'knee': round(knee, 2), 'hip': side(geometry[leg]['hip']),
                         'knee_point': side(points['knee']), 'foot': side(points['foot']),
                         'stance': motion == 'stance' or leg_phase < DUTY[settings['type']]}
        frames.append({'phase': round(phase, 4), 'legs': legs})
    return {'motion': motion, 'type': settings['type'], 'cycle': settings['cycle'], 'duty': DUTY[settings['type']],
            'phase': PHASE[settings['type']], 'frames': frames,
            'ranges': {joint: [round(low, 2), round(high, 2)] for joint, (low, high) in ranges.items()},
            'limits': {name: [round(v, 2) for v in limits] for g in geometry.values()
                       for name, limits in g['limits'].items()},
            'knees': {leg: 'forward' if geometry[leg].get('knee_forward') else 'backward' for leg in LEGS},
            'unreachable': sorted(unreachable)}


def foot_positions(robot):
    """Current foot tips in body axes, from Bullet's link poses (to check the inverse kinematics)."""
    client, body = robot.client, robot.robot
    base_position, base_quaternion = frames.link_frame(client, body, -1)
    to_body = frames.inverse(frames.multiply(base_quaternion, robot.alignment))
    legs = robot.settings.get('legs') or leg_design.stock_design()
    result = {}
    for leg in LEGS:
        position, quaternion = frames.link_frame(client, body, robot.links[f'{leg}-knee-link'])
        tip = p.multiplyTransforms(position, quaternion, leg_design.foot_tip(leg, legs), frames.IDENTITY)[0]
        result[leg] = np.array(frames.rotate(to_body, [tip[i] - base_position[i] for i in range(3)]))
    return result
