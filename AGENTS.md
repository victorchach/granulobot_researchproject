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
| `tools/agent-hooks/` | The edit guard shared by the Claude Code and Codex hooks. |
| `.agents/skills/` | Shared agent skills (`feature`, `run-sim`, `sync`, `humanizer`). Codex reads them here. |
| `.claude/` | Claude Code settings; `.claude/skills/<name>` are symlinks to `.agents/skills/<name>`. |
| `.codex/` | Codex project hooks (`hooks.json`). |

## Workflow (both developers, both agents)

Victor (Claude Code) and Hugo (Codex) follow the same workflow, through the
skills in `.agents/skills/`:

| Skill | Use it for |
| --- | --- |
| `feature` | Any code change (`*.py`, `*.ipynb`, `Makefile`), however small, from spec to merge |
| `run-sim` | Running a scenario and analysing its outputs, without changing code |
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

`make test` only covers `test_granulobot_physics.py`. `test_3_granulobots.py`
matches `test_*.py` but is the simulator, not a test file (a rename is
planned).

The 2-unit bench (one facing pair, active A to free B):
`make sim NAME=bench_2 ARGS="--robots 2 --tensions 0.3 0 0"`.

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
- `prototype_hugo.json`: the prototype dimensions Hugo provided, plus what is
  still to measure.

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
