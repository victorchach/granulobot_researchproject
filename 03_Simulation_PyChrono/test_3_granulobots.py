"""Trois granulobots : roue motorisée, deux rotors et roue libre, vue de dessus.

Les paramètres SI et leurs origines sont dans granulobot_physics.py.
Commande en tension par défaut ; pas de vitesse ni de déplacement imposé.
Le sol fournit la réaction au poids et les frottements NSC. Un guide ne
bloque que le basculement (Rx/Ry), jamais X, Y, Z ou la rotation autour de Z.
Les aimants affleurants de diamètre 8 mm et hauteur 10 mm ont leurs pôles
sur les faces plates. Leur champ plan est calculé par charges surfaciques,
avec quadrature et contact NSC. Les dipôles restent une variante de comparaison.
La rotation propre autour de Z ne change pas une aimantation axiale.
Les aimants restent mécaniquement solidaires du rotor : leur roulement propre
(et son effet sur le frottement de contact), les dents et les collisions
internes entre aimants restent omis.

Exemples (environnement conda chrono) :
    python test_3_granulobots.py
    python test_3_granulobots.py --tensions 1 2 3
    python test_3_granulobots.py --mode vitesse --vitesses 0.3 0.3 0.3
    python test_3_granulobots.py --sans-sol --sans-magnetisme
    python test_3_granulobots.py --duree 0.2 --sans-gif --sortie /chemin/essai

Sorties : GIF à vitesse réelle, CSV de mesures, JSON de paramètres/bilan.
Le modèle simple précédent reste dans test_3_granulobots_simple.py.
"""
import argparse
from bisect import bisect_left
import csv
from dataclasses import dataclass
from itertools import combinations
import json
import math
from pathlib import Path

from chrono_headless import chrono
from granulobot_physics import Parametres, dipoles, frottement, moteur_cc

# Modifier ces paramètres pour les essais. Les détails sont dans le module physique.
PARAMETRES = Parametres()
def noms(robots):
    return tuple(chr(ord("A") + i) for i in range(len(robots)))


def paires(robots):
    return tuple(combinations(range(len(robots)), 2))


def appariements(robots):
    return ((0, 1),) if len(robots) == 2 else ((0, 1), (1, 2), (2, 0))


def vect(v):
    return chrono.ChVector3d(*v)


def xyz(v):
    return (v.x, v.y, v.z)


def angle(b):
    q = b.GetRot()
    return 2 * math.atan2(q.e3, q.e0)


def omega(b):
    return b.GetAngVelParent().z


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


