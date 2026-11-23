"""Interaction de deux cylindres uniformément aimantés selon Z, en vue plane.

Charges magnétiques surfaciques +/- M sur les deux faces annulaires :
U = mu0/(4*pi) * somme(qi*qj/r). Quadrature des surfaces, puis interpolation
Hermite de l'énergie : F = -dU/dd, pour conserver force/potentiel cohérents.
Les axes sont parallèles, les centres sont supposés à la même hauteur.
Une rotation propre autour de Z ne change ni les pôles ni cette interaction.
Br et l'uniformité de l'aimantation restent des hypothèses à calibrer.
Référence de la méthode des charges surfaciques :
https://doi.org/10.1016/j.jmmm.2022.169482

Dipôles ponctuels avec potentiel régularisé : approximation des aimants finis,
non valable comme prédiction quantitative à très courte distance sans calibration.
appliquer_magnetisme applique l'un ou l'autre modèle aux corps Chrono à chaque pas.
"""
from bisect import bisect_right
from functools import lru_cache
from itertools import combinations
import math

from granulobot.chrono_env import vect


class CylindresAxiaux:
    def __init__(self, diametre, trou, hauteur, remanence, facteur=1,
                 epsilon=0.0002, radial=4, angulaire=16, points=161):
        self.diametre, self.epsilon, self.hauteur = diametre, epsilon, hauteur
        ro, ri = diametre / 2, trou / 2
        surface = math.pi * (ro**2 - ri**2)
        q = facteur * remanence / (4 * math.pi * 1e-7) * surface / (radial * angulaire)
        self.coeff = 2e-7 * q**2
        noeuds = []
        for k in range(radial):
            rayon = math.sqrt(ri**2 + (ro**2 - ri**2) * (k + 0.5) / radial)
            for j in range(angulaire):
                a = 2 * math.pi * (j + 0.5) / angulaire
                noeuds.append((rayon * math.cos(a), rayon * math.sin(a)))
        self.ecarts = tuple((b[0] - a[0], b[1] - a[1]) for a in noeuds for b in noeuds)
        # Maillage dense près du contact ; extrapolation directe au-delà.
        debut, fin = 0.995 * diametre, max(0.3, 12 * diametre)
        self.ds = [debut * (fin / debut)**(i / (points - 1)) for i in range(points)]
        self.valeurs = [self.direct(d) for d in self.ds]

    def direct(self, distance):
        """Retourne énergie et force radiale pour deux polarités identiques.

        Polarités opposées : multiplier les deux sorties par -1.
        La quadrature intègre les quatre paires de faces ; deux paires égales.
        """
        u = f = 0.0
        h2, eps2 = self.hauteur**2, self.epsilon**2
        for dx, dy in self.ecarts:
            x = distance + dx
            r2 = x*x + dy*dy + eps2
            r = math.sqrt(r2)
            s = math.sqrt(r2 + h2)
            u += 1 / r - 1 / s
            f += x * (1 / (r2 * r) - 1 / ((r2 + h2) * s))
        return self.coeff * u, self.coeff * f

    def evaluer(self, distance):
        if distance < self.ds[0] or distance > self.ds[-1]:
            return self.direct(distance)
        i = min(bisect_right(self.ds, distance) - 1, len(self.ds) - 2)
        h = self.ds[i + 1] - self.ds[i]
        t = (distance - self.ds[i]) / h
        u0, f0 = self.valeurs[i]
        u1, f1 = self.valeurs[i + 1]
        m0, m1 = -f0, -f1
        u = (2*t**3-3*t*t+1)*u0 + (t**3-2*t*t+t)*h*m0 + (-2*t**3+3*t*t)*u1 + (t**3-t*t)*h*m1
        du = (6*t*t-6*t)/h*u0 + (3*t*t-4*t+1)*m0 + (-6*t*t+6*t)/h*u1 + (3*t*t-2*t)*m1
        return u, -du


@lru_cache(maxsize=16)
def modele(diametre, trou, hauteur, remanence, facteur, epsilon, radial, angulaire):
    return CylindresAxiaux(diametre, trou, hauteur, remanence, facteur,
                          epsilon, radial, angulaire)


def pour_parametres(p):
    return modele(p.diametre_aimant_ext, p.diametre_aimant_int, p.epaisseur_aimant,
                  p.remanence, p.facteur_moment, p.adoucissement_magnetique,
                  p.quadrature_radiale, p.quadrature_angulaire)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def dipoles(r, mi, mj, epsilon):
    """r = position_j - position_i ; retourne F sur j, couples i/j et énergie.

    Force = -gradient_r U. La force sur i vaut -F. Chaque force doit être
    appliquée AU POINT de l'aimant ; les couples retournés sont des couples
    purs (orientation du dipôle), supplémentaires au moment de cette force.
    Le même potentiel adouci sert aux forces et aux couples, sans plafonnement.
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


def appliquer_magnetisme(robots, p):
    if not p.magnetisme_actif or p.liaison_ideale:
        return 0.0, 0.0
    aimants = [(i, *u.aimant(actif, p)) for i, u in enumerate(robots) for actif in (True, False)]
    cylindres = None
    if p.modele_magnetique == 'cylindres':
        cylindres = pour_parametres(p)
    energie, force_max = 0.0, 0.0
    for ai, aj in combinations(aimants, 2):
        i, bi, idxi, pi, mi = ai
        j, bj, idxj, pj, mj = aj
        if i == j and not p.interactions_internes:
            continue
        r = tuple(b - a for a, b in zip(pi, pj))
        if cylindres is None:
            f, ti, tj, potentiel = dipoles(r, mi, mj, p.adoucissement_magnetique)
        else:
            d = math.hypot(r[0], r[1])
            if d < 1e-12:
                raise RuntimeError('Centres des aimants confondus')
            potentiel, radial = cylindres.evaluer(d)
            signe = 1 if mi[2] * mj[2] >= 0 else -1
            potentiel *= signe
            f = (signe * radial * r[0] / d, signe * radial * r[1] / d, 0)
            ti = tj = (0, 0, 0)  # Axiale : pas de couple propre autour de Z.
        bi.AccumulateForce(idxi, vect(tuple(-c for c in f)), vect(pi), False)
        bj.AccumulateForce(idxj, vect(f), vect(pj), False)
        bi.AccumulateTorque(idxi, vect(ti), False)
        bj.AccumulateTorque(idxj, vect(tj), False)
        energie += potentiel
        force_max = max(force_max, math.sqrt(sum(c * c for c in f)))
    return energie, force_max
