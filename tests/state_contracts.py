#!/usr/bin/env python3
"""Persistence contracts: inference is not feedback, and state stays bounded."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = [str(ROOT / 'wolfe')]


class StateContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        self.state = self.directory / 'state.json'

    def tearDown(self):
        self.tmp.cleanup()

    def run_engine(self, query='play Rammstein', options=(), check=True):
        result = subprocess.run(ENGINE + ['--state', str(self.state)] + list(options) + [query],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        if check:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result

    def feedback(self, kind):
        self.run_engine(options=['--feedback', kind])
        return json.loads(self.state.read_text())

    def test_inference_does_not_create_state(self):
        self.run_engine()
        self.assertFalse(self.state.exists())

    def test_explicit_feedback_updates_only_selected_tool(self):
        state = self.feedback('accepted')
        self.assertEqual(state['tools']['play_music'], {'accepted': 1, 'rejected': 0})
        self.assertTrue(all(v == {'accepted': 0, 'rejected': 0}
                            for k, v in state['tools'].items() if k != 'play_music'))
        state = self.feedback('rejected')
        self.assertEqual(state['tools']['play_music'], {'accepted': 1, 'rejected': 1})
        self.assertLess(self.state.stat().st_size, 2048)

    def test_predictions_leave_existing_state_byte_identical(self):
        self.feedback('accepted')
        before = self.state.read_bytes()
        self.run_engine('pause the music')
        self.run_engine()
        self.assertEqual(before, self.state.read_bytes())

    def test_deleting_state_restores_original_output(self):
        original = self.run_engine().stdout
        self.feedback('rejected')
        self.assertNotEqual(original, self.run_engine().stdout)
        self.state.unlink()
        self.assertEqual(original, self.run_engine().stdout)

    def test_changed_definitions_reject_stale_state(self):
        self.feedback('accepted')
        changed = self.directory / 'changed.jsonl'
        changed.write_bytes((ROOT / 'examples.jsonl').read_bytes() + b'\n')
        result = self.run_engine(options=['--examples', str(changed)], check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('identity', result.stderr.lower())

    def test_counter_saturation_is_bounded(self):
        state = self.feedback('accepted')
        state['tools']['play_music'] = {'accepted': 65535, 'rejected': 0}
        self.state.write_text(json.dumps(state))
        state = self.feedback('rejected')
        self.assertEqual(state['tools']['play_music'], {'accepted': 32767, 'rejected': 1})

    def test_invalid_feedback_never_writes_state(self):
        for query, options in [('hello there', ['--feedback', 'accepted']),
                               ('play Rammstein', ['--feedback', 'invented'])]:
            with self.subTest(query=query, options=options):
                self.assertNotEqual(self.run_engine(query, options, check=False).returncode, 0)
                self.assertFalse(self.state.exists())

    def test_invalid_counters_are_rejected(self):
        state = self.feedback('accepted')
        for value in (-1, 0.5, 65536, 'one'):
            with self.subTest(value=value):
                state['tools']['play_music']['accepted'] = value
                self.state.write_text(json.dumps(state))
                self.assertNotEqual(self.run_engine(check=False).returncode, 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', default=str(ROOT / 'wolfe'))
    args, rest = parser.parse_known_args()
    ENGINE = shlex.split(args.engine)
    unittest.main(argv=['state_contracts.py'] + rest, verbosity=2)
