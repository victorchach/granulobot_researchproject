# Decisions

Newest first. Each entry gives the decision and the reason for it.

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
  it for now.

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
