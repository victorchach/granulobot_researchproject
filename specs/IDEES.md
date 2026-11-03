# Ideas backlog

Things to handle later. When one is scheduled, it becomes a spec and is
removed from this list.

## Roadmap step 1 (synchronized liquid state)

- Generalize the simulator from 2 or 3 units to N units, with a regular
  hexagon ring for N = 6. The 2/3 assumption is hard-coded in
  `Parametres.verifier`, `appariements`, the 3-value tuples (`tensions_cibles`,
  ...), the `--tensions A B C` CLI flags and `diagnostic_accrochage.analyser`.
- Alternating open-loop biases u_i = (-1)^i |u| (paper eq. 8).
- Long-run metrics for step 1: ring shape, alternation of rotor directions,
  sum of rotor speeds.

## Later steps

- Self-organizing control u_i = |u| sgn(dθ_i/dt) (eq. 7) for step 2.
- Full feedback law U = u - (αη0/k)dθ/dt - (G/k)θ (eq. 2) for the
  self-oscillating solid.
- Static vs kinetic friction (stick-slip) on steric contacts.
- Switch the defaults to the paper's dimensions (r = 24 mm).
- Performance for 2 to 5 min runs at dt = 1e-5 s: magnetism computed in pure
  Python over all magnet pairs at every step (vectorize, or use a neighbour
  cutoff).

## Cleanup

- Translate the French identifiers, comments and CSV column names to English.
  This breaks old CSV/JSON files; plan a compatibility note.
- Remove the legacy scripts `test_3_granulobots_simple.py` (it runs a
  simulation when imported, which breaks `unittest` discovery) and `unite.py`.
- Rename `test_3_granulobots.py` (it is the simulator, not a test) and move
  `validation_modele.py` under the test naming.
