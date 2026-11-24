# Decisions

Newest first. Each entry gives the decision and the reason for it.

## 2026-11-24: N-unit ring (spec 006)

- **Any number of units from 2 to 26**, ported from the 6-unit work on Hugo's
  branch `granulobot-research` (not merged: it starts from the pre-reorg
  layout) and generalized beyond 6. N >= 3 is a closed ring on a regular
  polygon with the triangle's neighbour spacing; N = 2 stays the facing pair.
  The cap of 26 only comes from the names A..Z (Victor's choice: enough for
  now; going further is in `specs/IDEES.md`).
- **The triangle is unchanged**, up to rounding: the polygon formula gives its
  corners within 1.4e-17 m. That rounding is enough to move a default 0.2 s
  run by 5e-8 m and 1.7e-6 rad through the iterative solver; with the old
  coordinates injected, the CSV matches `main` bit for bit.
- **No 6-value defaults.** The set points keep their 3-value defaults; a ring
  of N needs its set points from `--voltages` or a parameter file. Only the
  tuple read by the current motor mode must have N values, so the 2-unit
  inputs with an unused C value keep working.
- **Alternating biases are a config, not a default**:
  `configs/ring6_alternating.json` sets u_i = (-1)^i * 3.25 V, A positive
  (paper eq. 8; 3.25 V is the default target voltage, as in Hugo's
  `reference_alternee.json`). Friction stays uniform; Hugo's rim friction
  model is planned as spec 007.

## 2026-11-24: English interface (spec 005)

- **The run interface is in English**: `Parameters` and its fields, CLI
  flags (`--duration`, `--no-gif`, `--params`, ...), CSV columns, JSON keys,
  GIF text, campaign scenarios and `configs/prototype_hugo.json`. The full
  old-to-new tables are in `specs/005-translate-interface/spec.md`; they are
  also the dictionary for porting Hugo's prototype.
