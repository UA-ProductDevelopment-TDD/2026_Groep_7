"""The coop simulator end to end: scenario edits, driving, sensors, self-tests and the hub's HTTP API."""
import math
import shutil
import socket
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

import coop_server
from coop import config
from engine import DATA, asset_url

PNG = b'\x89PNG\r\n\x1a\n'


def _leg(name, x, y):
    return f'''
  <link name="{name}-foot"><inertial><mass value="0.03"/><inertia ixx="2e-5" iyy="2e-5" izz="2e-6" ixy="0" ixz="0" iyz="0"/></inertial>
    <visual><origin xyz="0 0 -0.04"/><geometry><cylinder radius="0.01" length="0.08"/></geometry></visual>
    <collision><origin xyz="0 0 -0.04"/><geometry><cylinder radius="0.01" length="0.08"/></geometry></collision></link>
  <joint name="{name}-hip" type="revolute"><parent link="body"/><child link="{name}-foot"/>
    <origin xyz="{x} {y} -0.02"/><axis xyz="0 1 0"/><limit lower="-1" upper="1" effort="1" velocity="3"/></joint>'''


# A primitive four-legged robot, facing +x, whose links are not Bittle's.
BOX_DOG = '''<?xml version="1.0"?>
<robot name="box-dog">
  <link name="body"><inertial><mass value="0.3"/><inertia ixx="3e-4" iyy="1e-3" izz="1e-3" ixy="0" ixz="0" iyz="0"/></inertial>
    <visual><geometry><box size="0.2 0.1 0.04"/></geometry></visual>
    <collision><geometry><box size="0.2 0.1 0.04"/></geometry></collision></link>''' + ''.join(
    _leg(name, x, y) for name, x, y in (('fl', .08, .05), ('fr', .08, -.05), ('hl', -.08, .05), ('hr', -.08, -.05))
) + '\n</robot>\n'


class CoopApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(coop_server.app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def setUp(self):
        self.client.put('/api/coop/scenario', json=config.default()).raise_for_status()

    def run_physics(self, seconds):
        session = coop_server.session
        with session.lock:  # the worker thread cannot tick meanwhile
            session.set_running(True)
            for _ in range(int(seconds * session.scenario['simulation']['physics_hz'])):
                if not session.running:  # the session paused itself, as the worker would see
                    break
                session.tick()
            session.set_running(False)

    def test_model_and_state(self):
        model = self.client.get('/api/coop/model').json()
        terrain = model['world']['terrain']
        self.assertEqual(len(terrain['heights']), terrain['rows'] * terrain['cols'])
        self.assertGreater(len(model['world']['boxes']), 10)
        self.assertGreater(len(model['robot']['visuals']), 8)
        self.assertEqual(len(model['robot']['feet']), 4)
        self.assertEqual([s['id'] for s in model['sensors']], ['head-cam', 'tof-left', 'tof-front', 'imu'])
        self.assertIn('/assets/bittle/bittle.urdf', [m['url'] for m in model['robot_models']])
        state = self.client.get('/api/coop/state').json()
        self.assertEqual(state['time'], 0)
        self.assertFalse(state['robot']['fallen'])
        self.assertAlmostEqual(state['robot']['heading'], model['scenario']['robot']['start']['heading'], delta=1)
        self.assertEqual(set(state['sensors']), {'head-cam', 'tof-left', 'tof-front', 'imu'})
        self.assertEqual(set(state['robot']['transforms']), set(model['robot']['links']))
        frame = self.client.get('/api/hub/frame/head-cam.png')
        self.assertEqual(frame.status_code, 200)
        self.assertTrue(frame.content.startswith(PNG))
        self.assertEqual(self.client.get('/api/hub/frame/nothing.png').status_code, 404)

    def test_every_module_passes_its_self_test(self):
        ids = {m['id'] for m in self.client.get('/api/hub/modules').json()}
        self.assertTrue({'physics', 'robot', 'world', 'head-cam', 'tof-left', 'tof-front', 'imu'} <= ids)
        results = self.client.post('/api/hub/test-all').json()
        failed = {r['module']: [c for c in r['checks'] if not c['ok']] for r in results if not r['ok']}
        self.assertEqual(failed, {})
        modules = {m['id']: m for m in self.client.get('/api/hub/modules').json()}
        self.assertTrue(all(m['limitations'] for m in modules.values()), 'every module says what it does not model')
        self.assertTrue(modules['world']['last_test']['ok'])

    def test_walk_forward_on_the_coop_terrain(self):
        before = self.client.get('/api/coop/state').json()['robot']
        self.client.post('/api/coop/command', json={'action': 'drive', 'value': 'walk'}).raise_for_status()
        self.run_physics(4)
        after = self.client.get('/api/coop/state').json()
        self.assertFalse(after['robot']['fallen'])
        self.assertEqual(after['robot']['skill'], 'wkF')
        heading = math.radians(before['heading'])
        moved = [a - b for a, b in zip(after['robot']['position'], before['position'])]
        self.assertGreater(moved[0] * math.cos(heading) + moved[1] * math.sin(heading), .08)
        self.assertGreater(after['time'], 3.9)
        self.assertGreater(after['sensors']['head-cam']['frame'], 10)
        self.client.post('/api/coop/command', json={'action': 'reset'}).raise_for_status()
        reset = self.client.get('/api/coop/state').json()
        self.assertEqual(reset['time'], 0)
        self.assertLess(math.dist(reset['robot']['position'][:2], before['position'][:2]), .005)
        response = self.client.post('/api/coop/command', json={'action': 'drive', 'value': 'gB'})
        self.assertEqual(response.status_code, 400)

    def test_the_run_pauses_at_the_terrain_edge(self):
        scenario = config.default()
        scenario['robot']['start'] = {'position': [3.75, 0], 'heading': 0}
        self.client.put('/api/coop/scenario', json=scenario).raise_for_status()
        self.client.post('/api/coop/command', json={'action': 'drive', 'value': 'trot'}).raise_for_status()
        self.run_physics(6)
        state = self.client.get('/api/coop/state').json()
        self.assertFalse(state['running'])
        self.assertIsNone(state['robot']['skill'])
        self.assertTrue(any('edge of the terrain' in e['text'] for e in state['events']))
        self.assertLess(state['robot']['position'][0], 4)
        self.assertGreater(state['robot']['position'][2], -.1)  # still on the ground, not falling off the map

    def test_scenario_edits_rebuild_only_what_changed(self):
        session = coop_server.session
        world = session.world
        scenario = config.default()
        scenario['sensors'] = [s for s in scenario['sensors'] if s['id'] != 'tof-front']
        revision = self.client.get('/api/coop/state').json()['revision']
        model = self.client.put('/api/coop/scenario', json=scenario).json()
        self.assertIs(session.world, world)  # sensors only: same terrain bodies
        self.assertEqual(len(model['sensors']), 3)
        self.assertEqual(model['revision'], revision + 1)
        self.assertEqual(self.client.get('/api/coop/state').json()['revision'], revision + 1)
        self.assertNotIn('tof-front', {m['id'] for m in self.client.get('/api/hub/modules').json()})
        self.assertNotIn('sensors/tof-front', self.client.get('/api/hub/topics').json())  # no stale last message
        mass = model['robot']['mass']
        scenario['robot']['payload'].append({'id': 'battery', 'name': 'Extra battery', 'mass': .05, 'link': 'base-frame-link'})
        model = self.client.put('/api/coop/scenario', json=scenario).json()
        self.assertAlmostEqual(model['robot']['mass'], mass + .05, places=6)
        self.assertIs(session.world, world)
        scenario['terrain']['roughness'] = .02
        model = self.client.put('/api/coop/scenario', json=scenario).json()
        self.assertIsNot(session.world, world)
        self.assertEqual(model['scenario']['terrain']['roughness'], .02)

    def test_another_robot_model_takes_over_payload_and_sensors(self):
        folder = DATA / ('coop-test-' + uuid.uuid4().hex)
        folder.mkdir()
        try:
            (folder / 'robot.urdf').write_text(BOX_DOG, encoding='utf-8')
            scenario = config.default()
            scenario['robot'].update(model=asset_url(folder / 'robot.urdf'), forward_axis='+x')
            model = self.client.put('/api/coop/scenario', json=scenario).json()
            self.assertEqual(sorted(model['robot']['feet']), ['fl-foot', 'fr-foot', 'hl-foot', 'hr-foot'])
            self.assertEqual({s['link'] for s in model['scenario']['sensors']}, {'body'})
            self.assertEqual({item['link'] for item in model['scenario']['robot']['payload']}, {'body'})
            events = [e['text'] for e in self.client.get('/api/coop/state').json()['events']]
            self.assertTrue(any('Head camera (ESP32-S3) moved from head-link to body' in e for e in events))
            self.assertTrue(all(r['ok'] for r in self.client.post('/api/hub/test-all').json() if r['module'] != 'head-cam'))
            # A wrong link without a model change is still an error.
            scenario = model['scenario']
            scenario['sensors'][0]['link'] = 'tail'
            self.assertEqual(self.client.put('/api/coop/scenario', json=scenario).status_code, 400)
        finally:
            self.client.put('/api/coop/scenario', json=config.default())
            shutil.rmtree(folder, ignore_errors=True)

    def test_bad_edits_are_refused_and_the_world_keeps_working(self):
        response = self.client.put('/api/coop/scenario', json={'terrain': {'roughness': 5}})
        self.assertEqual(response.status_code, 400)
        self.assertIn('roughness', response.json()['detail'])
        scenario = config.default()
        scenario['sensors'][0]['link'] = 'tail-link'
        response = self.client.put('/api/coop/scenario', json=scenario)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Head camera', response.json()['detail'])
        self.assertEqual(self.client.get('/api/coop/scenario').json(), config.validate(config.default()))
        self.assertEqual(self.client.get('/api/coop/state').status_code, 200)
        scenario = config.default()
        scenario['terrain']['seed'] = 99
        scenario['robot']['model'] = '/assets/missing/robot.urdf'
        self.assertEqual(self.client.put('/api/coop/scenario', json=scenario).status_code, 400)
        self.assertEqual(coop_server.session.scenario['terrain']['seed'], config.DEFAULT_SCENARIO['terrain']['seed'])
        cross = self.client.post('/api/coop/command', json={'action': 'reset'}, headers={'Origin': 'http://evil.example'})
        self.assertEqual(cross.status_code, 403)

    def test_speed_and_saved_scenarios(self):
        self.client.post('/api/coop/command', json={'action': 'speed', 'value': 4}).raise_for_status()
        self.assertEqual(self.client.get('/api/coop/state').json()['speed'], 4)
        self.assertEqual(self.client.post('/api/coop/command', json={'action': 'speed', 'value': 3}).status_code, 400)
        original = config.SCENARIOS
        with tempfile.TemporaryDirectory() as folder:
            config.SCENARIOS = Path(folder)
            try:
                saved = self.client.post('/api/coop/scenarios/save', json={'name': 'my test'}).json()
                self.assertEqual(saved['scenarios'], [{'file': 'my test', 'name': 'Default coop'}])
                model = self.client.post('/api/coop/scenarios/load', json={'name': 'my test'}).json()
                self.assertEqual(model['scenario']['simulation']['speed'], 4)
                self.assertEqual(self.client.post('/api/coop/scenarios/load', json={'name': 'nope'}).status_code, 400)
            finally:
                config.SCENARIOS = original

    def test_outside_module_over_http(self):
        c = self.client
        described = c.post('/api/hub/register', json={'id': 'ai-camera', 'name': 'AI camera', 'kind': 'detector',
                                                      'publishes': ['vision/detections']}).json()
        self.assertTrue(described['external'])
        c.post('/api/hub/modules/ai-camera/heartbeat').raise_for_status()
        message = c.post('/api/hub/publish', json={'module': 'ai-camera', 'topic': 'vision/detections',
                                                   'value': [{'label': 'fox', 'confidence': .8}]}).json()
        self.assertEqual(message['source'], 'ai-camera')
        topics = c.get('/api/hub/topics', params={'prefix': 'vision/'}).json()
        self.assertEqual(topics['vision/detections']['value'][0]['label'], 'fox')
        self.assertEqual(c.post('/api/hub/publish', json={'module': 'robot', 'topic': 'x/y', 'value': 1}).status_code, 400)
        self.assertEqual(c.delete('/api/hub/modules/robot').status_code, 400)
        c.delete('/api/hub/modules/ai-camera').raise_for_status()
        self.assertNotIn('ai-camera', {m['id'] for m in c.get('/api/hub/modules').json()})


class HubClientTest(unittest.TestCase):
    """hub_client.py against a real server, as an outside program would use it."""

    @classmethod
    def setUpClass(cls):
        import uvicorn
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            cls.port = probe.getsockname()[1]
        cls.server = uvicorn.Server(uvicorn.Config(coop_server.app, host='127.0.0.1', port=cls.port, log_level='warning'))
        cls.thread = threading.Thread(target=cls.server.run, daemon=True)
        cls.thread.start()
        for _ in range(200):
            if cls.server.started:
                break
            time.sleep(.05)
        else:
            raise RuntimeError('Test server did not start')

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True
        cls.thread.join(10)

    def test_register_publish_stream_and_frame(self):
        from coop.hub_client import HubClient
        client = HubClient('test-module', 'Test module', kind='test', publishes=['test/value'],
                           base_url=f'http://127.0.0.1:{self.port}')
        client.register()
        try:
            self.assertIn('test-module', {m['id'] for m in client.modules()})
            client.heartbeat()
            client.publish('test/value', {'n': 1})
            self.assertEqual(client.latest('test/')['test/value']['value'], {'n': 1})
            self.assertTrue(client.frame('head-cam').startswith(PNG))
            stream = client.stream('test/', since=0)
            self.assertEqual(next(stream)['value'], {'n': 1})
            stream.close()
        finally:
            client.close()
        self.assertNotIn('test-module', {m['id'] for m in client.modules()})


if __name__ == '__main__':
    unittest.main()
