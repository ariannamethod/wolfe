"""Declare the physical action vocabulary and a fixed arbitrary starting table."""

import itertools
import json
from pathlib import Path
import random


ACTIONS = {
    "turn_left": "Hold the left rotation button for one decision quantum",
    "turn_right": "Hold the right rotation button for one decision quantum",
    "move_forward": "Hold the forward movement button for one decision quantum",
    "strafe_left": "Hold the left sideways movement button for one decision quantum",
    "strafe_right": "Hold the right sideways movement button for one decision quantum",
    "shoot": "Hold the attack button for one decision quantum",
}


def main():
    root = Path(__file__).resolve().parent
    tools = {"tools": [
        {"name": name, "description": description,
         "parameters": {"type": "object", "properties": {}, "required": [],
                        "additionalProperties": False}}
        for name, description in ACTIONS.items()
    ]}
    states = list(itertools.product(
        ["healthlow", "healthmid", "healthhigh"],
        ["ammoabsent", "ammopresent"],
        ["sceneempty", "sceneleft", "scenecenter", "sceneright"],
    ))
    actions = list(ACTIONS) * 4
    random.Random(1729).shuffle(actions)
    records = [{"text": " ".join(state), "tool": action, "arguments": {}}
               for state, action in zip(states, actions)]
    # Refuse replacement: the run's starting policy is an explicit input.
    with (root / "tools.json").open("x") as stream:
        stream.write(json.dumps(tools, indent=2) + "\n")
    with (root / "initial_examples.jsonl").open("x") as stream:
        for record in records:
            stream.write(json.dumps(record) + "\n")
    print(f"Wrote {len(tools['tools'])} tools and {len(records)} initial associations; seed 1729")


if __name__ == "__main__":
    main()
