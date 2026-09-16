#!/usr/bin/env python3
"""Focused regressions for malformed input and schema-constrained calls.

These fixtures are temporary declarations, independent of the demonstration
corpus and language-quality benchmarks. Run against either implementation with
--engine './wolfe' or --engine 'python3 wolfe.py'.
"""
import argparse
import json
import pathlib
import shlex
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
ENGINE = [str(ROOT / 'wolfe')]


class ParserContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.tools = self.root / 'tools.json'
        self.examples = self.root / 'examples.jsonl'
        self.define({'type': 'string'})

    def tearDown(self):
        self.tmp.cleanup()

    def define(self, prop=None, parameters=None):
        if parameters is None:
            parameters = {'type': 'object', 'properties': {'value': prop},
                          'required': ['value']}
        tool = {'name': 'set_value', 'description': 'Set value.',
                'parameters': parameters}
        self.tools.write_text(json.dumps([tool]), encoding='utf-8')
        row = {'text': 'set value {value}' if prop else 'set value',
               'tool': 'set_value',
               'arguments': {'value': '{value}'} if prop else {}}
        self.examples.write_text(json.dumps(row) + '\n', encoding='utf-8')

    def run_engine(self, query=None, batch=None):
        argv = ENGINE + ['--tools', str(self.tools), '--examples', str(self.examples)]
        if batch is not None:
            argv.append('--batch')
        elif query is not None:
            argv.append(query)
        return subprocess.run(argv, input=batch, capture_output=True, cwd=ROOT,
                              timeout=30)

    def assert_startup_error(self, proc):
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertTrue(proc.stderr.strip() or proc.stdout.strip())
        if proc.stdout.strip():
            for line in proc.stdout.decode('utf-8').splitlines():
                result = json.loads(line)
                self.assertEqual(result['calls'], [])
                self.assertEqual(result['status'], 'error')

    def assert_request_error(self, proc):
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        lines = proc.stdout.decode('utf-8').splitlines()
        self.assertEqual(len(lines), 1, proc.stderr)
        result = json.loads(lines[0])
        self.assertEqual(result['calls'], [])
        self.assertEqual(result['status'], 'error')

    def test_each_enum_member_obeys_declared_type(self):
        # The second enum member must not evade validation merely because the
        # first member passed. Numeric 2 is not a member of [1, "2"].
        self.define({'type': 'integer', 'enum': [1, '2']})
        self.assert_startup_error(self.run_engine('set value 2'))

    def test_valid_integer_enum_control(self):
        self.define({'type': 'integer', 'enum': [1, 2]})
        proc = self.run_engine('set value 2')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout.decode('utf-8'))
        self.assertEqual(result['status'], 'call')
        self.assertEqual(result['calls'], [
            {'name': 'set_value', 'arguments': {'value': 2}}])
        self.assertIs(type(result['calls'][0]['arguments']['value']), int)

    def test_unsupported_property_constraint_rejected(self):
        self.define({'type': 'integer', 'const': 1})
        self.assert_startup_error(self.run_engine('set value 2'))

    def test_unsupported_object_constraint_rejected(self):
        self.define(parameters={'type': 'object', 'properties': {},
                                'minProperties': 1})
        self.assert_startup_error(self.run_engine('set value'))

    def test_duplicate_request_keys_rejected(self):
        self.assert_request_error(self.run_engine(
            batch=b'{"text":"set value two","text":"nothing"}\n'))

    def test_batch_text_must_be_string(self):
        for value in ({'set': 'value'}, 12, True, None):
            with self.subTest(value=value):
                row = (json.dumps({'text': value}) + '\n').encode('utf-8')
                self.assert_request_error(self.run_engine(batch=row))

    def test_invalid_unicode_rejected(self):
        for payload in (b'\xff', b'\xc0\xaf', b'\xed\xa0\x80', b'\\ud800'):
            with self.subTest(payload=payload):
                self.assert_request_error(self.run_engine(
                    batch=b'{"text":"set value ' + payload + b'"}\n'))

    def test_valid_unicode_and_json_escaping_control(self):
        value = 'Montréal \\ "café" 🐺'
        row = (json.dumps({'text': 'set value ' + value}) + '\n').encode('utf-8')
        proc = self.run_engine(batch=row)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout.decode('utf-8'))
        self.assertEqual(result['status'], 'call')
        self.assertEqual(result['calls'], [
            {'name': 'set_value', 'arguments': {'value': value}}])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', default=str(ROOT / 'wolfe'),
                        help='Executable command; Python command also accepted')
    args, remainder = parser.parse_known_args()
    ENGINE = shlex.split(args.engine)
    unittest.main(argv=['parser_contracts.py'] + remainder, verbosity=2)
