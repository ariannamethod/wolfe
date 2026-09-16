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
ADAPT_PARENT_SHA256 = "7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005"


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


def adaptation_context(previous, output):
    """Choose the first affected uncorrected input from old offline receipts."""
    state_source = previous / "memory.json"
    if digest(state_source) != ADAPT_PARENT_SHA256:
        raise ValueError("Adaptation requires the declared two-correction parent")
    parent_corrections = json.loads(state_source.read_text())["corrections"]
    if len(parent_corrections) != 2:
        raise ValueError("Adaptation requires exactly two inherited corrections")
    source_paths = [state_source, previous / "manifest.json", previous / "table.json",
                    previous / "historical-inputs.json", previous / "historical-inputs.jsonl"]
    old_manifest = json.loads((previous / "manifest.json").read_text())
    if old_manifest["state_sha256"] != ADAPT_PARENT_SHA256:
        raise ValueError("Previous experiment used a different parent memory")
    if digest(previous / "historical-inputs.json") != old_manifest["historical_receipt_sha256"]:
        raise ValueError("Historical input receipt changed")
    for name in ("run.py", "wolfe_binding.py", "tools.json", "initial_examples.jsonl", "perception.py"):
        if digest(ROOT / name) != old_manifest["source_hashes"][name]:
            raise ValueError(f"Frozen perception input changed: {name}")
    build = json.loads((ROOT / ".build/build.json").read_text())
    if (digest(ROOT.parent / "wolfe.c") != old_manifest["engine"]["source_sha256"]
            or build != old_manifest["engine"]):
        raise ValueError("The inherited C engine/build receipt changed")

    trajectories = {}
    for path, expected in old_manifest["previous_input_sha256"].items():
        source = Path(path)
        if source.name == "trajectory.jsonl":
            if source.parent.name not in {f"seed{seed}" for seed in range(301, 309)}:
                raise ValueError("Historical trajectory is outside the declared training seeds")
            if digest(source) != expected:
                raise ValueError("Historical training trajectory changed")
            trajectories[path] = []
            source_paths.append(source)
    if (len(trajectories) != 8
            or {Path(path).parent.name for path in trajectories} != {f"seed{seed}" for seed in range(301, 309)}):
        raise ValueError("Expected exactly the eight old training trajectories")
    texts = observations()
    excluded = {record["text"] for record in parent_corrections}
    for line in (previous / "historical-inputs.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["trajectory"] not in trajectories:
            raise ValueError("Offline receipt names an undeclared training trajectory")
        if any(text not in texts for text in row["inputs"].values()):
            raise ValueError("Offline receipt contains an undeclared observation")
        trajectories[row["trajectory"]].append(row)

    counts = Counter()
    witnesses = []
    for path in sorted(trajectories):
        eligible = [row for row in trajectories[path]
                    if row["choices"]["legacy"] != row["choices"]["no-effects"]
                    and row["inputs"]["no-effects"] not in excluded]
        if eligible:
            first = min(eligible, key=lambda row: row["decision"])
            witnesses.append(first)
            counts[first["inputs"]["no-effects"]] += 1
    eligible_texts = [text for text in texts if text not in excluded and counts[text] > 0]
    if not eligible_texts:
        raise ValueError("No affected uncorrected context exists in old training receipts")
    context = max(eligible_texts, key=lambda text: counts[text])
    previous_hashes = {str(path): digest(path) for path in source_paths}
    receipt = {
        "rule": "earliest changed choice per old trajectory; count filtered inputs; initial example order breaks ties",
        "previous": str(previous), "historical_seeds": list(range(301, 309)),
        "parent_state_sha256": ADAPT_PARENT_SHA256,
        "selected_context": context, "selected_trajectories": counts[context],
        "first_decision_witnesses": witnesses,
        "counts": [{"input": text, "trajectories": counts[text], "excluded": text in excluded}
                   for text in texts],
        "previous_input_sha256": previous_hashes,
        "current_input_sha256": {name: digest(ROOT / name) for name in
                                 ("tools.json", "initial_examples.jsonl", "run.py", "STEP5.md")},
    }
    write_json(output / "context-selection.json", receipt)
    parent_state = output / "parent-memory.json"
    shutil.copyfile(state_source, parent_state)
    if digest(parent_state) != ADAPT_PARENT_SHA256:
        raise RuntimeError("Copied adaptation parent does not match its declared hash")
    return context, parent_state, parent_corrections, previous_hashes


def play(output, seed, state, perception=None):
    """Each episode uses a fresh game and C model with a fixed memory."""
    command = [sys.executable, str(ROOT / "run.py"), "--output", str(output),
               "--seed", str(seed), "--decisions", "128"]
    state_before = digest(state) if state else None
    if state:
        command += ["--state", str(state)]
    if perception is not None:
        command += ["--perception", perception]
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


def run(output, previous=None, adapt=False):
    output = output.resolve()
    if adapt and previous is None:
        raise ValueError("Adaptation requires the previous perception experiment")
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
    perception = None
    if previous is not None:
        baseline = "parent"
        if adapt:
            context, baseline_state, parent_corrections, previous_hashes = adaptation_context(previous, output)
            selection_seeds, evaluation_seeds = tuple(range(601, 609)), tuple(range(701, 717))
            protocol, perception = "STEP5.md", "no-effects"
        else:
            context, baseline_state, parent_corrections, previous_hashes = inherited_context(previous, output)
            selection_seeds, evaluation_seeds = tuple(range(301, 309)), tuple(range(401, 417))
            protocol = "STEP3.md"
    baseline_sha256 = digest(baseline_state) if baseline_state is not None else None
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
        metadata["parent_state_sha256"] = baseline_sha256
        metadata["context_selection_sha256"] = digest(output / "context-selection.json")
    if adapt:
        metadata["mechanism"] = "adapt_one_inherited_decision_to_no_effects"
        metadata["selection_perception"] = perception
        metadata["evaluation_conditions"] = {
            "parent": "no-effects", "selected": "no-effects", "legacy_reference": "legacy"}
    write_json(output / "manifest.json", metadata)
    (output / "protocol.md").write_bytes((ROOT / protocol).read_bytes())
    with open_model(baseline_state) as ancestor:
        initial_table = decision_table(ancestor)
    if adapt and initial_table != json.loads((previous / "table.json").read_text()):
        raise RuntimeError("The inherited full C response table changed")
    write_json(output / f"{baseline}-table.json", initial_table)
    candidates = [{"name": baseline, "state": baseline_state, "table": initial_table}]
    for index, name in enumerate(names):
        folder = output / f"candidate-{index}-{name}"
        folder.mkdir()
        state = folder / "memory.json"
        if baseline_state is not None:
            shutil.copyfile(baseline_state, state)
            if digest(state) != baseline_sha256:
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
            episode = play(folder / f"seed{seed}", seed, candidate["state"], perception)
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
            "parent_state_unchanged": digest(baseline_state) == baseline_sha256,
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
        conditions = [(baseline, baseline_state, perception), ("selected", selected_state, perception)]
        if adapt:
            conditions.append(("legacy_reference", baseline_state, "legacy"))
        for name, state, mode in conditions:
            folder = output / "evaluation" / name
            folder.mkdir(parents=True, exist_ok=True)
            episodes[name] = play(folder / f"seed{seed}", seed, state, mode)
        delta = episodes["selected"]["reward"] - episodes[baseline]["reward"]
        pair = {"seed": seed, **episodes, "reward_delta": delta}
        if adapt:
            pair["legacy_reward_delta"] = episodes["selected"]["reward"] - episodes["legacy_reference"]["reward"]
        pairs.append(pair)
        print(f"evaluation seed={seed} {baseline}={episodes[baseline]['reward']} selected={episodes['selected']['reward']} delta={delta}", flush=True)
        if adapt:
            print(f"reference seed={seed} legacy={episodes['legacy_reference']['reward']} selected-minus-legacy={pair['legacy_reward_delta']}", flush=True)
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
    if adapt:
        result["legacy_reference_comparison"] = {
            "paired_mean_reward_delta": sum(pair["legacy_reward_delta"] for pair in pairs) / len(pairs),
            "improved_seeds": sum(pair["legacy_reward_delta"] > 0 for pair in pairs),
            "worsened_seeds": sum(pair["legacy_reward_delta"] < 0 for pair in pairs),
            "tied_seeds": sum(pair["legacy_reward_delta"] == 0 for pair in pairs),
            "used_for_selection_or_benefit_gate": False,
        }
        result["totals"] = {name: {key: sum(pair[name][key] for pair in pairs)
                                   for key in ("reward", "kills", "dead")}
                            for name in ("parent", "selected", "legacy_reference")}
        result["claim"] = "one inherited memory adaptation under fixed no-effects perception; not self-play"
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
    adaptation = subparsers.add_parser("adapt")
    adaptation.add_argument("--previous", type=Path, required=True)
    adaptation.add_argument("--output", type=Path, required=True)
    table = subparsers.add_parser("table")
    table.add_argument("--state", type=Path)
    table.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "table":
        with open_model(args.state) as model:
            write_json(args.output, decision_table(model))
        return 0
    return run(args.output, args.previous if args.command in {"continue", "adapt"} else None,
               adapt=args.command == "adapt")


if __name__ == "__main__":
    raise SystemExit(main())
