# Architecture

How the code fits together: where each file lives, and what happens, in
order, when a simulation runs. The physics behind it is in `model.md`.
Keep this page in step with the code: any spec that moves a function or a
file updates it.

## Files

```
src/granulobot/          the simulator package
├── __main__.py          python -m granulobot  ->  simulator.main()
├── simulator.py         builds the system, runs the time loop, writes outputs
├── parameters.py        Parametres (every setting, with its origin) + pure laws
├── magnets.py           field of finite axial cylinder magnets
├── chrono_env.py        imports the PyChrono core without graphics extensions
└── analysis.py          post-analysis of a run (no PyChrono)
tests/
├── test_physics.py      pure laws, magnets, analysis        (make test)
└── test_dynamics.py     short PyChrono runs                 (make validate)
scripts/
└── campaign.py          scenario sweeps and convergence campaigns
configs/                 parameter files for --parametres
```

Spec 003 will split `simulator.py` into `model/` (unit, motor, magnets,
contacts), `simulation/` (world, loop, recording) and `output/` (analysis,
animation).

## What `make sim` does

`make sim NAME=probe ARGS="--duree 0.2"` runs
`python -m granulobot --sortie runs/probe --duree 0.2` with `PYTHONPATH=src`.
Each step names the file it lives in; `[PyChrono]` marks library calls.

```
 python -m granulobot ...                             [__main__.py]
   │
   ▼
 ═══ IMPORT ════════════════════════════════════════════════════════════
   import chrono                                       [chrono_env.py]
   import Parametres, moteur_cc, frottement, dipoles   [parameters.py]
   PARAMETRES = Parametres()   all defaults            [simulator.py]
   │
   ▼
 ═══ main() ════════════════════════════════════════  [simulator.py]
   parse the CLI options (argparse)
   p = PARAMETRES, then --parametres JSON, then the flags override it
   │
   ▼
 ═══ simuler(p, sortie) ════════════════════════════  [simulator.py]
   │
   ├─ p.verifier()  are the values consistent?         [parameters.py]
   │
   ├─ 1. BUILD ─────────────────────────────────────────────────────────
   │   creer_systeme(p)                                [simulator.py]
   │     ├─ ChSystemNSC(), solver PSOR or APGD         [PyChrono]
   │     ├─ fixed reference body (ChBody), the guides' anchor [PyChrono]
   │     ├─ the ground, if sol_actif: ChBodyEasyBox     [PyChrono]
   │     ├─ per unit: Unite(...), 4 bodies             [simulator.py]
   │     │    shell, active rotor, free rotor, free wheel
   │     │    ├─ ChLinkMateGeneric  guide: blocks tipping only
   │     │    ├─ ChLinkMotorRotationTorque  motor, active rotor <-> shell
   │     │    └─ ChLinkLockRevolute  pivots of free rotor and free wheel
   │     └─ ContactsCirculaires(...)  analytic contacts [simulator.py]
   │          └─ RegisterCustomCollisionCallback       [PyChrono]
   │
   ├─ 2. LOOP: duree / dt steps (20 000 for 0.2 s at 1e-5 s) ──────────
   │   each step:
   │   ├─ every 1/200 s: mesure(t, sys, robots, p) -> one CSV row
   │   │    ├─ ComputeContactForces, GetPos, ...       [PyChrono]
   │   │    └─ angle(), omega()                        [simulator.py]
   │   ├─ u.vider_forces()  clear last step's forces   [simulator.py]
   │   ├─ appliquer_moteur(u, i, t, p)  per unit       [simulator.py]
   │   │    ├─ moteur_cc(...)  voltage -> current -> torque [parameters.py]
   │   │    └─ frottement(...)  internal rotor friction     [parameters.py]
   │   ├─ appliquer_magnetisme(robots, p)  all magnet pairs [simulator.py]
   │   │    ├─ u.aimant(...)  magnet position          [simulator.py]
   │   │    ├─ pour_parametres(p)  magnet model, cached [magnets.py]
   │   │    ├─ CylindresAxiaux.evaluer(d)  force vs distance [magnets.py]
   │   │    │   (or dipoles(...) if modele_magnetique = "dipoles")
   │   │    └─ AccumulateForce / AccumulateTorque      [PyChrono]
   │   └─ sys.DoStepDynamics(dt)                       [PyChrono]
   │        ├─ calls ContactsCirculaires.OnCustomCollision:
   │        │  contact points, normals, distances      [simulator.py]
   │        ├─ solves contact forces + Coulomb friction [PyChrono]
   │        └─ integrates velocities and positions     [PyChrono]
   │
   └─ 3. END ───────────────────────────────────────────────────────────
       ├─ summary: max overlap, max force, displacements [simulator.py]
       ├─ analyser(rows, p)  rotations, distances, detachments [analysis.py]
       ├─ writes runs/probe.csv   (one row per sample)  [simulator.py]
       ├─ writes runs/probe.json  (parameters, assumptions, summary)
       └─ animation(rows, p, sortie) -> runs/probe.gif  [simulator.py]
            matplotlib redraws from the rows; no physics
```

In short: `simulator.py` drives everything, `parameters.py` and `magnets.py`
provide the physics we compute ourselves, PyChrono does the heavy work inside
`DoStepDynamics`, and `analysis.py` only runs at the end.

## Other entry points

- `make diag CSV=...`: `python -m granulobot.analysis`, reads a CSV and its
  JSON, prints the analysis. No PyChrono.
- `make replay CSV=...`: `python -m granulobot --rejouer`, redraws the GIF
  from a CSV without rerunning the dynamics.
- `scripts/campaign.py`: calls `simuler` once per scenario and writes a
  summary to `runs/campaign/`.
- `tests/test_dynamics.py`: calls `creer_systeme` and `simuler` on short runs.
