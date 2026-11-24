---
marp: true
theme: granulobot
paginate: true
header: "Granulobot simulation · 2. Model"
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _header: "" -->

# Granulobot simulation

2. The physical model

What one unit is, and how units interact

---

<!-- _footer: "Added 2026-11-24" -->

## One unit: four rigid bodies

<div class="cols">
<div>

- **Shell** (body), Ø 70 mm, 50 mm high, 98 g in total.
- **Active rotor**, driven by the motor, carries the <span style="color:#c8102e">**active magnet**</span>.
- **Free rotor** on a pivot, carries the <span style="color:#1f5fa8">**free magnet**</span>.
- **Outer free wheel** on its own pivot.

</div>
<div>

- The motor acts **between the active rotor and the shell**: an internal torque, never an external one.
- Axes stay vertical: a guide blocks tipping only, never X, Y, Z or the rotation about Z.
- **Planar projection**: XY forces and Z torques kept, tipping moments dropped.

</div>
</div>

<div class="note">docs/model.md · src/granulobot/model/unit.py</div>

---

<!-- _footer: "Added 2026-11-24" -->

## Contacts (NSC)

- **Shell to shell, magnet to magnet**: analytic circular geometry, passed to the NSC solver through a custom collision callback. Normal contacts are constraints; friction is **exact Coulomb**. No permanent springs.
- **Ground**: equivalent disc, with a normal reaction, Coulomb friction and a torsion resistance μ·N·2R/3 (uniform pressure).
- **Tiny compliance** to share load between flush contacts: shells 10⁻⁷ m/N, magnets 10⁻⁸ m/N. Zero gives back the rigid reference.
- Uniform shell friction μ = 0.6 (estimate). Hugo's contact-dependent rim friction is **on hold** (see the Results deck).

<div class="note">src/granulobot/model/contacts.py · docs/decisions.md</div>

---

<!-- _footer: "Added 2026-11-24" -->

## Magnets and motor

<div class="cols">
<div>

### Magnets
- Ø 8 × 10 mm, flush, **axial poles**, 31 mm from the axis.
- Field of **finite uniformly magnetised cylinders** by surface-charge quadrature; F = −∇U holds exactly.
- About **12 N** of attraction at contact.
- Point dipoles kept for comparison.

</div>
<div>

### Motor
- DC motor, quasi-static: U − K<sub>e</sub>·β·ω = R·I, torque β·K<sub>t</sub>·I.
- Gear ratio β = 379, R = 9.6 Ω, dry friction 0.024 N·m (paper, fig. 8).
- Control in **voltage** (default), speed or torque; 0.5 s start ramp.

</div>
</div>

<div class="note">src/granulobot/model/magnets.py, motor.py</div>

---

<!-- _footer: "Added 2026-11-24" -->

## Where the numbers come from

| Parameters | Origin |
| --- | --- |
| R = 35 mm, H = 50 mm, magnets Ø 8 × 10 mm, axial | Hugo's prototype (to measure) |
| Mass 98 g, active rotor, motor constants | Paper, fig. 8 (not our motor yet) |
| 3.25 V target | Estimate: about 30 rpm without load |
| μ shells 0.6, μ ground 0.1, other masses | Estimates, to measure |
| Remanence 1.45 T (N54) | Assumed, to confirm |
| dt, softening, tolerances | Numerical, to check by convergence |

> **Not established yet: convergence in dt.** At dt = 10⁻⁵ s the magnets touch about 25 % of the time, against 100 % at 10⁻⁴ s.

<div class="note">docs/model.md, "Parameter origins"</div>
