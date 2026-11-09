"""Scenario files: every setting of the coop simulation, validated in one place.

A scenario is plain JSON kept in coop-scenarios/. validate() fills in missing values from DEFAULT_SCENARIO and
rejects anything out of range with a message that names the setting, so a typo never becomes a silent default.
"""
import copy
import json
import math
import re

from engine import PROJECT

SCENARIOS = PROJECT / 'coop-scenarios'
SCENARIOS.mkdir(exist_ok=True)

SPEEDS = (0, .5, 1, 2, 4, 8)  # real-time factors; 0 runs as fast as the computer allows
SENSOR_TYPES = ('camera', 'tof', 'imu')
FORWARD_AXES = ('+x', '-x', '+y', '-y')
GAIT_TYPES = ('crawl', 'trot', 'crab')
KNEE_DIRECTIONS = ('backward', 'forward')
TIMES_OF_DAY = ('day', 'night')
VISITOR_KINDS = ('fox', 'person')
LOCOMOTION = ('auto', 'petoi', 'gait')  # auto: Petoi's skills for stock legs, the generated gait for other designs
DETECTOR_TYPES = ('ground-truth', 'colour-blob', 'external')
BUNDLED_BITTLE = '/assets/bittle/bittle.urdf'

STOCK_LEGS = {'upper': .0492, 'lower': .0550, 'splay': 0.0, 'fan': 0.0, 'front_offset': 0.0, 'rear_offset': 0.0,
              'front_knees': 'backward', 'rear_knees': 'backward'}
# Leg designs with a gait that suits them.
# Spider: legs 1.5 times as long, shoulders tilted 25° outward, front shoulders 2 cm further forward, a low and wide
# crawl with the front feet reaching ahead. All knees point backward, as on the stock Bittle.
# Crab: the same long legs, but the front legs are mounted mirrored so their knees point forward and the rear knees
# backward. The crab gait moves diagonal pairs (a crab's alternating leg sets), lifts each foot straight up and sets
# it straight down; the front feet reach ahead and pull, the rear feet reach back and push.
LEG_PRESETS = {
    'stock': {'legs': dict(STOCK_LEGS),
              'gait': {'type': 'crawl', 'hip_height': .07, 'stride': .03, 'step_height': .015, 'front_reach': 0.0,
                       'rear_reach': 0.0, 'cycle': 1.2}},
    # A 20 mm foot lift: in a sweep on level ground 30 mm made this crawl slip to under half its intended speed.
    'spider': {'legs': {**STOCK_LEGS, 'upper': .075, 'lower': .083, 'splay': 25.0, 'front_offset': .02},
               'gait': {'type': 'crawl', 'hip_height': .09, 'stride': .05, 'step_height': .02, 'front_reach': .04,
                        'rear_reach': .01, 'cycle': 1.6}},
    # Chosen in a sweep on level ground: 5.3 cm/s with 5° drift in 12 s. Without splay this narrow, tall trot tips
    # over; a body 85 mm up instead of 70 mm drifted more.
    'crab': {'legs': {**STOCK_LEGS, 'upper': .075, 'lower': .083, 'splay': 15.0, 'front_offset': .02,
                      'front_knees': 'forward'},
             'gait': {'type': 'crab', 'hip_height': .07, 'stride': .05, 'step_height': .02, 'front_reach': .03,
                      'rear_reach': .03, 'cycle': 1.2}},
}

