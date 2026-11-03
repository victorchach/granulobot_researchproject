# Kept results

Runs worth keeping, versioned on purpose. Scratch runs go to `runs/`, which is
ignored by git.

One folder per run, named `YYYY-MM-DD-<short-name>/`, containing:

- the run outputs (`.csv`, `.json`, `.gif`) exactly as the simulator wrote them;
- a `README.md` giving the command line, the git commit it ran on
  (`git rev-parse --short HEAD`), the question it answers, and the key
  numbers with their interpretation.

Never edit outputs by hand. To change a result, rerun it.
