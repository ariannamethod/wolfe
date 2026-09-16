# WOLFE Doom log

Newest entries first. Preserve failed episodes and their actual outcomes.

## 2026-09-17 — publish the joint-memory step and two actual game frames

Oleg authorized publishing STEP6, adding two screenshots to the README, and
continuing the investigation. The sealed sources, protocol, inherited inputs,
and selected memory were checked before committing STEP6 as `873c09f`.

The main README now shows two unedited 320 × 240 frames from the same selected
evaluation episode, seed 914, copied byte-for-byte into `assets/doom/`.
After 16 calls the player has one kill and health 100; after 128 calls it has
eight kills and health 84. The frame source, action indices, state hash, and
image hashes are recorded in `assets/doom/README.md`. The captions distinguish
the fixed horizon from game completion. These frames illustrate one success;
the six evaluation deaths remain in the experiment record.

Only existing gameplay images were copied; no new episodes were run for the
screenshots. Both relative README image links and exact source-image equality
were checked. No video or generated artwork was introduced.

## 2026-09-17 — the left-object reaction breaks the observed aiming loop

At Oleg's request, the preceding two steps were committed and pushed to main:
[`ce48fdc`](https://github.com/ariannamethod/wolfe/commit/ce48fdcd3dbe2b8bf77cec8847647d383d310057)
preserves the failed perception intervention;
[`76a3c71`](https://github.com/ariannamethod/wolfe/commit/76a3c71fb5d5be5963e571cf5c13821bde87a75f)
records the inherited adaptation. Each commit contains unique Quote and Method
lines, and its experimental sources match the corresponding original receipt.

The incoming independent audit examined the adapted parent's training seeds
601–608 before new work: 828 decisions, 104 overlapping A-B-A windows and
99 B-A-B windows, with the same focus object at both B observations in 95.
Here A is `healthhigh ammopresent sceneempty`, B is
`healthhigh ammopresent sceneleft`. On seed 601, decisions 5–8 alternate
turn_left/turn_right, holding position while the angle returns between
19.33594 and 33.39844 degrees. The visible Demon has the same id, 3.
This confirms the loop Oleg and chat Astra proposed investigating. A was an
acquired correction; B was still a random-prior association.

[STEP6.md](STEP6.md) was declared before candidates or new games. It allows
replacing A and adding B in a descendant, while preserving the first two
correction records and every other runtime decision. The existing C correction
API already supports replacement; no C change was required. A separate reader
checked the new `joint.py` implementation before the single command:

```sh
.venv/bin/python joint.py --previous runs/adaptation1 \
  --legacy-memory runs/perception1/memory.json --output runs/joint1
```

All 36 proposals realize both requested calls, keep the other 22 decisions
fixed, contain exactly the expected four correction records, and retain zero
feedback counters. Each starts from an identical three-correction parent.
All proposals and complete response tables are retained, including poor ones.

Selection returns, summed over seeds 801–808; rows are A, columns B:

| A / B | turn_left | turn_right | move_forward | strafe_left | strafe_right | shoot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| turn_left | 35 | 5 | 6 | **50** | 13 | 12 |
| turn_right | 7 | 7 | 7 | 8 | 6 | 7 |
| move_forward | 0 | 0 | 0 | 0 | 0 | 0 |
| strafe_left | 2 | 2 | 2 | 2 | 2 | 2 |
| strafe_right | 7 | 7 | 7 | 7 | 7 | 8 |
| shoot | 3 | 4 | 2 | 3 | 2 | 2 |

The unmodified parent scores 5. The parent-matching turn_left/turn_right
control reproduces its behavior. The unique maximum is turn_left/strafe_left;
selection was sealed before evaluation. The winner keeps A unchanged and
changes only B from turn_right to strafe_left. Joint search was permitted,
but this outcome does not demonstrate that revising both associations was
necessary. Its state hash is
`ef1a98d8093aac0c8eed9c82d4903ab6fab9656e222a9a9f9258760d7352d369`.
All 24 complete responses match after a fresh-process restart. The first two
acquired choices survive, along with the third search choice.

Fresh evaluation, seeds 901–916, with unmodified reward and horizon:

| Seed | Filtered parent reward | Joint child reward | Legacy reference reward |
| --- | ---: | ---: | ---: |
| 901 | 2 | 2 | 1 |
| 902 | 0 | 3 | 0 |
| 903 | 2 | 6 | 1 |
| 904 | 1 | 3 | 1 |
| 905 | 1 | 5 | 0 |
| 906 | 0 | 5 | 0 |
| 907 | 0 | 4 | 1 |
| 908 | 1 | 7 | 1 |
| 909 | 0 | 7 | 1 |
| 910 | 0 | 3 | 2 |
| 911 | 1 | 3 | 1 |
| 912 | 0 | 7 | 1 |
| 913 | 1 | 7 | 1 |
| 914 | 2 | 8 | 1 |
| 915 | 0 | 6 | 1 |
| 916 | 0 | 8 | 1 |

| Aggregate | Filtered parent | Joint child | Legacy reference |
| --- | ---: | ---: | ---: |
| Reward | 11 | 84 | 14 |
| Kills | 24 | 90 | 18 |
| Deaths | 13 | 6 | 4 |
| Alive at the fixed horizon | 3 | 10 | 12 |
| Decisions | 1,595 | 1,894 | 1,957 |
| A visits | 376 | 383 | 235 |
| B visits | 355 | 671 | 41 |
| A-B-A windows | 256 | 0 | 3 |
| B-A-B windows | 245 | 0 | 1 |
| Same-object B-A-B windows | 240 | 0 | 1 |
| A-B-A per 100 decisions | 16.0502 | 0 | 0.1533 |

The mechanism and predeclared reward-benefit gates pass: 15 improvements,
zero regressions, one tie against the filtered parent; mean paired difference
+4.5625. Against legacy, all 16 returns improve, mean difference +4.375.
Legacy remains a separate reference, never a selection or adoption criterion.

The observed alternating windows disappear despite more visits to both
contexts. Raw seed 901 shows what replaces them:

```text
decisions 3–5: empty -> turn_left; angle 0 -> 33.39844
decision 6: Demon id 3 at screen x=0, width=11 -> strafe_left
  angle stays 33.39844; position (0,0) -> (-3.75922,5.69835)
decisions 7–18: same Demon remains left -> strafe_left
  its screen center advances from x=4.5 to x=101.5
decision 19: same Demon reaches center (x=113,width=28) -> shoot
decision 20: shoot; kills 1 -> 2, ammo 25 -> 24, reward +1
decision 21: empty -> turn_left; search resumes
```

The existing centered-object shoot choice now follows lateral movement.
These traces support resolution of this particular high-health aiming loop
on the measured seeds, not general aiming competence. No short-history
feature was needed for this step; no claim is made about all perceptual aliases.

Survival is substantially better than the current filtered parent's, but
**has not recovered the legacy sample's level**: six deaths versus four.
Reward ties and gains still hide survival losses. On seed 901, the parent
survives with two kills; the child gets three kills and dies, leaving equal
reward 2. On seeds 904, 907, 910, and 911, the child dies where legacy survives;
on 905 and 906 it survives where legacy dies.

Seed 901 also exposes a remaining boundary. Health falls 76 -> 72 at decision
60 while the Demon is still left. At 61 the unchanged mid-health left choice
switches to shoot. Decisions 63–71 fire with an empty filtered scene, preserving
the angle while health eventually falls 46 -> 12; decision 72 dies during the
low-health strafe_right choice. This is an observed failure sequence, not proof
that one later correction would cure all six deaths. At the other extreme,
seed 914 reaches the 128-decision horizon with eight kills and health 84;
its actual final image is `runs/joint1/evaluation/selected/seed914/frame_128.png`.

All 344 real episodes and 32,757 decisions are retained in `runs/joint1/`.
The 2,955 prior artifact/source files remain byte-identical, with no additions
or removals in their sealed directories. C source, library, tools, original
corpus, perception, reward, and action timing retain their declared hashes.
An independent reader reconstructed all 344 episodes from raw records, checking
focus/input, full C responses, buttons, state continuity, tics, rewards, and
all structural/restart conditions. The parent-matching control reproduces all
eight parent selection histories. Its new `independent-audit.json` confirms
the selection, fresh comparisons, loop counts, and survival counterexamples
without changing any existing evidence; no discrepancies were found.
No additional pair, generation, reward change, or history feature was tried
after evaluation. The passed step returns to Oleg with the survival deficit
and all six deaths visible.

## 2026-09-16 — inherited memory adapts to the filtered scene

Oleg authorized continuing the adaptation investigation and repairing the
mechanism if necessary. The incoming raw audit reproduced STEP4's failed
benefit: reward 13 → 3, one improvement, eleven regressions, four ties. Its
seven exact source files were archived in `runs/perception1-source/` before
editing the shared experience driver. The failed result was not rewritten.
No commit or push was requested for this turn.

[STEP5.md](STEP5.md) declared one new memory association under unchanged
no-effects perception. Context selection used the older historical-input
receipt from training seeds 301–308, not STEP4's evaluation rewards. In each
of the eight trajectories, the first changed choice at an uncorrected input
was decision 3, `healthhigh ammopresent sceneempty`. The context therefore
received all eight votes. The old legacy action did not prescribe the target:
all six actions competed through new game outcomes.

A separate reader checked the declared contract and implementation before
the command was run once:

```sh
.venv/bin/python experience.py adapt --previous runs/perception1 --output runs/adaptation1
```

Selection, seeds 601–608, with no-effects perception throughout:

| Candidate third association | Return sum |
| --- | ---: |
| Unmodified filtered parent | 2 |
| turn_left | 11 |
| turn_right | 8 |
| move_forward | 2 |
| strafe_left | 2 |
| strafe_right | 2 |
| shoot | 6 |

`turn_left` won. Its memory contains the two original correction records plus
`healthhigh ammopresent sceneempty → turn_left`. The old corrected inputs still
choose shoot; all counters remain zero. Exactly one of the 24 choices changes,
from strafe_right to turn_left. The complete table matches after process
restart. The selected state hash is
`31fa2dc243e9aca6c7bfce5444a06c203fa08db178de8349ec8b99fc359b9b92`.

Selection was sealed before seeds 701–716. Each evaluation seed ran the
filtered parent, filtered child, and the old parent under legacy perception.
The legacy reference did not influence selection or the primary benefit gate.

| Seed | Filtered parent | Filtered child | Legacy reference |
| --- | ---: | ---: | ---: |
| 701 | 0 | 1 | 1 |
| 702 | 0 | 0 | 1 |
| 703 | 0 | 1 | 1 |
| 704 | 0 | 2 | 0 |
| 705 | 0 | 1 | 1 |
| 706 | 0 | 0 | 0 |
| 707 | 0 | 0 | 1 |
| 708 | 0 | 0 | 1 |
| 709 | 1 | 0 | 1 |
| 710 | 0 | 2 | 1 |
| 711 | 0 | 1 | 0 |
| 712 | 4 | 1 | 1 |
| 713 | 0 | 2 | 1 |
| 714 | 0 | 1 | 0 |
| 715 | 0 | 1 | 1 |
| 716 | 0 | 0 | 0 |

| Aggregate | Filtered parent | Filtered child | Legacy reference |
| --- | ---: | ---: | ---: |
| Reward | 5 | 13 | 11 |
| Kills | 20 | 28 | 16 |
| Deaths | 15 | 15 | 5 |

The adaptation mechanism and benefit gates pass. Against the filtered parent,
nine seeds improve, two worsen, five tie; mean paired return difference +0.5.
The two regressions remain: seed 709 falls 1 → 0; seed 712 falls 4 → 1, losing
two kills and changing a horizon-surviving episode into a death.

Against the legacy reference, five seeds improve, four worsen, seven tie;
mean difference +0.125. The child's sample total reward exceeds the reference
by two points, but it dies ten more times. This does not establish recovery
of the legacy policy's survival or general superiority.

Raw behavior on seed 701:

```text
decision 2: healthhigh ammopresent scenecenter, focus MarineChainsawVzd
  shoot; first kill, reward +1
decision 3: healthhigh ammopresent sceneempty, focus null
  turn_left; angle 0 -> 7.03125
decision 4: same empty input -> turn_left; angle 7.03125 -> 19.33594
decision 5: same empty input -> turn_left; angle 19.33594 -> 33.39844
decision 6: healthhigh ammopresent sceneleft, focus Demon
  turn_right; angle 33.39844 -> 19.33594
decision 7: empty again -> turn_left; angle 19.33594 -> 33.39844
decision 80: healthlow ammopresent sceneleft, focus Demon
  shoot; second kill, reward +1
decision 100: healthlow ammopresent sceneempty -> strafe_right
  health 12 -> 0; death, reward -1
```

The new turn exposes another actor, but an old opposite-turn association
still causes aiming oscillation. That remaining behavior is visible beside
the aggregate gain. Seed 710 reaches the horizon alive with two kills; most
other child episodes still end in death. No extra correction was added after
seeing these outcomes.

All 104 episodes and 10,376 decisions remain in `runs/adaptation1/`, including
the six candidates, context witnesses, full tables, restart, and three-way
evaluation. All 1,954 prior artifact/source files remain byte-identical, with
no files added or removed inside their sealed directories. Both acquired
choices survived the change; neither the C core nor perception was edited
in this step.

An independent reader reconstructed focus and input from raw labels, checked
every full C response, button, state boundary, tic count, and return, and
confirmed selection, memory retention, restart, and both comparisons. The
strafe-right control reproduces all parent selection histories. In every
parent-child evaluation pair, the first action difference is decision 3 from
the same raw state and input: strafe_right → turn_left. Both regressions and
the survival deficit against legacy were confirmed. The passed gate ends
this turn and returns the result to Oleg.

## 2026-09-16 — removing transient labels hurts the frozen learned policy

Step 3 was committed and pushed at Oleg's request as
[`911a5b4`](https://github.com/ariannamethod/wolfe/commit/911a5b4805090a525cbbd933757f1ef2191e02e5),
with unique `Quote:` and `Method:` lines. Its source/protocol hashes, raw
selection/evaluation returns, selected state, and restart table were checked
before publication. Arduino is a future user intention, outside this step.

[STEP4.md](STEP4.md) declared one intervention before implementation or games:
exclude exactly Blood and BulletPuff from the largest-label observation, keep
the two-correction memory frozen, and compare against legacy on seeds 501–516.
The existing DoomPlayer exclusion and all size/tie/bin rules remain unchanged.
All other objects remain eligible; the filter does not classify live enemies.

The incoming diagnosis used only old selection seeds 301–308. Of 1,005 raw
decisions, 549 focused on effects: Blood 30, BulletPuff 519. All 549 lacked
another eligible nonplayer label. Those effects kept the scene nonempty;
the evidence did not show an effect displacing a visible enemy. Offline replay
of these states changes 549 inputs and 545 choices under the frozen table.
In 240 cases the alternative changes move_forward to shoot, because the
acquired mid-health empty-scene correction already favors shooting.

A separate reader checked the exact intervention and paired-run code before
new data. Command, run once:

```sh
.venv/bin/python perception.py --previous runs/memory2 --output runs/perception1
```

The selected memory remains
`7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005`.
All 24 full C responses match the previous table. No correction or feedback
was applied. Each condition uses fresh processes and the same memory, seed,
actions, reward, and 128-decision horizon. The protocol, source hashes, and
offline comparison were sealed before the new games.

| Seed | Legacy reward | No-effects reward | Difference |
| --- | ---: | ---: | ---: |
| 501 | 1 | 0 | -1 |
| 502 | 1 | 0 | -1 |
| 503 | 1 | 0 | -1 |
| 504 | 0 | 2 | 2 |
| 505 | 2 | 0 | -2 |
| 506 | 1 | 0 | -1 |
| 507 | 1 | 0 | -1 |
| 508 | 0 | 0 | 0 |
| 509 | 0 | 0 | 0 |
| 510 | 0 | 0 | 0 |
| 511 | 1 | 0 | -1 |
| 512 | 1 | 0 | -1 |
| 513 | 1 | 0 | -1 |
| 514 | 1 | 0 | -1 |
| 515 | 1 | 1 | 0 |
| 516 | 1 | 0 | -1 |

| Aggregate | Legacy | No-effects |
| --- | ---: | ---: |
| Reward | 13 | 3 |
| Kills | 17 | 18 |
| Deaths | 4 | 15 |
| Shoot calls | 967 | 511 |
| Ammunition consumed | 375 | 159 |
| Elapsed game tics | 8,082 | 5,194 |

The perception mechanism passes: the filter changes real actions from matched
raw states in all 16 pairs while preserving the C decision table. The benefit
gate **fails**: one seed improves, eleven worsen, four tie; mean paired reward
difference -0.625. Lower ammunition consumption accompanies shorter episodes
and does not establish better shooting efficiency.

Raw first divergence on seed 501, decision 3, tic 22:

```text
same state: health 100, ammo 25, angle 0, kills 1, position (0,0)
only nonplayer label: Blood id=2, x=159, y=120, width=1, height=1
legacy:    healthhigh ammopresent scenecenter -> shoot
no-effects: healthhigh ammopresent sceneempty -> strafe_right
```

The legacy episode reaches tic 522 alive, health 14, ammo 0, reward +1. The
filtered episode dies at tic 302, health -8, ammo 18, reward 0. This identifies
the first direct effect of the observation change; it does not assign all
later damage to that single action.

The opposing case is also retained: seed 504 improves from one kill and death
to two kills and reaching the horizon alive, reward 0 → 2. Seed 515 gets an
extra kill but now dies, leaving reward tied at +1. No seed or outcome was
discarded to make the comparison uniform.

This rejects the proposed filter as an improvement for the existing frozen
policy on these episodes. It does not test whether a policy learned under
the filtered representation could do better. Its acquired action associations
were selected under the original observation function; changing that function
changes when those associations are invoked.

All 32 episodes and 3,324 decisions remain in `runs/perception1/`, alongside
full tables, the offline 1,005-state comparison, focused labels, paired first
divergences, and actual frames. The 1,642-file inventory of both prior memory
experiments remains byte-identical, with no files added or removed.
An independent reader reconstructed focus and input directly from raw labels,
without importing the adapter, and checked every full C response, button,
record boundary, tic count, return, and ammo decrease. All 16 pairs have
identical physical histories before their first shoot-to-strafe divergence.
Hashes, the unchanged response table, both gate verdicts, the sole improvement,
and the remaining counterexamples were confirmed without additional games.

Legacy remains the default. The two-name filter remains available explicitly
as an experiment. No retraining, other exclusions, changed seeds, longer
horizon, or hardware work followed the failed gate. Return the turn to Oleg.

## 2026-09-16 — a second association survives beside the first

At Oleg's request, step 2 was committed and pushed as
[`4531cd5`](https://github.com/ariannamethod/wolfe/commit/4531cd5f43e9c080aa6098a6764e4d91067c49b6),
with a unique `Quote:` and `Method:` line. Before continuing, its source hashes,
selection returns, paired evaluation returns, and full restart table were
rechecked from the files. All agreed with the previous report.

The next mechanism was declared in [STEP3.md](STEP3.md) before new candidates
or episodes: inherit the selected memory, use old training visitation to pick
one uncorrected context, and let new game returns select its action. A separate
reader checked the contract and implementation before the run.

Only the parent's old selection seeds 101–108 chose the context. Among their
615 decisions, the already corrected high-health center context had 208 visits
and was excluded. `healthmid ammopresent sceneempty` had the largest remaining
count, 154. Of these, 118 came from two episodes. Seed 108 repeated its existing
`strafe_right` decision 73 times without changing its viewing angle; health
fell from 64 to 12 and kills stayed at one. Visitation identifies a place to
intervene, not a causal verdict on individual actions.

The old trajectories also exposed a separate observation limitation: 182 of
208 high-health center observations focused on Blood or BulletPuff labels.
These effects can sustain shooting after an enemy dies. Perception was kept
unchanged for this experiment; its limitations remain visible in the receipts.

Command, run once:

```sh
.venv/bin/python experience.py continue --previous runs/memory1 --output runs/memory2
```

Each of six children inherited a separate copy of the same parent memory and
added one correction. Selection on seeds 301–308 produced:

| Candidate second association | Return sum |
| --- | ---: |
| Unmodified parent | 5 |
| turn_left | 5 |
| turn_right | 2 |
| move_forward | 3 |
| strafe_left | 5 |
| strafe_right | 5 |
| shoot | 6 |

The unique winner was `shoot`, by one reward point. Selection was sealed before
opening evaluation seeds. The aggregate win includes selection regressions:
seed 303 falls from return 1 to 0, and seed 305 from 3 to 2. The selected
memory contains exactly these records:

```json
[
  {"text":"healthhigh ammopresent scenecenter","tool":"shoot","arguments":{}},
  {"text":"healthmid ammopresent sceneempty","tool":"shoot","arguments":{}}
]
```

Selected state SHA-256:
`7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005`.
All reliability counters remain zero. The first acquired decision still calls
`shoot`; exactly one other choice changes, mid-health empty from `strafe_right`
to `shoot`. All 24 complete responses match after process restart. The shared
C field is rebuilt through its existing correction API; core code is unchanged.

Evaluation seeds 401–416, in order, produced paired reward differences:

```text
seed:   401 402 403 404 405 406 407 408 409 410 411 412 413 414 415 416
delta:   +1   0  +1   0   0   0   0   0  +1  +1  +1   0  +1   0   0  +1
```

| Evaluation measure | Parent | Selected child |
| --- | ---: | ---: |
| Total reward | 4 | 11 |
| Kills | 19 | 18 |
| Deaths | 15 | 7 |
| Reached the fixed 128-decision horizon alive | 1 | 9 |

Seven returns improve, nine tie, none worsen; paired mean difference +0.4375.
The benefit is fewer deaths within the fixed horizon, with one fewer kill.
Seed 415 exposes the tradeoff: the parent kills two and dies, while the child
kills one and reaches the horizon alive; both receive reward +1. This is not
an improvement on every possible measure.

Raw paired behavior on seed 401 is identical through the state before decision
42, tic 178: health 68, ammo 15, angle 0, kills 1, input
`healthmid ammopresent sceneempty`. Then:

```text
parent decision 42: strafe_right; tic 178 -> 182
child  decision 42: shoot;        tic 178 -> 182
child  decision 43: shoot; ammo 15 -> 14; kills remain 1
parent decision 107: health 8 -> -16; dead=true; total reward 0
child  decision 127: health 8; ammo 0; dead=false; total reward 1
```

The child's final real frame shows a nearby wall, not a demonstration of
competent navigation. It has spent all ammunition in that episode. On seed
406 both policies still die: the child lasts longer but earns the same return.
All these behaviors remain in the raw evidence.

Both declared gates pass: accumulated memory retains the first decision and
survives restart; the selected child improves the declared reward comparison
on fresh seeds. The result is bounded to this scenario and horizon. It does
not establish self-play or open-ended learning, and the kill count decreased.

All 88 episodes and 9,190 decisions are preserved in `runs/memory2/`, alongside
context counts, candidate memories, full tables, selection, and evaluation.
An independent reader reconstructed observations from raw labels and variables,
checked every full response against its frozen C table and literal buttons,
and recomputed trajectories, tics, reward, kills, and deaths. The same-action
control reproduces all eight parent selection histories. Selection and restart
precede evaluation; both gates and the survival/kill tradeoff were confirmed.
The complete 792-file inventory of `runs/memory1/` remains byte-identical, with
no added or removed files. No second context, perception change, or further
generation was attempted after the result. Return the turn to Oleg.

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
