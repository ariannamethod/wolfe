#!/usr/bin/env python3
"""Verify persisted state interchange using immutable C/Python source snapshots.

Both runtimes create, consume and extend the same version-2 memory file. The
fixture is unrelated to the six-tool evaluation corpus; no blind cases are read.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def equivalent(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(equivalent(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(equivalent(a, b) for a, b in zip(left, right))
    if type(left) in (int, float) and type(right) in (int, float):
        return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-6)
    return type(left) is type(right) and left == right


class InteropCheck:
    def __init__(self, directory, report, cc):
        self.directory, self.report = Path(directory), report
        self.checks = report['assertions']
        source_bytes = {name: (ROOT / name).read_bytes() for name in ('wolfe.c', 'wolfe.py')}
        report['source_sha256'] = {name: digest(data) for name, data in source_bytes.items()}
        for name, data in source_bytes.items():
            (self.directory / name).write_bytes(data)
        executable = self.directory / 'wolfe'
        command = shlex.split(cc) + ['-O2', '-std=c99', '-Wall', '-Wextra', '-Wpedantic',
                                    '-Werror', str(self.directory / 'wolfe.c'), '-lm',
                                    '-o', str(executable)]
        built = subprocess.run(command, capture_output=True, text=True, timeout=60)
        self.check('source_snapshot_compiles', built.returncode == 0,
                   error=built.stderr if built.returncode else None)
        report['binary_sha256'] = digest(executable.read_bytes())
        report['compiler_command'] = shlex.split(cc) + command[len(shlex.split(cc)):]
        report['compiler_command'] = [item.replace(str(self.directory), '<temporary>')
                                      for item in report['compiler_command']]
        self.engines = {'c': [str(executable)],
                        'python': [sys.executable, str(self.directory / 'wolfe.py')]}
        self.tools = self.directory / 'tools.json'
        self.examples = self.directory / 'examples.jsonl'
        definitions = {'tools': [
            {'name': name, 'description': 'A user-defined action.',
             'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}}
            for name in ('amber', 'violet')
        ]}
        definitions['tools'].append({
            'name': 'deliver_parcel', 'description': 'Deliver a parcel to a destination.',
            'parameters': {'type': 'object', 'properties': {'destination': {'type': 'string'}},
                           'required': ['destination'], 'additionalProperties': False}})
        rows = [
            {'text': 'sip cobalt', 'tool': 'amber', 'arguments': {}},
            {'text': 'fold copper', 'tool': 'violet', 'arguments': {}},
            {'text': 'deliver the parcel to {destination}', 'tool': 'deliver_parcel',
             'arguments': {'destination': '{destination}'}},
            {'text': 'send parcel to {destination}', 'tool': 'deliver_parcel',
             'arguments': {'destination': '{destination}'}},
            {'text': 'hello there', 'tool': None, 'arguments': {}},
        ]
        self.tools.write_text(json.dumps(definitions), encoding='utf-8')
        self.examples.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
        report['fixture_sha256'] = {path.name: digest(path.read_bytes())
                                    for path in (self.tools, self.examples)}

    def check(self, name, passed, **details):
        entry = {'name': name, 'passed': bool(passed)}
        entry.update({key: value for key, value in details.items() if value is not None})
        self.checks.append(entry)
        if not passed:
            raise AssertionError(name + ': ' + json.dumps(details, ensure_ascii=False))

    def invoke(self, engine, state, options, label):
        command = self.engines[engine] + ['--tools', str(self.tools), '--examples',
                                          str(self.examples), '--state', str(state)]
        process = subprocess.run(command + options, cwd=self.directory, capture_output=True,
                                 text=True, encoding='utf-8', timeout=30)
        self.check(label + '.exit', process.returncode == 0,
                   error=process.stderr if process.returncode else None)
        return json.loads(process.stdout)

    def pair(self, state, text, expected_calls, label):
        before = state.read_bytes() if state.exists() else None
        left = self.invoke('c', state, ['--reasoning', text], label + '.c')
        right = self.invoke('python', state, ['--reasoning', text], label + '.python')
        self.check(label + '.responses_match', equivalent(left, right))
        self.check(label + '.expected_call', left['calls'] == expected_calls,
                   expected=expected_calls)
        if not expected_calls:
            self.check(label + '.no_call_status', left['status'] == 'no_call')
        after = state.read_bytes() if state.exists() else None
        self.check(label + '.inference_does_not_write', before == after)

    def correct(self, engine, state, record, count, label):
        path = self.directory / 'correction.json'
        path.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
        result = self.invoke(engine, state, ['--correct', str(path)], label)
        self.check(label + '.receipt', result == {'status': 'corrected', 'corrections': count})
        saved = json.loads(state.read_text(encoding='utf-8'))
        self.check(label + '.version_and_record', saved['version'] == 2
                   and len(saved['corrections']) == count and saved['corrections'][-1] == record)

    def direction(self, writer, reader):
        label = writer + '_to_' + reader
        state = self.directory / (label + '.json')
        self.pair(state, 'sip cobalt', [{'name': 'amber', 'arguments': {}}], label + '.base')
        self.invoke(writer, state, ['--feedback', 'accepted', 'sip cobalt'], label + '.initial_feedback')
        saved = json.loads(state.read_text(encoding='utf-8'))
        self.check(label + '.feedback_version_two', saved['version'] == 2 and saved['corrections'] == [])
        self.pair(state, 'sip cobalt', [{'name': 'amber', 'arguments': {}}], label + '.counter_reload')

        self.correct(writer, state, {'text': 'sip cobalt', 'tool': 'violet', 'arguments': {}},
                     1, label + '.call_correction')
        self.pair(state, 'sip cobalt', [{'name': 'violet', 'arguments': {}}], label + '.call_reload')
        self.invoke(reader, state, ['--feedback', 'rejected', 'sip cobalt'], label + '.reverse_feedback')
        saved = json.loads(state.read_text(encoding='utf-8'))
        self.check(label + '.counters_and_correction_survive_reverse_write',
                   saved['tools']['amber'] == {'accepted': 1, 'rejected': 0}
                   and saved['tools']['violet'] == {'accepted': 0, 'rejected': 1}
                   and saved['corrections'] == [{'text': 'sip cobalt', 'tool': 'violet', 'arguments': {}}])
        self.pair(state, 'sip cobalt', [{'name': 'violet', 'arguments': {}}], label + '.reverse_counter_reload')

        self.correct(writer, state, {'text': 'fold copper', 'tool': None, 'arguments': {}},
                     2, label + '.null_correction')
        self.pair(state, 'fold copper', [], label + '.null_reload')

        query = 'deliver the parcel to my usual place {Ataeff}'
        destination = 'Montréal {家} / שלום — \\ "Ataeff"\n{literal}'
        constant = {'text': query, 'tool': 'deliver_parcel', 'arguments': {'destination': destination}}
        self.correct(reader, state, constant, 3, label + '.reverse_unicode_constant')
        expected = [{'name': 'deliver_parcel', 'arguments': {'destination': destination}}]
        self.pair(state, query, expected, label + '.unicode_braces_reload')
        self.invoke(writer, state, ['--feedback', 'accepted', query], label + '.constant_feedback')
        saved = json.loads(state.read_text(encoding='utf-8'))
        self.check(label + '.final_counters_and_records', saved['tools'] == {
            'amber': {'accepted': 1, 'rejected': 0},
            'violet': {'accepted': 0, 'rejected': 1},
            'deliver_parcel': {'accepted': 1, 'rejected': 0}}
            and len(saved['corrections']) == 3 and saved['corrections'][-1] == constant)
        self.pair(state, query, expected, label + '.final_reload')
        self.pair(state, 'fold copper', [], label + '.earlier_null_still_loaded')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--cc', default=os.environ.get('CC', 'cc'))
    args = parser.parse_args()
    report = {'check': 'version_2_state_interchange', 'status': 'running',
              'python': platform.python_version(), 'platform': platform.platform(),
              'score_absolute_tolerance': 1e-6, 'assertions': []}
    try:
        with tempfile.TemporaryDirectory(prefix='wolfe-state-interop-') as directory:
            suite = InteropCheck(directory, report, args.cc)
            suite.direction('c', 'python')
            suite.direction('python', 'c')
        report['status'] = 'passed'
    except (AssertionError, OSError, ValueError, subprocess.SubprocessError) as error:
        report['status'] = 'failed'
        report['error'] = str(error)
    report['passed_assertions'] = sum(item['passed'] for item in report['assertions'])
    report['total_assertions'] = len(report['assertions'])
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    if args.report:
        args.report.write_text(rendered, encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('status', 'passed_assertions', 'total_assertions')}))
    if report.get('error'):
        print(report['error'], file=sys.stderr)
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
