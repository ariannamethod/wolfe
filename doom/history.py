"""One declared previous-health bit and one fixed-exterior correction (STEP10)."""

import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

from experience import ROOT, changed_decisions, digest, observations, open_model, write_json
from joint import finish, read_json, trajectory


MODE = "previous-damage"
SUFFIX = " damagerecent"
BASE_TARGET = "healthmid ammopresent sceneempty"
TARGET = BASE_TARGET + SUFFIX
PARENT_SHA256 = "ef1a98d8093aac0c8eed9c82d4903ab6fab9656e222a9a9f9258760d7352d369"
SELECTION_SEEDS = tuple(range(1601, 1609))
EVALUATION_SEEDS = tuple(range(1701, 1717))
TOTAL_KEYS = ("reward", "kills", "dead", "survived_horizon", "decisions", "elapsed_tics",
              "target_visits", "base_target_visits", "history_flagged_decisions",
              "history_bit_transitions")


def decision_table(model):
    texts = observations()
    if len(texts) != 24 or len(set(texts)) != 24 or BASE_TARGET not in texts:
        raise ValueError("The declared 24-input corpus changed")
    return [{"input": text, "response": model.call(text)}
            for text in texts + [text + SUFFIX for text in texts]]


def choice(response):
    return {key: response[key] for key in ("status", "calls")}


def eligibility(state, table, parent_table, parent_records, names, action):
    changes = changed_decisions(parent_table, table)
    outside = [item for item in changes if item["input"] != TARGET]
    response = next(row["response"] for row in table if row["input"] == TARGET)
    memory = read_json(state)
    checks = {
        "requested_action_realized": choice(response) == {
            "status": "call", "calls": [{"name": action, "arguments": {}}]},
        "other_47_decisions_fixed": not outside,
        "exact_five_corrections": memory["corrections"] == parent_records + [
            {"text": TARGET, "tool": action, "arguments": {}}],
        "zero_reward_counters": memory["tools"] == {
            name: {"accepted": 0, "rejected": 0} for name in names},
    }
    return {"eligible": all(checks.values()), "checks": checks,
            "outside_changes": outside, "changed_decisions": changes,
            "actual_target": choice(response)}


def screen_width(folder):
    png = (folder / "frame_000.png").read_bytes()
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Initial frame is not a PNG")
    return struct.unpack(">I", png[16:20])[0]


def episode(output, seed, state, table):
    from run import action_vector, focus_label, observation

    before_hash = digest(state)
    command = [sys.executable, str(ROOT / "run.py"), "--output", str(output),
               "--seed", str(seed), "--decisions", "128", "--state", str(state),
               "--perception", "no-effects", "--history", MODE]
    with output.with_suffix(".console.txt").open("x") as stream:
        process = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    if process.returncode not in {0, 1} or not (output / "summary.json").is_file():
        raise RuntimeError(f"Episode failed; preserved output: {output}")
    if digest(state) != before_hash:
        raise RuntimeError("Frozen memory changed during gameplay")
    manifest = read_json(output / "manifest.json")
    if (manifest["history"] != MODE or manifest["perception"] != "no-effects"
            or manifest["state_sha256"] != before_hash or manifest["seed"] != seed
            or manifest["decision_quantum"] != 4 or manifest["max_decisions"] != 128):
        raise RuntimeError("Episode manifest differs from the declared condition")
    rows = trajectory(output / "trajectory.jsonl")
    if not rows or len(rows) > 128:
        raise RuntimeError("Episode has no decisions or exceeds the fixed horizon")
    responses = {row["input"]: row["response"] for row in table}
    width = screen_width(output)
    previous_health, previous_bit = None, False
    flagged = transitions = target_visits = base_visits = 0
    for index, row in enumerate(rows):
        raw = row["before"]
        health = raw["variables"]["health"]
        base = observation(raw, width, "no-effects")
        # Reconstruct the bit independently from already observed health.
        bit = previous_health is not None and health < previous_health
        text = base + SUFFIX if bit else base
        expected_history = {"mode": MODE, "previous_health": previous_health,
                            "damagerecent": bit}
        if (row["decision"] != index or row["base_input"] != base or row["input"] != text
                or row["history"] != expected_history
                or row["focus"] != focus_label(raw, "no-effects")):
            raise RuntimeError("Live input does not follow causal previous-health encoding")
        if row["response"] != responses[text]:
            raise RuntimeError("Live response differs from its frozen 48-response table")
        if action_vector(row["response"]) != (row["action"], row["buttons"], row["executor_fallback"]):
            raise RuntimeError("Live action differs from its C response")
        if (row["requested_tics"] != 4
                or row["elapsed_tics"] != row["after"]["tic"] - raw["tic"]):
            raise RuntimeError("Live action timing differs from its raw snapshots")
        flagged += bit
        transitions += bit != previous_bit
        target_visits += text == TARGET
        base_visits += base == BASE_TARGET
        previous_health, previous_bit = health, bit
    summary = read_json(output / "summary.json")
    reward = sum(row["reward"] for row in rows)
    elapsed = sum(row["elapsed_tics"] for row in rows)
    final = rows[-1]["after"]
    if (reward != summary["total_reward"] or len(rows) != summary["decisions"]
            or elapsed != summary["elapsed_tics"] or final != summary["final"]):
        raise RuntimeError("Raw episode behavior differs from its summary")
    return {"seed": seed, "reward": reward, "kills": final["variables"]["kills"],
            "dead": final["dead"], "decisions": len(rows), "elapsed_tics": elapsed,
            "survived_horizon": not final["dead"] and elapsed == 512 and len(rows) == 128,
            "target_visits": target_visits, "base_target_visits": base_visits,
            "history_flagged_decisions": flagged, "history_bit_transitions": transitions,
            "perception": "no-effects", "history": MODE, "directory": str(output)}


