"""Saved motions, maps and motor layouts: plain JSON files in platform-data/, checked before they are written.

Every document is validated here, so a broken file or a typo in a request never reaches the page or the robot, and
an error names what is wrong.
"""
import json
import math
import re
from pathlib import Path

from engine import PROJECT

DATA = PROJECT / 'platform-data'
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9 _-]{0,59}')
MODELS = ('stock', 'crab')
JOINTS = ('neck-joint', 'left-front-shoulder-joint', 'left-front-knee-joint', 'right-front-shoulder-joint',
          'right-front-knee-joint', 'left-back-shoulder-joint', 'left-back-knee-joint', 'right-back-shoulder-joint',
          'right-back-knee-joint')
MAP_KINDS = ('wall', 'fence', 'coop', 'house', 'obstacle', 'dock', 'marker', 'zone', 'label')
BACKGROUND_TYPES = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp'}
MAX_BACKGROUND = 8 * 1024 * 1024


def number(value, name, lo, hi):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} moet een getal zijn')
    if not lo <= value <= hi:
        raise ValueError(f'{name} moet tussen {lo} en {hi} liggen')
    return float(value)


def text(value, name, limit=60, required=False):
    value = str(value if value is not None else '').strip()[:limit]
    if required and not value:
        raise ValueError(f'{name} ontbreekt')
    return value


def check_name(name):
    name = str(name or '').strip()
    if not NAME.fullmatch(name):
        raise ValueError('Een naam bestaat uit letters, cijfers, spaties, - en _ (hoogstens 60) en begint met een letter of cijfer')
    return name


def default_servo(joint):
    """OpenCat servo number and direction of a Bittle joint, as the Studio maps them (right legs turn the other way)."""
    if joint == 'neck-joint':
        return 0, 1
    for leg, index in (('left-front', 8), ('right-front', 9), ('right-back', 10), ('left-back', 11)):
        if joint.startswith(leg):
            return index + (4 if 'knee' in joint else 0), -1 if leg.startswith('right') else 1
    raise ValueError('Onbekend gewricht ' + joint)


def default_layout():
    return {joint: {'servo': default_servo(joint)[0], 'sign': default_servo(joint)[1], 'offset': 0.} for joint in JOINTS}


def validate_layout(raw):
    """Motor layout of one model: joint -> {servo 0-15, sign +1/-1, offset degrees}; missing joints take defaults."""
    raw = raw if isinstance(raw, dict) else {}
    layout = default_layout()
    for joint, entry in raw.items():
        if joint not in layout:
            raise ValueError('Onbekend gewricht ' + str(joint))
        if not isinstance(entry, dict):
            raise ValueError(f'{joint} moet een object zijn')
        servo = entry.get('servo', layout[joint]['servo'])
        if isinstance(servo, bool) or not isinstance(servo, int) or not 0 <= servo <= 15:
            raise ValueError(f'{joint}: servo moet een geheel getal van 0 tot 15 zijn')
        sign = entry.get('sign', layout[joint]['sign'])
        if sign not in (1, -1):
            raise ValueError(f'{joint}: richting moet 1 of -1 zijn')
        layout[joint] = {'servo': servo, 'sign': sign,
                         'offset': number(entry.get('offset', 0), f'{joint} offset', -90, 90)}
    servos = [entry['servo'] for entry in layout.values()]
    if len(set(servos)) != len(servos):
        raise ValueError('Twee gewrichten gebruiken hetzelfde servonummer')
    return layout


def validate_pose(raw, where):
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f'{where} heeft geen gewrichtshoeken')
    pose = {}
    for joint, angle in raw.items():
        if joint not in JOINTS:
            raise ValueError(f'{where}: onbekend gewricht {joint}')
        pose[joint] = round(number(angle, f'{where} {joint}', -180, 180), 2)
    return pose


def validate_motion(raw, name):
    if not isinstance(raw, dict):
        raise ValueError('Een beweging moet een JSON-object zijn')
    frames = raw.get('frames')
    if not isinstance(frames, list) or not 1 <= len(frames) <= 500:
        raise ValueError('Een beweging heeft 1 tot 500 houdingen')
    model = raw.get('model', 'stock')
    if model not in MODELS:
        raise ValueError('model moet een van deze zijn: ' + ', '.join(MODELS))
    return {'format': 'bittle-motion', 'version': 1, 'name': name, 'model': model,
            'notes': text(raw.get('notes'), 'notes', 1000), 'loop': bool(raw.get('loop', False)),
            'frames': [{'pose': validate_pose(frame.get('pose') if isinstance(frame, dict) else None, f'houding {i + 1}'),
                        'seconds': number(frame.get('seconds', .5), f'houding {i + 1} tijd', .02, 10)}
                       for i, frame in enumerate(frames)]}


