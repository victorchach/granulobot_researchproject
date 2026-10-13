#granulobot_researchproject

## Prérequis

- [conda](https://docs.conda.io/) ou [Miniforge](https://github.com/conda-forge/miniforge) (recommandé sur Mac Apple Silicon)
- PyChrono n'est distribué que via conda : `pip install` ne fonctionne pas.

## Installation

Créer un environnement dédié et y installer PyChrono :

```bash
conda create -n chrono python=3.11
conda activate chrono
conda install -c projectchrono -c conda-forge pychrono
```

Vérifier que l'installation fonctionne :

```bash
python -c "import pychrono as chrono; print(chrono.ChVector3d(1, 2, 3))"
```

## Utilisation

À chaque nouvelle session de terminal, activer l'environnement avant de lancer le projet :

```bash
conda activate chrono
python main.py
```

## Versions testées

- PyChrono 10.0.0
- Python 3.11
- macOS (Apple Silicon, M4)

> Remarque : les noms de classes ont changé entre PyChrono 8 et 9 (par exemple `ChVectorD` est devenu `ChVector3d`). Ce projet est écrit pour la version 10 et peut ne pas fonctionner avec une version plus ancienne.

## Limitations sur Mac Apple Silicon

Les modules `pychrono.fsi`, `pychrono.sensor` et `pychrono.pardisomkl` ne sont pas disponibles sur Mac Apple Silicon.