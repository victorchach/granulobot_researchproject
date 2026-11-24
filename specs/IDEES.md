# Ideas backlog

Things to handle later. When one is scheduled, it becomes a spec and is
removed from this list.

## Roadmap step 1 (synchronized liquid state)

- Long-run metrics for step 1: ring shape, alternation of rotor directions,
  sum of rotor speeds.
- Differentiated rim friction from Hugo's branch `origin/granulobot-research`
  (`frottement_jantes` in `granulobot_physics.py`): low steric friction
  (0.05), high friction (1.0) when facing magnets are engaged, blended by an
  engagement weight. Exploratory values, no source yet. Planned as spec 007,
  after 006; compare against his `reference_alternee` run.
- More than 26 units (spec 006 caps N at 26). The cap only comes from the
  names A..Z (`chr(65 + i)`). Lifting it needs names AA, AB, ... and a
  separator in the pair keys (`A-B_distance_m`, `max_overlap_m`): with plain
  concatenation, A+AB and AA+B both give `AAB`. Nothing reads those keys back,
  so `make diag` and `make replay` stay compatible. The real limit is then the
  cost (magnet pairs grow as N squared, see Performance below) and the ground
  size (`ground_width = 2 m` fits about 85 units).

## Running many configurations

- Batch runs: give several parameter files (or a sweep over one parameter)
  and get one run per configuration, each output named after its config so it
  can be found again, plus an index of what was run. Today this needs one
  `make sim NAME=x ARGS="--params configs/x.json"` per file, named by hand,
  and a reused NAME silently overwrites the previous run. `scripts/campaign.py`
  does batches, but its scenarios are hard-coded in Python. Victor wants this
  after spec 005 (2026-11-24).

## Later steps

- Self-organizing control u_i = |u| sgn(dθ_i/dt) (eq. 7) for step 2.
- Full feedback law U = u - (αη0/k)dθ/dt - (G/k)θ (eq. 2) for the
  self-oscillating solid.
- Static vs kinetic friction (stick-slip) on steric contacts.
- Switch the defaults to the paper's dimensions (r = 24 mm).
- Performance for 2 to 5 min runs at dt = 1e-5 s: magnetism computed in pure
  Python over all magnet pairs at every step (vectorize, or use a neighbour
  cutoff).
