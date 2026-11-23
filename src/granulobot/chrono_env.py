"""Normal import of the PyChrono core, without its optional graphics extensions.

The conda package imports vsg3d automatically in its __init__. A TEMPORARY
filter blocks these imports before their native code loads (and so SDL2).
It changes neither the conda install nor the binary modules. A plain
'import pychrono.core' is not enough, because Python also runs __init__.
"""
import importlib
import importlib.abc
import math
from pathlib import Path
import sys


class _CoreOnly(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('pychrono.') and fullname not in ('pychrono.core', 'pychrono._core'):
            raise ModuleNotFoundError(f'Optional extension disabled for this import: {fullname}')
        return None


def load_chrono():
    core_filter = _CoreOnly()
    sys.meta_path.insert(0, core_filter)
    try:
        core = importlib.import_module('pychrono.core')
    finally:
        sys.meta_path.remove(core_filter)
    # The conda initialiser does not set this path when fea is disabled.
    data = Path(core.__file__).resolve().parent / '../../../Library/data'
    if data.is_dir():
        core.SetChronoDataPath(str(data.resolve()) + '/')
    return core


chrono = load_chrono()


# Small conversions between PyChrono objects and plain Python values.
def vect(v):
    return chrono.ChVector3d(*v)


def xyz(v):
    return (v.x, v.y, v.z)


def angle(b):
    q = b.GetRot()
    return 2 * math.atan2(q.e3, q.e0)


def omega(b):
    return b.GetAngVelParent().z


if __name__ == '__main__':
    forbidden = [n for n in sys.modules if n.startswith(('pychrono.vsg', 'pychrono._vsg',
                 'pychrono.irrlicht', 'pychrono.sensor'))]
    if forbidden:
        raise RuntimeError(f'Graphics extensions already loaded: {forbidden}')
    test_system = chrono.ChSystemNSC()
    print('PyChrono core working; no graphics extension loaded.', flush=True)
