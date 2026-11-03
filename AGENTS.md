# Granulobot simulation (PIR INSA Lyon, 2026)

Shared instructions for every coding agent (Codex, Claude Code) and every human
working in this repo. Keep this file accurate: update it in the same change
that alters a command, a file layout or a convention.

## Goal

Build a general simulator of Granulobots (Saintyves, Spenko, Jaeger,
*Science Robotics* 2024) in PyChrono, using NSC contacts: rigid contacts and
exact Coulomb friction instead of last year's penalty springs. The current
focus is the aggregate's collective states, starting with the active liquid
state of a 6-unit ring. Later, the simulator will be calibrated against the
real robots. See `docs/roadmap.md` for the plan and `docs/decisions.md` for
the decisions behind it.

Contributors: Victor (Claude Code, macOS) and Hugo (Codex, Ubuntu), under
Pr. Baudouin Saintyves (Inria / INSA, CITI lab).

## Layout

| Path | Content |
| --- | --- |
| `01_Sujet_et_rapports/` | Reference material: the paper, its supplementary material, the assignment and last year's report (PDF, plus `.txt` extractions for search). Read only. |
| `03_Simulation_PyChrono/` | All simulation code (flat Python modules, see Architecture). |
| `04_Design_STL/` | CAD files of the real unit. Read only. |
| `docs/` | Roadmap, decisions and model notes (Markdown, the source of truth). |
| `specs/` | Feature specs (`NNN-name/spec.md`), index and ideas backlog. |
| `results/` | Runs worth keeping, versioned on purpose (see `results/README.md`). |
| `runs/` | Scratch simulation outputs. Ignored by git. |
| `tools/git-hooks/` | Versioned sources of the local git hooks. |

## Environment and commands

PyChrono is only distributed via conda. The tested env is named `chrono`, with
Python 3.11 and PyChrono 10.0.0, on macOS (Victor) and Ubuntu (Hugo, Python 3.11.17).

| `make` | Raw command (inside `conda activate chrono`) |
| --- | --- |
| `make setup` | `conda create -n chrono -c projectchrono -c conda-forge python=3.11 pychrono matplotlib pillow` |
| `make check-env` | `python 03_Simulation_PyChrono/chrono_headless.py` |
| `make test` | `python -m unittest discover -s 03_Simulation_PyChrono -p test_granulobot_physics.py` (fast, under 1 s) |
| `make validate` | `python 03_Simulation_PyChrono/validation_modele.py` (PyChrono dynamics, about 15 s) |
| `make sim NAME=x ARGS="..."` | `python 03_Simulation_PyChrono/test_3_granulobots.py --sortie runs/x ...` |
| `make diag CSV=runs/x.csv` | `python 03_Simulation_PyChrono/diagnostic_accrochage.py runs/x.csv` |
| `make replay CSV=runs/x.csv` | `python 03_Simulation_PyChrono/test_3_granulobots.py --rejouer runs/x.csv` |
| `make hooks` | copy `tools/git-hooks/*` into `.git/hooks/` |

Useful simulator flags: `--robots {2,3}`, `--duree`, `--dt`,
`--mode {tension,vitesse,couple}`, `--tensions A B C`, `--vitesses A B C`,
`--sans-moteurs`, `--sans-magnetisme`, `--sans-sol`, `--sans-gif`,
`--liaison-ideale`, `--parametres file.json`. Run a short probe first
(`--duree 0.2 --sans-gif`): the default `dt = 1e-5 s` makes long runs slow.

`make test` only covers `test_granulobot_physics.py`. Do not use
`-p 'test_*.py'`: `test_3_granulobots_simple.py` runs a simulation when it is
imported.

## Architecture (03_Simulation_PyChrono/)

- `granulobot_physics.py`: the `Parametres` dataclass, which holds every
  physical and numerical parameter together with a comment on where it comes
  from. It also has the pure laws, which don't need PyChrono: point dipoles
  (`dipoles`), the smoothed dry friction (`frottement`) and the DC motor
  (`moteur_cc`).
