"""One fixed-memory comparison of legacy and effect-filtered perception."""

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

from experience import ROOT, decision_table, digest, open_model, write_json
from run import action_vector, focus_label, observation


MEMORY_SHA256 = "7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005"
CONDITIONS = ("legacy", "no-effects")
SEEDS = tuple(range(501, 517))


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def screen_width(folder):
    png = (folder / "frame_000.png").read_bytes()
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Initial frame is not a PNG")
    return struct.unpack(">I", png[16:20])[0]


def offline_receipt(previous, output, table):
    counts = Counter()
    hashes = {}
    with (output / "historical-inputs.jsonl").open("x") as stream:
        for seed in range(301, 309):
            folder = previous / "selection" / "shoot" / f"seed{seed}"
            trajectory = folder / "trajectory.jsonl"
            for path in (trajectory, folder / "frame_000.png"):
                hashes[str(path)] = digest(path)
            width = screen_width(folder)
            for row in rows(trajectory):
                raw = row["before"]
                texts = {mode: observation(raw, width, mode) for mode in CONDITIONS}
                if texts["legacy"] != row["input"] or table[row["input"]] != row["response"]:
                    raise ValueError("Historical legacy observation or C response changed")
                choices = {mode: action_vector(table[text])[0] for mode, text in texts.items()}
                counts["decisions"] += 1
                counts["changed_inputs"] += texts["legacy"] != texts["no-effects"]
                counts["changed_choices"] += choices["legacy"] != choices["no-effects"]
                item = {"trajectory": str(trajectory), "decision": row["decision"],
                        "inputs": texts, "choices": choices,
                        "focus": {mode: focus_label(raw, mode) for mode in CONDITIONS}}
                stream.write(json.dumps(item, sort_keys=True) + "\n")
    receipt = {"counts": dict(counts), "input_sha256": hashes,
               "claim": "alternative encodings of historical states; no alternate episode returns"}
    write_json(output / "historical-inputs.json", receipt)
    return receipt


def episode(output, seed, condition, memory, table):
    command = [sys.executable, str(ROOT / "run.py"), "--output", str(output),
               "--seed", str(seed), "--decisions", "128", "--state", str(memory),
               "--perception", condition]
    with output.with_suffix(".console.txt").open("x") as stream:
        process = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    if process.returncode not in {0, 1} or not (output / "summary.json").is_file():
        raise RuntimeError(f"Episode failed; preserved output: {output}")
    if digest(memory) != MEMORY_SHA256:
        raise RuntimeError("Frozen memory changed during gameplay")
    trajectory = rows(output / "trajectory.jsonl")
    width = screen_width(output)
    for row in trajectory:
        raw = row["before"]
        if row["focus"] != focus_label(raw, condition) or row["input"] != observation(raw, width, condition):
            raise RuntimeError("Episode did not follow its declared perception")
        if row["response"] != table[row["input"]]:
            raise RuntimeError("Live response differs from the frozen C table")
        if action_vector(row["response"]) != (row["action"], row["buttons"], row["executor_fallback"]):
            raise RuntimeError("Live action differs from the C response")
    summary = json.loads((output / "summary.json").read_text())
    reward = sum(row["reward"] for row in trajectory)
    if reward != summary["total_reward"]:
        raise RuntimeError("Raw and summarized rewards differ")
    final = trajectory[-1]["after"]
    receipt = {"seed": seed, "condition": condition, "reward": reward,
               "kills": final["variables"]["kills"], "dead": final["dead"],
               "decisions": len(trajectory), "elapsed_tics": sum(row["elapsed_tics"] for row in trajectory),
               "shoot_calls": sum(row["action"] == "shoot" for row in trajectory),
               "ammo_consumed": sum(max(0, row["before"]["variables"]["ammo"] -
                                        row["after"]["variables"]["ammo"]) for row in trajectory),
               "directory": str(output)}
    return receipt, trajectory