- **Old run files are not converted.** The 2026-10-14 triangle in `results/`
  stays in its original format with a note (Victor's choice): rerunning it
  gives the same values under the new names.
- **Campaign scenario names say the voltage plainly**: the old `10V` meant
  1.0 V and `03V` meant 0.3 V (French decimal comma); they are now `1V` and
  `0p3V`.

## 2026-11-23: translate the code to English (specs 004 and 005)

- **Everything is translated, in two steps.** Spec 004 translates the
  internals (names, comments, docstrings, console messages) with no change to
  any output file, so it is checked byte for byte. Spec 005 translates the
  interface: `Parametres` fields, CLI flags, CSV columns, JSON keys, GIF text,
  campaign names and `configs/prototype_hugo.json`.
- **No compatibility with old run files** (Victor's decision): after spec 005,
  `make diag` and `make replay` will not read CSV/JSON files written before
  it. Nothing is kept that a rerun, or Hugo's next push, cannot give back.
- **One glossary for both specs** (`specs/004-translate-internals/spec.md`),
  so a French word always becomes the same English word (corps: body,
  aimant: magnet, couple: torque, tension: voltage, bilan: summary, ...).

## 2026-11-23: split the simulator (spec 003)

- **`simulator.py` (670 lines) was split into `model/`, `simulation/` and
  `output/`**, the target drawn with Victor. `model/` says what a Granulobot
  is (unit, motor, magnets, contacts), `simulation/` how a run works (world,
  loop, recording), `output/` what comes out (analysis, GIF). The 6-unit ring
  and the controllers now have obvious places: `simulation/world.py` and a
  future `model/controller.py`.
- **A law and the code that applies it live together**: `model/motor.py`
  holds the DC motor law and `appliquer_moteur`; `model/magnets.py` holds the
  field models and `appliquer_magnetisme`. Victor preferred this to keeping
  PyChrono-free laws apart, since everything about the motor is in one file.
  The cost is that `make test` now loads PyChrono (about 30 ms).
- Code was moved, not rewritten: all seven reference runs (triangle, 2-unit
  bench, ideal link, speed mode, dipoles, no ground, with GIF) give
  byte-identical CSV, JSON and GIF files.

## 2026-11-23: src layout (spec 002)

- **The code moved to a "src layout"**: the package `src/granulobot/`, with
  `tests/`, `scripts/` and `configs/` beside it. Victor chose it over a flat
  `src/` because a package can later hold sub-packages (`model/`,
  `simulation/`, `output/`, spec 003) and runs as `python -m granulobot`.
  The file names now say what the files do: `test_3_granulobots.py` became
  `simulator.py`, `granulobot_physics.py` became `parameters.py`, and so on
  (full table in `specs/002-src-layout/spec.md`).
- **`PYTHONPATH=src` instead of `pip install -e .`**: the Makefile exports it,
  so there is no extra setup step for either developer.
- **Default outputs go to `runs/`**, never into the code folders.
- **`01_Sujet_et_rapports/` became `references/` and `04_Design_STL/` became
  `cad/`**: top-level names say what the folders hold, without numbers. Both
  stay read only; the deny rules in `.claude/settings.json` follow them
  (approved by Victor).
- Entries below keep the old paths, since they describe the repo as it was.

## 2026-11-23: reorganise the repo before the 6-unit ring

- **The repo is reorganised now, in small specs, without waiting for Hugo.**
  Hugo has a 6-unit version on his machine, built as copies of
  `test_3_granulobots.py`, and cannot push it yet. When he can, he pushes it
  as is to a branch of his own (for example `hugo/6-units-prototype`), never
  to `main`. That branch is never merged: its diff against its base commit
  shows what he changed, and the parts worth keeping (hexagon geometry,
  initial state, voltages, tuned values) are ported by hand into the new
  layout, through the N-unit spec.
- **Dead scripts removed (spec 001)**: `unite.py` (first single-disc test with
  placeholder values), `test_3_granulobots_simple.py` (old spring model) and
  `test_2_granulobots.py` (a wrapper the CLI already covers with
  `--robots 2 --tensions 0.3 0 0`). Nothing used them. They are still in
  history: `git show 8233746:03_Simulation_PyChrono/<file>`.
- **The 2026-10-14 triangle run is kept** in
  `results/2026-10-14-triangle-3-units/`. It is the run behind the
  "6 units instead of 3" decision below.

## 2026-11-10: one workflow for both developers

Decided by Victor and Hugo on 2026-11-03, set up on 2026-11-10.

- **Hugo and Codex follow the same `feature` workflow as Victor and Claude
  Code**: spec, branch, approval, tests, independent review, local merge.
  Until now Hugo pushed straight to `main` and Victor documented his changes
  after each pull. That worked while one person wrote most of the simulator.
  The next phase (N-unit simulator, eq. 7 and eq. 2 controllers) has both of
  them editing the same files. Without a shared workflow, docs drift between
  syncs, physics changes lose their written reason, and conflicts show up
  late. Accepted costs: Hugo goes a little slower, and Codex compliance is not
  guaranteed (an edit through the shell gets past the hook).
- **The skills moved to `.agents/skills/`**, the path Codex reads. Claude
  Code sees them through one symlink per skill in `.claude/skills/`; both
  tools document symlinked skill folders. The skills no longer name a person
  or a tool: they address "the developer", in their language.
- **`sync-hugo` became `sync`** and works in both directions.
- **One edit guard for both agents** (`tools/agent-hooks/`), called by
  `.claude/settings.json` and `.codex/hooks.json`. It reads Claude's
  `file_path` and the file names inside a Codex `apply_patch`.
- **Spec numbers**: pick after pulling; on a collision, the one who merges
  second renumbers.

## 2026-11-03: repository organisation

- **Repo language is English**, and the README and docs were translated.
  French identifiers, comments and CSV column names stay in the code until a
  dedicated spec translates them. Renaming now would break the old CSV/JSON
  files and conflict with Hugo's ongoing work.
- **Derived outputs are no longer versioned.** The old campaign outputs
  (`03_Simulation_PyChrono/validation/`, `essais_plan/`, `engrenages.gif`,
  root `unite.gif` and `video.mp4`) were removed from the tree, along with
  `BRIEF_CLAUDE.md`. Its still-valid content moved into `AGENTS.md`; its
  Windows paths and mixed dimensions were out of date. Everything is still
  in git history: `git checkout b332380 -- <path>`. Runs worth keeping now go
  into `results/`.
- **`AGENTS.md` is the shared instruction file** for Codex (Hugo) and Claude
  Code (Victor). `CLAUDE.md` imports it, so the two agents never read
  contradictory rules.
- **Code changes follow the spec workflow** (`specs/`). Hugo does not follow
  it for now (superseded on 2026-11-10, see above).

## Late October 2026: simulation direction (team meeting)

- **6 units instead of 3.** In the synchronized state, neighbours turn in
  opposite directions. On a closed ring this needs an even number of units.
  With 3 units the ring is frustrated: in `test_3_granulobots` all three
  bodies drifted in the same direction. A hexagon is the smallest even ring in
  which non-neighbours do not touch.
- **The liquid state comes first** (open loop, G = 0), because it needs no new
  controller. Eq. 7 is needed for step 2, and eq. 2 (G, α) for the
  self-oscillating state.
- **"Direction" means the rotor's direction**, measured relative to the body,
  as the onboard encoder sees it.
- **Horizontal plane on a slippery support** for now.
- **Target dimensions: the paper's**, applied later. The current defaults are
  Hugo's prototype dimensions (R = 35 mm, H = 50 mm).
- **Magnetic vs steric friction.** Coulomb friction with the large magnetic
  normal force already makes magnetic contacts the stronger ones, so no extra
  coefficient is needed for now. Steric contacts must be able to slip when
  locomotion gets blocked.
- **Step 1 validation length: 2 to 5 min of simulated time**, standing in for
  "forever".
- **Computation time is not a priority** until the physics works.
