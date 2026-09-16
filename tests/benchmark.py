#!/usr/bin/env python3
"""Bounded standard-library benchmark for WOLFE's batch CLI.

Seven fresh processes measure empty-input startup. Loaded throughput first sends
one warm-up request, waits for its answer, then times an already-loaded process
answering a fixed cyclic batch. All JSON I/O remains inside the timed interval.
If the CLI does not flush replies interactively, report a separately labelled
startup-subtracted batch estimate. No holdout fixtures are read.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import queue
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time


REQUESTS = [
    "What is the weather in Kyoto?",
    "Set a timer for 90 seconds.",
    "Cancel the timer.",
    'Play "Teardrop".',
    "Pause the music.",
    "Create a note: bring the blue folder.",
]


def summary(samples):
    return {
        "count": len(samples),
        "minimum": min(samples) if samples else None,
        "median": statistics.median(samples) if samples else None,
        "maximum": max(samples) if samples else None,
        "mean": statistics.mean(samples) if samples else None,
        "p95_nearest_rank": sorted(samples)[max(0, math.ceil(0.95 * len(samples)) - 1)] if samples else None,
        "samples": samples,
    }


class Budget:
    def __init__(self, seconds):
        self.deadline = time.perf_counter() + seconds

    def remaining(self, cap=None):
        left = self.deadline - time.perf_counter()
        if left <= 0:
            raise TimeoutError("benchmark time budget exhausted")
        return min(left, cap) if cap else left


def invoke(command, cwd, payload, budget, cap=5):
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            command, cwd=cwd, input=payload, encoding="utf-8", text=True,
            capture_output=True, check=False, timeout=budget.remaining(cap),
        )
        return {
            "elapsed_seconds": time.perf_counter() - start,
            "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr,
        }
    except (OSError, subprocess.TimeoutExpired, TimeoutError) as exc:
        return {"error": str(exc), "elapsed_seconds": time.perf_counter() - start}


def json_lines(payload):
    lines = payload.splitlines()
    try:
        values = [json.loads(line) for line in lines]
    except ValueError:
        return {"lines": len(lines), "all_json_objects": False}
    return {"lines": len(lines), "all_json_objects": all(isinstance(value, dict) for value in values)}


def target_memory(pid):
    """Read the executed engine's live mm counters, not launcher rusage."""
    if not sys.platform.startswith("linux"):
        return None
    try:
        status = Path("/proc/%d/status" % pid).read_text()
        counters = {}
        for line in status.splitlines():
            key, _, value = line.partition(":")
            if key in ("VmHWM", "VmRSS"):
                number, unit = value.strip().split()
                if unit != "kB":
                    return None
                counters[key] = int(number) * 1024
        if "VmHWM" not in counters or "VmRSS" not in counters:
            return None
        return {
            "peak_rss_bytes": counters["VmHWM"],
            "resident_bytes_at_sample": counters["VmRSS"],
            "method": "Linux /proc/<engine_pid>/status VmHWM and VmRSS after timed requests, before stdin closes; live post-exec engine memory map",
        }
    except (OSError, ValueError):
        return None