def _point(value, where):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f'{where} moet [x, y] zijn')
    return [round(number(v, where, -500, 500), 4) for v in value]


def validate_map(raw, name):
    """A top-view map in metres: x to the right, y up (north). Items are walls, fences, buildings, the dock, markers."""
    if not isinstance(raw, dict):
        raise ValueError('Een kaart moet een JSON-object zijn')
    size = raw.get('size', [10, 10])
    items = raw.get('items', [])
    if not isinstance(items, list) or len(items) > 500:
        raise ValueError('Een kaart heeft hoogstens 500 onderdelen')
    result = {'format': 'bittle-map', 'version': 1, 'name': name, 'notes': text(raw.get('notes'), 'notes', 1000),
              'size': [number(size[0], 'kaartbreedte', 1, 500), number(size[1], 'kaarthoogte', 1, 500)]
              if isinstance(size, (list, tuple)) and len(size) == 2 else [10., 10.], 'items': [], 'robot': None,
              'background': None}
    for i, item in enumerate(items):
        where = f'onderdeel {i + 1}'
        if not isinstance(item, dict) or item.get('kind') not in MAP_KINDS:
            raise ValueError(f'{where}: soort moet een van deze zijn: ' + ', '.join(MAP_KINDS))
        clean = {'id': text(item.get('id') or f'item-{i + 1}', f'{where} id', 40), 'kind': item['kind'],
                 'label': text(item.get('label'), f'{where} label')}
        if 'points' in item:
            points = item['points']
            if not isinstance(points, list) or not 1 <= len(points) <= 200:
                raise ValueError(f'{where}: 1 tot 200 punten')
            clean['points'] = [_point(point, f'{where} punt') for point in points]
            clean['closed'] = bool(item.get('closed', False))
        for key, lo, hi in (('x', -500, 500), ('y', -500, 500), ('w', 0, 500), ('h', 0, 500), ('angle', -360, 360),
                            ('heading', -360, 360)):
            if key in item:
                clean[key] = round(number(item[key], f'{where} {key}', lo, hi), 4)
        if 'marker_id' in item:
            marker = item['marker_id']
            if isinstance(marker, bool) or not isinstance(marker, int) or not 0 <= marker <= 999:
                raise ValueError(f'{where}: markernummer moet 0 tot 999 zijn')
            clean['marker_id'] = marker
        if 'points' not in clean and not ('x' in clean and 'y' in clean):
            raise ValueError(f'{where} heeft punten of x en y nodig')
        result['items'].append(clean)
    robot = raw.get('robot')
    if robot is not None:
        if not isinstance(robot, dict):
            raise ValueError('robot moet {x, y, heading} zijn')
        result['robot'] = {'x': number(robot.get('x', 0), 'robot x', -500, 500),
                           'y': number(robot.get('y', 0), 'robot y', -500, 500),
                           'heading': number(robot.get('heading', 0), 'robot heading', -360, 360)}
    background = raw.get('background')
    if background is not None:
        if not isinstance(background, dict):
            raise ValueError('achtergrond moet een object zijn')
        file = str(background.get('file') or '')
        if file and not re.fullmatch(r'[A-Za-z0-9 _-]{1,80}\.(png|jpg|webp)', file):
            raise ValueError('bestandsnaam van de achtergrond is ongeldig')
        result['background'] = {'file': file or None,
                                'scale': number(background.get('scale', .01), 'background scale', 1e-5, 10),
                                'origin': _point(background.get('origin', [0, 0]), 'background origin'),
                                'opacity': number(background.get('opacity', .6), 'background opacity', 0, 1)}
    return result


