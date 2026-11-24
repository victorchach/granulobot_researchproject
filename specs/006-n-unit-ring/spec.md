# 006: N-unit ring

Status: merged
Branch: `feature/006-n-unit-ring`

## Need

Roadmap step 1 needs a ring of 6 units in a regular hexagon, driven by
alternating open-loop biases (paper eq. 8), to reach the active liquid state.
The simulator only accepts 2 or 3 units: the count is hard-coded in seven
places (see Files concerned).

Hugo built a 6-unit version on his branch `origin/granulobot-research`
(`simulate_granulobots.py`, `granulobot_physics.py`). That branch starts from
the old layout (2026-10-14) and is not merged. This spec ports the ring part of
his work into `src/granulobot/` and generalizes it to any N, not only 6. His
rim friction model is left for spec 007.

## Expected behaviour

- **Unit count.** `Parameters.n_units` accepts any integer from 2 to 26
  (names A to Z). The default stays 3.
  - `n_units = 2` keeps the current bench: one facing pair, active A to free
    B, the two other magnets facing outwards.
  - `n_units >= 3` is a closed ring: unit i's active magnet faces unit i+1's
    free magnet, and the last unit's active magnet faces A's free magnet.
- **Layout.** For N >= 3, the centres sit on a regular N-gon with side
  `side = 2R + initial_gap` (the same spacing as today's triangle):
  - circumradius `r = side / (2 sin(pi/N))`;
  - unit i at angle `theta_i = -pi/2 - pi/N + 2 pi i/N`, counterclockwise
    from A.
  - For N = 3 this gives the current triangle (A bottom left, B bottom right,
    C on top), equal to the current hard-coded coordinates within 1e-15 m.
  - N = 2 keeps its explicit positions `(-side/2, 0)` and `(side/2, 0)`.
- **Ring and ground.** With the ground enabled, `check()` rejects a ring that
  does not fit on it: `r + R > ground_width / 2`.
- **Pairings.** One function gives the coupled pairs: `((0, 1),)` for N = 2,
  and `(i, (i+1) % N)` for N >= 3. The ideal link (`world.py`), the rotor
  orientations (`unit.py`) and the analysis (`analysis.py`) all use it. The
  two current copies of the triangle pairs are removed.
- **Set points.** The target tuple read by the current motor mode must have
  at least N finite values: `target_speeds` in speed mode, `target_voltages`
  in voltage mode, `target_torques` in torque mode. Extra values are ignored,
  so the existing 2-unit inputs with an unused C value still work. The other
  two tuples must only be finite. The 3-value defaults are unchanged, so a
  6-unit run needs its set points from `--voltages` or a parameter file;
  otherwise `check()` raises a clear error ("voltage mode needs at least 6
  target_voltages, got 3").
- **Torque mode.** `apply_motor` stops reading `target_voltages` in torque
  mode. It never used that value there, so behaviour does not change.
- **CLI.**
  - `--units N`: any integer; `check()` validates the range.
  - `--voltages V [V ...]` and `--speeds W [W ...]` take one value per unit,
    in order A, B, ...
- **Alternating reference config.** A new file,
  `configs/ring6_alternating.json`, sets `n_units = 6` and `target_voltages =
  [3.25, -3.25, 3.25, -3.25, 3.25, -3.25]`. It sits next to an `origin` note,
  in the same format as `prototype_hugo.json`. Run it with
  `make sim NAME=ring6 ARGS="--params configs/ring6_alternating.json"`.
- **Outputs.** CSV, JSON, analysis and GIF work for any N. They already loop
  over the units and all pairs, so their format does not change. The pair
  analysis lists the N coupled pairs, e.g. `F_active/A_free` for N = 6.
- **Default runs unchanged, up to rounding.** A default run (triangle) gives
  the same results as on `main`, up to the rounding of the corner
  coordinates (see Planned tests).

## Physics and assumptions

- **Layout.** Same neighbour spacing and initial gap as the triangle. The two
  magnets of each unit point at the centres of its two ring neighbours. In a
  hexagon they are 120 degrees apart on the rim, compared with 60 degrees in
  the triangle. Non-neighbours do not touch: in a hexagon, units i and i+2
  are `sqrt(3) * side` apart.
- **Alternating biases.** u_i = (-1)^i |u| with i = 0 for A (paper eq. 8;
  `docs/roadmap.md`, step 1). |u| = 3.25 V is the current default
  `target_voltages` value (estimate, about 30 rpm without load), and Hugo's
  reference `reference_alternee.json` uses the same value. For odd N the
  alternation cannot close around the ring: the last unit and A get the same
  sign. Only the even case N = 6 gets a config.
- **No physical default changes.** Friction stays uniform
  (`mu_shells = 0.6`), as on `main`.

## Files concerned

- `src/granulobot/simulation/layout.py` (new, no PyChrono): `ring_positions(n,
  side)` and `coupled_pairs(n)`.
- `src/granulobot/simulation/world.py`: uses `ring_positions` and
  `coupled_pairs`; its local `coupled_pairs` is removed; docstring.
- `src/granulobot/model/unit.py`: the neighbour index uses `% p.n_units`
  instead of `% 3`.
- `src/granulobot/parameters.py`: range check on `n_units`, set-point rule,
  ring-on-ground check, comments.
- `src/granulobot/model/motor.py`: torque mode does not read
  `target_voltages`.
- `src/granulobot/output/analysis.py`: uses `coupled_pairs`.
- `src/granulobot/__main__.py`: `--units`, `--voltages`, `--speeds`;
  docstring.
- `configs/ring6_alternating.json` (new).
- `tests/test_physics.py`, `tests/test_dynamics.py`: new tests.
- Docs:
  - `AGENTS.md`: flags, the "2 or 3 units" limit, the architecture list;
  - `docs/architecture.md`: file map, layout step;
  - `docs/model.md`: layout;
  - `docs/decisions.md`: entry for this spec;
  - `README.md`: a 6-unit example;
  - `specs/README.md` and `specs/IDEES.md`.

## Planned tests

- **Unit tests (`make test`):**
  - `ring_positions(3, side)` equals the old triangle coordinates (1e-15 m),
    and `ring_positions(2, side)` the facing pair.
  - `ring_positions(6, side)`: neighbour distances all equal `side`,
    distances between units i and i+2 equal `sqrt(3) * side`, and the
    centroid is at the origin.
  - `coupled_pairs(2) == ((0, 1),)`; `coupled_pairs(6)` has 6 pairs, the last
    one `(5, 0)`.
  - `check()`:
    - accepts N = 6 with 6 voltages, even though `target_speeds` keeps 3
      values;
    - accepts N = 2 with 3 voltages;
    - rejects N = 1, N = 27, N = 6 with 3 voltages, N = 6 in speed mode with 3
      speeds, and a ring that does not fit on the ground.
  - `analyze` on synthetic 6-unit rows returns 6 pairs, including
    `F_active/A_free`.
- **Dynamics (`make validate`):**
  - `create_system` with N = 6 builds 6 units.
  - For every i, the distance from unit i's active magnet to unit i+1's free
    magnet equals the triangle's value, and the active magnet points at the
    next unit's centre.
  - A few hundred steps of the alternating config stay finite, without shell
    overlap.
- **Scenarios (`make sim`):**
  - **Default triangle on `main` and on the branch** (`--duration 0.2
    --no-gif`): positions and angles in the CSV agree to 1e-9.
    *Amended during implementation:* they agree to 5e-8 m and 1.7e-6 rad
    only. The polygon formula puts the triangle corners 1.4e-17 m away from
    the old literals, and the iterative solver amplifies that rounding over
    0.2 s. With the old literals injected (scratch script), the CSV is
    identical to `main` bit for bit, so the logic is unchanged.
  - **6-unit probe** (`--params configs/ring6_alternating.json --duration 0.2
    --no-gif`) to measure the cost per simulated second.
  - **Longer run.** Then a 2 s run with uniform friction, at dt = 1e-4 like
    Hugo's reference, kept as the baseline for spec 007. No expected numbers
    are set in advance: report the body rotation, the rotor hold ratio and
    the pair contact fraction. A long 2 to 5 min validation is out of scope.

## Out of scope

- More than 26 units: the cap comes from the names A..Z. Lifting it needs
  two-letter names and a separator in the pair keys; the idea is in
  `specs/IDEES.md`.
- Hugo's differentiated rim friction (`mu_sterique` / `mu_magnetique`):
  spec 007.
- Long-run step 1 metrics (sum of rotor speeds, alternation check, ring
  shape) and 2 to 5 min runs.
- Hugo's perturbation config (`rotor_perturbation_rad` already exists and can
  be added to a parameter file by hand).
- Importing Hugo's saved runs: their columns are French, and the code
  revision that produced them is unknown.
- Performance (magnetism over all magnet pairs grows as N squared), the eq. 7
  controller, the paper's dimensions.

## Review

Independent review by a separate agent (fresh context), 2026-11-24. No
blocking defect; geometry, pairings, checks, CLI, imports and docs were
confirmed. Findings, all low:

1. The "Default runs unchanged" bullet contradicted the amended regression
   result (5e-8 m after 0.2 s). Fixed: reworded to "up to rounding".
2. `configs/ring6_alternating.json` was not tested; a bad key would only
   surface at `make sim`. Fixed: `test_ring6_config_loads` in
   `tests/test_physics.py` loads it, checks its keys and the alternation.
3. No ground-fit check for N = 2 (units outside a tiny ground lose their
   ground contact silently). Predates this spec, which limits the check to
   rings: not changed.
4. `--units 6 --no-motors` still needs 6 `target_voltages`, because
   `apply_motor` reads them before checking `motors_enabled`. Intended: the
   clear `check()` error avoids an IndexError. Not changed.
