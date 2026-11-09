"""The hub: the one place where every part of the coop simulation, and any program outside it, meets.

A module is anything with an id, a status, settings, a self-test and a list of what it does not model: the world,
the robot, each sensor, the animals and visitors, the detector, the behaviour, the battery and the metrics. Modules
publish messages on topics
(camera/head-cam, sensors/tof-left, ...); the dashboard and outside programs read the latest message per topic or
follow them live. Outside programs, such as an AI camera model on a laptop, register over HTTP, send heartbeats and
publish their results on the same topics (see hub_client.py).
"""
import json
import re
import threading
import time
from collections import deque

TOPIC = re.compile(r'[a-z0-9][a-z0-9_.\-/]{0,119}')
MODULE_ID = re.compile(r'[A-Za-z0-9_-]{1,40}')
EXTERNAL_TIMEOUT = 5.  # wall-clock seconds without a heartbeat before an outside module counts as stale
MAX_EXTERNAL_MESSAGE = 64 * 1024
MAX_EXTERNAL_MODULES = 16


def check(name, ok, detail=''):
    """One line of a self-test report."""
    return {'name': str(name), 'ok': bool(ok), 'detail': str(detail)}


class Module:
    """Base class for everything that plugs into the hub."""
    kind = 'module'
    limitations = ()   # what this module does not model, shown in the dashboard
    publishes = ()     # topics it writes
    subscribes = ()    # topics it reads

    def __init__(self, module_id, name):
        self.id, self.name = module_id, name

    def status(self):
        return 'ok'

    def config(self):
        return {}

    def self_test(self):
        """A list of check(...) results; an exception counts as a failed test."""
        return []

    def describe(self):
        return {'id': self.id, 'name': self.name, 'kind': self.kind, 'status': self.status(), 'external': False,
                'config': self.config(), 'limitations': list(self.limitations),
                'publishes': list(self.publishes), 'subscribes': list(self.subscribes)}


def _topics(value, name):
    if not isinstance(value, list) or len(value) > 32 or not all(isinstance(t, str) and TOPIC.fullmatch(t) for t in value):
        raise ValueError(f'{name} must be a list of topic names such as vision/detections')
    return value


class ExternalModule(Module):
    """A program outside the simulator that registered over HTTP."""

    def __init__(self, definition):
        module_id = str(definition.get('id', ''))
        if not MODULE_ID.fullmatch(module_id):
            raise ValueError('Module id must be 1-40 letters, digits, - or _')
        name = str(definition.get('name') or module_id).strip()[:80]
        super().__init__(module_id, name)
        self.kind = str(definition.get('kind') or 'external').strip()[:40]
        self.publishes = _topics(definition.get('publishes', []), 'publishes')
        self.subscribes = _topics(definition.get('subscribes', []), 'subscribes')
        limitations = definition.get('limitations', [])
        if not isinstance(limitations, list) or len(limitations) > 20:
            raise ValueError('limitations must be a list of at most 20 sentences')
        self.limitations = [str(item)[:300] for item in limitations]
        info = definition.get('info', {})
        if not isinstance(info, dict) or len(json.dumps(info)) > 4000:
            raise ValueError('info must be a small object')
        self.info = info
        self.last_seen = time.monotonic()

    def age(self):
        return time.monotonic() - self.last_seen

    def status(self):
        return 'ok' if self.age() < EXTERNAL_TIMEOUT else 'stale'

    def config(self):
        return self.info

    def self_test(self):
        return [check('Heartbeat received recently', self.status() == 'ok', f'last seen {self.age():.1f} s ago')]

    def describe(self):
        return {**super().describe(), 'external': True, 'last_seen_s': round(self.age(), 2)}


