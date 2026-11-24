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
| `src/granulobot/` | The simulator, as a Python package (see Architecture). |
| `tests/` | `test_physics.py` (fast, `make test`) and `test_dynamics.py` (PyChrono, `make validate`). |
| `scripts/` | Entry points built on the package, such as scenario campaigns. |
| `configs/` | Parameter files for `--params` (inputs, versioned). |
| `references/` | Reference material: the paper, its supplementary material, the assignment and last year's report (PDF, plus `.txt` extractions for search). Read only. |
| `cad/` | CAD files (STL) of the real unit. Read only. |
| `docs/` | Roadmap, decisions, architecture and model notes (Markdown, the source of truth). |
| `specs/` | Feature specs (`NNN-name/spec.md`), index and ideas backlog. |
| `results/` | Runs that mark a step of the project, versioned on purpose, and `journal.md`, the path from one kept run to the next (see `results/README.md`). |
| `runs/` | Scratch simulation outputs. Ignored by git. |
| `tools/git-hooks/` | Versioned sources of the local git hooks. |
| `tools/agent-hooks/` | The edit guard shared by the Claude Code and Codex hooks. |
| `.agents/skills/` | Shared agent skills (`feature`, `run-sim`, `keep-result`, `sync`, `humanizer`). Codex reads them here. |
| `.claude/` | Claude Code settings; `.claude/skills/<name>` are symlinks to `.agents/skills/<name>`. |
| `.codex/` | Codex project hooks (`hooks.json`). |

## Workflow (both developers, both agents)

Victor (Claude Code) and Hugo (Codex) follow the same workflow, through the
skills in `.agents/skills/`:

| Skill | Use it for |
| --- | --- |
| `feature` | Any code change (`*.py`, `*.ipynb`, `Makefile`), however small, from spec to merge |
| `run-sim` | Running a scenario and analysing its outputs, without changing code |
| `keep-result` | Moving a run that matters from `runs/` to `results/`, with its analysis README and a new entry in `results/journal.md` |
| `sync` | Pulling the teammate's work and checking that docs still match the code |
| `humanizer` | Any prose meant for people (reports, README, docs, messages) |

- **No code change outside the `feature` workflow.** In short: investigate;
  write `specs/NNN-name/spec.md` on branch `feature/NNN-name`; wait for the
  developer's approval of the spec; implement and run `make test`; get an
  independent review by a separate agent; merge into `main` locally only
  after the developer's approval. A hook blocks code edits outside such a
  branch in both tools (see Agent hooks).
- Docs, specs, skills and config can be edited directly, but must stay
  consistent with this file.
- Pull before starting a spec, and run `sync` after every pull of the
  teammate's work. Push merged work soon, so the other side sees it.
- Spec numbers with two people: pick NNN as the next free number in
  `specs/README.md` right after pulling `main`. If both pick the same number,
  the one who merges second renumbers their spec (folder, title, index row
  and branch). On a `specs/README.md` conflict, keep both rows.
- Never commit, merge or push unless the developer asks. Suggest a commit
  when a coherent step is done.
- Talk to the developer in their language (French for both); everything
  written into the repo is in English.

## Environment and commands

PyChrono is only distributed via conda. The tested env is named `chrono`, with
Python 3.11 and PyChrono 10.0.0, on macOS (Victor) and Ubuntu (Hugo, Python 3.11.17).

The package lives in `src/`, so every raw command runs from the repo root
with `PYTHONPATH=src` (the Makefile sets it).

| `make` | Raw command (inside `conda activate chrono`, from the repo root) |
| --- | --- |
| `make setup` | `conda create -n chrono -c projectchrono -c conda-forge python=3.11 pychrono matplotlib pillow` |
| `make check-env` | `PYTHONPATH=src python -m granulobot.chrono_env` |
| `make test` | `PYTHONPATH=src python -m unittest discover -s tests -p test_physics.py` (fast, under 1 s) |
| `make validate` | `PYTHONPATH=src python tests/test_dynamics.py` (PyChrono dynamics, about 15 s) |
| `make sim NAME=x ARGS="..."` | `PYTHONPATH=src python -m granulobot --output runs/x ...` |
| `make diag CSV=runs/x.csv` | `PYTHONPATH=src python -m granulobot.output.analysis runs/x.csv` |
| `make replay CSV=runs/x.csv` | `PYTHONPATH=src python -m granulobot --replay runs/x.csv` |
| `make hooks` | copy `tools/git-hooks/*` into `.git/hooks/` |

Scenario campaigns: `PYTHONPATH=src python scripts/campaign.py --duration 0.6`
(outputs in `runs/campaign/`).

Useful simulator flags: `--units N` (2 to 26), `--duration`, `--dt`,
`--mode {voltage,speed,torque}`, `--voltages V ...`, `--speeds W ...` (one
value per unit, in order A, B, ...),
`--no-motors`, `--no-magnetism`, `--no-ground`, `--no-gif`,
`--ideal-link`, `--params file.json`. Run a short probe first
(`--duration 0.2 --no-gif`): the default `dt = 1e-5 s` makes long runs slow.

Without `--output`, the simulator writes to `runs/sim` at the repo root.
Nothing writes into `src/`, `scripts/` or `tests/`.

