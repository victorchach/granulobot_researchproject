# Roadmap

Agreed at the team meeting that reviewed `test_3_granulobots.gif`
(late October 2026). The reasons are in `decisions.md`.

## Step 1: start from a synchronized state and keep it

- Ring of 6 units laid out as a regular hexagon. Each unit's active magnet
  faces the free magnet of the next unit (A to B, ..., F to A).
- Target state: the active liquid state (paper, Fig. 4). The control is open
  loop with alternating biases, u_i = (-1)^i |u| (paper eq. 8), so that
  neighbouring rotors turn in opposite directions.
- Horizontal plane, units lying on a slippery support.
- Validated when, over a long run (2 to 5 min of simulated time):
  - the ring keeps its shape: pair distances stay stable and no unit
    detaches;
  - the rotor directions keep alternating;
  - the sum of the rotor speeds stays close to zero.

## Step 2: from a transient regime to the synchronized state

- Start from random initial states. The ring must converge from any of them,
  however long it takes.
- Needs the paper's self-organizing control, u_i = |u| sgn(dθ_i/dt)
  (eq. 7). The full feedback law of eq. 2 (gains G and α) comes later, for the
  self-oscillating solid state (Fig. 6).
- The synchronization metric is still to be chosen (candidate: <S_max> from
  the FFT of θ_i(t), as in the paper).

## Step 3: match reality

- Compare with experiments on the real robots to calibrate the constants:
  magnet force, friction coefficients, motor.
- Which experimental data will be available is still open.

## Cross-cutting

- Two friction regimes. A magnetic contact (coupled magnets, large normal
  force) rolls without slipping. A steric contact (shells touching without
  a coupled magnet) slips once the Coulomb limit is exceeded, which is what
  happens when locomotion gets blocked.
- Switch from the prototype dimensions to the paper's (r = 24 mm). This is
  deferred: the code is not to change yet.
- Computation time will be addressed once the physics works.
