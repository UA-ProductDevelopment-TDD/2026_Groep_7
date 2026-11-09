"""The robot: a URDF model (Bittle X by default) with the payload of the modules mounted on it, placed on the terrain."""
import math
import re

import pybullet as p

import skills
from coop import frames, gaits
from coop import legs as leg_design
from coop.config import BUNDLED_BITTLE
from coop.hub import Module, check
from engine import Simulation, upgrade_bundled_robot, url_path

FOOT_NAME = re.compile(r'knee|foot|paw|toe|shin|lower', re.I)
FALL_ANGLE = 60.  # degrees of body roll or pitch counted as a fall
CLEARANCE = .002  # metres between the lowest collision shape and the ground when the robot is placed


class CoopRobot(Simulation):
    """engine.Simulation's robot, loaded into the coop world's Bullet client.

    It keeps the Studio's joint control, servo mapping and Petoi skill playback, and adds body axes (frames.py),
    foot links for terrain friction, payload mass and placement on uneven ground.
    """
    physics_visuals = False

    def __init__(self, client, settings):
        path = url_path(settings['model'])
        if not path.is_file() or path.suffix.lower() not in ('.urdf', '.xacro'):
            raise ValueError('Robot model not found: ' + settings['model'])
        legs = settings.get('legs')
        if legs and settings['model'] == BUNDLED_BITTLE:
            path = leg_design.generate(legs)  # the bundled file itself for the stock design
        self.settings = settings
        self.forward_axis = settings['forward_axis']
        self.alignment = frames.body_alignment(self.forward_axis)
        super().__init__(client, upgrade_bundled_robot(path.read_text(encoding='utf-8'), path.parent), path.parent)
        self.zero_rotations = frames.zero_rotations(client, self.robot, self.links)
        self.gait_legs = gaits.measure(self)  # leg geometry at the zero pose, None when the legs are not Bittle's
        self.base_masses = {name: p.getDynamicsInfo(self.robot, index, physicsClientId=client)[0]
                            for name, index in self.links.items()}
        self.urdf_limits = {j['name']: (j['effort'], j['velocity']) for j in self.joints}
        self.feet = self._find_feet()
        self.payload = []
        self.apply_payload(settings['payload'])
        self.apply_servo(settings.get('servo'))

    def apply_servo(self, servo):
        """Every joint motor gets the servo's torque and speed; None keeps the URDF limits."""
        for j in self.joints:
            effort, velocity = self.urdf_limits[j['name']]
            j['effort'] = servo['torque'] if servo else effort
            j['velocity'] = math.radians(servo['speed']) if servo else velocity
        self.servo = servo

    def torques(self):
        """Torque each joint motor applied in the last physics step, in Nm (signed)."""
        return {j['name']: p.getJointState(self.robot, j['id'], physicsClientId=self.client)[3] for j in self.joints}

    def _find_feet(self):
        parents = {p.getJointInfo(self.robot, i, physicsClientId=self.client)[16]
                   for i in range(p.getNumJoints(self.robot, physicsClientId=self.client))}
        leaves = {name: index for name, index in self.links.items() if index >= 0 and index not in parents}
        named = {name: index for name, index in leaves.items() if FOOT_NAME.search(name)}
        if named:
            return named
        # No telling names: take the four lowest leaf links at the zero pose.
        lowest = sorted(leaves, key=lambda name: p.getAABB(self.robot, leaves[name], physicsClientId=self.client)[0][2])
        return {name: leaves[name] for name in lowest[:4]}

    def apply_payload(self, items):
        for name, index in self.links.items():
            p.changeDynamics(self.robot, index, mass=self.base_masses[name], physicsClientId=self.client)
        added = {}
        for item in items:
            if item['link'] not in self.links:
                raise ValueError(f"Payload {item['name']}: link {item['link']} is not part of this robot")
            added[item['link']] = added.get(item['link'], 0.) + item['mass']
        for name, mass in added.items():
            p.changeDynamics(self.robot, self.links[name], mass=self.base_masses[name] + mass, physicsClientId=self.client)
        self.payload = [dict(item) for item in items]

    def mass(self):
        return sum(p.getDynamicsInfo(self.robot, i, physicsClientId=self.client)[0] for i in self.links.values())

    def petoi_balance(self):
        """Petoi's balance posture through the robot's servo mapping, or the zero pose for other robots."""
        plan = skills.plan('kbalance', self.mapping)
        pose = plan['segments'][-1][1] if plan else {}
        return {j['name']: pose.get(j['name'], 0.) for j in self.joints}

    def standing_pose(self):
        """Stock legs stand in Petoi's balance posture; another leg design in its generated gait's stance."""
        legs = self.settings.get('legs')
        if self.gait_legs and legs and not leg_design.is_stock(legs) and self.settings.get('gait'):
            return {**self.petoi_balance(), **gaits.plan(self, self.settings['gait'], 'stance')['segments'][0][1]}
        return self.petoi_balance()

    def lowest_point(self):
        boxes = [p.getAABB(self.robot, i, physicsClientId=self.client)
                 for i in range(-1, p.getNumJoints(self.robot, physicsClientId=self.client))]
        return min(b[0][2] for b in boxes), [min(b[0][0] for b in boxes), min(b[0][1] for b in boxes),
                                             max(b[1][0] for b in boxes), max(b[1][1] for b in boxes)]

    def place(self, position, heading, height_at=None):
        """Stand the robot at (x, y) facing a world heading (degrees), its lowest shape just above the ground."""
        self.skill = None
        self.pose(self.standing_pose())
        quaternion = p.getQuaternionFromEuler([0, 0, frames.base_yaw(heading, self.forward_axis)])
        p.resetBasePositionAndOrientation(self.robot, [position[0], position[1], 1.], quaternion, physicsClientId=self.client)
        p.resetBaseVelocity(self.robot, [0, 0, 0], [0, 0, 0], physicsClientId=self.client)
        for j in self.joints:
            p.resetJointState(self.robot, j['id'], math.radians(self.targets[j['name']]), 0, physicsClientId=self.client)
        lowest, (x0, y0, x1, y1) = self.lowest_point()
        ground = 0.
        if height_at:
            ground = max(height_at(x0 + (x1 - x0) * i / 4, y0 + (y1 - y0) * k / 4) for i in range(5) for k in range(5))
        z = 1. + ground + CLEARANCE - lowest
        p.resetBasePositionAndOrientation(self.robot, [position[0], position[1], z], quaternion, physicsClientId=self.client)
        self.home_position, self.home_rotation = [position[0], position[1], z], [0., 0., frames.base_yaw(heading, self.forward_axis)]
        self._sensor_velocities.clear()

    def body_state(self, height_at=None):
        """Position, heading and body roll/pitch (about the forward and left axes), in degrees, plus a fall flag."""
        position, quaternion = frames.link_frame(self.client, self.robot, -1)
        roll, pitch, _ = p.getEulerFromQuaternion(frames.multiply(quaternion, self.alignment))
        linear, angular = frames.link_velocity(self.client, self.robot, -1)
        ground = height_at(position[0], position[1]) if height_at else 0.
        roll, pitch = math.degrees(roll), math.degrees(pitch)
        return {'position': position, 'heading': frames.heading(self.client, self.robot, self.forward_axis),
                'roll': roll, 'pitch': pitch, 'height': position[2] - ground, 'speed': math.hypot(linear[0], linear[1]),
                'turn_rate': math.degrees(angular[2]), 'fallen': abs(roll) > FALL_ANGLE or abs(pitch) > FALL_ANGLE}


