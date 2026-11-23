"""Interaction of two cylinders uniformly magnetised along Z, in a planar view.

Magnetic surface charges +/- M on the two annular faces:
U = mu0/(4*pi) * sum(qi*qj/r). Quadrature over the surfaces, then Hermite
interpolation of the energy: F = -dU/dd, so that force and potential stay
consistent. The axes are parallel and the centres are assumed at the same
height. A spin about Z changes neither the poles nor this interaction.
Br and the uniformity of the magnetisation remain assumptions to calibrate.
Reference for the surface charge method:
https://doi.org/10.1016/j.jmmm.2022.169482

Point dipoles with a regularised potential: an approximation of finite
magnets, not valid as a quantitative prediction at very short distance
without calibration.
apply_magnetism applies either model to the Chrono bodies at each step.
"""
from bisect import bisect_right
from functools import lru_cache
from itertools import combinations
import math

from granulobot.chrono_env import vect


class AxialCylinders:
    def __init__(self, diameter, hole, height, remanence, factor=1,
                 epsilon=0.0002, radial=4, angular=16, points=161):
        self.diameter, self.epsilon, self.height = diameter, epsilon, height
        ro, ri = diameter / 2, hole / 2
        surface = math.pi * (ro**2 - ri**2)
        q = factor * remanence / (4 * math.pi * 1e-7) * surface / (radial * angular)
        self.coeff = 2e-7 * q**2
        nodes = []
        for k in range(radial):
            radius = math.sqrt(ri**2 + (ro**2 - ri**2) * (k + 0.5) / radial)
            for j in range(angular):
                a = 2 * math.pi * (j + 0.5) / angular
                nodes.append((radius * math.cos(a), radius * math.sin(a)))
        self.offsets = tuple((b[0] - a[0], b[1] - a[1]) for a in nodes for b in nodes)
        # Dense grid near contact; direct computation beyond it.
        start, end = 0.995 * diameter, max(0.3, 12 * diameter)
        self.ds = [start * (end / start)**(i / (points - 1)) for i in range(points)]
        self.values = [self.direct(d) for d in self.ds]

    def direct(self, distance):
        """Return the energy and radial force for two identical polarities.

        Opposite polarities: multiply both outputs by -1.
        The quadrature integrates the four pairs of faces; two pairs are equal.
        """
        u = f = 0.0
        h2, eps2 = self.height**2, self.epsilon**2
        for dx, dy in self.offsets:
            x = distance + dx
            r2 = x*x + dy*dy + eps2
            r = math.sqrt(r2)
            s = math.sqrt(r2 + h2)
            u += 1 / r - 1 / s
            f += x * (1 / (r2 * r) - 1 / ((r2 + h2) * s))
        return self.coeff * u, self.coeff * f

    def evaluate(self, distance):
        if distance < self.ds[0] or distance > self.ds[-1]:
            return self.direct(distance)
        i = min(bisect_right(self.ds, distance) - 1, len(self.ds) - 2)
        h = self.ds[i + 1] - self.ds[i]
        t = (distance - self.ds[i]) / h
        u0, f0 = self.values[i]
        u1, f1 = self.values[i + 1]
        m0, m1 = -f0, -f1
        u = (2*t**3-3*t*t+1)*u0 + (t**3-2*t*t+t)*h*m0 + (-2*t**3+3*t*t)*u1 + (t**3-t*t)*h*m1
        du = (6*t*t-6*t)/h*u0 + (3*t*t-4*t+1)*m0 + (-6*t*t+6*t)/h*u1 + (3*t*t-2*t)*m1
        return u, -du


@lru_cache(maxsize=16)
def cached_model(diameter, hole, height, remanence, factor, epsilon, radial, angular):
    return AxialCylinders(diameter, hole, height, remanence, factor,
                          epsilon, radial, angular)


def for_parameters(p):
    return cached_model(p.diametre_aimant_ext, p.diametre_aimant_int, p.epaisseur_aimant,
                        p.remanence, p.facteur_moment, p.adoucissement_magnetique,
                        p.quadrature_radiale, p.quadrature_angulaire)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def dipoles(r, mi, mj, epsilon):
    """r = position_j - position_i; returns F on j, torques on i/j and energy.

    Force = -gradient_r U. The force on i is -F. Each force must be applied
    AT THE POINT of the magnet; the returned torques are pure torques (dipole
    orientation), on top of the moment of that force.
    The same softened potential gives the forces and the torques, with no cap.
    """
    s2 = dot(r, r) + epsilon**2
    s3, s5, s7 = s2**1.5, s2**2.5, s2**3.5
    a, b, c = dot(mi, r), dot(mj, r), dot(mi, mj)
    force = tuple(3e-7 * ((c * rk + b * mik + a * mjk) / s5 -
                         5 * a * b * rk / s7)
                  for rk, mik, mjk in zip(r, mi, mj))
    bi = tuple(1e-7 * (3 * rk * b / s5 - mjk / s3) for rk, mjk in zip(r, mj))
    bj = tuple(1e-7 * (3 * rk * a / s5 - mik / s3) for rk, mik in zip(r, mi))
    return force, cross(mi, bi), cross(mj, bj), 1e-7 * (c / s3 - 3 * a * b / s5)


def apply_magnetism(units, p):
    if not p.magnetisme_actif or p.liaison_ideale:
        return 0.0, 0.0
    magnets = [(i, *u.magnet(active, p)) for i, u in enumerate(units) for active in (True, False)]
    cylinders = None
    if p.modele_magnetique == 'cylindres':
        cylinders = for_parameters(p)
    energy, max_force = 0.0, 0.0
    for ai, aj in combinations(magnets, 2):
        i, bi, idxi, pi, mi = ai
        j, bj, idxj, pj, mj = aj
        if i == j and not p.interactions_internes:
            continue
        r = tuple(b - a for a, b in zip(pi, pj))
        if cylinders is None:
            f, ti, tj, potential = dipoles(r, mi, mj, p.adoucissement_magnetique)
        else:
            d = math.hypot(r[0], r[1])
            if d < 1e-12:
                raise RuntimeError('Magnet centres coincide')
            potential, radial = cylinders.evaluate(d)
            sign = 1 if mi[2] * mj[2] >= 0 else -1
            potential *= sign
            f = (sign * radial * r[0] / d, sign * radial * r[1] / d, 0)
            ti = tj = (0, 0, 0)  # Axial: no pure torque about Z.
        bi.AccumulateForce(idxi, vect(tuple(-c for c in f)), vect(pi), False)
        bj.AccumulateForce(idxj, vect(f), vect(pj), False)
        bi.AccumulateTorque(idxi, vect(ti), False)
        bj.AccumulateTorque(idxj, vect(tj), False)
        energy += potential
        max_force = max(max_force, math.sqrt(sum(c * c for c in f)))
    return energy, max_force
