# WOLFE Doom log

Newest entries first. Preserve failed episodes and their actual outcomes.

## 2026-09-16 — one remembered association selected by game consequences

Step 1 was committed and pushed at Oleg's request as
[`221c028`](https://github.com/ariannamethod/wolfe/commit/221c028aaf93efde25aa8f212b923c43e06957df).
Its commit includes the unique `Quote:` and `Method:` lines. This second step
is a new bounded experiment. The C source, library, action definitions,
observation bins, initial corpus, scenario, and episode horizon are unchanged.

[STEP2.md](STEP2.md) declared the mechanism, seeds, selection criterion,
restart requirement, two gates, and stopping rule before candidates or game
data were generated. A separate reader checked that the implementation
followed that declaration before the run.

Command, run once:

```sh
.venv/bin/python experience.py run --output runs/memory1
```

Six independent candidates each changed one corpus association through the
existing C correction API. The observation was fixed in advance:
`healthhigh ammopresent scenecenter`, the first input of the earlier seed-17
episode. The entire policy received its episode return; individual actions
were not labelled as successful because their episode did well.

Selection on seeds 101–108, sum of unmodified game reward:

| Candidate association | Return sum |
| --- | ---: |
| Unchanged ancestor | -7 |
| turn_left | -8 |
| turn_right | -7 |
| move_forward | -6 |
| strafe_left | -7 |
| strafe_right | -8 |
| shoot | 2 |

The experiment selected `shoot`, sealed the selection, and copied its memory.
The selected state contains exactly one correction and zero accepted/rejected
counters for all tools:

```json
{"text":"healthhigh ammopresent scenecenter","tool":"shoot","arguments":{}}
```

State SHA-256:
`9f53271cde84088f58c62cb9e2e95eec54e99f4634b0cd8c74349c5ed30eb0cc`.
The complete 24-response table matched after loading this file in a new
process. Exactly one action choice changed versus the ancestor:
`healthhigh ammopresent scenecenter`: `turn_right` → `shoot`. A correction
rebuilds the shared field, so a one-choice effect was observed here, not
assumed from the size of the edit.

Fresh evaluation used only this selected memory and the ancestor:

| Seed | Ancestor return | Selected return | Difference |
| --- | ---: | ---: | ---: |
| 201 | -1 | 0 | 1 |
| 202 | -1 | 0 | 1 |
| 203 | -1 | 0 | 1 |
| 204 | -1 | 0 | 1 |
| 205 | -1 | 1 | 2 |
| 206 | -1 | 1 | 2 |
| 207 | -1 | 0 | 1 |
| 208 | -1 | 2 | 3 |
| 209 | -1 | 0 | 1 |
| 210 | -1 | 0 | 1 |
| 211 | -1 | 0 | 1 |
| 212 | 1 | 0 | -1 |
| 213 | -1 | 0 | 1 |
| 214 | -1 | 1 | 2 |
| 215 | 2 | 0 | -2 |
| 216 | -1 | 0 | 1 |

Return sums: -11 → +5; paired mean difference +1.0. Fourteen seeds improved,
two worsened, none tied. Kills: 4 → 19. Deaths: 15 → 14; remaining episodes
reached the 128-decision horizon. These are comparisons of separate episodes
with matched seeds, not head-to-head wins.

Raw behavior, evaluation seed 201:

```text
ancestor decision 0, healthhigh ammopresent scenecenter:
  turn_right; tic 10 -> 14; angle 0 -> 352.96875008218194
selected decision 0, same observation:
  shoot; tic 10 -> 14; ammo 26 -> 26; reward 0
selected decision 1, same observation:
  shoot; tic 14 -> 18; ammo 26 -> 26; reward 0
selected decision 2, same observation:
  shoot; tic 18 -> 22; ammo 26 -> 25; kills 0 -> 1; reward +1
selected decision 114, healthlow ammopresent sceneempty:
  strafe_right; health 20 -> 0; reward -1; dead=true
```

The initial attack calls take effect through Doom's weapon timing; a call is
not an instantaneous shot. The selected policy gets an early kill but still
dies. On seed 215, the ancestor instead gets two kills and reaches the horizon;
the selected policy gets one kill and dies after 44 decisions. Seed 212 is
also worse. Both counterexamples are preserved alongside the improvements.

The declared memory-mechanism and fresh-seed-benefit gates both passed. An
independent reader recomputed all 88 episode returns from 6,255 raw decisions,
checked action/button mappings, record continuity, summaries and source hashes,
and verified the selected memory, zero counters, restart table, selection, and
paired results. No mismatch was found.

This establishes a small consequence-selected persistent policy change on
one scenario. The fixed observation and all six candidate actions were
supplied by the experiment; the reward chose among them. Every game action
still came from C WOLFE. It is not spontaneous discovery of the observation
space, a general Doom skill claim, or multiplayer self-play. Fourteen of the
sixteen selected-policy episodes still ended in death.

All candidate states, complete tables, selection and evaluation receipts,
trajectories, and real frames remain in `runs/memory1/`. Nothing was rerun to
remove a poor outcome. This step ends here and returns to Oleg; no second
generation, new context, changed seeds, or multiplayer phase was started.

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
