@AGENTS.md

# Claude Code specifics

The workflow, the skills and the rules are shared with Codex and live in
`AGENTS.md`. Put shared facts there, not here. This file only covers what is
specific to Claude Code.

## Skills

- The skills live in `.agents/skills/`, where Codex reads them. Claude Code
  sees them through one symlink per skill in `.claude/skills/`. To add a skill,
  create `.agents/skills/<name>/SKILL.md`, then
  `ln -s ../../.agents/skills/<name> .claude/skills/<name>`.
- The independent review of the `feature` skill uses the Agent tool
  (`general-purpose` subagent).

## Guardrails

- `.claude/settings.json` (versioned): safe commands are pre-allowed; commit,
  merge, push, rebase and reset always ask; edits to `references/` and `cad/`
  are denied; AI attribution is disabled; the PreToolUse hook runs
  `tools/agent-hooks/guard-code-edits.sh` on Edit, Write and NotebookEdit.
- Personal preferences (conversation language, ...) go in `CLAUDE.local.md`,
  which is not versioned.

## Memory

Claude's auto-memory is private to Victor's machine. Shared facts, decisions
and project state belong in `AGENTS.md` and `docs/`, so that Hugo and Codex
see them too. Memory only keeps pointers and personal context.

## Long simulations

Probe with `--duration 0.2 --no-gif` to estimate the cost, then run long jobs
in the background with outputs in `runs/`.
