#!/usr/bin/env python3
"""User-facing correction memory contracts; no internal implementation imports."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = [str(ROOT / 'wolfe')]


class CorrectionContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        self.tools = self.directory / 'tools.json'
        self.examples = self.directory / 'examples.jsonl'
        self.state = self.directory / 'state.json'
        self.record = self.directory / 'correction.json'
        definitions = [
            {'name': name, 'description': 'A user-defined action.',
             'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}}
            for name in ('amber', 'violet')
        ]
        definitions.append({'name': 'deliver_parcel', 'description': 'Deliver a parcel to a destination.',
                            'parameters': {'type': 'object', 'properties': {'destination': {'type': 'string'}},
                                           'required': ['destination'], 'additionalProperties': False}})
        self.tools.write_text(json.dumps({'tools': definitions}), encoding='utf-8')
        rows = [
            {'text': 'sip cobalt', 'tool': 'amber', 'arguments': {}},
            {'text': 'fold copper', 'tool': 'violet', 'arguments': {}},
            {'text': 'deliver the parcel to {destination}', 'tool': 'deliver_parcel',
             'arguments': {'destination': '{destination}'}},
            {'text': 'send parcel to {destination}', 'tool': 'deliver_parcel',
             'arguments': {'destination': '{destination}'}},
            {'text': 'hello there', 'tool': None, 'arguments': {}},
        ]
        self.examples.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def run_engine(self, query=None, extra=(), state=True):
        command = ENGINE + ['--tools', str(self.tools), '--examples', str(self.examples)]
        if state:
            command += ['--state', str(self.state)]
        command += list(extra)
        if query is not None:
            command.append(query)
        return subprocess.run(command, cwd=ROOT, text=True, encoding='utf-8', capture_output=True, timeout=30)

    def call(self, query='sip cobalt', extra=(), state=True):
        p = self.run_engine(query, extra, state)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        return json.loads(p.stdout)

    def correct(self, text='sip cobalt', tool='violet', arguments=None, check=True, state=True):
        self.record.write_text(json.dumps({'text': text, 'tool': tool, 'arguments': arguments or {}},
                                          ensure_ascii=False), encoding='utf-8')
        p = self.run_engine(extra=['--correct', str(self.record)], state=state)
        if check:
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
            receipt = json.loads(p.stdout)
            self.assertEqual(receipt['status'], 'corrected')
            self.assertEqual(receipt['corrections'], len(json.loads(self.state.read_text())['corrections']))
        return p

    def test_prediction_does_not_create_memory(self):
        self.call()
        self.assertFalse(self.state.exists())

    def test_explicit_correction_changes_old_label(self):
        self.assertEqual(self.call()['calls'], [{'name': 'amber', 'arguments': {}}])
        self.correct()
        self.assertEqual(self.call()['calls'], [{'name': 'violet', 'arguments': {}}])
        self.assertEqual(self.call('fold copper')['calls'], [{'name': 'violet', 'arguments': {}}])

    def test_correction_can_teach_no_call(self):
        self.correct(tool=None)
        self.assertEqual(self.call()['calls'], [])
        self.assertEqual(self.call()['status'], 'no_call')

    def test_explicit_argument_constant_is_preserved(self):
        destination = 'Haifa, Oleg \\ "Ataeff"'
        query = 'deliver the parcel to my usual place'
        self.correct(query, 'deliver_parcel', {'destination': destination})
        response = self.call(query, extra=['--reasoning'])
        self.assertEqual(response['calls'], [{'name': 'deliver_parcel', 'arguments': {'destination': destination}}])
        provenance = response['reasoning']['arguments'][0]['source']
        self.assertIn('correction', provenance.lower())

    def test_literal_braces_are_not_correction_templates(self):
        query = 'deliver the parcel to {my place}'
        value = 'Locker {A-7}'
        self.correct(query, 'deliver_parcel', {'destination': value})
        self.assertEqual(self.call(query)['calls'],
                         [{'name': 'deliver_parcel', 'arguments': {'destination': value}}])

    def test_deleting_state_restores_base_and_files(self):
        original = self.call()
        sources = (self.tools.read_bytes(), self.examples.read_bytes())
        self.correct()
        self.assertEqual(self.call(state=False), original)
        self.state.unlink()
        self.assertEqual(self.call(), original)
        self.assertEqual((self.tools.read_bytes(), self.examples.read_bytes()), sources)

    def test_read_only_inference_keeps_state_byte_identical(self):
        self.correct()
        before = self.state.read_bytes()
        self.call()
        self.call('send parcel to Montréal')
        self.assertEqual(self.state.read_bytes(), before)

    def test_same_query_replaces_existing_record(self):
        self.correct()
        self.correct(tool=None)
        state = json.loads(self.state.read_text())
        self.assertEqual(len(state['corrections']), 1)
        self.assertIsNone(state['corrections'][0]['tool'])
        self.assertEqual(self.call()['calls'], [])

    def test_fifo_capacity_and_stable_replacement_position(self):
        for n in range(32):
            self.correct(text='open capsule ' + str(n))
        self.correct(text='open capsule 10', tool='amber')
        self.correct(text='open capsule 32')
        records = json.loads(self.state.read_text())['corrections']
        self.assertEqual(len(records), 32)
        self.assertEqual([row['text'] for row in records], ['open capsule ' + str(n) for n in range(1, 33)])
        self.assertEqual(records[9]['tool'], 'amber')

    def test_invalid_correction_preserves_existing_state(self):
        self.correct()
        before = self.state.read_bytes()
        invalid = [
            {'text': 'sip cobalt', 'tool': 'unknown', 'arguments': {}},
            {'text': 'ship home', 'tool': 'deliver_parcel', 'arguments': {}},
            {'text': 'ship home', 'tool': 'deliver_parcel', 'arguments': {'destination': 42}},
            {'text': 'sip cobalt', 'tool': 'amber', 'arguments': {'invented': 'value'}},
            {'text': 'sip cobalt', 'tool': None, 'arguments': {'destination': 'Haifa'}},
            {'text': ['sip cobalt'], 'tool': 'violet', 'arguments': {}},
        ]
        for record in invalid:
            with self.subTest(record=record):
                self.record.write_text(json.dumps(record))
                p = self.run_engine(extra=['--correct', str(self.record)])
                self.assertNotEqual(p.returncode, 0)
                self.assertEqual(self.state.read_bytes(), before)
                self.assertEqual(self.call()['calls'], [{'name': 'violet', 'arguments': {}}])

    def test_correction_requires_explicit_state_path(self):
        self.assertNotEqual(self.correct(check=False, state=False).returncode, 0)
        self.assertFalse(self.state.exists())

    def test_definition_change_rejects_stale_memory(self):
        self.correct()
        self.examples.write_bytes(self.examples.read_bytes() + b'\n')
        p = self.run_engine('sip cobalt')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('identity', p.stderr.lower())

    def test_legacy_counters_survive_correction(self):
        p = self.run_engine('sip cobalt', ['--feedback', 'accepted'])
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        legacy = json.loads(self.state.read_text())
        legacy['version'] = 1
        legacy.pop('corrections', None)
        self.state.write_text(json.dumps(legacy))
        self.correct()
        state = json.loads(self.state.read_text())
        self.assertEqual(state['tools']['amber'], {'accepted': 1, 'rejected': 0})
        self.assertEqual(self.call()['calls'], [{'name': 'violet', 'arguments': {}}])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', default=str(ROOT / 'wolfe'))
    args, rest = parser.parse_known_args()
    ENGINE = shlex.split(args.engine)
    unittest.main(argv=['correction_contracts.py'] + rest, verbosity=2)
