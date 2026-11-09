"""Scenario validation: defaults fill gaps, mistakes are named, files round-trip."""
import json
import tempfile
import unittest
from pathlib import Path

from coop import config


class ConfigTest(unittest.TestCase):
    def test_default_is_valid_and_complete(self):
        scenario = config.validate(config.default())
        self.assertEqual(scenario, config.validate(scenario))
        self.assertEqual({s['type'] for s in scenario['sensors']}, {'camera', 'tof', 'imu'})
        self.assertEqual(config.validate({'name': 'Only a name'})['terrain'], config.DEFAULT_SCENARIO['terrain'])

    def test_mistakes_name_the_setting(self):
        cases = [
            ({'terrain': {'roughness': -1}}, 'terrain roughness'),
            ({'terrain': {'size': [8]}}, 'terrain size'),
            ({'terrain': {'size': [40, 40], 'resolution': .02}}, 'too many height samples'),
            ({'simulation': {'speed': 3}}, 'speed'),
            ({'coop': {'house_size': [5, 1, 1]}}, 'house must fit'),
            ({'robot': {'model': 'C:/robot.urdf'}}, 'robot model'),
            ({'robot': {'forward_axis': 'up'}}, 'forward axis'),
            ({'robot': {'start': {'position': [5, 0]}}}, 'robot start position lies outside the terrain'),
            ({'dock': {'position': [0, 9]}}, 'dock position lies outside'),
            ({'mud': [{'id': 'a', 'center': [0, 0], 'radius': .5, 'friction': .3},
                      {'id': 'a', 'center': [1, 0], 'radius': .5, 'friction': .3}]}, 'unique id'),
            ({'sensors': [{'id': 'cam', 'type': 'lidar', 'name': 'x', 'link': 'base'}]}, 'type must be one of'),
            ({'sensors': [{'id': 'cam', 'type': 'camera', 'name': 'Cam', 'link': 'head-link', 'fov': 400}]},
             'Cam field of view'),
            ({'sensors': [{'id': 'bad id', 'type': 'imu', 'name': 'IMU', 'link': 'base'}]}, 'IMU id'),
            ({'format': 'something-else'}, 'not a coop scenario'),
            ({'simulation': {'physics_hz': True}}, 'physics Hz'),
        ]
        for scenario, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                config.validate(scenario)

    def test_save_and_load(self):
        original = config.SCENARIOS
        with tempfile.TemporaryDirectory() as folder:
            config.SCENARIOS = Path(folder)
            try:
                scenario = config.default()
                scenario['name'] = 'Steep test'
                scenario['terrain']['roughness'] = .03
                self.assertEqual(config.save_scenario('steep test', scenario), {'file': 'steep test', 'name': 'Steep test'})
                self.assertEqual(config.list_scenarios(), [{'file': 'steep test', 'name': 'Steep test'}])
                self.assertEqual(config.load_scenario('steep test')['terrain']['roughness'], .03)
                (Path(folder) / 'broken.json').write_text('{not json', encoding='utf-8')
                self.assertEqual(len(config.list_scenarios()), 1)  # unreadable files are skipped, not fatal
                for bad in ('../escape', 'a/b', ''):
                    with self.assertRaises(ValueError):
                        config.scenario_path(bad)
                with self.assertRaises(ValueError):
                    config.load_scenario('missing')
            finally:
                config.SCENARIOS = original

    def test_bundled_scenarios_are_valid(self):
        for path in sorted(config.SCENARIOS.glob('*.json')):
            with self.subTest(path.name):
                config.validate(json.loads(path.read_text(encoding='utf-8')))


if __name__ == '__main__':
    unittest.main()
