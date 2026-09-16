# Step 4: separate transient effects from the observed scene

Declared 2026-09-16 before implementation or new episodes.
Parent code: `911a5b4805090a525cbbd933757f1ef2191e02e5`.
Frozen memory: step 3's selected state, SHA-256
`7342b16ea85139e4d19979984223bebecafe9e9c8b0461c86b72236aa2735005`.

## One intervention

Compare the existing largest-visible-label observation (`legacy`) with
`no-effects`: exclude exactly object names Blood and BulletPuff before the
same largest-area selection, object-id tie break, and left/center/right bins.
Both exclude DoomPlayer as before. Health and ammo bins stay unchanged. All
other object names remain eligible; this is not an enemy/alive-object filter.
Record the actual selected label beside each decision, including null when
none qualifies. Keep legacy as the default for existing episode commands.

The same two-correction memory chooses actions through the unchanged C engine
in both conditions. No correction, feedback, new tools, reward shaping, horizon
change, or policy selection is performed. This is a hand-specified change to
game-provided symbolic perception, not learned visual recognition.

## Incoming evidence

Step 3's raw selection/evaluation returns, source hashes, state hash, and full
restart table were rechecked before its publication. Only its selected policy's
old selection trajectories (301–308) motivated this intervention. They contain
1,005 decisions: 549 focus on effects (30 Blood, 519 BulletPuff). None of those
549 has another eligible nonplayer object. This supports effects keeping a
scene nonempty, not the stronger claim that they hide a visible live enemy.

On those same historical states, the alternative encoding would change 549
inputs and 545 choices under the frozen 24-response table. In 240 cases the
change would be move_forward to shoot: the inherited mid-health empty-scene
association makes less shooting an uncertain prediction. Filtering may hurt
a policy whose memory was selected under the old observation function.

Before new games, preserve old-input hashes and an offline receipt of both
encodings/choices for all eight historical trajectories. This diagnoses the
mechanism only; do not treat it as a counterfactual episode return.

## One paired experiment

Use exactly seeds 501–516. For each seed run legacy and no-effects once, from
fresh game/C processes with identical memory. There is no selection set or
later tuning: the single proposed filter is fixed above. Preserve all raw
trajectories, label focus, frames, and unmodified scenario reward.

Keep the six existing buttons, four-tic quantum, 128-decision horizon, corpus,
map, and all remaining game settings unchanged. Seal protocol/code/input hashes
and a copied frozen memory before games. The complete 24-response C table must
match the previous selected table; no learned decision is edited.

## Gates and stopping rule

The mechanism gate requires that every filtered focus follows the exact
two-name exclusion and original selection/bin rules, that the offline receipt
contains an actual changed input and changed C choice, and that at least one
paired live episode first diverges in action from an identical raw state due
to the observation filter. Every live response must match its frozen table,
and memory/core/prior inputs must remain unchanged. A filter producing no
action change does not pass the behavioral mechanism gate.

The separate benefit gate is positive mean paired return difference AND more
improved than worsened seeds, comparing no-effects against legacy. Publish
all returns, kills, deaths, and actual ammo use as well; better reward alone
does not establish better shooting. No assumed direction for ammo use is a
success condition.

If the benefit fails, keep the opt-in filter and failed evidence as an
experiment; do not relabel it as an improvement or alter the default. Do not
retrain the memory, vary excluded names, try other seeds, or lengthen episodes
in this turn. A passed gate also ends the step. Implementation defects may be
repaired with failed artifacts retained; the experimental law stays fixed.

Return observed behavior and both gate results to Oleg. Further perception,
policy adaptation, multiplayer, and hardware work remain separate steps.
