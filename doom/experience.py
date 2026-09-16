"""One predeclared generation of policy selection through WOLFE memory."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from wolfe_binding import Wolfe


ROOT = Path(__file__).resolve().parent
CONTEXT = "healthhigh ammopresent scenecenter"
SELECTION_SEEDS = tuple(range(101, 109))
EVALUATION_SEEDS = tuple(range(201, 217))
PARENT_SHA256 = "9f53271cde84088f58c62cb9e2e95eec54e99f4634b0cd8c74349c5ed30eb0cc"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def open_model(state=None):
    build = json.loads((ROOT / ".build/build.json").read_text())
    library = ROOT / ".build" / build["library"]
    if digest(library) != build["library_sha256"]:
        raise ValueError("C library no longer matches the build receipt")
    return Wolfe(library, ROOT / "tools.json", ROOT / "initial_examples.jsonl", state=state)


def observations():
    return [json.loads(line)["text"] for line in
            (ROOT / "initial_examples.jsonl").read_text().splitlines()]


def decision_table(model):
    return [{"input": text, "response": model.call(text)} for text in observations()]


def changed_decisions(before, after):
    changes = []
    if len(before) != len(after):
        raise ValueError("Decision table sizes differ")
    for original, revised in zip(before, after):
        if original["input"] != revised["input"]:
            raise ValueError("Decision table observations differ")
        left, right = original["response"], revised["response"]
        if (left["status"], left["calls"]) != (right["status"], right["calls"]):
            changes.append({"input": original["input"],
                            "before": {"status": left["status"], "calls": left["calls"]},
                            "after": {"status": right["status"], "calls": right["calls"]}})
    return changes


def inherited_context(previous, output):
    """Choose one uncorrected context from the parent's old selection only."""
    state_source = previous / "selected-memory.json"
    if digest(state_source) != PARENT_SHA256:
        raise ValueError("Previous memory is not the declared step-2 parent")
    state = json.loads(state_source.read_text())
    parent_corrections = state["corrections"]
    if parent_corrections != [{"text": CONTEXT, "tool": "shoot", "arguments": {}}]:
        raise ValueError("The declared parent correction changed")
    source_paths = [state_source, previous / "selection.json", previous / "manifest.json"]
    previous_selection = json.loads(source_paths[1].read_text())
    previous_manifest = json.loads(source_paths[2].read_text())
    if (previous_selection["selected"] != "shoot"
            or previous_selection["selection_state_sha256"] != PARENT_SHA256):
        raise ValueError("Previous selection does not identify the declared parent")
    for name in ["tools.json", "initial_examples.jsonl", "run.py", "wolfe_binding.py"]:
        if digest(ROOT / name) != previous_manifest["source_hashes"][name]:
            raise ValueError(f"The inherited experiment's {name} changed")
    if digest(ROOT.parent / "wolfe.c") != previous_manifest["engine"]["source_sha256"]:
        raise ValueError("The inherited C engine changed")

    texts = observations()
    counts = Counter()
    for seed in SELECTION_SEEDS:
        trajectory = previous / "selection" / "shoot" / f"seed{seed}" / "trajectory.jsonl"
        source_paths.append(trajectory)
        for line in trajectory.read_text().splitlines():
            text = json.loads(line)["input"]
            if text not in texts:
                raise ValueError("Old trajectory contains an undeclared observation")
            counts[text] += 1
    excluded = {record["text"] for record in parent_corrections}
    eligible = [text for text in texts if text not in excluded and counts[text] > 0]
    if not eligible:
        raise ValueError("No visited uncorrected context remains")
    # max keeps the first tied item, hence the original example order.
    context = max(eligible, key=lambda text: counts[text])
    previous_hashes = {str(path): digest(path) for path in source_paths}
    receipt = {
        "rule": "most visited uncorrected input; initial example order breaks ties",
        "previous": str(previous), "selection_policy": "shoot",
        "selection_seeds": SELECTION_SEEDS, "parent_state_sha256": PARENT_SHA256,
        "selected_context": context, "selected_visits": counts[context],
        "total_decisions": sum(counts.values()),
        "counts": [{"input": text, "visits": counts[text], "excluded": text in excluded}
                   for text in texts],
        "previous_input_sha256": previous_hashes,
        "current_input_sha256": {name: digest(ROOT / name) for name in
                                 ["tools.json", "initial_examples.jsonl", "STEP3.md"]},
    }
    write_json(output / "context-selection.json", receipt)
    parent_state = output / "parent-memory.json"
    shutil.copyfile(state_source, parent_state)
    if digest(parent_state) != PARENT_SHA256:
        raise RuntimeError("Copied parent memory does not match its declared hash")
    return context, parent_state, parent_corrections, previous_hashes


def unchanged_previous(previous_hashes):
    for path, expected in previous_hashes.items():
        if digest(path) != expected:
            raise RuntimeError(f"Previous evidence changed: {path}")


