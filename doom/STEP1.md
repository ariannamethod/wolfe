# Step 1: WOLFE decisions reach a real Doom world

Declared before the first game run, 2026-09-16.

Question: can the unchanged C WOLFE engine receive a symbolic observation,
choose a typed primitive action, and advance a real ViZDoom environment?

Use ViZDoom 1.3.0 with its bundled `defend_the_center` scenario and Freedoom
assets. Use synchronous PLAYER mode and a fixed four-tic decision quantum.
This first episode is against scenario monsters, not multiplayer self-play.

The action vocabulary contains turning left/right, moving forward, strafing
left/right, and shooting. Each tool holds exactly one engine button for the
same quantum. No aiming, navigation, pickup seeking, or tactical routine is
hidden behind a tool. Abstention applies no buttons and remains visible.

Observation consists of the player's health/ammunition and currently visible
engine-labelled actors. The adapter exposes coarse bearing and resource tokens;
it never emits an action recommendation. Raw labels and numeric variables are
retained beside that text. This uses symbolic perception supplied by the game;
it does not establish learning vision from pixels.

WOLFE's initial examples associate each of 24 combinations of health/ammo/view
bins with one primitive action. A balanced list of actions is shuffled once
with Python Random seed 1729 before any observation or outcome is collected.
This arbitrary initial table is not a tactical teacher or earned experience.
Definitions are frozen for this step; no feedback, correction,
optimization, or best-run selection occurs.

## Gate

- A live ViZDoom process provides the observations.
- Every executed button vector is the literal translation of the recorded C
  WOLFE response, or an explicit all-zero vector for a non-call.
- At least one WOLFE call produces a nonzero button vector, game time advances,
  and a recorded player variable (position, view angle, or ammo) changes.
- The JSONL receipt exposes the before observation, exact model input, full
  response, applied buttons, elapsed tics, reward, and after observation.
- Save real game frames and a short readable trace beside the measurements.

A pass establishes an environment connection only. It does not establish
learning, tactical competence, causal credit for actions, or improvement over
the starting policy. On failure, diagnose this connection before adding work.
After a pass, return the artifacts to Oleg before starting experience updates
or self-play. Preserve failed runs.

Use game seed 17, at most 128 decisions. Health bins are <=25, <=75, >75;
ammo is absent/present. View bins are empty/left/center/right, using the center
of the largest visible labelled object other than the player (middle third
of the screen is center). Raw object names and boxes remain in the receipt;
this salience rule makes no assertion that every labelled object is an enemy.

The next research question remains how consequences should change
context-specific action preference, including delayed outcomes. Match victory
alone is not a causal label for every action in its trajectory.
