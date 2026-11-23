# 003: Split the simulator into model, simulation and output

Status: merged
Branch: `feature/003-split-simulator`

## Need

Third step of the repository reorganisation (`docs/decisions.md`,
2026-11-23). `src/granulobot/simulator.py` is 670 lines that do everything:
geometry helpers, the contact callback, the unit and its four bodies, the
world, the motor and magnet forces, the measurements, the time loop, the
outputs, the GIF and the CLI. The physical laws sit in `parameters.py` next
to the parameters. The 6-unit ring (roadmap step 1) and the controllers
(eq. 7, eq. 2) need clear places to go.

Target agreed with Victor on 2026-11-23 (drawn in the conversation, recorded
in `docs/architecture.md`): `model/` (what a granulobot is), `simulation/`
(how it runs), `output/` (what we get out of it).

## Expected behaviour

The code moves; it is not rewritten. Function bodies are copied as they are.
The only structural edit is that the body of the per-unit loop in
`creer_systeme` becomes a function, `creer_unite`, called from the same loop,
so that the bodies and links are created in exactly the same order.

### Where each piece goes

```
src/granulobot/
├── __init__.py        RACINE (repo root, for default outputs)
├── __main__.py        CLI: module docstring, PARAMETRES, main()
├── parameters.py      Parametres only
├── chrono_env.py      PyChrono import + vect, xyz, angle, omega
├── model/
│   ├── unit.py        noms, paires, Unite, creer_unite (4 bodies + links)
│   ├── motor.py       moteur_cc, frottement, appliquer_moteur
│   ├── magnets.py     CylindresAxiaux, pour_parametres, dot, cross,
│   │                  dipoles, appliquer_magnetisme
│   └── contacts.py    ContactsCirculaires
├── simulation/
│   ├── world.py       appariements, creer_systeme (solver, ground,
│   │                  layout, ideal link, contact callback)
│   ├── loop.py        simuler (time loop, summary, writes outputs)
│   └── recording.py   mesure, hypotheses, ecrire_sorties (CSV + JSON)
└── output/
    ├── analysis.py    analyser (git mv of analysis.py)
    └── animation.py   animation
```

| Today | After |
| --- | --- |
| `simulator.py` docstring, `PARAMETRES`, `main` | `__main__.py` |
| `simulator.py` `RACINE` | `__init__.py` |
| `simulator.py` `vect`, `xyz`, `angle`, `omega` | `chrono_env.py` |
| `simulator.py` `noms`, `paires`, `Unite`, unit part of `creer_systeme` | `model/unit.py` |
| `parameters.py` `moteur_cc`, `frottement`; `simulator.py` `appliquer_moteur` | `model/motor.py` |
| `magnets.py`; `parameters.py` `dot`, `cross`, `dipoles`; `simulator.py` `appliquer_magnetisme` | `model/magnets.py` |
| `simulator.py` `ContactsCirculaires` | `model/contacts.py` |
| `simulator.py` `appariements`, rest of `creer_systeme` | `simulation/world.py` |
| `simulator.py` `simuler` (minus the output writing) | `simulation/loop.py` |
| `simulator.py` `mesure`; output writing and `hypotheses` dict from `simuler` | `simulation/recording.py` |
| `analysis.py` | `output/analysis.py` |
| `simulator.py` `animation` | `output/animation.py` |

`simulator.py` and the top-level `magnets.py` and `analysis.py` disappear.
Each new sub-package has an `__init__.py` with a one-line docstring.

Choice to confirm: the motor law and the code that applies it to the Chrono
bodies live together in `model/motor.py` (same for the magnets), as drawn.
These modules import PyChrono, so `tests/test_physics.py` now loads it too
(about 30 ms; both developers have it). The alternative is to keep the laws
PyChrono-free and put `appliquer_moteur` and `appliquer_magnetisme` in a
`simulation/forces.py`.

### Callers updated

- `tests/test_physics.py`, `tests/test_dynamics.py`, `scripts/campaign.py`:
  imports from the new modules.
- `Makefile`: `make diag` runs `python -m granulobot.output.analysis`. The
  other targets do not change.
- Lazy imports that only existed to dodge the big module
  (`pour_parametres` inside `appliquer_magnetisme`, `analyser` inside
  `simuler`) become normal imports where no import cycle results.
  `animation` keeps its lazy matplotlib import.

### Unchanged

CLI flags, defaults, outputs (CSV columns, JSON content, GIF), French
identifiers and comments (spec 004), the 2-or-3-unit limit.

## Physics and assumptions

None. No law, parameter or default changes.

## Files concerned

`src/granulobot/` (all modules above), `tests/test_physics.py`,
`tests/test_dynamics.py`, `scripts/campaign.py`, `Makefile`, `AGENTS.md`
(architecture, `make diag` raw command), `docs/architecture.md` (file map and
call flow), `docs/model.md` (where `PARAMETRES` lives), `docs/decisions.md`,
`specs/README.md`.

## Planned tests

References recorded on `main` (`b2f0021`) before branching, outputs of
`python -m granulobot`:

| Run | Flags |
| --- | --- |
| triangle | `--duree 0.1 --sans-gif` |
| 2-unit bench | `--robots 2 --tensions 0.3 0 0 --duree 0.1 --sans-gif` |
| ideal link | `--liaison-ideale --duree 0.05 --sans-gif` |
| speed mode | `--mode vitesse --vitesses 0.3 0.3 0.3 --duree 0.05 --sans-gif` |
| dipoles | `--parametres <file with modele_magnetique=dipoles> --duree 0.05 --sans-gif` |
| no ground | `--sans-sol --sans-magnetisme --duree 0.05 --sans-gif` |
| with GIF | `--duree 0.08` |

- Every CSV and JSON is byte-identical to its reference; the GIF too.
- `make diag` on the triangle gives the same output as the reference.
- `make replay` works.
- `make test` (10 tests), `make validate` (7 tests), `make check-env` pass.
- `scripts/campaign.py --help` works.
- No module imports `granulobot.simulator`, `granulobot.magnets` or
  `granulobot.analysis` any more (`grep`).

## Out of scope

- Translating identifiers to English (spec 004).
- Generalising to N units or a ring layout; the layout code moves to
  `world.py` but is not changed.
- Any cleanup inside function bodies (naming, long lines, duplicated code).

## Review

Independent review by a separate agent (2026-11-23). No blocking finding.

- Function bodies compared with `ast` between `main` and the branch: 32 of 35
  names identical, each defined in exactly one place. The three that differ
  are the documented ones (`appliquer_magnetisme` loses its lazy import,
  `simuler` calls `ecrire_sorties`, `creer_systeme` calls `creer_unite`).
  `creer_unite` matches the old loop body, with the same order of
  `AddBody`, `AddLink` and `AddAccumulator` calls.
- The reviewer also ran 8 short runs on `main` and on the branch (including
  torque mode with `--sans-moteurs`, not in the reference set): CSV, JSON, GIF,
  `diag` output and `--rejouer` GIF are byte-identical.
- No import cycle; importing `granulobot`, `parameters` or `output` loads
  neither PyChrono nor matplotlib. No leftover reference to the removed
  modules outside history entries. Docs match the code.
- Non-blocking: `tests/test_physics.py` now needs PyChrono, as chosen in this
  spec. No action: the pre-commit hook already required the `chrono` env to
  run `make test`.
