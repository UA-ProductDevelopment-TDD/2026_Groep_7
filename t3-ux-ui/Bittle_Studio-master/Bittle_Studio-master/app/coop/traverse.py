"""Traverse test: leg designs walk the same course, each in a world of its own, and are compared side by side.

The course is the current scenario (terrain, mud, stones) from the robot's start position along its start heading.
Every run gets a fresh Bullet world without sensors, so the test does not disturb the running simulation and runs
much faster than real time.
"""
import math

import pybullet as p

import skills
from coop import config, gaits
from coop.robot import CoopRobot
from coop.world import World

SETTLE_S = 1.       # seconds to ease into the first frame before measuring
SAMPLE_EVERY = 6    # physics steps between measurements
EDGE = .15          # metres from the terrain edge where a run stops
SATURATED = .98


def variants(scenario):
    """(name, robot settings, (kind, command)) per run: stock legs with Petoi's walk and with the generated crawl,
    spider legs with the generated crawl, crab legs with the crab gait, and the current design when it is no preset."""
    robot = scenario['robot']
    stock, spider, crab = (config.LEG_PRESETS[name] for name in ('stock', 'spider', 'crab'))
    runs = [('Stock legs · Petoi walk', {**robot, **stock}, ('petoi', 'kwkF')),
            ('Stock legs · generated crawl', {**robot, **stock}, ('gait', 'forward')),
            ('Spider legs · generated crawl', {**robot, **spider}, ('gait', 'forward')),
            ('Crab legs · crab gait', {**robot, **crab}, ('gait', 'forward'))]
    if {'legs': robot['legs'], 'gait': robot['gait']} not in (stock, spider, crab):
        runs.append((f"Current design · generated {robot['gait']['type']}", robot, ('gait', 'forward')))
    return runs


def run_one(scenario, name, settings, walk, seconds):
    hz = scenario['simulation']['physics_hz']
    client = p.connect(p.DIRECT)
    try:
        p.setGravity(0, 0, -9.81, physicsClientId=client)
        p.setTimeStep(1 / hz, physicsClientId=client)
        p.setPhysicsEngineParameter(numSolverIterations=80, physicsClientId=client)
        world = World(client, scenario)
        robot = CoopRobot(client, settings)
        start = settings['start']
        robot.place(start['position'], start['heading'], world.height_at)
        robot.running = True
        plan = skills.plan(walk[1], robot.mapping) if walk[0] == 'petoi' else gaits.plan(robot, settings['gait'], walk[1])
        robot.play_skill(plan)
        stones = {uid for uid, item in world.bodies.items() if item['kind'] == 'stone'}
        limit = robot.servo['torque']

        def step():
            robot.advance_skill(1 / hz)
            robot.drive_motors()
            world.update_foot_friction(robot.robot, robot.feet)
            p.stepSimulation(physicsClientId=client)

        for _ in range(int(SETTLE_S * hz)):
            step()
        first = robot.body_state(world.height_at)
        if first['fallen']:  # a design that cannot even stand at the start is reported as such, not as a slow walker
            return {'name': name, 'walk': f'{walk[0]} {walk[1]}', 'legs': settings['legs'], 'mass': round(robot.mass(), 4),
                    'error': f"fell over while standing at the start (roll {first['roll']:.0f}°, "
                             f"pitch {first['pitch']:.0f}°)", 'distance': 0.}
        heading = math.radians(first['heading'])
        samples = falls = fallen = at_limit = in_mud = on_stone = 0
        torque_sum, was_fallen, edge = 0., first['fallen'], False
        half = [v / 2 - EDGE for v in scenario['terrain']['size']]
        for index in range(int(seconds * hz)):
            step()
            if index % SAMPLE_EVERY:
                continue
            state = robot.body_state(world.height_at)
            samples += 1
            falls += state['fallen'] and not was_fallen
            fallen += state['fallen']
            was_fallen = state['fallen']
            torques = [abs(v) for v in robot.torques().values()]
            at_limit += max(torques) >= SATURATED * limit
            torque_sum += sum(torques) / len(torques)
            feet = [p.getLinkState(robot.robot, i, physicsClientId=client)[0] for i in robot.feet.values()]
            in_mud += any(world.material_at(x, y)['material'] == 'mud' for x, y, _ in feet)
            on_stone += any(c[2] in stones for c in p.getContactPoints(bodyA=robot.robot, physicsClientId=client))
            if abs(state['position'][0]) > half[0] or abs(state['position'][1]) > half[1]:
                edge = True
                break
        last = robot.body_state(world.height_at)
        moved = [last['position'][i] - first['position'][i] for i in range(2)]
        walked = samples * SAMPLE_EVERY / hz
        share = lambda count: round(count / samples, 3) if samples else 0.
        forward = moved[0] * math.cos(heading) + moved[1] * math.sin(heading)
        return {
            'name': name, 'walk': f'{walk[0]} {walk[1]}', 'legs': settings['legs'],
            'gait': settings['gait'] if walk[0] == 'gait' else None, 'mass': round(robot.mass(), 4),
            'seconds': round(walked, 2), 'distance': round(forward, 4),
            'speed': round(forward / walked, 4) if walked else 0.,
            'sideways': round(-moved[0] * math.sin(heading) + moved[1] * math.cos(heading), 4),
            'turned': round((last['heading'] - first['heading'] + 180) % 360 - 180, 1),
            'falls': falls, 'fallen_share': share(fallen), 'at_limit_share': share(at_limit),
            'mean_torque': round(torque_sum / samples, 4) if samples else 0., 'mud_share': share(in_mud),
            'stone_share': share(on_stone), 'stopped_at_edge': edge, 'warnings': plan.get('warnings', []),
        }
    finally:
        p.disconnect(client)


def run(scenario, seconds=30.):
    """Every variant on the same course; a variant that cannot be built or walked is reported, not fatal."""
    if not 5 <= seconds <= 120:
        raise ValueError('A traverse test lasts 5 to 120 simulated seconds')
    runs = []
    for name, settings, walk in variants(scenario):
        try:
            runs.append(run_one(scenario, name, settings, walk, seconds))
        except ValueError as error:
            runs.append({'name': name, 'error': str(error), 'distance': 0.})
    return collect(scenario, seconds, runs)


def collect(scenario, seconds, runs):
    """The test result from its runs (also used when the runs went to worker processes)."""
    start = scenario['robot']['start']
    return {'seconds': seconds, 'start': start['position'], 'heading': start['heading'],
            'course': {'roughness': scenario['terrain']['roughness'], 'mud_patches': len(scenario['mud']),
                       'stones': scenario['stones']['count'], 'servo': scenario['robot']['servo']},
            'runs': runs}
