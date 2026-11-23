# Specs

One folder per code change: `specs/NNN-<name>/spec.md`, worked on in branch
`feature/NNN-<name>`. The procedure is in `.agents/skills/feature/SKILL.md`.
Ideas not yet scheduled go to `IDEES.md`.

Two people write specs in parallel. Pick NNN as the next free number here
right after pulling `main`. If both pick the same number, the one who merges
second renumbers their spec (folder, title, row below and branch). On a merge
conflict in this table, keep both rows.

Status values: `draft` (waiting for approval), `approved` (being implemented),
`review`, `merged`, `dropped`.

| NNN | Name | Status | Summary |
| --- | --- | --- | --- |
| 001 | remove-dead-code | merged | Delete `unite.py`, `test_3_granulobots_simple.py` and `test_2_granulobots.py` |
| 002 | src-layout | merged | Move the code to `src/granulobot/`, `tests/`, `scripts/`, `configs/`; rename `01_`/`04_` to `references/`, `cad/` |
| 003 | split-simulator | merged | Split `simulator.py` into `model/`, `simulation/`, `output/`; move the pure laws out of `parameters.py` |
| 004 | translate-internals | merged | Translate identifiers, comments and messages to English; outputs unchanged |
| 005 | translate-interface | merged | Translate parameters, CLI flags, CSV/JSON, GIF, campaign to English; old run files no longer readable |
