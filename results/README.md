# Kept results

Runs that mark a step in the project, versioned on purpose. Scratch runs go
to `runs/`, which is ignored by git.

[`journal.md`](journal.md) tells the path from one kept run to the next: why
each run was made, what it showed and what was decided. Use the
`keep-result` skill to add a run: it creates the folder below and the
journal entry together.

One folder per run (or per group of runs answering one question), named
`YYYY-MM-DD-<short-name>/`, containing:

- the run outputs (`.csv`, `.json`, `.gif`) exactly as the simulator wrote them.
  A CSV over about 5 MB stays in `runs/` (local); the README then says how
  to regenerate it;
- a `README.md` giving the command line, the git commit it ran on
  (`git rev-parse --short HEAD`), the question it answers, and the key
  numbers with their interpretation.

Never edit outputs by hand. To change a result, rerun it.
