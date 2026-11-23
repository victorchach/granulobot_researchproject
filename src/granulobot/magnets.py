"""Interaction de deux cylindres uniformément aimantés selon Z, en vue plane.

Charges magnétiques surfaciques +/- M sur les deux faces annulaires :
U = mu0/(4*pi) * somme(qi*qj/r). Quadrature des surfaces, puis interpolation
Hermite de l'énergie : F = -dU/dd, pour conserver force/potentiel cohérents.
Les axes sont parallèles, les centres sont supposés à la même hauteur.
Une rotation propre autour de Z ne change ni les pôles ni cette interaction.
Br et l'uniformité de l'aimantation restent des hypothèses à calibrer.
Référence de la méthode des charges surfaciques :
https://doi.org/10.1016/j.jmmm.2022.169482
"""
from bisect import bisect_right
from functools import lru_cache
import math


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
