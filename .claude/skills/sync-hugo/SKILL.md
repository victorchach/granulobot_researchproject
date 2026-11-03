---
name: sync-hugo
description: Use when Victor pulls or wants to pull Hugo's work, or when commits by someone else appear on main. Examples of requests: "Hugo pushed", "pull Hugo's changes", "I just pulled", "sync with Hugo", "what did Hugo change?". Also run it before merging a feature branch if origin/main moved. Hugo works with Codex on Ubuntu, pushes straight to main and does not follow the spec workflow.
---

# Sync with Hugo's work

## 1. Look before pulling

```bash
git status --short          # must be clean; otherwise ask Victor (commit or stash?)
git fetch origin
git log --oneline HEAD..origin/main
git diff --stat HEAD...origin/main
```

If Victor already pulled, use `ORIG_HEAD..HEAD`, or the merge commit's first
parent, as the range instead.

## 2. Pull

- From `main`: `git pull --no-rebase origin main`. This matches the project's
  history; never rebase or force anything.
- If a feature branch is in progress: update `main` first, then ask Victor
  whether to merge `main` into the branch now.
- For conflicts, show them to Victor and propose a resolution. Never pick a
  side silently.

## 3. Read Hugo's changes

Read the full diff, not only the stat. For each change, ask:
- Does it add, rename or remove a script, a CLI flag, an output, a command or
  a dependency? If so, update `AGENTS.md` (commands, layout, architecture),
  and the `Makefile` if a target breaks. The `Makefile` is code: if it needs
  changes, go through the feature skill.
- Does it change a physical default or a modelling assumption? If so, record
  it in `docs/decisions.md` (with "Hugo" as the source) and in
  `docs/model.md`.
- Did Hugo, or his Codex, edit `AGENTS.md`? Keep his edits. Reconcile them
  with `CLAUDE.md` and the skills, and flag any contradiction to Victor.
- Does it touch the code of an open spec (`specs/README.md`)? Note the
  overlap in that spec and tell Victor.
- Did he commit derived outputs (CSV/GIF/JSON outside `results/`)? Flag them;
  don't delete them without asking.

## 4. Check

- `make test`, plus `make validate` if the simulator or the contacts changed.
- Report failures with their output. Don't fix Hugo's code outside the
  feature skill.

## 5. Update memory and report

- Update the memory files that are now out of date (for example, what Hugo
  is working on).
- Report to Victor, in French: a summary of Hugo's commits, the docs you
  updated, the test results and the points that need a decision.
- Suggest a commit for the doc updates; commit only when asked.

## Final checks

- [ ] `AGENTS.md` matches the code after the pull
- [ ] Physical changes are recorded in `docs/`
- [ ] Tests were run and their results reported
- [ ] Nothing committed or pushed without Victor's approval
