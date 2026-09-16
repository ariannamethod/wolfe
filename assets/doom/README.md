# Recorded Doom frames

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
