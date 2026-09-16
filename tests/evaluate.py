#!/usr/bin/env python3
"""Independent, standard-library-only tool-calling evaluation.

The default heldout set is an engineering holdout: its requests are not examples
used to construct the field, but developers may examine failures. The separate
final_holdout.jsonl was authored at the same time and must be reported separately
once inspected. Neither set is a public benchmark or a statistical estimate of
arbitrary-language performance.

Example:
    python3 tests/evaluate.py --engine ./wolfe --modes neural,field,keyword
    python3 tests/evaluate.py --python-engine 'python3 wolfe.py' --report report.json

No training, feedback, calibration writes or corpus edits are performed here.
"""

import argparse
import collections
import json
import math
from pathlib import Path
import re
import shlex
import statistics
import subprocess
import sys
import time
import unicodedata


TOOLS = {
    "get_weather": {
        "city": ("string", True, None),
        "unit": ("enum", True, ["celsius", "fahrenheit"]),
    },
    "set_timer": {"seconds": ("integer", True, (1, 86400))},
    "cancel_timer": {},
    "play_music": {"query": ("string", True, None)},
    "pause_music": {},
    "create_note": {"text": ("string", True, None)},
}
STATUSES = {"call", "no_call", "ambiguous", "missing_arguments"}


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def load_fixtures(path):
    rows = []
    seen = set()
    with open(path, encoding="utf-8") as src:
        for line_number, line in enumerate(src, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row.get("text"), str) or not isinstance(row.get("calls"), list):
                raise ValueError("invalid fixture at line %d" % line_number)
            if row["text"] in seen:
                raise ValueError("duplicate input at line %d" % line_number)
            seen.add(row["text"])
            expected = {
                "calls": row["calls"],
                "status": "call" if row["calls"] else row.get("allowed_status", ["no_call"])[0],
                "confidence": 0.5,
            }
            issues = schema_issues(expected)
            if issues:
                raise ValueError("invalid fixture at line %d: %s" % (line_number, issues))
            row.setdefault("category", "unspecified")
            row["line"] = line_number
            rows.append(row)
    if not rows:
        raise ValueError("fixture set is empty")
    return rows


def overlap_audit(fixtures, corpus_path):
    """Audit exact normalized phrasing only; do not infer semantic leakage."""
    path = Path(corpus_path)
    if not path.is_file():
        return {"corpus_file": str(path), "status": "unavailable", "overlap_lines": []}

    def normalize(text):
        return " ".join(re.findall(r"\w+", unicodedata.normalize("NFKC", text).casefold()))

    construction = collections.defaultdict(list)
    with path.open(encoding="utf-8") as src:
        for number, line in enumerate(src, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict) and isinstance(row.get("text"), str):
                construction[normalize(row["text"])].append(number)
    overlaps = []
    for row in fixtures:
        locations = construction.get(normalize(row["text"]), [])
        if locations:
            overlaps.append({"fixture_line": row["line"], "corpus_lines": locations, "text": row["text"]})
    return {
        "corpus_file": str(path),
        "status": "audited",
        "normalization": "Unicode NFKC, casefold, Unicode word tokens separated by one space; no semantic matching",
        "unique_construction_phrasings": len(construction),
        "overlap_count": len(overlaps),
        "overlap_lines": [row["fixture_line"] for row in overlaps],
        "overlaps": overlaps,
        "note": "Non-overlap establishes only absence of exact normalized phrasing, not independence from patterns, vocabulary, or developer inspection.",
    }


def schema_issues(obj):
    """Validate this demo's explicit six-tool contract, including unknown keys."""
    issues = []
    if not isinstance(obj, dict):
        return ["response is not an object"]
    if obj.get("status") not in STATUSES:
        issues.append("unknown or missing status")
    confidence = obj.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        issues.append("confidence is not numeric")
    elif not math.isfinite(confidence) or not 0 <= confidence <= 1:
        issues.append("confidence is outside [0, 1]")
    calls = obj.get("calls")
    if not isinstance(calls, list):
        return issues + ["calls is not an array"]
    if len(calls) > 1:
        issues.append("more than one call")
    if bool(calls) != (obj.get("status") == "call"):
        issues.append("status and presence of calls disagree")
    for call in calls:
        if not isinstance(call, dict):
            issues.append("call is not an object")
            continue
        name = call.get("name")
        if not isinstance(name, str) or name not in TOOLS:
            issues.append("unknown tool name")
            continue
        args = call.get("arguments")
        if not isinstance(args, dict):
            issues.append("arguments is not an object")
            continue
        if set(call) - {"name", "arguments"}:
            issues.append("unexpected call fields")
        contract = TOOLS[name]
        if set(args) - set(contract):
            issues.append("unexpected arguments for " + name)
        for key, (kind, required, constraint) in contract.items():
            if key not in args:
                if required:
                    issues.append("missing " + name + "." + key)
                continue
            value = args[key]
            if kind == "string" and (not isinstance(value, str) or not value.strip()):
                issues.append("invalid string " + name + "." + key)
            if kind == "enum" and value not in constraint:
                issues.append("invalid enum " + name + "." + key)
            if kind == "integer" and (
                isinstance(value, bool) or not isinstance(value, int)
                or not constraint[0] <= value <= constraint[1]
            ):
                issues.append("invalid integer " + name + "." + key)
    return issues