def totals(episodes):
    return {key: sum(item[key] for item in episodes) for key in TOTAL_KEYS}


def historical_witness(previous, parent_table):
    from run import focus_label, observation

    responses = {row["input"]: row["response"] for row in parent_table}
    paths, visits, episodes = [], [], []
    flagged_positions = []
    for seed in range(1401, 1409):
        folder = previous / "selection" / "parent" / f"seed{seed}"
        path = folder / "trajectory.jsonl"
        paths.extend((path, folder / "frame_000.png"))
        rows, width = trajectory(path), screen_width(folder)
        prior = None
        count = flagged = 0
        for row in rows:
            base = observation(row["before"], width, "no-effects")
            if (base != row["input"] or row["response"] != responses[base]
                    or row["focus"] != focus_label(row["before"], "no-effects")):
                raise RuntimeError("Historical parent input, focus or complete response changed")
            previous_health = prior["before"]["variables"]["health"] if prior else None
            bit = previous_health is not None and row["before"]["variables"]["health"] < previous_health
            flagged += bit
            if base == BASE_TARGET:
                count += 1
                visits.append({"seed": seed, "trajectory": str(path), "previous": prior,
                               "current": row, "previous_health": previous_health,
                               "damagerecent": bit, "history_input": base + SUFFIX if bit else base})
                if bit:
                    flagged_positions.append((seed, row["decision"]))
            prior = row
        episodes.append({"seed": seed, "decisions": len(rows), "base_target_visits": count,
                         "history_flagged_decisions": flagged})
    if len(visits) != 17 or flagged_positions != [(1402, 47), (1402, 48), (1406, 73), (1406, 86)]:
        raise RuntimeError("The declared 17-visit/four-decrease training witness changed")
    return {"selection_seeds": list(range(1401, 1409)), "policy": "retained parent",
            "episodes": episodes, "base_target_visits": len(visits),
            "flagged_target_visits": len(flagged_positions), "visits": visits,
            "claim": "same base input with different previous health; an observable distinction, not proof of a better action"}, paths


