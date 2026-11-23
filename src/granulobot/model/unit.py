"""Une unité Granulobot : quatre corps rigides et leurs liaisons.

Corps (coque), rotor actif (aimant actif, entraîné par le moteur), rotor libre
(aimant libre, sur pivot) et roue libre extérieure (sur pivot). Le moteur agit
entre le rotor actif et le corps ; un guide ne bloque que le basculement.
"""
from dataclasses import dataclass
from itertools import combinations
import math

from granulobot.chrono_env import chrono, xyz


def noms(robots):
    return tuple(chr(ord("A") + i) for i in range(len(robots)))


def paires(robots):
    return tuple(combinations(range(len(robots)), 2))


@dataclass
class Unite:
    corps: object
    actif: object
    libre: object
    idx_corps: int
    idx_actif: int
    idx_libre: int
    moteur: object
    fonction: object
    pivot_libre: object
    guide: object
    roue: object = None
    idx_roue: int = None
    pivot_roue: object = None
    integrale: float = 0.0
    tension: float = 0.0
    courant: float = 0.0
    couple_moteur: float = 0.0
    couple_transmis: float = 0.0

    def aimant(self, actif, p):
        b = self.actif if actif else self.libre
        e = p.excentricite_actif if actif else p.excentricite_libre
        # Le centre de masse du rotor est décalé de e par rapport au pivot.
        point = b.TransformPointLocalToParent(chrono.ChVector3d(p.rayon_aimant - e, 0, 0))
        direction = b.TransformDirectionLocalToParent(chrono.ChVector3d(1, 0, 0))
        signe = 1 if actif else -1  # polarités opposées actif / libre
        moment = ((0, 0, signe * p.moment_aimant) if p.orientation_aimant == 'axiale'
                  else tuple(signe * p.moment_aimant * c for c in xyz(direction)))
        return b, self.idx_actif if actif else self.idx_libre, xyz(point), moment

    def vider_forces(self):
        pieces = [(self.corps, self.idx_corps), (self.actif, self.idx_actif),
                  (self.libre, self.idx_libre)]
        if self.roue is not None:
            pieces.append((self.roue, self.idx_roue))
        for b, idx in pieces:
            b.EmptyAccumulator(idx)

    def corps_dynamiques(self):
        return (self.corps, self.actif, self.libre) + ((self.roue,) if self.roue is not None else ())