def streamed_loaded_batch(command, cwd, payload, n, latency_count, budget):
    """Use background pipe readers to support bounded request/reply on POSIX."""
    proc = None
    output = queue.Queue()
    diagnostics = []
    start = time.perf_counter()

    def read_stdout(pipe):
        try:
            for line in pipe:
                output.put(line)
        finally:
            output.put(None)

    def read_stderr(pipe):
        # Drain the pipe even after this small diagnostic buffer is full.
        for line in pipe:
            if len(diagnostics) < 20:
                diagnostics.append(line)

    try:
        budget.remaining()
        proc = subprocess.Popen(
            command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1,
        )
        threading.Thread(target=read_stdout, args=(proc.stdout,), daemon=True).start()
        threading.Thread(target=read_stderr, args=(proc.stderr,), daemon=True).start()
        proc.stdin.write(json.dumps({"text": REQUESTS[0]}) + "\n")
        proc.stdin.flush()
        first = output.get(timeout=budget.remaining(3))
        if first is None:
            raise RuntimeError("engine exited before warm-up response")
        if not isinstance(json.loads(first), dict):
            raise RuntimeError("warm-up response is not a JSON object")
        warmup_seconds = time.perf_counter() - start
        latencies = []
        for index in range(latency_count):
            request = json.dumps({"text": REQUESTS[index % len(REQUESTS)]}) + "\n"
            latency_start = time.perf_counter()
            proc.stdin.write(request)
            proc.stdin.flush()
            reply = output.get(timeout=budget.remaining(5))
            latency_seconds = time.perf_counter() - latency_start
            if reply is None or not isinstance(json.loads(reply), dict):
                raise RuntimeError("invalid response during warmed request/reply sampling")
            latencies.append(latency_seconds * 1000)
        batch_start = time.perf_counter()
        proc.stdin.write(payload)
        proc.stdin.flush()
        replies = []
        for _ in range(n):
            line = output.get(timeout=budget.remaining(5))
            if line is None:
                raise RuntimeError("engine exited before all batch responses")
            replies.append(line)
        elapsed = time.perf_counter() - batch_start
        # Keep stdin open so the engine remains alive waiting for its next
        # request. Sampling its post-exec mm avoids launcher pre-exec RSS peaks.
        memory = target_memory(proc.pid)
        proc.stdin.close()
        proc.wait(timeout=budget.remaining(2))
        # Ensure no extra output is silently ignored.
        trailing = []
        while True:
            line = output.get(timeout=budget.remaining(1))
            if line is None:
                break
            trailing.append(line)
        output_check = json_lines("".join(replies))
        return {
            "method": "loaded_process_after_one_response",
            "warmup_including_startup_seconds": warmup_seconds,
            "warmed_individual_request_ms": summary(latencies),
            "batch_seconds": elapsed,
            "request_count": n,
            "amortized_ms_per_request": elapsed * 1000 / n,
            "requests_per_second": n / elapsed,
            "returncode": proc.returncode,
            "output_check": output_check,
            "extra_output_lines": len(trailing),
            "protocol_ok": proc.returncode == 0 and output_check["all_json_objects"] and not trailing,
            **({"target_memory": memory} if memory is not None else {}),
            **({"stderr": "".join(diagnostics)} if diagnostics else {}),
        }
    except (OSError, ValueError, RuntimeError, queue.Empty, TimeoutError, subprocess.TimeoutExpired) as exc:
        return {
            "method": "loaded_process_after_one_response",
            "error": str(exc) or "timed out waiting for a flushed response",
            "elapsed_seconds": time.perf_counter() - start,
            **({"stderr": "".join(diagnostics)} if diagnostics else {}),
        }
    finally:
        if proc is not None:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                if pipe is not None and not pipe.closed:
                    pipe.close()


def rss_helper(spec):
    """A new helper owns exactly one child: ru_maxrss cannot contain older runs."""
    import resource
    proc = subprocess.run(
        spec["command"], cwd=spec["cwd"], input=spec["payload"],
        encoding="utf-8", text=True, capture_output=True, check=False,
    )
    native = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    rss_bytes = int(native) if sys.platform == "darwin" else int(native * 1024)
    print(json.dumps({
        "peak_rss_bytes": rss_bytes,
        "returncode": proc.returncode,
        "output_check": json_lines(proc.stdout),
        "method": "resource.getrusage(RUSAGE_CHILDREN) in a fresh helper with exactly one child",
        "limitation": "Child rusage can retain a launcher pre-exec high-water mark; this fallback may overstate the executed engine's own RSS. It is not a model-only memory measurement.",
        "native_ru_maxrss": native,
        "native_unit": "bytes" if sys.platform == "darwin" else "KiB",
    }))
    return 0