def run(previous, output):
    previous, output = previous.resolve(), output.resolve()
    archive = previous.with_name(previous.name + "-source")
    if any(output == path or path in output.parents for path in (previous, archive)):
        raise ValueError("Output must be outside the incoming evidence and archived sources")
    parent_source = previous / "parent-memory.json"
    old_table = read_json(previous / "parent-table.json")
    old_manifest, old_selection = read_json(previous / "manifest.json"), read_json(previous / "selection.json")
    old_result, archive_manifest = read_json(previous / "result.json"), read_json(archive / "manifest.json")
    failed_hash = digest(previous / "selected-memory.json")
    if (digest(parent_source) != PARENT_SHA256 or old_manifest["parent_state_sha256"] != PARENT_SHA256
            or old_result["mechanism"] != "PASS" or old_result["benefit"] != "FAIL"
            or old_result["selected_state_sha256"] != failed_hash
            or old_selection["selection_state_sha256"] != failed_hash or failed_hash == PARENT_SHA256
            or old_result["selected"] != old_selection["selected"]
            or old_selection["adopted"] is not True
            or old_manifest["selection_seeds"] != list(range(1401, 1409))
            or old_manifest["evaluation_seeds"] != list(range(1501, 1517))):
        raise ValueError("STEP10 retains STEP9's four-record parent after failed fresh benefit")
    source_names = {"STEP9.md", "joint.py", "experience.py", "run.py", "perception.py",
                    "revise.py", "wolfe_binding.py", "tools.json", "initial_examples.jsonl"}
    if (set(old_manifest["source_hashes"]) != source_names
            or archive_manifest["source_hashes"] != old_manifest["source_hashes"]
            or archive_manifest["engine"] != old_manifest["engine"]):
        raise ValueError("The nine archived STEP9 sources do not match its manifest")
    prior_paths = [parent_source, previous / "parent-table.json", previous / "manifest.json",
                   previous / "selection.json", previous / "result.json",
                   previous / "selected-memory.json", archive / "manifest.json"]
    for name, expected in old_manifest["source_hashes"].items():
        if digest(archive / name) != expected:
            raise ValueError(f"Archived source changed: {name}")
        prior_paths.append(archive / name)
        if name != "run.py" and digest(ROOT / name) != expected:
            raise ValueError(f"Inherited input changed: {name}")
    build = read_json(ROOT / ".build/build.json")
    if (build != old_manifest["engine"] or digest(ROOT.parent / "wolfe.c") != build["source_sha256"]
            or digest(ROOT / ".build" / build["library"]) != build["library_sha256"]):
        raise ValueError("The frozen C core, library or build receipt changed")
    names = [item["name"] for item in read_json(ROOT / "tools.json")["tools"]]
    parent_records = read_json(parent_source)["corrections"]
    if (len(names) != 6 or names != old_manifest["action_order"] or len(parent_records) != 4
            or any(record["text"] == TARGET for record in parent_records)
            or [row["input"] for row in old_table] != observations()):
        raise ValueError("The inherited action, correction or observation surface changed")
    witness, witness_paths = historical_witness(previous, old_table)
    prior_paths.extend(witness_paths)
    previous_hashes = {str(path): digest(path) for path in prior_paths}
    source_hashes = {name: digest(ROOT / name) for name in sorted(source_names | {"STEP10.md", "history.py"})}
    frozen = previous_hashes | {str(ROOT / name): value for name, value in source_hashes.items()}
    frozen.update({str(ROOT.parent / "wolfe.c"): build["source_sha256"],
                   str(ROOT / ".build/build.json"): digest(ROOT / ".build/build.json"),
                   str(ROOT / ".build" / build["library"]): build["library_sha256"]})
    output.mkdir(parents=True, exist_ok=False)
    parent_state = output / "parent-memory.json"
    shutil.copyfile(parent_source, parent_state)
    if digest(parent_state) != PARENT_SHA256:
        raise RuntimeError("Copied parent does not match its declared hash")
    frozen[str(parent_state)] = PARENT_SHA256
    write_json(output / "historical-witness.json", {**witness, "previous_input_sha256": previous_hashes})
    write_json(output / "manifest.json", {
        "mechanism": "one_previous_health_bit_and_one_correction_with_fixed_other47",
        "history": MODE, "target": TARGET, "parent_state_sha256": PARENT_SHA256,
        "failed_step9_child_sha256": failed_hash, "failed_step9_child_promoted": False,
        "observation_order": "24 corpus inputs, then the same 24 with damagerecent suffix",
        "history_rule": "current predecision health < previous predecision health; initial false",
        "action_order": names, "selection_seeds": SELECTION_SEEDS, "evaluation_seeds": EVALUATION_SEEDS,
        "perception": "no-effects", "parent_matching_control": "shoot",
        "criterion": "summed unmodified reward; parent wins ties; first strict maximum in tools order",
        "survival": "alive after exactly 128 decisions and 512 elapsed tics",
        "statistics": "flagged decisions and adjacent bit transitions, including all contexts; target is flagged mid-health empty scene",
        "engine": build, "source_hashes": source_hashes, "previous_input_sha256": previous_hashes,
        "historical_witness_sha256": digest(output / "historical-witness.json")})
    (output / "protocol.md").write_bytes((ROOT / "STEP10.md").read_bytes())
    with open_model(parent_state) as model:
        parent_table = decision_table(model)
    write_json(output / "parent-table.json", parent_table)
    baseline_changes = [{"input": flagged["input"], "base_input": base["input"],
                         "before": choice(base["response"]), "after": choice(flagged["response"])}
                        for base, flagged in zip(parent_table[:24], parent_table[24:])
                        if choice(base["response"]) != choice(flagged["response"])]
    baseline = {"original_24_full_responses_match": parent_table[:24] == old_table,
                "flagged_24_choices_match": not baseline_changes}
    write_json(output / "baseline-gate.json", {"checks": baseline, "flagged_changes": baseline_changes})
    if not all(baseline.values()):
        return finish(output, {"mechanism": "BASELINE_CHANGED", "benefit": "NOT_RUN",
                               "proposal_count": 0, "eligible_count": 0, "parent_retained": True}, frozen)
    parent_target = next(row["response"] for row in parent_table if row["input"] == TARGET)
    if choice(parent_target) != {"status": "call", "calls": [{"name": "shoot", "arguments": {}}]}:
        raise RuntimeError("The declared parent-matching target is not shoot")

    proposals, eligible = [], []
    for index, action in enumerate(names):
        folder = output / f"candidate-{index}-{action}"
        folder.mkdir()
        state = folder / "memory.json"
        shutil.copyfile(parent_state, state)
        if digest(state) != PARENT_SHA256:
            raise RuntimeError("A proposal did not start from the declared parent")
        correction = {"text": TARGET, "tool": action, "arguments": {}}
        with open_model(state) as model:
            model.correct(correction)
            table = decision_table(model)
        verdict = eligibility(state, table, parent_table, parent_records, names, action)
        write_json(folder / "correction.json", correction)
        write_json(folder / "table.json", table)
        write_json(folder / "eligibility.json", verdict)
        proposals.append({"name": action, "index": index, "parent_matching_control": action == "shoot",
                          "state_sha256": digest(state), **verdict})
        frozen[str(state)] = digest(state)
        if verdict["eligible"]:
            eligible.append({"name": action, "state": state, "table": table})
    common = {"proposal_count": len(proposals), "eligible_count": len(eligible)}
    write_json(output / "preflight.json", {**common, "proposals": proposals})
    if not eligible or not any(item["name"] != "shoot" for item in eligible):
        reason = "NO_REPRESENTABLE_ACTION" if not eligible else "NO_ALTERNATIVE_ACTION"
        return finish(output, {**common, "mechanism": reason, "benefit": "NOT_RUN",
                               "parent_retained": True}, frozen)

    candidates = [{"name": "parent", "state": parent_state, "table": parent_table}] + eligible
    selection = []
    for candidate in candidates:
        folder = output / "selection" / candidate["name"]
        folder.mkdir(parents=True)
        episodes = []
        for seed in SELECTION_SEEDS:
            receipt = episode(folder / f"seed{seed}", seed, candidate["state"], candidate["table"])
            episodes.append(receipt)
            print(f"selection {candidate['name']} seed={seed} reward={receipt['reward']} kills={receipt['kills']}", flush=True)
        entry = {"name": candidate["name"], "episodes": episodes, "totals": totals(episodes),
                 "reward_sum": sum(item["reward"] for item in episodes), "state_sha256": digest(candidate["state"])}
        write_json(folder / "results.json", entry)
        selection.append(entry)
    winner = 0
    for index in range(1, len(selection)):
        if selection[index]["reward_sum"] > selection[winner]["reward_sum"]:
            winner = index
    chosen = candidates[winner]
    sealed = {**common, "selected": chosen["name"], "selected_index": winner, "adopted": winner != 0,
              "selection": selection, "selection_state_sha256": digest(chosen["state"]),
              "preflight_sha256": digest(output / "preflight.json")}
    write_json(output / "selection.json", sealed)
    if winner == 0:
        return finish(output, {**common, "mechanism": "NO_ADOPTION", "benefit": "NOT_RUN",
                               "parent_retained": True}, frozen)
    selected_state = output / "selected-memory.json"
    shutil.copyfile(chosen["state"], selected_state)
    if digest(selected_state) != sealed["selection_state_sha256"]:
        raise RuntimeError("Selected memory differs from sealed selection")
    frozen[str(selected_state)] = sealed["selection_state_sha256"]
    restarted_path = output / "restarted-table.json"
    subprocess.run([sys.executable, str(ROOT / "history.py"), "table", "--state", str(selected_state),
                    "--output", str(restarted_path)], cwd=ROOT, check=True)
    restarted = read_json(restarted_path)
    verdict = eligibility(selected_state, restarted, parent_table, parent_records, names, chosen["name"])
    identical = restarted == chosen["table"]
    changed = any(item["input"] == TARGET for item in verdict["changed_decisions"])
    write_json(output / "restart-gate.json", {"restart_table_identical": identical,
                                              "target_decision_changed": changed, **verdict})
    if not identical or not verdict["eligible"] or not changed:
        return finish(output, {**common, "mechanism": "FAIL", "benefit": "NOT_RUN",
                               "reason": "Selected child failed restart/structural gate",
                               "parent_retained": True}, frozen)
    pairs = []
    for seed in EVALUATION_SEEDS:
        episodes = {}
        for name, state, table in (("parent", parent_state, parent_table), ("selected", selected_state, restarted)):
            folder = output / "evaluation" / name
            folder.mkdir(parents=True, exist_ok=True)
            episodes[name] = episode(folder / f"seed{seed}", seed, state, table)
        delta = episodes["selected"]["reward"] - episodes["parent"]["reward"]
        pairs.append({"seed": seed, **episodes, "reward_delta": delta})
        print(f"evaluation seed={seed} parent={episodes['parent']['reward']} selected={episodes['selected']['reward']} delta={delta}", flush=True)
    write_json(output / "evaluation.json", pairs)
    mean_delta = sum(pair["reward_delta"] for pair in pairs) / len(pairs)
    improved, worsened = sum(pair["reward_delta"] > 0 for pair in pairs), sum(pair["reward_delta"] < 0 for pair in pairs)
    passed = mean_delta > 0 and improved > worsened
    return finish(output, {**common, "mechanism": "PASS", "benefit": "PASS" if passed else "FAIL",
                           "selected": chosen["name"], "selected_state_sha256": digest(selected_state),
                           "parent_retained": not passed, "restart_table_identical": identical,
                           "structural_eligibility": verdict["checks"], "paired_mean_reward_delta": mean_delta,
                           "improved_seeds": improved, "worsened_seeds": worsened,
                           "tied_seeds": len(pairs) - improved - worsened,
                           "totals": {name: totals([pair[name] for pair in pairs]) for name in ("parent", "selected")},
                           "non_tied_trajectories": [{"seed": pair["seed"], "reward_delta": pair["reward_delta"],
                                                      **{name: str(Path(pair[name]["directory"]) / "trajectory.jsonl")
                                                         for name in ("parent", "selected")}}
                                                     for pair in pairs if pair["reward_delta"] != 0],
                           "claim": "one externally remembered health decrease; local signals do not prove danger or causal action credit"}, frozen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    experiment = commands.add_parser("run")
    experiment.add_argument("--previous", type=Path, required=True)
    experiment.add_argument("--output", type=Path, required=True)
    table = commands.add_parser("table")
    table.add_argument("--state", type=Path, required=True)
    table.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "table":
        before = digest(args.state)
        with open_model(args.state) as model:
            result = decision_table(model)
        if digest(args.state) != before:
            raise RuntimeError("Frozen memory changed while reading its full table")
        write_json(args.output, result)
        return 0
    return run(args.previous, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
