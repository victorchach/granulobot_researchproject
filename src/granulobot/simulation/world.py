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
                      'APGD': chrono.ChSolver.Type_APGD}[p.solver])
    solver = sys.GetSolver().AsIterative()
    solver.SetMaxIterations(p.solver_iterations)
    solver.SetTolerance(p.solver_tolerance)
    sys.SetMaxPenetrationRecoverySpeed(p.contact_recovery_speed)
    sys.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, -p.gravity))
    chrono.ChCollisionModel.SetDefaultSuggestedEnvelope(p.collision_envelope)
    chrono.ChCollisionModel.SetDefaultSuggestedMargin(p.collision_margin)
    mat = chrono.ChContactMaterialNSC()
    mat.SetFriction(p.mu_shells)
    mat.SetRestitution(p.restitution)
    mat.SetCompliance(p.compliance_shells)
    mat.SetRollingFriction(p.rolling_resistance)
    mat.SetSpinningFriction(p.spinning_resistance)
    frame = chrono.ChBody()
    frame.SetFixed(True)
    sys.AddBody(frame)
    ground = None
    if p.ground_enabled:
        mat_ground = chrono.ChContactMaterialNSC()
        mat_ground.SetFriction(p.mu_ground)
        mat_ground.SetRestitution(p.restitution)
        mat_ground.SetRollingFriction(p.rolling_resistance)
        mat_ground.SetSpinningFriction(p.spinning_resistance)
        ground = chrono.ChBodyEasyBox(p.ground_width, p.ground_width, p.ground_thickness,
                                      1000, False, True, mat_ground)
        ground.SetPos(chrono.ChVector3d(0, 0, -p.ground_thickness / 2))
        ground.SetFixed(True)
        if p.ground_model == 'equivalent_disc':
            ground.GetCollisionModel().SetFamilyMask(0)  # Support added by the callback.
        sys.AddBody(ground)
    side = 2 * p.R + p.initial_gap
    positions = ((-side / 2, -side / (2 * math.sqrt(3))),
                 (side / 2, -side / (2 * math.sqrt(3))),
                 (0, side / math.sqrt(3)))
    if p.n_units == 2:
        positions = ((-side / 2, 0), (side / 2, 0))
    units = [create_unit(sys, p, mat, frame, i, positions) for i in range(len(positions))]
    links = []
    if p.ideal_link:
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
