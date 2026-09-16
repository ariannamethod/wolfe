#!/usr/bin/env python3
"""Measure explicit correction files and CLI rebuild cost in a temporary directory."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    report = {
        'c_sha256': hashlib.sha256((ROOT / 'wolfe.c').read_bytes()).hexdigest(),
        'method': '32 sequential explicit CLI corrections; each duration includes process startup, initial loading, candidate-field rebuild and atomic state replacement. Small illustrative records, not maximum-size records or a warmed API latency benchmark.',
        'records': [],
    }
    with tempfile.TemporaryDirectory() as directory:
        state = Path(directory) / 'state.json'
        correction = Path(directory) / 'correction.json'
        base = subprocess.run([str(ROOT / 'wolfe'), '--stats', 'play Portishead'],
                              cwd=ROOT, text=True, capture_output=True, check=True)
        report['base_model_stats'] = json.loads(base.stderr)
        for index in range(32):
            record = {'text': 'remember my phrase %d' % index, 'tool': 'create_note',
                      'arguments': {'text': 'Saved item %d' % index}}
            correction.write_text(json.dumps(record) + '\n', encoding='utf-8')
            began = time.perf_counter()
            p = subprocess.run([str(ROOT / 'wolfe'), '--state', str(state),
                                '--correct', str(correction)], cwd=ROOT, text=True,
                               capture_output=True, check=True)
            elapsed = (time.perf_counter() - began) * 1000
            receipt = json.loads(p.stdout)
            assert receipt == {'status': 'corrected', 'corrections': index + 1}
            report['records'].append({'record': record, 'count': index + 1,
                                      'state_bytes': state.stat().st_size,
                                      'cli_correction_ms': elapsed})
        loaded = subprocess.run([str(ROOT / 'wolfe'), '--state', str(state),
                                 '--stats', 'remember my phrase 31'], cwd=ROOT,
                                text=True, capture_output=True, check=True)
        report['model_stats_with_32_corrections'] = json.loads(loaded.stderr)
        report['state_bytes_one_record'] = report['records'][0]['state_bytes']
        report['state_bytes_32_records'] = state.stat().st_size
        report['cli_correction_ms_median'] = statistics.median(
            row['cli_correction_ms'] for row in report['records'])
    Path(args.report).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
