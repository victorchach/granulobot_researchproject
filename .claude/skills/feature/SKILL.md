---
name: feature
description: Use for ANY change to the simulation code (*.py, Makefile), however small. That covers new physics, new scenarios, bug fixes, refactors, renames and deleting scripts. Examples of requests: "generalize the simulator to 6 robots", "add the eq. 7 controller", "fix the overlap bug", "remove unite.py", "translate the code to English", "change the default friction". Not for docs, specs or config edits, and not for just running a simulation (use run-sim).
---

# Feature workflow

Every code change follows these steps in order. A hook blocks code edits
unless the current branch is `feature/NNN-name` and `specs/NNN-name/spec.md`
exists.

## 0. Investigate first

- Read the code concerned and grep for every caller. Reproduce the problem or
  measure the current behaviour (`make test`, a short `make sim`).
- Change code only when there is a real problem or a real need. If the
  investigation shows nothing is wrong, say so and stop.
- Check `specs/README.md` for a related spec and `specs/IDEES.md` for an idea
  this change already covers.

## 1. Branch and spec

1. Make sure the tree is clean and `main` is up to date. If Hugo pushed
   recently, run the `sync-hugo` skill first.
2. NNN is the next free 3-digit number in `specs/README.md`; the name is
   kebab-case.
3. `git switch -c feature/NNN-name main`
4. Write `specs/NNN-name/spec.md` from `spec-template.md` (in this folder).
   Fill in the need, the expected behaviour, the files concerned, the planned
   tests, what is out of scope, and the physical assumptions with their
   sources.
5. Add a row to `specs/README.md` with status `draft`. If the change comes
   from an idea in `specs/IDEES.md`, remove that idea.
6. **Stop.** Show Victor the spec, in French, summarized, with a link to the
   file. Do not write code before he explicitly approves it. Then set the
   status to `approved`.

## 2. Implement

- Follow the spec. If it turns out to be wrong or incomplete, update the spec
  and tell Victor before going further.
- Match the surrounding code: its naming (French identifiers stay in existing
  files until the translation spec), comment density and idioms. Anything
  new written into the repo is in English.
- Never change a physical default without a source. Record such a change in
  `docs/decisions.md`.
- Add unit tests to `03_Simulation_PyChrono/test_granulobot_physics.py` for
  pure laws, or to `validation_modele.py` for PyChrono dynamics.
- `make test` must pass. Also run `make validate` if the simulator or the
  contacts changed. Run a short `make sim` when behaviour changes.
- Update `AGENTS.md` (commands, layout, architecture) and `docs/` in the same
  branch if the change affects them.

## 3. Independent review

Launch a separate agent (Agent tool, `general-purpose`) with:
- the spec path and `git diff main...HEAD`;
- the instruction to check correctness, adherence to the spec, the physics
  and units, the test coverage and the repo rules in `AGENTS.md`;
- the instruction to report concrete findings only, each with a failure
  scenario.

Verify each finding yourself. Fix the confirmed ones, rerun the tests, and
record the outcome in the spec's "Review" section.

## 4. Show the result

Report to Victor, in French:
- what changed, file by file;
- the test output;
- the review findings and what was done about them;
- anything left open.

Set the spec status to `review`. Suggest a commit; commit only when he asks
(English message, imperative mood, no attribution).

## 5. Merge (only after explicit approval)

```bash
git switch main
git merge --no-ff feature/NNN-name
make test
```

Set the status to `merged` in `specs/README.md`. Do not push unless asked.
Delete the branch only if Victor agrees. Move any idea that came up along the
way into `specs/IDEES.md`.

## Final checks

- [ ] The spec is approved and matches what was built
- [ ] `make test` passes (and `make validate` if dynamics changed)
- [ ] The review was done and its findings handled
- [ ] `AGENTS.md`, `docs/` and `specs/README.md` are up to date
- [ ] No derived outputs are staged outside `results/`
