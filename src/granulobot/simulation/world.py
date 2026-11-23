"""The simulated world: NSC system, solver, ground, placement of the units.

create_system returns the system, the units and the SWIG objects to keep.
The layout (2 facing units or a triangle) is defined here.
"""
import math

from granulobot.chrono_env import chrono, vect
from granulobot.model.contacts import CircularContacts
from granulobot.model.unit import create_unit


def coupled_pairs(units):
    return ((0, 1),) if len(units) == 2 else ((0, 1), (1, 2), (2, 0))


def create_system(p):
    sys = chrono.ChSystemNSC()
    sys.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)
    sys.SetSolverType({'PSOR': chrono.ChSolver.Type_PSOR,
                      'APGD': chrono.ChSolver.Type_APGD}[p.solveur])
    solver = sys.GetSolver().AsIterative()
    solver.SetMaxIterations(p.iterations_solveur)
    solver.SetTolerance(p.tolerance_solveur)
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
    frame = chrono.ChBody()
    frame.SetFixed(True)
    sys.AddBody(frame)
    ground = None
    if p.sol_actif:
        mat_ground = chrono.ChContactMaterialNSC()
        mat_ground.SetFriction(p.mu_sol)
        mat_ground.SetRestitution(p.restitution)
        mat_ground.SetRollingFriction(p.roulement_contact)
        mat_ground.SetSpinningFriction(p.pivotement_contact)
        ground = chrono.ChBodyEasyBox(p.largeur_sol, p.largeur_sol, p.epaisseur_sol,
                                      1000, False, True, mat_ground)
        ground.SetPos(chrono.ChVector3d(0, 0, -p.epaisseur_sol / 2))
        ground.SetFixed(True)
        if p.modele_sol == 'disque_equivalent':
            ground.GetCollisionModel().SetFamilyMask(0)  # Support added by the callback.
        sys.AddBody(ground)
    side = 2 * p.R + p.jeu_initial
    positions = ((-side / 2, -side / (2 * math.sqrt(3))),
                 (side / 2, -side / (2 * math.sqrt(3))),
                 (0, side / math.sqrt(3)))
    if p.nombre_robots == 2:
        positions = ((-side / 2, 0), (side / 2, 0))
    units = [create_unit(sys, p, mat, frame, i, positions) for i in range(len(positions))]
    links = []
    if p.liaison_ideale:
        # Reference link, rigid and with no breaking threshold. It keeps the
        # relative pose of the two rotors, never their centres on the ground.
        for i, j in coupled_pairs(units):
            _, _, a, _ = units[i].magnet(True, p)
            _, _, b, _ = units[j].magnet(False, p)
            point = vect(tuple((x + y) / 2 for x, y in zip(a, b)))
            link = chrono.ChLinkLockLock()
            link.Initialize(units[i].active, units[j].free, chrono.ChFramed(point))
            sys.AddLink(link)
            links.append(link)
    contacts = CircularContacts(units, mat, p, ground)
    sys.RegisterCustomCollisionCallback(contacts)
    return sys, units, (frame, ground, contacts, links)  # Keep the SWIG references alive.