DEFAULT_SCENARIO = {
    'format': 'coop-scenario',
    'version': 1,
    'name': 'Default coop',
    'notes': '',
    'simulation': {'physics_hz': 240, 'speed': 1},
    'terrain': {
        'size': [8.0, 8.0],         # metres along x and y, centred on the origin
        'resolution': .05,          # metres between height samples
        'roughness': .012,          # metres: standard deviation of the bumps (0 = flat)
        'feature_size': .5,         # metres: typical width of a bump
        'seed': 7,
        'friction': .8,             # dry ground
        'flat_margin': .3,          # metres of level ground kept around the fenced run and the dock
    },
    'mud': [
        {'id': 'mud-1', 'name': 'Mud at the south-east corner', 'center': [1.6, -1.5], 'radius': .45,
         'friction': .35, 'depth': .01},
    ],
    # Loose stones scattered outside the fenced run (none near the dock or the robot's start). Sizes in metres;
    # area None spreads them over the whole terrain, [x0, y0, x1, y1] keeps them inside that rectangle.
    'stones': {'count': 0, 'min_size': .02, 'max_size': .05, 'seed': 3, 'area': None},
    'coop': {
        'position': [0.0, 0.0],
        'yaw': 0.0,                 # degrees
        'run_size': [3.0, 2.0],     # fenced run, metres
        'fence_height': .6,
        'post_spacing': .5,
        'house_size': [1.0, .8, .7],  # stands inside the run against its -x fence
    },
    # Just south of the patrol route: the robot turns off the route, walks south into the dock and backs out again.
    'dock': {
        'position': [-1.0, -1.75],
        'yaw': -90.0,               # heading of the docked robot, degrees (0 = world +x)
        'capture_distance': .03,    # metres: how close the robot origin must come to latch
        'capture_angle': 10.0,      # degrees of heading error allowed to latch
        # metres from the dock position to the stop block: more than the robot reaches ahead of its origin (stock
        # Bittle 113 mm, the crab legs 171 mm while walking), or the robot is stopped before it is in the zone
        'stop_distance': .12,
    },
    'robot': {
        'model': '/assets/bittle/bittle.urdf',
        'forward_axis': '+y',       # which axis of the base link points forward (Bittle: +y)
        'start': {'position': [0.3, -1.5], 'heading': 0.0},  # on the patrol line south of the fence, facing +x
        'payload': [
            {'id': 'esp32-cam', 'name': 'ESP32-S3 camera board', 'mass': .012, 'link': 'base-frame-link'},
            {'id': 'tof-boards', 'name': 'Two VL53L0X boards', 'mass': .004, 'link': 'base-frame-link'},
        ],
        # Leg design (legs.py); these are the stock Bittle values. Lengths in metres, angles in degrees. Splay tilts
        # the legs outward seen from the front, fan turns them outward seen from above.
        'legs': dict(STOCK_LEGS),
        # Servo limits used by every joint motor. 0.29 Nm = 3 kg·cm, a retailer figure for Bittle's metal-gear
        # servo set that Petoi does not confirm; 350 °/s is the loaded speed skills.py already assumes.
        'servo': {'torque': .29, 'speed': 350.0},
        # Generated gait (gaits.py). Heights and lengths in metres, cycle in seconds.
        'gait': {'type': 'crawl', 'hip_height': .07, 'stride': .03, 'step_height': .015, 'front_reach': 0.0,
                 'rear_reach': 0.0, 'cycle': 1.2},
    },
    'sensors': [
        {'id': 'head-cam', 'type': 'camera', 'name': 'Head camera (ESP32-S3)', 'link': 'head-link',
         'position': [.05, 0, .01], 'rotation': [0, 0, 0], 'fov': 60, 'width': 160, 'height': 120,
         'range': 5.0, 'rate': 4},
        # Tilted 13° up (negative pitch): level at 10 cm height, the 25° cone would hit the ground at about 0.47 m.
        {'id': 'tof-left', 'type': 'tof', 'name': 'ToF left (VL53L0X)', 'link': 'base-frame-link',
         'position': [0, .03, 0], 'rotation': [0, -13, 90], 'range': 2.0, 'cone': 25, 'rays': 5, 'noise': .03,
         'rate': 20},
        {'id': 'tof-front', 'type': 'tof', 'name': 'ToF front (VL53L0X)', 'link': 'base-frame-link',
         'position': [.06, 0, 0], 'rotation': [0, -13, 0], 'range': 2.0, 'cone': 25, 'rays': 5, 'noise': .03,
         'rate': 20},
        {'id': 'imu', 'type': 'imu', 'name': 'Body IMU (MPU6050)', 'link': 'base-frame-link', 'noise': 0.0,
         'rate': 100},
    ],
    # Day or night. At night the camera sees moonlight only, plus whatever its infrared LEDs light up.
    'environment': {
        'time_of_day': 'day',
        'moonlight': .05,           # night brightness without infrared, as a share of daylight
        'ir_light': True,           # infrared LEDs next to the camera, switched on at night
        'ir_range': 2.5,            # metres up to which the infrared light makes things bright enough to see
    },
    # Chickens wander inside the fenced run, and some outside it around the run, where they get in the robot's way.
    'chickens': {'inside': 4, 'outside': 2, 'speed': .15, 'seed': 5},
    # Visitors walk their path (metres) from their appear time (seconds). With loop on they then pace the path back
    # and forth. A fox runs off when the robot, deterring, comes within its flee distance; a person never does.
    'visitors': [
        {'id': 'fox', 'kind': 'fox', 'name': 'Fox', 'appear': 40.0, 'speed': .3, 'loop': True, 'flee_distance': 1.0,
         'path': [[3.7, 3.2], [2.3, 1.6], [1.75, .6], [1.75, -.6], [1.0, -1.25], [-1.0, -1.25]]},
        {'id': 'farmer', 'kind': 'person', 'name': 'Farmer', 'appear': 120.0, 'speed': .9, 'loop': False,
         'flee_distance': 0.0, 'path': [[-3.7, 2.6], [0.0, 2.4], [3.7, 2.6]]},
    ],
    # Patrol: a closed loop of waypoints around the run, walked in this order. 'locomotion' auto walks with Petoi's
    # skills on stock legs and with the generated gait on any other leg design.
    'patrol': {
        'route': [[2.0, -1.5], [2.0, 1.5], [-2.0, 1.5], [-2.0, -1.5]],
        'tolerance': .25,           # metres from a waypoint that count as reaching it
        'locomotion': 'auto',
        'obstacle_sensor': 'tof-front',  # ToF sensor that makes the robot stop for an obstacle ('' = none)
        'obstacle_distance': .12,   # metres
    },
    # Recognising fox, chicken and person in the camera image. ground-truth knows what each pixel shows (an ideal
    # model), colour-blob looks for fox-orange, chicken-white and jacket-blue patches, external takes the detections
    # an outside program (the AI camera module) publishes on external_topic.
    'detector': {
        'type': 'ground-truth',
        'camera': 'head-cam',
        'min_pixels': 20,           # smallest object, in pixels, that counts
        'min_brightness': .15,      # darker pixels show nothing (night without enough light)
        'confirm': 2,               # frames in a row with a fox before the alarm goes off
        'external_topic': 'detections/external',
        'stale': 2.0,               # seconds after which an outside detection is too old to use
    },
    # The state machine: patrol -> detect -> deter -> back to the dock -> charge -> patrol.
    'behaviour': {
        'laps_before_charging': 0,  # also go and charge after this many laps (0 = only when low or after a fox)
        'low_battery': .3,          # state of charge at which the robot goes to the dock
        'resume_battery': .9,       # state of charge at which charging stops and the patrol resumes
        'deter_time': 10.0,         # seconds the deterrent stays on after the fox was last seen
        'chase_distance': .5,       # metres the deterring robot keeps from the fox
        'dock_attempts': 3,         # approaches before docking counts as failed
        'self_right': True,         # after a fall, stand up again where it lies (Bittle's firmware can)
    },
    # Battery and power. Assumed values: check the battery label and measure the boards' current.
    'energy': {
        'battery_wh': 7.4,          # 7.4 V x 1000 mAh
        'voltage': 7.4,
        'base_power': 1.5,          # W: BiBoard, ESP32-S3 camera board, ToF sensors
        'ir_power': 1.0,            # W while the infrared LEDs are on
        'servo_idle_current': .01,  # A per servo
        'servo_stall_current': 1.0,  # A per servo at the servo torque limit; current grows in proportion to torque
        'charge_power': 7.0,        # W into the battery while docked
        'start_charge': 1.0,        # state of charge at the start (0-1)
    },
}