def run(previous, output):
    previous, output = previous.resolve(), output.resolve()
    if output == previous or previous in output.parents:
        raise ValueError("Output must be outside the previous evidence")
    original_state = previous / "selected-memory.json"
    if digest(original_state) != MEMORY_SHA256:
        raise ValueError("This step requires the declared two-correction memory")
    old_manifest = json.loads((previous / "manifest.json").read_text())
    for name in ("tools.json", "initial_examples.jsonl", "wolfe_binding.py"):
        if digest(ROOT / name) != old_manifest["source_hashes"][name]:
            raise ValueError(f"Frozen input changed: {name}")
    build = json.loads((ROOT / ".build/build.json").read_text())
    if (digest(ROOT.parent / "wolfe.c") != old_manifest["engine"]["source_sha256"]
            or build != old_manifest["engine"]):
        raise ValueError("The C engine/build receipt changed")
    output.mkdir(parents=True, exist_ok=False)
    memory = output / "memory.json"
    shutil.copyfile(original_state, memory)
    with open_model(memory) as model:
        complete_table = decision_table(model)
    if complete_table != json.loads((previous / "restarted-table.json").read_text()):
        raise RuntimeError("The inherited full C response table changed")
    write_json(output / "table.json", complete_table)
    table = {row["input"]: row["response"] for row in complete_table}
    history = offline_receipt(previous, output, table)
    old_hashes = history["input_sha256"] | {
        str(path): digest(path) for path in
        (original_state, previous / "manifest.json", previous / "restarted-table.json")}
    source_hashes = {name: digest(ROOT / name) for name in
                     ("STEP4.md", "perception.py", "run.py", "experience.py", "wolfe_binding.py",
                      "tools.json", "initial_examples.jsonl")}
    manifest = {"mechanism": "exclude_two_transient_label_names", "conditions": CONDITIONS,
                "evaluation_seeds": SEEDS, "state_sha256": MEMORY_SHA256,
                "previous_input_sha256": old_hashes, "source_hashes": source_hashes,
                "engine": build, "historical_receipt_sha256": digest(output / "historical-inputs.json")}
    write_json(output / "manifest.json", manifest)
    (output / "protocol.md").write_bytes((ROOT / "STEP4.md").read_bytes())

    pairs = []
    for seed in SEEDS:
        episodes, trajectories = {}, {}
        for condition in CONDITIONS:
            folder = output / "episodes" / condition
            folder.mkdir(parents=True, exist_ok=True)
            episodes[condition], trajectories[condition] = episode(
                folder / f"seed{seed}", seed, condition, memory, table)
        if trajectories["legacy"][0]["before"] != trajectories["no-effects"][0]["before"]:
            raise RuntimeError("Paired episodes have different initial states")
        divergence = None
        for left, right in zip(trajectories["legacy"], trajectories["no-effects"]):
            if left["action"] != right["action"]:
                if left["before"] != right["before"] or left["input"] == right["input"]:
                    raise RuntimeError("First action divergence is not from a shared raw state")
                divergence = {"decision": left["decision"], "raw": left["before"],
                              "legacy": {k: left[k] for k in ("input", "focus", "action")},
                              "no-effects": {k: right[k] for k in ("input", "focus", "action")}}
                break
        delta = episodes["no-effects"]["reward"] - episodes["legacy"]["reward"]
        pairs.append({"seed": seed, **episodes, "reward_delta": delta,
                      "first_action_divergence": divergence})
        print(f"seed={seed} legacy={episodes['legacy']['reward']} no-effects={episodes['no-effects']['reward']} delta={delta}", flush=True)
    write_json(output / "evaluation.json", pairs)
    for path, expected in old_hashes.items():
        if digest(path) != expected:
            raise RuntimeError(f"Historical input changed: {path}")
    for name, expected in source_hashes.items():
        if digest(ROOT / name) != expected:
            raise RuntimeError(f"Experimental source changed: {name}")
    improved = sum(pair["reward_delta"] > 0 for pair in pairs)
    worsened = sum(pair["reward_delta"] < 0 for pair in pairs)
    mean_delta = sum(pair["reward_delta"] for pair in pairs) / len(pairs)
    live_divergences = sum(pair["first_action_divergence"] is not None for pair in pairs)
    mechanism = (history["counts"]["changed_inputs"] > 0
                 and history["counts"]["changed_choices"] > 0 and live_divergences > 0)
    result = {"mechanism": "PASS" if mechanism else "FAIL",
              "benefit": "PASS" if mean_delta > 0 and improved > worsened else "FAIL",
              "paired_mean_reward_delta": mean_delta, "improved_seeds": improved,
              "worsened_seeds": worsened, "tied_seeds": len(pairs) - improved - worsened,
              "paired_live_divergences": live_divergences, "historical_changes": history["counts"],
              "state_sha256": digest(memory), "table_matches_parent": True,
              "totals": {mode: {key: sum(pair[mode][key] for pair in pairs) for key in
                         ("reward", "kills", "dead", "shoot_calls", "ammo_consumed")}
                         for mode in CONDITIONS},
              "claim": "one symbolic perception intervention with a frozen policy"}
    write_json(output / "result.json", result)
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.previous, args.output))
