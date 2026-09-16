# Step 6: jointly revise two neighboring decisions

Declared 2026-09-16 before candidates or new game data.
Parent code: `76a3c71fb5d5be5963e571cf5c13821bde87a75f`.
Three-correction parent memory SHA-256:
`31fa2dc243e9aca6c7bfce5444a06c203fa08db178de8349ec8b99fc359b9b92`.
Legacy reference memory SHA-256:
`7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005`.

## Observed conflict and one mechanism

Oleg proposed joint selection for these two contexts:

- A: `healthhigh ammopresent sceneempty`, currently turn_left.
- B: `healthhigh ammopresent sceneleft`, currently turn_right.

The incoming independent audit read only the parent's training trajectories
601–608: 828 decisions, A visited 199 times and B 169. There are 104 consecutive
A-B-A windows and 99 B-A-B windows, counted with overlap. In 95 of the latter,
both B records focus on the same object id. A is the third acquired correction;
B is still an initial random-prior association, not an acquired correction.

At seed 601, decisions 5–8 alternate A/turn_left and B/turn_right. The angle
alternates 19.33594 and 33.39844 degrees; B twice focuses on Demon id 3.
Position stays (0,0), health 100, ammo 25, kills 1, reward zero throughout.
The pair is explicitly proposed from this observed behavior, not selected by
an invented automatic search over contexts or by held-out rewards.

Use the existing correction API to revise A and add B together. Keep
no-effects perception, C core, initial corpus, six primitive tools, game
reward, four-tic quantum, and 128-decision horizon unchanged. No history token
or per-action credit mechanism is added in this experiment.

## Complete proposal grid and structural eligibility

Construct all 36 proposals in tools.json order, A outer and B inner. Every
proposal starts from a fresh byte-identical parent copy. Correct A first,
replacing its existing third slot; then correct B, appending a fourth record.
The first two correction records remain exact. The prior parent state and its
history are immutable even when a descendant revises an acquired decision.

Before any games, save every proposed state, requested pair, complete 24-answer
table, and eligibility receipt. A proposal is eligible only when:

- A and B actually emit their requested single call with empty arguments;
- all other 22 `(status, calls)` decisions equal the parent;
- state has exactly the expected four corrections and zero counters.

The C API rebuilds a shared field; a written correction alone is not evidence
of these properties. Ineligible proposals remain recorded with their specific
diff and are not played or repaired. This is a 36-proposal grid, with at most
36 playable candidates; report the actual count. With no eligible proposals,
record NO_REPRESENTABLE_PAIR and stop before games. Do not silently broaden
the mutable decision set. Changes to numerical reasoning on unchanged calls
do not violate the 22-decision constraint.

## Whole-episode selection

Run the unchanged parent and every eligible proposal under no-effects on
seeds 801–808. Rank only by summed unmodified episode return. Parent wins
ties; among improving tied proposals the first in the fixed grid order wins.
The parent-matching pair (turn_left, turn_right) stays as an explicit control.
Loop disappearance, survival, and kills get no additional selection bonus.

If none strictly improves the parent, record NO_ADOPTION. Otherwise seal
identity, all selection returns, and chosen memory hash before evaluation.
Reopen the chosen memory in a new process; require all 24 complete responses
to match the selected table and its structural eligibility to remain true.
At least one target decision must differ from the parent. A restart or
structural failure ends the experiment without choosing a runner-up.

## Fresh evaluation, behavior, and survival

On seeds 901–916 run three conditions from fresh processes:

1. Three-correction parent, no-effects.
2. Selected joint child, no-effects.
3. Original two-correction reference, legacy perception.

The primary benefit gate remains positive mean paired return difference AND
more improved than worsened seeds against the current filtered parent. The
legacy reference neither selects the candidate nor changes the reward gate.

Also report, for each condition, raw A-B-A and B-A-B windows, same-object B-A-B
returns, and A-B-A windows per 100 decisions. Compare actual sequences beside
these counts: fewer visits alone do not prove better aiming. These are behavior
measurements, not a hidden reward or candidate filter.

Report kills, deaths, and survival through the fixed horizon in all three
conditions. Compare the child with legacy on these very same seeds. Passing
the reward gate alone does not establish restored survival, elimination of
oscillation, or general competence. Do not move a threshold to rename a tradeoff.

At most 296 selection episodes and 48 evaluation episodes are run once. Both
success and failure are preserved. This command has no extra generation,
alternative pair, changed seed set, history feature, or reward adjustment.
Inspect raw results, obtain an independent read, and return the turn to Oleg.
