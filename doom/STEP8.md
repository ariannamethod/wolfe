# Step 8: let experience select the mid-health centered-object action

Declared 2026-09-17 before candidates or new game data.
Parent code: `b616bb2e9659ec6aaff60ca6c89aa08505d89769`.
Retained four-correction parent memory SHA-256:
`ef1a98d8093aac0c8eed9c82d4903ab6fab9656e222a9a9f9258760d7352d369`.
Legacy reference memory SHA-256:
`7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005`.

## Incoming audit and one question

STEP7 correctly retained the parent: all six proposals were structurally
eligible, but selection returns were 43 for parent/shoot versus 39–42 for
alternatives. All 56 episodes and 7,024 decisions were independently checked.
No child, restart of a selected child, or evaluation was manufactured.

The next diagnosis uses only that retained parent's training episodes
1001–1008 (`revision1/selection/parent`). Mid-health, ammo-present left occurs
147 times in five seeds; center occurs 16 times in four seeds. There are five
center-to-left and two left-to-center transitions, but only one consecutive
left-center-left window and no center-left-center window. This does not
justify treating the pair as another established oscillation.

Test only `healthmid ammopresent scenecenter`, whose current random-prior
choice is move_forward and which has no acquired correction. On seed 1006,
decisions 107–110 repeatedly use move_forward with the same Marine id 14,
angle 260.15625 degrees, ammo 9, and kills 4. Its box grows from 52×113 to
174×195 while health falls 44 -> 32. This is a raw witness, not causal damage
credit. Across all 16 target windows, health decreases by 30, ammo by 3,
and kills increase by 1; outcomes within an action window are not necessarily
caused by that command. The target is a diagnosed question, not a claim that
it is the most frequent or most damaging context.

## One added association, with the exterior fixed

Start each of six proposals from the exact retained four-record parent.
Use the existing C correction API to append one fifth record for the target,
in tools.json action order. Preserve all four existing records exactly.
No replacement action is prescribed: all six primitive tools compete.

Before any games, save every proposed memory, requested correction, complete
24-answer table, and eligibility receipt. Admit a proposal only if the target
actually emits its requested single call with empty arguments, the other 23
`(status, calls)` decisions equal the parent, state contains exactly the four
inherited records plus the requested fifth, and tool counters remain zero.
Keep ineligible proposals and reasons; do not repair or play them. With none
eligible, record NO_REPRESENTABLE_ACTION and stop.

C core, library, corpus, tools, no-effects perception, unmodified game reward,
four-tic action quantum, and 128-decision horizon stay fixed. There is no
second context, history token, hand-designed aiming rule, or new reward.

Reuse `revise.py` through an explicit `--step8` mode instead of copying its
search loop. Its original STEP7 behavior remains available. The original
STEP7 code was committed before editing, and exact source copies were archived
in `runs/revision1-source/`; previous artifacts remain unchanged.
STEP8 reads `parent-memory.json` and
`parent-table.json` from the NO_ADOPTION experiment, never a nonexistent child.

## Selection and persistence

Run the unchanged parent and every eligible proposal once on seeds 1201–1208.
Only summed unmodified episode reward selects a candidate. Parent wins ties;
among strictly improving tied candidates, tools.json order breaks ties.
The move_forward candidate is the explicit parent-matching control.
Local damage, kills during target windows, and target run lengths are only
descriptions; they supply no additional selection score.

With no strict improvement, record NO_ADOPTION and stop. Otherwise seal the
selected identity, all selection returns, and state hash before evaluation.
Reopen the selected memory in a fresh process and require the complete 24
responses to match its saved table, structural eligibility to remain true,
and the target decision to change. A failed restart ends the experiment
without a runner-up.

## Fresh evidence and stopping point

On seeds 1301–1316, compare fresh processes for:

1. Retained four-correction parent, no-effects.
2. Selected five-correction child, no-effects.
3. Original two-correction reference, legacy.

The benefit gate remains positive mean paired return difference AND more
improved than worsened seeds against the current parent. Legacy is a separate
reference and never selects a candidate or alters the gate. Reward improvement
does not establish restored legacy survival or general competence.

Report kills, deaths, fixed-horizon survival, and the existing high-health
empty/left alternating windows for all conditions. Report target visits,
shoot calls, positive ammo/health decreases and kill increases within those
action windows, and the longest consecutive target run. Aggregate longest
run is the maximum within any episode. Legacy encodes the same target text
using its own perception; the underlying observed situations can differ.
Show actual transitions and every regression beside the measurements.

At most 56 selection and 48 evaluation episodes run once. Previously reserved
STEP7 evaluation seeds 1101–1116 remain unused. Preserve success or failure,
inspect raw behavior, obtain an independent read, and return the turn to Oleg.
No second context, extra generation, altered reward, or additional seeds follow
silently from this step.
