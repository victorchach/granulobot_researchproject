# Triangle of 3 units, 3.25 V on every motor (2026-10-14)

The run reviewed at the late-October team meeting. It is the evidence behind
the decision to move from 3 units to a 6-unit ring (`docs/decisions.md`).

## How it was made

- Run on Victor's machine on 2026-10-14 at 21:38, after pulling commit
  `b332380` (the 0.6 s run committed in `b332380` is a different one). The
  exact command was not recorded. Its parameters are the simulator defaults
  of that commit, and they are still the defaults on `8233746`.
- To rerun it: `make sim NAME=triangle` (3 s simulated, triangle, 3.25 V on
  A, B and C, all other values by default). It takes a while at
  `dt = 1e-5 s`; probe first with `ARGS="--duree 0.2 --sans-gif"`.
- Files, as the simulator wrote them: `test_3_granulobots.csv` (200 Hz
  measurements), `.json` (parameters, assumptions, summary), `.gif` (25 fps).

## Question

What does a closed ring of 3 units do when every motor gets the same voltage?

## Key numbers (from the JSON summary)

| Unit | Net body rotation (turns) | Max centre displacement (mm) |
| --- | --- | --- |
| A | -0.45 | 11.7 |
| B | -0.39 | 13.7 |
| C | -0.38 | 13.3 |

- All three bodies turn the same way. On an odd ring, neighbours cannot turn
  in opposite directions, so the ring is frustrated. This is why the next
  target is an even ring (hexagon).
- The three magnetic pairs stay coupled: the active-to-free magnet distance
  stays between 8.00 and 8.50 mm (8.05 mm at the start) and no detachment is
  detected.
- Maximum shell overlap: about 5 µm. Maximum magnetic force: 12.3 N.

These numbers describe the model, not the real robots. Physical convergence
in `dt` was not established at the time (see `docs/model.md`).
