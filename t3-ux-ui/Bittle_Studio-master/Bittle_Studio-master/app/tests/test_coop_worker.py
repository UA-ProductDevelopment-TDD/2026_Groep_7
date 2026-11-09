"""An unreachable experimental gait must not kill the simulation worker."""
import threading
import time
import unittest

from coop import config
from coop.session import CoopSession


class WorkerRecoveryTest(unittest.TestCase):
    def test_unreachable_gait_pauses_and_recovers_after_settings_change(self):
        scenario = config.load_scenario('crab')
        session = CoopSession(scenario)
        # A later mission manoeuvre can ask for an unreachable foot target even
        # after the world was successfully built and placed.
        session.robot.settings['gait']['hip_height'] = .25
        paused = threading.Event()
        original_log = session.log

        def log(text):
            original_log(text)
            if text.startswith('Simulation paused:'):
                paused.set()

        session.log = log
        worker = threading.Thread(target=session.worker, daemon=True)
        worker.start()
        try:
            session.command({'action': 'mission'})
            self.assertTrue(paused.wait(5), 'The unreachable gait should produce a visible pause message')
            self.assertFalse(session.running)
            self.assertTrue(worker.is_alive(), 'Invalid settings must not terminate the worker')
            self.assertIn('out of reach', session.events[-1]['text'])

            scenario['robot']['gait']['hip_height'] = .07
            session.apply(scenario)
            session.command({'action': 'mission'})
            deadline = time.monotonic() + 5
            while session.time < .1 and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertGreaterEqual(session.time, .1, 'The same worker should run the corrected scenario')
            self.assertTrue(worker.is_alive())
        finally:
            session.close()
            worker.join(2)
