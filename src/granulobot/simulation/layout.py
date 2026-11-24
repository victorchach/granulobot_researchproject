"""Layout of the units: positions on the support and coupled pairs (no PyChrono).

2 units: one facing pair, active A -> free B.
N >= 3: a closed ring on a regular N-gon, active magnet of unit i facing the
free magnet of unit i+1, and the last unit coupled back to A.
"""
import math

MAX_UNITS = 26  # names A..Z; see specs/IDEES.md to go further


def ring_radius(n, side):
    """Circumradius of the regular n-gon with this side (n >= 3)."""
    return side / (2 * math.sin(math.pi / n))


def ring_positions(n, side):
    """Unit centres (x, y), counterclockwise from A; neighbours are `side` apart.

    For n = 3 this is the original triangle: A bottom left, B bottom right,
    C on top.
    """
    if n == 2:
        return ((-side / 2, 0), (side / 2, 0))
    r = ring_radius(n, side)
    angles = (-math.pi / 2 - math.pi / n + 2 * math.pi * i / n for i in range(n))
    return tuple((r * math.cos(a), r * math.sin(a)) for a in angles)


def coupled_pairs(n):
    """(active unit, free unit) index pairs whose magnets face each other."""
    return ((0, 1),) if n == 2 else tuple((i, (i + 1) % n) for i in range(n))
