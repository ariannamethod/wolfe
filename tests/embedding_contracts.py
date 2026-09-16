#!/usr/bin/env python3
"""Compile a real C host and test the public API without invoking the CLI."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class EmbeddingContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory()
        cls.host = Path(cls.build.name) / 'host'
        command = shlex.split(os.environ.get('CC', 'cc')) + [
            '-O2', '-std=c99', '-Wall', '-Wextra', '-Wpedantic', '-Werror',
            str(ROOT / 'tests/embedding_host.c'), '-lm', '-o', str(cls.host)]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60)
        if result.returncode:
            raise AssertionError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.build.cleanup()

    def run_host(self, mode):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([str(self.host), mode, directory], cwd=ROOT,
                                    text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '', 'API must not print responses')
            if mode not in ('correction', 'literal-braces'):
                self.assertFalse((Path(directory) / 'memory.json').exists())

    def test_model_reused_without_response_state_leak(self): self.run_host('reuse')
    def test_two_independent_models(self): self.run_host('two-models')
    def test_exact_capacity_counting_and_empty_short_output(self): self.run_host('capacity')
    def test_invalid_calls_do_not_poison_context(self): self.run_host('invalid')
    def test_explicit_correction_rebuild_and_invalid_rollback(self): self.run_host('correction')
    def test_failed_persistence_preserves_loaded_model(self): self.run_host('write-failure')
    def test_changed_sources_reject_correction_preserving_model(self): self.run_host('stale-source')
    def test_braces_in_corrections_stay_literal(self): self.run_host('literal-braces')

if __name__ == '__main__':
    unittest.main(verbosity=2)
