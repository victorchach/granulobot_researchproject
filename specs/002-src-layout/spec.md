# 002: Move the code to a src/ layout

Status: merged
Branch: `feature/002-src-layout`

## Need

Second step of the repository reorganisation (see `docs/decisions.md`,
2026-11-23). The simulator lives in `03_Simulation_PyChrono/`, a flat folder
whose file names do not say what the files do: the simulator is called
`test_3_granulobots.py`, the tests and the validation sit next to it, and
outputs used to be written into it. The top-level folders carry numbers
(`01_`, `03_`, `04_`) that mean nothing to a new reader.

This spec only moves and renames. Splitting the 670-line simulator into
modules is spec 003; translating identifiers to English is spec 004.

Target layout agreed with Victor on 2026-11-23 (option A, "src layout").

## Expected behaviour

### Moves (`git mv`, content unchanged apart from imports and paths)

| Before | After |
| --- | --- |
| `03_Simulation_PyChrono/test_3_granulobots.py` | `src/granulobot/simulator.py` |
| `03_Simulation_PyChrono/granulobot_physics.py` | `src/granulobot/parameters.py` |
| `03_Simulation_PyChrono/magnet_cylinders.py` | `src/granulobot/magnets.py` |
| `03_Simulation_PyChrono/chrono_headless.py` | `src/granulobot/chrono_env.py` |
| `03_Simulation_PyChrono/diagnostic_accrochage.py` | `src/granulobot/analysis.py` |
| `03_Simulation_PyChrono/campagne_accrochage.py` | `scripts/campaign.py` |
| `03_Simulation_PyChrono/test_granulobot_physics.py` | `tests/test_physics.py` |
| `03_Simulation_PyChrono/validation_modele.py` | `tests/test_dynamics.py` |
| `03_Simulation_PyChrono/prototype_hugo.json` | `configs/prototype_hugo.json` |
| `01_Sujet_et_rapports/` | `references/` |
| `04_Design_STL/` | `cad/` |

New files: `src/granulobot/__init__.py` (package docstring only) and
`src/granulobot/__main__.py` (calls `simulator.main()`).

`parameters.py` keeps the pure laws (`dipoles`, `frottement`, `moteur_cc`)
for now; spec 003 moves them into the model modules.

### Imports and how to run

- Imports become absolute: `from granulobot.parameters import Parametres`,
  `from granulobot.chrono_env import chrono`, and so on, including the lazy
  imports inside functions.
- `src/` goes on the import path through `PYTHONPATH=src`, exported by the
  Makefile. No `pip install` step, so nothing changes in `make setup`.
- Raw commands (from the repo root, inside `conda activate chrono`):

  | `make` | Raw command |
  | --- | --- |
  | `make check-env` | `PYTHONPATH=src python -m granulobot.chrono_env` |
  | `make test` | `PYTHONPATH=src python -m unittest discover -s tests -p test_physics.py` |
  | `make validate` | `PYTHONPATH=src python tests/test_dynamics.py` |
  | `make sim NAME=x ARGS=...` | `PYTHONPATH=src python -m granulobot --sortie runs/x ...` |
  | `make diag CSV=...` | `PYTHONPATH=src python -m granulobot.analysis runs/x.csv` |
  | `make replay CSV=...` | `PYTHONPATH=src python -m granulobot --rejouer runs/x.csv` |

  `make sim`, `make test` and the other targets keep their names and
  arguments.

### Default output paths (the only behaviour change)

Nothing is written inside `src/`, `scripts/` or `tests/` any more:

- simulator without `--sortie`: `runs/sim` at the repo root (before: next to
  the script, `03_Simulation_PyChrono/test_3_granulobots.*`);
- `scripts/campaign.py` without `--sortie`: `runs/campaign/` (before:
  `03_Simulation_PyChrono/essais_plan/`);
- `tests/test_dynamics.py --animation`: `runs/validation_animation` (before:
  `03_Simulation_PyChrono/test_3_granulobots`).

The repo root is found from the module path
(`Path(__file__).resolve().parents[2]` in `src/granulobot/`), so these
defaults do not depend on the current directory.

### Config, docs and guards

- `Makefile`: `PYTHONPATH=src`, new paths for every target.
- `.gitignore`: the `03_Simulation_PyChrono/**` output patterns are replaced
  by the same patterns for `src/`, `scripts/` and `tests/`.
