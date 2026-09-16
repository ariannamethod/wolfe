# Step 3: inherit one memory, let experience choose the next context

Declared 2026-09-16 before new candidates or new game episodes.
Parent code: `4531cd5f43e9c080aa6098a6764e4d91067c49b6`.
Parent memory: step 2's selected state, SHA-256
`9f53271cde84088f58c62cb9e2e95eec54e99f4634b0cd8c74349c5ed30eb0cc`.

## One question

Can the already selected policy acquire a second useful association while
retaining its first acquired decision? Use the existing bounded C correction
memory. Keep the C engine, perception, six actions, corpus, scenario, four-tic
action quantum, reward, and 128-decision horizon unchanged.

The incoming audit recomputed step 2's raw returns and restart table. Its
16-seed evaluation remains historical evidence and is not used to choose the
next context, action, or candidate. The analysis below reads only the selected
policy's old selection episodes, seeds 101–108.

## Let visitation choose one context

Count exact input-text visits in all eight old selection trajectories for
step 2's selected policy. Exclude texts already present in its corrections.
Choose the largest remaining count; break ties by order in the unchanged
24-row initial_examples.jsonl. Freeze the counts, selected text, input hashes,
and parent-state hash before constructing candidates or running new episodes.

This rule selects `healthmid ammopresent sceneempty`, with 154 visits out of
615 decisions. The inherited `healthhigh ammopresent scenecenter` has 208
visits and is excluded. Counts localize the experiment; they do not prove
that the current action causes a bad outcome. Of those 154 visits, 118 occur
in just two episodes.

The same old data reveal a perception limitation: central Blood and BulletPuff
labels often sustain shooting after the first kill. This step deliberately
retains the declared observation function. A perception change is a separate
question, not an additional intervention in this experiment.

## Six independent children of the same parent

Copy the frozen parent state separately for every candidate. Append exactly
one correction for the selected context, with empty arguments, for each of
the six actions in tools.json order. No candidate inherits another candidate.
The unmodified parent is the seventh policy and wins ties. Record complete
24-response tables and changes relative to the parent for all candidates.

Selection seeds are 301–308, eight episodes per policy. Maximize the sum of
unmodified scenario reward. Use strict improvement over the parent; among
tied improving candidates, the first maximum in tools.json order wins. No
extra reward for aiming, shooting, movement, survival, or avoiding repeats.
No per-action causal credit is inferred from the episode return.

Seal selection identity, returns, and state hash before evaluation. Reopen the
selected memory in a fresh process and require the entire 24-response table
to match. Counters stay zero; the original parent state and old receipts must
remain byte-identical. The persisted selected state must contain the original
correction unchanged plus exactly the one new correction.

## Gate and end of turn

Evaluation seeds are 401–416. Run only the frozen parent and the one selected
child, with no memory updates during either selection or evaluation episodes.
These seeds are not opened until selection is sealed.

The accumulation mechanism passes only if a child is adopted, at least one
action/status decision changes versus the parent, the old corrected context
still chooses the same action/status as the parent, the two corrections are
preserved as specified, and all 24 full responses survive process restart.
Publish this separately from the benefit gate: positive mean paired return
difference AND more improved than worsened evaluation seeds.
If retention or restart fails, record mechanism FAIL and benefit NOT_RUN,
then stop before opening evaluation seeds.

No adoption, retention failure, or failed benefit is a valid result of this
step. Keep all counterexamples. Do not try another context, parent, seed set,
ranking rule, perception function, or generation to manufacture a pass.
Implementation defects may be repaired while preserving failed artifacts;
the experimental law does not change.

This tests one additional inherited memory association on one scenario.
It does not establish open-ended learning, visual recognition, or self-play.
Return raw behavior and both gate results to Oleg, then stop this step.
