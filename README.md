# Granulobot simulation

PyChrono simulation of Granulobots, the self-organizing robotic aggregate of
Saintyves, Spenko and Jaeger (*Science Robotics*, 2024). Research project
(PIR) at INSA Lyon, 2026.

- Goal, layout, commands and conventions: [`AGENTS.md`](AGENTS.md)
- Plan: [`docs/roadmap.md`](docs/roadmap.md)
- Modelling assumptions and limitations: [`docs/model.md`](docs/model.md)
- Decisions and their reasons: [`docs/decisions.md`](docs/decisions.md)

## Install

PyChrono is only distributed via conda (`pip install` does not work). On
Apple Silicon, use [Miniforge](https://github.com/conda-forge/miniforge).

```bash
make setup            # or: conda create -n chrono -c projectchrono -c conda-forge python=3.11 pychrono matplotlib pillow
conda activate chrono
make check-env        # or: python 03_Simulation_PyChrono/chrono_headless.py
```

## Use

```bash
make test                                   # unit tests of the physics laws
make validate                               # PyChrono dynamics checks
make sim NAME=probe ARGS="--duree 0.2 --sans-gif"
make sim NAME=v123 ARGS="--tensions 1 2 3"  # independent voltages for A, B, C
make diag CSV=runs/probe.csv                # attachment diagnostics of a run
```

The equivalent raw commands (without `make`) are listed in
`AGENTS.md`. Each run writes a CSV of measurements (200 Hz), a JSON file with
the parameters, assumptions and summary, and a GIF in physical time.

## Tested versions

- PyChrono 10.0.0 with Python 3.11, on macOS (Apple Silicon) and Ubuntu.
- Class names changed between PyChrono 8 and 9 (`ChVectorD` became
  `ChVector3d`). This code targets version 10.
- `pychrono.fsi`, `pychrono.sensor` and `pychrono.pardisomkl` are not
  available on Apple Silicon. The conda build cannot load the graphics
  extensions (vsg3d/SDL2), so simulations run headless and are rendered with
  matplotlib.
