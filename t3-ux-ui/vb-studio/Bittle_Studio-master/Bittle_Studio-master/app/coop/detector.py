"""The detector: recognises fox, chicken and person in the frames of one camera, as a part of its own.

The camera only takes pictures. This module reads them (or the detections of an outside program, such as the AI camera
module) and says what is in each one: label, confidence, box, size in pixels, distance and bearing. It does not raise
the alarm: the behaviour module reads latest() and decides how many frames in a row it needs ('confirm').

Three kinds, chosen by the scenario's 'detector' section:
  ground-truth  an ideal model that knows from the segmentation which body each pixel shows; only light and size limit it
  colour-blob   a hand-made classifier of the picture's colours: fox orange, chicken white, jacket blue
  external      the detections an outside program publishes on a hub topic (see examples/external_detector.py)
This file needs numpy only, so the outside example can reuse the colour classifier without Bullet.
"""
import copy
import math

import numpy as np

from coop.hub import Module, check

LABELS = ('fox', 'chicken', 'person')
TYPES = ('ground-truth', 'colour-blob', 'external')
NAMES = {'ground-truth': 'Detector (ground truth)', 'colour-blob': 'Detector (colour blobs)',
         'external': 'Detector (outside program)'}
EPSILON = 1e-9   # seconds of tolerance when comparing simulation times
FUTURE = .5      # seconds an outside detection may be stamped ahead of the clock; later ones date from before a reset
LUMA = np.array([.299, .587, .114], np.float32)  # weights of red, green and blue in the brightness of a pixel

# The classifier is tuned to the simulator's flat colours. The renderer shades a surface to 60-100 % of its colour but
# keeps hue and saturation, so classes are made of those. Each is a reference value with a tolerance, so that a pixel
# also has a closeness (1 = the reference colour exactly) that goes into the blob's confidence.
FOX_HUE, FOX_HUE_TOLERANCE = 24., 8.            # orange body #d4661c; the hens' yellow legs (36) and the roof (10) lie outside
FOX_SATURATION, FOX_SATURATION_TOLERANCE = .87, .27  # the tan house (.47) and the skin of a head (.37) are paler
WHITE_SATURATION, WHITE_TOLERANCE = .05, .025  # cream-white hen #f2efe6; the sky is neutral (0), the fence and stones differ
WHITE_VALUE = .5                                # brightest-channel level below which a grey is a stone, not a hen
PERSON_HUE, PERSON_HUE_TOLERANCE = 216., 6.     # jacket #2f5fa8; the dock's blue is 206, ten degrees away
PERSON_SATURATION, PERSON_SATURATION_TOLERANCE = .72, .22
CONFIDENCE_CAP = .95                            # a colour rule is never certain
# Pixels as the renderer shades the actors' colours (facing the camera), for the colour classifier's self-test.
SAMPLES = {'fox': (127, 61, 16), 'chicken': (145, 143, 138), 'person': (28, 57, 100)}
GROUND = (73, 103, 77)


def horizontal_fov(fov, width, height):
    """Horizontal field of view in degrees of a camera whose 'fov' is the vertical one."""
    return math.degrees(2 * math.atan(math.tan(math.radians(fov) / 2) * width / height))


def bearing(bbox, width, fov):
    """Direction of a box in degrees, positive to the LEFT of the image centre. fov is the horizontal field of view."""
    offset = (width / 2 - (bbox[0] + bbox[2]) / 2) / (width / 2)  # +1 at the left edge of the image, -1 at the right
    return math.degrees(math.atan(offset * math.tan(math.radians(fov) / 2)))


