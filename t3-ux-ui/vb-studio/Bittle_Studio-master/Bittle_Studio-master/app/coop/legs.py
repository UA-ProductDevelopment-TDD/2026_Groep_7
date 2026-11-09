"""Leg design for the bundled Bittle: longer upper and lower legs, shoulders angled outward or moved, knees reversed.

generate() writes a variant of robot-models/bittle/bittle.urdf: leg meshes are stretched along the leg (visual and
collision alike), the knee joint moves with the upper leg's length, leg masses grow with their length, and the
shoulder mounts are tilted outward (splay, seen from the front), turned outward (fan, seen from above) or shifted
forward/back as a 3D-printed bracket would. Lengths are measured in the plane the leg swings in: upper = shoulder
axis to knee axis, lower = knee axis to the foot tip.

Stock Bittle's knees all point backward. A knee set to point forward gets its lower leg mounted half a turn round on
the knee servo: at the zero pose the shin then sticks out backward instead of forward, and the leg is the mirror
image of a stock leg, joint limits included.
"""
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from functools import lru_cache

import numpy as np
import pybullet as p
import trimesh

from engine import ASSETS

BITTLE = ASSETS / 'bittle'
GENERATED = BITTLE / 'generated'  # git-ignored; meshes stay shared through ../obj and ../head
LEGS = ('left-front', 'right-front', 'left-back', 'right-back')
LIMITATIONS = (
    'Leg parts are the stock meshes stretched along the leg: a real printed leg has its own shape and stiffness.',
    'Leg mass grows in proportion to length; weigh the printed parts and add the difference as payload.',
    'The splay and fan angles turn each shoulder mount; the bracket itself is not modelled.',
    'A forward-pointing knee is the stock lower leg turned half a turn on its servo, with mirrored joint limits; '
    'check on the real parts that the shin clears the thigh.',
)
KNEE_AXIS_TURN = (0., 0., math.pi)  # the knee joint turns about its link's z axis


def _rotation(rpy):
    return np.array(p.getMatrixFromQuaternion(p.getQuaternionFromEuler(rpy))).reshape(3, 3)


def _numbers(text, default=(0, 0, 0)):
    return [float(v) for v in text.split()] if text else list(default)


def _fmt(values):
    return ' '.join(f'{v:.9g}' for v in values)


UPPER_AXIS, LOWER_AXIS = 1, 0  # link axes along the upper leg (shoulder frame y) and lower leg (knee frame x)


def _mesh_axis(origin_rpy, link_axis):
    """Index of the mesh axis that the visual rotation lays along a link axis."""
    return int(np.argmax(np.abs(_rotation(origin_rpy)[link_axis, :])))


@lru_cache(maxsize=1)
def stock():
    """Stock in-plane lengths per leg (metres) and the foot tip in each knee frame, read from the bundled model.

    At Bittle's zero (calibration) pose the thigh hangs down and the shin sticks out level at a right angle, so the
    shin runs along its knee frame's x axis.
    """
    tree = ET.parse(BITTLE / 'bittle.urdf').getroot()
    joints = {j.get('name'): j for j in tree.findall('joint')}
    links = {l.get('name'): l for l in tree.findall('link')}
    result = {}
    for leg in LEGS:
        knee = _numbers(joints[f'{leg}-knee-joint'].find('origin').get('xyz'))
        collision = links[f'{leg}-knee-link'].find('collision')
        origin = collision.find('origin')
        mesh = collision.find('geometry/mesh')
        vertices = trimesh.load(str(BITTLE / mesh.get('filename')), force='mesh', process=False).vertices
        points = np.asarray(vertices) * _numbers(mesh.get('scale'), (1, 1, 1)) @ _rotation(_numbers(origin.get('rpy'))).T
        points += _numbers(origin.get('xyz'))
        tip = points[np.argmax(np.hypot(points[:, 0], points[:, 1]))]  # farthest from the knee axis in the leg plane
        result[leg] = {'upper': math.hypot(knee[0], knee[1]), 'lower': math.hypot(tip[0], tip[1]),
                       'knee': knee, 'tip': tip.tolist()}
    return result


def stock_design():
    reference = stock()['left-front']
    return {'upper': reference['upper'], 'lower': reference['lower'], 'splay': 0., 'fan': 0., 'front_offset': 0.,
            'rear_offset': 0., 'front_knees': 'backward', 'rear_knees': 'backward'}


def is_stock(legs):
    """True when a leg design is the bundled Bittle as it is (within half a millimetre)."""
    reference = stock()['left-front']
    return (abs(legs['upper'] - reference['upper']) < 5e-4 and abs(legs['lower'] - reference['lower']) < 5e-4
            and abs(legs['splay']) < .05 and abs(legs.get('fan', 0)) < .05 and abs(legs['front_offset']) < 5e-4
            and abs(legs['rear_offset']) < 5e-4
            and legs.get('front_knees', 'backward') == legs.get('rear_knees', 'backward') == 'backward')


def knee_forward(leg, legs):
    """True when this leg's knee points forward (its lower leg is mounted the other way round)."""
    return legs.get('front_knees' if 'front' in leg else 'rear_knees', 'backward') == 'forward'


def factors(leg, legs):
    """How much one leg's upper and lower parts are stretched so their in-plane lengths match the design."""
    reference = stock()[leg]
    knee, tip = reference['knee'], reference['tip']
    return (math.sqrt(max(legs['upper'] ** 2 - knee[0] ** 2, 1e-8)) / abs(knee[1]),
            math.sqrt(max(legs['lower'] ** 2 - tip[1] ** 2, 1e-8)) / abs(tip[0]))


