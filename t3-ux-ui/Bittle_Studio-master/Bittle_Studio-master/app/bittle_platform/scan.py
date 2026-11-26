"""Turn-and-scan: the robot turns on the spot in steps; at every step the platform keeps a camera frame, what the
camera's AI model recognised there and what the distance sensor measured, and works out how far the robot really
turned. Finishing a scan puts it all on the map: a 360-degree photo, recognised objects at their estimated place, the
measured outline of the surroundings, and a top-down picture of the floor around the robot.

How far the robot turned comes from the pictures themselves: frames are warped to a cylinder, where turning by an
angle shifts the picture sideways by focal length x angle, and phase correlation finds that shift. A gyro angle or
the commanded turn stand in when a picture shows too little (a bare wall). When the circle closes, comparing the
last frame with the first spreads the accumulated error over all steps and measures the lens's field of view.

Angles are degrees, positive = counter-clockwise (turning left), as on the map. Image columns run left to right, so a
left turn moves the picture to the right.
"""
import io
import json
import math
import re
import time
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

from bittle_platform import distance as sensor

DEFAULT_CAMERA = {'height': .1, 'tilt': 0., 'hfov': 53., 'forward': .1}
CAMERA_LIMITS = {'height': (.01, 2.), 'tilt': (-60., 60.), 'hfov': (20., 160.), 'forward': (-.3, .5)}
MIN_CONFIDENCE = 8.     # phase-correlation peak, in standard deviations above the rest, that counts as a match
SPECTRUM_SIGMA = .1     # cycles per pixel: finer detail (JPEG blocks, noise) counts less in the match
CLOSE_CONFIDENCE = 20.  # stricter for "this is the start again": that match has no commanded turn to narrow it
MATCH_ROWS = .7         # upper share of the picture used to measure turns: the robot's own legs sit at the bottom
HALF_TURN = 180.        # degrees (as estimated) after which every frame is compared with the first
GROUND_RANGE = 1.2      # metres around the robot in the floor picture
GROUND_CELL = .01       # metres per pixel of the floor picture
OUTLINE_GAP = .4        # metres between measured points that are still joined into one outline
# Real heights (metres) of things a model may recognise, for a distance estimate when their foot is out of sight.
HEIGHTS = {'person': 1.7, 'face': .22, 'chicken': .35, 'hen': .35, 'fox': .45, 'dog': .5, 'cat': .3}
ID = re.compile(r'[0-9a-f]{12}')


