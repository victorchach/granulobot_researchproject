"""One Granulobot unit: four rigid bodies and their links.

Body (shell), active rotor (active magnet, driven by the motor), free rotor
(free magnet, on a pivot) and outer free wheel (on a pivot). The motor acts
between the active rotor and the body; a guide only blocks tipping.
"""
from dataclasses import dataclass
from itertools import combinations
import math

from granulobot.chrono_env import chrono, xyz


def unit_names(units):
    return tuple(chr(ord("A") + i) for i in range(len(units)))


def unit_pairs(units):
    return tuple(combinations(range(len(units)), 2))


@dataclass
class Unit:
    body: object
    active: object
    free: object
    idx_body: int
    idx_active: int
    idx_free: int
    motor: object
    torque_function: object
    free_pivot: object
    guide: object
    wheel: object = None
    idx_wheel: int = None
    wheel_pivot: object = None
    integral: float = 0.0
    voltage: float = 0.0
    current: float = 0.0
    motor_torque: float = 0.0
    transmitted_torque: float = 0.0

    def magnet(self, active, p):
        b = self.active if active else self.free
        e = p.excentricite_actif if active else p.excentricite_libre
        # The rotor's centre of mass is offset by e from the pivot.
        point = b.TransformPointLocalToParent(chrono.ChVector3d(p.rayon_aimant - e, 0, 0))
        direction = b.TransformDirectionLocalToParent(chrono.ChVector3d(1, 0, 0))
        sign = 1 if active else -1  # opposite polarities, active / free
        moment = ((0, 0, sign * p.moment_aimant) if p.orientation_aimant == 'axiale'
                  else tuple(sign * p.moment_aimant * c for c in xyz(direction)))
        return b, self.idx_active if active else self.idx_free, xyz(point), moment

    def clear_forces(self):
        parts = [(self.body, self.idx_body), (self.active, self.idx_active),
                 (self.free, self.idx_free)]
        if self.wheel is not None:
            parts.append((self.wheel, self.idx_wheel))
        for b, idx in parts:
            b.EmptyAccumulator(idx)

    def dynamic_bodies(self):
        return (self.body, self.active, self.free) + ((self.wheel,) if self.wheel is not None else ())