def creer_systeme(p):
    sys = chrono.ChSystemNSC()
    sys.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)
    sys.SetSolverType({'PSOR': chrono.ChSolver.Type_PSOR,
                      'APGD': chrono.ChSolver.Type_APGD}[p.solveur])
    solveur = sys.GetSolver().AsIterative()
    solveur.SetMaxIterations(p.iterations_solveur)
    solveur.SetTolerance(p.tolerance_solveur)
    sys.SetMaxPenetrationRecoverySpeed(p.vitesse_correction_contact)
    sys.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, -p.gravite))
    chrono.ChCollisionModel.SetDefaultSuggestedEnvelope(p.enveloppe_collision)
    chrono.ChCollisionModel.SetDefaultSuggestedMargin(p.marge_collision)
    mat = chrono.ChContactMaterialNSC()
    mat.SetFriction(p.mu_robots)
    mat.SetRestitution(p.restitution)
    mat.SetCompliance(p.compliance_coques)
    mat.SetRollingFriction(p.roulement_contact)
    mat.SetSpinningFriction(p.pivotement_contact)
    repere = chrono.ChBody()
    repere.SetFixed(True)
    sys.AddBody(repere)
    sol = None
    if p.sol_actif:
        mat_sol = chrono.ChContactMaterialNSC()
        mat_sol.SetFriction(p.mu_sol)
        mat_sol.SetRestitution(p.restitution)
        mat_sol.SetRollingFriction(p.roulement_contact)
        mat_sol.SetSpinningFriction(p.pivotement_contact)
        sol = chrono.ChBodyEasyBox(p.largeur_sol, p.largeur_sol, p.epaisseur_sol,
                                  1000, False, True, mat_sol)
        sol.SetPos(chrono.ChVector3d(0, 0, -p.epaisseur_sol / 2))
        sol.SetFixed(True)
        if p.modele_sol == 'disque_equivalent':
            sol.GetCollisionModel().SetFamilyMask(0)  # Support ajouté par le callback.
        sys.AddBody(sol)
    cote = 2 * p.R + p.jeu_initial
    positions = ((-cote / 2, -cote / (2 * math.sqrt(3))),
                 (cote / 2, -cote / (2 * math.sqrt(3))),
                 (0, cote / math.sqrt(3)))
    if p.nombre_robots == 2:
        positions = ((-cote / 2, 0), (cote / 2, 0))
    robots = []
    for i, (x, y) in enumerate(positions):
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
        robots.append(Unite(corps, *rotors, corps.AddAccumulator(),
                            rotors[0].AddAccumulator(), rotors[1].AddAccumulator(),
                            moteur, fonction, libre, guide))
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
            robots[-1].roue, robots[-1].pivot_roue = roue, pivot_roue
            robots[-1].idx_roue = roue.AddAccumulator()
    attaches = []
    if p.liaison_ideale:
        # Liaison de référence, indéformable et sans seuil de rupture. Elle
        # conserve la pose relative des deux rotors, jamais leurs centres au sol.
        for i, j in appariements(robots):
            _, _, a, _ = robots[i].aimant(True, p)
            _, _, b, _ = robots[j].aimant(False, p)
            point = vect(tuple((x + y) / 2 for x, y in zip(a, b)))
            lien = chrono.ChLinkLockLock()
            lien.Initialize(robots[i].actif, robots[j].libre, chrono.ChFramed(point))
            sys.AddLink(lien)
            attaches.append(lien)
    contacts = ContactsCirculaires(robots, mat, p, sol)
    sys.RegisterCustomCollisionCallback(contacts)
    return sys, robots, (repere, sol, contacts, attaches)  # Conserver les références SWIG.


def appliquer_moteur(u, i, t, p):
    w = omega(u.actif) - omega(u.corps)
    rampe = min(1, t / p.rampe_demarrage) if p.rampe_demarrage else 1
    if p.mode_moteur == "vitesse":
        cible = p.vitesses_cibles[i] * rampe
        erreur = cible - w
        # Anticipation du freinage électrique et des pertes + PI avec anti-windup.
        gain = p.rendement_reducteur * p.rapport_reduction * p.kt / p.resistance_moteur
        sec = p.couple_frottement_actif if p.frottement_interne_actif else 0
        ff = p.ke * p.rapport_reduction * cible + sec * math.tanh(cible / p.vitesse_regularisation) / gain
        brut = ff + p.gain_p_vitesse * erreur + p.gain_i_vitesse * u.integrale
        if abs(brut) < p.tension_max or brut * erreur < 0:
            u.integrale += erreur * p.dt
        tension = brut
    else:
        tension = p.tensions_cibles[i] * rampe
    if p.moteur_actif:
        if p.mode_moteur == "couple":
            couple = max(-p.couple_max, min(p.couple_max, p.couples_cibles[i] * rampe))
            u.tension = u.courant = 0.0  # Pas de modèle électrique dans ce mode.
        else:
            couple, u.courant, u.tension = moteur_cc(tension, w, p)
    else:
        couple = 0.0  # Moteur déconnecté, circuit ouvert ; pas de freinage électrique.
        u.tension = u.courant = 0.0
    u.couple_moteur = couple
    if p.frottement_interne_actif:
        couple += frottement(w, p.couple_frottement_actif, 0, p.vitesse_regularisation)
    u.couple_transmis = couple
    u.fonction.SetConstant(couple)  # Chrono applique automatiquement la réaction au corps.
    wlibre = omega(u.libre) - omega(u.corps)
    perte = frottement(wlibre, p.couple_frottement_libre, p.viscosite_libre,
                      p.vitesse_regularisation) if p.frottement_interne_actif else 0
    u.libre.AccumulateTorque(u.idx_libre, chrono.ChVector3d(0, 0, perte), False)
    u.corps.AccumulateTorque(u.idx_corps, chrono.ChVector3d(0, 0, -perte), False)
    if u.roue is not None:
        wr = omega(u.roue) - omega(u.corps)
        cr = frottement(wr, p.couple_frottement_roue, p.viscosite_roue,
                       p.vitesse_regularisation) if p.frottement_interne_actif else 0
        u.roue.AccumulateTorque(u.idx_roue, chrono.ChVector3d(0, 0, cr), False)
        u.corps.AccumulateTorque(u.idx_corps, chrono.ChVector3d(0, 0, -cr), False)
    v = u.corps.GetPosDt()
    u.corps.AccumulateForce(u.idx_corps,
                           chrono.ChVector3d(-p.resistance_translation * v.x,
                                            -p.resistance_translation * v.y, 0),
                           u.corps.GetPos(), False)
    u.corps.AccumulateTorque(u.idx_corps,
                            chrono.ChVector3d(0, 0, -p.resistance_rotation * omega(u.corps)), False)


