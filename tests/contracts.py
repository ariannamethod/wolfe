#!/usr/bin/env python3
"""Black-box contracts. These are not the language-quality benchmark."""
import argparse
import json
import pathlib
import shlex
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENGINE = [str(ROOT / 'wolfe')]


class Contracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.tools = self.root / 'tools.json'
        self.examples = self.root / 'examples.jsonl'
        self.define([
            {'name': 'send_parcel', 'description': 'Send a parcel to a destination.',
             'parameters': {'type': 'object', 'properties': {'destination': {'type': 'string'}},
                            'required': ['destination']}},
            {'name': 'hold_parcel', 'description': 'Hold the parcel. Stop its dispatch.',
             'parameters': {'type': 'object', 'properties': {}}}
        ], [
            {'text': 'send the parcel to {destination}', 'tool': 'send_parcel', 'arguments': {'destination': '{destination}'}},
            {'text': 'dispatch a parcel to {destination}', 'tool': 'send_parcel', 'arguments': {'destination': '{destination}'}},
            {'text': 'hold the parcel', 'tool': 'hold_parcel', 'arguments': {}},
            {'text': 'stop parcel dispatch', 'tool': 'hold_parcel', 'arguments': {}},
            {'text': 'hello there', 'tool': None, 'arguments': {}},
        ])

    def tearDown(self):
        self.tmp.cleanup()

    def define(self, tools, examples):
        self.tools.write_text(json.dumps({'tools': tools}), encoding='utf-8')
        self.examples.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in examples), encoding='utf-8')

    def run_engine(self, query=None, extra=(), stdin=None):
        argv = ENGINE + ['--tools', str(self.tools), '--examples', str(self.examples)] + list(extra)
        if query is not None:
            argv.append(query)
        return subprocess.run(argv, input=stdin, text=True, encoding='utf-8', capture_output=True,
                              cwd=ROOT, timeout=30)

    def call(self, query, extra=()):
        proc = self.run_engine(query, extra)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        obj = json.loads(proc.stdout)
        self.assertIsInstance(obj['calls'], list)
        self.assertGreaterEqual(obj['confidence'], 0)
        self.assertLessEqual(obj['confidence'], 1)
        return obj

    def test_tool_vocabulary_is_data(self):
        self.assertEqual(self.call('hold the parcel')['calls'], [{'name': 'hold_parcel', 'arguments': {}}])

    def test_verbatim_unicode_argument(self):
        calls = self.call('send the parcel to Montréal')['calls']
        self.assertEqual(calls, [{'name': 'send_parcel', 'arguments': {'destination': 'Montréal'}}])

    def test_json_metacharacters_remain_data(self):
        value = 'Oleg \\ "Ataeff"'
        calls = self.call('send the parcel to ' + value)['calls']
        self.assertEqual(calls, [{'name': 'send_parcel', 'arguments': {'destination': value}}])

    def test_missing_required_is_not_a_call(self):
        self.assertEqual(self.call('send the parcel to')['calls'], [])

    def test_batch_one_result_per_request(self):
        proc = self.run_engine(extra=['--batch'], stdin='{"text":"hold the parcel"}\n{"text":"send the parcel to Rome"}\n')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = [json.loads(x) for x in proc.stdout.splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['calls'][0]['name'], 'hold_parcel')
        self.assertEqual(rows[1]['calls'][0]['arguments']['destination'], 'Rome')

    def test_reasoning_preserves_decision(self):
        plain = self.call('hold the parcel')
        explained = self.call('hold the parcel', ['--reasoning'])
        self.assertEqual(plain['calls'], explained['calls'])
        self.assertIn('reasoning', explained)

    def test_source_files_are_unchanged_by_inference(self):
        before = (self.tools.read_bytes(), self.examples.read_bytes())
        self.call('hold the parcel')
        self.assertEqual(before, (self.tools.read_bytes(), self.examples.read_bytes()))

    def test_rebuilding_follows_edited_examples(self):
        tools = [{'name': n, 'description': 'A user-defined action.', 'parameters': {'type': 'object', 'properties': {}}}
                 for n in ('amber', 'violet')]
        examples = [{'text': 'sip cobalt', 'tool': 'amber', 'arguments': {}},
                    {'text': 'fold copper', 'tool': 'violet', 'arguments': {}}]
        self.define(tools, examples)
        first = self.call('sip cobalt')['calls']
        self.assertEqual(first, [{'name': 'amber', 'arguments': {}}])
        examples[0]['tool'], examples[1]['tool'] = 'violet', 'amber'
        self.define(tools, examples)
        self.assertEqual(self.call('sip cobalt')['calls'], [{'name': 'violet', 'arguments': {}}])

    def test_schema_unknown_tool_is_rejected(self):
        self.examples.write_text('{"text":"hello","tool":"not_declared","arguments":{}}\n')
        proc = self.run_engine('hello')
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(proc.stderr.strip())

    def test_nested_schema_is_explicitly_rejected(self):
        self.define([{'name': 'complex', 'description': 'A nested operation.', 'parameters': {'type': 'object',
                     'properties': {'payload': {'type': 'object', 'properties': {'x': {'type': 'string'}}}}}}],
                    [{'text': 'complex', 'tool': 'complex', 'arguments': {}}])
        proc = self.run_engine('complex')
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(proc.stderr.strip())

    def test_malformed_schema_rejected(self):
        self.tools.write_text('{"tools":[broken}')
        self.assertNotEqual(self.run_engine('hold the parcel').returncode, 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', default=str(ROOT / 'wolfe'), help='Executable command; Python command also accepted')
    args, remainder = parser.parse_known_args()
    ENGINE = shlex.split(args.engine)
    unittest.main(argv=['contracts.py'] + remainder, verbosity=2)
