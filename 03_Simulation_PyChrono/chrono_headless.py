"""Import normal du coeur PyChrono sans ses extensions graphiques optionnelles.

Le paquet conda importe automatiquement vsg3d dans son __init__. Un filtre
TEMPORAIRE bloque ces imports avant leur chargement natif (et donc SDL2).
Il ne modifie ni l'installation conda ni les modules binaires. Un simple
'import pychrono.core' ne suffit pas, car Python exécute aussi __init__.
"""
import importlib
import importlib.abc
from pathlib import Path
import sys


class _CoreOnly(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('pychrono.') and fullname not in ('pychrono.core', 'pychrono._core'):
            raise ModuleNotFoundError(f'Extension optionnelle désactivée pour cet import : {fullname}')
        return None


def charger_chrono():
    filtre = _CoreOnly()
    sys.meta_path.insert(0, filtre)
    try:
        core = importlib.import_module('pychrono.core')
    finally:
        sys.meta_path.remove(filtre)
    # L'initialiseur conda ne configure pas ce chemin si fea est désactivé.
    data = Path(core.__file__).resolve().parent / '../../../Library/data'
    if data.is_dir():
        core.SetChronoDataPath(str(data.resolve()) + '/')
    return core


chrono = charger_chrono()

if __name__ == '__main__':
    interdits = [n for n in sys.modules if n.startswith(('pychrono.vsg', 'pychrono._vsg',
                   'pychrono.irrlicht', 'pychrono.sensor'))]
    if interdits:
        raise RuntimeError(f'Extensions graphiques déjà chargées : {interdits}')
    sys_test = chrono.ChSystemNSC()
    print('Coeur PyChrono opérationnel ; aucune extension graphique chargée.', flush=True)