`make test` only covers `tests/test_physics.py`. The dynamics tests in
`tests/test_dynamics.py` take about 15 s and run with `make validate`.

The 2-unit bench (one facing pair, active A to free B):
`make sim NAME=bench_2 ARGS="--units 2 --voltages 0.3 0 0"`.

The 6-unit ring with alternating biases (roadmap step 1, paper eq. 8):
`make sim NAME=ring6 ARGS="--params configs/ring6_alternating.json"`. It costs
about 4 min of computing per simulated second at `dt = 1e-5 s`.

## Architecture (src/granulobot/)

`docs/architecture.md` has the file map and the call flow of a run, from the
CLI to the outputs. Imports are absolute
(`from granulobot.model.motor import dc_motor`). The simulator takes 2 to 26
units: a facing pair for 2, a closed ring on a regular polygon for 3 or more
(spec 006).

- `__main__.py`: the CLI (`python -m granulobot`), with `PARAMETERS`, the
  defaults used by a run, and `main`.
- `__init__.py`: `REPO_ROOT`, the repo root, for default outputs in `runs/`.
- `parameters.py`: the `Parameters` dataclass, which holds every
  physical and numerical parameter together with a comment on where it comes
  from.
- `chrono_env.py`: imports the PyChrono core without the graphics
  extensions, which fail to load (vsg3d/SDL2). Always import chrono through it
  (`from granulobot.chrono_env import chrono`). Also `vect`, `xyz`, `angle`,
  `omega`.
- `model/`, what a Granulobot is:
  - `unit.py`: `Unit` and `create_unit`, which builds one unit's four bodies
    (shell, active rotor, free rotor, outer free wheel) and their links;
    `unit_names` and `unit_pairs`.
  - `motor.py`: the DC motor law (`dc_motor`), the smoothed dry friction
    (`friction`) and `apply_motor`, which applies them at each step.
  - `magnets.py`: the field of axially magnetised finite cylinders, computed
    by surface-charge quadrature (the energy is Hermite-interpolated so that
    F = -dU/dd holds exactly), point dipoles (`dipoles`), and
    `apply_magnetism`, which applies them at each step.
  - `contacts.py`: `CircularContacts`, a custom collision callback with
    analytic contacts between the shells, between the magnets and with the
    ground, passed to the NSC solver.
- `simulation/`, how a run works:
  - `world.py`: `create_system` (solver, ground, placement of the units,
    ideal link, contact callback).
  - `layout.py`: `ring_positions` and `coupled_pairs`, the layout of the
    units (no PyChrono, also used by the analysis).
  - `loop.py`: `simulate`, the time loop, the summary and the outputs.
  - `recording.py`: `measure` (one CSV row) and the CSV/JSON writing.
- `output/`, what we get out of a run (no PyChrono needed):
  - `analysis.py`: `analyze`, post-analysis of a CSV (rotations, distances,
    detachment events).
  - `animation.py`: `animate`, the GIF.

Outside the package:

- `scripts/campaign.py`: scenario sweeps and convergence campaigns.
- `configs/prototype_hugo.json`: the prototype dimensions Hugo provided, plus
  what is still to measure.
- `configs/ring6_alternating.json`: the 6-unit ring with alternating biases
  ±3.25 V (roadmap step 1).

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
  messages, run outputs) is in English (specs 004 and 005). Name new things
  with the glossary in `specs/004-translate-internals/spec.md`; the old
  French names and their English equivalents are listed in
  `specs/005-translate-interface/spec.md`. Run files written before spec 005
  (French columns and keys) are not readable by `make diag` or `make replay`.

## Rules

- Never edit or delete `references/` or `cad/`.
- Never commit derived outputs (CSV, GIF, MP4, logs, run JSON) outside
  `results/`. The `.gitignore` and the pre-commit hook enforce this. In
  `results/`, a CSV over about 5 MB stays local too (`keep-result`).
  Input files (parameter JSON, `requirements.txt`, ...) are versioned: a
  parameter file worth keeping goes in `configs/` (or next to the result it
  produced in `results/`). `runs/` is ignored whole, so a file there is
  scratch.
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

## Agent hooks

`tools/agent-hooks/guard-code-edits.sh` is a PreToolUse hook used by both
agents. It blocks any edit of `*.py`, `*.ipynb` or `Makefile` unless the
current branch is `feature/NNN-name` and `specs/NNN-name/spec.md` exists. It
needs `python3` on the PATH. Two exceptions:
- files outside this repo (scratch scripts in a temp dir) are not guarded,
  and each git worktree is checked on its own branch;
- during a merge, files still in conflict can be edited on any branch, so a
  conflict from `sync` can be resolved on `main`.

- Claude Code runs it from `.claude/settings.json` (Edit, Write,
  NotebookEdit).
- Codex runs it from `.codex/hooks.json` (`apply_patch`). Project hooks run
  only once the project `.codex/` layer is trusted, and again after each
  change to the hooks: review and trust them with `/hooks` in Codex.
- It does not see edits made through shell commands (`sed`, `cat > file`).
  Agents must not use the shell to get around it.
- The guard and its configuration (`tools/agent-hooks/`, `.claude/settings.json`,
  `.codex/hooks.json`) change only with the developer's explicit approval,
  even though they are config files.