def default():
    return copy.deepcopy(DEFAULT_SCENARIO)


def number(value, name, lo, hi, integer=False, unit=''):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a number')
    if not lo <= value <= hi:
        raise ValueError(f'{name} must be between {lo} and {hi}' + (' ' + unit if unit else ''))
    if integer:
        if value != int(value):
            raise ValueError(f'{name} must be a whole number')
        return int(value)
    return float(value)


def vector(value, name, length, lo, hi, unit=''):
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise ValueError(f'{name} must be a list of {length} numbers')
    return [number(v, f'{name}[{i}]', lo, hi, unit=unit) for i, v in enumerate(value)]


def text(value, name, limit=80, required=True):
    value = str(value if value is not None else '').strip()[:limit]
    if required and not value:
        raise ValueError(f'{name} is required')
    return value


def choice(value, name, options):
    if value not in options:
        raise ValueError(f'{name} must be one of ' + ', '.join(map(str, options)))
    return value


def flag(value, name):
    if not isinstance(value, bool):
        raise ValueError(f'{name} must be true or false')
    return value


def points(value, name, least, most, lo=-20, hi=20):
    if not isinstance(value, list) or not least <= len(value) <= most:
        raise ValueError(f'{name} must be a list of {least} to {most} points [x, y]')
    return [vector(point, f'{name} point {i + 1}', 2, lo, hi, unit='m') for i, point in enumerate(value)]