def foot_tip(leg, legs):
    """The foot tip in the knee link's frame (metres) for a leg design: the stock tip, stretched along the shin and
    turned half a turn about the knee axis when the knee points forward."""
    tip = list(stock()[leg]['tip'])
    if not is_stock(legs):
        tip[LOWER_AXIS] *= factors(leg, legs)[1]
    if knee_forward(leg, legs):
        tip = [-tip[0], -tip[1], tip[2]]
    return tip


def _stretch(xyz, axis, factor):
    return [v * factor if i == axis else v for i, v in enumerate(xyz)]


def _stretch_link(link, axis, factor):
    """Stretch a link's visuals, collisions and centre of mass along one of its axes; its mass grows with the length."""
    for node in link.findall('visual') + link.findall('collision'):
        origin = node.find('origin')
        xyz, rpy = _numbers(origin.get('xyz')), _numbers(origin.get('rpy'))
        origin.set('xyz', _fmt(_stretch(xyz, axis, factor)))
        mesh = node.find('geometry/mesh')
        if mesh is not None:
            scale = _numbers(mesh.get('scale'), (1, 1, 1))
            scale[_mesh_axis(rpy, axis)] *= factor
            mesh.set('scale', _fmt(scale))
    inertial = link.find('inertial')
    origin = inertial.find('origin')
    origin.set('xyz', _fmt(_stretch(_numbers(origin.get('xyz')), axis, factor)))
    mass = inertial.find('mass')
    mass.set('value', f"{float(mass.get('value')) * factor:.6g}")


def _turn_link(link):
    """Turn a link's visuals, collisions and centre of mass half a turn about its z axis (the knee axis)."""
    for node in link.findall('visual') + link.findall('collision') + link.findall('inertial'):
        origin = node.find('origin')
        xyz, rpy = _numbers(origin.get('xyz')), _numbers(origin.get('rpy'))
        turned = p.multiplyTransforms([0, 0, 0], p.getQuaternionFromEuler(KNEE_AXIS_TURN), xyz,
                                      p.getQuaternionFromEuler(rpy))
        origin.set('xyz', _fmt(turned[0]))
        origin.set('rpy', _fmt(p.getEulerFromQuaternion(turned[1])))


def _mirror_limits(joint):
    """A mirrored leg folds the other way: the knee's limits swap sides."""
    limit = joint.find('limit')
    lower, upper = float(limit.get('lower')), float(limit.get('upper'))
    limit.set('lower', f'{-upper:.9g}')
    limit.set('upper', f'{-lower:.9g}')


def _relative(path):
    """Mesh paths from the generated folder back to the bundled meshes."""
    return '../' + path if not path.startswith('../') else path


def generate(legs):
    """Path of the URDF for a leg design (written once per design), or the bundled URDF for the stock design."""
    if is_stock(legs):
        return BITTLE / 'bittle.urdf'
    key = hashlib.sha256(json.dumps(legs, sort_keys=True).encode()).hexdigest()[:16]
    path = GENERATED / f'bittle-legs-{key}.urdf'
    if path.is_file():
        return path
    tree = ET.parse(BITTLE / 'bittle.urdf')
    root = tree.getroot()
    root.set('name', 'bittle-legs')
    joints = {j.get('name'): j for j in root.findall('joint')}
    links = {l.get('name'): l for l in root.findall('link')}
    for leg in LEGS:
        # Stretch along the leg so the in-plane length becomes the target; the small offset across it stays.
        upper_factor, lower_factor = factors(leg, legs)
        _stretch_link(links[f'{leg}-shoulder-link'], UPPER_AXIS, upper_factor)
        _stretch_link(links[f'{leg}-knee-link'], LOWER_AXIS, lower_factor)
        if knee_forward(leg, legs):
            _turn_link(links[f'{leg}-knee-link'])
            _mirror_limits(joints[f'{leg}-knee-joint'])
        knee_origin = joints[f'{leg}-knee-joint'].find('origin')
        xyz = _numbers(knee_origin.get('xyz'))
        knee_origin.set('xyz', _fmt([xyz[0], xyz[1] * upper_factor, xyz[2]]))
        shoulder = joints[f'{leg}-shoulder-joint'].find('origin')
        xyz, rpy = _numbers(shoulder.get('xyz')), _numbers(shoulder.get('rpy'))
        # The base frame's +y points forward and +x to the right: tilt left legs toward -x, right legs toward +x.
        side = 1 if leg.startswith('left') else -1
        quaternion = p.getQuaternionFromAxisAngle([0, 1, 0], math.radians(legs['splay']) * side)
        # Then turn the mount about the vertical: front legs toward the front corners, rear legs toward the rear ones.
        fan = math.radians(legs.get('fan', 0)) * side * (1 if 'front' in leg else -1)
        quaternion = p.multiplyTransforms([0, 0, 0], p.getQuaternionFromAxisAngle([0, 0, 1], fan),
                                          [0, 0, 0], quaternion)[1]
        quaternion = p.multiplyTransforms([0, 0, 0], quaternion, [0, 0, 0], p.getQuaternionFromEuler(rpy))[1]
        shift = legs['front_offset'] if 'front' in leg else -legs['rear_offset']
        shoulder.set('xyz', _fmt([xyz[0], xyz[1] + shift, xyz[2]]))
        shoulder.set('rpy', _fmt(p.getEulerFromQuaternion(quaternion)))
    for mesh in root.iter('mesh'):
        mesh.set('filename', _relative(mesh.get('filename')))
    GENERATED.mkdir(exist_ok=True)
    temporary = path.with_suffix('.tmp')
    tree.write(temporary, encoding='unicode', xml_declaration=True)
    temporary.replace(path)
    return path