def appliquer_magnetisme(robots, p):
    if not p.magnetisme_actif or p.liaison_ideale:
        return 0.0, 0.0
    aimants = [(i, *u.aimant(actif, p)) for i, u in enumerate(robots) for actif in (True, False)]
    cylindres = None
    if p.modele_magnetique == 'cylindres':
        from magnet_cylinders import pour_parametres
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


def mesure(t, sys, robots, p):
    sys.GetContactContainer().ComputeContactForces()
    row = {"t_s": t, "contacts_total_sol_compris": sys.GetNumContacts()}
    for nom, u in zip(noms(robots), robots):
        pos, vel = u.corps.GetPos(), u.corps.GetPosDt()
        row.update({f"{nom}_x_m": pos.x, f"{nom}_y_m": pos.y, f"{nom}_z_m": pos.z,
                    f"{nom}_angle_corps_rad": angle(u.corps),
                    f"{nom}_angle_actif_rad": angle(u.actif), f"{nom}_angle_libre_rad": angle(u.libre),
                    f"{nom}_omega_corps_rad_s": omega(u.corps),
                    f"{nom}_omega_actif_relative_rad_s": omega(u.actif) - omega(u.corps),
                    f"{nom}_omega_libre_relative_rad_s": omega(u.libre) - omega(u.corps),
                    f"{nom}_vitesse_m_s": math.hypot(vel.x, vel.y),
                    f"{nom}_tension_V": u.tension, f"{nom}_courant_A": u.courant,
                    f"{nom}_couple_moteur_Nm": u.couple_moteur,
                    f"{nom}_couple_transmis_Nm": u.couple_transmis})
        pieces = [('corps', u.corps), ('actif', u.actif), ('libre', u.libre)]
        if u.roue is not None:
            pieces.append(('roue_libre', u.roue))
        for piece, b in pieces:
            force, couple = b.GetContactForce(), b.GetContactTorque()
            for axe, val in zip('xyz', xyz(force)):
                row[f'{nom}_contact_{piece}_F{axe}_N'] = val
            row[f'{nom}_contact_{piece}_couple_z_Nm'] = couple.z
        if u.roue is not None:
            row[f'{nom}_omega_roue_libre_rad_s'] = omega(u.roue)
            row[f'{nom}_angle_roue_libre_rad'] = angle(u.roue)
    for i, j in paires(robots):
        a, b = robots[i].corps.GetPos(), robots[j].corps.GetPos()
        row[f"{noms(robots)[i]}{noms(robots)[j]}_distance_m"] = math.hypot(b.x - a.x, b.y - a.y)
    if not all(math.isfinite(v) for v in row.values()):
        raise RuntimeError("État non fini : vérifier les paramètres et réduire dt")
    return row


