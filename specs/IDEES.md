# Ideas backlog

Things to handle later. When one is scheduled, it becomes a spec and is
removed from this list.

## Roadmap step 1 (synchronized liquid state)

- Generalize the simulator from 2 or 3 units to N units, with a regular
  hexagon ring for N = 6. The 2/3 assumption is hard-coded in
  `Parameters.check`, `simulation/world.py` (`coupled_pairs`, the triangle
  positions), `model/unit.py` (`create_unit`, rotor orientations), the 3-value
  tuples (`target_voltages`, ...), the `--voltages A B C` CLI flags and
  `output/analysis.py` (`analyze`).
- Alternating open-loop biases u_i = (-1)^i |u| (paper eq. 8).
- Long-run metrics for step 1: ring shape, alternation of rotor directions,
  sum of rotor speeds.

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
