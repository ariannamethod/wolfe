"""One declared grid of two-context memory interventions, with a fixed exterior."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from experience import (ROOT, changed_decisions, decision_table, digest,
                        open_model, play, write_json)


A = "healthhigh ammopresent sceneempty"
B = "healthhigh ammopresent sceneleft"
PARENT_SHA256 = "31fa2dc243e9aca6c7bfce5444a06c203fa08db178de8349ec8b99fc359b9b92"
LEGACY_SHA256 = "7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005"
SELECTION_SEEDS = tuple(range(801, 809))
EVALUATION_SEEDS = tuple(range(901, 917))


def read_json(path):
    return json.loads(path.read_text())


def trajectory(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def loop_stats(rows):
    aba = bab = same_object = 0
    for left, middle, right in zip(rows, rows[1:], rows[2:]):
        sequence = (left["input"], middle["input"], right["input"])
        aba += sequence == (A, B, A)
        if sequence == (B, A, B):
            bab += 1
            first, last = left["focus"], right["focus"]
            same_object += first is not None and last is not None and first["id"] == last["id"]
    return {"decisions": len(rows), "a_visits": sum(row["input"] == A for row in rows),
            "b_visits": sum(row["input"] == B for row in rows),
            "aba_windows": aba, "bab_windows": bab, "same_object_bab_windows": same_object,
            "aba_per_100_decisions": 100 * aba / len(rows) if rows else 0.0}


def eligibility(state, table, parent_table, parent_records, names, pair):
    changes = changed_decisions(parent_table, table)
    responses = {row["input"]: row["response"] for row in table}
    expected = parent_records[:2] + [
        {"text": A, "tool": pair[0], "arguments": {}},
        {"text": B, "tool": pair[1], "arguments": {}},
    ]
    memory = read_json(state)
    outside = [change for change in changes if change["input"] not in {A, B}]
    checks = {
        "requested_pair_realized": all(
            responses[text]["status"] == "call"
            and responses[text]["calls"] == [{"name": tool, "arguments": {}}]
            for text, tool in zip((A, B), pair)),
        "other_22_decisions_fixed": not outside,
        "exact_four_corrections": memory["corrections"] == expected,
        "zero_reward_counters": memory["tools"] == {
            name: {"accepted": 0, "rejected": 0} for name in names},
    }
    return {"eligible": all(checks.values()), "checks": checks,
            "outside_changes": outside, "changed_decisions": changes,
            "actual_targets": {text: {key: responses[text][key] for key in ("status", "calls")}
                               for text in (A, B)}}


def fixed_episode(output, seed, state, perception, table):
    receipt = play(output, seed, state, perception)
    rows = trajectory(output / "trajectory.jsonl")
    responses = {row["input"]: row["response"] for row in table}
    if not rows or sum(row["reward"] for row in rows) != receipt["reward"]:
        raise RuntimeError("Raw episode return differs from its summary")
    for row in rows:
        if row["response"] != responses[row["input"]]:
            raise RuntimeError("A live response differs from its frozen C table")
    elapsed = sum(row["elapsed_tics"] for row in rows)
    if (receipt["decisions"] != len(rows) or receipt["elapsed_tics"] != elapsed
            or receipt["kills"] != rows[-1]["after"]["variables"]["kills"]
            or receipt["dead"] != rows[-1]["after"]["dead"]):
        raise RuntimeError("Raw episode behavior differs from its summary")
    receipt["perception"] = perception
    receipt["loops"] = loop_stats(rows)
    receipt["survived_horizon"] = not receipt["dead"] and elapsed == 512 and len(rows) == 128
    return receipt


def totals(episodes):
    result = {key: sum(episode[key] for episode in episodes)
              for key in ("reward", "kills", "dead", "survived_horizon", "decisions")}
    for key in ("a_visits", "b_visits", "aba_windows", "bab_windows", "same_object_bab_windows"):
        result[key] = sum(episode["loops"][key] for episode in episodes)
    result["aba_per_100_decisions"] = (100 * result["aba_windows"] / result["decisions"]
                                       if result["decisions"] else 0.0)
    return result


def unchanged(hashes):
    for path, expected in hashes.items():
        if digest(path) != expected:
            raise RuntimeError(f"Frozen input changed: {path}")


def finish(output, result, hashes):
    unchanged(hashes)
    write_json(output / "result.json", result)
    print(json.dumps(result, indent=2), flush=True)
    return 0


def run(previous, legacy_source, output):
    previous, legacy_source, output = previous.resolve(), legacy_source.resolve(), output.resolve()
    if (output == previous or previous in output.parents
            or output == legacy_source.parent or legacy_source.parent in output.parents):
        raise ValueError("Output must be outside the prior evidence directories")
    parent_source = previous / "selected-memory.json"
    if digest(parent_source) != PARENT_SHA256 or digest(legacy_source) != LEGACY_SHA256:
        raise ValueError("This step requires its declared parent and legacy memories")
    old_manifest = read_json(previous / "manifest.json")
    old_selection = read_json(previous / "selection.json")
    if (old_selection["selection_state_sha256"] != PARENT_SHA256
            or old_manifest["selection_seeds"] != list(range(601, 609))):
        raise ValueError("Previous selection does not identify the declared parent")
    for name in ("experience.py", "run.py", "wolfe_binding.py", "tools.json", "initial_examples.jsonl"):
        if digest(ROOT / name) != old_manifest["source_hashes"][name]:
            raise ValueError(f"Inherited input changed: {name}")
    build = read_json(ROOT / ".build/build.json")
    if (build != old_manifest["engine"]
            or digest(ROOT.parent / "wolfe.c") != build["source_sha256"]):
        raise ValueError("The C core/build receipt changed")
    names = [tool["name"] for tool in read_json(ROOT / "tools.json")["tools"]]
    parent_records = read_json(parent_source)["corrections"]
    if len(names) != 6 or len(parent_records) != 3 or parent_records[2]["text"] != A:
        raise ValueError("The declared action or parent correction surface changed")
    output.mkdir(parents=True, exist_ok=False)
    parent_state, legacy_state = output / "parent-memory.json", output / "legacy-memory.json"
    shutil.copyfile(parent_source, parent_state)
    shutil.copyfile(legacy_source, legacy_state)
    if digest(parent_state) != PARENT_SHA256 or digest(legacy_state) != LEGACY_SHA256:
        raise RuntimeError("Copied memories do not match their declared hashes")
    with open_model(parent_state) as model:
        parent_table = decision_table(model)
    if parent_table != read_json(previous / "restarted-table.json") or len(parent_table) != 24:
        raise RuntimeError("The parent's complete decision table changed")
    with open_model(legacy_state) as model:
        legacy_table = decision_table(model)
    write_json(output / "parent-table.json", parent_table)
    write_json(output / "legacy-table.json", legacy_table)
    parent_calls = {row["input"]: row["response"] for row in parent_table}
    for text, tool in ((A, "turn_left"), (B, "turn_right")):
        if (parent_calls[text]["status"] != "call"
                or parent_calls[text]["calls"] != [{"name": tool, "arguments": {}}]):
            raise RuntimeError("The declared parent pair changed")

    prior_paths = [parent_source, legacy_source, previous / "manifest.json",
                   previous / "selection.json", previous / "restarted-table.json"]
    old_episodes, witness = [], []
    for seed in range(601, 609):
        path = previous / "selection" / old_selection["selected"] / f"seed{seed}" / "trajectory.jsonl"
        prior_paths.append(path)
        rows = trajectory(path)
        if any(row["response"] != parent_calls[row["input"]] for row in rows):
            raise RuntimeError("Historical training responses differ from the declared parent")
        old_episodes.append({"seed": seed, "trajectory": str(path), "loops": loop_stats(rows)})
        if seed == 601:
            witness = [row for row in rows if 5 <= row["decision"] <= 8]
    previous_hashes = {str(path): digest(path) for path in prior_paths}
    write_json(output / "historical-witness.json", {
        "contexts": {"A": A, "B": B}, "selection_seeds": list(range(601, 609)),
        "episodes": old_episodes, "seed601_decisions5_to8": witness,
        "previous_input_sha256": previous_hashes,
        "claim": "user-proposed pair supported by prior training behavior; no held-out reward used",
    })
    source_hashes = {name: digest(ROOT / name) for name in
                     ("STEP6.md", "joint.py", "experience.py", "run.py", "perception.py",
                      "wolfe_binding.py", "tools.json", "initial_examples.jsonl")}
    frozen_hashes = previous_hashes | {str(ROOT / name): value for name, value in source_hashes.items()}
    frozen_hashes.update({str(parent_state): PARENT_SHA256, str(legacy_state): LEGACY_SHA256,
                          str(ROOT.parent / "wolfe.c"): build["source_sha256"],
                          str(ROOT / ".build" / build["library"]): build["library_sha256"]})
    write_json(output / "manifest.json", {
        "mechanism": "joint_two_context_correction_grid_with_fixed_other22",
        "contexts": {"A": A, "B": B}, "action_order": names,
        "grid_order": "A outer, B inner; tools.json order",
        "parent_state_sha256": PARENT_SHA256, "legacy_state_sha256": LEGACY_SHA256,
        "selection_seeds": SELECTION_SEEDS, "evaluation_seeds": EVALUATION_SEEDS,
        "selection_perception": "no-effects",
        "evaluation_conditions": {"parent": "no-effects", "selected": "no-effects", "legacy_reference": "legacy"},
        "criterion": "summed unmodified return; parent wins ties; first improving grid maximum wins",
        "loop_windows": "overlapping consecutive input triples; same-object BAB compares both B focus ids",
        "survival": "alive after exactly 128 decisions and 512 elapsed tics",
        "engine": build, "source_hashes": source_hashes, "previous_input_sha256": previous_hashes,
        "historical_witness_sha256": digest(output / "historical-witness.json"),
    })
    (output / "protocol.md").write_bytes((ROOT / "STEP6.md").read_bytes())

    proposals, eligible = [], []
    for a_index, a_tool in enumerate(names):
        for b_index, b_tool in enumerate(names):
            index = a_index * len(names) + b_index
            name = f"pair-{index:02d}-{a_tool}-{b_tool}"
            folder = output / name
            folder.mkdir()
            state = folder / "memory.json"
            shutil.copyfile(parent_state, state)
            if digest(state) != PARENT_SHA256:
                raise RuntimeError("A proposal did not start from the declared parent")
            pair = (a_tool, b_tool)
            records = [{"text": text, "tool": tool, "arguments": {}}
                       for text, tool in zip((A, B), pair)]
            with open_model(state) as model:
                for record in records:
                    model.correct(record)
                table = decision_table(model)
            verdict = eligibility(state, table, parent_table, parent_records, names, pair)
            write_json(folder / "requested-pair.json", {"A": a_tool, "B": b_tool, "corrections_in_order": records})
            write_json(folder / "table.json", table)
            write_json(folder / "eligibility.json", verdict)
            write_json(folder / "changed-decisions.json", verdict["changed_decisions"])
            proposal = {"name": name, "index": index, "pair": list(pair),
                        "parent_matching_control": pair == ("turn_left", "turn_right"),
                        "state_sha256": digest(state), **verdict}
            frozen_hashes[str(state)] = proposal["state_sha256"]
            proposals.append(proposal)
            if verdict["eligible"]:
                eligible.append({"name": name, "pair": pair, "state": state, "table": table})
    write_json(output / "preflight.json", {"proposals": proposals, "proposal_count": len(proposals),
                                           "eligible_count": len(eligible)})
    common = {"proposal_count": len(proposals), "eligible_count": len(eligible)}
    if not eligible:
        return finish(output, {**common, "mechanism": "NO_REPRESENTABLE_PAIR", "benefit": "NOT_RUN"}, frozen_hashes)

    candidates = [{"name": "parent", "state": parent_state, "table": parent_table}] + eligible
    selection = []
    for candidate in candidates:
        folder = output / "selection" / candidate["name"]
        folder.mkdir(parents=True)
        episodes = []
        for seed in SELECTION_SEEDS:
            episode = fixed_episode(folder / f"seed{seed}", seed, candidate["state"], "no-effects", candidate["table"])
            episodes.append(episode)
            print(f"selection {candidate['name']} seed={seed} reward={episode['reward']} kills={episode['kills']}", flush=True)
        entry = {"name": candidate["name"], "episodes": episodes,
                 "reward_sum": sum(episode["reward"] for episode in episodes),
                 "state_sha256": digest(candidate["state"]), "totals": totals(episodes)}
        write_json(folder / "results.json", entry)
        selection.append(entry)
    winner = 0
    for index in range(1, len(selection)):
        if selection[index]["reward_sum"] > selection[winner]["reward_sum"]:
            winner = index
    chosen = candidates[winner]
    sealed = {**common, "selected": chosen["name"], "selected_index": winner,
              "adopted": winner != 0, "selection": selection,
              "selected_pair": list(chosen["pair"]) if winner else None,
              "selection_state_sha256": selection[winner]["state_sha256"],
              "preflight_sha256": digest(output / "preflight.json")}
    write_json(output / "selection.json", sealed)
    if winner == 0:
        return finish(output, {**common, "mechanism": "NO_ADOPTION", "benefit": "NOT_RUN",
                               "reason": "No eligible proposal strictly improved the parent"}, frozen_hashes)

    selected_state = output / "selected-memory.json"
    shutil.copyfile(chosen["state"], selected_state)
    if digest(selected_state) != sealed["selection_state_sha256"]:
        raise RuntimeError("Selected memory does not match sealed selection")
    restarted_path = output / "restarted-table.json"
    subprocess.run([sys.executable, str(ROOT / "experience.py"), "table", "--state", str(selected_state),
                    "--output", str(restarted_path)], cwd=ROOT, check=True)
    restarted = read_json(restarted_path)
    restart_identical = restarted == chosen["table"]
    verdict = eligibility(selected_state, restarted, parent_table, parent_records, names, chosen["pair"])
    target_changed = any(change["input"] in {A, B} for change in verdict["changed_decisions"])
    mechanism = restart_identical and verdict["eligible"] and target_changed
    write_json(output / "restart-gate.json", {"restart_table_identical": restart_identical,
                                              "target_decision_changed": target_changed, **verdict})
    if not mechanism:
        return finish(output, {**common, "mechanism": "FAIL", "benefit": "NOT_RUN",
                               "selected": chosen["name"], "reason": "Selected child failed the restart/structural gate"}, frozen_hashes)
    frozen_hashes[str(selected_state)] = sealed["selection_state_sha256"]
    pairs = []
    for seed in EVALUATION_SEEDS:
        episodes = {}
        for name, state, mode, table in (("parent", parent_state, "no-effects", parent_table),
                                         ("selected", selected_state, "no-effects", restarted),
                                         ("legacy_reference", legacy_state, "legacy", legacy_table)):
            folder = output / "evaluation" / name
            folder.mkdir(parents=True, exist_ok=True)
            episodes[name] = fixed_episode(folder / f"seed{seed}", seed, state, mode, table)
        delta = episodes["selected"]["reward"] - episodes["parent"]["reward"]
        legacy_delta = episodes["selected"]["reward"] - episodes["legacy_reference"]["reward"]
        pairs.append({"seed": seed, **episodes, "reward_delta": delta, "legacy_reward_delta": legacy_delta})
        print(f"evaluation seed={seed} parent={episodes['parent']['reward']} selected={episodes['selected']['reward']} legacy={episodes['legacy_reference']['reward']} delta={delta}", flush=True)
    write_json(output / "evaluation.json", pairs)
    mean_delta = sum(pair["reward_delta"] for pair in pairs) / len(pairs)
    improved = sum(pair["reward_delta"] > 0 for pair in pairs)
    worsened = sum(pair["reward_delta"] < 0 for pair in pairs)
    result = {
        **common, "mechanism": "PASS", "benefit": "PASS" if mean_delta > 0 and improved > worsened else "FAIL",
        "selected": chosen["name"], "selected_pair": list(chosen["pair"]),
        "selected_state_sha256": digest(selected_state), "restart_table_identical": restart_identical,
        "structural_eligibility": verdict["checks"], "paired_mean_reward_delta": mean_delta,
        "improved_seeds": improved, "worsened_seeds": worsened, "tied_seeds": len(pairs) - improved - worsened,
        "legacy_reference_comparison": {
            "paired_mean_reward_delta": sum(pair["legacy_reward_delta"] for pair in pairs) / len(pairs),
            "improved_seeds": sum(pair["legacy_reward_delta"] > 0 for pair in pairs),
            "worsened_seeds": sum(pair["legacy_reward_delta"] < 0 for pair in pairs),
            "tied_seeds": sum(pair["legacy_reward_delta"] == 0 for pair in pairs),
            "used_for_selection_or_benefit_gate": False},
        "totals": {name: totals([pair[name] for pair in pairs])
                   for name in ("parent", "selected", "legacy_reference")},
        "claim": "one user-proposed two-context policy intervention; reward does not establish survival or aiming",
    }
    return finish(output, result, frozen_hashes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--legacy-memory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.previous, args.legacy_memory, args.output))