def identifier(value, name):
    value = str(value or '').strip()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,39}', value):  # ids become hub topics, which are lower-case
        raise ValueError(f'{name} must be 1-40 lower-case letters, digits, - or _')
    return value


def unique(items, name):
    ids = [item['id'] for item in items]
    if len(set(ids)) != len(ids):
        raise ValueError(f'Every {name} needs a unique id')
    return items


def _section(scenario, key):
    value = scenario.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f'{key} must be an object')
    return {**DEFAULT_SCENARIO[key], **value}


def _sensor(raw, index):
    if not isinstance(raw, dict):
        raise ValueError('Every sensor must be an object')
    kind = str(raw.get('type', '')).lower()
    if kind not in SENSOR_TYPES:
        raise ValueError(f'sensors[{index}].type must be one of {", ".join(SENSOR_TYPES)}')
    where = f'sensor {raw.get("name") or raw.get("id") or index}'
    sensor = {'id': identifier(raw.get('id'), where + ' id'), 'type': kind, 'name': text(raw.get('name'), where + ' name'),
              'link': text(raw.get('link'), where + ' link', 120)}
    if kind == 'imu':
        sensor['noise'] = number(raw.get('noise', 0), where + ' noise', 0, 1)
        sensor['rate'] = number(raw.get('rate', 100), where + ' rate', 1, 500, unit='Hz')
        return sensor
    sensor['position'] = vector(raw.get('position', [0, 0, 0]), where + ' position', 3, -.5, .5, unit='m')
    sensor['rotation'] = vector(raw.get('rotation', [0, 0, 0]), where + ' rotation', 3, -360, 360, unit='°')
    if kind == 'camera':
        sensor['fov'] = number(raw.get('fov', 60), where + ' field of view', 10, 170, unit='°')
        sensor['width'] = number(raw.get('width', 160), where + ' width', 32, 640, integer=True, unit='pixels')
        sensor['height'] = number(raw.get('height', 120), where + ' height', 24, 480, integer=True, unit='pixels')
        sensor['range'] = number(raw.get('range', 5), where + ' range', .1, 50, unit='m')
        sensor['rate'] = number(raw.get('rate', 4), where + ' rate', .2, 30, unit='Hz')
    else:
        sensor['range'] = number(raw.get('range', 2), where + ' range', .01, 10, unit='m')
        sensor['cone'] = number(raw.get('cone', 25), where + ' cone', 0, 90, unit='°')
        sensor['rays'] = number(raw.get('rays', 5), where + ' rays', 1, 25, integer=True)
        sensor['noise'] = number(raw.get('noise', .03), where + ' noise', 0, .5)
        sensor['rate'] = number(raw.get('rate', 20), where + ' rate', 1, 200, unit='Hz')
    return sensor


