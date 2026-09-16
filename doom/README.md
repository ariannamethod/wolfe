# WOLFE in Doom

The C WOLFE engine now controls a real ViZDoom player through its existing
tool-calling API. One bounded experiment also selects a persistent memory
correction using game outcomes. Self-play remains a future research question.

The first recorded episode ended in death: 39 typed calls, 154 game tics,
zero shots, zero kills. A fixed arbitrary initial policy controlled every
action. No learning occurred in this run.

In the second experiment, game reward selected one correction from six
independent candidates. It changed one of the 24 observation decisions and
survived process restart. On 16 separate evaluation seeds, episode return
improved in 14 cases and worsened in two; kills increased from 4 to 19 in total.
The selected player still died in 14 episodes. This is a small improvement on
one fixed scenario, under game-provided symbolic perception.

Two actual frames from the later joint-memory experiment are shown in the
[main README](../README.md#doom-experiment), with their
[source episode and hashes](../assets/doom/README.md).

## Run

From this directory, with Python 3.10+ and a C99 compiler:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python build.py
.venv/bin/python run.py --output runs/my-first-episode --seed 17
```

Add `--visible` to show the game window. The synchronous engine advances four
tics per decision; it runs as fast as the caller, rather than at viewing speed.
Use a new output directory for every run. Existing records are never replaced.

`build.py` compiles the parent `wolfe.c` as a shared library, using
`WOLFE_NO_MAIN`. It records the source and library hashes and git revision.
The adapter loads that C API through `ctypes`; the model chooses the tool and
the adapter applies the corresponding button. Calls are serialized.

ViZDoom supplies the `defend_the_center` scenario and Freedoom assets. No
separately purchased game data is needed for this scenario. The source and
definitions used by the ordinary WOLFE caller remain separate from this example.

## What the player sees and does

The model receives three alphanumeric tokens, for example:

```text
healthhigh ammopresent scenecenter
```

Health is divided at 25 and 75. Ammo is absent/present. The largest visible
labelled object determines left/center/right, with the middle third of the
screen counted as center; no visible object gives `sceneempty`. Only the
player label is excluded. Object names and boxes remain in the raw receipt.
This is game-provided symbolic perception, not a learned visual encoder.

The six tools are `turn_left`, `turn_right`, `move_forward`, `strafe_left`,
`strafe_right`, and `shoot`, each with empty arguments. Every action holds one
button for the same four-tic quantum. A model abstention applies no buttons
and is explicitly recorded. Invalid calls stop the run.

`initial_examples.jsonl` is the entire declared starting prior: 24 possible
observation combinations paired with a balanced, shuffled list of actions
using Python Random seed 1729. `make_prior.py` documents its construction and
refuses to overwrite definitions. The assignment uses no game outcomes or
hand-authored aiming strategy. WOLFE still performs its normal recurrent
inference on this corpus; it is not a direct lookup in the executor.

## Inspect the episode

Each output directory contains:

- `trajectory.jsonl`: raw before/after observations, exact model input, full
  C response and reasoning, applied buttons, tics, reward, and terminal state.
- `trace.txt`: readable decisions and changes in player variables.
- `manifest.json`: source/configuration hashes and declared run settings.
- `summary.json`: recomputed counts and the environment-connection gate.
- `frame_*.png`: actual game frames, when the player is still alive at the
  scheduled capture points.

The first episode is preserved locally in `runs/seed17/`; run artifacts and
dependencies are ignored by Git. Its result and representative raw transitions
are recorded in [WOLFEDOOMLOG.md](WOLFEDOOMLOG.md).

The gate was declared in [STEP1.md](STEP1.md) before gameplay. It measures
whether real WOLFE calls reach the game, not whether the player is competent.
No learning was performed during that episode.

## One change selected by experience

With the same build and environment, run the predeclared [STEP2.md](STEP2.md):

```sh
.venv/bin/python experience.py run --output runs/my-memory-experiment
```

The experiment varies only the association for
`healthhigh ammopresent scenecenter`. Each of the six primitive actions gets
one candidate, created from the unchanged ancestor through the existing C
correction API. The ancestor and candidates play seeds 101–108. Only total
scenario reward selects a candidate; the ancestor wins ties. No action is
chosen by the outer experiment during an episode.

Selection is sealed before seeds 201–216 are used to compare the chosen
memory against the ancestor. Every game starts a fresh process with fixed
memory. A separate restart also checks all 24 model responses against the
selected candidate. The original corpus, C source, and reliability counters
stay unchanged. This is one generation of search through example memory;
there is no gradient update, opponent pool, or multiplayer self-play.

The output preserves all candidate memories and decision tables, selection
results, the sealed `selection.json`, `selected-memory.json`, restart table,
paired `evaluation.json`, and separate mechanism/benefit verdicts in
`result.json`. Every episode has the same raw receipts and frames described
above. `NO_ADOPTION` or a failed benefit gate is also a completed experiment;
the command does not search again to force a pass.

To inspect a fixed selected memory in another episode:

```sh
.venv/bin/python run.py --state runs/my-memory-experiment/selected-memory.json \
  --output runs/inspect-memory --seed 201
```

The first complete experiment is preserved locally in `runs/memory1/`, with
all 88 episodes, including both evaluation regressions. Its raw transitions,
full paired returns, and limitations are in [WOLFEDOOMLOG.md](WOLFEDOOMLOG.md).

## Accumulate one additional memory

[STEP3.md](STEP3.md) tests one more association inherited alongside the first:

```sh
.venv/bin/python experience.py continue --previous runs/my-memory-experiment \
  --output runs/my-second-memory
```

This declared step requires the exact selected parent-state hash recorded in
STEP3. It reads only that parent's old selection trajectories, chooses the
most visited observation without an existing correction, and freezes that
choice before new games. Each of six children inherits the same first memory
and adds one candidate correction. Selection uses seeds 301–308; the chosen
child then faces its parent on seeds 401–416. The old corrected decision must
survive, as must the complete response table after process restart.

The command runs one generation and stops. Its mechanism and benefit verdicts
are separate. Perception, tools, initial corpus, and game reward stay fixed.

The first continuation retained the initial correction and selected a second
one. On its 16 new evaluation seeds, reward improved in seven cases and tied
in nine. Deaths fell from 15 to 7 within the fixed horizon; kills fell from 19
to 18. Both corrections survived restart. Full results and raw examples,
including wasted ammunition and remaining perception limits, are recorded in
[WOLFEDOOMLOG.md](WOLFEDOOMLOG.md); local artifacts are in `runs/memory2/`.

## Compare perception with the same memory

[STEP4.md](STEP4.md) isolates one observation change with the two-correction
policy frozen:

```sh
.venv/bin/python perception.py --previous runs/my-second-memory \
  --output runs/my-perception-comparison
```

It compares 16 matched seeds, 501–516. `legacy` uses the original largest
nonplayer label; `no-effects` additionally excludes exactly `Blood` and
`BulletPuff`. Other objects and all binning rules remain unchanged. This is
filtering game-provided labels, not recognizing living enemies. The command
requires the exact selected memory hash recorded in STEP4 and performs no
learning. Each trajectory records its selected `focus` label.

The output contains alternative encodings of the old selection states,
32 real episodes, and the first action divergence from an identical raw state
for each pair. `result.json` separates the observation mechanism from reward
benefit, and reports kills, deaths, `shoot` calls, and ammunition consumed.
Filtering does not imply less shooting: the existing memory can map the new
empty-scene observation to `shoot`.

Individual episodes accept `--perception no-effects`; `legacy` remains the
default. Both modes use the same C policy and button executor.

The first comparison passed the perception-mechanism check and **failed the
benefit gate**. With identical memory, filtering improved one seed, worsened
eleven, and tied four. Total reward fell from 13 to 3; deaths rose from 4 to 15.
It consumed less ammunition and scored one more kill overall, but episodes
also ended much earlier. The filter remains an opt-in experiment, not the
adopted policy. All results are preserved locally in `runs/perception1/` and
described in [WOLFEDOOMLOG.md](WOLFEDOOMLOG.md).

## Adapt memory to the filtered observation

[STEP5.md](STEP5.md) tests one additional inherited association under the
fixed no-effects observation:

```sh
.venv/bin/python experience.py adapt --previous runs/my-perception-comparison \
  --output runs/my-adaptation
```

The old historical-state comparison chooses the most frequent first affected
uncorrected input across eight earlier trajectories. Six independent children
inherit both existing corrections and each try one action for that input.
New game returns on seeds 601–608 select a child, with the parent winning ties.
The two acquired choices and all 24 responses must survive the memory checks
and process restart before evaluation.

Seeds 701–716 compare three fixed conditions: filtered parent, filtered child,
and the parent under legacy perception. The benefit gate compares the child
with the filtered parent. The legacy reference separately shows whether that
gain recovers the earlier policy's performance; it does not choose a child.
The command performs one generation, preserving all candidates and outcomes.

The first adaptation selected `turn_left` for
`healthhigh ammopresent sceneempty`. It retained both earlier choices and
survived restart. On the 16 fresh seeds, reward rose from 5 to 13 against the
filtered parent: nine improvements, two regressions, five ties. Kills rose
from 20 to 28; both policies died in 15 episodes.

The separate legacy reference scored reward 11, 16 kills, and five deaths.
Thus the adapted policy slightly exceeded that reference's total reward on
this sample, while surviving much less often. Remaining aiming oscillations
and both primary regressions are recorded in [WOLFEDOOMLOG.md](WOLFEDOOMLOG.md).
Local artifacts are in `runs/adaptation1/`. To inspect the selected child:

```sh
.venv/bin/python run.py --state runs/my-adaptation/selected-memory.json \
  --perception no-effects --output runs/inspect-adaptation --seed 701
```

## Revise two neighboring decisions together

[STEP6.md](STEP6.md) jointly revisits the high-health empty-scene choice and
the high-health left-object choice observed in an aiming loop:

```sh
.venv/bin/python joint.py --previous runs/my-adaptation \
  --legacy-memory runs/my-perception-comparison/memory.json \
  --output runs/my-joint-search
```

It constructs all 36 action pairs from separate copies of the three-correction
parent. Each proposal must realize its requested calls while preserving the
other 22 decisions before it can enter game selection. Every proposal and any
eligibility failure are preserved. One previously acquired correction may be
revised in a descendant; the original parent and experience remain intact.

Selection uses the same episode reward on seeds 801–808, with the unchanged
parent winning ties. Evaluation on 901–916 compares the chosen child, current
parent, and older legacy reference. The report includes alternating-context
windows and their rates, kills, deaths, and survival through the fixed horizon.
These measurements expose whether joint selection helps the observed loop or
survival; they do not add a hidden selection bonus.

The first grid admitted all 36 proposals. Reward selected
`sceneempty → turn_left`, `sceneleft → strafe_left` in the two high-health,
ammo-present contexts. Thus the winning pair retained the acquired search
turn and changed only the left-object reaction. This experiment does not
establish that changing both decisions jointly was necessary.

On the 16 fresh seeds, the child improved reward in 15 cases and tied one.
Total reward rose from 11 to 84, kills from 24 to 90, and deaths fell from 13
to 6. The measured empty-left-empty and left-empty-left windows both fell to
zero. Raw sequences show lateral movement bringing the object into the center,
where the existing shoot association takes over.

The older legacy reference scored 14 reward, 18 kills, and four deaths on
these same seeds. Its survival was **not recovered**: the child survived the
fixed horizon in 10 episodes, versus 12 for legacy. Seed 901 also exposes a
reward tie that hides a survival regression against the current parent.
All 344 episodes, 32,757 decisions, proposals, and restart evidence remain
locally in `runs/joint1/`; see [WOLFEDOOMLOG.md](WOLFEDOOMLOG.md) for raw behavior
and remaining failures. No history token, new reward, or C-core change was used.

## Revisit an acquired empty-scene reaction

[STEP7.md](STEP7.md) tests one correction originally acquired under legacy
perception, `healthmid ammopresent sceneempty → shoot`, against the current
four-correction parent:

```sh
.venv/bin/python revise.py --previous runs/my-joint-search \
  --legacy-memory runs/my-perception-comparison/memory.json \
  --output runs/my-revision
```

The diagnosis comes from the parent's earlier selection trajectories: long
runs of shooting with no filtered focus, no new kills, and ammunition and
health decreasing. All six actions compete; the replacement is not prescribed.
Each candidate replaces that one acquired record and must preserve the other
three records and 23 runtime decisions before games.

Selection uses the unchanged episode reward on seeds 1001–1008, with parent
winning ties. A strict improvement must survive restart before the three-way
comparison on 1101–1116. Target visits, shooting, ammunition, damage, and
consecutive runs are descriptive outputs alongside kills and survival. The
command stops after this single revision experiment, including NO_ADOPTION.

The first revision experiment ended in **NO_ADOPTION**. All six proposals
preserved the other 23 choices, but the existing shoot reaction scored 43
across the eight selection seeds; alternatives scored 39–42. The parent
survived seven episodes and each alternative six. The closest alternative,
turn_left, shortened the longest target run from 24 calls to four while adding
one death. Improving that local measurement did not improve episode return.

All 56 episodes and 7,024 decisions remain in `runs/revision1/`. No replacement
memory was adopted and the reserved evaluation seeds were not run. The
four-correction player from STEP6 remains the selected policy. See the
[log](WOLFEDOOMLOG.md) for raw sequences and the full selection table.

Environment documentation: [ViZDoom quick start](https://vizdoom.farama.org/introduction/python_quickstart/).
