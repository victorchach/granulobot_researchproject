---
marp: true
theme: granulobot
paginate: true
header: "Granulobot simulation · 1. Context"
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _header: "" -->

# Granulobot simulation

1. Context and goal

PIR, INSA Lyon, 2026 · Victor and Hugo
Supervisors: Baudouin Saintyves (Inria / INSA, CITI lab), Olivier Simonin

---

<!-- _footer: "Added 2026-11-24 · Saintyves, Spenko, Jaeger, Science Robotics 9, eadh4130 (2024), Fig. 1" -->

## Granulobots

![w:740](img/paper_fig1_granulobots.png)

- Gear-like units with **one actuator each**, coupled by magnets: an <span style="color:#c8102e">**active magnet**</span> driven by the motor, a <span style="color:#1f5fa8">**free magnet**</span> on a pivot.
- Aggregates self-assemble, reconfigure, and show **solid-like and liquid-like** collective states.


---

<!-- _footer: "Added 2026-11-24" -->

## The PIR assignment

- **Two subgroups**: one optimises the robot firmware, the other builds a **software simulator** of the aggregate.
- The simulator should make it easier to **test distributed algorithms** and to **scale to more units** than the hardware allows.
- Both platforms then implement strategies that let an aggregate **find a self-coordinated locomotion state from arbitrary initial parameters**.
- If time allows: compare simulation and hardware.

<div class="note">Sujet 15, PIR Granulobots 2026 (references/Sujet_15_PIR_Granulobots_2026.pdf).</div>

---

<!-- _footer: "Added 2026-11-24" -->

## Our approach

<div class="cols">
<div>

### Simulator
- **PyChrono 10** multibody engine.
- **NSC contacts**: rigid contacts and exact Coulomb friction, solved as constraints.
- Replaces last year's **spring-damper model**: contact stiffness and damping, plus a spring link between neighbours to hold the ring together. Its constants had to be tuned, and stiff ones made the time step unstable.

</div>
<div>

### Focus
- First the aggregate's **collective states**, starting with the **active liquid state** of a ring of 6 units.
- Then convergence to that state from any start.
- Later, **calibrate** against the real robots.

</div>
</div>

---

<!-- _footer: "Added 2026-11-24" -->

## Target: the active liquid state

<div class="cols-wide-left">
<div>

![w:640](img/paper_fig4_liquid_state.png)

</div>
<div>

- Closed chain of units, each motor biased with the **same magnitude**.
- Neighbours rotate in **opposite directions**, and the **sum of the rotation speeds stays near zero**.
- Open loop: alternating biases u<sub>i</sub> = (−1)<sup>i</sup> |u| (eq. 8).
- Self-organising: u<sub>i</sub> = |u| sgn(dθ<sub>i</sub>/dt) (eq. 7) reaches it after a transient.

</div>
</div>

<div class="note">Saintyves et al. (2024), Fig. 4 A–B (N = 10 units).</div>

---

<!-- _footer: "Added 2026-11-24" -->

## Roadmap

| Step | Goal | Status |
| --- | --- | --- |
| **1** | Ring of 6 units, alternating biases (eq. 8): keep the liquid state for 2 to 5 min | <span class="tag">in progress</span> holds 60 s; 5 min run running |
| **2** | Reach the synchronised state from random starts (eq. 7), synchronisation metric | <span class="tag grey">next</span> |
| **3** | Compare with the real robots, calibrate magnets, friction, motor | <span class="tag grey">later</span> |

- Cross-cutting: two friction regimes (magnetic contacts roll, steric contacts slip), the paper's dimensions, computing time.

<div class="note">docs/roadmap.md</div>
