"""One predeclared revision of an acquired decision, with 23 choices fixed."""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

from experience import (ROOT, changed_decisions, decision_table, digest,
                        open_model, write_json)
from joint import finish, fixed_episode, read_json, totals, trajectory


TARGET = "healthmid ammopresent sceneempty"
PARENT_SHA256 = "ef1a98d8093aac0c8eed9c82d4903ab6fab9656e222a9a9f9258760d7352d369"
LEGACY_SHA256 = "7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005"
SELECTION_SEEDS = tuple(range(1001, 1009))
EVALUATION_SEEDS = tuple(range(1101, 1117))


def target_stats(rows, target=TARGET):
    result = {"visits": 0, "shoot_calls": 0, "rounds_consumed": 0,
              "health_lost": 0, "kills_gained": 0, "longest_consecutive_run": 0}
    consecutive = 0
    for row in rows:
        if row["input"] != target:
            consecutive = 0
            continue
        consecutive += 1
        result["visits"] += 1
        result["shoot_calls"] += row["action"] == "shoot"
        before, after = row["before"]["variables"], row["after"]["variables"]
        result["rounds_consumed"] += max(0, before["ammo"] - after["ammo"])
        result["health_lost"] += max(0, before["health"] - after["health"])
        result["kills_gained"] += max(0, after["kills"] - before["kills"])
        result["longest_consecutive_run"] = max(result["longest_consecutive_run"], consecutive)
    return result


def target_totals(episodes):
    result = {key: sum(episode["target"][key] for episode in episodes)
              for key in ("visits", "shoot_calls", "rounds_consumed", "health_lost", "kills_gained")}
    result["longest_consecutive_run"] = max(
        (episode["target"]["longest_consecutive_run"] for episode in episodes), default=0)
    return result


def episode(output, seed, state, perception, table, target=TARGET):
    receipt = fixed_episode(output, seed, state, perception, table)
    receipt["target"] = target_stats(trajectory(output / "trajectory.jsonl"), target)
    return receipt


def descriptive_totals(episodes):
    return {**totals(episodes), "target": target_totals(episodes)}


def eligibility(state, table, parent_table, parent_records, names, action, *, target=TARGET, correction_index=1):
    changes = changed_decisions(parent_table, table)
    outside = [change for change in changes if change["input"] != target]
    response = next(row["response"] for row in table if row["input"] == target)
    expected = list(parent_records)
    record = {"text": target, "tool": action, "arguments": {}}
    if correction_index is None:
        expected.append(record)
    else:
        expected[correction_index] = record
    memory = read_json(state)
    checks = {
        "requested_action_realized": response["status"] == "call"
        and response["calls"] == [{"name": action, "arguments": {}}],
        "other_23_decisions_fixed": not outside,
        ("exact_five_corrections" if correction_index is None else "exact_four_corrections"):
            memory["corrections"] == expected,
        "zero_reward_counters": memory["tools"] == {
            name: {"accepted": 0, "rejected": 0} for name in names},
    }
    return {"eligible": all(checks.values()), "checks": checks,
            "outside_changes": outside, "changed_decisions": changes,
            "actual_target": {key: response[key] for key in ("status", "calls")}}


