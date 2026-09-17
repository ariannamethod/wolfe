# WOLFE Doom log

Newest entries first. Preserve failed episodes and their actual outcomes.

## 2026-09-17 — reject a global attention-product change

Incoming main is
[`8940f39`](https://github.com/ariannamethod/wolfe/commit/8940f390bc455749bae491dec0448643d8d6bbcf).
The original library reproduced all 336 STEP10 responses exactly. The initial
audit confirmed five ambiguous alternatives, one eligible shoot control and
zero games. Eleven STEP10 sources were archived before this experiment;
the incoming inventory covers 11,553 files in fourteen historical directories.

Oleg suggested more available functions. The C engine supports up to 64 tools;
the Doom adapter currently maps six tools to six individual buttons. Additional
actions could expose useful combinations, such as firing while strafing.
However, each blocked STEP10 action already ranks first. Adding definitions
would also change the field and state identity, so this turn isolates the
existing scoring limitation while retaining the same six actions.

[STEP11.md](STEP11.md) declares one formula before core edits or new results.
Only neural content attention changes, identically in C and Python:

```text
before: 0.78 * example_squared_coverage + 0.22 * query_coverage
trial:  example_squared_coverage * query_coverage
```

Field-mode scores, ordered-pair evidence, role and negation handling, recurrent
steps, reliability, abstention thresholds and all input files stay fixed.
There is no Doom token, correction privilege or literal-match override in the
patch. No second coefficient or formula is tried after the result.

The independent neutral contract uses two zero-argument tools, a broad
`sort cobalt parcel` example and a `sort cobalt parcel urgent` correction.
Eight permutations reverse tool order, example order and action labels. The
old implementation fails the qualified action in all eight; the trial passes
all 64 query checks in both languages. Broad and unrelated calls, unknown and
quoted additions, equal conflicts, omitted qualifiers and a null correction
retain their declared behavior. All 80 parsed C/Python outputs, including the
16 correction receipts, match exactly. The test and its fixtures were fixed
before either outcome.

Raw qualified behavior in the first neutral fixture:

```text
sort cobalt parcel urgent
  original: {"calls":[],"status":"ambiguous","confidence":0.982558}
  trial:    {"calls":[{"name":"violet","arguments":{}}],"status":"call","confidence":0.982813}
```

These excerpts omit reasoning but retain the returned decision and activation.
The Doom target also becomes callable in every sealed child:

| Requested action | Trial target activation | Other choices lost |
| --- | ---: | ---: |
| turn_left | 0.983998 | 2 |
| turn_right | 0.983910 | 2 |
| move_forward | 0.983666 | 3 |
| strafe_left | 0.983854 | 3 |
| strafe_right | 0.983792 | 2 |
| shoot control | 0.984579 | 3 |

The retained parent's 48 choices are unchanged. Each child, however, now
returns ambiguous for two or three other flagged inputs. For example, in the
turn_left child:

```text
healthmid ammopresent sceneempty damagerecent
  original: ambiguous, []
  trial:    call turn_left {}
healthlow ammopresent sceneempty damagerecent
  original: call strafe_right {}
  trial:    ambiguous, []
```

All seven state files remain byte-identical, and all 336 trial responses match
their fresh-process reloads completely. The first reload harness incorrectly
sent plain text to the JSONL batch interface; its malformed-JSON outputs and
source are preserved separately. Correcting only that invocation to objects
with a `text` key yields the complete matches. The collateral choice changes
are genuine behavior of the declared formula, not this harness error.

The general fixture gate independently fails:

| Frozen fixture set | Original correct | Trial correct | Newly incorrect |
| --- | ---: | ---: | ---: |
| heldout | 117/119 | 99/119 | 18 |
| final_holdout | 24/24 | 21/24 | 3 |
| confirmation_holdout | 32/32 | 22/32 | 10 |
| v2_engineering | 74/80 | 70/80 | 7 |
| v2_blind | 44/48 | 39/48 | 7 |

Total: **291 -> 251 correct out of 303**, with 45 regressions and five
improvements. The wider result is not just reduced willingness to call:

```text
Play some jazz.
  original: call play_music {"query":"jazz"}, confidence 0.935487
  trial:    no_call [], confidence 0.358318
Write a note: play music after dinner.
  original: call create_note {"text":"play music after dinner"}, confidence 0.916741
  trial:    call play_music {"query":"music after dinner"}, confidence 0.939592
Set a timer for 14 minutes and pause the music.
  original: ambiguous [], confidence 0.920739
  trial:    call pause_music {}, confidence 0.971291
```

The original `make test` passes. The candidate fails existing custom and
semantic contracts in both implementations: a package address and a compound
timer request lose their calls. Remaining declared contracts pass, including
embedding, 512 seeded fuzz responses and 115 state-interchange assertions.
No failed fixture or expected output is changed.

Full C/Python parity compares 2,727 pairs: 303 requests across three modes and
three reasoning settings. It passes 2,721 under the unchanged 1e-6 tolerance.
The six discrepancies repeat one existing numerical boundary at engineering
row 58: argument evidence 2.401688 versus 2.401687 has a binary float difference
slightly above 1e-6. Twelve bounded original-engine calls reproduce the same
discrepancy in all six configurations; calls and status agree. This pre-existing
issue is recorded separately from the trial's 45 new behavioral errors.

Result: **REJECTED; zero games**. Production `wolfe.c`, `wolfe.py` and Makefile
are restored exactly. The original Doom library and retained four-record
memory remain in place. The patch, experimental test and every changed fixture
decision are published alongside this log; full source snapshots, raw outputs,
binaries and receipts remain in `runs/core1/`. The narrow specificity success
does not establish a usable general scorer or improved Doom play. This turn
returns to Oleg without another formula, new tools or a gameplay phase.

The independent audit reconstructs the table and fixture comparisons from raw
outputs and separately reproduces four before/after pairs with the archived
binaries. It confirms all six target calls, every collateral Doom change and
the exact 45 regression rows. Its receipt is `runs/core1/independent-audit.json`;
the separate fixture/parity audit is `runs/core1/after/fixture-independent-audit.json`.

## 2026-09-17 — distinguish one already-observed health decrease

Oleg authorized the next turn after
[`0a15797`](https://github.com/ariannamethod/wolfe/commit/0a1579702e485f16ae826780606740655bade42a).
The incoming review matched STEP9's committed sources, protocol, engine and
previous input hashes to its sealed artifacts and intact independent report.
Its three non-tied raw outcomes again reproduce reward 95 -> 94 and deaths
4 -> 5. The failed five-record candidate remains evidence; the retained parent
is still `ef1a98d8093aac0c8eed9c82d4903ab6fab9656e222a9a9f9258760d7352d369`.

The prior C review motivated investigating information missing from the three
tokens. New diagnosis used only that parent's old selection seeds 1401–1408.
They contain 17 mid-health, ammo-present, empty-scene decisions. Four follow
an observed health decrease; thirteen do not. The clearest adjacent witness:

```text
seed 1406, decision 73:
  previous observed health 80 -> current health 48
  ammo20, angle302.34375, kills4, no focus -> empty-scene shoot
seed 1406, decision 74:
  previous observed health 48 -> current health 48
  ammo20, angle302.34375, kills4, no focus -> the identical C response
```

This shows a missing distinction, not an optimal alternative action. Decision
74 is only four tics after decision 73; absence of another decrease does not
mean safety. No policy is prescribed from the apparent desirability of dodging.

A separate suspicion about zero-width labels was falsified. Tagged ViZDoom
1.3.0 admits labelled sprites with positive pixel counts, but writes bounding
dimensions as max minus min: a single visible column can have width zero.
Dropping those labels would remove real evidence. The same engine prefixes
dead actors with `Dead`; none occur in STEP9's 40,128 predecision snapshots.
See the primary [label construction](https://github.com/Farama-Foundation/ViZDoom/blob/1.3.0/src/vizdoom/src/viz_game.cpp#L480)
and [actor naming](https://github.com/Farama-Foundation/ViZDoom/blob/1.3.0/src/vizdoom/src/viz_game.cpp#L241).
Using inclusive box area changes ranking in two shared evaluation states,
and changes tokens in only one; it changes none of the selection states.
No label-selection change is part of this turn.

[STEP10.md](STEP10.md) declares one opt-in bit: current predecision health below
the previous decision's predecision health appends `damagerecent`; first call
is false. Each player derives it from its own history. `run.py` records base
input, the previous health and the bit before the next action is interpreted.
Old observation/action helpers are unchanged. Read-only replay reproduced
all 899 old selection inputs, with 32 flagged observations in total and four
flagged target visits. Initial, unchanged-health and healing cases produce no
flag. An independent reader confirmed the update uses `before`, never future
`after` or reward; default mode preserves the old input and record schema.

Unknown words have nonzero influence in the C field, so the protocol first
tests all 24 flagged/unflagged parent action pairs. Only if those choices match
may six independent children append a flagged mid-health empty-scene correction.
Each must retain the four original records, zero counters and the other 47
choices. Failure to represent a different action ends the step before games.
Otherwise one reward selection on 1601–1608 and a fresh paired comparison on
1701–1716 answer whether that distinction helps. No alternate feature, token,
reward or C change follows from a failure.

Nine exact incoming sources were archived in `runs/joint-mid1-source/` before
the episode adapter changed. The incoming inventory covers 11,508 historical
files in twelve sealed directories.

Independent pre-data review found no contract or implementation blocker. The
declared command ran once:

```sh
.venv/bin/python history.py run --previous runs/joint-mid1 --output runs/history1
```

The baseline gate passes: all 24 original full responses match, and all 24
flagged choices equal their unflagged counterparts. Each of the six candidates
contains exactly the original four records plus its requested fifth record;
counters stay zero and all other 47 choices remain fixed. However, every
different requested target action returns `ambiguous`, with no emitted call.
Only the parent-matching shoot correction is eligible:

| Requested target action | Actual status | Top activation | Runner activation | Margin | Other choices changed |
| --- | --- | ---: | ---: | ---: | ---: |
| turn_left | ambiguous | 0.981218 | 0.969232 | 0.011986 | 0 |
| turn_right | ambiguous | 0.981130 | 0.969169 | 0.011961 | 0 |
| move_forward | ambiguous | 0.980800 | 0.969109 | 0.011690 | 0 |
| strafe_left | ambiguous | 0.981077 | 0.969098 | 0.011978 | 0 |
| strafe_right | ambiguous | 0.980998 | 0.969208 | 0.011790 | 0 |
| shoot control | call | 0.981359 | 0.725072 | 0.256287 | 0 |

The requested action ranks first in every row. Shoot is runner-up for the
five alternatives; strafe_right is runner-up for the control. Serialized
values are rounded, so displayed subtraction can differ in the last digit.
These are neural activations, not calibrated success probabilities.

The raw turn_left candidate shows the phenomenon directly:

```text
healthmid ammopresent sceneempty
  -> call shoot
healthmid ammopresent sceneempty damagerecent
  -> {"calls":[],"status":"ambiguous","confidence":0.981218,...}
     best example: healthmid ammopresent sceneempty damagerecent -> turn_left
     runner example: healthmid ammopresent sceneempty -> shoot
```

The result is **NO_ALTERNATIVE_ACTION / benefit NOT_RUN**. There are 336
recorded responses: 48 for the parent and 48 for each of six corrected models.
There are **zero new game episodes**. No selection, selected memory, restart,
or evaluation artifacts were produced, and seeds 1601–1608 / 1701–1716 remain
unused. The existing four-record player and its published gameplay statistics
are unchanged.

A separate source reader identified the precise boundary. The neural branch
of [`infer`](../wolfe.c#L2125) rejects a choice when its activation margin is
below 0.065, the runner is above 0.52, and its evidence advantage is below 0.08.
All three hold here. For turn_left, the new exact four-token example has
evidence 1; the old three-token shoot example retains approximately 0.933042,
so the evidence advantage is approximately 0.066958. Every old example token
and adjacent pair still matches. The extra query condition affects only the
query-coverage part of `example_scores`, weighted 0.22; the source-coverage part
remains complete. After recurrent settling, the winning and competing
activations remain close enough for the explicit ambiguity gate to fire.

Correction retains the old example because its text differs from the new one.
Thus this is a demonstrated limit of this additive conditional representation
and ambiguity contract, not lost state, future-data leakage, or collateral
changes to other decisions. It does not establish that every possible history
encoding would fail. A future question is how more-specific experience should
coexist with a broader association while preserving abstention for equally
supported conflicting evidence. No threshold, token, corpus, target or C implementation
was changed to rescue this failed experiment.

Independent reconstruction of all 336 saved responses, six memories and the
899-decision historical witness found no discrepancy. It confirms 331 calls
and five abstentions, only the shoot control eligible, and no game artifacts.
The receipt is `runs/history1/independent-audit.json`. Source, protocol, engine,
library and inherited input hashes match; all 11,508 prior files remain
byte-identical, with no additions or removals in their sealed directories.
Syntax, CLI, whitespace and documentation-link checks passed. The game-selection
and evaluation branches were not exercised because the predeclared
representation gate stopped the experiment.

## 2026-09-17 — jointly revisit mid-health center and empty-scene memory

Oleg authorized continuing, publication, new screenshots, and a parallel
review of the C engine. Incoming main was
[`4cd8fba`](https://github.com/ariannamethod/wolfe/commit/4cd8fbae49cfa3a286344b4aae27416a8ea515ae).
The previous independent raw audit confirmed STEP8's mechanism PASS and
benefit FAIL. Its selected fifth-record shoot memory was not promoted.
The retained parent is still the four-record STEP6 memory, SHA-256
`ef1a98d8093aac0c8eed9c82d4903ab6fab9656e222a9a9f9258760d7352d369`.
Nine exact STEP8 source files were archived in `runs/center1-source/` before
editing the shared `joint.py` driver.

The hypothesis originated openly from the previous evaluation's seed 1307:
an earlier centered kill leaves mid health and enters the acquired empty-scene
shoot reaction. It is not a training-only discovery. A separate old training
witness, seed 1201, contains one center-to-empty transition after a kill,
followed by 23 empty-scene shoot calls. That candidate actually improves the
training return, so the sequence alone is not proof of harm.

[STEP9.md](STEP9.md) fixes A = `healthmid ammopresent scenecenter` and
B = `healthmid ammopresent sceneempty`. All 36 pairs start from the retained
parent, append A first, and replace B in its original second slot. The other
three acquired records and 22 runtime decisions must remain fixed. Selection
uses only unmodified episode reward on 1401–1408; parent wins ties, and the
first strict grid maximum wins candidate ties. Fresh evaluation is 1501–1516.
No C change, history token, new reward, or further generation is included.

Before games, syntax, CLI and whitespace checks passed. Read-only comparison
with the archived implementation reproduced all 36 STEP6 eligibility receipts,
344 old episode receipts and their aggregates; the old high-health loop
function is unchanged. An independent reader reviewed the new contract and
code before this single command:

```sh
.venv/bin/python joint.py --step9 --previous runs/center1 \
  --legacy-memory runs/perception1/memory.json --output runs/joint-mid1
```

All 36 proposals passed structural eligibility. The parent-matching control,
pair 17 (move_forward, shoot), reproduces all eight parent physical histories.
Pair 35 (shoot, shoot) is byte-identical to STEP8's failed candidate; it is one
proposal, never the inherited parent. Full selection reward grid, with A in
rows and B in columns; parent reward is 40:

| A \\ B | turn_left | turn_right | move_forward | strafe_left | strafe_right | shoot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| turn_left | 38 | 38 | 38 | 37 | 38 | 38 |
| turn_right | **42** | 42 | 42 | 41 | 42 | 42 |
| move_forward | 40 | 40 | 40 | 39 | 40 | 40 |
| strafe_left | 40 | 40 | 39 | 38 | 39 | 39 |
| strafe_right | 41 | 40 | 40 | 39 | 39 | 39 |
| shoot | 42 | 42 | 42 | 41 | 42 | 42 |

Ten pairs tie at 42. The declared ordering selects pair 06: center turn_right,
empty turn_left. Thus this sample does not uniquely identify either action
as best. Pair 11 (turn_right, shoot) also scores 42 while retaining B, so a
need to change both decisions is not established. Selection kills rise
43 -> 45, with three deaths in both conditions.
Selected memory SHA-256:
`b52e4363e412bb4f12428836e05928c1774ccb7a2c77cd8e01adc14ef6b2a9b8`.
The full 24-response table and five-record structural gate survive a separate
process restart. Both target calls change; all other 22 stay fixed.

Fresh evaluation returns:

| Seed | Parent | Selected candidate | Legacy reference |
| --- | ---: | ---: | ---: |
| 1501 | 7 | 7 | 0 |
| 1502 | 8 | 8 | 1 |
| 1503 | 7 | 7 | 1 |
| 1504 | 6 | 5 | 0 |
| 1505 | 6 | 6 | 0 |
| 1506 | 4 | 4 | 1 |
| 1507 | 6 | 6 | 1 |
| 1508 | 4 | 3 | 1 |
| 1509 | 8 | 8 | 0 |
| 1510 | 4 | 4 | 0 |
| 1511 | 2 | 2 | 1 |
| 1512 | 6 | 6 | 0 |
| 1513 | 11 | 11 | 1 |
| 1514 | 5 | 6 | 1 |
| 1515 | 3 | 3 | 0 |
| 1516 | 8 | 8 | 1 |

| Aggregate | Parent | Selected candidate | Legacy reference |
| --- | ---: | ---: | ---: |
| Reward | 95 | 94 | 9 |
| Kills | 99 | 99 | 17 |
| Deaths | 4 | 5 | 8 |
| Alive through fixed horizon | 12 | 11 | 8 |
| Mid-health center visits | 25 | 15 | 408 |
| Mid-health empty visits | 79 | 27 | 384 |
| Direct center-to-empty transitions | 0 | 0 | 96 |
| Those transitions after a kill in the center window | 0 | 0 | 0 |
| Longest consecutive mid-health empty run | 24 | 11 | 3 |
| High-health A-B-A windows | 1 | 1 | 0 |
| High-health B-A-B windows | 1 | 1 | 0 |

Legacy uses its older scene encoding even where the input text is identical.
The mechanism passes; **the benefit gate fails**. Mean paired reward change
is -0.0625, with one improvement, two regressions and thirteen ties. The
retained parent remains the working player. Both new target reactions persist,
but shortening the empty-scene run does not improve the episode result.
Neither parent nor chosen candidate produces the original center-to-empty
chain in this fresh sample, or in their new selection episodes. This step
does not demonstrate that the proposed interaction has been resolved.

All three non-tied outcomes begin with a different action from identical raw
states. Decision indices below are zero-based:

```text
seed 1504, decision 85: mid-health empty; health 48, ammo 15, kills 6
  parent: shoot; later low-health strafe and left-side shoot
          seventh kill at 107, dies at 118
  candidate: turn_left reveals MarineChainsawVzd id12 on the left
             later follows a different low-health turning path;
             no further kills, dies at 113

seed 1508, decision 87: mid-health center; health 60, ammo 12, kills 4
  parent: move_forward through 93, then strafe_left and empty-scene shoot
          low-health strafe begins at 120; survives with health 12
  candidate: turn_right at 87-89 moves id7 to the left; shoot at 90-99
             another centered turn at 100; health falls, dies at 106
             neither branch gains another kill

seed 1514, decision 59: mid-health empty; health 56, ammo 18, kills 5
  parent: shoot through 72; then low-health strafe, survives with five kills
  candidate: turn_left through 65 reveals id15 on the left
             subsequent low-health path kills a Demon at 108;
             survives with six kills and health 12
```

There are ten first action divergences and six physically identical evaluation
episodes. Seed 1513 is one of the identical cases: the retained player reaches
eleven kills with health 30. Its unedited frames at calls 64 and 128 now appear
near the top of the main README, with byte hashes and provenance in
[`assets/doom/README.md`](../assets/doom/README.md). Old images remain intact.
The latest table exposes all three policies, deaths and sample size. The
retained player's 99 kills on these seeds versus 90 on STEP6's different seeds
is not evidence of a new improvement.

The parallel bounded review found no demonstrated `wolfe.c` defect explaining
this path. Ninety-six read-only calls reproduced complete responses after
reload, reversed query order and interleaving two separate models. Corrections
persist and rebuild the shared field; activations reset for each call and
settle recurrently within that decision. This is the implementation's explicit
construction, not accidentally lost recurrent state. In old seed 1307, identical
three-token inputs yield identical responses while health falls 54 -> 38 -> 22.
The adapter omits that change and short history. This establishes information
compression, not which extra feature would help, nor that the C core is perfect.
The scoped local notes are in `doom/.build/core-audit-step9.md`; no C edit was
justified or made during this step.

An independent reader reconstructed **344 episodes and 40,128 decisions**,
including full C responses, observation/focus, buttons, tic and state continuity,
returns, all proposal records, control histories, restart, selection ties and
both comparisons. Its receipt is `runs/joint-mid1/independent-audit.json`.
All 7,983 prior files in ten sealed directories remain byte-identical, with no
additions or removals. The core, library, protocol and inherited input hashes
match the sealed manifest. All proposals and the failed outcome are preserved;
no runner-up, extra episode set, new feature or next generation was tried.

## 2026-09-17 — let game outcomes select the mid-health centered-object choice

Oleg authorized publishing the negative STEP7 experiment and continuing.
It was committed and pushed as
[`b616bb2`](https://github.com/ariannamethod/wolfe/commit/b616bb2e9659ec6aaff60ca6c89aa08505d89769),
with a unique Quote and Method line. Remote main was checked against that hash.
The incoming independent audit reproduced NO_ADOPTION, all 56 raw episodes,
the seven selection totals, and source/state hashes. Its nine exact source
files were archived in `runs/revision1-source/` before changing the shared
`revise.py` driver; the previous evidence remains intact.

The next diagnosis read only retained-parent selection seeds 1001–1008.
Mid-health left has 147 visits in five seeds; mid-health center has 16 in four.
There are five center-to-left and two left-to-center transitions, but only one
consecutive left-center-left window and no center-left-center window. This
does not support a repeated pair oscillation like the STEP6 problem.

The next narrow question is the centered-object choice, currently the initial
move_forward association. In seed 1006, decisions 107–110 keep Marine id 14 in
focus with fixed angle 260.15625; its box grows 52×113 -> 174×195 while health
falls 44 -> 32. Ammo stays 9 and kills 4. Across all 16 centered windows there
are three ammo decreases, one kill increase and 30 health lost. Window-level
outcomes do not establish causal credit for the command currently issued.

[STEP8.md](STEP8.md) declares six independently appended fifth corrections for
`healthmid ammopresent scenecenter`, with all four acquired records and the
other 23 runtime decisions fixed. No replacement action is prescribed. The
same episode reward selects on 1201–1208; only a strict winner passing restart
reaches the parent/child/legacy comparison on 1301–1316. The previous unused
evaluation seeds 1101–1116 remain unused. This step reuses the search driver
through explicit `--step8`, preserving the original STEP7 entry point.

Before games, syntax, CLI and whitespace checks passed. A read-only replay
against the archived STEP7 implementation reproduced eight historical target
statistics, six full eligibility verdicts, and all seven selection aggregates.
The new target's historical totals also reproduce 16 visits, three ammo
decrements, 30 health lost, one kill gained, and maximum consecutive run four.
An independent reader checked the new mode and original defaults before the
command was run once:

```sh
.venv/bin/python revise.py --step8 --previous runs/revision1 \
  --legacy-memory runs/perception1/memory.json --output runs/center1
```

All six proposals passed structural eligibility: actual requested target call,
five exact records containing the original four, zero counters, and the other
23 decisions fixed. Selection uses only summed episode reward:

| Target action | Reward, 1201–1208 | Kills | Deaths |
| --- | ---: | ---: | ---: |
| Parent | 38 | 40 | 2 |
| turn_left | 40 | 41 | 1 |
| turn_right | 39 | 41 | 2 |
| move_forward control | 38 | 40 | 2 |
| strafe_left | 39 | 41 | 2 |
| strafe_right | 39 | 40 | 1 |
| shoot | **41** | 42 | 1 |

Shoot was sealed as the unique maximum. Its state hash is
`c25d2d2bc5b4f06604cc9a6966923f2a2e446e33892dce76a5f285d8b115a70c`.
The complete 24-response table survived fresh-process restart, as did the
structural gate. Only mid-health center changes its emitted call. This proves
that the fifth association persists; it does not establish a better player.

Fresh evaluation returns:

| Seed | Parent | Selected candidate | Legacy reference |
| --- | ---: | ---: | ---: |
| 1301 | 3 | 3 | 1 |
| 1302 | 6 | 6 | 1 |
| 1303 | 9 | 9 | 1 |
| 1304 | 4 | 4 | 1 |
| 1305 | 3 | 3 | 1 |
| 1306 | 6 | 4 | 0 |
| 1307 | 4 | 3 | 0 |
| 1308 | 5 | 5 | 1 |
| 1309 | 5 | 5 | 0 |
| 1310 | 6 | 6 | 1 |
| 1311 | 6 | 6 | 0 |
| 1312 | 4 | 4 | 2 |
| 1313 | 3 | 3 | 1 |
| 1314 | 5 | 5 | 1 |
| 1315 | 3 | 3 | 1 |
| 1316 | 8 | 8 | 1 |

| Aggregate | Parent | Selected candidate | Legacy reference |
| --- | ---: | ---: | ---: |
| Reward | 80 | 77 | 13 |
| Kills | 85 | 84 | 18 |
| Deaths | 5 | 7 | 5 |
| Alive through fixed horizon | 11 | 9 | 11 |
| Target visits | 30 | 41 | 409 |
| Shoot calls in target | 0 | 41 | 0 |
| Ammo consumed during target windows | 4 | 15 | 3 |
| Health lost during target windows | 82 | 80 | 216 |
| Kills gained during target windows | 3 | 6 | 1 |
| Longest consecutive target run | 7 | 14 | 16 |
| High-health A-B-A windows | 2 | 2 | 0 |
| High-health B-A-B windows | 2 | 2 | 0 |

The mechanism passes; **the benefit gate fails**. Mean paired difference is
-0.1875: zero improvements, two regressions, fourteen ties. Seven evaluation
seeds never visit the target under either policy. Both regressions change a
surviving parent episode into a death. The candidate beats legacy return on
all 16 seeds (mean +4), but that is not the declared comparison for this new
change. The current parent also scores far more kills than legacy and has
the same death count on this sample; changing samples does not establish that
its earlier survival deficit has been repaired.

Two raw counterexamples begin from identical states in each matched pair:

```text
seed 1306, decision 102: health 72, ammo 8, kills 4; Marine id 8 centered
  parent: move_forward, then left-side shoot; kills at 110 and 122
          survives 128 calls with six kills and health 32
  candidate: centered shoot for decisions 102–115; kill at 115
             health 72 -> 32 at 115; dies at 119 with five kills

seed 1307, decision 96: health 74, ammo 13, kills 3; Marine id 9 centered
  parent: move_forward; kills the Marine at 101, already at health 10
          low-health empty scene -> strafe_right; survives with four kills
  candidate: shoot; kills the Marine at 97 with health 54
             mid-health empty scene -> shoot, then later low-health strafe
             dies at 114 with the same four kills
```

The second trace shows an earlier kill followed by a different health-context
path through existing memories. It does not prove that another isolated or
joint correction would fix the whole episode. In the first trace, the parent
and candidate also follow different movement histories after the first call.
The three-token observation and discrete inherited actions remain limited;
neither the apparent desirability of shooting nor a local kill count overrides
the full-episode result.

The two A-B-A windows occur in seeds 1303 (decisions 38–40) and 1304 (40–42),
with turn_left/strafe_left/turn_left and increasing angle in both policies.
These context windows recur, but they do not reproduce the old opposite-turn
oscillation: the strafe holds the angle instead of reversing it. Zero windows
in STEP6's earlier sample was not a universal guarantee.

The selected candidate remains recorded, but is not promoted as an improved
replacement. The retained four-correction STEP6 player remains the working
reference. All 104 episodes and 12,748 decisions remain in `runs/center1/`.
All 6,909 prior files, including the archived STEP7 sources, remain byte-identical
with no additions or removals in their sealed directories. Current source,
protocol and inherited input hashes match the new manifest. No runner-up,
second context, altered reward, or additional episode set was tried after
the failed benefit gate.

An independent reader reconstructed all 104 episodes and 12,748 decisions,
checking full responses, focus/input, buttons, tics, state continuity, returns,
memory retention, restart and both comparisons. The move_forward control
reproduces all eight parent selection histories. On the nine evaluation seeds
that visit the target, the first differing action occurs there from the same
raw state; the other seven physical histories remain identical. The new
`independent-audit.json` confirms both regressions and the limited meaning of
the repeated context windows, with no discrepancies. This completed step is
prepared for publication under Oleg's granted push authority.

## 2026-09-17 — revisit the acquired mid-health empty-scene reaction

Oleg authorized publishing STEP6 and two actual screenshots, then continuing
one bounded learning step. STEP6 is committed as
[`873c09f`](https://github.com/ariannamethod/wolfe/commit/873c09f);
the frames and README update as
[`f4e2812`](https://github.com/ariannamethod/wolfe/commit/f4e28129d04ad5edfd65185eebfda834753a701d).
Both were pushed to main, whose remote hash was checked. Their unique Quote
and Method lines are part of the history.

The incoming reader reproduced STEP6's selection, restart, raw evaluation,
survival deficit, and source/state hashes. New diagnosis used only the
selected child's training seeds 801–808: 1,024 decisions, all eight episodes
alive at the fixed horizon. There were six high-to-mid and four mid-to-low
health transitions. The acquired `healthmid ammopresent sceneempty → shoot`
reaction was visited 75 times across four seeds, consuming 21 rounds, losing
82 health, and gaining zero kills during those action windows.

The most frequent uncorrected context was mid-health left, with 113 visits.
This step instead explicitly investigates the old empty-scene correction.
On seed 806, decisions 79–112 form 34 consecutive empty-scene shoot calls:
ammunition 14 -> 5, health 44 -> 16, no new kills. Seed 805 has 26 such calls
at decisions 102–127, ammunition 14 -> 6 and health 46 -> 32. Neither diagnosis
claims the shots caused damage or predicts which replacement must help.

[STEP7.md](STEP7.md) declares six independent replacements for this one memory
record, preserving the other three records and 23 runtime decisions. All six
actions compete under the unchanged game reward; shoot remains a control.
Selection uses seeds 1001–1008, with parent winning ties. Any strict winner
must reproduce all 24 responses after restart before fresh parent/child/legacy
evaluation on 1101–1116. A separate reader checked the declared contract.

The new `revise.py` reuses the existing game and episode readers. It passed
syntax/CLI checks and an independent pre-data review before the single run:

```sh
.venv/bin/python revise.py --previous runs/joint1 \
  --legacy-memory runs/perception1/memory.json --output runs/revision1
```

All six proposals passed the structural gate before games. Each changes only
the requested second correction record, retains exactly four records and zero
counters, and realizes its requested call with all other 23 decisions fixed.

Selection on seeds 1001–1008:

| Target action | Reward | Kills | Deaths | Longest target run |
| --- | ---: | ---: | ---: | ---: |
| Unmodified parent (shoot) | **43** | 44 | **1** | 24 |
| turn_left | 42 | 44 | 2 | 4 |
| turn_right | 40 | 42 | 2 | 16 |
| move_forward | 39 | 41 | 2 | 80 |
| strafe_left | 41 | 43 | 2 | 4 |
| strafe_right | 41 | 43 | 2 | 80 |
| shoot control | **43** | 44 | **1** | 24 |

No candidate strictly improved the parent. The result is **NO_ADOPTION**;
benefit is **NOT_RUN**. No `selected-memory.json`, restart of a selected child,
or evaluation directory was created. The reserved seeds 1101–1116 were not
used, and no fresh comparison with legacy was claimed. The STEP6 policy stays
selected. This is a completed negative experiment, not a failed execution.

Complete selection returns, preserving ties and losses:

| Seed | Parent | Left | Right | Forward | Strafe left | Strafe right | Shoot control |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1001 | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
| 1002 | 4 | 3 | 4 | 2 | 2 | 2 | 4 |
| 1003 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| 1004 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
| 1005 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| 1006 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| 1007 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| 1008 | 5 | 5 | 2 | 3 | 5 | 5 | 5 |

Three seeds never visit the target under the parent, so identical results
there do not establish anything about the replacement. The parent visits it
50 times across the remaining five seeds, fires on all 50, and consumes 13
rounds during those windows. The turn_left candidate visits it 11 times,
never issues shoot there, and records no health loss in those windows.
Nevertheless its total death count is higher. These are measurements within
action windows, not causal credit for the command active at the time.

The closest candidate's one reward regression, seed 1002, is visible in raw
behavior. Both players have health 72, ammo 23, three kills and angle 226.75781
at decision 57, with the same empty observation. The parent shoots and keeps
its angle; the candidate turns left to 233.78906. At 58 the candidate sees a
left-side actor and enters the unchanged mid-health left -> shoot reaction.
Later it reaches a centered actor at decisions 82–85 but uses the unchanged
mid-health center -> move_forward reaction. It gets its fourth kill at 92,
turns through four empty observations at 93–96, then loses health 56 -> 24 at
97 with a left-side actor in view. At decision 111 it dies during the unchanged
low-health empty -> strafe_right reaction, finishing with four kills and
reward 3. The parent reaches decision 128 alive with four kills, health 8,
and reward 4. This describes the divergent sequences; it does not assign the
whole death to a single neighboring reaction.

The earlier high-health alternating-context windows remain zero in all seven
selection conditions. Resolving those windows remains intact, while changing
the diagnosed mid-health empty reaction alone does not produce a better
candidate on these eight seeds. The experiment does not establish that shoot
is generally optimal, or that a coordinated revision elsewhere cannot help.

All 56 real episodes and 7,024 decisions are retained in `runs/revision1/`.
All 6,303 previous artifact files remain byte-identical, with no additions or
removals in sealed directories. Source, protocol, inherited inputs, parent,
and candidate hashes remain fixed. An independent reader checked all 56
episodes and 7,024 full decision records, structural eligibility, hashes,
target/loop/survival statistics, and the seed-1002 regression. The shoot control
has the same state hash and all eight physical histories as the parent.
Its new `independent-audit.json` reports zero discrepancies and confirms that
no evaluation or selected-child restart was run. The declared stopping rule is honored;
no replacement action, second context, reward change, or new seed set is
introduced after this result.

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
