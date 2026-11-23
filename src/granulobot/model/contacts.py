"""Contacts analytiques entre unités (jantes, aimants) et avec le sol."""
from itertools import combinations
import math

from granulobot.chrono_env import chrono
from granulobot.model.unit import paires


class ContactsCirculaires(chrono.CustomCollisionCallback):
    """Géométrie exacte du contact latéral pour des cylindres parallèles à Z.

    Seule la détection change : les contraintes normales et Coulomb restent
    calculées par Chrono NSC. Bullet continue de détecter les contacts au sol.
    Ce modèle convient aux axes verticaux imposés, pas à des cylindres inclinés.
    """
    def __init__(self, robots, mat, p, sol=None):
        super().__init__()
        self.robots, self.mat, self.p = robots, mat, p
        self.sol = sol
        self.mat_support = chrono.ChContactMaterialNSC()
        self.mat_support.SetFriction(p.mu_sol)
        self.mat_support.SetRestitution(p.restitution)
        # NSC : |couple autour de la normale| <= longueur * force normale.
        self.mat_support.SetSpinningFriction(p.mu_sol * p.facteur_rayon_frottement_sol * p.R)
        self.mat_aimant = chrono.ChContactMaterialNSC()
        self.mat_aimant.SetFriction(p.mu_aimants)
        self.mat_aimant.SetRestitution(p.restitution)
        self.mat_aimant.SetCompliance(p.compliance_aimants)

    def OnCustomCollision(self, sys):
        p = self.p
        if self.sol is not None and p.modele_sol == 'disque_equivalent':
            for u in self.robots:
                support = u.roue if u.roue is not None and not p.roue_motorisee_en_bas else u.corps
                pos = support.GetPos()
                gap = pos.z - p.H / 2
                if gap > 2 * p.enveloppe_collision:
                    continue
                if abs(pos.x) > p.largeur_sol / 2 or abs(pos.y) > p.largeur_sol / 2:
                    continue
                info = chrono.ChCollisionInfo()
                info.modelA = self.sol.GetCollisionModel()
                info.modelB = support.GetCollisionModel()
                info.vN = chrono.ChVector3d(0, 0, 1)
                info.vpA = chrono.ChVector3d(pos.x, pos.y, 0)
                info.vpB = chrono.ChVector3d(pos.x, pos.y, gap)
                info.distance = gap
                sys.GetContactContainer().AddContact(info, self.mat_support, self.mat_support)
        for i, j in paires(self.robots):
            self.contact_jantes(sys, self.robots[i].corps, self.robots[j].corps,
                                False, p)
            if self.robots[i].roue is not None:
                self.contact_jantes(sys, self.robots[i].roue, self.robots[j].roue,
                                    True, p)
        if p.contact_aimants and not p.liaison_ideale:
            self.contact_petits_aimants(sys, p)

    def contact_jantes(self, sys, a, b, libre, p):
        # Deux plans de jantes indépendants ; pas un cylindre unique.
        pa, pb = a.GetPos(), b.GetPos()
        dx, dy = pb.x - pa.x, pb.y - pa.y
        d = math.hypot(dx, dy)
        if d - 2 * p.R > 2 * p.enveloppe_collision or abs(pb.z - pa.z) >= (p.epaisseur_roue if p.roue_libre_exterieure else p.H):
            return
        if d < 1e-12:
            raise RuntimeError("Centres confondus : état initial ou pas de temps invalide")
        nx, ny = dx / d, dy / d
        z = (pa.z + pb.z) / 2
        # Projection plane : même force XY et même couple Z ; les moments de
        # basculement sont omis avec les degrés Rx/Ry déjà bloqués.
        info = chrono.ChCollisionInfo()
        info.modelA, info.modelB = a.GetCollisionModel(), b.GetCollisionModel()
        info.vN = chrono.ChVector3d(nx, ny, 0)
        info.vpA = chrono.ChVector3d(pa.x + p.R * nx, pa.y + p.R * ny, z)
        info.vpB = chrono.ChVector3d(pb.x - p.R * nx, pb.y - p.R * ny, z)
        info.distance = d - 2 * p.R
        info.eff_radius = p.R / 2
        sys.GetContactContainer().AddContact(info, self.mat, self.mat)

    def contact_petits_aimants(self, sys, p):
        aimants = [(i, *u.aimant(actif, p)) for i, u in enumerate(self.robots)
                   for actif in (True, False)]
        for ai, aj in combinations(aimants, 2):
            i, a, _, pa, _ = ai
            j, b, _, pb, _ = aj
            if i == j:
                continue  # Disposition axiale interne du prototype à préciser.
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            d = math.hypot(dx, dy)
            if d - p.diametre_aimant_ext > 2 * p.enveloppe_collision or abs(pb[2] - pa[2]) >= p.epaisseur_aimant:
                continue
            if d < 1e-12:
                raise RuntimeError('Centres des aimants confondus')
            nx, ny, rayon = dx / d, dy / d, p.diametre_aimant_ext / 2
            z = (pa[2] + pb[2]) / 2
            info = chrono.ChCollisionInfo()
            info.modelA, info.modelB = a.GetCollisionModel(), b.GetCollisionModel()
            info.vN = chrono.ChVector3d(nx, ny, 0)
            info.vpA = chrono.ChVector3d(pa[0] + rayon * nx, pa[1] + rayon * ny, z)
            info.vpB = chrono.ChVector3d(pb[0] - rayon * nx, pb[1] - rayon * ny, z)
            info.distance = d - 2 * rayon
            info.eff_radius = rayon / 2
            sys.GetContactContainer().AddContact(info, self.mat_aimant, self.mat_aimant)