def animation(rows, p, sortie):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.patches import Circle
    # Le CSV est enregistré à 200 Hz ; la vidéo reste à 25 images/s.
    temps = [r['t_s'] for r in rows]
    selection = []
    for k in range(round(temps[-1] * p.fps) + 1):
        cible = k / p.fps
        i = min(bisect_left(temps, cible), len(rows) - 1)
        if i and abs(temps[i-1] - cible) < abs(temps[i] - cible):
            i -= 1
        selection.append(rows[i])
    rows = selection
    NOMS = tuple(chr(ord("A") + i) for i in range(p.nombre_robots))
    fig, ax = plt.subplots(figsize=(7, 7))
    xs = [r[f"{n}_x_m"] for r in rows for n in NOMS]
    ys = [r[f"{n}_y_m"] for r in rows for n in NOMS]
    xc, yc = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    lim = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 1.5 * p.R
    ax.set(xlim=(xc - lim, xc + lim), ylim=(yc - lim, yc + lim),
           xlabel="x (m)", ylabel="y (m)", aspect="equal")
    cercles, reperes, traces, actifs, libres, etiquettes = [], [], [], [], [], []
    for i, n in enumerate(NOMS):
        c = f"C{i}"
        cercle = Circle((0, 0), p.R, facecolor=c, edgecolor=c, alpha=0.2)
        ax.add_patch(cercle)
        cercles.append(cercle)
        reperes.append(ax.plot([], [], color=c, lw=2, label="Orientation du corps" if i == 0 else None)[0])
        traces.append(ax.plot([], [], ":", color=c, alpha=0.6)[0])
        for liste, couleur, etiquette in ((actifs, 'red', 'Aimant motorisé'),
                                           (libres, 'blue', 'Aimant libre')):
            aimant = Circle((0, 0), p.diametre_aimant_ext / 2, facecolor=couleur,
                            edgecolor='black', lw=0.7, alpha=0.85,
                            label=etiquette if i == 0 else None)
            ax.add_patch(aimant)
            liste.append(aimant)
        etiquettes.append(ax.text(0, 0, n, ha="center", va="center"))
    ax.legend(loc="upper right", fontsize=8)
    titre = ax.set_title("")

    def maj(k):
        r = rows[k]
        for i, n in enumerate(NOMS):
            x, y, a = r[f"{n}_x_m"], r[f"{n}_y_m"], r[f"{n}_angle_corps_rad"]
            cercles[i].center = (x, y)
            reperes[i].set_data([x, x + p.R * math.cos(a)], [y, y + p.R * math.sin(a)])
            traces[i].set_data([e[f"{n}_x_m"] for e in rows[:k + 1]],
                               [e[f"{n}_y_m"] for e in rows[:k + 1]])
            for artiste, suffixe in ((actifs[i], "actif"), (libres[i], "libre")):
                # Position exacte enregistrée, même si le pivot dérive numériquement.
                artiste.center = (r[f"{n}_aimant_{suffixe}_x_m"],
                                   r[f"{n}_aimant_{suffixe}_y_m"])
            etiquettes[i].set_position((x, y))
        titre.set_text(f"{p.nombre_robots} granulobots — commande en {p.mode_moteur}\nt = {r['t_s']:.2f} s")
        return (*cercles, *reperes, *traces, *actifs, *libres, *etiquettes, titre)

    anim = FuncAnimation(fig, maj, frames=len(rows), interval=1000 / p.fps)
    anim.save(sortie.with_suffix(".gif"), writer=PillowWriter(fps=p.fps))
    plt.close(fig)