def strict_json(line):
    def bad_constant(value):
        raise ValueError("non-JSON number " + value)

    def unique_keys(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError("duplicate JSON key " + key)
            out[key] = value
        return out

    return json.loads(line, parse_constant=bad_constant, object_pairs_hook=unique_keys)


def command_for(command, mode, args):
    command = shlex.split(command) + ["--batch", "--mode", mode]
    if args.tools:
        command += ["--tools", str(Path(args.tools).resolve())]
    if args.examples:
        command += ["--examples", str(Path(args.examples).resolve())]
    if args.reasoning:
        command += ["--reasoning"]
    return command


def invoke(command, payload, cwd, timeout):
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            command, input=payload, text=True, encoding="utf-8", capture_output=True,
            cwd=cwd, timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": str(exc), "elapsed_seconds": time.perf_counter() - start}
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "elapsed_seconds": time.perf_counter() - start,
    }


def call_names(calls):
    if not isinstance(calls, list):
        return None
    if not all(isinstance(item, dict) and isinstance(item.get("name"), str) for item in calls):
        return None
    return [item["name"] for item in calls]


def exact_json(left, right):
    # Python considers True == 1 and 1.0 == 1. Canonical JSON keeps these distinct.
    return json.dumps(left, sort_keys=True, ensure_ascii=False) == json.dumps(
        right, sort_keys=True, ensure_ascii=False
    )


def score(fixtures, responses):
    counts = collections.Counter()
    categories = collections.defaultdict(collections.Counter)
    per_tool = collections.defaultdict(collections.Counter)
    fields = collections.defaultdict(collections.Counter)
    errors = []
    confusion = collections.defaultdict(collections.Counter)
    for row, response in zip(fixtures, responses):
        counts["requests"] += 1
        category = categories[row["category"]]
        category["requests"] += 1
        expected = row["calls"]
        obj = response.get("value")
        actual = obj.get("calls") if isinstance(obj, dict) else None
        status = obj.get("status") if isinstance(obj, dict) else None
        expected_names = call_names(expected)
        actual_names = call_names(actual)
        allowed_status = ["call"] if expected else row.get("allowed_status", ["no_call"])
        parsed = "value" in response
        issues = schema_issues(obj) if parsed else [response.get("error", "missing response")]
        valid = not issues
        tool_correct = actual_names == expected_names
        status_correct = status in allowed_status
        complete = valid and exact_json(actual, expected) and status_correct
        category["tool_correct"] += tool_correct
        category["complete_correct"] += complete
        counts["tool_correct"] += tool_correct
        counts["status_correct"] += status_correct
        counts["complete_correct"] += complete
        counts["valid_responses"] += valid
        counts["json_parse_failures"] += not parsed
        counts["schema_violations"] += not valid
        counts["abstentions"] += actual_names == []
        label = expected_names[0] if expected_names else "<no-call>"
        actual_label = actual_names[0] if actual_names else (
            "<no-call>" if actual_names == [] else "<invalid>"
        )
        confusion[label][actual_label] += 1
        per_tool[label]["requests"] += 1
        per_tool[label]["tool_correct"] += tool_correct
        per_tool[label]["complete_correct"] += complete
        if not expected:
            counts["expected_abstentions"] += 1
            counts["false_calls"] += isinstance(actual, list) and bool(actual)
            counts["correct_abstentions"] += actual_names == []
        else:
            counts["expected_calls"] += 1
            counts["call_tool_correct"] += tool_correct
            counts["call_complete_correct"] += complete
            counts["missed_calls"] += actual_names == []
            expected_call = expected[0]
            actual_args = {}
            if tool_correct and actual and isinstance(actual[0].get("arguments"), dict):
                actual_args = actual[0]["arguments"]
            for key, value in expected_call["arguments"].items():
                field = expected_call["name"] + "." + key
                correct = key in actual_args and exact_json(actual_args[key], value)
                fields[field]["expected"] += 1
                fields[field]["correct"] += correct
                counts["argument_fields"] += 1
                counts["correct_argument_fields"] += correct
                if tool_correct:
                    counts["argument_fields_given_correct_tool"] += 1
                    counts["correct_argument_fields_given_correct_tool"] += correct
        if not complete:
            errors.append({
                "line": row["line"], "category": row["category"], "text": row["text"],
                "expected": {"calls": expected, "allowed_status": allowed_status},
                "actual": obj, "issues": issues,
                **({"raw": response["raw"]} if "raw" in response and not parsed else {}),
            })

    def table(items):
        return {
            key: {
                **dict(value),
                "tool_accuracy": ratio(value["tool_correct"], value["requests"]),
                "complete_call_accuracy": ratio(value["complete_correct"], value["requests"]),
            }
            for key, value in sorted(items.items())
        }

    return {
        "counts": dict(counts),
        "metrics": {
            "tool_accuracy_all_requests": ratio(counts["tool_correct"], counts["requests"]),
            "tool_accuracy_expected_calls": ratio(counts["call_tool_correct"], counts["expected_calls"]),
            "complete_call_accuracy": ratio(counts["complete_correct"], counts["requests"]),
            "complete_call_accuracy_expected_calls": ratio(counts["call_complete_correct"], counts["expected_calls"]),
            "argument_field_accuracy": ratio(counts["correct_argument_fields"], counts["argument_fields"]),
            "argument_field_accuracy_given_correct_tool": ratio(
                counts["correct_argument_fields_given_correct_tool"], counts["argument_fields_given_correct_tool"]
            ),
            "status_accuracy": ratio(counts["status_correct"], counts["requests"]),
            "false_call_rate": ratio(counts["false_calls"], counts["expected_abstentions"]),
            "abstention_rate": ratio(counts["abstentions"], counts["requests"]),
            "correct_abstention_rate": ratio(counts["correct_abstentions"], counts["expected_abstentions"]),
            "missed_call_rate": ratio(counts["missed_calls"], counts["expected_calls"]),
            "malformed_or_schema_violation_rate": ratio(counts["schema_violations"], counts["requests"]),
            "json_parse_failure_rate": ratio(counts["json_parse_failures"], counts["requests"]),
        },
        "by_category": table(categories),
        "by_tool": table(per_tool),
        "by_argument": {
            key: {**dict(value), "accuracy": ratio(value["correct"], value["expected"])}
            for key, value in sorted(fields.items())
        },
        "tool_confusion": {key: dict(value) for key, value in sorted(confusion.items())},
        "errors": errors,
    }