def create_unit(sys, p, mat, frame, i, positions):
    """Create unit i at positions[i] and add it to the system; body order unchanged."""
    x, y = positions[i]
    pivot = chrono.ChVector3d(x, y, p.H / 2 + p.enveloppe_collision)
    rho = p.masse_corps / (math.pi * p.R**2 * p.H)
    body = chrono.ChBodyEasyCylinder(chrono.ChAxis_Z, p.R, p.H, rho, False, False, mat)
    contact_height = p.epaisseur_roue if p.roue_libre_exterieure else p.H
    z_contact = ((-1 if p.roue_motorisee_en_bas else 1) *
                 (p.H - contact_height) / 2 if p.roue_libre_exterieure else 0)
    body.AddCollisionShape(chrono.ChCollisionShapeCylinder(mat, p.R, contact_height),
                           chrono.ChFramed(chrono.ChVector3d(0, 0, z_contact),
                                           chrono.QuatFromAngleX(math.pi / 2)))
    body.EnableCollision(True)
    body.SetPos(pivot)
    body.SetFixed(False)
    # Contacts between robots are added analytically by the callback.
    body.GetCollisionModel().SetFamily(1)
    body.GetCollisionModel().DisallowCollisionsWith(1)
    body.SetInertiaXX(chrono.ChVector3d(
        p.masse_corps * (3 * p.R**2 + p.H**2) / 12,
        p.masse_corps * (3 * p.R**2 + p.H**2) / 12,
        p.facteur_inertie_corps * p.masse_corps * p.R**2))
    sys.AddBody(body)
    guide = chrono.ChLinkMateGeneric()
    # With a ground: Z free, so the ground carries the weight, not the guide.
    guide.SetConstrainedCoords(False, False, not p.sol_actif, True, True, False)
    guide.Initialize(body, frame, chrono.ChFramed(pivot))
    sys.AddLink(guide)
    rotors = []
    for active in (True, False):
        if p.nombre_robots == 2:
            # One facing pair: active A -> free B.
            # The two other magnets face outwards.
            phi = 0.0 if active else math.pi
        else:
            neighbour = (i + 1) % 3 if active else (i - 1) % 3
            phi = math.atan2(positions[neighbour][1] - y, positions[neighbour][0] - x)
        if active and i == 0:
            phi += p.perturbation_rotor_rad
        mass = p.masse_actif if active else p.masse_libre
        e = p.excentricite_actif if active else p.excentricite_libre
        inertia = p.inertie_actif_pivot if active else p.inertie_libre_pivot
        rotor = chrono.ChBody()
        rotor.SetMass(mass)
        # Parallel axis theorem: the eccentricity is not counted twice.
        icom = inertia - mass * e**2
        rotor.SetInertiaXX(chrono.ChVector3d(icom / 2, icom / 2, icom))
        rotor.SetPos(chrono.ChVector3d(x + e * math.cos(phi), y + e * math.sin(phi), pivot.z))
        rotor.SetRot(chrono.QuatFromAngleZ(phi))
        # Real magnet geometry attached to the rotor. Contact detection is
        # analytic; the solid shells hide the magnet housings.
        shape = chrono.ChCollisionShapeCylinder(mat, p.diametre_aimant_ext / 2,
                                                p.epaisseur_aimant)
        rotor.AddCollisionShape(shape, chrono.ChFramed(
            chrono.ChVector3d(p.rayon_aimant - e, 0, 0),
            chrono.QuatFromAngleX(math.pi / 2)))
        rotor.GetCollisionModel().SetFamilyMask(0)  # No duplicate Bullet contact.
        sys.AddBody(rotor)  # No rotor/shell collision: internal parts.
        rotors.append(rotor)
    motor = chrono.ChLinkMotorRotationTorque()
    motor.Initialize(rotors[0], body, chrono.ChFramed(pivot))
    torque_function = chrono.ChFunctionConst(0)
    motor.SetTorqueFunction(torque_function)
    sys.AddLink(motor)
    free_pivot = chrono.ChLinkLockRevolute()
    free_pivot.Initialize(rotors[1], body, chrono.ChFramed(pivot))
    sys.AddLink(free_pivot)
    unit = Unit(body, *rotors, body.AddAccumulator(),
                rotors[0].AddAccumulator(), rotors[1].AddAccumulator(),
                motor, torque_function, free_pivot, guide)
    if p.roue_libre_exterieure:
        rho_wheel = p.masse_roue_libre / (math.pi * p.R**2 * p.epaisseur_roue)
        wheel = chrono.ChBodyEasyCylinder(chrono.ChAxis_Z, p.R, p.epaisseur_roue,
                                         rho_wheel, False, True, mat)
        z = pivot.z + (1 if p.roue_motorisee_en_bas else -1) * (p.H-p.epaisseur_roue)/2
        # Virtual COM in the common plane: equivalent for XY/yaw, without an
        # artificial vertical lever arm in the guide constraints.
        wheel.SetPos(pivot)
        wheel.GetCollisionModel().Clear()
        wheel.AddCollisionShape(chrono.ChCollisionShapeCylinder(mat, p.R, p.epaisseur_roue),
                                chrono.ChFramed(chrono.ChVector3d(0, 0, z-pivot.z),
                                                chrono.QuatFromAngleX(math.pi/2)))
        wheel.GetCollisionModel().SetFamily(1)
        wheel.GetCollisionModel().DisallowCollisionsWith(1)
        sys.AddBody(wheel)
        wheel_pivot = chrono.ChLinkLockRevolute()
        wheel_pivot.Initialize(wheel, body, chrono.ChFramed(pivot))
        sys.AddLink(wheel_pivot)
        unit.wheel, unit.wheel_pivot = wheel, wheel_pivot
        unit.idx_wheel = wheel.AddAccumulator()
    return unit
