# 001: Remove dead code

Status: merged
Branch: `feature/001-remove-dead-code`

## Need

First step of the repository reorganisation. Before restructuring the
simulator into a package, remove the scripts that nothing uses, so that the
next specs only move code that matters.

Investigation (2026-11-23, `main` at `8233746`):

- `unite.py`: Hugo's first PyChrono test (2026-10-13). A single disc seen from
  the side with an eccentric rotor and a constant torque; placeholder values
  ("valeurs provisoires"). No file imports it, no `make` target runs it. It
  shares nothing with the simulator (no `Parametres`, no magnets, no analytic
  contacts, no DC motor).
- `test_3_granulobots_simple.py`: the old spring model of the triangle
  (external torques, magnetic springs). Superseded by the NSC simulator. It
  runs a simulation on import, which is why `make test` cannot use
  `-p 'test_*.py'`. Its only mention in code is a docstring line in
  `test_3_granulobots.py`.
- `test_2_granulobots.py`: a 21-line wrapper that sets `nombre_robots=2` and
  `tensions_cibles=(0.3, 0, 0)`, then calls `test_3_granulobots.main()`. The
  CLI already does the same with `--robots 2 --tensions 0.3 0 0`. Nothing
  imports it.

Kept on purpose: `campagne_accrochage.py` (convergence campaigns, still needed
by the roadmap), `validation_modele.py` (`make validate`), `prototype_hugo.json`
(cited by `docs/model.md`), and all other modules (used by the simulator or
the tests).

## Expected behaviour

- The three files above are deleted (`git rm`). They stay in git history:
  `git show 8233746:03_Simulation_PyChrono/<file>`.
- The simulator, its CLI flags and its defaults are unchanged. No simulator
  logic is touched; the only code edit is removing the docstring line that
  points to `test_3_granulobots_simple.py`.
- The 2-unit bench is run with
  `make sim NAME=bench_2 ARGS="--robots 2 --tensions 0.3 0 0"`, which gives the
  same parameters as the old wrapper.

## Physics and assumptions

None. Purely technical.

## Files concerned

- `03_Simulation_PyChrono/unite.py`: deleted.
- `03_Simulation_PyChrono/test_3_granulobots_simple.py`: deleted.
- `03_Simulation_PyChrono/test_2_granulobots.py`: deleted.
- `03_Simulation_PyChrono/test_3_granulobots.py`: drop the docstring line
  "Le modèle simple précédent reste dans test_3_granulobots_simple.py."
- `AGENTS.md`: Architecture section (drop the legacy and wrapper entries, add
  the 2-unit bench command), and the `make test` note about
  `test_3_granulobots_simple.py`.
- `specs/IDEES.md`: drop the "remove the legacy scripts" idea.
- `docs/decisions.md`: record the removal and where to find the files.
- `results/2026-10-14-triangle-3-units/`: new. The 3 s triangle run at 3.25 V
  from 2026-10-14 21:38 (made on Victor's machine after pulling `b332380`, the GIF
  reviewed at the team meeting), moved there from the ignored
  `03_Simulation_PyChrono/test_3_granulobots.{csv,gif,json}`, with a
  `README.md` following `results/README.md`. Its parameters equal the current
  defaults. It differs from the copy in history, so it is kept rather than
  deleted (developer's choice, 2026-11-23).

Local cleanup on Victor's machine (ignored files, not in git, not part of the
commit; approved by the developer on 2026-11-23 because they cannot be
recovered):

- `engrenages.gif` (repo root, 2026-10-13): an early animation, differs from
  the copy removed in `5581a15`.
- `runs/probe_point_tech.{csv,json}`: a 2026-11-10 probe.
- `03_Simulation_PyChrono/__pycache__/`: regenerated automatically.

## Planned tests

- `make test` passes (10 tests).
- `make check-env` passes.
- Equivalence of the 2-unit bench: before deleting the wrapper, run
  `test_2_granulobots.py --duree 0.1 --sans-gif` and the CLI with
  `--robots 2 --tensions 0.3 0 0 --duree 0.1 --sans-gif`; the two CSV files
  must be identical.
- Short triangle run (`--duree 0.1 --sans-gif`, 21 samples) gives a CSV
  and a JSON identical to the same run before the deletions.
- `grep` finds no remaining reference to the deleted files outside
  `docs/decisions.md`, `specs/` and git history.

## Out of scope

- Renaming or moving files, restructuring into a package (next spec).
- Translating identifiers to English.
- Changing the `make test` discovery pattern.
- Renaming `01_Sujet_et_rapports/` and `04_Design_STL/`.
- `.vscode/settings.json` (editor config, harmless).

## Review

Independent review by a separate agent (2026-11-23). `make test` passes.

- No remaining reference to the deleted files in code, Makefile, hooks,
  `.gitignore` or docs, apart from history entries and the example phrase in
  the `feature` skill. No action.
- Bench equivalence confirmed: `Parametres` derives nothing from
  `nombre_robots` at construction, and the CLI sets the same two fields. Only
  the default output path differs (`runs/bench_2.*` instead of
  `03_Simulation_PyChrono/test_2_granulobots.*`). No action.
- Edge case: with the wrapper, a `--parametres` JSON that sets
  `nombre_robots` or `tensions_cibles` overrode the bench values; with the
  flags, the flags win. The new order is the expected one. No action.
- Results README said the run was made by Hugo. Confirmed wrong: Victor's
  reflog shows the pull of `b332380` at 21:30 and the files date from 21:38
  on his machine; the copy in `b332380` is a 0.6 s run. Fixed.
- README numbers match the JSON summary, the rerun command matches the
  defaults, and `.gitignore` and the pre-commit hook accept the outputs under
  `results/` (about 2.4 MB). No action.
