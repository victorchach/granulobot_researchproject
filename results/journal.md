# Journal of results

The path of the project, one kept run at a time. Each entry says why the run
was made, given the entry before it, what it showed, and what we decided
next. The details (commands, commits, full numbers) are in the README of each
folder. New entries go at the end, through the `keep-result` skill.

## 1. 2026-10-14: triangle of 3 units, 3.25 V on every motor

Folder: [`2026-10-14-triangle-3-units/`](2026-10-14-triangle-3-units/)

- **Why**: first closed ring run with the NSC simulator (rigid contacts,
  exact Coulomb friction), all three motors at the default 3.25 V.
- **What we saw**: the three bodies all turn the same way (-0.38 to -0.45
  turn in 3 s) and their centres move by 11.7 to 13.7 mm. The three magnet
  pairs stay coupled and none detaches.
- **Limits**: on an odd ring, neighbours cannot turn in opposite directions,
  so the ring is frustrated. Time-step convergence was not established.
- **Next**: at the late-October team meeting we decided to move to a 6-unit
  ring with alternating biases (paper eq. 8), aiming at the active liquid
  state (`docs/roadmap.md`, step 1; `docs/decisions.md`). The simulator was
  generalized to N units in spec 006.

## 2. 2026-11-24: ring of 6 units, alternating ±3.25 V, 2 s

Folder: [`2026-11-24-ring6-alternating/`](2026-11-24-ring6-alternating/)
(`uniform_dt1e4.*`)

- **Why**: after entry 1, an even ring lets neighbours turn in opposite
  directions. First run of the hexagon with u_i = (-1)^i × 3.25 V, uniform
  shell friction, dt = 1e-4 s.
- **What we saw**: the bodies turn in alternation (±0.847 turn) while each
  active rotor stays locked against its neighbour's free magnet (0.0013 turn
  in the lab frame). Neighbouring rims roll on each other like gears, the
  centres move less than 0.1 mm and the six magnet pairs stay in contact. Hugo's
  run with his differentiated rim friction gave the same rotation (-0.848
  turn): without slipping, the friction coefficient plays no part.
- **Limits**: only 2 s, from an ideal start. Not converged in dt: a 1 s run
  at dt = 1e-5 s (local only, `runs/ring6/uniform_dt1e5`) gives the same
  rotation within about 6 %, but the magnets are in contact only about 25 % of
  the time instead of 100 %.
- **Next**: run longer to check that the state lasts. Hugo's rim friction
  (spec 007) needs a scenario where rims slip to make a difference.

## 3. 2026-11-24: ring of 6 units, alternating ±3.25 V, 60 s

Folder: [`2026-11-24-ring6-alternating/`](2026-11-24-ring6-alternating/)
(`uniform_dt1e4_60s.*`)

- **Why**: after entry 2, check that the liquid state holds over time, with
  the same settings for 60 s.
- **What we saw**: the three step 1 criteria of the roadmap hold for the
  whole run. The rotor directions alternate on every sample after the start
  ramp. The sum of the six rotor speeds averages 0.0002 rad/s, against
  6 × 2.64 rad/s. The neighbour distances stay constant within 0.1 µm, with no
  detachment. The bodies make ±29.1 turns (about 29 rpm). The ring drifts
  slowly as a block, without deforming: 0.25 mm in 60 s, cause unknown.
- **Limits**: the roadmap asks for 2 to 5 min; dt = 1e-4 s is not
  converged; the start is ideal (exact symmetry, identical motors).
- **Next**: step 1 holds for 60 s at dt = 1e-4 s. Still open before calling
  it validated: time-step convergence, a 2 to 5 min run (and whether the
  drift stays linear), robustness to unequal voltages and perturbations.

## 4. 2026-11-24: ring of 6 units, alternating ±3.25 V, 300 s

Folder: [`2026-11-24-ring6-alternating-300s/`](2026-11-24-ring6-alternating-300s/)

- **Why**: after entry 3, run the 5 minutes that roadmap step 1 asks for,
  and see whether the slow drift stays linear.
- **What we saw**: the three step 1 criteria hold for the whole 300 s. The
  rotor directions alternate on all 59 900 samples, the sum of the rotor
  speeds averages 0.0002 rad/s, and no pair detaches. The bodies make
  ±146.2 turns at the same speed in the last minute as in the first. The
  centroid drifts in a straight line at 3.4 µm/s (1.06 mm). The hexagon
  also flattens slowly along the C-F axis: C and F move 0.8 mm away from the
  centre and their angles close to 118.4°. Entry 3's "without deforming" was
  wrong: the flattening had already started (0.18 mm at 60 s).
- **Limits**: dt = 1e-4 s is still not converged, and the drift and the
  flattening may be numerical. Ideal start, no robustness test. 300 s does
  not tell whether the flattening stops.
- **Next**: step 1 holds for 5 min at dt = 1e-4 s. Before calling it
  validated: a dt convergence run, then robustness to unequal voltages and
  perturbations. The working hypothesis is that the drift and the
  flattening are numerical: with exact Coulomb friction at the ground and
  balanced forces, the centres should not move, and the rims do not slip at
  the contacts (mean slip under 10 µm/s against a rim speed of 0.104 m/s), so
  Hugo's rim friction (spec 007) should not change them. To test it, a 20 s
  run at dt = 1e-5 s was started on 2026-11-24
  (`runs/ring6/uniform_dt1e5_20s`, local only, analysis pending), to compare
  with the first 20 s of this run.