- `.claude/settings.json`: the read-only deny rules move from
  `01_Sujet_et_rapports/**` and `04_Design_STL/**` to `references/**` and
  `cad/**` (approved by Victor on 2026-11-23). The edit guard script and
  `.codex/hooks.json` need no change (they match `*.py` anywhere).
- `.vscode/settings.json`: add `"python.analysis.extraPaths": ["src"]` so the
  editor resolves `granulobot` imports.
- Docstring usage lines in the moved files (`python test_3_granulobots.py ...`)
  are updated to the new commands. French prose stays (spec 004).
- The paper path written into each run's JSON (`hypotheses.sources`) becomes
  `references/scirobotics.adh4130.txt`. This is the only difference in the
  run outputs.
- `AGENTS.md`: layout table, commands table, architecture section, rules
  (`references/` and `cad/` read only), `make test` note.
- `CLAUDE.md`, `README.md`, `docs/model.md`, `.agents/skills/feature/SKILL.md`,
  `.agents/skills/run-sim/SKILL.md`: new paths.
- `docs/architecture.md` (new): the file map and the call flow of `make sim`
  (what calls what, from the CLI to `DoStepDynamics` and the outputs), for the
  layout after this spec. Spec 003 updates it.
- `docs/decisions.md`: the layout decision. Older entries keep the old paths,
  since they describe the past.
- `specs/IDEES.md`: drop the "Rename `test_3_granulobots.py`" idea.

## Physics and assumptions

None. Purely technical. No parameter or law changes.

## Files concerned

Every file listed in the moves table, plus `Makefile`, `.gitignore`,
`.claude/settings.json`, `.vscode/settings.json`, `AGENTS.md`, `CLAUDE.md`,
`README.md`, `docs/model.md`, `docs/architecture.md`, `docs/decisions.md`,
the `feature` and `run-sim` skills, `specs/IDEES.md`, `specs/README.md`.

## Planned tests

References recorded on `main` (`a022c6c`) before branching: triangle and
2-unit bench, `--duree 0.1 --sans-gif`, 21 samples each; `make validate`
passes (7 tests).

- `make test` passes (10 tests) and `make validate` passes (7 tests).
- `make check-env` passes.
- `make sim NAME=x ARGS="--duree 0.1 --sans-gif"` gives a CSV identical to the
  triangle reference; with `--robots 2 --tensions 0.3 0 0`, identical to the
  bench reference. The JSON files match except `hypotheses.sources`.
- `make diag` and `make replay` work on that run.
- `python -m granulobot --duree 0.01 --sans-gif` run from the repo root and
  from another directory writes to `<repo>/runs/sim.*`.
- `git diff -M --stat main` shows the moves as renames, so `git log --follow`
  keeps each file's history.
- `grep` finds no stale reference to the old paths outside history entries
  (`docs/decisions.md`, `specs/001-*`, `results/`).
- No iCloud duplicate (`* 2`) after the folder renames.

## Out of scope

- Splitting `simulator.py` (spec 003) and translating identifiers (spec 004).
- A `pyproject.toml` and an installable package.
- Changing what `make test` covers.
- Hugo's 6-unit prototype: it stays on its own branch, on the old layout, and
  is ported by hand later.

## Review

Independent review by a separate agent (2026-11-23). It ran `make test`,
`make check-env`, `make validate`, a short `make sim`, `make diag`,
`make replay`, `--parametres configs/prototype_hugo.json` and the package
imports; all pass. Imports, default outputs, the Makefile (make 3.81 and 4.x),
the guards and the renames (R093 to R100) are fine. Findings:

- Part of the change was not staged (the `hypotheses.sources` path in
  `simulator.py`, the spec, `specs/IDEES.md`). Confirmed; everything is
  staged before the commit.
- `docs/decisions.md`: the new entry replaced the heading of the previous
  2026-11-23 entry instead of going above it. Confirmed and fixed.
- `.gitignore`: outputs left on disk in `03_Simulation_PyChrono/` after a pull
  (run JSON, `essais_plan/`) were no longer ignored and could be committed by
  `git add -A`. Confirmed (`git check-ignore`); the old patterns are kept in a
  "old layout" block. `.py` files there are still not ignored.
- `run-sim` skill and `AGENTS.md` disagreed on where a `--parametres` file
  goes. Confirmed; both now say: scratch in `runs/`, kept in `configs/` or in
  the result folder.
- `docs/architecture.md` called the fixed reference `ChBody` "the ground".
  Confirmed; it now lists the reference body and the `ChBodyEasyBox` ground
  separately.
