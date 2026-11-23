# Architecture

How the code fits together: where each piece lives, and what happens, in
order, when a simulation runs. The physics behind it is in `model.md`.
Keep this page in step with the code: any spec that moves a function or a
file updates it.

## Files

```
src/granulobot/               the simulator package
├── __main__.py               CLI: python -m granulobot (PARAMETERS, main)
├── __init__.py               REPO_ROOT, the repo root (default outputs in runs/)
├── parameters.py             Parametres: every setting, with its origin
├── chrono_env.py             PyChrono import without graphics + vect, xyz, angle, omega
│
├── model/                    WHAT a Granulobot is
│   ├── unit.py               Unit and create_unit: the 4 bodies and their links
│   ├── motor.py              DC motor law, internal friction, apply_motor
│   ├── magnets.py            cylinder and dipole fields, apply_magnetism
│   └── contacts.py           CircularContacts: analytic shell/magnet/ground contacts
│
├── simulation/               HOW a run works
│   ├── world.py              create_system: solver, ground, layout of the units
│   ├── loop.py               simulate: the time loop, summary, outputs
│   └── recording.py          measure (one CSV row), CSV and JSON writing
│
└── output/                   WHAT we get out of it (no PyChrono)
    ├── analysis.py           rotations, distances, detachments of a run
    └── animation.py          the GIF
tests/
├── test_physics.py           laws, magnets, analysis              (make test)
└── test_dynamics.py          short PyChrono runs                  (make validate)
scripts/
└── campaign.py               scenario sweeps and convergence campaigns
configs/                      parameter files for --parametres
```

Where future work goes: a new layout (the 6-unit ring) in
`simulation/world.py`; a new controller (eq. 7, eq. 2) in a new
`model/controller.py`, called from `model/motor.py`; a new measured quantity
in `simulation/recording.py`.

## What `make sim` does

`make sim NAME=probe ARGS="--duree 0.2"` runs
`python -m granulobot --sortie runs/probe --duree 0.2` with `PYTHONPATH=src`.
Each step names the file it lives in; `[PyChrono]` marks library calls.

```
 python -m granulobot ...                                    [__main__.py]
   │
   ▼
 ═══ main() ═══════════════════════════════════════════════  [__main__.py]
   PARAMETERS = Parametres()  all defaults                 [parameters.py]
   parse the CLI options (argparse)
   p = PARAMETERS, then --parametres JSON, then the flags override it
   │
   ▼
 ═══ simulate(p, output) ═══════════════════════════  [simulation/loop.py]
   │
   ├─ p.verifier()  are the values consistent?             [parameters.py]
   │
   ├─ 1. BUILD ──────────────────────────────────────────────────────────
   │   create_system(p)                               [simulation/world.py]
   │     ├─ ChSystemNSC(), solver PSOR or APGD             [PyChrono]
   │     ├─ fixed reference body (ChBody), the guides' anchor
   │     ├─ the ground, if sol_actif: ChBodyEasyBox        [PyChrono]
   │     ├─ positions: 2 units face to face, or a triangle
   │     ├─ per unit: create_unit(...)                       [model/unit.py]
   │     │    shell, active rotor, free rotor, free wheel
   │     │    ├─ ChLinkMateGeneric  guide: blocks tipping only
   │     │    ├─ ChLinkMotorRotationTorque  motor, active rotor <-> shell
   │     │    └─ ChLinkLockRevolute  pivots of free rotor and free wheel
   │     ├─ optional ideal link between paired magnets (--liaison-ideale)
   │     └─ CircularContacts(...)                     [model/contacts.py]
   │          └─ RegisterCustomCollisionCallback       [PyChrono]
   │
   ├─ 2. LOOP: duree / dt steps (20 000 for 0.2 s at 1e-5 s) ───────────
   │   each step:
   │   ├─ every 1/200 s: measure(t, sys, units, p) -> one CSV row
   │   │                                         [simulation/recording.py]
   │   │    ├─ ComputeContactForces, GetPos, ...       [PyChrono]
   │   │    └─ angle(), omega()                           [chrono_env.py]
   │   │    + magnet positions, from u.magnet(...)        [model/unit.py]
   │   ├─ u.clear_forces()  clear last step's forces      [model/unit.py]
   │   ├─ apply_motor(u, i, t, p)  per unit         [model/motor.py]
   │   │    ├─ dc_motor(...)  voltage -> current -> torque
   │   │    └─ friction(...)  internal friction of rotors and wheel
   │   ├─ apply_magnetism(units, p)  all magnet pairs [model/magnets.py]
   │   │    ├─ u.magnet(...)  magnet position             [model/unit.py]
   │   │    ├─ for_parameters(p)  magnet model, cached
   │   │    ├─ AxialCylinders.evaluate(d)  force vs distance
   │   │    │   (or dipoles(...) if modele_magnetique = "dipoles")
   │   │    └─ AccumulateForce / AccumulateTorque      [PyChrono]
   │   └─ sys.DoStepDynamics(dt)                       [PyChrono]
   │        ├─ calls CircularContacts.OnCustomCollision:
   │        │  contact points, normals, distances      [model/contacts.py]
   │        ├─ solves contact forces + Coulomb friction [PyChrono]
   │        └─ integrates velocities and positions     [PyChrono]
   │
   └─ 3. END ────────────────────────────────────────────────────────────
       ├─ summary: max overlap, max force, displacements [simulation/loop.py]
       ├─ analyze(rows, p)  rotations, distances, detachments
       │                                              [output/analysis.py]
       ├─ write_outputs: runs/probe.csv and runs/probe.json
       │    (parameters, assumptions, summary)    [simulation/recording.py]
       └─ animate(rows, p, output) -> runs/probe.gif [output/animation.py]
            matplotlib redraws from the rows; no physics
```

In short: `simulation/loop.py` drives a run, `model/` holds the physics we
compute ourselves, PyChrono does the heavy work inside `DoStepDynamics`, and
`output/` only runs at the end.

## Other entry points

- `make diag CSV=...`: `python -m granulobot.output.analysis`, reads a CSV and
  its JSON, prints the analysis. No PyChrono.
- `make replay CSV=...`: `python -m granulobot --rejouer`, redraws the GIF
  from a CSV without rerunning the dynamics (`output/animation.py`).
- `scripts/campaign.py`: calls `simulate` once per scenario and writes a
  summary to `runs/campaign/`.
- `tests/test_dynamics.py`: calls `create_system`, `apply_motor` and
  `simulate` on short runs.
