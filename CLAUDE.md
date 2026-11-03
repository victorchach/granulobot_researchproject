@AGENTS.md

# Claude Code specifics

## Workflow

- Any change to code (`*.py`, `Makefile`) goes through the `feature` skill:
  spec, branch `feature/NNN-name`, tests, review by a separate agent, then a
  local merge after approval. A PreToolUse hook
  (`.claude/hooks/guard-code-edits.sh`) blocks code edits outside such a
  branch.
- Docs, specs, skills and config can be edited directly, but must stay
  consistent with `AGENTS.md`.
- Never commit, merge or push unless asked. Suggest a commit when a coherent
  step is done.
- Hugo works with Codex and pushes straight to `main`; he does not follow the
  spec workflow. After every pull of his work, run the `sync-hugo` skill.
  `AGENTS.md` is the file both agents read: put shared facts there, not here.

## Skills (.claude/skills/)

| Skill | Use it for |
| --- | --- |
| `feature` | Any code change, from spec to merge |
| `run-sim` | Running a scenario and analysing its outputs |
| `sync-hugo` | Pulling Hugo's work and updating docs and memory to match |
| `humanizer` | Any prose meant for people (reports, README, docs, messages) |

## Guardrails

- `.claude/settings.json` (versioned): safe commands are pre-allowed; commit,
  merge, push, rebase and reset always ask; edits to `01_*` and `04_*` are
  denied; AI attribution is disabled.
- Git hooks (`tools/git-hooks/`, installed with `make hooks`): `commit-msg`
  rejects Co-Authored-By trailers and "Generated with" lines; `pre-commit`
  rejects derived outputs outside `results/` and runs `make test` when code is
  staged. Reinstall them after every fresh clone.

## Long simulations

Probe with `--duree 0.2 --sans-gif` to estimate the cost, then run long jobs
in the background with outputs in `runs/`.