class Hub:
    def __init__(self, clock=None):
        self.clock = clock or (lambda: 0.)  # simulation time stamped on every message
        self.lock = threading.RLock()
        self.changed = threading.Condition(self.lock)
        self.sequence = 0
        self._modules = {}
        self._latest = {}
        self._log = deque(maxlen=2000)
        self._frames = {}
        self.tests = {}

    # Modules

    def register(self, module):
        """Add or replace a built-in module (rebuilding a sensor registers it again under the same id)."""
        with self.lock:
            self._modules[module.id] = module
            self.tests.pop(module.id, None)
        return module

    def unregister(self, module_id):
        """Remove a module with its last self-test, camera frame and latest messages (a deleted sensor's topics go)."""
        with self.lock:
            self._modules.pop(module_id, None)
            self.tests.pop(module_id, None)
            self._frames.pop(module_id, None)
            self._latest = {topic: m for topic, m in self._latest.items() if m['source'] != module_id}

    def unregister_kind(self, kind):
        for module in self.list(kind):
            self.unregister(module.id)

    def module(self, module_id):
        with self.lock:
            if module_id not in self._modules:
                raise ValueError('Module not found: ' + str(module_id))
            return self._modules[module_id]

    def list(self, kind=None):
        with self.lock:
            return [m for m in self._modules.values() if kind is None or m.kind == kind]

    def modules(self):
        with self.lock:
            return [{**m.describe(), 'last_test': self.tests.get(m.id)} for m in self._modules.values()]

    # Messages

    def publish(self, topic, value, source):
        if not isinstance(topic, str) or not TOPIC.fullmatch(topic):
            raise ValueError('Topic names use lower-case letters, digits and . _ - /, for example vision/detections')
        with self.changed:
            self.sequence += 1
            message = {'seq': self.sequence, 'topic': topic, 'source': source, 'time': self.clock(), 'value': value}
            self._latest[topic] = message
            self._log.append(message)
            self.changed.notify_all()
            return message

    def latest(self, prefix=''):
        with self.lock:
            return {topic: message for topic, message in sorted(self._latest.items()) if topic.startswith(prefix)}

    def since(self, sequence, prefix=''):
        with self.lock:
            return [m for m in self._log if m['seq'] > sequence and m['topic'].startswith(prefix)]

    def wait(self, sequence, timeout):
        """Block until a message newer than sequence exists or timeout passes; returns the current sequence."""
        with self.changed:
            self.changed.wait_for(lambda: self.sequence > sequence, timeout)
            return self.sequence

    # Self-tests

    def run_test(self, module_id):
        module = self.module(module_id)
        started = time.perf_counter()
        try:
            checks = list(module.self_test())
        except Exception as error:  # a crashing self-test is a failed self-test, not a server error
            checks = [check('Self-test ran', False, f'{type(error).__name__}: {error}')]
        result = {'module': module.id, 'name': module.name, 'ok': bool(checks) and all(c['ok'] for c in checks),
                  'checks': checks, 'time': self.clock(), 'duration_ms': round((time.perf_counter() - started) * 1000, 1)}
        with self.lock:
            self.tests[module.id] = result
        self.publish('hub/self-test', result, 'hub')
        return result

    def run_all_tests(self):
        return [self.run_test(module.id) for module in self.list()]

    # Outside programs

    def register_external(self, definition):
        if not isinstance(definition, dict):
            raise ValueError('Send the module definition as a JSON object')
        module = ExternalModule(definition)
        with self.lock:
            existing = self._modules.get(module.id)
            if existing is not None and not isinstance(existing, ExternalModule):
                raise ValueError('That id belongs to a built-in module; choose another')
            if existing is None and sum(isinstance(m, ExternalModule) for m in self._modules.values()) >= MAX_EXTERNAL_MODULES:
                raise ValueError(f'At most {MAX_EXTERNAL_MODULES} outside modules can be registered')
            self._modules[module.id] = module
        self.publish('hub/modules', {'registered': module.id}, 'hub')
        return module.describe()

    def external(self, module_id):
        module = self.module(module_id)
        if not isinstance(module, ExternalModule):
            raise ValueError('Only outside modules use this call')
        return module

    def heartbeat(self, module_id):
        module = self.external(module_id)
        module.last_seen = time.monotonic()
        return module.describe()

    def publish_external(self, module_id, topic, value):
        module = self.external(module_id)
        if len(json.dumps(value)) > MAX_EXTERNAL_MESSAGE:
            raise ValueError('Messages from outside modules must be smaller than 64 KB; send images as files instead')
        module.last_seen = time.monotonic()
        return self.publish(topic, value, module.id)

    def remove_external(self, module_id):
        self.external(module_id)
        self.unregister(module_id)
        self.publish('hub/modules', {'removed': module_id}, 'hub')

    # Camera images (too large for messages; the message carries the frame number)

    def store_frame(self, camera_id, png, meta):
        with self.lock:
            self._frames[camera_id] = (png, meta)

    def frame(self, camera_id):
        with self.lock:
            return self._frames.get(camera_id)
