# Kept results

Runs that mark a step in the project, versioned on purpose. Scratch runs go
to `runs/`, which is ignored by git.

[`journal.md`](journal.md) tells the path from one kept run to the next: why
each run was made, what it showed and what was decided. Use the
`keep-result` skill to add a run: it creates the folder below and the
journal entry together.

One folder per run (or per group of runs answering one question), named
`YYYY-MM-DD-<short-name>/`, containing:

- the run outputs (`.csv`, `.json`, `.gif`) exactly as the simulator wrote them.
  A CSV over about 5 MB stays in `runs/` (local); the README then says how
  to regenerate it;
- a `README.md` giving the command line, the git commit it ran on
  (`git rev-parse --short HEAD`), the question it answers, and the key
  numbers with their interpretation.

Never edit outputs by hand. To change a result, rerun it.

## Measures

The numbers and figures in these READMEs and in the journal use the
definitions below. Some come from the simulator's JSON summary
(`output/analysis.py`): net rotations, rotor abs/rel speed ratio, contact
fraction of the magnet pairs, pair distances, detachment, maximum
displacement. The others are computed from the CSV by plotting scripts that
are not in the repo yet. They follow these definitions exactly.

Notation: P_i(t) = (`<X>_x_m`, `<X>_y_m`) is the centre of unit i (the
centre of its shell), units in ring order A, B, C, ... A sample is one CSV
row (200 per second). "After the start ramp" means t > 0.5 s, or t > 1 s
when stated.

| Measure | Definition |
| --- | --- |
| Centroid C(t) | Mean of the unit centres, recomputed at every sample: C(t) = (1/N) Σ P_i(t). It is a geometric point: no unit sits there. All units have the same mass, so it is also, very nearly, the centre of mass of the ring. |
| Drift (centroid displacement) | \|C(t) − C(0)\|: how far the ring has moved as a block. |
| Drift speed | Slope of straight-line fits of the centroid's x and y against t, after the start ramp, combined: sqrt(a_x² + a_y²). |
| Distance to the centroid | r_i(t) = \|P_i(t) − C(t)\|, taken at the same instant. A rigid drift or rotation of the ring leaves it unchanged, so it only changes when the shape changes. |
| Change of distance to the centroid | r_i(t) − r_i(0.6 s). The reference is taken just after the start ramp, during which the initial 50 µm gap between the shells closes. |
| Shape spread | max_i − min_i of the change of distance to the centroid, at one instant. 0 for a ring that keeps its shape. |
| Neighbour distance | \|P_{i+1}(t) − P_i(t)\|, the last unit paired with the first. |
| Interior angle at unit i | Angle between P_{i−1} − P_i and P_{i+1} − P_i. 120° for every unit of a regular hexagon. |
| Exaggerated shape (`shape_exaggerated.png`) | Positions at 0.6 s and at the end, each taken relative to its own centroid. The rigid rotation is removed by the best-fit rotation (least squares, SVD) that maps the late shape onto the early one. The remaining displacement is multiplied by a stated factor (30). |
| Alternation of the rotor directions | Share of samples, after the start ramp, where the signs of `<X>_active_rel_omega_rad_s` alternate around the ring. |
| Sum of the rotor speeds | Σ_i `<X>_active_rel_omega_rad_s` at each sample, given as its mean over time and its largest absolute value. |
| Oscillation of the body speeds | Standard deviation over time of `<X>_body_omega_rad_s`, after the start ramp, averaged over the units. |
| Slip at a neighbour contact | The contact point is taken at the midpoint of the two centres. The velocity of each centre comes from finite differences of the positions (`numpy.gradient` on the 200 Hz samples); the spin is `<X>_body_omega_rad_s`. The slip is the tangential component of the difference between the velocities of the two material points at the contact. Only its mean over time means something: the sampling adds fluctuations of about 0.1 mm/s. |
