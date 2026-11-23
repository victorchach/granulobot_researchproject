"""Le monde simulé : système NSC, solveur, sol, placement des unités.

creer_systeme renvoie le système, les unités et les objets SWIG à conserver.
La disposition (2 unités face à face ou triangle) est définie ici.
"""
import math

from granulobot.chrono_env import chrono, vect
from granulobot.model.contacts import ContactsCirculaires
from granulobot.model.unit import creer_unite


def appariements(robots):
    return ((0, 1),) if len(robots) == 2 else ((0, 1), (1, 2), (2, 0))


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
    robots = [creer_unite(sys, p, mat, repere, i, positions) for i in range(len(positions))]
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
