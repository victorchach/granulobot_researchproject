---
name: keep-result
description: Use to move a run that matters for the project from runs/ (local scratch) to results/ (versioned), with its analysis README and a new entry in results/journal.md. Examples of requests: "keep this result", "on valide ce run", "put this run in results", "add this experiment to the journal", "garde le run de 60 s". Not for running a simulation (use run-sim first) and not for code changes (use feature).
---

# Keep a result and extend the journal

`results/` holds the runs that mark a step in the project's reasoning.
`results/journal.md` tells that reasoning in order: each entry says why the
run was made, given what the previous entry taught, what it showed, and what
was decided next. A reader who goes through the journal top to bottom should
follow the whole path (for example: triangle and its limits, then a short
6-unit ring, then a long one to check it holds).

Only keep a run when the developer asks. "The developer" is the person you
work with; talk to them in their language. Everything written into the repo
is in English.

## 1. Check the run

- The outputs exist in `runs/` (`.json`, plus `.csv` and `.gif` when made).
- Find the code the run used: `git log`, the file times and the run log.
  If it ran on an uncommitted working tree, say which commit later recorded
  that code unchanged. If you cannot tell, say so in the README.
- Read `results/journal.md` to find the entry this run follows from.

## 2. Create the folder

- Name it `results/YYYY-MM-DD-<short-name>/`, with the run's date. Several
  runs that answer one question (a short and a long run, two time steps) can
  share a folder.
- Copy the outputs exactly as the simulator wrote them. Never edit them; to
  change a result, rerun it.
  - `.json` and `.gif`: always.
  - `.csv`: only under about 5 MB. A larger CSV stays in `runs/`, and the
    README gives the command that regenerates it and its rough cost.
  - No `.log` files.
- Never overwrite an existing folder in `results/`.

## 3. Write the folder's README.md

The README is the analysis of the run. Follow the existing ones
(`results/2026-10-14-triangle-3-units/README.md`,
`results/2026-11-24-ring6-alternating/README.md`):

- **Title**: what was run and the date.
- **How it was made**: exact command (`make sim ...`), the parameter file,
  the commit, which files are versioned and which stay local.
- **Question**: what the run was meant to answer.
- **Key numbers**: from the JSON summary and the CSV, never from the GIF
  alone, with units.
- **Interpretation**: what the numbers mean physically.
- **Caveats**: time-step convergence, estimated parameters, duration,
  idealised start, anything not tested.

Use the `humanizer` skill on the prose.

## 4. Add the journal entry

Append one entry per run (two runs in one folder can get two entries) at the
end of `results/journal.md`, in this shape:

```markdown
## N. YYYY-MM-DD: <title>

Folder: [`YYYY-MM-DD-<short-name>/`](YYYY-MM-DD-<short-name>/)

- **Why**: what the previous entry left open, and what this run tests.
- **What we saw**: two to four key numbers, each with its meaning.
- **Limits**: what this run does not show.
- **Next**: the decision taken and the step it leads to.
```

- Number the entries in order. Link back to the previous entry in "Why"
  when it helps ("after entry 2, ...").
- Keep the entry short: the details live in the folder's README.
- Be exact about what is established. Write "holds for 60 s at
  dt = 1e-4 s", not "validated", unless the roadmap criterion is fully met.
- A run that matters but is not kept (a local probe, a convergence check)
  can be mentioned inside an entry, with its path in `runs/` and the fact
  that it is local only.

## 5. Record decisions and finish

- If the run leads to a decision (a change of plan, a model choice), add it
  to `docs/decisions.md` and link the folder.
- If it changes the roadmap status, update `docs/roadmap.md`.
- Show the developer the new folder, the README and the journal entry.
  Suggest a commit (English, imperative mood, no attribution); commit only
  when asked. The pre-commit hook allows CSV and GIF files inside
  `results/` only.

## Final checks

- [ ] The folder is named `YYYY-MM-DD-<short-name>` and nothing in it was edited by hand
- [ ] No CSV over about 5 MB is versioned, and the README says how to get it back
- [ ] The README has the command, the commit, the question, key numbers, interpretation and caveats
- [ ] `results/journal.md` has a new entry that follows from the previous one
- [ ] Nothing committed or pushed without the developer's approval
