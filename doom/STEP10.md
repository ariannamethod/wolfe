# Step 10: one remembered health change before an empty-scene choice

Declared 2026-09-17 before new model calls, corrections or games.
Incoming commit: `0a1579702e485f16ae826780606740655bade42a`.
Retained parent SHA-256:
`ef1a98d8093aac0c8eed9c82d4903ab6fab9656e222a9a9f9258760d7352d369`.

## Incoming result and training witness

STEP9's source/protocol/engine hashes and raw non-tied outcomes match its
independent audit: 344 episodes, 40,128 decisions, mechanism PASS, benefit FAIL.
The five-record candidate is not promoted. The four-record parent remains.
Exact incoming sources are archived in `runs/joint-mid1-source/`.

The prior core review showed that identical three-token requests yield the
same response despite changing raw health. This motivates checking one small
piece of history. The concrete new witness comes from retained-parent
selection 1401–1408, not from new game outcomes. At seed 1406, decisions 73
and 74 both have health 48, ammo 20, angle 302.34375, four kills, no focus,
and the same input `healthmid ammopresent sceneempty`. Before decision 73,
health fell 80 -> 48; before decision 74 it remained 48 -> 48.
The 17 visits to this context split into four following a health decrease
(1402:47,48; 1406:73,86) and thirteen without one.

This is an observable distinction, not proof that it needs a different action.
No recent decrease does not imply safety, and a net health change need not
identify the cause of damage. Do not prescribe a dodge or a turn.

## One causal bit, opt-in

With `run.py --history previous-damage`, append the single token
`damagerecent` exactly when current predecision health is less than the
previous decision's predecision health. At the first decision it is false.
Use only already observed health; never current action outcome or future
reward. Each policy derives the bit from its own trajectory. Record base
input, previous observed health and the bit alongside the actual input.
When false, send the original three-token input without an added token.

Keep the existing default and no-effects label selection unchanged. Do not
filter zero-width boxes: tagged ViZDoom 1.3.0 encodes width as max minus min,
so one visible column can have width zero. This separate suspicion did not
justify changing perception. C core, library, initial corpus, tools, counters,
reward, four-tic actions and 128-decision horizon are fixed.

## Representation before game selection

`history.py` enumerates the 24 original inputs in corpus order, then those
same 24 with the suffix. Preserve the complete 48-response parent table.
Its original 24 full responses must match the incoming parent table. Each
flagged response must have the same `(status, calls)` as its unflagged parent
counterpart; full reasoning may differ. An unknown word has nonzero influence
in WOLFE, so this equivalence is tested, not assumed. Failure means
BASELINE_CHANGED: preserve evidence and stop before candidates or games.

The sole target is `healthmid ammopresent sceneempty damagerecent`.
Create six independent children from byte-identical parent states, appending
one target correction in tools.json order. Each must actually emit its requested
single empty-argument call, retain all four original records exactly, contain
exactly five records and zero counters, and preserve the other 47 `(status,
calls)` decisions. Save all six states, tables and eligibility verdicts before
games. No fallback action, corpus expansion or C patch may rescue a rejected
proposal. No eligible action means NO_REPRESENTABLE_ACTION. Only eligible
actions identical to the parent's target means NO_ALTERNATIVE_ACTION. Both
stop before games. The parent-matching requested action is shoot.

## One selection and fresh evaluation

If a different eligible target choice exists, run parent and every eligible
proposal with no-effects perception and this same history encoding on seeds
1601–1608. Rank by summed unmodified episode reward: parent wins ties, first
strict maximum in tool order wins candidate ties. No local damage, target
visits, safety score or survival bonus enters selection.

No strict improvement means NO_ADOPTION and stop. Otherwise seal the choice,
all selection returns and memory hash before reloading in a fresh process.
All 48 complete responses must match the selected table; repeat the structural
gate and require a changed target. Failure stops without a runner-up.

On fresh seeds 1701–1716 compare parent and child, both with the history bit
and no-effects perception. The benefit gate is unchanged: positive mean
paired reward difference AND more improved than worsened seeds. Report kills,
deaths, survival through the fixed horizon, target visits, the bit's actual
changes, and all non-tied trajectories. No legacy-reference games are needed
to answer this one comparison. The baseline equivalence check ensures that
the parent has not acquired a new action just from receiving the token.

At most 56 selection and 32 evaluation episodes. Failed representation,
NO_ADOPTION and failed fresh benefit are valid completed outcomes; retain
the four-record reference unless benefit passes. Preserve all evidence,
independently inspect the result, publish within existing authority and return
the turn. Do not add another bit, alter the token/target/threshold/seeds, relax
the fixed exterior, rewrite C, or try another generation after seeing results.
