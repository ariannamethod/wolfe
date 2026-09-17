#!/usr/bin/env python3
"""Independent, predeclared STEP11 specificity contracts on neutral tools."""
import argparse
import itertools
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = [str(ROOT / 'wolfe')]
BROAD = 'sort cobalt parcel'
ANCHOR = 'fold copper'
REPORT = {'fixtures': [], 'responses': []}


class SpecificityContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def variants(self):
        for index, (reverse_tools, reverse_examples, swap_labels) in enumerate(
                itertools.product((False, True), repeat=3)):
            self.variant = {'reverse_tools': reverse_tools, 'reverse_examples': reverse_examples,
                            'swap_labels': swap_labels}
            self.fixture = self._testMethodName + ':' + str(index)
            folder = self.directory / str(index)
            folder.mkdir()
            self.tools, self.examples = folder / 'tools.json', folder / 'examples.jsonl'
            self.state, self.record = folder / 'state.json', folder / 'correction.json'
            names = ['amber', 'violet']
            if reverse_tools:
                names.reverse()
            definitions = {'tools': [
                {'name': name, 'description': 'A user-defined action.',
                 'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}}
                for name in names]}
            self.tools.write_text(json.dumps(definitions), encoding='utf-8')
            self.definitions = definitions
            yield ('violet', 'amber') if swap_labels else ('amber', 'violet')

    def define(self, rows):
        if self.variant['reverse_examples']:
            rows = list(reversed(rows))
        self.examples.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
        REPORT['fixtures'].append({'id': self.fixture, **self.variant,
                                   'tools': self.definitions, 'examples': rows})

    def invoke(self, query=None, correction=None):
        command = ENGINE + ['--tools', str(self.tools), '--examples', str(self.examples),
                            '--state', str(self.state)]
        if correction is not None:
            self.record.write_text(json.dumps(correction), encoding='utf-8')
            command += ['--correct', str(self.record)]
        else:
            command += ['--reasoning', query]
        process = subprocess.run(command, cwd=ROOT, text=True, encoding='utf-8',
                                 capture_output=True, timeout=30)
        REPORT['responses'].append({'fixture': self.fixture, 'query': query, 'correction': correction,
                                    'returncode': process.returncode,
                                    'stdout': process.stdout, 'stderr': process.stderr})
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        return json.loads(process.stdout)

    def correct(self, text, tool):
        record = {'text': text, 'tool': tool, 'arguments': {}}
        self.assertEqual(self.invoke(correction=record), {'status': 'corrected', 'corrections': 1})
        self.assertEqual(json.loads(self.state.read_text())['corrections'], [record])

    def assert_choice(self, query, tool, statuses=('call',)):
        before = self.state.read_bytes() if self.state.exists() else None
        response = self.invoke(query)
        after = self.state.read_bytes() if self.state.exists() else None
        self.assertEqual(after, before, 'Inference must not alter correction memory')
        expected = [] if tool is None else [{'name': tool, 'arguments': {}}]
        self.assertEqual(response['calls'], expected, response)
        self.assertIn(response['status'], statuses, response)

    def test_qualified_correction_retains_broad_anchor_and_nonqualifiers(self):
        for broad_tool, qualified_tool in self.variants():
            with self.subTest(**self.variant):
                self.define([{'text': BROAD, 'tool': broad_tool, 'arguments': {}},
                             {'text': ANCHOR, 'tool': qualified_tool, 'arguments': {}}])
                self.correct(BROAD + ' urgent', qualified_tool)
                # Every query starts a new process and reloads the saved correction.
                cases = [(BROAD + ' urgent', qualified_tool), (BROAD, broad_tool),
                         (ANCHOR, qualified_tool), (BROAD + ' zyxwvu', broad_tool),
                         (BROAD + ' "urgent"', broad_tool)]
                for query, expected in cases:
                    with self.subTest(query=query):
                        self.assert_choice(query, expected)

    def test_equal_conflicting_construction_examples_remain_ambiguous(self):
        for first, second in self.variants():
            with self.subTest(**self.variant):
                text = BROAD + ' urgent'
                self.define([{'text': text, 'tool': first, 'arguments': {}},
                             {'text': text, 'tool': second, 'arguments': {}}])
                self.assert_choice(text, None, ('ambiguous',))

    def test_omitted_qualifier_without_broad_default_does_not_call(self):
        for urgent_tool, routine_tool in self.variants():
            with self.subTest(**self.variant):
                self.define([{'text': BROAD + ' urgent', 'tool': urgent_tool, 'arguments': {}},
                             {'text': BROAD + ' routine', 'tool': routine_tool, 'arguments': {}}])
                self.assert_choice(BROAD, None, ('ambiguous', 'no_call'))

    def test_qualified_null_correction_remains_no_call(self):
        for broad_tool, anchor_tool in self.variants():
            with self.subTest(**self.variant):
                self.define([{'text': BROAD, 'tool': broad_tool, 'arguments': {}},
                             {'text': ANCHOR, 'tool': anchor_tool, 'arguments': {}}])
                self.correct(BROAD + ' forbidden', None)
                self.assert_choice(BROAD + ' forbidden', None, ('no_call',))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', default=str(ROOT / 'wolfe'))
    parser.add_argument('--report', type=Path, help='Preserve fixtures and raw outputs as JSON')
    args, rest = parser.parse_known_args()
    ENGINE = shlex.split(args.engine)
    program = unittest.main(argv=['specificity_contracts.py'] + rest, verbosity=2, exit=False)
    if args.report:
        REPORT.update({'engine': ENGINE, 'passed': program.result.wasSuccessful(),
                       'tests_run': program.result.testsRun,
                       'failures': [(str(case), error) for case, error in program.result.failures],
                       'errors': [(str(case), error) for case, error in program.result.errors]})
        with args.report.open('x', encoding='utf-8') as stream:
            json.dump(REPORT, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
    raise SystemExit(0 if program.result.wasSuccessful() else 1)