def regions(mask):
    """4-connected regions of a boolean image: (labels, boxes).

    labels is an int32 image, 0 for background and i + 1 for region i; boxes[i] is its x0, y0, x1, y1 (x1 and y1 lie
    just outside). It joins horizontal runs of pixels instead of pixels, so a frame takes well under a millisecond.
    """
    height, width = mask.shape
    edges = np.diff(np.pad(mask.astype(np.int8), ((0, 0), (1, 1))), axis=1)  # +1 where a run starts, -1 just after it
    rows, begin = np.nonzero(edges == 1)
    end = np.nonzero(edges == -1)[1]  # the same runs in the same order: a run starts before it ends, in its own row
    if not len(rows):
        return np.zeros((height, width), np.int32), np.zeros((0, 4), np.int32)
    stride = width + 1  # one more than any column, so a position in the whole image is rows * stride + column
    first, last = rows * stride + begin, rows * stride + end
    below = (rows + 1) * stride
    low = np.searchsorted(last, below + begin, 'right')  # runs of the next row that end after this one begins ...
    high = np.searchsorted(first, below + end, 'left')   # ... and begin before it ends touch it
    count = np.maximum(high - low, 0)
    upper = np.repeat(np.arange(len(rows)), count)
    lower = np.repeat(low - (np.cumsum(count) - count), count) + np.arange(int(count.sum()))
    parent = list(range(len(rows)))  # union-find over runs; a region's root is its first run
    for a, b in zip(upper.tolist(), lower.tolist()):
        while parent[a] != a:
            parent[a] = a = parent[parent[a]]
        while parent[b] != b:
            parent[b] = b = parent[parent[b]]
        if a != b:
            parent[max(a, b)] = min(a, b)
    for i in range(len(parent)):  # parents always point to earlier runs, so one pass settles every root
        parent[i] = parent[parent[i]]
    region = np.unique(np.array(parent), return_inverse=True)[1].ravel()
    boxes = np.empty((int(region.max()) + 1, 4), np.int32)
    boxes[:] = (width, height, 0, 0)
    np.minimum.at(boxes[:, 0], region, begin)
    np.minimum.at(boxes[:, 1], region, rows)
    np.maximum.at(boxes[:, 2], region, end)
    np.maximum.at(boxes[:, 3], region, rows + 1)
    paint = np.zeros((height, width + 1), np.int32)  # +id where a run starts, -id after it: a running sum paints the runs
    paint[rows, begin] += region + 1
    paint[rows, end] -= region + 1
    return np.cumsum(paint, axis=1, dtype=np.int32)[:, :width], boxes


def classify(rgb, min_brightness):
    """{label: (mask, closeness)} of the pixels that look like a fox, a chicken or a person's jacket.

    mask is a boolean image; closeness (float 0-1, valid where the mask is set) tells how near the reference colour.
    Pixels darker than min_brightness (the luma of the colour) belong to no class.
    """
    colour = rgb.astype(np.float32) / 255
    red, green, blue = colour[:, :, 0], colour[:, :, 1], colour[:, :, 2]
    value = colour.max(axis=2)
    span = value - colour.min(axis=2)
    saturation = span / np.maximum(value, 1e-6)
    step = np.maximum(span, 1e-6)
    hue = np.where(value == red, ((green - blue) / step) % 6, np.where(value == green, (blue - red) / step + 2,
                                                                       (red - green) / step + 4)) * 60
    lit = colour @ LUMA >= min_brightness
    # Each closeness is 1 at the reference colour and 0 at the edge of what the class accepts.
    fox = 1 - np.maximum(abs(hue - FOX_HUE) / FOX_HUE_TOLERANCE,
                         abs(saturation - FOX_SATURATION) / FOX_SATURATION_TOLERANCE)
    person = 1 - np.maximum(abs(hue - PERSON_HUE) / PERSON_HUE_TOLERANCE,
                            abs(saturation - PERSON_SATURATION) / PERSON_SATURATION_TOLERANCE)
    # A hen is a warm white (red >= green >= blue): the neutral sky and the cool-grey fence do not qualify.
    white = 1 - abs(saturation - WHITE_SATURATION) / WHITE_TOLERANCE
    warm = (red >= green) & (green >= blue) & (value >= WHITE_VALUE)
    return {'fox': (lit & (fox > 0), fox), 'chicken': (lit & warm & (white > 0), white),
            'person': (lit & (person > 0), person)}


def colour_blobs(rgb, min_pixels=20, min_brightness=.15, masks=False):
    """Objects found in an rgb image (uint8 HxWx3) by colour alone, largest and surest first.

    Each is {'label', 'confidence', 'bbox': [x0, y0, x1, y1], 'pixels'}: the box starts at pixel (x0, y0) and ends just
    before (x1, y1). A patch of one class that is connected (4-neighbours) and has min_pixels pixels is an object; its
    confidence grows with its size and with how close its colours are to the class colour. With masks=True each
    object also has 'mask', a boolean array the size of its box that marks its pixels.
    """
    objects = []
    for label, (mask, closeness) in classify(rgb, min_brightness).items():
        if mask.sum() < min_pixels:
            continue
        labels, boxes = regions(mask)
        counts = np.bincount(labels.ravel(), minlength=len(boxes) + 1)[1:]
        purity = np.bincount(labels.ravel(), weights=closeness.ravel(), minlength=len(boxes) + 1)[1:] / np.maximum(counts, 1)
        for index in np.flatnonzero(counts >= min_pixels).tolist():
            x0, y0, x1, y1 = (int(v) for v in boxes[index])
            size = counts[index] / (counts[index] + 2 * min_pixels)  # 1/3 at the smallest size, 0.71 at 5 times that
            found = {'label': label, 'confidence': round(float(min(CONFIDENCE_CAP, purity[index] * size)), 3),
                     'bbox': [x0, y0, x1, y1], 'pixels': int(counts[index])}
            if masks:
                found['mask'] = labels[y0:y1, x0:x1] == index + 1
            objects.append(found)
    return sorted(objects, key=lambda o: (-o['confidence'], -o['pixels']))