- `magnet_cylinders.py`: the field of axially magnetised finite cylinders,
  computed by surface-charge quadrature. The energy is Hermite-interpolated so
  that F = -dU/dd holds exactly.
- `test_3_granulobots.py`: the simulator, despite its name.
  - `creer_systeme` builds the bodies: per unit, a body, an active rotor, a
    free rotor and an outer free wheel.
  - `ContactsCirculaires` is a custom collision callback: analytic contacts
    between the shells, between the magnets and with the ground, passed to the
    NSC solver.
  - `appliquer_moteur` and `appliquer_magnetisme` apply the forces at each step.
  - `mesure` records the CSV row, `animation` makes the GIF, `simuler` and
    `main` run the simulation and the CLI.
  - It is currently limited to 2 or 3 units.
- `chrono_headless.py`: imports the PyChrono core without the graphics
  extensions, which fail to load (vsg3d/SDL2). Always import chrono through it.
- `diagnostic_accrochage.py`: post-analysis of a CSV (rotations, distances,
  detachment events). No PyChrono needed.
- `campagne_accrochage.py`: scenario sweeps and convergence campaigns.
- `test_2_granulobots.py`: a 2-unit wrapper around the simulator.
- `prototype_hugo.json`: the prototype dimensions Hugo provided, plus what is
  still to measure.
- Legacy: `test_3_granulobots_simple.py` (spring model) and `unite.py` (first
  single-unit test).

Outputs of a run: `<name>.csv` (200 Hz measurements, including contact
forces), `<name>.json` (parameters, assumptions, summary) and `<name>.gif`
(25 fps, physical time). See `docs/model.md` for the modelling assumptions and
the known limitations.

## Conventions

- SI units everywhere. z points up; unit axes are vertical (top view, flat on
  the support); units are named A, B, C, ...
- Every parameter default records its origin: measured, from the paper, or an
  estimate. Never change a physical default without a source, and record the
  change in `docs/decisions.md`.
- PyChrono 10 API notes:
  - declare the collision system explicitly
    (`sys.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)`),
    otherwise there are no contacts;
  - SWIG enums are flat symbols;
  - there is no `SetTimestep`: pass `dt` to `DoStepDynamics`;
  - a large `dt` causes tunneling;
  - names changed after version 8 (`ChVectorD` became `ChVector3d`).
- Language: everything written to the repo (code, comments, docs, commit
  messages) is in English. Existing French identifiers and comments are kept
  until a dedicated spec translates them; match the style of the file you
  edit.

## Rules

- Never edit or delete `01_Sujet_et_rapports/` or `04_Design_STL/`.
- Never commit derived outputs (CSV, GIF, MP4, logs, run JSON) outside
  `results/`. The `.gitignore` and the pre-commit hook enforce this.
  Input files (parameter JSON, `requirements.txt`, ...) are versioned: keep
  them outside `runs/`, `essais_*/` and `validation/`, which are ignored
  whole.
- Commit messages are in English, in the imperative mood, with no AI
  attribution (no `Co-Authored-By` trailer, no "Generated with" line). The
  commit-msg hook enforces this.
- Don't rewrite published history on `main` (no force push).
- Fix code only when there is a real problem, and investigate before changing
  anything.

## Git hooks

Git hooks are not versioned by git itself. After a fresh clone, run
`make hooks`, or copy `tools/git-hooks/*` into `.git/hooks/` and make them
executable. Re-run it whenever `tools/git-hooks/` changes.

- `commit-msg` rejects `Co-Authored-By` trailers and "Generated with ..."
  lines.
- `pre-commit` rejects derived outputs (CSV, GIF, MP4, logs) staged outside
  `results/`. When code is staged, it also runs `make test`, which needs
  `make` and the conda env `chrono`; if `make` is missing, the tests are
  skipped with a warning.