def validate(scenario):
    """A complete, checked copy of a scenario; missing settings take their defaults."""
    if not isinstance(scenario, dict):
        raise ValueError('A scenario must be a JSON object')
    if scenario.get('format', 'coop-scenario') != 'coop-scenario':
        raise ValueError('This file is not a coop scenario')
    if scenario.get('version', 1) != 1:
        raise ValueError('This scenario was made by a newer version')
    result = {'format': 'coop-scenario', 'version': 1, 'name': text(scenario.get('name', 'Coop scenario'), 'name'),
              'notes': text(scenario.get('notes', ''), 'notes', 4000, required=False)}

    s = _section(scenario, 'simulation')
    speed = s['speed']
    if speed not in SPEEDS:
        raise ValueError('simulation speed must be one of ' + ', '.join(map(str, SPEEDS)) + ' (0 = as fast as possible)')
    result['simulation'] = {'physics_hz': number(s['physics_hz'], 'physics Hz', 120, 1000, integer=True), 'speed': speed}

    t = _section(scenario, 'terrain')
    result['terrain'] = {
        'size': vector(t['size'], 'terrain size', 2, 2, 40, unit='m'),
        'resolution': number(t['resolution'], 'terrain resolution', .02, .5, unit='m'),
        'roughness': number(t['roughness'], 'terrain roughness', 0, .1, unit='m (0-100 mm)'),
        'feature_size': number(t['feature_size'], 'terrain feature size', .05, 5, unit='m'),
        'seed': number(t['seed'], 'terrain seed', 0, 2 ** 31 - 1, integer=True),
        'friction': number(t['friction'], 'ground friction', 0, 3),
        'flat_margin': number(t['flat_margin'], 'flat margin', 0, 3, unit='m'),
    }
    size = result['terrain']['size']
    if (size[0] / result['terrain']['resolution'] + 1) * (size[1] / result['terrain']['resolution'] + 1) > 250_000:
        raise ValueError('Terrain has too many height samples: use a coarser resolution or a smaller size')

    mud = scenario.get('mud', DEFAULT_SCENARIO['mud'])
    if not isinstance(mud, list) or len(mud) > 50:
        raise ValueError('mud must be a list of at most 50 patches')
    result['mud'] = unique([{
        'id': identifier(m.get('id'), 'mud id'), 'name': text(m.get('name', 'Mud'), 'mud name'),
        'center': vector(m.get('center'), 'mud centre', 2, -20, 20, unit='m'),
        'radius': number(m.get('radius'), 'mud radius', .05, 10, unit='m'),
        'friction': number(m.get('friction'), 'mud friction', 0, 3),
        'depth': number(m.get('depth', 0), 'mud depth', 0, .1, unit='m (0-100 mm)'),
    } for m in (item if isinstance(item, dict) else {} for item in mud)], 'mud patch')

    c = _section(scenario, 'coop')
    result['coop'] = {
        'position': vector(c['position'], 'coop position', 2, -20, 20, unit='m'),
        'yaw': number(c['yaw'], 'coop yaw', -360, 360, unit='°'),
        'run_size': vector(c['run_size'], 'run size', 2, .5, 20, unit='m'),
        'fence_height': number(c['fence_height'], 'fence height', .05, 3, unit='m'),
        'post_spacing': number(c['post_spacing'], 'post spacing', .1, 5, unit='m'),
        'house_size': vector(c['house_size'], 'house size', 3, .1, 10, unit='m'),
    }
    if any(h > r for h, r in zip(result['coop']['house_size'], result['coop']['run_size'])):
        raise ValueError('The house must fit inside the fenced run')

    d = _section(scenario, 'dock')
    result['dock'] = {
        'position': vector(d['position'], 'dock position', 2, -20, 20, unit='m'),
        'yaw': number(d['yaw'], 'dock yaw', -360, 360, unit='°'),
        'capture_distance': number(d['capture_distance'], 'dock capture distance', .001, .5, unit='m (1-500 mm)'),
        'capture_angle': number(d['capture_angle'], 'dock capture angle', .1, 90, unit='°'),
        'stop_distance': number(d['stop_distance'], 'dock stop distance', .03, .5, unit='m'),
    }

    r = _section(scenario, 'robot')
    start = r.get('start', {})
    if not isinstance(start, dict):
        raise ValueError('robot start must be an object')
    if r['forward_axis'] not in FORWARD_AXES:
        raise ValueError('robot forward axis must be one of ' + ', '.join(FORWARD_AXES))
    payload = r.get('payload', [])
    if not isinstance(payload, list) or len(payload) > 30:
        raise ValueError('payload must be a list of at most 30 items')
    result['robot'] = {
        'model': text(r['model'], 'robot model', 300),
        'forward_axis': r['forward_axis'],
        'start': {'position': vector(start.get('position', [0, 0]), 'robot start position', 2, -20, 20, unit='m'),
                  'heading': number(start.get('heading', 0), 'robot start heading', -360, 360, unit='°')},
        'payload': unique([{
            'id': identifier(item.get('id'), 'payload id'), 'name': text(item.get('name'), 'payload name'),
            'mass': number(item.get('mass'), 'payload mass', 0, 2, unit='kg (0-2000 g)'),
            'link': text(item.get('link'), 'payload link', 120),
        } for item in (raw if isinstance(raw, dict) else {} for raw in payload)], 'payload item'),
    }
    if not result['robot']['model'].startswith(('/assets/', '/data/')):
        raise ValueError('robot model must be an /assets/... or /data/... URDF path')
    legs = {**DEFAULT_SCENARIO['robot']['legs'], **(r.get('legs') or {})}
    result['robot']['legs'] = {
        'upper': number(legs['upper'], 'upper leg length', .03, .15, unit='m (30-150 mm)'),
        'lower': number(legs['lower'], 'lower leg length', .03, .15, unit='m (30-150 mm)'),
        'splay': number(legs['splay'], 'leg splay', 0, 45, unit='°'),
        'fan': number(legs['fan'], 'leg fan angle', 0, 45, unit='°'),
        'front_offset': number(legs['front_offset'], 'front shoulder offset', -.03, .06, unit='m (-30 to 60 mm)'),
        'rear_offset': number(legs['rear_offset'], 'rear shoulder offset', -.03, .06, unit='m (-30 to 60 mm)'),
        'front_knees': choice(legs['front_knees'], 'front knee direction', KNEE_DIRECTIONS),
        'rear_knees': choice(legs['rear_knees'], 'rear knee direction', KNEE_DIRECTIONS),
    }
    from coop import legs as leg_design  # imported here: legs.py reads the bundled model, config must stay light
    if result['robot']['model'] != BUNDLED_BITTLE and not leg_design.is_stock(result['robot']['legs']):
        raise ValueError('The leg design can only change the bundled Bittle; set the legs back to stock for this model')
    servo = {**DEFAULT_SCENARIO['robot']['servo'], **(r.get('servo') or {})}
    result['robot']['servo'] = {'torque': number(servo['torque'], 'servo torque', .02, 5, unit='Nm'),
                                'speed': number(servo['speed'], 'servo speed', 30, 2000, unit='°/s')}
    gait = {**DEFAULT_SCENARIO['robot']['gait'], **(r.get('gait') or {})}
    if gait['type'] not in GAIT_TYPES:
        raise ValueError('gait type must be one of ' + ', '.join(GAIT_TYPES))
    result['robot']['gait'] = {
        'type': gait['type'],
        'hip_height': number(gait['hip_height'], 'gait hip height', .02, .25, unit='m'),
        'stride': number(gait['stride'], 'gait stride', 0, .15, unit='m'),
        'step_height': number(gait['step_height'], 'gait step height', 0, .08, unit='m'),
        'front_reach': number(gait['front_reach'], 'front foot reach', -.08, .12, unit='m'),
        'rear_reach': number(gait['rear_reach'], 'rear foot reach', -.08, .12, unit='m'),
        'cycle': number(gait['cycle'], 'gait cycle', .3, 6, unit='s'),
    }

    stones = _section(scenario, 'stones')
    result['stones'] = {
        'count': number(stones['count'], 'stone count', 0, 500, integer=True),
        'min_size': number(stones['min_size'], 'smallest stone', .005, .2, unit='m'),
        'max_size': number(stones['max_size'], 'largest stone', .005, .2, unit='m'),
        'seed': number(stones['seed'], 'stone seed', 0, 2 ** 31 - 1, integer=True),
        'area': None if stones.get('area') is None else vector(stones['area'], 'stone area', 4, -20, 20, unit='m'),
    }
    if result['stones']['min_size'] > result['stones']['max_size']:
        raise ValueError('The smallest stone must not be larger than the largest stone')
    area = result['stones']['area']
    if area and (area[0] >= area[2] or area[1] >= area[3]):
        raise ValueError('The stone area is [x0, y0, x1, y1] with x0 < x1 and y0 < y1')
    for label, point in (('robot start', result['robot']['start']['position']), ('dock', result['dock']['position']),
                         ('coop', result['coop']['position'])):
        if abs(point[0]) > size[0] / 2 or abs(point[1]) > size[1] / 2:
            raise ValueError(f'The {label} position lies outside the terrain')

    sensors = scenario.get('sensors', DEFAULT_SCENARIO['sensors'])
    if not isinstance(sensors, list) or len(sensors) > 16:
        raise ValueError('sensors must be a list of at most 16 sensors')
    result['sensors'] = unique([_sensor(raw, i) for i, raw in enumerate(sensors)], 'sensor')
    _phase_two(scenario, result)
    return result


