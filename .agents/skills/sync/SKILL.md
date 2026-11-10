---
name: sync
description: Use when the developer pulls or wants to pull the teammate's work, or when commits by someone else appear on origin/main. Examples of requests: "Hugo pushed", "Victor pushed", "pull the latest changes", "I just pulled", "sync with main", "what did my teammate change?". Also run it before merging a feature branch if origin/main moved. Works in both directions (Victor with Claude Code, Hugo with Codex).
---

# Sync with the teammate's work

Two developers work on this repo: Victor (Claude Code, macOS) and Hugo
(Codex, Ubuntu). Both follow the `feature` workflow and push merged work to
`main`. "The developer" is the person you work with; talk to them in their
language (French for both).

## 1. Look before pulling

```bash
git status --short          # must be clean; otherwise ask the developer (commit or stash?)
git fetch origin
git log --oneline HEAD..origin/main
git diff --stat HEAD...origin/main
```

If the developer already pulled, use `ORIG_HEAD..HEAD`, or the merge commit's
first parent, as the range instead.

## 2. Pull

- From `main`: `git pull --no-rebase origin main`. This matches the project's
  history; never rebase or force anything.
- If a feature branch is in progress: update `main` first, then ask the
  developer whether to merge `main` into the branch now.
- For conflicts, show them to the developer and propose a resolution. Never
  pick a side silently. On a `specs/README.md` conflict, keep both rows.
  The edit guard lets you edit code files while they are in conflict, even
  on `main`; resolve only the conflict, then run `make test` before
  concluding the merge.

## 3. Read the teammate's changes

Read the full diff, not only the stat. For each change, ask:
- Did the code change go through the workflow? Each code change should come
  with a spec in `specs/` marked `merged`. If code changed without a spec,
  flag it to the developer and document it as below.
- Does it add, rename or remove a script, a CLI flag, an output, a command or
  a dependency? If so, check that `AGENTS.md` (commands, layout,
  architecture) was updated; update it if not. The `Makefile` is code: if it
  needs changes, go through the `feature` skill.
- Does it change a physical default or a modelling assumption? Check that it
  is recorded in `docs/decisions.md` (with its source) and `docs/model.md`;
  record it if not.
- Was `AGENTS.md` or a skill edited? Keep those edits. Reconcile them with
  the agent-specific files (`CLAUDE.md`, `.claude/`, `.codex/`) and flag any
  contradiction to the developer.
- Does it touch the code of a spec still open on your side? Note the overlap
  in that spec and tell the developer.
- Does a newly merged spec use the same NNN as a spec still open on your
  side? Yours will be renumbered when it is merged (see the `feature` skill,
  step 5). Tell the developer.
- Were derived outputs committed (CSV/GIF/run JSON outside `results/`)? Flag
  them; don't delete them without asking.

## 4. Check

- `make test`, plus `make validate` if the simulator or the contacts changed.
- Report failures with their output. Don't fix the teammate's code outside
  the `feature` skill.

## 5. Update notes and report

- If your agent keeps a memory outside the repo, update what is now out of
  date (for example, what the teammate is working on). Shared facts go into
  `AGENTS.md` or `docs/`, not into private memory.
- Report to the developer: a summary of the teammate's commits, the docs you
  updated, the test results and the points that need a decision.
- Suggest a commit for the doc updates; commit only when asked.

## Final checks

- [ ] `AGENTS.md` matches the code after the pull
- [ ] Physical changes are recorded in `docs/`
- [ ] Tests were run and their results reported
- [ ] Nothing committed or pushed without the developer's approval
