#!/usr/bin/env python3
"""The same unmodified engine serves an unrelated, entirely data-defined API."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('move package to Haifa', 'move_package', {'destination': 'Haifa'}),
    ('send package to Rue des Lilas 12', 'move_package', {'destination': 'Rue des Lilas 12'}),
    ('set kitchen lamp to 30', 'set_lamp', {'room': 'kitchen', 'brightness': 30}),
    ('dim bedroom lamp to 20', 'set_lamp', {'room': 'bedroom', 'brightness': 20}),
    ('turn device on', 'switch_device', {'power': True}),
    ('turn device off', 'switch_device', {'power': False}),
    ('switch device enabled', 'switch_device', {'power': True}),
    ('set study lamp to 101', None, None),
    ('do not move package', None, None),
    ('weather today', None, None),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', default=str(ROOT / 'wolfe'))
    args = parser.parse_args()
    process = subprocess.run(shlex.split(args.engine) + [
        '--tools', 'examples/custom_tools.json', '--examples', 'examples/custom_examples.jsonl', '--batch'
    ], input=''.join(json.dumps({'text': q}) + '\n' for q, _, _ in CASES),
        text=True, capture_output=True, cwd=ROOT, timeout=30)
    assert process.returncode == 0, process.stderr
    results = [json.loads(line) for line in process.stdout.splitlines()]
    assert len(results) == len(CASES)
    for (query, name, arguments), result in zip(CASES, results):
        expected = [] if name is None else [{'name': name, 'arguments': arguments}]
        assert result['calls'] == expected, (query, expected, result)
    print(f'{len(CASES)} custom-schema contracts passed')


if __name__ == '__main__':
    main()
