"""The distance sensor slot: where a lidar or ultrasonic sensor plugs into the scan.

A source answers read(pose, map) with readings [{'bearing': degrees left of the robot's forward direction,
'distance': metres}] (empty when nothing is in range). Single-beam sensors (ultrasonic, TF-Luna, VL53L1X) give one
reading per scan step; a rotating 2D lidar gives a whole ring at once.

Sources:
  'camera': the SRF05 on the camera's XIAO. Its readings come with the camera's stream (about 14 a second); a scan
            step takes the median of the readings made while the robot stood still.
  'test':   measures the walls, fences and buildings drawn on the map, so the whole scan can be tried out.
"""
import math
import statistics

SOURCES = {
    'none': 'Geen afstandssensor',
    'camera': 'SRF05 op de camera (XIAO)',
    'test': 'Nagebootste sensor (meet wat op de kaart getekend is)',
}
SOLID = ('wall', 'fence', 'coop', 'house', 'obstacle')
BEAM = 15.      # degrees either side of its direction that an ultrasonic sensor hears (SRF05: about 30 degrees wide)
MIN_RANGE = .03  # metres: closer readings of an SRF05 are not trustworthy


def validate_settings(raw):
    raw = raw if isinstance(raw, dict) else {}
    source = raw.get('source', 'none')
    if source not in SOURCES:
        raise ValueError('afstandssensor moet een van deze zijn: ' + ', '.join(SOURCES))
    numbers = {'bearing': (0., -180, 180), 'forward': (.1, -.5, .5), 'max_range': (4., .1, 40)}
    result = {'source': source}
    for key, (default, lo, hi) in numbers.items():
        value = raw.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not lo <= value <= hi:
            raise ValueError(f'afstandssensor {key} moet tussen {lo} en {hi} liggen')
        result[key] = float(value)
    return result


def segments(map_doc):
    """Every solid edge on a map as ((x0, y0), (x1, y1))."""
    edges = []
    for item in (map_doc or {}).get('items', []):
        if item.get('kind') not in SOLID:
            continue
        if 'points' in item:
            points = item['points']
            pairs = list(zip(points, points[1:]))
            if item.get('closed') and len(points) > 2:
                pairs.append((points[-1], points[0]))
            edges += [(tuple(a), tuple(b)) for a, b in pairs]
        elif 'w' in item and 'h' in item:
            angle = math.radians(item.get('angle', 0))
            c, s = math.cos(angle), math.sin(angle)
            corners = [(item['x'] + u * c - v * s, item['y'] + u * s + v * c)
                       for u, v in ((-item['w'] / 2, -item['h'] / 2), (item['w'] / 2, -item['h'] / 2),
                                    (item['w'] / 2, item['h'] / 2), (-item['w'] / 2, item['h'] / 2))]
            edges += list(zip(corners, corners[1:] + corners[:1]))
    return edges


def cast(origin, heading, edges, max_range):
    """Distance along a ray to the nearest edge, or None beyond max_range."""
    dx, dy = math.cos(math.radians(heading)), math.sin(math.radians(heading))
    best = None
    for (x0, y0), (x1, y1) in edges:
        ex, ey = x1 - x0, y1 - y0
        denominator = dx * ey - dy * ex
        if abs(denominator) < 1e-12:
            continue
        t = ((x0 - origin[0]) * ey - (y0 - origin[1]) * ex) / denominator   # along the ray
        u = ((x0 - origin[0]) * dy - (y0 - origin[1]) * dx) / denominator   # along the edge
        if t > 1e-6 and -1e-9 <= u <= 1 + 1e-9 and (best is None or t < best):
            best = t
    return best if best is not None and best <= max_range else None


def from_samples(settings, samples):
    """One reading from a sensor's samples in centimetres (None: no echo): their median when most of them echoed."""
    heard = [cm / 100. for cm in samples if isinstance(cm, (int, float)) and not isinstance(cm, bool)]
    if not samples or len(heard) * 2 < len(samples):  # mostly no echo: nothing in reach in this direction
        return []
    distance = statistics.median(heard)
    if not MIN_RANGE <= distance <= settings['max_range']:
        return []
    return [{'bearing': settings['bearing'], 'distance': round(distance, 3), 'samples': len(heard)}]


def read(settings, pose, map_doc, samples=None):
    """Readings of the configured source at a robot pose {x, y, heading} (world, degrees). samples: the 'camera'
    source's readings in centimetres taken during this step."""
    if settings['source'] == 'camera':
        return from_samples(settings, samples or [])
    if settings['source'] == 'test':
        heading = pose['heading'] + settings['bearing']
        origin = (pose['x'] + settings['forward'] * math.cos(math.radians(pose['heading'])),
                  pose['y'] + settings['forward'] * math.sin(math.radians(pose['heading'])))
        distance = cast(origin, heading, segments(map_doc), settings['max_range'])
        return [] if distance is None else [{'bearing': settings['bearing'], 'distance': round(distance, 4)}]
    return []
