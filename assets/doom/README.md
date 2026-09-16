# Recorded Doom frames

## Latest frames: retained player, STEP9 evaluation

The main README shows two new, unedited 320 × 240 PNGs from seed 1513,
`doom/runs/joint-mid1/evaluation/parent/seed1513/`. This is the retained
four-correction player under `no-effects` perception, not the failed STEP9
candidate. ViZDoom uses `defend_the_center` and its supplied Freedoom assets.

| Published image | Original | Captured after | Kills | Health |
| --- | --- | ---: | ---: | ---: |
| `retained-seed1513-064.png` | `frame_064.png` | 64 calls / 256 elapsed tics | 5 | 100 |
| `retained-seed1513-128.png` | `frame_128.png` | 128 calls / 512 elapsed tics | 11 | 30 |

The corresponding trajectory records are 63 and 127, with `shoot` in both.
The image copies are byte-identical to the engine captures. Memory SHA-256:
`ef1a98d8093aac0c8eed9c82d4903ab6fab9656e222a9a9f9258760d7352d369`.

```text
4a81f0bcbbac27d6de64e1418e2bbfedf042e9618f72383a6ca74220edb52973  retained-seed1513-064.png
7a1526125b447618fe48c90f4883c10b97cf51ec6878c83a43829152ff5cf761  retained-seed1513-128.png
```

This episode was selected to show successful gameplay. Across all 16 fresh
STEP9 seeds, this same retained memory scored 99 kills and died four times.
The trial candidate also scored 99 kills but died five times, failing the
benefit gate. Neither these screenshots nor the higher total on a different
seed set establish improvement over the retained memory's earlier 90 kills.
The horizon marks the end of observation, not completion of the game.

## Earlier frames: STEP6 selected player

These 320 × 240 PNGs are unedited copies from STEP6's selected player in
ViZDoom's `defend_the_center` scenario, using its supplied Freedoom assets.
They belong to one evaluation episode, seed 914, under `no-effects` perception.
The local source directory is `doom/runs/joint1/evaluation/selected/seed914/`.

| Published image | Original | Captured after | Kills | Health |
| --- | --- | ---: | ---: | ---: |
| `joint-seed914-016.png` | `frame_016.png` | 16 calls / 64 elapsed tics | 1 | 100 |
| `joint-seed914-128.png` | `frame_128.png` | 128 calls / 512 elapsed tics | 8 | 84 |

Each call holds one primitive action for four game tics. Frames are captured
after that action, so the corresponding trajectory records are 15 and 127.
The last image reaches the fixed experiment horizon, not the end of the game.

Selected memory SHA-256:
`ef1a98d8093aac0c8eed9c82d4903ab6fab9656e222a9a9f9258760d7352d369`.

Image SHA-256 hashes:

```text
fcfc068d5af75746e4398c265dda0daf7fd1447d30dabbed08bfa5ff323d3473  joint-seed914-016.png
c9bc00442df8d7a070d64ce20785163272bb29d9556e017b237eaf0e155f114e  joint-seed914-128.png
```

The frames illustrate one successful episode. Across all 16 evaluation seeds,
the selected player died six times. See the [full result](../../doom/WOLFEDOOMLOG.md)
for comparisons and counterexamples.