def native_rss(command, cwd, payload, budget, compiler):
    """Fork the measured child from a tiny native process, not from Python."""
    if os.name != "posix":
        return {"error": "native RSS launcher requires POSIX"}
    source = r'''
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>
int main(int argc, char **argv) {
    pid_t child; int status, code; struct rusage usage; FILE *report;
    if (argc < 3) return 125;
    child = fork();
    if (child < 0) { perror("fork"); return 125; }
    if (child == 0) { execvp(argv[2], argv + 2); perror("execvp"); _exit(127); }
    while (waitpid(child, &status, 0) < 0) {
        if (errno != EINTR) { perror("waitpid"); return 125; }
    }
    if (getrusage(RUSAGE_CHILDREN, &usage) != 0) return 125;
    code = WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status);
    report = fopen(argv[1], "w");
    if (!report) return 125;
    fprintf(report, "{\"native_ru_maxrss\":%ld,\"returncode\":%d}\n", usage.ru_maxrss, code);
    if (fclose(report) != 0) return 125;
    return code;
}
'''
    with tempfile.TemporaryDirectory(prefix="wolfe-native-rss-") as scratch:
        scratch = Path(scratch)
        source_path, helper = scratch / "rss.c", scratch / "rss"
        source_path.write_text(source)
        build = invoke(shlex.split(compiler) + ["-std=c99", "-O2", str(source_path), "-o", str(helper)], cwd, "", budget)
        if build.get("returncode") != 0:
            return {"error": "native RSS launcher compilation failed", "detail": build.get("error", build.get("stderr", ""))[:1000]}

        def measured(argv, data, filename):
            measurement = scratch / filename
            run = invoke([str(helper), str(measurement)] + argv, cwd, data, budget)
            if "error" in run or not measurement.is_file():
                return {"error": run.get("error", "native launcher did not produce a measurement")}
            try:
                counters = json.loads(measurement.read_text())
                native = counters["native_ru_maxrss"]
            except (OSError, ValueError, KeyError) as exc:
                return {"error": str(exc)}
            return {
                "peak_rss_bytes": int(native) if sys.platform == "darwin" else int(native * 1024),
                "native_ru_maxrss": native,
                "native_unit": "bytes" if sys.platform == "darwin" else "KiB",
                "returncode": run.get("returncode"),
                "output_check": json_lines(run.get("stdout", "")),
            }

        result = measured(command, payload, "engine.json")
        if "peak_rss_bytes" not in result or result.get("returncode") != 0:
            return result
        baseline_command = shutil.which("true")
        baseline = measured([baseline_command], "", "baseline.json") if baseline_command else {"error": "true executable unavailable"}
        result.update({
            "method": "Fresh minimal native C launcher forks and execs the engine, then waitpid + getrusage(RUSAGE_CHILDREN) measures its sole child",
            "baseline": {"command": baseline_command, **baseline},
            "note": "The measured child forks from the small native launcher memory map, avoiding Python launcher's pre-exec RSS high-water. Peak includes engine startup/runtime/data and any small native pre-exec footprint. The true-process baseline is a sanity check and is NOT subtracted.",
        })
        return result


def measure_rss(command, cwd, payload, budget, compiler):
    native = native_rss(command, cwd, payload, budget, compiler)
    if "peak_rss_bytes" in native and native.get("returncode") == 0:
        return native
    if sys.platform.startswith("linux") and Path("/usr/bin/time").is_file():
        with tempfile.TemporaryDirectory(prefix="wolfe-benchmark-") as scratch:
            measurement = Path(scratch) / "rss.txt"
            run = invoke(
                ["/usr/bin/time", "-f", "%M", "-o", str(measurement)] + command,
                cwd, payload, budget,
            )
            if run.get("returncode") == 0 and measurement.is_file():
                try:
                    kib = int(measurement.read_text().strip())
                    return {
                        "peak_rss_bytes": kib * 1024,
                        "method": "GNU /usr/bin/time maximum resident set size (%M KiB), fresh engine process",
                        "returncode": run["returncode"],
                        "output_check": json_lines(run["stdout"]),
                    }
                except ValueError:
                    pass
    helper = invoke(
        [sys.executable, str(Path(__file__).resolve()), "--rss-helper"], cwd,
        json.dumps({"command": command, "cwd": cwd, "payload": payload}), budget,
    )
    if helper.get("returncode") == 0:
        try:
            return json.loads(helper["stdout"])
        except ValueError:
            pass
    return {"error": helper.get("error", helper.get("stderr", "RSS measurement unavailable"))}


