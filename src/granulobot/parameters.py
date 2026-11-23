"""Parameters: every physical and numerical setting, in SI units, with its origin.

The laws that use them live in granulobot.model (motor.py, magnets.py).
"""
from dataclasses import dataclass, asdict
import math


@dataclass
class Parameters:
    n_units: int = 3                       # 2: test bench; 3: triangle
    ideal_link: bool = False                 # kinematic reference, NOT a real model
    rotor_perturbation_rad: float = 0.0          # active rotor of A, passive restoring test
    detachment_margin: float = 0.003     # diagnostic criterion, not a physical law
    # Measurements provided by Hugo; M is still to be weighed on the current prototype.
    R: float = 0.035                 # outer radius (m)
    H: float = 0.050                 # height (m)
    M: float = 0.098                 # TOTAL mass, rotors included (kg)
    outer_free_wheel: bool = True           # confirmed mechanics: second free wheel
    wheel_mass: float = 0.008              # estimate, included in M
    wheel_thickness: float = 0.004                # thickness of both rims, to measure
    motorised_wheel_at_bottom: bool = True          # layout from the paper, to check
    wheel_friction_torque: float = 0.0001       # wheel/body bearing, estimate N.m
    wheel_viscosity: float = 0.00001              # N.m.s/rad
    # Estimated split; active rotor mass/inertia from fig. 8.
    active_rotor_mass: float = 0.036
    free_rotor_mass: float = 0.010
    active_rotor_inertia: float = 0.036 * 0.020**2  # kg.m²
    free_rotor_inertia: float = 0.010 * 0.020**2  # estimate
    active_rotor_eccentricity: float = 0.008             # offset COM, estimate (m)
    free_rotor_eccentricity: float = 0.004             # estimate (m)
    body_inertia_factor: float = 0.65           # Izz = factor * M_body * R²
    # NSC contact with configurable compliance; no added spring force.
    mu_shells: float = 0.6                       # to measure
    compliance_shells: float = 1e-7             # m/N per material, plastic estimate
    compliance_magnets: float = 1e-8             # m/N per material, metal estimate
    # Small NSC deformation: load sharing between flush contacts.
    # Setting both to zero gives back the perfectly rigid reference.
    restitution: float = 0.0
    rolling_resistance: float = 0.0               # NSC rolling resistance, optional
    spinning_resistance: float = 0.0             # NSC spinning resistance, optional
    collision_envelope: float = 1e-5            # numerical parameter (m)
    collision_margin: float = 1e-5
    # Real ground: gravity + normal reaction + Coulomb computed by Chrono.
    ground_enabled: bool = True
    ground_model: str = 'equivalent_disc'        # central NSC contact + torsion resistance
    ground_friction_radius_factor: float = 2/3    # uniform-pressure disc: R_eff=2R/3
    gravity: float = 9.81
    mu_ground: float = 0.10                         # estimate, support to be specified
    ground_width: float = 2.0                     # m
    ground_thickness: float = 0.05
    # Extra resistances, off so that Coulomb is not counted twice.
    translation_damping: float = 0.0          # N.s/m, optional air/fluid/support
    rotation_damping: float = 0.0             # N.m.s/rad
    # Motor from the paper, fig. 8D; to recalibrate for the motor actually used.
    motors_enabled: bool = True
    motor_mode: str = "voltage"                 # voltage, speed, torque
    gear_ratio: float = 379.0
    kt: float = 5.8e-3                           # N.m/A, BEFORE the gearbox
    ke: float = 2.65e-3                          # V.s/rad, BEFORE the gearbox
    motor_resistance: float = 9.6               # ohms
    gear_efficiency: float = 1.0             # fitted model from the paper
    max_voltage: float = 6.0
    max_current: float = 0.4                     # estimated limit, to measure
    max_torque: float = 0.10                     # estimated mechanical protection
    target_speeds: tuple = (math.pi, math.pi, math.pi)  # 1 turn/2 s, speed mode
    target_voltages: tuple = (3.25, 3.25, 3.25)  # estimate ~30 rpm without load
    target_torques: tuple = (5e-5, 5e-5, 5e-5)  # N.m, torque mode only
    speed_gain_p: float = 1.0                  # V / (rad/s), estimate
    speed_gain_i: float = 0.5                  # V / rad, estimate
    startup_ramp: float = 0.5                 # s
    # Regularised dry friction: opposes the speed, no real static locking.
    internal_friction_enabled: bool = True
    active_friction_torque: float = 0.024       # N.m, paper fig. 8
    free_friction_torque: float = 0.0002      # N.m, bearing estimate
    free_viscosity: float = 0.0001              # N.m.s/rad, estimate
    regularisation_speed: float = 0.05        # rad/s, numerical, to refine
    # Cylindrical magnets: diameter/flush mounting estimated by Hugo;
    # 10 mm height and axial poles provided; hole and remanence to confirm.
    magnetism_enabled: bool = True
    magnet_contact: bool = True                 # side contact between magnets of different units
    magnet_orientation: str = 'axial'           # poles on the flat faces, confirmed by Hugo
    magnet_model: str = 'cylinders'          # finite cylinders, or dipoles for comparison
    radial_quadrature: int = 4                 # accuracy of the magnetised faces
    angular_quadrature: int = 16
    mu_magnets: float = 0.05                     # estimate, independent of the shells
    magnet_outer_diameter: float = 0.008            # estimate given by Hugo
    magnet_inner_diameter: float = 0.0             # assumed solid; possible hole to confirm
    magnet_thickness: float = 0.010              # estimate given by Hugo
    remanence: float = 1.45                      # T, N54 estimate
    moment_factor: float = 1.0                  # calibration of the effective moment
    magnet_recess: float = 0.0                  # flush edge, confirmed by Hugo
    magnetic_softening: float = 0.0002     # numerical, to check by convergence
    internal_interactions: bool = False         # magnets of the same robot, to study
    # Dipoles assumed rigidly attached to their rotor; the magnet's own spin is omitted.
    # Triangle, independent motors; no permanent link between neighbours.
    initial_gap: float = 5e-5                    # m between the shells
    dt: float = 1e-5                            # s, resolves the stiff motor braking
    duration: float = 3.0
    fps: int = 25                               # 40 ms: exact in the GIF format
    sample_rate: int = 200                # data separate from the video rate
    solver_iterations: int = 1000
    solver: str = 'PSOR'                      # PSOR or APGD, numerical comparison
    solver_tolerance: float = 1e-9
    contact_recovery_speed: float = 10.0     # m/s, NUMERICAL cap, not an imposed speed
    # With compliance Ctot, this cap also bounds N ~ v_max*dt/Ctot.
    # The old value 0.05 capped the shells at 2.5 N at dt = 1e-5 s, not enough
    # under ~12 N of magnetic force. 10 avoids this limit in the runs.

    @property
    def body_mass(self):
        return self.M - self.active_rotor_mass - self.free_rotor_mass - (
            self.wheel_mass if self.outer_free_wheel else 0)

    @property
    def magnet_radius(self):
        return self.R - self.magnet_outer_diameter / 2 - self.magnet_recess

    @property
    def magnet_moment(self):
        volume = math.pi / 4 * (self.magnet_outer_diameter**2 -
                               self.magnet_inner_diameter**2) * self.magnet_thickness
        return self.moment_factor * self.remanence * volume / (4 * math.pi * 1e-7)

    def check(self):
        if self.n_units not in (2, 3):
            raise ValueError("The bench accepts two or three granulobots")
        if self.solver not in ('PSOR', 'APGD'):
            raise ValueError('solver: PSOR or APGD')
        if self.ground_model not in ('equivalent_disc', 'bullet'):
            raise ValueError('ground_model: equivalent_disc or bullet')
        if self.magnet_orientation not in ('radial', 'axial'):
            raise ValueError('magnet_orientation: radial or axial')
        if self.magnet_model not in ('cylinders', 'dipoles'):
            raise ValueError('magnet_model: cylinders or dipoles')
        if self.magnet_model == 'cylinders' and self.magnet_orientation != 'axial':
            raise ValueError('The cylinder model needs an axial magnetisation')
        if self.radial_quadrature < 1 or self.angular_quadrature < 4:
            raise ValueError('Invalid magnetic quadrature')
        if self.magnetic_softening >= self.magnet_outer_diameter * math.sqrt(2 / 3):
            raise ValueError('Softening too large: the radial force can change sign at contact')
        for name in ("R", "H", "M", "active_rotor_mass", "free_rotor_mass", "dt", "duration",
                     "fps", "motor_resistance", "gear_ratio", "kt", "ke",
                     "regularisation_speed", "magnetic_softening",
                     "max_voltage", "max_current", "max_torque", "ground_width"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive and finite")
        if self.body_mass <= 0 or self.magnet_radius <= 0:
            raise ValueError("Impossible mass split or magnet geometry")
        if self.outer_free_wheel and (not 0 < self.wheel_thickness < self.H / 2
                                         or not 0 < self.wheel_mass < self.M):
            raise ValueError("Invalid free wheel mass or thickness")
        for mass, inertia, eccentricity in (
                (self.active_rotor_mass, self.active_rotor_inertia, self.active_rotor_eccentricity),
                (self.free_rotor_mass, self.free_rotor_inertia, self.free_rotor_eccentricity)):
            if eccentricity < 0 or inertia <= mass * eccentricity**2:
                raise ValueError("The inertia about the pivot must exceed mass * eccentricity²")
        if self.motor_mode not in ("speed", "voltage", "torque"):
            raise ValueError("motor_mode: speed, voltage or torque")
        for targets in (self.target_speeds, self.target_voltages, self.target_torques):
            if len(targets) != 3 or not all(math.isfinite(v) for v in targets):
                raise ValueError("Three finite set points are needed, for A, B and C")
        for name in ("mu_shells", "mu_ground", "gravity", "translation_damping",
                     "rotation_damping", "active_friction_torque",
                     "free_friction_torque", "free_viscosity", "initial_gap",
                     "startup_ramp", "moment_factor", "rolling_resistance",
                     "spinning_resistance", "mu_magnets", "magnet_recess",
                     "detachment_margin", "compliance_shells", "compliance_magnets",
                     "wheel_friction_torque", "wheel_viscosity"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) < 0:
                raise ValueError(f"{name} must be positive or zero")
        if not 0 <= self.restitution <= 1 or not 0 < self.gear_efficiency <= 1:
            raise ValueError("Restitution or gearbox efficiency out of range")
        if not 0 <= self.magnet_inner_diameter < self.magnet_outer_diameter:
            raise ValueError("Invalid magnet diameters")
        if self.rolling_resistance > 0 and self.spinning_resistance == 0:
            raise ValueError("Chrono recommends a non-zero spinning resistance with rolling resistance")

    def to_dict(self):
        return asdict(self)
