# Granulobot simulation

PyChrono multicorps simulator of magnetically coupled Granulobots. The current
six-unit reference starts in a regular hexagon on a horizontal support and uses
alternating motor voltage biases. Physical calibration and numerical convergence
remain work in progress; see [model decisions](docs/decisions.md).

## Environment

Use the conda environment `chrono` with PyChrono 10, matplotlib and Pillow.
PyChrono must be imported through `chrono_loader.py` to avoid loading the
optional graphics extensions. Commands below run from this project directory.

```powershell
conda activate chrono
python 03_Simulation_PyChrono/chrono_loader.py
```

## Source files

All Python modules are in `03_Simulation_PyChrono/`:

| File | Purpose |
| --- | --- |
| `simulate_granulobots.py` | Main simulator and GIF rendering; supports 2, 3 or 6 units |
| `granulobot_physics.py` | Parameters, motor, dipole and effective rim-friction laws |
| `magnetic_cylinders.py` | Finite-cylinder magnetic energy and force |
| `chrono_loader.py` | Load the PyChrono core without graphics extensions |
| `analyse_simulation.py` | Analyse recorded rotations, displacement and magnetic-pair distances |
| `test_granulobot_physics.py` | Unit tests of physical laws, including effective friction |

Parameter inputs are kept separately from generated results:

- `reference_alternee.json`: six-unit reference with alternating biases;
- `perturbation_1deg.json`: same biases, with a +1 degree initial offset of A's active rotor;
- `prototype_hugo.json`: prototype dimensions and remaining measurement questions;
- `parametres/*.parametres.json`: preserved historical triangle parameter inputs,
  moved out of the old generated `validation/` directory without content changes.
  These are partial overrides: use `--robots 3` and review their friction settings
  before comparing them with the current model.

`docs/decisions.md` records model assumptions and exploratory parameters.
`01_Sujet_et_rapports/` and `04_Design_STL/` are read-only reference material.
`.git/`, `.gitignore` and `.vscode/` support version control and the development
workspace; they are not simulation outputs.

## Run a simulation

Run a short probe first; the nominal timestep is `1e-5 s` and longer runs are
expensive. No interactive graphics window opens.

```powershell
python 03_Simulation_PyChrono/simulate_granulobots.py --duree 0.01 --sans-gif --sortie runs/probe
python 03_Simulation_PyChrono/simulate_granulobots.py --duree 2 --dt 1e-4 --parametres 03_Simulation_PyChrono/reference_alternee.json --sortie runs/reference_alternee
python 03_Simulation_PyChrono/simulate_granulobots.py --duree 2 --dt 1e-4 --parametres 03_Simulation_PyChrono/perturbation_1deg.json --sortie runs/perturbation_alternee_1deg
python 03_Simulation_PyChrono/simulate_granulobots.py --robots 2 --tensions 0.3 0 --duree 0.01 --sans-gif --sortie runs/deux_granulobots
```

The `1e-4` commands are exploratory; compare against `1e-5` before interpreting
quantitative results. Voltages ramp up over 0.5 simulated seconds. A finer
integration timestep increases calculation time; it does not prescribe a slower
robot speed.

Each run writes `<name>.csv` (measurements), `<name>.json` (parameters,
assumptions and summary) and optionally `<name>.gif` (25 fps in physical time).
Without `--sortie`, the simulator writes to `runs/simulation` at the project root.
Use `--robots 2` for the two-unit bench; no separate wrapper is needed.
Existing outputs with the same name are replaced. Keep parameter inputs outside
`runs/`, which is ignored by git.

The five recent experiments have been retained in `runs/`. Their JSON metadata
is the source for their actual timestep and control settings: notably,
`hexagone_dt_1e4` used `dt=1e-3`, uniform positive voltages and the old uniform
rim-friction model. To reproduce that old model, explicitly set
`frottements_differencies` to `false`; older JSON files do not contain that field.

```powershell
python 03_Simulation_PyChrono/analyse_simulation.py runs/reference_alternee.csv
python 03_Simulation_PyChrono/simulate_granulobots.py --rejouer runs/reference_alternee.csv
```

## Verify the model

```powershell
python -m unittest discover -s 03_Simulation_PyChrono -p test_granulobot_physics.py
```

The separate Chrono dynamic-check script was removed at Hugo's request.
The remaining unit tests check physical laws, not the full simulated dynamics.

Passing these tests does not establish experimental calibration, long-run
stability or timestep convergence. The rim-tooth model is an effective friction
approximation; the tentative 21-tooth count does not create explicit gear teeth.
