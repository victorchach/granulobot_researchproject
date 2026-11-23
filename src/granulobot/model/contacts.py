"""Analytic contacts between units (rims, magnets) and with the ground."""
from itertools import combinations
import math

from granulobot.chrono_env import chrono
from granulobot.model.unit import unit_pairs


class CircularContacts(chrono.CustomCollisionCallback):
    """Exact geometry of the side contact for cylinders parallel to Z.

    Only the detection changes: the normal and Coulomb constraints are still
    computed by Chrono NSC. Bullet still detects the ground contacts.
    This model suits imposed vertical axes, not tilted cylinders.
    """
    def __init__(self, units, mat, p, ground=None):
        super().__init__()
        self.units, self.mat, self.p = units, mat, p
        self.ground = ground
        self.mat_support = chrono.ChContactMaterialNSC()
        self.mat_support.SetFriction(p.mu_sol)
        self.mat_support.SetRestitution(p.restitution)
        # NSC: |torque about the normal| <= length * normal force.
        self.mat_support.SetSpinningFriction(p.mu_sol * p.facteur_rayon_frottement_sol * p.R)
        self.mat_magnet = chrono.ChContactMaterialNSC()
        self.mat_magnet.SetFriction(p.mu_aimants)
        self.mat_magnet.SetRestitution(p.restitution)
        self.mat_magnet.SetCompliance(p.compliance_aimants)

    def OnCustomCollision(self, sys):
        p = self.p
        if self.ground is not None and p.modele_sol == 'disque_equivalent':
            for u in self.units:
                support = u.wheel if u.wheel is not None and not p.roue_motorisee_en_bas else u.body
                pos = support.GetPos()
                gap = pos.z - p.H / 2
                if gap > 2 * p.enveloppe_collision:
                    continue
                if abs(pos.x) > p.largeur_sol / 2 or abs(pos.y) > p.largeur_sol / 2:
                    continue
                info = chrono.ChCollisionInfo()
                info.modelA = self.ground.GetCollisionModel()
                info.modelB = support.GetCollisionModel()
                info.vN = chrono.ChVector3d(0, 0, 1)
                info.vpA = chrono.ChVector3d(pos.x, pos.y, 0)
                info.vpB = chrono.ChVector3d(pos.x, pos.y, gap)
                info.distance = gap
                sys.GetContactContainer().AddContact(info, self.mat_support, self.mat_support)
        for i, j in unit_pairs(self.units):
            self.rim_contact(sys, self.units[i].body, self.units[j].body,
                             False, p)
            if self.units[i].wheel is not None:
                self.rim_contact(sys, self.units[i].wheel, self.units[j].wheel,
                                 True, p)
        if p.contact_aimants and not p.liaison_ideale:
            self.magnet_contact(sys, p)

    def rim_contact(self, sys, a, b, free, p):
        # Two independent rim planes, not a single cylinder.
        pa, pb = a.GetPos(), b.GetPos()
        dx, dy = pb.x - pa.x, pb.y - pa.y
        d = math.hypot(dx, dy)
        if d - 2 * p.R > 2 * p.enveloppe_collision or abs(pb.z - pa.z) >= (p.epaisseur_roue if p.roue_libre_exterieure else p.H):
            return
        if d < 1e-12:
            raise RuntimeError("Centres coincide: invalid initial state or time step")
        nx, ny = dx / d, dy / d
        z = (pa.z + pb.z) / 2
        # Planar projection: same XY force and same Z torque; the tipping
        # moments are dropped, with the Rx/Ry degrees already blocked.
        info = chrono.ChCollisionInfo()
        info.modelA, info.modelB = a.GetCollisionModel(), b.GetCollisionModel()
        info.vN = chrono.ChVector3d(nx, ny, 0)
        info.vpA = chrono.ChVector3d(pa.x + p.R * nx, pa.y + p.R * ny, z)
        info.vpB = chrono.ChVector3d(pb.x - p.R * nx, pb.y - p.R * ny, z)
        info.distance = d - 2 * p.R
        info.eff_radius = p.R / 2
        sys.GetContactContainer().AddContact(info, self.mat, self.mat)

    def magnet_contact(self, sys, p):
        magnets = [(i, *u.magnet(active, p)) for i, u in enumerate(self.units)
                   for active in (True, False)]
        for ai, aj in combinations(magnets, 2):
            i, a, _, pa, _ = ai
            j, b, _, pb, _ = aj
            if i == j:
                continue  # Internal axial layout of the prototype still to specify.
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            d = math.hypot(dx, dy)
            if d - p.diametre_aimant_ext > 2 * p.enveloppe_collision or abs(pb[2] - pa[2]) >= p.epaisseur_aimant:
                continue
            if d < 1e-12:
                raise RuntimeError('Magnet centres coincide')
            nx, ny, radius = dx / d, dy / d, p.diametre_aimant_ext / 2
            z = (pa[2] + pb[2]) / 2
            info = chrono.ChCollisionInfo()
            info.modelA, info.modelB = a.GetCollisionModel(), b.GetCollisionModel()
            info.vN = chrono.ChVector3d(nx, ny, 0)
            info.vpA = chrono.ChVector3d(pa[0] + radius * nx, pa[1] + radius * ny, z)
            info.vpB = chrono.ChVector3d(pb[0] - radius * nx, pb[1] - radius * ny, z)
            info.distance = d - 2 * radius
            info.eff_radius = radius / 2
            sys.GetContactContainer().AddContact(info, self.mat_magnet, self.mat_magnet)
