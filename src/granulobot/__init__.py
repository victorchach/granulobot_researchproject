"""Granulobot simulator in PyChrono (NSC contacts, exact Coulomb friction).

Run it with `python -m granulobot` (see `__main__.py` and AGENTS.md).
Sub-packages: `model` (what a unit is), `simulation` (how it runs),
`output` (what we get out of it). The modules are imported on demand, so
importing the package does not load PyChrono.
"""
from pathlib import Path

# Repo root (src/granulobot/__init__.py -> root): default outputs go to runs/.
RACINE = Path(__file__).resolve().parents[2]
