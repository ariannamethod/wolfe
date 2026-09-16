#!/usr/bin/env python3
"""Independent load-time validation of edited correction memory.

These black-box tests edit persisted JSON directly. They complement normal
correction-write contracts: loading a file must not bypass the same schema.
"""
import argparse
import copy
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = [str(ROOT / 'wolfe')]


class PersistedCorrectionValidation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        self.tools = self.directory / 'tools.json'
        self.examples = self.directory / 'examples.jsonl'
        self.state = self.directory / 'state.json'
        self.tools.write_text(json.dumps({'tools': [
            {'name': 'wake_beacon', 'description': 'Wake a beacon.',
             'parameters': {'type': 'object', 'properties': {},
                            'additionalProperties': False}},
            {'name': 'dispatch_packet', 'description': 'Dispatch a packet.',
             'parameters': {'type': 'object', 'properties': {
                 'destination': {'type': 'string'},
                 'attempts': {'type': 'integer', 'enum': [1, 2, 3]},
                 'urgent': {'type': 'boolean'}},
                 'required': ['destination', 'attempts'],
                 'additionalProperties': False}},
        ]}), encoding='utf-8')
        rows = [
            {'text': 'wake beacon', 'tool': 'wake_beacon', 'arguments': {}},
            {'text': 'dispatch to {destination}', 'tool': 'dispatch_packet',
             'arguments': {'destination': '{destination}', 'attempts': 1}},
            {'text': 'good morning', 'tool': None, 'arguments': {}},
        ]
        self.examples.write_text(''.join(json.dumps(row) + '\n' for row in rows),
                                 encoding='utf-8')
        process = self.invoke(['--feedback', 'accepted'])
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        self.base = json.loads(self.state.read_text(encoding='utf-8'))
        self.base['version'] = 2
        self.base['corrections'] = []

    def tearDown(self):
        self.tmp.cleanup()

    def invoke(self, extra=()):
        command = ENGINE + ['--tools', str(self.tools), '--examples',
                            str(self.examples), '--state', str(self.state)]
        return subprocess.run(command + list(extra) + ['wake beacon'], cwd=ROOT,
                              capture_output=True, text=True, encoding='utf-8',
                              timeout=30)

    def write_state(self, value):
        self.state.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def assert_rejected_unchanged(self, value):
        self.write_state(value)
        before = self.state.read_bytes()
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stderr.strip(), 'rejection needs an error message')
        self.assertEqual(self.state.read_bytes(), before)
        self.assertFalse(Path(str(self.state) + '.tmp').exists())

    @staticmethod
    def record(text='deliver this packet'):
        return {'text': text, 'tool': 'dispatch_packet',
                'arguments': {'destination': 'Montréal', 'attempts': 2,
                              'urgent': True}}

    def with_records(self, records):
        state = copy.deepcopy(self.base)
        state['corrections'] = records
        return state

    def test_valid_edited_corrections_load_without_writing(self):
        value = self.with_records([self.record(),
                                   {'text': 'just a statement', 'tool': None,
                                    'arguments': {}}])
        self.write_state(value)
        before = self.state.read_bytes()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['calls'],
                         [{'name': 'wake_beacon', 'arguments': {}}])
        self.assertEqual(self.state.read_bytes(), before)

    def test_unknown_tool_and_missing_tool_rejected(self):
        for label in ('not_in_the_schema', 7, ['wake_beacon']):
            with self.subTest(label=label):
                record = self.record()
                record['tool'] = label
                self.assert_rejected_unchanged(self.with_records([record]))
        record = self.record()
        del record['tool']
        self.assert_rejected_unchanged(self.with_records([record]))

    def test_missing_required_arguments_rejected(self):
        for missing in ('destination', 'attempts', 'arguments'):
            with self.subTest(missing=missing):
                record = self.record()
                if missing == 'arguments':
                    del record['arguments']
                else:
                    del record['arguments'][missing]
                self.assert_rejected_unchanged(self.with_records([record]))
        self.assert_rejected_unchanged(self.with_records([
            {'text': 'wake beacon', 'tool': 'wake_beacon'}]))

    def test_argument_types_enums_and_unknown_properties_rejected(self):
        bad_arguments = [
            {'destination': 4, 'attempts': 2},
            {'destination': 'Haifa', 'attempts': True},
            {'destination': 'Haifa', 'attempts': '2'},
            {'destination': 'Haifa', 'attempts': 2.5},
            {'destination': 'Haifa', 'attempts': 4},
            {'destination': 'Haifa', 'attempts': 2, 'urgent': 1},
            {'destination': 'Haifa', 'attempts': 2, 'invented': False},
            {'destination': {'city': 'Haifa'}, 'attempts': 2},
            [], None,
        ]
        for arguments in bad_arguments:
            with self.subTest(arguments=arguments):
                record = self.record()
                record['arguments'] = arguments
                self.assert_rejected_unchanged(self.with_records([record]))

    def test_no_call_cannot_smuggle_arguments(self):
        record = self.record()
        record['tool'] = None
        self.assert_rejected_unchanged(self.with_records([record]))

    def test_record_shape_and_literal_text_validated_on_load(self):
        records = [None, 42, 'a correction', [],
                   {'text': '', 'tool': None},
                   {'text': '   ', 'tool': None},
                   {'text': ['wake beacon'], 'tool': None},
                   {'text': 'wake beacon', 'tool': None, 'confidence': 1.0}]
        for record in records:
            with self.subTest(record=record):
                self.assert_rejected_unchanged(self.with_records([record]))

    def test_corrections_must_be_an_array_in_version_two(self):
        for value in (None, {}, 'records', 32):
            with self.subTest(value=value):
                self.assert_rejected_unchanged(self.with_records(value))
        state = copy.deepcopy(self.base)
        del state['corrections']
        self.assert_rejected_unchanged(state)

    def test_more_than_32_persisted_records_rejected(self):
        records = [self.record('packet number ' + str(i)) for i in range(33)]
        self.assert_rejected_unchanged(self.with_records(records))

    def test_duplicate_text_is_rejected_instead_of_silently_overwritten(self):
        first = self.record()
        second = {'text': first['text'], 'tool': None, 'arguments': {}}
        self.assert_rejected_unchanged(self.with_records([first, second]))

    def test_future_missing_and_invalid_versions_rejected(self):
        for version in (0, 3, -1, 2.5, 1e300, '2', True, None):
            with self.subTest(version=version):
                state = copy.deepcopy(self.base)
                state['version'] = version
                self.assert_rejected_unchanged(state)
        state = copy.deepcopy(self.base)
        del state['version']
        self.assert_rejected_unchanged(state)

    def test_legacy_version_one_loads_counters_without_migration_on_read(self):
        state = copy.deepcopy(self.base)
        state['version'] = 1
        del state['corrections']
        self.write_state(state)
        before = self.state.read_bytes()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.state.read_bytes(), before)
        self.assertEqual(json.loads(result.stdout)['status'], 'call')

    def test_version_one_cannot_contain_correction_records(self):
        for records in ([], [self.record()]):
            with self.subTest(records=records):
                state = self.with_records(records)
                state['version'] = 1
                self.assert_rejected_unchanged(state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', default=str(ROOT / 'wolfe'))
    args, rest = parser.parse_known_args()
    ENGINE = shlex.split(args.engine)
    unittest.main(argv=['correction_state_validation.py'] + rest, verbosity=2)