def _visitor(raw, index):
    if not isinstance(raw, dict):
        raise ValueError('Every visitor must be an object')
    where = f'visitor {raw.get("name") or raw.get("id") or index + 1}'
    kind = choice(raw.get('kind'), where + ' kind', VISITOR_KINDS)
    return {'id': identifier(raw.get('id'), where + ' id'), 'kind': kind,
            'name': text(raw.get('name', kind.capitalize()), where + ' name'),
            'appear': number(raw.get('appear', 0), where + ' appear time', 0, 86400, unit='s'),
            'speed': number(raw.get('speed', .3), where + ' speed', .02, 5, unit='m/s'),
            'loop': flag(raw.get('loop', False), where + ' loop'),
            'flee_distance': number(raw.get('flee_distance', 0), where + ' flee distance', 0, 10, unit='m'),
            'path': points(raw.get('path'), where + ' path', 2, 50)}


def _phase_two(scenario, result):
    """Environment, animals, patrol, detector, behaviour and energy (phase 2 sections)."""
    e = _section(scenario, 'environment')
    result['environment'] = {
        'time_of_day': choice(e['time_of_day'], 'time of day', TIMES_OF_DAY),
        'moonlight': number(e['moonlight'], 'moonlight', 0, 1),
        'ir_light': flag(e['ir_light'], 'infrared light'),
        'ir_range': number(e['ir_range'], 'infrared range', .1, 20, unit='m'),
    }
    c = _section(scenario, 'chickens')
    result['chickens'] = {
        'inside': number(c['inside'], 'chickens inside the run', 0, 30, integer=True),
        'outside': number(c['outside'], 'chickens outside the run', 0, 30, integer=True),
        'speed': number(c['speed'], 'chicken speed', 0, 2, unit='m/s'),
        'seed': number(c['seed'], 'chicken seed', 0, 2 ** 31 - 1, integer=True),
    }
    visitors = scenario.get('visitors', DEFAULT_SCENARIO['visitors'])
    if not isinstance(visitors, list) or len(visitors) > 10:
        raise ValueError('visitors must be a list of at most 10 visitors')
    result['visitors'] = unique([_visitor(raw, i) for i, raw in enumerate(visitors)], 'visitor')

    a = _section(scenario, 'patrol')
    sensor_ids = {s['id']: s['type'] for s in result['sensors']}
    result['patrol'] = {
        'route': points(a['route'], 'patrol route', 2, 40),
        'tolerance': number(a['tolerance'], 'waypoint tolerance', .05, 2, unit='m'),
        'locomotion': choice(a['locomotion'], 'patrol locomotion', LOCOMOTION),
        'obstacle_sensor': str(a['obstacle_sensor'] or ''),
        'obstacle_distance': number(a['obstacle_distance'], 'obstacle distance', 0, 1, unit='m'),
    }
    # A sensor that is not there (removed, or not added yet) is allowed: the behaviour's self-test reports it.
    obstacle = result['patrol']['obstacle_sensor']
    if obstacle and sensor_ids.get(obstacle, 'tof') != 'tof':
        raise ValueError(f'The obstacle sensor must be a ToF sensor, and {obstacle} is a {sensor_ids[obstacle]}')
    from coop import legs as leg_design
    if result['patrol']['locomotion'] == 'petoi' and not leg_design.is_stock(result['robot']['legs']):
        raise ValueError("Petoi's skills only fit the stock legs: choose the generated gait (or auto) for this design")

    d = _section(scenario, 'detector')
    result['detector'] = {
        'type': choice(d['type'], 'detector type', DETECTOR_TYPES),
        'camera': str(d['camera'] or ''),
        'min_pixels': number(d['min_pixels'], 'detector minimum pixels', 1, 10000, integer=True),
        'min_brightness': number(d['min_brightness'], 'detector minimum brightness', 0, 1),
        'confirm': number(d['confirm'], 'detector confirm frames', 1, 20, integer=True),
        'external_topic': str(d['external_topic'] or ''),
        'stale': number(d['stale'], 'detector stale time', .1, 60, unit='s'),
    }
    camera = result['detector']['camera']
    if camera and sensor_ids.get(camera, 'camera') != 'camera':
        raise ValueError(f'The detector camera must be a camera, and {camera} is a {sensor_ids[camera]}')
    from coop.hub import TOPIC
    if not TOPIC.fullmatch(result['detector']['external_topic']):
        raise ValueError('The external detection topic must be a topic name such as detections/external')

    b = _section(scenario, 'behaviour')
    result['behaviour'] = {
        'laps_before_charging': number(b['laps_before_charging'], 'laps before charging', 0, 100, integer=True),
        'low_battery': number(b['low_battery'], 'low battery level', 0, 1),
        'resume_battery': number(b['resume_battery'], 'resume battery level', 0, 1),
        'deter_time': number(b['deter_time'], 'deter time', 0, 600, unit='s'),
        'chase_distance': number(b['chase_distance'], 'chase distance', .1, 5, unit='m'),
        'dock_attempts': number(b['dock_attempts'], 'docking attempts', 1, 20, integer=True),
        'self_right': flag(b['self_right'], 'self-righting'),
    }
    if result['behaviour']['resume_battery'] <= result['behaviour']['low_battery']:
        raise ValueError('The resume battery level must be above the low battery level')

    n = _section(scenario, 'energy')
    result['energy'] = {
        'battery_wh': number(n['battery_wh'], 'battery capacity', .1, 1000, unit='Wh'),
        'voltage': number(n['voltage'], 'battery voltage', 1, 48, unit='V'),
        'base_power': number(n['base_power'], 'base power', 0, 100, unit='W'),
        'ir_power': number(n['ir_power'], 'infrared power', 0, 100, unit='W'),
        'servo_idle_current': number(n['servo_idle_current'], 'servo idle current', 0, 5, unit='A'),
        'servo_stall_current': number(n['servo_stall_current'], 'servo stall current', 0, 20, unit='A'),
        'charge_power': number(n['charge_power'], 'charging power', 0, 1000, unit='W'),
        'start_charge': number(n['start_charge'], 'start charge', 0, 1),
    }


def scenario_path(name):
    if not re.fullmatch(r'[A-Za-z0-9 _-]{1,60}', str(name)):
        raise ValueError('Scenario names may use letters, digits, spaces, - and _')
    return SCENARIOS / (str(name).strip() + '.json')


def list_scenarios():
    result = []
    for path in sorted(SCENARIOS.glob('*.json')):
        try:
            title = json.loads(path.read_text(encoding='utf-8')).get('name', path.stem)
        except (OSError, ValueError):
            continue
        result.append({'file': path.stem, 'name': title})
    return result


def load_scenario(name):
    path = scenario_path(name)
    if not path.is_file():
        raise ValueError('Scenario not found: ' + str(name))
    return validate(json.loads(path.read_text(encoding='utf-8')))


def save_scenario(name, scenario):
    checked = validate(scenario)
    path = scenario_path(name)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(checked, indent=2), encoding='utf-8')
    temporary.replace(path)
    return {'file': path.stem, 'name': checked['name']}