def simuler(p, sortie, gif=True, verbose=True):
    p.verifier()
    sys, robots, references = creer_systeme(p)
    NOMS = noms(robots)
    rows, min_distances = [], {paire: 2 * p.R for paire in paires(robots)}
    force_max, vitesse_max, energie_elec = 0.0, 0.0, 0.0
    periode = max(1, round(1 / (p.frequence_mesures * p.dt)))
    nsteps = round(p.duree / p.dt)
    if verbose:
        print(f"Mode={p.mode_moteur}, dt={p.dt:g} s, durée={p.duree:g} s", flush=True)
        print(f"Masse totale/unité={p.M:g} kg ; moment estimé/aimant={p.moment_aimant:.3f} A.m²", flush=True)
    positions_initiales = [xyz(u.corps.GetPos()) for u in robots]
    for k in range(nsteps + 1):
        t = sys.GetChTime()
        if k % periode == 0 or k == nsteps:
            row = mesure(t, sys, robots, p)
            for n, u in zip(noms(robots), robots):
                for actif, suffixe in ((True, "actif"), (False, "libre")):
                    _, _, pos, _ = u.aimant(actif, p)
                    row[f"{n}_aimant_{suffixe}_x_m"] = pos[0]
                    row[f"{n}_aimant_{suffixe}_y_m"] = pos[1]
            rows.append(row)
        for i, j in paires(robots):
            a, b = robots[i].corps.GetPos(), robots[j].corps.GetPos()
            min_distances[i, j] = min(min_distances[i, j], math.hypot(b.x - a.x, b.y - a.y))
        vitesse_max = max(vitesse_max, *(abs(omega(u.corps)) for u in robots))
        if k == nsteps:
            break
        for i, u in enumerate(robots):
            u.vider_forces()
            appliquer_moteur(u, i, t, p)
        _, fm = appliquer_magnetisme(robots, p)
        force_max = max(force_max, fm)
        energie_elec += sum(u.tension * u.courant for u in robots) * p.dt
        sys.DoStepDynamics(p.dt)
        if verbose and (k + 1) % max(1, round(0.5 / p.dt)) == 0:
            print(f"t={sys.GetChTime():.2f} s  contacts(sol compris)={sys.GetNumContacts()}  "
                  f"vitesses corps={[round(omega(u.corps), 3) for u in robots]} rad/s", flush=True)
    bilan = {
        "recouvrement_max_m": {NOMS[i] + NOMS[j]: max(0, 2 * p.R - d) for (i, j), d in min_distances.items()},
        "omega_corps_max_rad_s": vitesse_max, "force_aimant_max_N": force_max,
        "energie_electrique_signee_J": energie_elec,
        "deplacement_final_m": {n: math.hypot(u.corps.GetPos().x - pos[0], u.corps.GetPos().y - pos[1])
                                for n, u, pos in zip(NOMS, robots, positions_initiales)},
        "vitesse_actif_final_rad_s": {n: omega(u.actif) - omega(u.corps) for n, u in zip(noms(robots), robots)},
        "duree_simulee_s": sys.GetChTime(),
    }
    from diagnostic_accrochage import analyser
    bilan["accrochage"] = analyser(rows, p)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with sortie.with_suffix(".csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    hypotheses = {
        "geometrie": {
            "rayon_m": p.R, "hauteur_m": p.H,
            "seconde_roue_libre": p.roue_libre_exterieure,
            "epaisseur_jante_estimee_m": p.epaisseur_roue,
            "roue_motorisee_en_bas_hypothese": p.roue_motorisee_en_bas,
            "vue": "Partie motorisée seulement ; axes verticaux, basculement bloqué",
        },
        "prototype": "La masse totale et les paramètres moteur de l'article ne sont pas encore mesurés sur ce prototype",
        "projection_plane": "Centres de masse et contacts latéraux dans un plan commun ; forces XY et couples Z conservés, moments de basculement omis ; hauteurs des formes conservées pour le sol Bullet",
        "moteur": "Électricité quasi stationnaire, inductance et inertie réfléchie du moteur omises",
        "contact": "NSC latéral avec faible compliance estimée plastique/métal pour régulariser les contacts affleurants ; zéro = référence rigide. Support disque équivalent (normal, Coulomb translation, torsion mu*N*2R/3) ou Bullet ; limites translation/torsion séparées, à calibrer en mouvement combiné",
        "aimants": "Diamètre 8 mm, hauteur 10 mm, tranche affleurante et pôles axiaux estimés/confirmés par Hugo ; remanence et trou à confirmer ; cylindres uniformément aimantés par quadrature des faces ou dipôles de comparaison ; centres magnétiques coplanaires dans le modèle fini",
        "frottement": "Frottement interne lissé ; pas de seuil statique exact ; support réel à préciser",
        "liaison_ideale": p.liaison_ideale,
        "validation": "Comparer plusieurs dt et calibrer les forces avant une comparaison quantitative",
        "sources": ["01_Sujet_et_rapports/scirobotics.adh4130.txt, prototype et fig. 8",
                    "https://api.projectchrono.org/motors.html",
                    "https://api.projectchrono.org/10.0.0/tutorial_demo_friction.html"],
    }
    sortie.with_suffix(".json").write_text(json.dumps({"parametres": p.dictionnaire(),
                                                      "hypotheses": hypotheses, "bilan": bilan},
                                                     indent=2, ensure_ascii=False), encoding="utf-8")
    if gif:
        animation(rows, p, sortie)
    if verbose:
        print(json.dumps(bilan, indent=2, ensure_ascii=False), flush=True)
        print(f"Résultats : {sortie} (.csv, .json" + (", .gif)" if gif else ")"), flush=True)
    return rows, bilan


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--robots", type=int, choices=(2, 3))
    parser.add_argument("--liaison-ideale", action="store_true")
    parser.add_argument("--parametres", type=Path, help="JSON de paramètres mesurés/estimés")
    parser.add_argument("--duree", type=float)
    parser.add_argument("--dt", type=float)
    parser.add_argument("--mode", choices=("tension", "vitesse", "couple"))
    parser.add_argument("--tensions", type=float, nargs=3, metavar=("A", "B", "C"))
    parser.add_argument("--vitesses", type=float, nargs=3, metavar=("A", "B", "C"))
    parser.add_argument("--sans-moteurs", action="store_true")
    parser.add_argument("--sans-magnetisme", action="store_true")
    parser.add_argument("--sans-sol", action="store_true")
    parser.add_argument("--sans-gif", action="store_true")
    parser.add_argument("--rejouer", type=Path, help="Régénérer le GIF d'un CSV sans refaire la dynamique")
    parser.add_argument("--sortie", type=Path)
    args = parser.parse_args()
    if args.rejouer:
        meta = json.loads(args.rejouer.with_suffix('.json').read_text(encoding='utf-8'))
        p = Parametres(**meta['parametres'])
        with args.rejouer.open(encoding='utf-8') as f:
            rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
        animation(rows, p, args.sortie or args.rejouer.with_suffix(''))
        print('GIF régénéré à partir des mesures, sans refaire la dynamique.', flush=True)
        return
    p = PARAMETRES
    if args.parametres:
        donnees = json.loads(args.parametres.read_text(encoding="utf-8"))
        for cle, valeur in donnees.get("parametres", donnees).items():
            if cle not in p.dictionnaire():
                raise ValueError(f"Paramètre inconnu : {cle}")
            setattr(p, cle, valeur)
    if args.robots is not None:
        p.nombre_robots = args.robots
    p.liaison_ideale = p.liaison_ideale or args.liaison_ideale
    for option, attribut in ((args.duree, "duree"), (args.dt, "dt"), (args.mode, "mode_moteur"),
                            (args.tensions, "tensions_cibles"), (args.vitesses, "vitesses_cibles")):
        if option is not None:
            setattr(p, attribut, tuple(option) if isinstance(option, list) else option)
    p.moteur_actif = not args.sans_moteurs and p.moteur_actif
    p.magnetisme_actif = not args.sans_magnetisme and p.magnetisme_actif
    p.sol_actif = not args.sans_sol and p.sol_actif
    simuler(p, args.sortie or Path(__file__).with_suffix(''), not args.sans_gif)


if __name__ == "__main__":
    main()
