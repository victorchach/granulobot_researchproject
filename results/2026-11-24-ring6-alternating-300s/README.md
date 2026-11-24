# Ring of 6 units, alternating ±3.25 V, 300 s (2026-11-24)

The same hexagon as [`2026-11-24-ring6-alternating/`](../2026-11-24-ring6-alternating/),
with alternating open-loop biases u_i = (-1)^i × 3.25 V, A positive (paper
eq. 8), and uniform shell friction (`mu_shells = 0.6`). This time it runs for
the 5 minutes that roadmap step 1 asks for.

## How it was made

```
make sim NAME=ring6/uniform_dt1e4_300s ARGS="--params configs/ring6_alternating.json --dt 1e-4 --duration 300 --no-gif"
```

It ran on `main` at `fcc6052`, with a clean working tree. The simulator code
in `src/` has not changed since `1b3d045` (spec 006). The run took 2 h 15 of
CPU on Victor's Mac, about 27 s of CPU per simulated second. Sleep stretched
that to 5 h 14 of wall time.

| File | What it is | Made by |
| --- | --- | --- |
| `uniform_dt1e4_300s.json` | parameters, assumptions, summary | the simulator |
| `minute4-5_x4.gif` | t = 240 to 300 s, one frame every 0.2 s, played 4 times faster; the dashed circles are the ring at t = 240 s | plotting script, from the CSV |
| `drift_and_shape.png` | four frames (240, 260, 280, 300 s) over the 240 s ring, and two curves over the whole run: centroid displacement, and each unit's distance to the centroid | plotting script, from the CSV |
| `shape_exaggerated.png` | the ring's outline at 300 s against the regular hexagon, with the drift and the rigid rotation removed and the deformation magnified 30 times | plotting script, from the CSV |

Not versioned:

- the CSV (229 MB). Rerun the command above to get it back.
- the GIF of the full run. The simulator's 25 fps GIF of 300 s would weigh
  more than 100 MB, so the run used `--no-gif`.
- the plotting scripts. They were scratch scripts outside the repo, and the
  figures can only be redrawn from them for now. Putting them in the repo is
  a code change, so it needs a spec.

## Question

Does the liquid state seen over 60 s (journal entry 3) hold for 5 minutes?
The step 1 criteria from `docs/roadmap.md`: the ring keeps its shape, the
rotor directions keep alternating, and the sum of the rotor speeds stays
close to zero. A second question: does the slow drift seen at 60 s stay
linear?

## Key numbers

From the JSON summary, and from the CSV for the time series (after the 0.5 s
start ramp).

| | 60 s (entry 3) | 300 s |
| --- | --- | --- |
| Net body rotation | ±29.13 turns | ±146.17 turns (about 29 rpm) |
| Mean body speed | | 2.967 rad/s over 1 to 60 s, 2.967 rad/s over 240 to 300 s |
| Net rotation of the active rotors in the lab frame | 0.002 turn at most | 0.004 turn at most |
| Rotor abs/rel speed ratio | 0.087 | 0.087 |
| Rotor directions alternating | 11 900 of 11 900 samples | 59 900 of 59 900 samples |
| Sum of the six relative rotor speeds | 0.0002 rad/s on average, 0.13 peak | 0.0002 rad/s on average, 0.13 peak |
| Magnet pairs in contact | 100 % of samples | 100 % of samples, no detachment |
| Neighbour distances | constant within 0.1 µm | constant within 0.3 µm |
| Max shell overlap | 1.3 µm | 1.3 µm |
| Centroid displacement | 0.25 mm | 1.06 mm |
| Change of distance to the centroid | up to 0.18 mm | from -0.53 mm (D) to +0.85 mm (C) |
| Interior angles (120° at start) | 119.7 to 120.2° | 118.4° (C), 118.5° (F), 120.5 to 121.0° (others) |

The centroid moves along a straight line at 3.4 µm/s, in a fixed direction
(about -27° from the x axis). It stays within 0.03 mm of a linear fit over
the whole run.

## Interpretation

- The rotation regime does not change in 5 minutes. Body speed, rotor
  locking and the alternation are the same in the last minute as in the
  first.
- The drift of the ring as a block stays linear and does not speed up.
- The ring does deform, slowly. Six links of fixed length do not hold the
  angles of a hexagon: with the six sides fixed, three ways of changing the
  angles remain free. Nothing in the model pulls the angles back to 120°.
  The hexagon flattens along the C-F axis: C and F move away from the
  centre and their angles close to about 118.4°, while A, B, D and E move in
  and their angles open to 120.5 to 121°. `shape_exaggerated.png` shows it.
  The change grows steadily, at about 3 µm/s for C and F, with no sign of
  speeding up or of settling.
- At 60 s the same deformation was already there (up to 0.18 mm). Journal
  entry 3 described the ring as drifting "without deforming", which was not
  accurate.
- The cause of the drift and of the flattening is not known. They could be
  numerical (they are slow and might change with `dt`) or physical (no
  restoring force, so any small asymmetry builds up).

## Caveats

- `dt = 1e-4 s` is not converged (see entry 2: at `dt = 1e-5 s` the magnet
  pairs touch only about 25 % of the time instead of 100 %). The drift and
  the flattening are the numbers most likely to depend on `dt`.
- The start is ideal: exact symmetry, identical motors, no noise.
  Robustness is not tested.
- 300 s does not say whether the flattening stops, keeps growing or ends up
  changing the state.
- The parameters are prototype estimates (see `docs/model.md`). These
  numbers describe the model, not the real robots.