class Detector(Module):
    """Recognises fox, chicken and person for one camera. Settings are the scenario's 'detector' section."""
    kind = 'detector'
    common_limitations = (
        'It only reports what each frame shows; confirming a sighting over several frames is up to the behaviour.',
        'Taking a frame costs no time here; a real model on the camera board needs a fraction of a second.',
    )
    type_limitations = {
        'ground-truth': (
            'An ideal model: it reads from the renderer which body every pixel shows, so it never confuses animals '
            'and never reports anything that is not there.',
            'Only light and size limit it: pixels darker than the minimum brightness do not count, and an object '
            'with fewer than the minimum number of pixels is not seen.',
        ),
        'colour-blob': (
            "Looks at colour only, tuned to the simulator's flat colours (fox orange, chicken cream-white, jacket "
            'blue). Real fur, feathers and clothes, shadows and white balance would need other rules.',
            'Known confusions: the hens\' beak and legs and the person\'s skin are not orange enough to count as a '
            'fox, but the fox\'s pale tail tip counts as a small chicken, and the dock\'s blue differs from the '
            'jacket by only ten degrees of hue.',
            'A person is found by the jacket only (trousers and head are not blue), so only seen from the waist up.',
            'Nothing is found in the grey infrared image, and little by moonlight alone: the colours are gone.',
        ),
        'external': (
            'The detections come from an outside program (the AI camera module); this module only checks their '
            'shape and age.',
            'A message counts for the stale time in simulation seconds, so a slow program at a high simulation '
            'speed is often too late.',
            'An object without a label fox, chicken or person, a confidence from 0 to 1 and a box [x0, y0, x1, y1] '
            'is skipped and counted.',
            'Bearing is worked out from the box when the program sends none; distance stays unknown unless sent.',
        ),
    }

    def __init__(self, hub, settings, cameras, labels):
        """cameras(camera_id) gives the CameraSensor or None; labels() gives {Bullet body id: 'fox'|'chicken'|'person'}."""
        super().__init__('detector', NAMES['ground-truth'])
        self.hub, self.cameras, self.labels = hub, cameras, labels
        self.time = 0.        # simulation time of the latest update()
        self.error = None     # what went wrong in the latest detection, if anything
        self.set_settings(settings)

    @property
    def limitations(self):
        return self.common_limitations + self.type_limitations[self.settings['type']]

    def set_settings(self, settings):
        """Use new settings from now on. The next update() detects again on the current frame."""
        if settings.get('type') not in TYPES:
            raise ValueError(f"Detector type must be one of {', '.join(TYPES)}")
        self.settings = copy.deepcopy(settings)
        self.name = NAMES[settings['type']]
        camera = self.settings['camera']
        external = settings['type'] == 'external'
        self.topic = f'detections/{camera}' if camera else None
        self.publishes = () if external or not camera else (self.topic,)
        self.subscribes = (settings['external_topic'],) if external else (f'camera/{camera}',) if camera else ()
        self.result = None    # newest result of a built-in kind
        self.seen = None      # the camera shot it was made from
        self.error = None
        self.skipped = 0      # objects of outside messages that were malformed, so far
        self.problem = None   # the latest reason for skipping one
        self.counted = None   # sequence number of the outside message already counted
        self.normalised = None
        self.measured = None  # (shot, labels, min_brightness, truth) of the latest truth()

    # Detecting

    def camera(self):
        return self.cameras(self.settings['camera'])

    def update(self, time):
        """Call after every physics step: detects, and publishes on 'detections/<camera id>', when the camera has a new frame."""
        self.time = time
        if self.settings['type'] == 'external':
            return
        camera = self.camera()
        shot = None if camera is None else camera.shot
        if shot is None or shot is self.seen:
            return
        self.seen = shot  # before detecting, so a failing frame is not tried again at every physics step
        try:
            self.result = {'time': round(float(time if camera.last is None else camera.last), 6),
                           'frame': shot['frame'], 'camera': camera.id, 'detector': self.settings['type'],
                           'lighting': shot['lighting'], 'objects': self.detect(camera, shot)}
            self.error = None
        except Exception as error:  # one broken detector must not stop the physics loop; its status shows 'error'
            self.error = f'{type(error).__name__}: {error}'
            return
        self.hub.publish(self.topic, self.result, self.id)

    def detect(self, camera, shot):
        """The objects of one frame, for the built-in kinds."""
        s, width = self.settings, shot['rgb'].shape[1]
        d = camera.definition
        fov = horizontal_fov(d['fov'], width, d['height'])
        if s['type'] == 'colour-blob':
            found = [(o['label'], o['confidence'], o['bbox'], o['mask'])
                     for o in colour_blobs(shot['rgb'], s['min_pixels'], s['min_brightness'], masks=True)]
        else:
            found = []
            for label, _, lit in self.bodies(shot):
                if lit.sum() >= s['min_pixels']:
                    ys, xs = np.nonzero(lit)
                    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
                    found.append((label, 1., bbox, lit[bbox[1]:bbox[3], bbox[0]:bbox[2]]))
        objects = []
        for label, confidence, bbox, mask in found:
            metres = shot['depth'][bbox[1]:bbox[3], bbox[0]:bbox[2]][mask]
            metres = metres[np.isfinite(metres)]
            objects.append({'label': label, 'confidence': confidence, 'bbox': bbox, 'pixels': int(mask.sum()),
                            'distance': round(float(np.median(metres)), 3) if metres.size else None,
                            'bearing': round(bearing(bbox, width, fov), 2)})
        return sorted(objects, key=lambda o: (-o['confidence'], -o['pixels']))

    def bodies(self, shot):
        """[(label, all pixels, pixels bright enough)] as boolean images, for every labelled body in the frame."""
        labels, segmentation = self.labels(), shot['segmentation']
        bright = shot['brightness'] >= self.settings['min_brightness']
        found = []
        for body in np.unique(segmentation).tolist():
            if body in labels:
                there = segmentation == body
                found.append((labels[body], there, there & bright))
        return found

    # Reading

    def latest(self, time):
        """The newest usable result at simulation time `time`, or None. Do not change it: the hub holds the same object.

        A built-in kind gives the latest frame's result, an outside program the newest message on its topic; both
        count as usable for `stale` seconds (a built-in one also for two camera periods, if that is longer).
        """
        if self.settings['type'] == 'external':
            return self.outside(time)
        camera = self.camera()
        if self.result is None or camera is None:
            return None
        return self.result if self.fresh(self.result['time'], time, max(self.settings['stale'], 2 * camera.period)) else None

    @staticmethod
    def fresh(stamp, time, stale):
        return -FUTURE <= time - stamp <= stale + EPSILON

    def truth(self):
        """What the latest frame really shows, whatever the kind: {'frame', 'objects': {label: {...}}}.

        Per label seen: 'pixels' (all of them), 'lit_pixels' (bright enough to count) and 'distance' (metres to the
        nearest body of that label, from the median depth of its pixels; None if no depth). Labels not in view are absent.
        """
        camera = self.camera()
        shot = None if camera is None else camera.shot
        if shot is None:
            return {'frame': None, 'objects': {}}
        key = (dict(self.labels()), self.settings['min_brightness'])
        if self.measured and self.measured[0] is shot and self.measured[1] == key:
            return copy.deepcopy(self.measured[2])  # asked again for the same frame: metrics may do so at every step
        seen = {}
        for label, there, lit in self.bodies(shot):
            metres = shot['depth'][there]
            metres = metres[np.isfinite(metres)]
            entry = seen.setdefault(label, {'pixels': 0, 'lit_pixels': 0, 'distance': None})
            entry['pixels'] += int(there.sum())
            entry['lit_pixels'] += int(lit.sum())
            if metres.size:
                near = round(float(np.median(metres)), 3)
                entry['distance'] = near if entry['distance'] is None else min(entry['distance'], near)
        result = {'frame': shot['frame'], 'objects': seen}
        self.measured = (shot, key, result)
        return copy.deepcopy(result)

    # Outside programs

    def outside(self, time):
        topic = self.settings['external_topic']
        message = self.hub.latest(topic).get(topic)  # latest() matches prefixes: pick the exact topic
        if message is None or not self.fresh(message['time'], time, self.settings['stale']):
            return None
        if self.counted != message['seq']:  # looked at once per message: malformed objects are counted once
            self.counted, self.normalised = message['seq'], self.normalise(message)
        return self.normalised

    def normalise(self, message):
        """A message from an outside program in the shape of a built-in result, without its malformed objects."""
        value, camera = message['value'], self.camera()
        if not isinstance(value, dict) or not isinstance(value.get('objects'), list):
            self.skipped, self.problem = self.skipped + 1, "the message needs an 'objects' list"
            return None
        objects = []
        for index, raw in enumerate(value['objects']):
            try:
                objects.append(self.outside_object(raw, camera))
            except ValueError as error:
                self.skipped, self.problem = self.skipped + 1, f'object {index + 1}: {error}'
        frame = value.get('frame')
        return {'time': message['time'], 'frame': frame if isinstance(frame, int) and not isinstance(frame, bool) else None,
                'camera': self.settings['camera'], 'detector': 'external',
                'lighting': None if camera is None or camera.shot is None else camera.shot['lighting'],
                'objects': sorted(objects, key=lambda o: (-o['confidence'], -o['pixels']))}

    @staticmethod
    def number(value, name, lo=-math.inf, hi=math.inf):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) \
                or not lo <= value <= hi:
            raise ValueError(f'{name} must be a number' + ('' if (lo, hi) == (-math.inf, math.inf) else f' from {lo} to {hi}'))
        return float(value)

    def outside_object(self, raw, camera):
        if not isinstance(raw, dict):
            raise ValueError('it must be an object')
        label = str(raw.get('label', '')).strip().lower()
        if label not in LABELS:
            raise ValueError(f"label must be one of {', '.join(LABELS)}")
        confidence = self.number(raw.get('confidence'), 'confidence', 0, 1)
        box = raw.get('bbox')
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            raise ValueError('bbox must be [x0, y0, x1, y1]')
        x0, y0, x1, y1 = (self.number(v, 'bbox') for v in box)
        if x1 <= x0 or y1 <= y0:
            raise ValueError('bbox must have x1 > x0 and y1 > y0')
        bbox = [round(v, 2) for v in (x0, y0, x1, y1)]
        pixels = raw.get('pixels')
        pixels = int(self.number(pixels, 'pixels', 0, math.inf)) if pixels is not None else round((x1 - x0) * (y1 - y0))
        distance = raw.get('distance')
        distance = round(self.number(distance, 'distance', 0, math.inf), 3) if distance is not None else None
        direction = raw.get('bearing')
        if direction is not None:
            direction = self.number(direction, 'bearing', -180, 180)
        elif camera is not None:
            d = camera.definition
            direction = bearing(bbox, d['width'], horizontal_fov(d['fov'], d['width'], d['height']))
        return {'label': label, 'confidence': round(confidence, 3), 'bbox': bbox, 'pixels': pixels,
                'distance': distance, 'bearing': None if direction is None else round(direction, 2)}

    # Hub module

    def status(self):
        """'ok'; 'waiting' for an outside program with no fresh message; 'error' if the camera is missing or detection failed."""
        if self.error:
            return 'error'
        if self.settings['type'] == 'external':
            return 'ok' if self.outside(self.time) is not None else 'waiting'
        return 'ok' if self.camera() is not None else 'error'

    def config(self):
        config = copy.deepcopy(self.settings)
        if self.settings['type'] == 'external':
            config.update(skipped=self.skipped, last_problem=self.problem)
        return config

    def self_test(self):
        s = self.settings
        labels = self.labels()
        unknown = sorted({str(v) for v in labels.values()} - set(LABELS))
        checks = [check('Labels name only fox, chicken or person', not unknown,
                        f'{len(labels)} labelled bodies' + (f', unknown: {", ".join(unknown)}' if unknown else ''))]
        if s['type'] == 'external':
            message = self.hub.latest(s['external_topic']).get(s['external_topic'])
            age = None if message is None else self.time - message['time']
            checks.append(check('A fresh message arrived on ' + s['external_topic'], self.outside(self.time) is not None,
                                'none yet' if message is None else f"newest is {age:.1f} s old, stale after {s['stale']} s"))
            checks.append(check('Outside objects are well formed', self.skipped == 0,
                                f'{self.skipped} skipped' + (f': {self.problem}' if self.problem else '')))
            return checks
        camera = self.camera()
        checks.append(check('Camera ' + (s['camera'] or '(none chosen)') + ' exists', camera is not None,
                            'a camera sensor is needed' if camera is None else camera.name))
        if camera is None:
            return checks
        if s['type'] == 'colour-blob':
            picture = np.empty((24, 72, 3), np.uint8)
            picture[:] = GROUND
            for i, colour in enumerate(SAMPLES.values()):
                picture[4:20, 4 + 24 * i:20 + 24 * i] = colour
            found = sorted(o['label'] for o in colour_blobs(picture, s['min_pixels'], s['min_brightness']))
            checks.append(check('Colour classes find a fox, chicken and person patch', found == sorted(SAMPLES),
                                f"found {', '.join(found) or 'nothing'} in a test picture (patches of 256 pixels)"))
        return checks