def artifact(path):
    path = Path(path)
    if not path.is_file():
        return {"path": str(path), "available": False}
    raw = path.read_bytes()
    return {
        "path": str(path), "available": True, "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def engine_argv(command, args):
    argv = shlex.split(command) + ["--batch", "--mode", args.mode]
    if args.tools:
        argv += ["--tools", str(Path(args.tools).resolve())]
    if args.examples:
        argv += ["--examples", str(Path(args.examples).resolve())]
    return argv


def measure_engine(command, args, budget):
    argv = engine_argv(command, args)
    startup = []
    errors = []
    for _ in range(args.startup_runs):
        run = invoke(argv, args.cwd, "", budget)
        if run.get("returncode") == 0:
            startup.append(run["elapsed_seconds"])
        else:
            errors.append({"phase": "startup", **run})
            if "error" in run:
                break
    median_startup = statistics.median(startup) if startup else None
    payload = "".join(json.dumps({"text": REQUESTS[i % len(REQUESTS)]}) + "\n" for i in range(args.batch_size))
    batches = []
    streaming_works = True
    for _ in range(args.batch_runs):
        if streaming_works:
            run = streamed_loaded_batch(argv, args.cwd, payload, args.batch_size, args.latency_samples, budget)
            if "error" not in run:
                batches.append(run)
                continue
            errors.append({"phase": "streaming_batch", **run})
            streaming_works = False
        run = invoke(argv, args.cwd, payload, budget)
        if run.get("returncode") != 0:
            errors.append({"phase": "fallback_batch", **run})
            break
        adjusted = max(0, run["elapsed_seconds"] - median_startup) if median_startup is not None else None
        check = json_lines(run["stdout"])
        batches.append({
            "method": "fresh_process_minus_independent_median_startup_estimate",
            "batch_seconds_including_startup": run["elapsed_seconds"],
            "batch_seconds_estimate_excluding_startup": adjusted,
            "request_count": args.batch_size,
            "amortized_ms_per_request": adjusted * 1000 / args.batch_size if adjusted is not None else None,
            "requests_per_second": args.batch_size / adjusted if adjusted else None,
            "output_check": check,
            "protocol_ok": check["all_json_objects"] and check["lines"] == args.batch_size,
        })
    live_memory = [run["target_memory"] for run in batches
                   if run.get("protocol_ok") and "target_memory" in run]
    if live_memory:
        rss = {
            "peak_rss_bytes": max(sample["peak_rss_bytes"] for sample in live_memory),
            "resident_bytes_at_sample_maximum": max(sample["resident_bytes_at_sample"] for sample in live_memory),
            "method": "Maximum live post-exec engine VmHWM from Linux /proc/<engine_pid>/status across loaded batch processes; sampled before closing stdin",
            "samples": live_memory,
            "note": "Kernel-reported process resident-memory high-water mark since exec. Includes engine startup and runtime/data allocations; excludes Python benchmark launcher's pre-exec RSS. Not incremental model-only RAM.",
        }
    else:
        rss = measure_rss(argv, args.cwd, payload, budget, args.compiler)
    amortized = [run["amortized_ms_per_request"] for run in batches
                 if run.get("protocol_ok") and run.get("amortized_ms_per_request") is not None]
    latencies = [sample for run in batches if run.get("protocol_ok")
                 for sample in run.get("warmed_individual_request_ms", {}).get("samples", [])]
    return {
        "command": argv,
        "complete": len(startup) == args.startup_runs and len(batches) == args.batch_runs
                    and all(run.get("protocol_ok") for run in batches)
                    and "peak_rss_bytes" in rss,
        "fresh_process_startup_seconds": summary(startup),
        "loaded_batch_amortized_ms_per_request": summary(amortized),
        "warmed_individual_request_ms": summary(latencies),
        "batches": batches,
        "peak_memory": rss,
        "errors": errors,
    }


def main():
    if sys.argv[1:] == ["--rss-helper"]:
        return rss_helper(json.load(sys.stdin))
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default="./wolfe", help="command split with shlex, never a shell")
    parser.add_argument("--python-engine", help="optional, e.g. 'python3 wolfe.py'")
    parser.add_argument("--cwd", default=str(root))
    parser.add_argument("--tools")
    parser.add_argument("--examples")
    parser.add_argument("--state", help="optional existing calibration state to size; never passed to the engine")
    parser.add_argument("--mode", choices=["neural", "field", "keyword"], default="neural")
    parser.add_argument("--startup-runs", type=int, default=7)
    parser.add_argument("--batch-runs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--latency-samples", type=int, default=30, help="sequential request/reply samples per loaded process before the throughput batch")
    parser.add_argument("--budget-seconds", type=float, default=25)
    parser.add_argument("--compiler", default="cc")
    parser.add_argument("--report")
    args = parser.parse_args()
    if min(args.startup_runs, args.batch_runs, args.batch_size, args.latency_samples) < 1 or args.budget_seconds <= 0:
        parser.error("sample counts, batch size, and time budget must be positive")
    args.cwd = str(Path(args.cwd).resolve())
    budget = Budget(args.budget_seconds)
    compiler = invoke(shlex.split(args.compiler) + ["--version"], args.cwd, "", budget, cap=2)
    cpu = platform.processor()
    if Path("/proc/cpuinfo").is_file():
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.partition(":")[2].strip()
                break
    c_binary = shlex.split(args.engine)[0]
    resolved_binary = Path(args.cwd) / c_binary if "/" in c_binary else Path(shutil.which(c_binary) or c_binary)
    paths = {
        "c_binary": resolved_binary,
        "c_source": Path(args.cwd) / "wolfe.c",
        "python_source": Path(args.cwd) / "wolfe.py",
        "tool_definitions": Path(args.tools).resolve() if args.tools else Path(args.cwd) / "tools.json",
        "construction_examples": Path(args.examples).resolve() if args.examples else Path(args.cwd) / "examples.jsonl",
    }
    if args.state:
        paths["existing_state"] = Path(args.state).resolve()
    report = {
        "environment": {
            "system": platform.system(), "release": platform.release(),
            "machine": platform.machine(), "cpu": cpu,
            "logical_cpu_count": os.cpu_count(),
            "python": sys.version.splitlines()[0],
            "compiler": compiler.get("stdout", compiler.get("error", "unavailable")).splitlines()[:3],
        },
        "artifacts": {key: artifact(path) for key, path in paths.items()},
        "methodology": {
            "startup": "Seven fresh processes by default, --batch with empty stdin. Includes process creation, loading and exit. OS file caches are NOT flushed; this is not cold-disk startup. Loading is included only if the engine loads eagerly.",
            "warmed_latency": "After one warm-up response, send one request at a time and await its flushed reply before the next. Samples time parent write/flush through receipt of that response line, including engine JSON I/O, pipes and scheduling. Report median and nearest-rank p95; these are host end-to-end samples, not internal kernel timings.",
            "loaded_throughput": "After warm-up and sequential latency sampling, the already-loaded process receives a cyclic fixed batch. Time starts before writing that batch and ends on receiving its final line; divide by request count. Includes input/output JSON and pipe overhead, excludes initial loading and process exit. This is amortized throughput, not a p50 individual-request latency.",
            "fallback": "If streaming replies are unavailable, subtract median independent empty-batch startup from total fresh-process batch wall time; label the result an estimate. Negative differences clamp to zero.",
            "rss": "Prefer Linux /proc/<engine_pid>/status VmHWM and VmRSS sampled directly from each already-executed engine after timed requests while stdin remains open. Report maximum VmHWM across these processes; sampling is outside the timed interval. If unavailable, compile a tiny temporary native fork/exec/waitpid/getrusage launcher and measure its sole child, with a separate true-process baseline (not subtracted). This avoids Python pre-exec high-water contamination. Further fallback: GNU time or resource in a fresh Python helper; the latter may retain Python pre-exec high-water and overstate engine RSS. All methods include runtime/data and startup, not model-only memory.",
            "workload": "Six fixed tool requests repeated cyclically; measures bounded demo traffic, not language coverage. No heldout file is read. Neither tool execution nor calibration feedback is requested.",
            "comparison": "Identical command flags and payloads for C and optional Python. All measurements reflect this single host; no phone, ARM or microcontroller result is inferred.",
            "budget_seconds": args.budget_seconds,
        },
        "requests": REQUESTS,
        "engines": {},
    }
    began = time.perf_counter()
    for name, command in [("c", args.engine), ("python", args.python_engine)]:
        if not command:
            continue
        try:
            budget.remaining()
            report["engines"][name] = measure_engine(command, args, budget)
        except TimeoutError as exc:
            report["engines"][name] = {"error": str(exc)}
    report["measurement_elapsed_seconds"] = time.perf_counter() - began
    output = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.report:
        Path(args.report).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0 if all(item.get("complete") for item in report["engines"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
