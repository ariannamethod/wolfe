# WOLFE Doom log

Newest entries first. Preserve failed episodes and their actual outcomes.

## 2026-09-16 — first real episode, environment connection passes

Oleg chose `wolfe/doom/` inside the existing repository. Initial preparation
started in a sibling staging directory; authored files were moved before the
first game run. A fresh virtual environment was installed at the final path.

Unchanged parent engine: `809ea0dd0a5d5aae93e7c6782b6dc2016779e6b8`.
`wolfe.c` SHA-256:
`dea0df2c4f81d64543b927e3f6e4d1a23bdf585500230a135f24a73f20529fda`.
C99 shared-library build with `-Wall -Wextra -Wpedantic` succeeded on macOS arm64, Python 3.14.4,
ViZDoom 1.3.0. No pretrained weights, optimizer, external model, or learning
process was used. The initial corpus is the declared arbitrary seed-1729 prior.

Before running, a separate reader inspected observation encoding, action
translation, the C binding, and the stated gate. No blocking mismatch was found.

Command, run once:

```sh
.venv/bin/python run.py --output runs/seed17
```

Real `defend_the_center` episode, game seed 17:

- 39 decisions; 154 elapsed tics, from tic 10 to death at tic 164.
- Calls: 5 turn-right, 19 forward, 12 strafe-right, 2 strafe-left, 1 turn-left.
- No shooting; ammunition stayed 26. No kills. Final health -14; reward -1.
- All 39 calls coincided with a change in recorded player position or angle.
  The receipt exposes these values; it does not attribute every displacement
  exclusively to the requested action (the game also has momentum and damage).
- The final call lasted two tics because the episode ended during its quantum.

Representative raw transitions from `trajectory.jsonl`:

```text
decision 0: healthhigh ammopresent scenecenter
  {"name":"turn_right","arguments":{}}
  tic 10 -> 14; angle 0 -> 352.96875008218194
decision 3: healthhigh ammopresent sceneright
  {"name":"move_forward","arguments":{}}
  position (0,0) -> (5.9388427734375,-3.9112091064453125)
decision 31: healthmid ammopresent sceneright
  {"name":"strafe_left","arguments":{}}
  health 68 -> 64; tic 134 -> 138
decision 38: healthlow ammopresent sceneright
  {"name":"turn_left","arguments":{}}
  health 6 -> -14; tic 162 -> 164; terminal=true
```

The declared environment-connection gate passed. This was a losing episode
under a fixed arbitrary prior, not evidence of learning or tactical skill.
The policy was not revised after seeing this outcome. All run receipts and
three real frames remain in `runs/seed17/`.

The independent reader subsequently recomputed all counts from the raw JSONL,
checked every call-to-button mapping and all 38 inter-record boundaries, and
verified the source/input/library hashes against the manifest. No mismatch
was found. The final partial quantum and losing outcome were preserved exactly.

Next hand: choose one mechanism by which experienced consequences change a
context-specific action preference, with a preserved frozen starting policy.
No experience-update step or self-play batch was started after this gate.
No commit, push, or public repository was created for this step.