def run(previous, legacy_source, output, *, step8=False):
    previous, legacy_source, output = previous.resolve(), legacy_source.resolve(), output.resolve()
    if (output == previous or previous in output.parents
            or output == legacy_source.parent or legacy_source.parent in output.parents):
        raise ValueError("Output must be outside prior evidence directories")
    target, correction_index, protocol = TARGET, 1, "STEP7.md"
    selection_seeds, evaluation_seeds = SELECTION_SEEDS, EVALUATION_SEEDS
    historical_seeds = tuple(range(801, 809))
    parent_filename, table_filename = "selected-memory.json", "restarted-table.json"
    control_action = "shoot"
    witness_ranges = {805: (102, 127), 806: (79, 112)}
    if step8:
        target, correction_index, protocol = "healthmid ammopresent scenecenter", None, "STEP8.md"
        selection_seeds, evaluation_seeds = tuple(range(1201, 1209)), tuple(range(1301, 1317))
        historical_seeds = tuple(range(1001, 1009))
        parent_filename, table_filename = "parent-memory.json", "parent-table.json"
        control_action = "move_forward"
        witness_ranges = {1002: (46, 50), 1006: (107, 110)}
    parent_source = previous / parent_filename
    if digest(parent_source) != PARENT_SHA256 or digest(legacy_source) != LEGACY_SHA256:
        raise ValueError("This step requires its declared four-correction parent and legacy memory")
    old_manifest = read_json(previous / "manifest.json")
    old_selection = read_json(previous / "selection.json")
    if (old_selection["selection_state_sha256"] != PARENT_SHA256
            or old_manifest["selection_seeds"] != list(historical_seeds)):
        raise ValueError("Previous selection does not identify the declared parent")
    archive_paths = []
    if step8:
        if (old_selection["selected"] != "parent" or old_selection["adopted"] is not False
                or read_json(previous / "result.json")["mechanism"] != "NO_ADOPTION"):
            raise ValueError("STEP8 requires STEP7's retained parent after NO_ADOPTION")
        archive = previous.with_name(previous.name + "-source")
        archive_manifest = read_json(archive / "manifest.json")
        if (archive_manifest["source_hashes"] != old_manifest["source_hashes"]
                or archive_manifest["engine"] != old_manifest["engine"]):
            raise ValueError("Archived STEP7 source manifest does not match its experiment")
        archive_paths = [archive / "manifest.json", previous / "result.json"]
        for name, expected in old_manifest["source_hashes"].items():
            archived = archive / name
            if digest(archived) != expected:
                raise ValueError(f"Archived STEP7 source changed: {name}")
            archive_paths.append(archived)
    inherited_sources = ("joint.py", "experience.py", "run.py", "perception.py",
                         "wolfe_binding.py", "tools.json", "initial_examples.jsonl")
    for name in inherited_sources:
        if digest(ROOT / name) != old_manifest["source_hashes"][name]:
            raise ValueError(f"Inherited input changed: {name}")
    build = read_json(ROOT / ".build/build.json")
    if (build != old_manifest["engine"]
            or digest(ROOT.parent / "wolfe.c") != build["source_sha256"]):
        raise ValueError("The C core/build receipt changed")
    names = [tool["name"] for tool in read_json(ROOT / "tools.json")["tools"]]
    parent_records = read_json(parent_source)["corrections"]
    if (len(names) != 6 or len(parent_records) != 4
            or (step8 and any(record["text"] == target for record in parent_records))
            or (not step8 and parent_records[1]["text"] != target)):
        raise ValueError("The action or inherited correction surface changed")
    output.mkdir(parents=True, exist_ok=False)
    parent_state, legacy_state = output / "parent-memory.json", output / "legacy-memory.json"
    shutil.copyfile(parent_source, parent_state)
    shutil.copyfile(legacy_source, legacy_state)
    if digest(parent_state) != PARENT_SHA256 or digest(legacy_state) != LEGACY_SHA256:
        raise RuntimeError("Copied memories do not match their declared hashes")
    with open_model(parent_state) as model:
        parent_table = decision_table(model)
    if len(parent_table) != 24 or parent_table != read_json(previous / table_filename):
        raise RuntimeError("The parent's full response table changed")
    with open_model(legacy_state) as model:
        legacy_table = decision_table(model)
    write_json(output / "parent-table.json", parent_table)
    write_json(output / "legacy-table.json", legacy_table)
    parent_calls = {row["input"]: row["response"] for row in parent_table}
    if (parent_calls[target]["status"] != "call"
            or parent_calls[target]["calls"] != [{"name": control_action, "arguments": {}}]):
        raise RuntimeError("The declared acquired reaction changed")

    prior_paths = [parent_source, legacy_source, previous / "manifest.json",
                   previous / "selection.json", previous / table_filename, *archive_paths]
    old_episodes, witnesses = [], {}
    for seed in historical_seeds:
        path = previous / "selection" / old_selection["selected"] / f"seed{seed}" / "trajectory.jsonl"
        prior_paths.append(path)
        rows = trajectory(path)
        if any(row["response"] != parent_calls[row["input"]] for row in rows):
            raise RuntimeError("Historical training responses differ from the parent")
        old_episodes.append({"seed": seed, "trajectory": str(path), "decisions": len(rows),
                             "target": target_stats(rows, target)})
        if seed in witness_ranges:
            first, last = witness_ranges[seed]
            witnesses[f"seed{seed}_decisions{first}_to{last}"] = [
                row for row in rows if first <= row["decision"] <= last]
    previous_hashes = {str(path): digest(path) for path in prior_paths}
    write_json(output / "historical-witness.json", {
        "target": target, "selection_seeds": list(historical_seeds), "episodes": old_episodes,
        "decisions": sum(item["decisions"] for item in old_episodes),
        "target_totals": target_totals(old_episodes), "witnesses": witnesses,
        "previous_input_sha256": previous_hashes,
        "claim": ("diagnosed uncorrected context from retained-parent training; no held-out reward used" if step8
                  else "diagnosed acquired reaction from old training; no held-out reward used"),
    })
    source_hashes = {name: digest(ROOT / name) for name in (protocol, "revise.py", *inherited_sources)}
    frozen = previous_hashes | {str(ROOT / name): value for name, value in source_hashes.items()}
    frozen.update({str(parent_state): PARENT_SHA256, str(legacy_state): LEGACY_SHA256,
                   str(ROOT.parent / "wolfe.c"): build["source_sha256"],
                   str(ROOT / ".build" / build["library"]): build["library_sha256"]})
    write_json(output / "manifest.json", {
        "mechanism": ("append_one_context_correction_with_fixed_other23" if step8
                      else "revise_one_acquired_correction_with_fixed_other23"), "target": target,
        "correction_index": len(parent_records) if correction_index is None else correction_index,
        "action_order": names, "parent_state_sha256": PARENT_SHA256,
        "legacy_state_sha256": LEGACY_SHA256, "selection_seeds": selection_seeds,
        "evaluation_seeds": evaluation_seeds, "selection_perception": "no-effects",
        "evaluation_conditions": {"parent": "no-effects", "selected": "no-effects", "legacy_reference": "legacy"},
        "criterion": "summed unmodified return; parent wins ties; first improving maximum in tools.json order",
        "target_statistics": "only decisions whose input equals target; sum positive ammo/health decreases and kill increases; longest run is the maximum within any episode",
        "legacy_target_interpretation": "the same input text is encoded using legacy perception, so its observed scene differs from no-effects",
        "survival": "alive after exactly 128 decisions and 512 elapsed tics",
        "engine": build, "source_hashes": source_hashes, "previous_input_sha256": previous_hashes,
        "historical_witness_sha256": digest(output / "historical-witness.json"),
    })
    (output / "protocol.md").write_bytes((ROOT / protocol).read_bytes())

    proposals, eligible = [], []
    for index, action in enumerate(names):
        folder = output / f"candidate-{index}-{action}"
        folder.mkdir()
        state = folder / "memory.json"
        shutil.copyfile(parent_state, state)
        if digest(state) != PARENT_SHA256:
            raise RuntimeError("A candidate did not start from the declared parent")
        record = {"text": target, "tool": action, "arguments": {}}
        with open_model(state) as model:
            model.correct(record)
            table = decision_table(model)
        verdict = eligibility(state, table, parent_table, parent_records, names, action,
                              target=target, correction_index=correction_index)
        write_json(folder / "correction.json", record)
        write_json(folder / "table.json", table)
        write_json(folder / "eligibility.json", verdict)
        write_json(folder / "changed-decisions.json", verdict["changed_decisions"])
        proposal = {"name": action, "index": index, "parent_matching_control": action == control_action,
                    "state_sha256": digest(state), **verdict}
        frozen[str(state)] = proposal["state_sha256"]
        proposals.append(proposal)
        if verdict["eligible"]:
            eligible.append({"name": action, "state": state, "table": table})
    common = {"proposal_count": len(proposals), "eligible_count": len(eligible)}
    write_json(output / "preflight.json", {**common, "proposals": proposals})
    if not eligible:
        return finish(output, {**common, "mechanism": "NO_REPRESENTABLE_ACTION", "benefit": "NOT_RUN"}, frozen)

    candidates = [{"name": "parent", "state": parent_state, "table": parent_table}] + eligible
    selection = []
    for candidate in candidates:
        folder = output / "selection" / candidate["name"]
        folder.mkdir(parents=True)
        episodes = []
        for seed in selection_seeds:
            receipt = episode(folder / f"seed{seed}", seed, candidate["state"], "no-effects", candidate["table"], target)
            episodes.append(receipt)
            print(f"selection {candidate['name']} seed={seed} reward={receipt['reward']} kills={receipt['kills']}", flush=True)
        entry = {"name": candidate["name"], "episodes": episodes,
                 "reward_sum": sum(item["reward"] for item in episodes),
                 "state_sha256": digest(candidate["state"]), "totals": descriptive_totals(episodes)}
        write_json(folder / "results.json", entry)
        selection.append(entry)
    winner = 0
    for index in range(1, len(selection)):
        if selection[index]["reward_sum"] > selection[winner]["reward_sum"]:
            winner = index
    chosen = candidates[winner]
    sealed = {**common, "selected": chosen["name"], "selected_index": winner,
              "adopted": winner != 0, "selection": selection,
              "selection_state_sha256": selection[winner]["state_sha256"],
              "preflight_sha256": digest(output / "preflight.json")}
    write_json(output / "selection.json", sealed)
    if winner == 0:
        return finish(output, {**common, "mechanism": "NO_ADOPTION", "benefit": "NOT_RUN",
                               "reason": "No eligible revision strictly improved the parent"}, frozen)

    selected_state = output / "selected-memory.json"
    shutil.copyfile(chosen["state"], selected_state)
    if digest(selected_state) != sealed["selection_state_sha256"]:
        raise RuntimeError("Selected memory differs from sealed selection")
    restarted_path = output / "restarted-table.json"
    subprocess.run([sys.executable, str(ROOT / "experience.py"), "table", "--state", str(selected_state),
                    "--output", str(restarted_path)], cwd=ROOT, check=True)
    restarted = read_json(restarted_path)
    identical = restarted == chosen["table"]
    verdict = eligibility(selected_state, restarted, parent_table, parent_records, names, chosen["name"],
                          target=target, correction_index=correction_index)
    target_changed = any(change["input"] == target for change in verdict["changed_decisions"])
    write_json(output / "restart-gate.json", {"restart_table_identical": identical,
                                              "target_decision_changed": target_changed, **verdict})
    if not identical or not verdict["eligible"] or not target_changed:
        return finish(output, {**common, "mechanism": "FAIL", "benefit": "NOT_RUN",
                               "selected": chosen["name"], "reason": "Selected revision failed the restart/structural gate"}, frozen)
    frozen[str(selected_state)] = sealed["selection_state_sha256"]
    pairs = []
    for seed in evaluation_seeds:
        episodes = {}
        for name, state, mode, table in (("parent", parent_state, "no-effects", parent_table),
                                         ("selected", selected_state, "no-effects", restarted),
                                         ("legacy_reference", legacy_state, "legacy", legacy_table)):
            folder = output / "evaluation" / name
            folder.mkdir(parents=True, exist_ok=True)
            episodes[name] = episode(folder / f"seed{seed}", seed, state, mode, table, target)
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
        "selected": chosen["name"], "selected_state_sha256": digest(selected_state),
        "restart_table_identical": identical, "structural_eligibility": verdict["checks"],
        "paired_mean_reward_delta": mean_delta, "improved_seeds": improved,
        "worsened_seeds": worsened, "tied_seeds": len(pairs) - improved - worsened,
        "legacy_reference_comparison": {
            "paired_mean_reward_delta": sum(pair["legacy_reward_delta"] for pair in pairs) / len(pairs),
            "improved_seeds": sum(pair["legacy_reward_delta"] > 0 for pair in pairs),
            "worsened_seeds": sum(pair["legacy_reward_delta"] < 0 for pair in pairs),
            "tied_seeds": sum(pair["legacy_reward_delta"] == 0 for pair in pairs),
            "used_for_selection_or_benefit_gate": False},
        "totals": {name: descriptive_totals([pair[name] for pair in pairs])
                   for name in ("parent", "selected", "legacy_reference")},
        "legacy_target_interpretation": "target visits in legacy use legacy scene encoding, not no-effects",
        "claim": ("one uncorrected context acquired an association; target-window outcomes are not causal action credit" if step8
                  else "one acquired reaction revised; target-associated damage is not causal action credit"),
    }
    return finish(output, result, frozen)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--legacy-memory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--step8", action="store_true", help="Append the declared mid-health centered-object association")
    args = parser.parse_args()
    raise SystemExit(run(args.previous, args.legacy_memory, args.output, step8=args.step8))
