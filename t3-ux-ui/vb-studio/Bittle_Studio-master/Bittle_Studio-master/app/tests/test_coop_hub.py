"""The module hub on its own: modules, topics, self-tests and outside programs."""
import threading
import time
import unittest

from coop import hub as hub_module
from coop.hub import Hub, Module, check


class Probe(Module):
    kind = 'probe'
    limitations = ('Not a real sensor.',)
    publishes = ('probe/value',)

    def __init__(self, module_id='probe', result=True):
        super().__init__(module_id, 'Probe')
        self.result = result

    def self_test(self):
        if self.result == 'crash':
            raise RuntimeError('broken')
        return [check('Works', self.result, 'detail')]


class HubTest(unittest.TestCase):
    def setUp(self):
        self.clock = 0.
        self.hub = Hub(clock=lambda: self.clock)

    def test_modules_and_self_tests(self):
        self.hub.register(Probe())
        self.hub.register(Probe('bad', False))
        self.hub.register(Probe('crash', 'crash'))
        described = {m['id']: m for m in self.hub.modules()}
        self.assertEqual(described['probe']['limitations'], ['Not a real sensor.'])
        self.assertTrue(self.hub.run_test('probe')['ok'])
        self.assertFalse(self.hub.run_test('bad')['ok'])
        crashed = self.hub.run_test('crash')
        self.assertFalse(crashed['ok'])
        self.assertIn('broken', crashed['checks'][0]['detail'])
        self.assertEqual(len(self.hub.run_all_tests()), 3)
        self.assertTrue({m['id']: m for m in self.hub.modules()}['probe']['last_test']['ok'])
        self.hub.unregister('bad')
        self.assertNotIn('bad', [m['id'] for m in self.hub.modules()])
        with self.assertRaises(ValueError):
            self.hub.run_test('bad')

    def test_topics_carry_simulation_time_and_sequence(self):
        self.clock = 1.5
        first = self.hub.publish('sensors/tof-left', {'distance': .4}, 'tof-left')
        second = self.hub.publish('camera/head-cam', {'frame': 1}, 'head-cam')
        self.assertEqual((first['seq'], second['seq'], first['time']), (1, 2, 1.5))
        self.assertEqual(list(self.hub.latest('sensors/')), ['sensors/tof-left'])
        self.assertEqual([m['topic'] for m in self.hub.since(1)], ['camera/head-cam'])
        for bad in ('', 'Upper/Case', 'spaces here', '/leading', 'x' * 200):
            with self.assertRaises(ValueError):
                self.hub.publish(bad, 1, 'test')

    def test_wait_wakes_on_publish(self):
        start = self.hub.sequence
        threading.Timer(.05, lambda: self.hub.publish('a/b', 1, 'test')).start()
        began = time.perf_counter()
        self.assertEqual(self.hub.wait(start, 2), start + 1)
        self.assertLess(time.perf_counter() - began, 1)
        self.assertEqual(self.hub.wait(self.hub.sequence, .01), self.hub.sequence)

    def test_outside_modules(self):
        self.hub.register(Probe('robot'))
        described = self.hub.register_external({'id': 'ai-camera', 'name': 'AI camera', 'kind': 'detector',
                                                'publishes': ['vision/detections'], 'subscribes': ['camera/head-cam'],
                                                'limitations': ['Trained on photos, not on simulator images.']})
        self.assertTrue(described['external'])
        self.assertEqual(described['status'], 'ok')
        message = self.hub.publish_external('ai-camera', 'vision/detections', [{'label': 'fox', 'confidence': .9}])
        self.assertEqual(message['source'], 'ai-camera')
        with self.assertRaises(ValueError):
            self.hub.register_external({'id': 'robot'})  # built-in ids cannot be taken over
        with self.assertRaises(ValueError):
            self.hub.publish_external('robot', 'x/y', 1)  # built-in modules publish directly
        with self.assertRaises(ValueError):
            self.hub.publish_external('ai-camera', 'x/y', 'z' * 70_000)
        with self.assertRaises(ValueError):
            self.hub.register_external({'id': 'bad id!'})
        with self.assertRaises(ValueError):
            self.hub.register_external({'id': 'x', 'publishes': ['Not A Topic']})
        module = self.hub.external('ai-camera')
        module.last_seen -= hub_module.EXTERNAL_TIMEOUT + 1
        self.assertEqual(module.status(), 'stale')
        self.assertFalse(self.hub.run_test('ai-camera')['ok'])
        self.hub.heartbeat('ai-camera')
        self.assertEqual(module.status(), 'ok')
        self.hub.remove_external('ai-camera')
        self.assertNotIn('ai-camera', [m['id'] for m in self.hub.modules()])
        with self.assertRaises(ValueError):
            self.hub.remove_external('robot')

    def test_outside_module_limit(self):
        for i in range(hub_module.MAX_EXTERNAL_MODULES):
            self.hub.register_external({'id': f'm{i}'})
        self.hub.register_external({'id': 'm0'})  # re-registering an existing one is allowed
        with self.assertRaises(ValueError):
            self.hub.register_external({'id': 'one-too-many'})

    def test_frames(self):
        self.assertIsNone(self.hub.frame('head-cam'))
        self.hub.store_frame('head-cam', b'png', {'frame': 3})
        self.assertEqual(self.hub.frame('head-cam'), (b'png', {'frame': 3}))


if __name__ == '__main__':
    unittest.main()