class RobotModule(Module):
    kind = 'robot'
    publishes = ('robot/state',)
    base_limitations = (
        'Servos are ideal position motors limited to the scenario\'s servo torque and speed: no backlash, '
        'compliance, heating or battery voltage sag. The default 0.29 Nm is an unconfirmed retailer figure.',
        'Gaits (Petoi\'s skill frames and the generated ones) play open-loop; the firmware balance controller is not '
        'simulated.',
        'Payload adds mass to its link but keeps that link\'s inertia and centre of mass.',
        'Bullet uses the simplified collision shapes for contacts and for the simulated camera image.',
    )

    @property
    def limitations(self):
        legs = self.session.robot.settings.get('legs') if self.session.robot else None
        extra = leg_design.LIMITATIONS if legs and not leg_design.is_stock(legs) else ()
        return self.base_limitations + extra + gaits.LIMITATIONS

    def __init__(self, session):
        self.session = session
        super().__init__('robot', 'Robot')

    @property
    def robot(self):
        return self.session.robot

    def config(self):
        robot = self.robot
        legs = robot.settings.get('legs')
        return {'model': robot.settings['model'], 'forward_axis': robot.forward_axis, 'joints': len(robot.joints),
                'feet': sorted(robot.feet), 'mass_kg': round(robot.mass(), 4),
                'payload_kg': round(sum(item['mass'] for item in robot.payload), 4),
                'legs': 'stock' if not legs or leg_design.is_stock(legs) else legs, 'servo': robot.servo,
                'generated_gaits': robot.gait_legs is not None}

    def self_test(self):
        robot, world = self.robot, self.session.world
        base = sum(robot.base_masses.values())
        payload = sum(item['mass'] for item in robot.payload)
        state = robot.body_state(world.height_at)
        start = robot.settings['start']
        lowest, (x0, y0, x1, y1) = robot.lowest_point()
        ground = world.height_at((x0 + x1) / 2, (y0 + y1) / 2)
        checks = [
            check('Robot has actuated joints', robot.joints, f'{len(robot.joints)} joints'),
            check('Four feet found for terrain friction', len(robot.feet) == 4, ', '.join(sorted(robot.feet))),
            check('Payload mass is added', abs(robot.mass() - base - payload) < 1e-6,
                  f'{base:.3f} kg robot + {payload:.3f} kg payload = {robot.mass():.3f} kg'),
            check('Not fallen', not state['fallen'], f"roll {state['roll']:.0f}°, pitch {state['pitch']:.0f}°"),
            check('Lowest shape is near the ground', -.03 < lowest - ground < .05, f'{(lowest - ground) * 1000:.0f} mm'),
        ]
        if not self.session.running and self.session.time == 0:
            error = (state['heading'] - start['heading'] + 180) % 360 - 180
            checks.append(check('Faces the start heading', abs(error) < 1, f"{state['heading']:.1f}° (start {start['heading']:.1f}°)"))
        if robot.gait_legs and robot.settings.get('gait'):
            try:
                gaits.plan(robot, robot.settings['gait'], 'stance')
                checks.append(check('The generated gait\'s stance is within reach', True, robot.settings['gait']['type']))
            except ValueError as error:
                checks.append(check('The generated gait\'s stance is within reach', False, error))
        return checks
