---
marp: true
theme: granulobot
paginate: true
header: "Granulobot simulation · 3. Code and workflow"
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _header: "" -->

# Granulobot simulation

3. Code architecture and workflow

How the code evolved, version by version

---

<!-- _footer: "Added 2026-11-24 · describes the code of 2026-10-14 (commit b332380)" -->

## <span class="tag grey">v1</span> October 2026: one folder of scripts

<div class="cols-wide-left">
<div>

```
03_Simulation_PyChrono/
├── test_3_granulobots.py         670 lines
├── granulobot_physics.py         230
├── test_3_granulobots_simple.py  156
├── test_granulobot_physics.py    116
├── validation_modele.py          111
├── campagne_accrochage.py        102
├── unite.py                       89
├── diagnostic_accrochage.py       81
├── magnet_cylinders.py            77
├── chrono_headless.py             43
├── test_2_granulobots.py          21
└── validation/, essais_plan/   run outputs
```

</div>
<div>

- One **670-line script** held the bodies, contacts, motor, magnetism, time loop, CSV, GIF and CLI.
- Old prototypes next to the current code.
- Run outputs committed beside the sources.
- French names; **2 or 3 units only**.
- Hard to extend to a ring, and two people editing one file.

</div>
</div>

---

<!-- _footer: "Added 2026-11-24 · specs 001 to 005, merged 2026-11-23 and 24" -->

## <span class="tag">v2</span> November 2026: a Python package

<div class="cols-wide-left">
<div>

```
src/granulobot/
├── __main__.py      CLI            92 lines
├── parameters.py    every setting, with its origin
├── model/           WHAT a Granulobot is
│   ├── unit.py         4 bodies and their links
│   ├── motor.py        DC motor, internal friction
│   ├── magnets.py      cylinder field, dipoles
│   └── contacts.py     analytic NSC contacts
├── simulation/      HOW a run works
│   ├── world.py        solver, ground, units
│   ├── loop.py         time loop, summary
│   └── recording.py    CSV and JSON
└── output/          WHAT we get out (no PyChrono)
    ├── analysis.py     rotations, detachments
    └── animation.py    the GIF
tests/  scripts/  configs/  results/  runs/ (ignored)
```

</div>
<div>

- Split by role: **model**, **simulation**, **output**.
- Largest file: 193 lines.
- Fast tests (`make test`, < 1 s) and PyChrono tests (`make validate`).
- Everything in **English**: code, CSV columns, docs.
- Run outputs in `runs/`, kept results in `results/`.

</div>
</div>

---

<!-- _footer: "Added 2026-11-24" -->

## What happens in one run

```
make sim NAME=ring6 ARGS="--params configs/ring6_alternating.json"
  │
  ├─ Parameters.check()                         are the values consistent?
  ├─ create_system(p)                           simulation/world.py
  │    ├─ NSC system, solver, ground
  │    ├─ ring_positions(n, side)               simulation/layout.py
  │    ├─ create_unit(...) for each unit        model/unit.py
  │    └─ CircularContacts callback             model/contacts.py
  ├─ time loop, dt = 1e-5 s by default          simulation/loop.py
  │    ├─ apply_motor(...)                      model/motor.py
  │    ├─ apply_magnetism(...)                  model/magnets.py
  │    ├─ DoStepDynamics(dt)                    PyChrono
  │    └─ measure(...) at 200 Hz                simulation/recording.py
  ├─ analyze(rows)                              output/analysis.py
  └─ runs/ring6.csv, .json, .gif                output/animation.py
```

<div class="note">docs/architecture.md has the full call flow.</div>

---

<!-- _footer: "Added 2026-11-24 · spec 006, merged 2026-11-24" -->

## <span class="tag">v3</span> Spec 006: a ring of N units

- New `simulation/layout.py`, with no PyChrono:
  - `ring_positions(n, side)`: units on a **regular polygon**, neighbours `2R + gap` apart;
  - `coupled_pairs(n)`: unit i's active magnet faces unit i+1's free magnet, and the last unit closes the ring on A.
- **N = 2 to 26** (names A to Z); N = 3 gives back the old triangle.
- `--voltages` takes one value per unit; the 6-unit alternating reference is a config file: `configs/ring6_alternating.json`.
- Ported from Hugo's 6-unit branch, without merging it: it started from v1.

---

<!-- _footer: "Added 2026-11-24" -->

## How we work: two developers, two coding agents

<div class="cols">
<div>

- Victor with **Claude Code**, Hugo with **Codex**: same rules (`AGENTS.md`), same shared skills.
- **Any code change** goes through a spec:
  1. spec in `specs/NNN-name/`, approved before coding;
  2. implementation and tests;
  3. **independent review** by a second agent;
  4. merge into `main` after approval.
- A hook **blocks code edits** outside such a branch.

</div>
<div>

| Skill | For |
| --- | --- |
| `feature` | code changes, spec to merge |
| `run-sim` | running and analysing a scenario |
| `keep-result` | moving a run to `results/` and the journal |
| `slides` | updating these decks |
| `sync` | pulling the teammate's work |
| `humanizer` | prose for people |

</div>
</div>
