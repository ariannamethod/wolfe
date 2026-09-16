#!/usr/bin/env python3
"""One controlled role-feature ablation on the visible V2 engineering set.

Compile two temporary copies of the current C source. In the second copy only,
replace prefix_agreement's body with return 1. This disables the corpus prefix
compatibility factor while preserving argument extraction, field construction,
neural recurrence, thresholds and declaration files. Evaluate each copy once.
No runtime option, corpus mutation, feedback or blind evaluation is introduced.

    python3 tests/ablate_role.py --report docs/role_ablation_v2.json
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SIGNATURE = "static double prefix_agreement("
REPLACEMENT = "{\n    (void) m; (void) q; (void) example;\n    return 1.;\n}"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def body_bounds(source):
    """Locate the complete C function body, ignoring quoted/commented braces."""
    if source.count(SIGNATURE) != 1:
        raise ValueError("expected exactly one prefix_agreement definition")
    start = source.index("{", source.index(SIGNATURE))
    depth = 0
    state = "code"
    i = start
    while i < len(source):
        char = source[i]
        following = source[i + 1] if i + 1 < len(source) else ""
        if state in ('"', "'"):
            if char == "\\":
                i += 2
                continue
            if char == state:
                state = "code"
        elif state == "line_comment":
            if char == "\n":
                state = "code"
        elif state == "block_comment":
            if char == "*" and following == "/":
                state = "code"
                i += 2
                continue
        elif char == "/" and following in ("/", "*"):
            state = "line_comment" if following == "/" else "block_comment"
            i += 2
            continue
        elif char in ('"', "'"):
            state = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    raise ValueError("unterminated prefix_agreement body")


def checked(command):
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8", timeout=120)
    if process.returncode:
        raise RuntimeError("command failed: %s\n%s\n%s" %
                           (shlex.join(command), process.stdout, process.stderr))
    return process


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cc", default=os.environ.get("CC", "cc"))
    parser.add_argument("--flags", default="-O2 -std=c99")
    parser.add_argument("--report", default=str(ROOT / "docs/role_ablation_v2.json"))
    args = parser.parse_args()
    source_bytes = (ROOT / "wolfe.c").read_bytes()
    source = source_bytes.decode("utf-8")
    start, finish = body_bounds(source)
    ablated = source[:start] + REPLACEMENT + source[finish:]
    compiler = shlex.split(args.cc)
    flags = shlex.split(args.flags)
    if not compiler:
        parser.error("--cc must name a compiler")
    fixture = ROOT / "tests/v2_engineering.jsonl"
    report = {
        "method": "Compile two temporary copies of one source snapshot; replace only "
                  "prefix_agreement's body in the ablated copy; evaluate each once "
                  "in neural mode on the same visible V2 engineering requests.",
        "scope": "Developer-visible diagnostic ablation; no significance or "
                 "unseen-data accuracy claim follows from this small set.",
        "source_file": "wolfe.c",
        "source_sha256": digest(source_bytes),
        "ablated_source_sha256": digest(ablated.encode("utf-8")),
        "patch": {"function": "prefix_agreement", "replacement_body": REPLACEMENT,
                  "original_body_sha256": digest(source[start:finish].encode("utf-8")),
                  "location": "Function body found by brace depth with C strings, "
                              "character literals and comments excluded."},
        "compiler": {"command": compiler, "flags": flags, "libraries": ["-lm"],
                     "version": checked(compiler + ["--version"]).stdout.splitlines()[0]},
        "inputs": {
            str(path.relative_to(ROOT)): {"sha256": digest(path.read_bytes()),
                                           "bytes": path.stat().st_size}
            for path in (fixture, ROOT / "tools.json", ROOT / "examples.jsonl")
        },
        "variants": {},
    }
    with tempfile.TemporaryDirectory(prefix="wolfe-role-ablation-") as temporary:
        directory = Path(temporary)
        for label, text in (("full_v2", source), ("without_prefix_compatibility", ablated)):
            c_file = directory / (label + ".c")
            engine = directory / label
            evaluation_file = directory / (label + ".json")
            c_file.write_text(text, encoding="utf-8")
            compile_command = compiler + flags + [str(c_file), "-lm", "-o", str(engine)]
            checked(compile_command)
            evaluate_command = [sys.executable, str(ROOT / "tests/evaluate.py"),
                                "--engine", shlex.join([str(engine)]),
                                "--fixtures", str(fixture), "--modes", "neural",
                                "--startup-runs", "0", "--report", str(evaluation_file)]
            checked(evaluate_command)
            evaluation = json.loads(evaluation_file.read_text(encoding="utf-8"))
            result = evaluation["engines"]["neural"]["c"]
            report["variants"][label] = {
                "compile_command": [item.replace(temporary, "<temporary>") for item in compile_command],
                "evaluation_command": [item.replace(temporary, "<temporary>") for item in evaluate_command],
                "counts": result["counts"], "metrics": result["metrics"],
                "errors": result["errors"],
                "protocol_ok": result["process"]["protocol_ok"],
                "construction_overlap_audit": evaluation["construction_overlap_audit"],
            }
    full = report["variants"]["full_v2"]["counts"]
    control = report["variants"]["without_prefix_compatibility"]["counts"]
    report["differences_full_minus_control"] = {
        key: full[key] - control[key]
        for key in ("complete_correct", "false_calls", "call_complete_correct")
    }
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Full V2: %d/%d complete, %d/%d false calls; without role: %d/%d complete, %d/%d false calls." %
          (full["complete_correct"], full["requests"], full["false_calls"], full["expected_abstentions"],
           control["complete_correct"], control["requests"], control["false_calls"], control["expected_abstentions"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
