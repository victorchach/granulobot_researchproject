---
name: run-sim
description: Use to run a simulation scenario and analyse its outputs without changing code. Examples of requests: "run the triangle at 1 V", "what happens without magnetism?", "run test_3 for 10 s", "check whether the ring holds", "compare dt 1e-5 and 5e-6", "regenerate the GIF of this run", "keep this result". If the scenario needs code changes (new geometry, new controller, new default), use the feature skill instead.
---

# Run and analyse a simulation

## 1. Prepare

- `make check-env` if the environment has not been used in this session.
- Translate the request into simulator flags (list in `AGENTS.md`). Use
  `--parametres file.json` for several overrides; keep that file in `runs/`
  unless the result will be kept.
- Pick a short, descriptive `NAME`. Outputs go to `runs/NAME.{csv,json,gif}`.
  Never write into `03_Simulation_PyChrono/` or overwrite an existing result.

## 2. Probe, then run

1. Probe: `make sim NAME=NAME-probe ARGS="<flags> --duree 0.2 --sans-gif"`, and
   time it to extrapolate the cost of the full run.
2. If the full run takes more than about 2 minutes, run it in the background
   and say how long it should take. Add `--sans-gif` for very long runs and
   build the GIF afterwards with `make replay` if it is needed.

## 3. Analyse

- `make diag CSV=runs/NAME.csv` gives the attachment diagnostics. Also read
  the `bilan` in `runs/NAME.json`: maximum overlap, maximum magnet force,
  final displacements.
- For directional questions, compute the signs of
  `<X>_omega_actif_relative_rad_s` per unit from the CSV. For the ring, check
  that the directions alternate and that the sum of rotor speeds stays close
  to 0.
- Look at 3 to 5 frames of the GIF (extract them with PIL into the
  scratchpad) to spot anything the numbers miss.
- Check plausibility: overlaps must stay at the µm level, with no NaN. If a
  result depends on numerics, rerun with `--dt` halved before concluding
  (convergence is not established, see `docs/model.md`).

## 4. Report (in French)

- Give the exact command, the simulated duration and the wall-clock time.
- Give the key numbers and what they mean physically.
- Give caveats: estimated parameters, convergence, the 3 mm detachment
  threshold is only an indicator.
- Suggest a next step if it is useful.

## 5. Keep a result (only when asked)

Copy the outputs to `results/YYYY-MM-DD-NAME/` and add the `README.md`
described in `results/README.md` (command, commit, question, key numbers).
Suggest a commit.

## Final checks

- [ ] Nothing written outside `runs/` (or `results/` when keeping a run)
- [ ] The numbers reported come from the CSV/JSON, not from the GIF alone
- [ ] Numerical sensitivity was checked before any strong conclusion
