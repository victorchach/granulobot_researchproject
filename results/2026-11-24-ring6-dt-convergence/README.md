# Ring of 6 units, alternating ±3.25 V, 20 s at dt = 1e-5 s (2026-11-24)

A time-step check of the 300 s run in
[`2026-11-24-ring6-alternating-300s/`](../2026-11-24-ring6-alternating-300s/):
the same hexagon and the same biases, with a time step ten times smaller, over
20 s. It is compared with the first 20 s of the 300 s run.

## How it was made

```
make sim NAME=ring6/uniform_dt1e5_20s ARGS="--params configs/ring6_alternating.json --dt 1e-5 --duration 20 --no-gif"
```

It was started on 2026-11-24 at 23:24 on `main` at `96b6cb5`, with a clean
working tree, and finished at 00:45 the next day. The simulator code in
`src/` has not changed since `1b3d045` (spec 006). It took 1 h 22 of CPU
on Victor's Mac, about 4 min per simulated second.

| File | What it is | Made by |
| --- | --- | --- |
| `uniform_dt1e5_20s.json` | parameters, assumptions, summary | the simulator |
| `dt_comparison.png` | first 20 s at dt = 1e-4 s against dt = 1e-5 s: centroid displacement, spread of the distances to the centroid, and each unit's distance to the centroid | plotting script, from both CSVs |

Not versioned:

- the CSV (15 MB). Rerun the command above to get it back.
- a GIF: the run used `--no-gif`. `make replay CSV=runs/ring6/uniform_dt1e5_20s.csv`
  makes one from the CSV.
- the plotting script (a scratch script outside the repo, as for the 300 s
  run).

How the figure measures things, in short: the centroid is the mean of the
six unit centres, recomputed at every sample. The drift is the centroid's
distance from its position at t = 0. The shape is measured by each unit's
distance to the centroid at the same instant, minus its value at t = 0.6 s
(after the start ramp). A rigid drift of the ring leaves those distances
unchanged. The full definitions, including the angles, the rotor sum and the
slip at the contacts, are in [`../README.md`](../README.md#measures).

## Question

After the 300 s run, the working hypothesis was that the slow drift of the
ring and the flattening of the hexagon were numerical. Do they shrink when
dt goes from 1e-4 s to 1e-5 s? A second question was open since journal
entry 2: does the liquid state itself hold at the finer time step?

## Key numbers

First 20 s of each run, after the start ramp where it matters. The JSON
summaries give the rotations and contact fractions. The CSVs give the rest.

| | dt = 1e-4 s | dt = 1e-5 s |
| --- | --- | --- |
| Mean body speed | 2.967 rad/s | 2.941 rad/s (-0.9 %) |
| Rotor directions alternating | 3 800 of 3 800 samples | 3 800 of 3 800 samples |
| Net rotation of the active rotors in the lab frame | 0.002 turn at most | 0.012 turn at most |
| Rotor abs/rel speed ratio | 0.087 | 0.067 |
| Sum of the six relative rotor speeds | 0.0002 rad/s on average, 0.02 peak | 0.0025 rad/s on average, 0.19 peak |
| Spread of the body speeds in time (std) | 0.06 rad/s | 0.22 rad/s |
| Magnet pairs in contact | 100 % of samples | 1.2 to 1.4 % of samples |
| Magnet pair distance | 8.000 to 8.050 mm | 8.000 to 8.147 mm, no detachment |
| Neighbour shell distances | constant within 0.2 µm | constant within 0.2 µm |
| Max shell overlap | 1.3 µm | 4.1 µm |
| Centroid displacement at 20 s | 0.094 mm (fit 4.2 µm/s) | 0.083 mm (fit 3.7 µm/s) |
| Spread of the distances to the centroid at 20 s | 0.15 mm | 0.94 mm |
| Units moving out / in | C, F out; B, E, A, D in | B, E out (+0.46, +0.41 mm); C, F in (-0.48, -0.42 mm) |
| Interior angles at 20 s | 119.8 to 120.1° | 119.1° (B), 119.3° (E), 120.8° (F), 120.9° (C) |

## Interpretation

- The rotation regime is converged: same body speed within 0.9 %, perfect
  alternation, rotors still locked in the magnetic notch. The active liquid
  state does not come from the time step.
- The drift of the ring as a block barely changes with dt (4.2 against
  3.7 µm/s). It does not come from the time step. It could still come from
  the solver's tolerance or from the contact model, but that is not tested.
- The flattening does not go away either. It is six times larger at
  dt = 1e-5 s, and along another axis (B-E instead of C-F). With the six
  sides held by the magnet pairs, the hexagon keeps three free ways to
  change its angles, and nothing pulls them back to 120°. Any small
  disturbance can make it drift slowly. The time step changes how large the
  disturbances are: at dt = 1e-5 s the magnets hover instead of resting in
  contact, and the body speeds fluctuate more. So the flattening looks like
  a real behaviour of the model, while its speed and axis are not
  converged.
- The magnet contact is not converged. At dt = 1e-4 s the two magnets of
  each pair rest against each other. At dt = 1e-5 s they stay within
  0.15 mm but touch only about 1 % of the time. The 1 s run of entry 2
  (25 % in contact) was too short to show this.

## Caveats

- Only 20 s at dt = 1e-5 s. A finer step (5e-6 s) would cost about 8 min of
  CPU per simulated second and was not run.
- Two time steps do not show convergence. They only show what changes and
  what does not.
- The start is ideal: exact symmetry, identical motors, no noise.
- The parameters are prototype estimates (see `docs/model.md`).