def run_engine(command, mode, args, fixtures):
    argv = command_for(command, mode, args)
    payload = "".join(json.dumps({"text": row["text"]}, ensure_ascii=False) + "\n" for row in fixtures)
    result = invoke(argv, payload, args.cwd, args.timeout)
    responses = []
    lines = result.get("stdout", "").splitlines()
    for index in range(len(fixtures)):
        if index >= len(lines):
            responses.append({"error": "no output line", "raw": None})
            continue
        line = lines[index]
        try:
            responses.append({"value": strict_json(line), "raw": line})
        except (ValueError, TypeError) as exc:
            responses.append({"error": str(exc), "raw": line})
    report = score(fixtures, responses)
    nonoverlap = [(row, response) for row, response in zip(fixtures, responses)
                  if row["line"] not in args.overlap_lines]
    if args.overlap_audited:
        separate = score([item[0] for item in nonoverlap], [item[1] for item in nonoverlap])
        report["excluding_exact_normalized_corpus_overlap"] = {
            "counts": separate["counts"], "metrics": separate["metrics"]
        }
    report["command"] = argv
    report["process"] = {
        key: value for key, value in result.items() if key != "stdout"
    }
    report["process"]["output_lines"] = len(lines)
    report["process"]["expected_output_lines"] = len(fixtures)
    if len(lines) > len(fixtures):
        report["process"]["unexpected_extra_lines"] = lines[len(fixtures):]
    report["process"]["protocol_ok"] = (
        result.get("returncode") == 0 and len(lines) == len(fixtures)
    )
    cold = [invoke(argv, "", args.cwd, args.timeout) for _ in range(args.startup_runs)]
    times = [item["elapsed_seconds"] for item in cold if item.get("returncode") == 0]
    cold_median = statistics.median(times) if times else None
    elapsed = result["elapsed_seconds"]
    report["timing"] = {
        "batch_total_seconds": elapsed,
        "batch_mean_ms_including_startup": elapsed * 1000 / len(fixtures),
        "cold_empty_batch_seconds": times,
        "cold_empty_batch_median_seconds": cold_median,
        "startup_adjusted_batch_mean_ms_estimate": (
            max(0, elapsed - cold_median) * 1000 / len(fixtures)
            if cold_median is not None else None
        ),
        "note": "Wall-clock subprocess timings include JSON I/O. Empty-batch startup includes definition loading only if the engine loads eagerly. Subtracting a separate process is an estimate, not a latency distribution. OS caches are not flushed.",
    }
    return report, responses


