# Step 9: jointly select mid-health center and empty-scene reactions

Declared 2026-09-17 before candidates or new game data.
Incoming code: `4cd8fbae49cfa3a286344b4aae27416a8ea515ae`.
Retained four-correction parent SHA-256:
`ef1a98d8093aac0c8eed9c82d4903ab6fab9656e222a9a9f9258760d7352d369`.
Legacy reference SHA-256:
`7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005`.

## Hypothesis origin and one joint intervention

STEP8's incoming raw audit confirms 104 episodes, 12,748 decisions, mechanism
PASS and benefit FAIL: the selected shoot candidate scores 77 versus parent
80, with seven versus five deaths. It is not promoted; the four-record parent
remains the reference. STEP7's isolated empty-scene revision also found no
improvement over that same parent.

The hypothesis for this pair arose explicitly from STEP8 evaluation seed 1307:
an earlier centered kill leaves mid health and enters the old empty-scene
shoot reaction, while the parent kills later at low health and then strafes.
Oleg authorized investigating that interaction. This is knowledge acquired
from a previous evaluation, not an independent training-only discovery.
None of those old returns will select the new pair; evaluation uses new seeds.

Inspection of training 1201–1208 provides a separate witness. The old parent
has 18 center and 53 empty visits, with no direct center-to-empty transition.
The failed shoot candidate has 23 center and 76 empty visits. Its one direct
center-to-empty transition follows a kill at seed 1201, decision 71. Decisions
72–94 then issue 23 empty-scene shoot calls, ammo 15 -> 9 and health 68 -> 24.
That candidate nevertheless survives and improves this training seed's return
from 2 to 4. This witnesses a reachable sequence, not proof that the empty
reaction is harmful or that joint change will help. There are no reverse
empty-to-center transitions or alternating triples in those training records.

Fix the pair:

- A: `healthmid ammopresent scenecenter`, currently move_forward, uncorrected.
- B: `healthmid ammopresent sceneempty`, currently shoot, acquired record 2.

No particular replacement action is prescribed. Hold C core, library, corpus,
tools, no-effects perception, original reward, four-tic quantum and 128-decision
horizon fixed. The parallel read-only C audit does not change this experiment.

## Grid, memory, and structural gate

Reuse `joint.py` through explicit `--step9`; preserve its original STEP6 mode
and the high-health loop statistics used by later scripts. Exact incoming
STEP8 sources were archived in `runs/center1-source/` before editing.
Read `parent-memory.json` and `parent-table.json` from the failed experiment.
Its selected candidate is used only as historical diagnosis, never as parent.

Construct all 36 proposals in tools.json order, A outer and B inner. Each
starts from a byte-identical parent copy. Correct A first, appending a fifth
record; correct B second, replacing the existing second record in place.
Retain all other three inherited records exactly. Persist every proposed
state, requested pair, full 24-response table, and eligibility receipt before
games. Admit only proposals which actually emit both requested single calls
with empty arguments, preserve the other 22 `(status, calls)` decisions, have
exactly the expected five records and zero counters. Record and exclude any
structural failure without repair. No eligible proposals means
NO_REPRESENTABLE_PAIR and no games.

## Selection and restart

Run the parent and every eligible proposal once on seeds 1401–1408. Rank only
by summed unmodified episode reward. Parent wins ties; the first improving
maximum in grid order wins candidate ties. The pair (move_forward, shoot)
is the explicit parent-matching control. Local kills, health, sequence counts,
or fewer empty-scene shots supply no extra reward or candidate filter.

No strict improvement means NO_ADOPTION and stop. Otherwise seal chosen
identity, all selection returns and memory hash before evaluation. Reopen
the selected memory in a new process and require all 24 complete responses
to match its saved table, structural eligibility to hold, and at least one
target decision to change. Failure ends the step without a runner-up.

## Fresh evaluation and raw behavior

On seeds 1501–1516 compare fresh processes for parent and selected child with
no-effects perception, plus the original two-record reference with legacy.
The primary benefit gate remains positive mean paired reward difference AND
more improved than worsened seeds against the current parent. Legacy is an
independent reference, never a selection or adoption criterion.

Report reward, kills, deaths and survival through the fixed horizon. Keep the
original high-health A-B-A/B-A-B statistics separate from this new pair.
For the new pair report each context's visits, direct A-to-B transitions,
those A-to-B transitions with a kill increase during the preceding A action,
and the longest consecutive B run (aggregate is the episode maximum).
These are descriptive measurements, not causal credit or a hidden bonus.
Legacy observations use legacy encoding even for identical context text.
Inspect actual sequences and all regressions alongside totals. A reward pass
does not by itself prove restored legacy survival or a generally solved game.

At most 296 selection and 48 evaluation episodes run once. Previously reserved
1101–1116 remain unused. Preserve every proposal and outcome, independently
read the raw result, then return the turn. No extra pair, generation, reward,
observation feature, or C change follows silently from the result.
