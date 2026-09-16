#!/usr/bin/env python3
"""Compare complete C/Python JSON responses, including all reasoning fields.

No expected calls are read: this checks implementation agreement, not accuracy.
Use evaluate.py to measure whether the agreed decisions are correct.

    python3 tests/parity.py
    python3 tests/parity.py --fixtures tests/heldout.jsonl tests/final_holdout.jsonl
    python3 tests/parity.py --report reports/parity.json --tolerance 0
"""
import argparse
import json
import math
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def first_difference(left, right, tolerance, path='$'):
    """Return the first differing path, or None for structurally equal JSON."""
    if isinstance(left, bool) or isinstance(right, bool):
        return None if type(left) is type(right) and left == right else path
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if math.isfinite(left) and math.isfinite(right) and abs(left - right) <= tolerance:
            return None
        return path
    if type(left) is not type(right):
        return path
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return path + '.keys'
        for key in left:
            different = first_difference(left[key], right[key], tolerance, path + '.' + key)
            if different is not None:
                return different
        return None
    if isinstance(left, list):
        if len(left) != len(right):
            return path + '.length'
        for i, (a, b) in enumerate(zip(left, right)):
            different = first_difference(a, b, tolerance, '%s[%d]' % (path, i))
            if different is not None:
                return different
        return None
    return None if left == right else path


def run_engine(command, mode, payload, count, timeout, reasoning='full'):
    options = ['--batch', '--mode', mode]
    if reasoning != 'off':
        options.append('--reasoning' if reasoning == 'full' else '--reasoning-compact')
    process = subprocess.run(shlex.split(command) + options,
                             input=payload, text=True, encoding='utf-8', capture_output=True,
                             cwd=ROOT, timeout=timeout)
    if process.returncode:
        raise ValueError('%s exited %d: %s' % (command, process.returncode, process.stderr.strip()))
    rows = [json.loads(line) for line in process.stdout.splitlines()]
    if len(rows) != count:
        raise ValueError('%s returned %d rows for %d requests' % (command, len(rows), count))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', default=str(ROOT / 'wolfe'), help='C executable command')
    parser.add_argument('--python-engine', default='python3 wolfe.py', help='Python executable command')
    parser.add_argument('--fixtures', nargs='+', default=[str(ROOT / 'tests/heldout.jsonl')], help='Explicit JSONL fixture files')
    parser.add_argument('--modes', default='neural,field,keyword')
    parser.add_argument('--reasoning', choices=['off', 'full', 'compact'], default='full')
    parser.add_argument('--tolerance', type=float, default=1e-6, help='Absolute tolerance for all JSON numbers')
    parser.add_argument('--timeout', type=float, default=180)
    parser.add_argument('--report', help='Optional JSON report path')
    args = parser.parse_args(argv)
    if not math.isfinite(args.tolerance) or args.tolerance < 0:
        parser.error('--tolerance must be finite and nonnegative')
    modes = args.modes.split(',')
    if not modes or any(mode not in ('neural', 'field', 'keyword') for mode in modes):
        parser.error('--modes must contain neural, field, and/or keyword')
    queries = []
    for filename in args.fixtures:
        for number, line in enumerate(Path(filename).read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get('text'), str):
                raise ValueError('%s:%d needs a text string' % (filename, number))
            queries.append((filename, number, row['text']))
    if not queries:
        raise ValueError('fixture set is empty')
    payload = ''.join(json.dumps({'text': text}, ensure_ascii=False) + '\n' for _, _, text in queries)
    report = {'fixtures': args.fixtures, 'requests_per_mode': len(queries),
              'comparison': 'Entire parsed JSON tree, including reasoning and source spans',
              'absolute_tolerance': args.tolerance, 'engines': {'c': args.engine, 'python': args.python_engine},
              'reasoning': args.reasoning, 'modes': {}}
    passed = True
    for mode in modes:
        c = run_engine(args.engine, mode, payload, len(queries), args.timeout, args.reasoning)
        python = run_engine(args.python_engine, mode, payload, len(queries), args.timeout, args.reasoning)
        exact, compatible, differences = 0, 0, []
        for (filename, number, text), left, right in zip(queries, c, python):
            if first_difference(left, right, 0) is None:
                exact += 1
            path = first_difference(left, right, args.tolerance)
            if path is None:
                compatible += 1
            else:
                differences.append({'fixture': filename, 'line': number, 'text': text,
                                    'first_differing_path': path, 'c': left, 'python': right})
        passed &= compatible == len(queries)
        report['modes'][mode] = {'requests': len(queries), 'exact_full_json_matches': exact,
                                'full_json_matches_within_tolerance': compatible, 'differences': differences}
        print('%s: %d/%d exact; %d/%d within %.1g' %
              (mode, exact, len(queries), compatible, len(queries), args.tolerance))
    report['passed'] = passed
    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if passed else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print('parity: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
