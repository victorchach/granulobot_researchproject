# Ring of 6 units, alternating ±3.25 V (2026-11-24)

The first runs of the 6-unit ring after spec 006: a regular hexagon with
alternating open-loop biases u_i = (-1)^i × 3.25 V, A positive (paper eq. 8),
and uniform shell friction (`mu_shells = 0.6`). They are the first check of
roadmap step 1 (active liquid state) and the baseline for spec 007 (Hugo's rim
friction model).

## How they were made

Both runs use `configs/ring6_alternating.json` and `dt = 1e-4 s`; every other
value is a simulator default.

| Run | Files | Command | Code |
| --- | --- | --- | --- |
| short, 2 s | `uniform_dt1e4.{csv,json,gif}` | `make sim NAME=ring6/uniform_dt1e4 ARGS="--params configs/ring6_alternating.json --dt 1e-4 --duration 2"` | working tree of branch `feature/006-n-unit-ring`, committed unchanged in `src/` as `1b3d045` |
| long, 60 s | `uniform_dt1e4_60s.{json,gif}` | `make sim NAME=ring6/uniform_dt1e4_60s ARGS="--params configs/ring6_alternating.json --dt 1e-4 --duration 60 --no-gif"`, then `make replay CSV=runs/ring6/uniform_dt1e4_60s.csv` | `1ee5305` (main) |

The CSV of the long run (46 MB) is not versioned. Rerun the command above to
get it back: about 30 min of CPU on Victor's Mac.

## Question

Does the hexagon with alternating biases reach and keep the active liquid
state? The criteria come from `docs/roadmap.md`, step 1: the ring keeps its
shape, the rotor directions keep alternating, and the sum of the rotor speeds
stays close to zero.

## Key numbers

From the JSON summaries, and from the CSV for the time series.

| | 2 s | 60 s |
| --- | --- | --- |
| Net body rotation | ±0.847 turn | ±29.13 turns (about 29 rpm) |
| Net rotation of the active rotors in the lab frame | 0.0013 turn | 0.002 turn at most |
| Rotor abs/rel speed ratio | 0.087 | 0.087 |
| Max centre displacement | 0.08 mm | 0.36 mm |
| Magnet pairs in contact | 100 % of samples | 100 % of samples |
| Max shell overlap | 1.3 µm | 1.3 µm |

In the 60 s run:

- the rotor directions alternate on every sample after the 0.5 s start ramp
  (11 900 of 11 900);
- the sum of the six relative rotor speeds averages 0.0002 rad/s, with a peak
  of 0.13 rad/s, against 6 × 2.64 rad/s;
- the neighbour distances stay constant within 0.1 µm, and no pair detaches.

## Interpretation

- Each active rotor stays locked in the magnetic notch of its neighbour's free
  magnet. The motor's reaction torque then turns the body in place instead.
- Neighbouring bodies turn at equal and opposite speeds, so their rims roll on
  each other like gears, without slipping. The shell friction coefficient
  plays no part here: Hugo's run with his differentiated rim friction gave
  -0.848 turn at 2 s, against -0.847 here.
- The motor torques are internal and the magnetic and contact forces cancel by
  symmetry, so the centres barely move. The ring still drifts slowly as a
  block, without deforming: its centroid moves 0.25 mm in 60 s, about 4 µm/s
  and roughly linear. The cause (numerical or ground friction) is not known.
- Compare the 2026-10-14 triangle, where all 3 bodies turn the same way and
  move by more than 10 mm.

## Caveats

- `dt = 1e-4 s` is not converged. A 1 s run at `dt = 1e-5 s` (kept locally
  only, `runs/ring6/uniform_dt1e5`) gives the same body rotation within about
  6 %, but the magnet pairs are in contact only about 25 % of the time instead
  of 100 %.
- The start is ideal: exact symmetry, identical motors, no noise. Robustness
  (unequal voltages, large perturbations, random start) is not tested.
- 60 s is short of the 2 to 5 min that the roadmap asks for.
- The parameters are prototype estimates (see `docs/model.md`). These numbers
  describe the model, not the real robots.
