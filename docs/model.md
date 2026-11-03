# Model notes

The modelling assumptions, where the parameters come from, and the known
limitations of the current simulator (`03_Simulation_PyChrono/`). All values
are SI. The parameters live in `Parametres` (`granulobot_physics.py`); for a
one-off run, override them in `PARAMETRES = Parametres(...)` or with
`--parametres file.json`.

## Mechanics of one unit

- Each unit is modelled as four bodies:
  - the body (shell);
  - an active rotor, driven by the motor, which carries one magnet;
  - a free rotor on a pivot, which carries the second magnet;
  - an outer free wheel on its own pivot.

  The free wheel's contacts with the neighbours are separate from those of
  the motorised wheel.
- The motor acts between the active rotor and the body, together with its
  reaction torque. It is never an external torque on the aggregate.
- Unit axes are vertical (top view). A guide blocks tipping (Rx/Ry) only, never
  X, Y, Z or the rotation about Z.
- Planar projection: centres of mass and side contacts sit in a common plane.
  XY forces and Z torques are kept; tipping moments are dropped. The collision
  shapes keep both heights for the Bullet ground contact.
- The view shows the motorised part only. The free wheel is 4 mm thick and
  weighs 8 g (included in the 98 g unit mass); both values and its pivot
  friction are estimates. `roue_motorisee_en_bas` compares the two
  orientations on the support.
- Magnets are rigidly attached to their rotors. Their own rotation on
  bearings does not change an axial field, but it could change the contact
  friction; this is to be modelled once the prototype is checked.
- Not modelled yet: gear teeth, collisions between the magnets of the same
  unit, the real vertical stacking of the magnets (the field assumes their
  centres are coplanar), the motor inductance and the reflected inertia of the
  gearbox.

## Contacts

- Side contacts between parallel cylinders use an analytic circular geometry
  and are passed to the NSC solver through a custom collision callback.
  Normal contacts are constraints, and friction is exact Coulomb friction.
  There are no permanent springs between units.
- Ground support (`modele_sol="disque_equivalent"`, the default):
  - a normal reaction plus Coulomb friction;
  - a torsion resistance of `mu_sol * N * 2R/3`, which assumes a uniform
    pressure.

  The translation and torsion limits are treated separately, so they must be
  calibrated in combined motion. The Bullet ground contact can still be chosen
  with `modele_sol="bullet"`.
- A very small NSC compliance distinguishes the plastic shells
  (`compliance_coques=1e-7` m/N) from the metal magnets
  (`compliance_aimants=1e-8` m/N). Perfectly rigid flush contacts give an
  ambiguous load sharing. Both values are assumptions to be measured, not a
  fit. Setting both to zero gives back the rigid reference.
- The NSC penetration recovery speed cap is 10 m/s. It is a numerical limit
  and imposes no speed on the units. With compliance, Chrono also caps the
  reaction at about `v_correction * dt / C_total`. The old value of 0.05 m/s
  limited the shell reaction to about 2.5 N, while the estimated magnetic
  forces reach 12 N. This caused artificial sinking that depended on the time
  step ([Chrono 10 contact code](https://github.com/projectchrono/chrono/blob/10.0.0/src/chrono/physics/ChContactNSC.cpp#L129-L147)).
- NSC rolling and spinning resistances and the extra viscous resistances are
  available but set to zero by default, to avoid counting an unknown
  resistance twice.

## Magnets

- The magnets are 8 mm in diameter and 10 mm high, flush with the surface,
  with their poles on the flat faces (axial magnetisation). They sit 31 mm
  from the axis.
- The field of uniformly magnetised cylinders is computed by quadrature of the
  surface charges
  ([method](https://doi.org/10.1016/j.jmmm.2022.169482)). The potential is
  interpolated so that F = -grad(U) holds.
- The tests check the gradient of the potential, the dipole limit at large
  distance, and the sensitivity to refining the quadrature.
- Point dipoles remain available for comparison (`modele_magnetique`).
- The remanence (1.45 T, N54 assumed) and the presence of a hole in the
  magnets are still to be confirmed.

## Motor and internal friction

- The motor is a DC motor in quasi-static electrical regime (inductance
  neglected): U - Ke·β·ω = R·I, and the torque is β·Kt·I after the gearbox.
- Control modes: `tension` (default), `vitesse` (PI on the relative rotor
  speed, limited in voltage and torque) and `couple`. Voltages ramp up over
  `rampe_demarrage`.
- The internal dry friction is smoothed (tanh), so it does not reproduce an
  exact static threshold.

## Parameter origins

| Parameters | Origin / limit |
| --- | --- |
| `R=0.035`, `H=0.050` | Dimensions given by Hugo (prototype), converted from cm |
| `M=0.098`, active mass/inertia | Paper; to check on the current prototype |
| Reduction 379, Kt, Ke, resistance 9.6 Ω, active friction 0.024 N·m | Paper, fig. 8; not a calibration of the current motor |
| Voltage 3.25 V | Estimate for a free rotor turning about once every 2 s |
| `mu_sol`, `mu_robots`, other masses/inertias, eccentricities | Estimates, to measure |
| Magnets Ø8 mm × 10 mm, flush, axial poles | Estimates and details from Hugo; centres 31 mm from the axis |
| Remanence, possible hole | 1.45 T and solid magnets assumed; to confirm |
| Magnetic softening, dt, collision tolerances | Numerical; to check by convergence |

`prototype_hugo.json` keeps the dimensions Hugo provided, separate from the
parameters that are still estimated.

## Validation status (before the 2026-11-03 cleanup)

The campaigns cited here were archived in git history (commit `b332380`,
folders `03_Simulation_PyChrono/validation/` and `essais_plan/`).

- Short checks at the nominal step pass. In the corrected abrupt-start case,
  PSOR with dt halved still reaches 90 µm of overlap and a different rotation.
- On the 2-unit bench at 1 V (before the second wheel was added), halving dt
  or doubling the iterations still changes the maximum displacement by about
  1 mm.
- Triangle at 1 V per motor with `mu_robots=0.05`, over 0.6 s: the motorised
  parts turn about 14.5°; the centres drift by less than 0.04 mm; the active
  rotors' absolute speed is about 100 times smaller than their speed relative
  to the body; the maximum shell overlap is 3.8 µm.
- A first try with vertical lever arms and Rx/Ry guides
  (`diagnostic_deux_roues_3D/`) penetrated by 1.6 mm under motor load. It is a
  numerical diagnosis, not a usable physical result.
- Campaigns recorded with the 0.05 m/s recovery cap do not validate the
  corrected model.
- Physical convergence is **not** established. It must be resolved before any
  quantitative prediction.

The 3 mm detachment threshold in the diagnostics is an indicator, not a
physical breaking law. An ideal link (`--liaison-ideale`) has no pull-off
force and does not validate the magnetism.

## To calibrate

- Pull-off force and breakaway torque of the magnets.
- Motor voltage and speed, without load and under load.
- Rotational resistance on the table, and sliding friction between shells.

Don't adopt a setting just because its animation looks right.