def parity(fixtures, native, reference, tolerance):
    differences = []
    structure_equal = confidence_equal = 0
    confidence_comparable = 0
    for row, left, right in zip(fixtures, native, reference):
        a, b = left.get("value"), right.get("value")
        structured = (
            isinstance(a, dict) and isinstance(b, dict)
            and exact_json(a.get("calls"), b.get("calls"))
            and a.get("status") == b.get("status")
        )
        structure_equal += structured
        confidence_ok = None
        if isinstance(a, dict) and isinstance(b, dict):
            ca, cb = a.get("confidence"), b.get("confidence")
            if all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in (ca, cb)):
                confidence_comparable += 1
                confidence_ok = abs(ca - cb) <= tolerance
                confidence_equal += confidence_ok
        if not structured or confidence_ok is False:
            differences.append({"line": row["line"], "text": row["text"], "native": a, "python": b})
    return {
        "requests": len(fixtures),
        "matching_calls_and_status": structure_equal,
        "calls_and_status_match_rate": ratio(structure_equal, len(fixtures)),
        "confidence_tolerance": tolerance,
        "comparable_confidences": confidence_comparable,
        "confidences_within_tolerance": confidence_equal,
        "differences": differences,
    }


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--engine", default="./wolfe", help="shell-like command, executed without a shell")
    parser.add_argument("--python-engine", help="optional reference command, e.g. 'python3 wolfe.py'")
    parser.add_argument("--cwd", default=str(root), help="engine working directory")
    parser.add_argument("--fixtures", default=str(root / "tests" / "heldout.jsonl"))
    parser.add_argument("--modes", default="neural,field,keyword")
    parser.add_argument("--tools")
    parser.add_argument("--examples")
    parser.add_argument("--audit-examples", help="construction JSONL for normalized exact-overlap audit; defaults to --examples or examples.jsonl in --cwd")
    parser.add_argument("--reasoning", action="store_true")
    parser.add_argument("--startup-runs", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--confidence-tolerance", type=float, default=1e-5)
    parser.add_argument("--report", help="write JSON here instead of stdout")
    parser.add_argument("--require-perfect", action="store_true", help="exit 1 if any full-call error; off by default")
    args = parser.parse_args()
    modes = [mode.strip() for mode in args.modes.split(",") if mode.strip()]
    if not modes or any(mode not in ("neural", "field", "keyword") for mode in modes):
        parser.error("--modes must contain neural, field, and/or keyword")
    if args.startup_runs < 0:
        parser.error("--startup-runs must be nonnegative")
    fixtures = load_fixtures(args.fixtures)
    audit = overlap_audit(fixtures, args.audit_examples or args.examples or Path(args.cwd) / "examples.jsonl")
    args.overlap_lines = set(audit["overlap_lines"])
    args.overlap_audited = audit["status"] == "audited"
    report = {
        "fixture_file": str(Path(args.fixtures).resolve()),
        "fixture_count": len(fixtures),
        "fixture_scope": "independently authored bounded-domain requests; not a public benchmark",
        "construction_overlap_audit": audit,
        "metric_notes": {
            "tool_accuracy": "Exact ordered tool names, with [] counted as an abstention decision; ignores arguments and status.",
            "complete_call_accuracy": "Exact tool and all arguments, allowed status, and schema-valid response; argument extra keys fail.",
            "argument_field_accuracy": "Each expected argument field counts once. Wrong tool or absent value is wrong; types and string contents must match.",
            "false_call_rate": "Calls emitted on fixtures expecting no call divided by such fixtures, including missing-argument and multi-action requests.",
            "confidence": "Scores are not assumed calibrated probabilities. No claim about confidence calibration follows from output range validation.",
        },
        "engines": {},
    }
    process_failure = accuracy_failure = False
    for mode in modes:
        native_report, native_responses = run_engine(args.engine, mode, args, fixtures)
        report["engines"][mode] = {"c": native_report}
        process_failure |= not native_report["process"]["protocol_ok"]
        accuracy_failure |= bool(native_report["errors"])
        if args.python_engine:
            py_report, py_responses = run_engine(args.python_engine, mode, args, fixtures)
            report["engines"][mode]["python"] = py_report
            report["engines"][mode]["parity"] = parity(
                fixtures, native_responses, py_responses, args.confidence_tolerance
            )
            process_failure |= not py_report["process"]["protocol_ok"]
            accuracy_failure |= bool(py_report["errors"])
    output = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.report:
        Path(args.report).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 2 if process_failure else (1 if args.require_perfect and accuracy_failure else 0)


if __name__ == "__main__":
    raise SystemExit(main())