def play(output, seed, state):
    """Each episode uses a fresh game and C model with a fixed memory."""
    command = [sys.executable, str(ROOT / "run.py"), "--output", str(output),
               "--seed", str(seed), "--decisions", "128"]
    state_before = digest(state) if state else None
    if state:
        command += ["--state", str(state)]
    with output.with_suffix(".console.txt").open("x") as stream:
        result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    summary_path = output / "summary.json"
    # An all-idle candidate can fail the old connection gate and still has a
    # legitimate episode return. Never exclude poor policies from selection.
    if result.returncode not in {0, 1} or not summary_path.is_file():
        raise RuntimeError(f"Episode process failed; preserved output at {output}")
    if state and digest(state) != state_before:
        raise RuntimeError("Frozen memory changed during an episode")
    summary = json.loads(summary_path.read_text())
    return {"seed": seed, "reward": summary["total_reward"],
            "kills": summary["final"]["variables"]["kills"],
            "dead": summary["final"]["dead"], "decisions": summary["decisions"],
            "elapsed_tics": summary["elapsed_tics"], "actions": summary["actions"],
            "directory": str(output)}


def run(output, previous=None):
    output = output.resolve()
    if previous is not None:
        previous = previous.resolve()
        if output == previous or previous in output.parents:
            raise ValueError("Continuation output must be outside previous evidence")
    output.mkdir(parents=True, exist_ok=False)
    names = [tool["name"] for tool in json.loads((ROOT / "tools.json").read_text())["tools"]]
    if len(names) != 6 or len(observations()) != 24 or CONTEXT not in observations():
        raise ValueError("The frozen action/observation surface changed")
    context = CONTEXT
    baseline = "ancestor"
    baseline_state = None
    parent_corrections = []
    previous_hashes = {}
    selection_seeds, evaluation_seeds = SELECTION_SEEDS, EVALUATION_SEEDS
    protocol = "STEP2.md"
    if previous is not None:
        context, baseline_state, parent_corrections, previous_hashes = inherited_context(previous, output)
        baseline = "parent"
        selection_seeds, evaluation_seeds = tuple(range(301, 309)), tuple(range(401, 417))
        protocol = "STEP3.md"
    metadata = {
        "mechanism": ("one_generation_selection_of_one_correction" if previous is None
                      else "inherit_one_correction_select_one_more"),
        "context": context, "action_order": names,
        "selection_seeds": selection_seeds, "evaluation_seeds": evaluation_seeds,
        "criterion": f"sum of unmodified scenario returns; {baseline} wins ties",
        "source_hashes": {name: digest(ROOT / name) for name in
                          [protocol, "experience.py", "run.py", "wolfe_binding.py",
                           "tools.json", "initial_examples.jsonl"]},
        "engine": json.loads((ROOT / ".build/build.json").read_text()),
    }
    if previous is not None:
        metadata["parent_state_sha256"] = PARENT_SHA256
        metadata["context_selection_sha256"] = digest(output / "context-selection.json")
    write_json(output / "manifest.json", metadata)
    (output / "protocol.md").write_bytes((ROOT / protocol).read_bytes())
    with open_model(baseline_state) as ancestor:
        initial_table = decision_table(ancestor)
    write_json(output / f"{baseline}-table.json", initial_table)
    candidates = [{"name": baseline, "state": baseline_state, "table": initial_table}]
    for index, name in enumerate(names):
        folder = output / f"candidate-{index}-{name}"
        folder.mkdir()
        state = folder / "memory.json"
        if baseline_state is not None:
            shutil.copyfile(baseline_state, state)
            if digest(state) != PARENT_SHA256:
                raise RuntimeError("Candidate did not inherit the declared parent")
        record = {"text": context, "tool": name, "arguments": {}}
        with open_model(state) as model:
            model.correct(record)
            table = decision_table(model)
        write_json(folder / "correction.json", record)
        write_json(folder / "table.json", table)
        write_json(folder / "changed-decisions.json", changed_decisions(initial_table, table))
        candidates.append({"name": name, "state": state, "table": table})

    selection = []
    for candidate in candidates:
        folder = output / "selection" / candidate["name"]
        folder.mkdir(parents=True)
        episodes = []
        for seed in selection_seeds:
            episode = play(folder / f"seed{seed}", seed, candidate["state"])
            episodes.append(episode)
            print(f"selection {candidate['name']} seed={seed} reward={episode['reward']} kills={episode['kills']}", flush=True)
        entry = {"name": candidate["name"], "episodes": episodes,
                 "reward_sum": sum(item["reward"] for item in episodes),
                 "state_sha256": digest(candidate["state"]) if candidate["state"] else None}
        write_json(folder / "results.json", entry)
        selection.append(entry)

    # Strict greater-than preserves the baseline on ties and the first maximum
    # among improving candidates in the original tools.json order.
    winner = 0
    for index in range(1, len(selection)):
        if selection[index]["reward_sum"] > selection[winner]["reward_sum"]:
            winner = index
    receipt = {"selected": selection[winner]["name"], "selected_index": winner,
               "adopted": winner != 0, "selection": selection,
               "selection_state_sha256": selection[winner]["state_sha256"]}
    write_json(output / "selection.json", receipt)
    if winner == 0:
        unchanged_previous(previous_hashes)
        result = {"mechanism": "NO_ADOPTION", "benefit": "NOT_RUN",
                  "reason": f"No candidate strictly improved the {baseline} on selection seeds"}
        write_json(output / "result.json", result)
        print(json.dumps(result), flush=True)
        return 0

    selected_state = output / "selected-memory.json"
    shutil.copyfile(candidates[winner]["state"], selected_state)
    if digest(selected_state) != receipt["selection_state_sha256"]:
        raise RuntimeError("Selected memory copy does not match sealed selection")
    restart_table = output / "restarted-table.json"
    subprocess.run([sys.executable, str(Path(__file__).resolve()), "table",
                    "--state", str(selected_state), "--output", str(restart_table)],
                   cwd=ROOT, check=True)
    restarted = json.loads(restart_table.read_text())
    restart_identical = restarted == candidates[winner]["table"]
    if not restart_identical and previous is None:
        raise RuntimeError("Complete decision table changed across process restart")
    changes = changed_decisions(initial_table, restarted)
    write_json(output / "changed-decisions.json", changes)
    memory_gate = {}
    if previous is not None:
        saved = json.loads(selected_state.read_text())
        expected = parent_corrections + [{"text": context, "tool": selection[winner]["name"],
                                          "arguments": {}}]
        before = {item["input"]: item["response"] for item in initial_table}
        after = {item["input"]: item["response"] for item in restarted}
        retained = all((before[item["text"]]["status"], before[item["text"]]["calls"])
                       == (after[item["text"]]["status"], after[item["text"]]["calls"])
                       for item in parent_corrections)
        memory_gate = {
            "parent_decisions_retained": retained,
            "exact_inherited_plus_one_correction": saved["corrections"] == expected,
            "zero_reward_counters": saved["tools"] == {
                name: {"accepted": 0, "rejected": 0} for name in names},
            "parent_state_unchanged": digest(baseline_state) == PARENT_SHA256,
        }
        unchanged_previous(previous_hashes)
        if not changes or not restart_identical or not all(memory_gate.values()):
            result = {"mechanism": "FAIL", "benefit": "NOT_RUN",
                      "selected": selection[winner]["name"],
                      "changed_observations": len(changes),
                      "restart_table_identical": restart_identical, **memory_gate,
                      "selected_state_sha256": digest(selected_state),
                      "reason": "The selected child failed the accumulation gate"}
            write_json(output / "result.json", result)
            print(json.dumps(result, indent=2), flush=True)
            return 0

    pairs = []
    for seed in evaluation_seeds:
        episodes = {}
        for name, state in [(baseline, baseline_state), ("selected", selected_state)]:
            folder = output / "evaluation" / name
            folder.mkdir(parents=True, exist_ok=True)
            episodes[name] = play(folder / f"seed{seed}", seed, state)
        delta = episodes["selected"]["reward"] - episodes[baseline]["reward"]
        pair = {"seed": seed, **episodes, "reward_delta": delta}
        pairs.append(pair)
        print(f"evaluation seed={seed} {baseline}={episodes[baseline]['reward']} selected={episodes['selected']['reward']} delta={delta}", flush=True)
    write_json(output / "evaluation.json", pairs)
    improved = sum(pair["reward_delta"] > 0 for pair in pairs)
    worsened = sum(pair["reward_delta"] < 0 for pair in pairs)
    mean_delta = sum(pair["reward_delta"] for pair in pairs) / len(pairs)
    unchanged_previous(previous_hashes)
    result = {
        "mechanism": "PASS" if changes else "FAIL",
        "benefit": "PASS" if mean_delta > 0 and improved > worsened else "FAIL",
        "selected": selection[winner]["name"], "changed_observations": len(changes),
        "restart_table_identical": restart_identical, "paired_mean_reward_delta": mean_delta,
        "improved_seeds": improved, "worsened_seeds": worsened,
        "tied_seeds": len(pairs) - improved - worsened,
        "selected_state_sha256": digest(selected_state),
        "claim": "one memory intervention on one scenario; not multiplayer self-play",
        **memory_gate,
    }
    write_json(output / "result.json", result)
    print(json.dumps(result, indent=2), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    experiment = subparsers.add_parser("run")
    experiment.add_argument("--output", type=Path, required=True)
    continuation = subparsers.add_parser("continue")
    continuation.add_argument("--previous", type=Path, required=True)
    continuation.add_argument("--output", type=Path, required=True)
    table = subparsers.add_parser("table")
    table.add_argument("--state", type=Path)
    table.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "table":
        with open_model(args.state) as model:
            write_json(args.output, decision_table(model))
        return 0
    return run(args.output, args.previous if args.command == "continue" else None)


if __name__ == "__main__":
    raise SystemExit(main())
