#!/usr/bin/env python3
"""Boundary contracts for literal payloads, argument absence and explanation modes."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = [str(ROOT / 'wolfe')]


class SemanticContracts(unittest.TestCase):
    def call(self, text, mode=None):
        options = [] if mode is None else ['--reasoning' if mode == 'full' else '--reasoning-compact']
        p = subprocess.run(ENGINE + options + [text], cwd=ROOT, text=True,
                           capture_output=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def test_function_words_can_be_a_bound_literal_title(self):
        for text in ('play For Me', 'play "For Me"'):
            with self.subTest(text=text):
                self.assertEqual(self.call(text)['calls'],
                                 [{'name': 'play_music', 'arguments': {'query': 'For Me'}}])

    def test_polite_suffix_is_outside_a_nonempty_argument(self):
        self.assertEqual(self.call('play Rammstein for me')['calls'],
                         [{'name': 'play_music', 'arguments': {'query': 'Rammstein'}}])

    def test_embedded_quotation_does_not_erase_its_surroundings(self):
        self.assertEqual(self.call('make a note: he said "yes" today')['calls'],
                         [{'name': 'create_note', 'arguments': {'text': 'he said "yes" today'}}])

    def test_observation_does_not_truncate_compound_duration(self):
        self.assertEqual(self.call('I am baking bread. Set a timer for 1 hour and 40 minutes.')['calls'],
                         [{'name': 'set_timer', 'arguments': {'seconds': 6000}}])

    def test_missing_argument_does_not_inherit_tool_confidence(self):
        answer = self.call('What is the weather like?', 'full')
        self.assertEqual(answer['calls'], [])
        self.assertEqual(answer['status'], 'missing_arguments')
        self.assertIn('city', answer['missing'])
        arguments = answer['reasoning']['arguments']
        self.assertTrue(any(a['name'] == 'unit' and a['value'] == 'celsius' for a in arguments))
        missing = answer['reasoning']['missing_arguments']
        self.assertEqual([a['name'] for a in missing], ['city'])
        self.assertGreater(missing[0]['candidates'], 0)
        self.assertIn('alternative', missing[0])

    def test_repeated_clause_extraction_preserves_default_provenance(self):
        answer = self.call('I have my coat ready. What is the weather in Berlin?', 'full')
        unit = next(a for a in answer['reasoning']['arguments'] if a['name'] == 'unit')
        self.assertEqual(unit['source'], 'schema default')
        self.assertEqual(unit['span'], [0, 0])

    def test_reasoning_levels_preserve_exact_plain_decision(self):
        text = 'play music by Portishead'
        plain = self.call(text)
        self.assertNotIn('reasoning', plain)
        for mode in ('full', 'compact'):
            with self.subTest(mode=mode):
                answer = self.call(text, mode)
                self.assertEqual({k: v for k, v in answer.items() if k != 'reasoning'}, plain)
                self.assertIn('reasoning', answer)
        full, compact = self.call(text, 'full'), self.call(text, 'compact')
        self.assertLess(len(json.dumps(compact)), len(json.dumps(full)))
        self.assertEqual(compact['reasoning']['winner'], 'play_music')
        self.assertEqual(compact['reasoning']['arguments'][0]['value'], 'Portishead')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', default=str(ROOT / 'wolfe'))
    args, rest = parser.parse_known_args()
    ENGINE = shlex.split(args.engine)
    unittest.main(argv=['semantic_contracts.py'] + rest, verbosity=2)
