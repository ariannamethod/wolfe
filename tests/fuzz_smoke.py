#!/usr/bin/env python3
"""Deterministic input robustness probe; no claim of exhaustive fuzz coverage."""
import argparse
import json
from pathlib import Path
import random
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', default=str(ROOT / 'wolfe'))
    parser.add_argument('--count', type=int, default=500)
    args = parser.parse_args()
    rng = random.Random(271828)
    alphabet = 'abcXYZ 0123456789{}[]<>:;,.!?\"\\\n\t-' + 'éא树🐺'
    inputs = ['', ' ', '\\', '"', '{}', '{query}', 'NaN', '1e9999', '-99999999999999',
              'play "pause music"', 'create a note: {"x":[1,2,3]}',
              'set a timer for 99999999999999999999999999999 hours']
    inputs.extend(''.join(rng.choice(alphabet) for _ in range(rng.randrange(0, 180)))
                  for _ in range(args.count))
    batch = ''.join(json.dumps({'text': s}, ensure_ascii=False) + '\n' for s in inputs)
    proc = subprocess.run(shlex.split(args.engine) + ['--batch'], input=batch,
                          capture_output=True, text=True, cwd=ROOT, timeout=120)
    if proc.returncode not in (0, 1):
        raise SystemExit(f'engine exited {proc.returncode}: {proc.stderr[-3000:]}')
    if 'AddressSanitizer' in proc.stderr or 'runtime error:' in proc.stderr:
        raise SystemExit(proc.stderr)
    rows = proc.stdout.splitlines()
    if len(rows) != len(inputs):
        raise SystemExit(f'{len(inputs)} requests produced {len(rows)} response lines')
    schema = {t['name']: t['parameters'] for t in json.loads((ROOT / 'tools.json').read_text())['tools']}
    calls = 0
    bounded_rejections = 0
    for row in rows:
        obj = json.loads(row)
        if obj.get('status') == 'error':
            if obj.get('calls') != [] or obj.get('error') not in {
                    'token exceeds 95 bytes', 'text exceeds 96 tokens'}:
                raise SystemExit(f'unexpected error: {obj}')
            bounded_rejections += 1
            continue
        for call in obj.get('calls', []):
            calls += 1
            if call['name'] not in schema:
                raise SystemExit(f'undeclared tool: {call}')
            properties = schema[call['name']]['properties']
            if set(call['arguments']) - set(properties):
                raise SystemExit(f'undeclared argument: {call}')
            if set(schema[call['name']].get('required', [])) - set(call['arguments']):
                raise SystemExit(f'missing required argument: {call}')
            for name, value in call['arguments'].items():
                spec = properties[name]
                if 'minimum' in spec and value < spec['minimum']:
                    raise SystemExit(f'below minimum: {call}')
                if 'maximum' in spec and value > spec['maximum']:
                    raise SystemExit(f'above maximum: {call}')
                if 'enum' in spec and value not in spec['enum']:
                    raise SystemExit(f'outside enum: {call}')
    if proc.returncode != int(bounded_rejections > 0):
        raise SystemExit('exit code does not match reported bounded input errors')
    print(json.dumps({'requests': len(inputs), 'valid_responses': len(rows), 'calls': calls,
                      'bounded_input_rejections': bounded_rejections,
                      'seed': 271828, 'scope': 'input robustness, not semantic accuracy'}))


if __name__ == '__main__':
    main()
