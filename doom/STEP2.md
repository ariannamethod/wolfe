# Step 2: consequences select one persistent memory change

Declared 2026-09-16, before generating candidates or collecting new episodes.
Parent: step 1, commit `221c028aaf93efde25aa8f212b923c43e06957df`.

## One mechanism

Use WOLFE's existing bounded corrections as a policy-search substrate. The
unchanged C engine remains the action chooser in every episode. An outer
experiment proposes memory variations and selects one using actual episode
reward; it does not substitute its own action choices during play.

The only mutable example text is:

```text
healthhigh ammopresent scenecenter
```

This is the first observation in the already recorded step-1 episode. That
episode motivated the choice of context and is not evaluation data here.
Keep observation bins, action definitions, initial corpus, scenario, four-tic
quantum, and 128-decision horizon unchanged. No pretrained parameters, gradient
update, hand-written aiming action, or additional reward shaping is introduced.

Construct six candidates, one for each action in the current tools.json order.
Each is a fresh C model with one explicit, schema-valid correction mapping the
fixed text to that action with empty arguments. No candidate inherits another
candidate's record. An unchanged ancestor is a seventh policy. The candidate
which repeats the original corpus association is retained as a control.

The correction rebuilds the shared numerical field. It may change decisions
for other observations too. Record the complete table of C decisions for all
24 declared observation texts before and after each candidate; do not claim
the intervention is confined to one runtime decision.

## Selection before unseen evaluation

Selection seeds are the eight integers 101 through 108. Run the ancestor and
all six candidates once on each seed. Maximize the sum of the scenario's
unmodified `get_total_reward()` (equivalent to the mean with equal counts).
Do not reward a shot, turn, or survival separately. Each candidate's entire
episode receives its observed return; individual actions receive no invented
causal labels.

If the ancestor ties for the maximum, retain it and record NO_ADOPTION. If
several candidates strictly improve on the ancestor, take the first maximum
in tools.json order. No fallback ranking or selection of a different context.

Before evaluation, seal the chosen identity, selection results, and selected
state hash. Copy the one chosen state into a separate persisted file. Reopen
it in a fresh Python process/C model and require the 24-decision table to
match the selected candidate's table. Reward counters remain zero; any changed
decision must be carried by the explicit correction.

Evaluation seeds are the sixteen integers 201 through 216. Open these only
after selecting and sealing the candidate. Run exactly that candidate and the
unchanged ancestor, with no corrections/feedback during evaluation. Preserve
all paired returns, deaths, kills, trajectories, and frames.

## Gate and stopping rule

The memory mechanism passes only if a candidate is adopted, at least one C
decision changes versus the ancestor, and the complete changed decision table
survives process restart from the selected state. The fresh-world benefit gate
also requires positive mean paired reward difference and more improved than
worsened evaluation seeds. Publish both results separately.

These sixteen pairs provide a bounded observation on one scenario; they are
not a statistical claim of general Doom skill or multiplayer win-rate growth.
This is one generation of policy search through example memory, not self-play.

If there is no adoption or no fresh-seed benefit, preserve that result and
stop this step. Do not try another context, criterion, seed set, or action
vocabulary to manufacture success. Code defects may be repaired with their
failed artifacts retained. The experiment's law stays fixed.

Return the raw behavior and outcomes to Oleg after this step. Multiplayer,
multi-generation search, finer perception, and delayed-action credit remain
separate future questions.