def creer_unite(sys, p, mat, repere, i, positions):
    """Crée l'unité i à positions[i] et l'ajoute au système ; ordre des corps inchangé."""
    x, y = positions[i]
    pivot = chrono.ChVector3d(x, y, p.H / 2 + p.enveloppe_collision)
    rho = p.masse_corps / (math.pi * p.R**2 * p.H)
    corps = chrono.ChBodyEasyCylinder(chrono.ChAxis_Z, p.R, p.H, rho, False, False, mat)
    hauteur_contact = p.epaisseur_roue if p.roue_libre_exterieure else p.H
    z_contact = ((-1 if p.roue_motorisee_en_bas else 1) *
                 (p.H - hauteur_contact) / 2 if p.roue_libre_exterieure else 0)
    corps.AddCollisionShape(chrono.ChCollisionShapeCylinder(mat, p.R, hauteur_contact),
                            chrono.ChFramed(chrono.ChVector3d(0, 0, z_contact),
                                            chrono.QuatFromAngleX(math.pi / 2)))
    corps.EnableCollision(True)
    corps.SetPos(pivot)
    corps.SetFixed(False)
    # Le contact entre robots est ajouté analytiquement par le callback.
    corps.GetCollisionModel().SetFamily(1)
    corps.GetCollisionModel().DisallowCollisionsWith(1)
    corps.SetInertiaXX(chrono.ChVector3d(
        p.masse_corps * (3 * p.R**2 + p.H**2) / 12,
        p.masse_corps * (3 * p.R**2 + p.H**2) / 12,
        p.facteur_inertie_corps * p.masse_corps * p.R**2))
    sys.AddBody(corps)
    guide = chrono.ChLinkMateGeneric()
    # Avec sol : Z libre pour que le sol supporte le poids, pas le guide.
    guide.SetConstrainedCoords(False, False, not p.sol_actif, True, True, False)
    guide.Initialize(corps, repere, chrono.ChFramed(pivot))
    sys.AddLink(guide)
    rotors = []
    for actif in (True, False):
        if p.nombre_robots == 2:
            # Une paire face à face : actif A -> libre B.
            # Les deux autres aimants sont orientés vers l'extérieur.
            phi = 0.0 if actif else math.pi
        else:
            voisin = (i + 1) % 3 if actif else (i - 1) % 3
            phi = math.atan2(positions[voisin][1] - y, positions[voisin][0] - x)
        if actif and i == 0:
            phi += p.perturbation_rotor_rad
        masse = p.masse_actif if actif else p.masse_libre
        e = p.excentricite_actif if actif else p.excentricite_libre
        inertie = p.inertie_actif_pivot if actif else p.inertie_libre_pivot
        rotor = chrono.ChBody()
        rotor.SetMass(masse)
        # Théorème des axes parallèles : pas de double comptage de l'excentricité.
        icom = inertie - masse * e**2
        rotor.SetInertiaXX(chrono.ChVector3d(icom / 2, icom / 2, icom))
        rotor.SetPos(chrono.ChVector3d(x + e * math.cos(phi), y + e * math.sin(phi), pivot.z))
        rotor.SetRot(chrono.QuatFromAngleZ(phi))
        # Géométrie réelle de l'aimant attachée au rotor. La détection de
        # contact est analytique ; les coques pleines cachent leurs logements.
        forme = chrono.ChCollisionShapeCylinder(mat, p.diametre_aimant_ext / 2,
                                                p.epaisseur_aimant)
        rotor.AddCollisionShape(forme, chrono.ChFramed(
            chrono.ChVector3d(p.rayon_aimant - e, 0, 0),
            chrono.QuatFromAngleX(math.pi / 2)))
        rotor.GetCollisionModel().SetFamilyMask(0)  # Pas de doublon Bullet.
        sys.AddBody(rotor)  # Pas de collision rotor/coque : pièces internes.
        rotors.append(rotor)
    moteur = chrono.ChLinkMotorRotationTorque()
    moteur.Initialize(rotors[0], corps, chrono.ChFramed(pivot))
    fonction = chrono.ChFunctionConst(0)
    moteur.SetTorqueFunction(fonction)
    sys.AddLink(moteur)
    libre = chrono.ChLinkLockRevolute()
    libre.Initialize(rotors[1], corps, chrono.ChFramed(pivot))
    sys.AddLink(libre)
    unite = Unite(corps, *rotors, corps.AddAccumulator(),
                  rotors[0].AddAccumulator(), rotors[1].AddAccumulator(),
                  moteur, fonction, libre, guide)
    if p.roue_libre_exterieure:
        rho_roue = p.masse_roue_libre / (math.pi * p.R**2 * p.epaisseur_roue)
        roue = chrono.ChBodyEasyCylinder(chrono.ChAxis_Z, p.R, p.epaisseur_roue,
                                        rho_roue, False, True, mat)
        z = pivot.z + (1 if p.roue_motorisee_en_bas else -1) * (p.H-p.epaisseur_roue)/2
        # COM virtuel dans le plan commun : équivalent pour XY/yaw,
        # sans levier vertical artificiel dans les contraintes du guide.
        roue.SetPos(pivot)
        roue.GetCollisionModel().Clear()
        roue.AddCollisionShape(chrono.ChCollisionShapeCylinder(mat, p.R, p.epaisseur_roue),
                               chrono.ChFramed(chrono.ChVector3d(0, 0, z-pivot.z),
                                               chrono.QuatFromAngleX(math.pi/2)))
        roue.GetCollisionModel().SetFamily(1)
        roue.GetCollisionModel().DisallowCollisionsWith(1)
        sys.AddBody(roue)
        pivot_roue = chrono.ChLinkLockRevolute()
        pivot_roue.Initialize(roue, corps, chrono.ChFramed(pivot))
        sys.AddLink(pivot_roue)
        unite.roue, unite.pivot_roue = roue, pivot_roue
        unite.idx_roue = roue.AddAccumulator()
    return unite
