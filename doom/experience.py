"""One predeclared generation of policy selection through WOLFE memory."""

import argparse
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


def run(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    names = [tool["name"] for tool in json.loads((ROOT / "tools.json").read_text())["tools"]]
    if len(names) != 6 or len(observations()) != 24 or CONTEXT not in observations():
        raise ValueError("The frozen action/observation surface changed")
    metadata = {
        "mechanism": "one_generation_selection_of_one_correction",
        "context": CONTEXT, "action_order": names,
        "selection_seeds": SELECTION_SEEDS, "evaluation_seeds": EVALUATION_SEEDS,
        "criterion": "sum of unmodified scenario returns; ancestor wins ties",
        "source_hashes": {name: digest(ROOT / name) for name in
                          ["STEP2.md", "experience.py", "run.py", "wolfe_binding.py",
                           "tools.json", "initial_examples.jsonl"]},
        "engine": json.loads((ROOT / ".build/build.json").read_text()),
    }
    write_json(output / "manifest.json", metadata)
    (output / "protocol.md").write_bytes((ROOT / "STEP2.md").read_bytes())
    with open_model() as ancestor:
        initial_table = decision_table(ancestor)
    write_json(output / "ancestor-table.json", initial_table)
    candidates = [{"name": "ancestor", "state": None, "table": initial_table}]
    for index, name in enumerate(names):
        folder = output / f"candidate-{index}-{name}"
        folder.mkdir()
        state = folder / "memory.json"
        record = {"text": CONTEXT, "tool": name, "arguments": {}}
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
        for seed in SELECTION_SEEDS:
            episode = play(folder / f"seed{seed}", seed, candidate["state"])
            episodes.append(episode)
            print(f"selection {candidate['name']} seed={seed} reward={episode['reward']} kills={episode['kills']}", flush=True)
        entry = {"name": candidate["name"], "episodes": episodes,
                 "reward_sum": sum(item["reward"] for item in episodes),
                 "state_sha256": digest(candidate["state"]) if candidate["state"] else None}
        write_json(folder / "results.json", entry)
        selection.append(entry)

    # Strict greater-than preserves the ancestor on ties and the first maximum
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
        result = {"mechanism": "NO_ADOPTION", "benefit": "NOT_RUN",
                  "reason": "No candidate strictly improved the ancestor on selection seeds"}
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
    if restarted != candidates[winner]["table"]:
        raise RuntimeError("Complete decision table changed across process restart")
    changes = changed_decisions(initial_table, restarted)
    write_json(output / "changed-decisions.json", changes)

    pairs = []
    for seed in EVALUATION_SEEDS:
        episodes = {}
        for name, state in [("ancestor", None), ("selected", selected_state)]:
            folder = output / "evaluation" / name
            folder.mkdir(parents=True, exist_ok=True)
            episodes[name] = play(folder / f"seed{seed}", seed, state)
        delta = episodes["selected"]["reward"] - episodes["ancestor"]["reward"]
        pair = {"seed": seed, **episodes, "reward_delta": delta}
        pairs.append(pair)
        print(f"evaluation seed={seed} ancestor={episodes['ancestor']['reward']} selected={episodes['selected']['reward']} delta={delta}", flush=True)
    write_json(output / "evaluation.json", pairs)
    improved = sum(pair["reward_delta"] > 0 for pair in pairs)
    worsened = sum(pair["reward_delta"] < 0 for pair in pairs)
    mean_delta = sum(pair["reward_delta"] for pair in pairs) / len(pairs)
    result = {
        "mechanism": "PASS" if changes else "FAIL",
        "benefit": "PASS" if mean_delta > 0 and improved > worsened else "FAIL",
        "selected": selection[winner]["name"], "changed_observations": len(changes),
        "restart_table_identical": True, "paired_mean_reward_delta": mean_delta,
        "improved_seeds": improved, "worsened_seeds": worsened,
        "tied_seeds": len(pairs) - improved - worsened,
        "selected_state_sha256": digest(selected_state),
        "claim": "one memory intervention on one scenario; not multiplayer self-play",
    }
    write_json(output / "result.json", result)
    print(json.dumps(result, indent=2), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    experiment = subparsers.add_parser("run")
    experiment.add_argument("--output", type=Path, required=True)
    table = subparsers.add_parser("table")
    table.add_argument("--state", type=Path)
    table.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "table":
        with open_model(args.state) as model:
            write_json(args.output, decision_table(model))
        return 0
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