class Folder:
    """Named JSON documents of one kind in one folder."""

    def __init__(self, path, validate, suffix='.json'):
        self.path, self.validate, self.suffix = Path(path), validate, suffix

    def file(self, name):
        return self.path / (check_name(name) + self.suffix)

    def list(self):
        if not self.path.is_dir():
            return []
        found = []
        for file in sorted(self.path.glob('*' + self.suffix), key=lambda f: f.stem.lower()):
            try:
                document = json.loads(file.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue
            found.append({'name': file.stem, 'updated': file.stat().st_mtime,
                          'frames': len(document.get('frames', [])), 'model': document.get('model'),
                          'items': len(document.get('items', []))})
        return found

    def get(self, name):
        file = self.file(name)
        if not file.is_file():
            raise KeyError(name)
        return self.validate(json.loads(file.read_text(encoding='utf-8')), file.stem)

    def put(self, name, document):
        name = check_name(name)
        checked = self.validate(document, name)
        self.path.mkdir(parents=True, exist_ok=True)
        file = self.file(name)
        temporary = file.with_suffix('.tmp')
        temporary.write_text(json.dumps(checked, indent=1), encoding='utf-8')
        temporary.replace(file)
        return checked

    def delete(self, name):
        file = self.file(name)
        if not file.is_file():
            raise KeyError(name)
        file.unlink()


def validate_settings(raw):
    """Camera mounting, distance sensor and how a scan turns: {camera, distance, scan}."""
    from bittle_platform import distance, scan  # scan needs numpy and Pillow; only settings and scans use them
    raw = raw if isinstance(raw, dict) else {}
    steps = raw.get('scan') if isinstance(raw.get('scan'), dict) else {}
    turn = str(steps.get('turn', 'kvtL'))
    if turn not in ('kvtL', 'manual') and not (turn.startswith('motion:') and NAME.fullmatch(turn[7:])):
        raise ValueError('draaien moet kvtL, manual of motion:<naam van een beweging> zijn')
    mode = str(steps.get('mode', 'neck'))
    if mode not in ('neck', 'body'):
        raise ValueError('scanmanier moet neck (nek zwaait) of body (lijf draait) zijn')
    return {'camera': scan.validate_camera(raw.get('camera')), 'distance': distance.validate_settings(raw.get('distance')),
            'scan': {'mode': mode,
                     'step': number(steps.get('step', 15), 'scanstap', 5, 45), 'turn': turn,
                     'settle': number(steps.get('settle', .8), 'wachttijd na draaien', .2, 5),
                     'neck_range': number(steps.get('neck_range', 90), 'nekbereik', 20, 90),
                     'neck_step': number(steps.get('neck_step', 15), 'nekstap', 5, 45),
                     'neck_settle': number(steps.get('neck_settle', .1), 'wachttijd na een nekstap', 0, 2)}}


class Store:
    def __init__(self, root=DATA):
        self.root = Path(root)
        self.motions = Folder(self.root / 'motions', validate_motion)
        self.maps = Folder(self.root / 'maps', validate_map)
        self.layout_file = self.root / 'motor-layout.json'
        self.settings_file = self.root / 'settings.json'

    def settings(self):
        try:
            return validate_settings(json.loads(self.settings_file.read_text(encoding='utf-8')))
        except (OSError, ValueError):
            return validate_settings({})

    def put_settings(self, raw):
        checked = validate_settings(raw)
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.settings_file.with_suffix('.tmp')
        temporary.write_text(json.dumps(checked, indent=1), encoding='utf-8')
        temporary.replace(self.settings_file)
        return checked

    # Motor layout per robot model

    def layouts(self):
        saved = {}
        if self.layout_file.is_file():
            try:
                saved = json.loads(self.layout_file.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                saved = {}
        result = {}
        for model in MODELS:
            try:
                result[model] = validate_layout(saved.get(model))
            except ValueError:
                result[model] = default_layout()  # a broken entry falls back rather than locking the page out
        return result

    def put_layout(self, model, layout):
        if model not in MODELS:
            raise ValueError('model moet een van deze zijn: ' + ', '.join(MODELS))
        layouts = self.layouts()
        layouts[model] = validate_layout(layout)
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.layout_file.with_suffix('.tmp')
        temporary.write_text(json.dumps(layouts, indent=1), encoding='utf-8')
        temporary.replace(self.layout_file)
        return layouts[model]

    # Map background images

    def background_file(self, map_name, content_type):
        if content_type not in BACKGROUND_TYPES:
            raise ValueError('De achtergrond moet een PNG-, JPEG- of WebP-afbeelding zijn')
        return self.root / 'maps' / (check_name(map_name) + '-background' + BACKGROUND_TYPES[content_type])

    def put_background(self, map_name, content_type, data):
        if not data or len(data) > MAX_BACKGROUND:
            raise ValueError('De afbeelding mag hoogstens 8 MB zijn')
        file = self.background_file(map_name, content_type)
        for old in file.parent.glob(file.stem + '.*'):
            old.unlink()
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        return file.name

    def delete_map(self, map_name):
        """A map with its background image."""
        self.maps.delete(map_name)
        for image in (self.root / 'maps').glob(check_name(map_name) + '-background.*'):
            image.unlink()

    def get_background(self, file_name):
        if not re.fullmatch(r'[A-Za-z0-9 _-]{1,80}\.(png|jpg|webp)', str(file_name)):
            raise KeyError(file_name)
        file = self.root / 'maps' / file_name
        if not file.is_file():
            raise KeyError(file_name)
        return file
