# Step 5: adapt one inherited decision to filtered perception

Declared 2026-09-16 before new candidates or episodes.
Published parent: `911a5b4805090a525cbbd933757f1ef2191e02e5` plus the local
step-4 perception change. Its exact source files are preserved separately in
`runs/perception1-source/`; the failed experiment remains unchanged.
Parent memory SHA-256:
`7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005`.

## One adaptation

Keep no-effects perception exactly as declared in STEP4. Preserve the two
existing corrections and their action/status decisions. Test one additional
correction through the existing C memory API. The C engine still chooses all
game actions; no new perception, action, reward, or planning mechanism is
introduced. Four-tic actions and the 128-decision horizon remain fixed.

The incoming audit reproduces STEP4's negative result from all 32 raw episodes.
Its evaluation rewards motivate the question, but are not used to select the
new context or action. No episode on seeds 501–516 is repeated or relabelled.

## Choose the first affected context from older experience

Read STEP4's historical-inputs.jsonl, which contains alternative encodings of
the eight STEP3 selection trajectories, seeds 301–308. For each trajectory,
take the earliest decision whose legacy and no-effects action choices differ
and whose no-effects input has no inherited correction. Count these first
eligible inputs across the eight trajectories. Pick the most frequent, with
ties resolved by the original 24-example order. Freeze all supporting hashes,
first-decision witnesses, counts, and the selected context before candidates.

This rule selects `healthhigh ammopresent sceneempty` in all eight trajectories,
at decision 3. The old choice is strafe_right under no-effects. The legacy
choice does not prescribe a new action: all six actions compete below.

## Selection and restart

Create six children as separate byte-identical copies of the parent, each
with one new correction for this context and empty arguments. The unchanged
parent is the seventh policy. Run all seven under no-effects on seeds 601–608.
Choose the largest sum of unmodified episode return. Parent wins ties; among
strictly improving tied children, the first in tools.json order wins.
Do not filter candidates by preferred action or perceived tactical sense.

Seal the chosen identity and memory hash before evaluation. In a fresh
process, reopen the selected state and require all 24 full responses to match
its candidate table. It must contain the unchanged two inherited corrections
plus exactly one new record, all counters zero. Both old corrected inputs must
retain their previous action/status. At least one other choice must change.

No adoption or failed retention/restart ends this experiment before evaluation.
Record the mechanism outcome and benefit NOT_RUN without trying a runner-up.

## Fresh evaluation and scope of the claim

Use seeds 701–716 only after selection and the mechanism check. For each seed
run three fixed conditions from fresh processes:

1. Parent memory, no-effects: primary adaptation baseline.
2. Selected child, no-effects: the proposed adaptation.
3. Parent memory, legacy: a reference for the earlier observation system.

The adaptation benefit gate is positive mean paired return difference AND
more improved than worsened seeds versus the filtered parent. Report kills,
deaths, and all paired returns. Separately publish the child's comparison to
the legacy reference; improvement over the filtered baseline alone is not
evidence of recovering the legacy policy's earlier performance. The reference
does not select a child or change the benefit criterion.

On a pass, inspect raw behavior, obtain an independent read, and return the
turn. On a failure, preserve it and diagnose the mechanism. Any warranted
repair must be a separately declared experiment with fresh evaluation; never
change this experiment's contexts, seeds, reward, or thresholds to force a pass.
There is no automatic extra generation or silent fallback in the command.

The old experiments remain byte-identical. Neither legacy default perception
nor previously selected memory is silently replaced by this experiment. No
commit, push, multiplayer, or Arduino work is part of this step.
