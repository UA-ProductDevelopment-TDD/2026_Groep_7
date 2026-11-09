"""Robot-centred frames, so sensors can be placed without knowing the URDF's own axes.

Sensor positions and rotations are given in body axes: x forward, y left, z up. A Mount is fixed to one link and
follows it when joints move (a head camera turns with the neck). At the zero pose its axes equal the body axes.
"""
import math

import pybullet as p

# Direction of the robot's forward axis, as a yaw angle inside the base link frame.
AXIS_ANGLE = {'+x': 0., '+y': math.pi / 2, '-x': math.pi, '-y': -math.pi / 2}
IDENTITY = (0., 0., 0., 1.)


def body_alignment(forward_axis):
    """Rotation from body axes (x forward, y left, z up) to the base link's axes."""
    return p.getQuaternionFromEuler([0, 0, AXIS_ANGLE[forward_axis]])


def base_yaw(heading_deg, forward_axis):
    """Base link yaw (radians) that points the robot's forward axis along a world heading (degrees, 0 = +x)."""
    return math.radians(heading_deg) - AXIS_ANGLE[forward_axis]


def rotate(quaternion, vector):
    return list(p.multiplyTransforms([0, 0, 0], quaternion, vector, IDENTITY)[0])


def multiply(a, b):
    return list(p.multiplyTransforms([0, 0, 0], a, [0, 0, 0], b)[1])


def inverse(quaternion):
    return list(p.invertTransform([0, 0, 0], quaternion)[1])


def link_frame(client, body, index):
    """World position and xyzw quaternion of a link's URDF frame (-1 = base), not its centre of mass."""
    if index < 0:
        position, quaternion = p.getBasePositionAndOrientation(body, physicsClientId=client)
        dynamics = p.getDynamicsInfo(body, -1, physicsClientId=client)
        inv_pos, inv_quat = p.invertTransform(dynamics[3], dynamics[4])
        position, quaternion = p.multiplyTransforms(position, quaternion, inv_pos, inv_quat)
        return list(position), list(quaternion)
    state = p.getLinkState(body, index, computeForwardKinematics=1, physicsClientId=client)
    return list(state[4]), list(state[5])


def link_velocity(client, body, index):
    """World linear (m/s) and angular (rad/s) velocity of a link (-1 = base)."""
    if index < 0:
        linear, angular = p.getBaseVelocity(body, physicsClientId=client)
        return list(linear), list(angular)
    state = p.getLinkState(body, index, computeLinkVelocity=1, computeForwardKinematics=1, physicsClientId=client)
    return list(state[6]), list(state[7])


def heading(client, body, forward_axis):
    """World heading of the robot's forward axis, degrees (0 = +x, 90 = +y)."""
    _, quaternion = p.getBasePositionAndOrientation(body, physicsClientId=client)
    forward = rotate(quaternion, rotate(body_alignment(forward_axis), [1, 0, 0]))
    return math.degrees(math.atan2(forward[1], forward[0]))


def zero_rotations(client, body, links):
    """Each link's orientation relative to the base at the current pose; call it once at the zero pose."""
    _, base = link_frame(client, body, -1)
    base_inverse = inverse(base)
    return {name: multiply(base_inverse, link_frame(client, body, index)[1]) for name, index in links.items()}


class Mount:
    """A point and orientation on one robot link, given in body axes (x forward, y left, z up) at the zero pose.

    robot needs: client, robot (Bullet body id), links {name: index}, zero_rotations {name: quaternion}, alignment.
    """

    def __init__(self, robot, link, position=(0, 0, 0), rotation_deg=(0, 0, 0)):
        if link not in robot.links:
            raise ValueError(f'Link {link} is not part of this robot')
        self.robot, self.link, self.index = robot, link, robot.links[link]
        self.position = [float(v) for v in position]
        self.rotation_deg = [float(v) for v in rotation_deg]
        self.local = p.getQuaternionFromEuler([math.radians(v) for v in self.rotation_deg])
        # Body axes expressed in this link's frame at the zero pose; the product follows the link as it moves.
        self.aligned = multiply(inverse(robot.zero_rotations[link]), robot.alignment)

    def frame(self):
        """World position and xyzw quaternion of the mount: its x axis is the looking direction, z is up."""
        link_position, link_quaternion = link_frame(self.robot.client, self.robot.robot, self.index)
        body = multiply(link_quaternion, self.aligned)
        position = p.multiplyTransforms(link_position, body, self.position, IDENTITY)[0]
        return list(position), multiply(body, self.local)

    def axes(self):
        """World position plus unit vectors (forward, left, up) of the mount."""
        position, quaternion = self.frame()
        return position, rotate(quaternion, [1, 0, 0]), rotate(quaternion, [0, 1, 0]), rotate(quaternion, [0, 0, 1])