def validate_camera(raw):
    raw = raw if isinstance(raw, dict) else {}
    result = {}
    for key, default in DEFAULT_CAMERA.items():
        value = raw.get(key, default)
        lo, hi = CAMERA_LIMITS[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not lo <= value <= hi:
            raise ValueError(f'camera {key} moet tussen {lo} en {hi} liggen')
        result[key] = float(value)
    return result


# Pictures

def grey(jpeg):
    """A JPEG as a float32 grey image (0-1)."""
    with Image.open(io.BytesIO(jpeg)) as image:
        return np.asarray(image.convert('L'), np.float32) / 255


def rgb(path):
    """A picture file as an RGB array, the file closed again (Windows cannot delete open files)."""
    with Image.open(path) as image:
        return np.asarray(image.convert('RGB'))


def focal(width, hfov):
    """Focal length in pixels for a picture width and horizontal field of view (degrees)."""
    return width / 2 / math.tan(math.radians(hfov) / 2)


def cylinder(image, f):
    """The picture warped onto a cylinder around the camera: then turning is a plain sideways shift of f x angle."""
    height, width = image.shape[:2]
    cx, cy = (width - 1) / 2, (height - 1) / 2
    angle = (cx - np.arange(width)) / f                         # column -> bearing, left positive
    source_x = cx - f * np.tan(angle)
    source_y = cy + (np.arange(height)[:, None] - cy) / np.cos(angle)[None, :]
    xs = np.clip(np.round(source_x).astype(int), 0, width - 1)
    ys = np.clip(np.round(source_y).astype(int), 0, height - 1)
    inside = (source_x >= 0) & (source_x <= width - 1)
    warped = image[ys, xs[None, :]]
    warped[:, ~inside] = 0
    return warped


def tukey(n, taper=.3):
    """Flat in the middle, cosine edges: keeps the overlap of two frames that moved far apart, unlike a Hann window."""
    x = np.linspace(0, 1, n)
    window = np.ones(n)
    edge = x < taper / 2
    window[edge] = .5 * (1 - np.cos(2 * np.pi * x[edge] / taper))
    window[x > 1 - taper / 2] = window[edge][::-1][:np.count_nonzero(x > 1 - taper / 2)]
    return window


def shift(a, b, dx_range=None):
    """(dx, dy, confidence): b is a moved by dx pixels to the right (and dy down). Phase correlation on the
    horizontal edges of both pictures (plain brightness, windowed, also matches the window itself at "no shift").
    dx_range (lo, hi) limits the search to the shifts that are possible at all."""
    a, b = np.diff(a, axis=1), np.diff(b, axis=1)
    window = np.outer(np.hanning(a.shape[0]), tukey(a.shape[1])).astype(np.float32)
    fa, fb = np.fft.rfft2((a - a.mean()) * window), np.fft.rfft2((b - b.mean()) * window)
    cross = fb * np.conj(fa)
    # Weigh down the finest detail: JPEG's 8x8 blocks sit at the same place in every frame and would vote for
    # "no turn"; the scene's coarser structure is what moves.
    fy, fx = np.fft.fftfreq(a.shape[0])[:, None], np.fft.rfftfreq(a.shape[1])[None, :]
    weight = np.exp(-(fx ** 2 + fy ** 2) / (2 * SPECTRUM_SIGMA ** 2))
    surface = np.fft.irfft2(cross / (np.abs(cross) + 1e-9) * weight, s=a.shape)
    search = surface
    if dx_range is not None:
        lags = np.arange(a.shape[1])
        lags = np.where(lags > a.shape[1] / 2, lags - a.shape[1], lags)
        search = np.where(((lags >= dx_range[0]) & (lags <= dx_range[1]))[None, :], surface, -np.inf)
    row, column = np.unravel_index(np.argmax(search), surface.shape)
    peak = surface[row, column]
    confidence = float((peak - surface.mean()) / (surface.std() + 1e-12))

    def refine(values, index):  # parabola through the peak and its neighbours: sub-pixel shift
        left, mid, right = values[(index - 1) % len(values)], values[index], values[(index + 1) % len(values)]
        bend = left - 2 * mid + right
        return index + (.5 * (left - right) / bend if bend else 0.)

    dx, dy = refine(surface[row, :], column), refine(surface[:, column], row)
    height, width = a.shape
    dx = dx - width if dx > width / 2 else dx
    dy = dy - height if dy > height / 2 else dy
    return float(dx), float(dy), confidence


def turn_between(previous, current, f, degrees_range=None):
    """Degrees turned left from one frame to the next, and how sure that is. degrees_range (lo, hi) is what is
    possible at all (from the commanded turn)."""
    rows = int(previous.shape[0] * MATCH_ROWS)
    width = previous.shape[1]
    # Only the columns the warp filled: its empty edges sit in the same place in both frames and would pull the
    # match towards "no turn".
    half = int(f * math.atan((width - 1) / 2 / f)) - 1
    centre = (width - 1) // 2
    band = slice(max(0, centre - half), min(width, centre + half + 1))
    pixels = None if degrees_range is None else tuple(f * math.radians(d) for d in degrees_range)
    dx, _, confidence = shift(cylinder(previous, f)[:rows, band], cylinder(current, f)[:rows, band], pixels)
    return math.degrees(dx / f), dx, confidence


def possible(commanded):
    """The turns (degrees) that fit a commanded one: Bittle turns more or less than asked, but not backwards."""
    if commanded is None:
        return None
    if commanded > 1:
        return .3 * commanded - 3, 2.5 * commanded + 5
    if commanded < -1:
        return 2.5 * commanded - 5, .3 * commanded + 3
    return -10, 10


# Geometry

# The neck: Bittle's head turns about an axis 4.8 cm ahead of the body's centre that leans 30 degrees forward from
# vertical (Petoi's official model, robot-models/bittle/bittle.urdf). A camera on the head therefore looks less far
# sideways than the neck turns (90 degrees of neck: about 74 degrees) and a little upwards.
NECK_PIVOT = .048
NECK_AXIS_TILT = math.radians(30)


def neck_view(neck):
    """(yaw left, pitch up) in degrees of a forward-looking camera on the head when the neck is at `neck` degrees."""
    t, a = math.radians(neck), NECK_AXIS_TILT
    forward = math.sin(a) ** 2 + math.cos(t) * math.cos(a) ** 2
    left = math.sin(t) * math.cos(a)
    up = math.sin(a) * math.cos(a) * (1 - math.cos(t))
    return math.degrees(math.atan2(left, forward)), math.degrees(math.asin(max(-1., min(1., up))))


def lens(scan):
    """Field of view to place things with: the one the closed circle measured, else the setting."""
    return scan.get('hfov_measured') or scan['camera']['hfov']


def head_origin(scan, step):
    """The point from which the head's camera and sensor sit `forward` metres along the view direction, and the view
    direction (world degrees). Without a neck turn that is the robot's centre and its heading."""
    world = scan['heading'] + step['heading']
    body = scan['heading'] + step.get('body', step['heading'])
    if body == world:
        return (scan['x'], scan['y']), world
    # pivot = centre + NECK_PIVOT along the body; the head part of `forward` (forward - NECK_PIVOT) turns with the view.
    b, w = math.radians(body), math.radians(world)
    return (scan['x'] + NECK_PIVOT * (math.cos(b) - math.cos(w)),
            scan['y'] + NECK_PIVOT * (math.sin(b) - math.sin(w))), world


def camera_pose(scan, step):
    """World position (x, y) and view direction of the camera in a step."""
    (x, y), world = head_origin(scan, step)
    forward = scan['camera']['forward']
    return (x + forward * math.cos(math.radians(world)), y + forward * math.sin(math.radians(world))), world


def camera_tilt(scan, step):
    """Degrees the camera looks down in a step: its mounting, less what a turned neck lifts it."""
    return scan['camera']['tilt'] - neck_view(step.get('neck') or 0.)[1]


def locate(scan, step, box, f):
    """World position and distance of a recognised box (centre x, y, width, height in pixels), or None."""
    width, height = step['size']
    cx, cy = (width - 1) / 2, (height - 1) / 2
    bearing = math.degrees(math.atan((cx - box['x']) / f))
    camera = scan['camera']
    below = math.degrees(math.atan((box['y'] + box['h'] / 2 - cy) / f)) + camera_tilt(scan, step)  # foot of the box
    distance = None
    if below > 1:
        distance = camera['height'] / math.tan(math.radians(below))
    elif box['label'].lower() in HEIGHTS and box['h'] > 2:
        distance = HEIGHTS[box['label'].lower()] * f / box['h']
    measured = measured_distance(scan, step, bearing)
    # The distance sensor's echo comes from the nearest thing in its beam: trust it for this box unless the picture
    # says the box is much nearer or further (then the echo came from something else).
    if measured is not None and (distance is None or .5 < measured / distance < 2):
        distance = measured
    else:
        measured = None
    if distance is None or distance > 15:
        return None
    (x, y), world = camera_pose(scan, step)
    direction = math.radians(world + bearing)
    return {'x': round(x + distance * math.cos(direction), 3), 'y': round(y + distance * math.sin(direction), 3),
            'distance': round(distance, 3), 'bearing': round((world + bearing) % 360, 1), 'measured': measured is not None}


def measured_distance(scan, step, bearing):
    """Distance from the camera that the distance sensor measured in this step towards a bearing (degrees left of
    straight ahead), when that bearing lies inside the sensor's beam; else None."""
    for reading in step.get('ranges', []):
        if abs((bearing - reading['bearing'] + 180) % 360 - 180) <= sensor.BEAM:
            return reading['distance'] + scan['sensor']['forward'] - scan['camera']['forward']
    return None


def ranges_world(scan, step):
    points = []
    for reading in step.get('ranges', []):
        (x, y), heading = head_origin(scan, step)
        forward = scan['sensor']['forward']
        x += forward * math.cos(math.radians(heading))
        y += forward * math.sin(math.radians(heading))
        direction = math.radians(heading + reading['bearing'])
        points.append({'x': round(x + reading['distance'] * math.cos(direction), 3),
                       'y': round(y + reading['distance'] * math.sin(direction), 3),
                       'distance': reading['distance'], 'bearing': round((heading + reading['bearing']) % 360, 1)})
    return points


def outline(points, centre):
    """Measured points ordered round the scan point and joined where neighbours are close: lists of [x, y].
    Far points may lie further apart (a beam's spacing grows with distance)."""
    if len(points) < 2:
        return []
    ordered = sorted(points, key=lambda p: math.atan2(p['y'] - centre[1], p['x'] - centre[0]))
    near = lambda a, b: math.hypot(a['x'] - b['x'], a['y'] - b['y']) <= max(OUTLINE_GAP, .2 * max(a['distance'], b['distance']))
    runs = [[ordered[0]]]
    for point in ordered[1:]:
        if near(runs[-1][-1], point):
            runs[-1].append(point)
        else:
            runs.append([point])
    if len(runs) > 1 and near(runs[-1][-1], runs[0][0]):  # the circle wraps: the last run continues into the first
        runs[0] = runs.pop() + runs[0]
    closed = len(runs) == 1 and len(ordered) > 2 and near(ordered[-1], ordered[0])
    lines = [[[p['x'], p['y']] for p in run] for run in runs if len(run) >= 2]
    if closed and lines:
        lines[0].append(lines[0][0])
    return lines


def merge(objects, radius=.4):
    """The same thing seen in two neighbouring frames becomes one object (the surest sighting, placed in between)."""
    merged = []
    for item in sorted(objects, key=lambda o: -o['score']):
        twin = next((m for m in merged if m['label'] == item['label']
                     and math.hypot(m['x'] - item['x'], m['y'] - item['y']) < radius), None)
        if twin:
            twin['x'], twin['y'] = round((twin['x'] + item['x']) / 2, 3), round((twin['y'] + item['y']) / 2, 3)
            twin['seen'] += 1
        else:
            merged.append({**item, 'seen': 1})
    return merged


# The scans on disk

class Scans:
    def __init__(self, root):
        self.root = Path(root)

    def folder(self, scan_id):
        if not ID.fullmatch(str(scan_id)):
            raise KeyError(scan_id)
        folder = self.root / scan_id
        if not (folder / 'scan.json').is_file():
            raise KeyError(scan_id)
        return folder

    def load(self, scan_id):
        return json.loads((self.folder(scan_id) / 'scan.json').read_text(encoding='utf-8'))

    def save(self, scan):
        folder = self.root / scan['id']
        folder.mkdir(parents=True, exist_ok=True)
        temporary = folder / 'scan.tmp'
        temporary.write_text(json.dumps(scan, indent=1), encoding='utf-8')
        for attempt in range(20):
            try:
                temporary.replace(folder / 'scan.json')
                break
            except PermissionError:  # Windows: the file is being read right now (the live map asks for it)
                if attempt == 19:
                    raise
                time.sleep(.025)
        return scan

    def create(self, map_name, pose, camera, distance_settings):
        for key in ('x', 'y', 'heading'):
            value = pose.get(key) if isinstance(pose, dict) else None
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('Zet de robot eerst op de kaart (gereedschap Robot): positie en richting')
        scan = {'format': 'bittle-scan', 'version': 1, 'id': uuid.uuid4().hex[:12], 'map': map_name or '',
                'created': time.time(), 'x': float(pose['x']), 'y': float(pose['y']), 'heading': float(pose['heading']),
                'camera': validate_camera(camera), 'sensor': sensor.validate_settings(distance_settings),
                'steps': [], 'finished': False, 'closure': None, 'hfov_measured': None}
        return self.save(scan)

    def list(self, map_name=None):
        found = []
        if not self.root.is_dir():
            return found
        for file in self.root.glob('*/scan.json'):
            try:
                scan = json.loads(file.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue
            if map_name is None or scan.get('map') == map_name:
                found.append(summary(scan))
        return sorted(found, key=lambda s: s['created'])

    def delete(self, scan_id):
        folder = self.folder(scan_id)
        for file in folder.iterdir():
            file.unlink()
        folder.rmdir()

    def file(self, scan_id, name):
        if not re.fullmatch(r'(frame-\d{2}\.jpg|panorama\.jpg|ground\.png)', name):
            raise KeyError(name)
        path = self.folder(scan_id) / name
        if not path.is_file():
            raise KeyError(name)
        return path

    # Steps

    def step(self, scan_id, jpeg=None, detections=(), commanded=None, gyro=None, map_doc=None, samples=None, neck=None):
        """Add one step: the frame taken after the robot stopped, and how far it was asked or measured to turn.
        commanded / gyro: degrees the body turned since the previous step (asked for / measured by the robot).
        neck: the neck angle in degrees (None: the head looks straight ahead, as in a body-turn scan).
        samples: the camera's SRF05 readings (cm, None for no echo) taken meanwhile; [] when none came."""
        scan = self.load(scan_id)
        if scan['finished']:
            raise ValueError('Deze scan is al afgerond')
        if len(scan['steps']) >= 72:
            raise ValueError('Een scan heeft hoogstens 72 stappen')
        index = len(scan['steps'])
        step = {'index': index, 'turn': 0., 'heading': 0., 'method': 'start', 'confidence': None, 'shift_px': None,
                'commanded': commanded, 'gyro': gyro, 'frame': None, 'size': None, 'detections': [], 'ranges': [],
                'to_start': None, 'samples': None if samples is None else len(samples), 'neck': neck, 'body': 0.}
        yaw = neck_view(neck or 0.)[0]
        folder = self.folder(scan_id)
        if jpeg:
            name = f'frame-{index + 1:02d}.jpg'
            (folder / name).write_bytes(jpeg)
            with Image.open(io.BytesIO(jpeg)) as image:
                step['frame'], step['size'] = name, list(image.size)
            step['detections'] = [{key: d[key] for key in ('label', 'score', 'x', 'y', 'w', 'h')} for d in detections]
        if index:
            previous = scan['steps'][-1]
            # The camera turns by what the body turned plus what the neck turned.
            neck_turn = yaw - neck_view(previous.get('neck') or 0.)[0]
            camera_commanded = None if commanded is None else commanded + neck_turn
            camera_gyro = None if gyro is None else gyro + neck_turn
            # Where to look for the match: what the body may really have turned, plus the neck's known turn.
            body_range = possible(commanded)
            search = None if body_range is None else (body_range[0] + neck_turn, body_range[1] + neck_turn)
            step['turn'], step['method'] = self._turn(scan, folder, previous, step, camera_commanded, camera_gyro, search)
            if step['method'] == 'command' and neck is not None and not commanded:
                step['method'] = 'neck'  # only the neck moved: its angle is known
            step['heading'] = round(previous['heading'] + step['turn'], 2)
            step['to_start'] = self._to_start(scan, folder, step)
        else:
            step['heading'] = round(yaw, 2)  # the first frame: the body is the scan's heading, the head may be turned
        step['body'] = round(step['heading'] - yaw, 2)
        if scan['sensor']['source'] != 'none':
            (x, y), world = head_origin(scan, step)
            step['ranges'] = sensor.read(scan['sensor'], {'x': x, 'y': y, 'heading': world}, map_doc, samples)
        scan['steps'].append(step)
        self.save(scan)
        return summary(scan)

    def _turn(self, scan, folder, previous, step, commanded, gyro, search=None):
        """Degrees the camera turned since the previous step: from the pictures when they agree well (searched within
        `search` degrees), else gyro or command."""
        if previous['frame'] and step['frame'] and previous['size'] == step['size']:
            f = focal(step['size'][0], scan['camera']['hfov'])
            degrees, dx, confidence = turn_between(grey((folder / previous['frame']).read_bytes()),
                                                   grey((folder / step['frame']).read_bytes()), f, search)
            step['confidence'], step['shift_px'] = round(confidence, 1), round(dx, 2)
            if confidence >= MIN_CONFIDENCE:
                return round(degrees, 2), 'image'
        if gyro is not None:
            return float(gyro), 'gyro'
        if commanded is not None:
            return float(commanded), 'command'
        raise ValueError('Geen draaihoek: de beelden lijken niet op elkaar en er is geen gyroscoop of commando')

    def _to_start(self, scan, folder, step):
        """Past half a turn: does this frame see the start again? Then the degrees still to turn to reach it.

        The sum of the steps can be far off when the field of view is wrong, so the pictures, not that sum, tell
        when the circle is complete."""
        first = scan['steps'][0]
        if step['heading'] - first['heading'] < HALF_TURN or not (first['frame'] and step['frame']) or first['size'] != step['size']:
            return None
        f = focal(step['size'][0], scan['camera']['hfov'])
        degrees, _, confidence = turn_between(grey((folder / step['frame']).read_bytes()),
                                              grey((folder / first['frame']).read_bytes()), f, (-30, 90))
        return round(degrees, 2) if confidence >= CLOSE_CONFIDENCE else None

    # Finishing

    def finish(self, scan_id):
        scan = self.load(scan_id)
        folder = self.folder(scan_id)
        steps = scan['steps']
        if not steps:
            raise ValueError('Deze scan heeft nog geen stappen')
        scan['closure'] = self._close(scan, folder)
        frames = [s for s in steps if s['frame']]
        if frames:
            size = frames[0]['size']
            f = focal(size[0], lens(scan))
            images = {s['index']: rgb(folder / s['frame']) for s in frames}
            panorama = stitch(scan, images, f)
            Image.fromarray(panorama).save(folder / 'panorama.jpg', quality=88)
            ground = floor(scan, images, f)
            if ground is not None:
                Image.fromarray(ground, 'RGBA').save(folder / 'ground.png')
        scan['finished'] = True
        self.save(scan)
        return summary(scan)

    def _close(self, scan, folder):
        """Compare the last frame with the first; spread the error over the steps and measure the field of view."""
        steps = scan['steps']
        if not (steps[0]['frame'] and steps[-1]['frame']):
            return {'closed': False, 'reason': 'zonder camerabeelden kan de cirkel niet gecontroleerd worden'}
        start = steps[0]['heading']  # a neck scan starts with the head turned
        if len(steps) < 3 or steps[-1]['heading'] - start < HALF_TURN:
            return {'closed': False, 'reason': 'te weinig gedraaid om de cirkel te sluiten'}
        size = steps[0]['size']
        f = focal(size[0], scan['camera']['hfov'])
        # From the last frame back to the first: what is left of the circle. Not "360 - heading": a wrong field of
        # view scales every step, so the sum can be far off while the last frame still overlaps the first.
        degrees, dx, confidence = turn_between(grey((folder / steps[-1]['frame']).read_bytes()),
                                               grey((folder / steps[0]['frame']).read_bytes()), f, (-30, 90))
        total = steps[-1]['heading'] - start + degrees  # what the steps add up to round the full circle
        # Up to a factor 2 either way: the field-of-view setting may be that far off before it is measured.
        if confidence < CLOSE_CONFIDENCE or not 180 < total < 720:
            return {'closed': False, 'reason': 'het laatste beeld lijkt niet genoeg op het eerste',
                    'confidence': round(confidence, 1)}
        factor = 360. / total
        for step in steps:
            step['turn'] = round(step['turn'] * factor, 2)
        running = start
        for step in steps:
            running += step['turn']
            step['heading'] = round(running, 2)
            step['body'] = round(running - neck_view(step.get('neck') or 0.)[0], 2)
        result = {'closed': True, 'error_deg': round(total - 360, 1), 'confidence': round(confidence, 1)}
        # Only a pure turn of the camera about itself measures the lens; a tilted neck axis also rolls the picture.
        if all(s['method'] in ('image', 'start') and s.get('neck') is None for s in steps):
            # The pixel shifts of the whole circle add up to 2 pi x the true focal length.
            pixels = sum(s['shift_px'] or 0 for s in steps) + dx
            true_focal = pixels / (2 * math.pi)
            if true_focal > 0:
                scan['hfov_measured'] = round(math.degrees(2 * math.atan(size[0] / 2 / true_focal)), 1)
                result['hfov_measured'] = scan['hfov_measured']
        return result


def stitch(scan, images, f):
    """A 360-degree photo: each panorama column takes the frame that looked most straight at it."""
    first = next(iter(images.values()))
    height, width = first.shape[:2]
    columns = max(1, round(2 * math.pi * f))
    cx = (width - 1) / 2
    panorama = np.zeros((height, columns, 3), np.uint8)
    headings = {s['index']: math.radians(s['heading']) for s in scan['steps'] if s['index'] in images}
    for u in range(columns):
        bearing = -2 * math.pi * u / columns             # reading left to right = turning right
        best, angle = None, None
        for index, heading in headings.items():
            delta = (bearing - heading + math.pi) % (2 * math.pi) - math.pi
            if abs(delta) < math.atan(width / 2 / f) and (best is None or abs(delta) < abs(angle)):
                best, angle = index, delta
        if best is None:
            continue
        x = int(round(cx - f * math.tan(angle)))
        if 0 <= x < width:
            panorama[:, u] = images[best][:, x]
    return panorama


def floor(scan, images, f):
    """The floor around the robot seen from above (RGBA, transparent where no frame saw it), centred on the scan."""
    camera = scan['camera']
    cells = int(round(2 * GROUND_RANGE / GROUND_CELL))
    offsets = (np.arange(cells) + .5) * GROUND_CELL - GROUND_RANGE
    gx, gy = np.meshgrid(offsets, offsets[::-1])               # image rows run from north (top) to south
    picture = np.zeros((cells, cells, 4), np.uint8)
    taken = np.zeros((cells, cells), bool)
    best = np.full((cells, cells), np.inf)
    for step in scan['steps']:
        if step['index'] not in images:
            continue
        tilt = math.radians(camera_tilt(scan, step))
        image = images[step['index']]
        height, width = image.shape[:2]
        cx, cy = (width - 1) / 2, (height - 1) / 2
        (camera_x, camera_y), world = camera_pose(scan, step)
        heading = math.radians(world)
        dx, dy = scan['x'] + gx - camera_x, scan['y'] + gy - camera_y
        ahead = dx * math.cos(heading) + dy * math.sin(heading)  # camera axes: forward, left, up
        left = -dx * math.sin(heading) + dy * math.cos(heading)
        up = -camera['height'] * np.ones_like(ahead)
        forward_tilted = ahead * math.cos(tilt) - up * math.sin(tilt)   # pitch the camera down by the tilt
        up_tilted = ahead * math.sin(tilt) + up * math.cos(tilt)
        visible = forward_tilted > .05
        u = cx - f * left / np.where(visible, forward_tilted, 1)
        v = cy - f * up_tilted / np.where(visible, forward_tilted, 1)
        visible &= (u >= 0) & (u <= width - 1) & (v >= 0) & (v <= height - 1)
        straight = np.abs(np.arctan2(left, ahead))                # prefer the frame that looked most straight
        use = visible & (straight < best)
        if not use.any():
            continue
        best[use] = straight[use]
        picture[use, :3] = image[np.round(v[use]).astype(int), np.round(u[use]).astype(int)]
        picture[use, 3] = 235
        taken |= use
    return picture if taken.any() else None


def view(scan, step):
    """Where a photo was taken, for the 3D surroundings: camera position (x, y on the map, z above the floor), view
    direction and downward tilt (degrees), field of view, and the depth in front of it as a grid of metres along the
    view (rows x columns over the picture; one cell for a single-beam sensor), or None when nothing was measured."""
    if not step['frame']:
        return None
    (x, y), world = camera_pose(scan, step)
    measured = measured_distance(scan, step, 0.)
    return {'x': round(x, 3), 'y': round(y, 3), 'z': scan['camera']['height'], 'heading': round(world % 360, 2),
            'tilt': round(camera_tilt(scan, step), 2), 'hfov': lens(scan), 'size': step['size'],
            'depth': step.get('grid') or (None if measured is None else [[round(measured, 3)]])}


def summary(scan):
    """A scan with everything placed in the world: steps, recognised objects, measured outline, files."""
    frames = [s for s in scan['steps'] if s['frame']]
    f = focal(frames[0]['size'][0], lens(scan)) if frames else None
    objects = []
    for step in frames:
        for box in step['detections']:
            place = locate(scan, step, box, f)
            if place:
                objects.append({'label': box['label'], 'score': box['score'], **place})
    points = [point for step in scan['steps'] for point in ranges_world(scan, step)]
    folder_files = {'panorama': 'panorama.jpg' if scan['finished'] and frames else None,
                    'ground': None}
    if scan['finished'] and frames:
        folder_files['ground'] = {'file': 'ground.png', 'x0': round(scan['x'] - GROUND_RANGE, 3),
                                  'y0': round(scan['y'] + GROUND_RANGE, 3), 'size': 2 * GROUND_RANGE}
    turned = scan['steps'][-1]['heading'] - scan['steps'][0]['heading'] if scan['steps'] else 0.
    return {**{k: scan[k] for k in ('id', 'map', 'created', 'x', 'y', 'heading', 'camera', 'sensor', 'finished',
                                     'closure', 'hfov_measured')},
            'turned': round(turned, 1), 'steps': [{k: s.get(k) for k in ('index', 'turn', 'heading', 'method', 'confidence',
                                                                         'frame', 'size', 'to_start', 'samples',
                                                                         'neck', 'body')}
                                                          | {'distance': s['ranges'][0]['distance'] if s.get('ranges') else None,
                                                             'view': view(scan, s)}
                                                          for s in scan['steps']],
            'objects': merge(objects), 'points': points, 'outline': outline(points, (scan['x'], scan['y'])),
            **folder_files}
