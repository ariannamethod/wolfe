"""One real Doom episode controlled by the unchanged C WOLFE engine."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import zlib

import vizdoom as vzd

from wolfe_binding import Wolfe


ROOT = Path(__file__).resolve().parent
QUANTUM = 4
BUTTONS = {
    "turn_left": vzd.Button.TURN_LEFT,
    "turn_right": vzd.Button.TURN_RIGHT,
    "move_forward": vzd.Button.MOVE_FORWARD,
    "strafe_left": vzd.Button.MOVE_LEFT,
    "strafe_right": vzd.Button.MOVE_RIGHT,
    "shoot": vzd.Button.ATTACK,
}
VARIABLES = {
    "health": vzd.GameVariable.HEALTH,
    "ammo": vzd.GameVariable.SELECTED_WEAPON_AMMO,
    "x": vzd.GameVariable.POSITION_X,
    "y": vzd.GameVariable.POSITION_Y,
    "angle": vzd.GameVariable.ANGLE,
    "kills": vzd.GameVariable.KILLCOUNT,
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot(game):
    state = game.get_state()
    labels = []
    if state is not None:
        for label in state.labels:
            labels.append({"id": int(label.object_id), "name": label.object_name,
                           "x": int(label.x), "y": int(label.y),
                           "width": int(label.width), "height": int(label.height)})
    return {
        "tic": int(game.get_episode_time()),
        "terminal": bool(game.is_episode_finished()),
        "dead": bool(game.is_player_dead()),
        "variables": {name: float(game.get_game_variable(variable))
                      for name, variable in VARIABLES.items()},
        "labels": labels,
    }


def focus_label(raw, perception="legacy"):
    """Select the original largest label, optionally excluding two effects."""
    if perception not in {"legacy", "no-effects"}:
        raise ValueError(f"Unknown perception mode: {perception}")
    excluded = {"DoomPlayer"}
    if perception == "no-effects":
        excluded.update({"Blood", "BulletPuff"})
    visible = [item for item in raw["labels"] if item["name"] not in excluded]
    return max(visible, key=lambda obj: (obj["width"] * obj["height"], -obj["id"]),
               default=None)


def observation(raw, width, perception="legacy"):
    values = raw["variables"]
    health = "healthlow" if values["health"] <= 25 else "healthmid" if values["health"] <= 75 else "healthhigh"
    ammo = "ammopresent" if values["ammo"] > 0 else "ammoabsent"
    item = focus_label(raw, perception)
    view = "sceneempty"
    if item is not None:
        center = item["x"] + item["width"] / 2
        view = "sceneleft" if center < width / 3 else "sceneright" if center > 2 * width / 3 else "scenecenter"
    return f"{health} {ammo} {view}"


def history_input(text, health, previous_health, mode="none"):
    """Optionally expose a health decrease already observed before this call."""
    if mode not in {"none", "previous-damage"}:
        raise ValueError(f"Unknown history mode: {mode}")
    if mode == "previous-damage" and previous_health is not None and health < previous_health:
        return text + " damagerecent"
    return text


def action_vector(response):
    """Translate a validated choice literally; never select a replacement tool."""
    calls = response.get("calls")
    status = response.get("status")
    if status in {"no_call", "ambiguous", "missing_arguments"}:
        if calls:
            raise ValueError("Non-call response unexpectedly contains calls")
        return "idle", [False] * len(BUTTONS), "policy_abstention"
    if status != "call" or not isinstance(calls, list) or len(calls) != 1:
        raise ValueError(f"Invalid WOLFE response: {response}")
    call = calls[0]
    name = call.get("name")
    if name not in BUTTONS or call.get("arguments") != {}:
        raise ValueError(f"Invalid primitive call: {call}")
    return name, [name == tool for tool in BUTTONS], None


def save_frame(game, path):
    state = game.get_state()
    if state is None:
        return False
    rgb = state.screen_buffer
    height, width, channels = rgb.shape
    if channels != 3:
        raise ValueError("Expected RGB24 framebuffer")
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
    rows = b"".join(b"\0" + rgb[row].tobytes() for row in range(height))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")
    path.write_bytes(png)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--decisions", type=int, default=128)
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--state", type=Path, help="Load a fixed WOLFE memory; never update it during an episode")
    parser.add_argument("--perception", choices=["legacy", "no-effects"], default="legacy",
                        help="Select the largest label, optionally excluding Blood and BulletPuff")
    parser.add_argument("--history", choices=["none", "previous-damage"], default="none",
                        help="Optionally report a health decrease since the previous decision")
    args = parser.parse_args()
    if args.decisions <= 0:
        parser.error("--decisions must be positive")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    build = json.loads((ROOT / ".build/build.json").read_text())
    library = ROOT / ".build" / build["library"]
    if digest(library) != build["library_sha256"]:
        raise ValueError("WOLFE library changed since the build receipt")
    config = Path(vzd.scenarios_path) / "defend_the_center.cfg"
    game = vzd.DoomGame()
    try:
        game.load_config(str(config))
        game.set_mode(vzd.Mode.PLAYER)
        game.set_seed(args.seed)
        game.set_window_visible(args.visible)
        game.set_sound_enabled(False)
        game.set_screen_format(vzd.ScreenFormat.RGB24)
        game.set_labels_buffer_enabled(True)
        game.set_objects_info_enabled(False)
        game.set_sectors_info_enabled(False)
        game.set_available_buttons(list(BUTTONS.values()))
        game.set_available_game_variables(list(VARIABLES.values()))
        game.set_episode_timeout(QUANTUM * args.decisions + 10)
        metadata = {
            "stage": "fixed_policy_episode", "seed": args.seed,
            "decision_quantum": QUANTUM, "max_decisions": args.decisions,
            "prior_seed": 1729, "learning": False, "vizdoom": vzd.__version__,
            "perception": args.perception,
            "excluded_names": (["DoomPlayer", "Blood", "BulletPuff"]
                               if args.perception == "no-effects" else ["DoomPlayer"]),
            "state_sha256": digest(args.state) if args.state is not None else None,
            "wolfe": build, "buttons": [button.name for button in BUTTONS.values()],
            "scenario_sha256": digest(config.with_suffix(".wad")),
            "scenario_config_sha256": digest(config),
            "inputs": {name: digest(ROOT / name) for name in
                       ["tools.json", "initial_examples.jsonl", "STEP1.md", "run.py", "wolfe_binding.py"]},
        }
        if args.history != "none":
            metadata["history"] = args.history
        (output / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
        game.init()
        save_frame(game, output / "frame_000.png")
        actions = Counter()
        changed = 0
        elapsed = 0
        records = 0
        previous_health = None
        with Wolfe(library, ROOT / "tools.json", ROOT / "initial_examples.jsonl", state=args.state) as wolf, \
                (output / "trajectory.jsonl").open("w") as journal, \
                (output / "trace.txt").open("w") as trace:
            while not game.is_episode_finished() and records < args.decisions:
                before = snapshot(game)
                base_input = observation(before, game.get_screen_width(), args.perception)
                text = history_input(base_input, before["variables"]["health"],
                                     previous_health, args.history)
                response = wolf.call(text)
                name, buttons, fallback = action_vector(response)
                reward = float(game.make_action(buttons, QUANTUM))
                after = snapshot(game)
                actual_tics = after["tic"] - before["tic"]
                record = {"decision": records, "before": before, "input": text,
                          "focus": focus_label(before, args.perception),
                          "response": response, "action": name,
                          "buttons": buttons, "executor_fallback": fallback,
                          "requested_tics": QUANTUM, "elapsed_tics": actual_tics,
                          "reward": reward, "after": after}
                if args.history != "none":
                    record["base_input"] = base_input
                    record["history"] = {
                        "mode": args.history, "previous_health": previous_health,
                        "damagerecent": text != base_input,
                    }
                previous_health = before["variables"]["health"]
                journal.write(json.dumps(record, sort_keys=True) + "\n")
                journal.flush()
                line = (f"{records:03d} tic {before['tic']}->{after['tic']} {text} "
                        f"=> {name} ammo {before['variables']['ammo']}->{after['variables']['ammo']} "
                        f"angle {before['variables']['angle']:.2f}->{after['variables']['angle']:.2f} "
                        f"health {before['variables']['health']}->{after['variables']['health']} "
                        f"reward {reward}\n")
                trace.write(line)
                trace.flush()
                print(line, end="", flush=True)
                actions[name] += 1
                elapsed += actual_tics
                if name != "idle" and any(before["variables"][key] != after["variables"][key]
                                          for key in ["x", "y", "angle", "ammo"]):
                    changed += 1
                records += 1
                if records in {1, 16, 64, args.decisions}:
                    save_frame(game, output / f"frame_{records:03d}.png")
        summary = {"decisions": records, "actions": dict(actions),
                   "elapsed_tics": elapsed, "calls_with_player_variable_change": changed,
                   "total_reward": float(game.get_total_reward()), "final": snapshot(game),
                   "gate": "PASS" if changed > 0 and elapsed > 0 else "FAIL",
                   "claim": "environment connection only; no learning performed"}
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
        return 0 if summary["gate"] == "PASS" else 1
    finally:
        game.close()


if __name__ == "__main__":
    raise SystemExit(main())
