# Step 7: revisit one acquired reaction after the perception change

Declared 2026-09-17 before candidates or new game data.
Parent code: `f4e28129d04ad5edfd65185eebfda834753a701d`.
Four-correction parent memory SHA-256:
`ef1a98d8093aac0c8eed9c82d4903ab6fab9656e222a9a9f9258760d7352d369`.
Legacy reference memory SHA-256:
`7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005`.

## Incoming result and diagnosed question

The raw STEP6 audit reproduces its 36 eligible proposals, selection 50 versus
5, complete restart, and fresh reward totals 84/11/14 (child/parent/legacy).
Child deaths are 6 versus 13 and 4. Its high-health empty/left alternating
windows disappear on that evaluation sample. All three earlier acquired
choices survive; only the previously uncorrected left-object choice changed.

Diagnosis for this new step uses only the selected child's training episodes
801–808. All eight survived the fixed horizon. Of their 1,024 decisions,
75 use `healthmid ammopresent sceneempty`, in four seeds. That acquired
correction still chooses shoot, having originally been selected under legacy
perception. Its observed windows consume 21 rounds, lose 82 health, and gain
zero kills. These associations do not prove that shooting caused the damage.

Seed 806 decisions 79–112 give a concrete witness: 34 consecutive shoot calls
with no focus label, 136 tics, ammunition 14 -> 5, health 44 -> 16, no kills.
Seed 805 decisions 102–127 give another: 26 calls, ammunition 14 -> 6, health
46 -> 32, no kills. The most frequent uncorrected input is instead mid-health
left (113 visits). This step explicitly tests the diagnosed acquired empty
reaction, not a claim that it was automatically the most frequent context.
Evaluation seeds 901–916 are not used to choose or rank the next action.

## One mechanism and structural gate

Fix the single target `healthmid ammopresent sceneempty`. Construct six
independent descendants, in tools.json order, from byte-identical copies of
the four-correction parent. Use the existing C correction API to replace its
second correction record. Keep the other three correction records exact.
The previous parent and all historical evidence remain immutable.

Save all six states and complete 24-answer tables before any new games.
A candidate is eligible only if the target actually emits its requested
single call with empty arguments, all other 23 `(status, calls)` decisions
equal the parent, its state has exactly the expected four corrections, and
all tool counters remain zero. Retain ineligible candidates and specific
reasons; do not play or repair them. With no eligible candidate, record
NO_REPRESENTABLE_ACTION and stop.

C core, library, initial corpus, tools, no-effects perception, original game
reward, four-tic action quantum, and 128-decision horizon remain unchanged.
There is no history token, additional context, hand-picked replacement action,
new reward, or new credit-assignment mechanism in this step.

## Whole-episode selection and restart

Run the parent and every eligible candidate once on seeds 1001–1008 under
no-effects perception. Select only by summed unmodified episode reward.
Parent wins ties; the first improving maximum in tools.json order wins ties
among candidates. The shoot candidate is an explicit parent-matching control.
Empty-scene shooting, health loss, and survival get no extra selection bonus.

With no strict improvement, record NO_ADOPTION and stop. Otherwise seal the
chosen identity, selection returns, and state hash before evaluation. Reopen
the chosen memory in a new process and require all 24 complete responses to
match the selected table, structural eligibility to remain true, and the target
decision to differ from its parent. Failure ends this experiment without a
runner-up. No candidate is retuned after selection.

## Fresh evaluation and behavior

On seeds 1101–1116, run three conditions from fresh processes:

1. Four-correction parent, no-effects.
2. Selected revised child, no-effects.
3. Original two-correction reference, legacy.

The primary benefit gate is positive mean paired reward difference AND more
improved than worsened seeds against the current parent. The legacy reference
does not select the action or change the benefit gate. Report both gates
separately: a persistent revised decision is not by itself a reward benefit.

Report rewards, kills, deaths, and survival through the fixed horizon for all
three conditions. Also report per-episode and aggregate visits to the target,
target shoot calls, rounds consumed, health lost, kills gained, and longest
consecutive target run. These are descriptive measurements, not a reward.
Keep the STEP6 A-B-A/B-A-B window counts visible as a separate behavior measure.
Compare actual sequences and any regressions beside the totals. Fewer target
visits do not by themselves establish a better reaction; a reward improvement
does not establish restored legacy survival or general competence.

At most 56 selection and 48 evaluation episodes run once. Preserve both
success and failure, inspect the raw behavior, obtain an independent read,
and return the turn to Oleg. No second context, generation, reward change,
or additional seed set follows silently from the result.
