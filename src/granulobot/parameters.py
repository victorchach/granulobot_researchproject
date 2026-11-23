"""Parametres: every physical and numerical setting, in SI units, with its origin.

The laws that use them live in granulobot.model (motor.py, magnets.py).
"""
from dataclasses import dataclass, asdict
import math


@dataclass
class Parametres:
    nombre_robots: int = 3                       # 2: test bench; 3: triangle
    liaison_ideale: bool = False                 # kinematic reference, NOT a real model
    perturbation_rotor_rad: float = 0.0          # active rotor of A, passive restoring test
    marge_detection_decrochage: float = 0.003     # diagnostic criterion, not a physical law
    # Measurements provided by Hugo; M is still to be weighed on the current prototype.
    R: float = 0.035                 # outer radius (m)
    H: float = 0.050                 # height (m)
    M: float = 0.098                 # TOTAL mass, rotors included (kg)
    roue_libre_exterieure: bool = True           # confirmed mechanics: second free wheel
    masse_roue_libre: float = 0.008              # estimate, included in M
    epaisseur_roue: float = 0.004                # thickness of both rims, to measure
    roue_motorisee_en_bas: bool = True          # layout from the paper, to check
    couple_frottement_roue: float = 0.0001       # wheel/body bearing, estimate N.m
    viscosite_roue: float = 0.00001              # N.m.s/rad
    # Estimated split; active rotor mass/inertia from fig. 8.
    masse_actif: float = 0.036
    masse_libre: float = 0.010
    inertie_actif_pivot: float = 0.036 * 0.020**2  # kg.m²
    inertie_libre_pivot: float = 0.010 * 0.020**2  # estimate
    excentricite_actif: float = 0.008             # offset COM, estimate (m)
    excentricite_libre: float = 0.004             # estimate (m)
    facteur_inertie_corps: float = 0.65           # Izz = factor * M_body * R²
    # NSC contact with configurable compliance; no added spring force.
    mu_robots: float = 0.6                       # to measure
    compliance_coques: float = 1e-7             # m/N per material, plastic estimate
    compliance_aimants: float = 1e-8             # m/N per material, metal estimate
    # Small NSC deformation: load sharing between flush contacts.
    # Setting both to zero gives back the perfectly rigid reference.
    restitution: float = 0.0
    roulement_contact: float = 0.0               # NSC rolling resistance, optional
    pivotement_contact: float = 0.0             # NSC spinning resistance, optional
    enveloppe_collision: float = 1e-5            # numerical parameter (m)
    marge_collision: float = 1e-5
    # Real ground: gravity + normal reaction + Coulomb computed by Chrono.
    sol_actif: bool = True
    modele_sol: str = 'disque_equivalent'        # central NSC contact + torsion resistance
    facteur_rayon_frottement_sol: float = 2/3    # uniform-pressure disc: R_eff=2R/3
    gravite: float = 9.81
    mu_sol: float = 0.10                         # estimate, support to be specified
    largeur_sol: float = 2.0                     # m
    epaisseur_sol: float = 0.05
    # Extra resistances, off so that Coulomb is not counted twice.
    resistance_translation: float = 0.0          # N.s/m, optional air/fluid/support
    resistance_rotation: float = 0.0             # N.m.s/rad
    # Motor from the paper, fig. 8D; to recalibrate for the motor actually used.
    moteur_actif: bool = True
    mode_moteur: str = "tension"                 # tension, vitesse, couple
    rapport_reduction: float = 379.0
    kt: float = 5.8e-3                           # N.m/A, BEFORE the gearbox
    ke: float = 2.65e-3                          # V.s/rad, BEFORE the gearbox
    resistance_moteur: float = 9.6               # ohms
    rendement_reducteur: float = 1.0             # fitted model from the paper
    tension_max: float = 6.0
    courant_max: float = 0.4                     # estimated limit, to measure
    couple_max: float = 0.10                     # estimated mechanical protection
    vitesses_cibles: tuple = (math.pi, math.pi, math.pi)  # 1 turn/2 s, speed mode
    tensions_cibles: tuple = (3.25, 3.25, 3.25)  # estimate ~30 rpm without load
    couples_cibles: tuple = (5e-5, 5e-5, 5e-5)  # N.m, torque mode only
    gain_p_vitesse: float = 1.0                  # V / (rad/s), estimate
    gain_i_vitesse: float = 0.5                  # V / rad, estimate
    rampe_demarrage: float = 0.5                 # s
    # Regularised dry friction: opposes the speed, no real static locking.
    frottement_interne_actif: bool = True
    couple_frottement_actif: float = 0.024       # N.m, paper fig. 8
    couple_frottement_libre: float = 0.0002      # N.m, bearing estimate
    viscosite_libre: float = 0.0001              # N.m.s/rad, estimate
    vitesse_regularisation: float = 0.05        # rad/s, numerical, to refine
    # Cylindrical magnets: diameter/flush mounting estimated by Hugo;
    # 10 mm height and axial poles provided; hole and remanence to confirm.
    magnetisme_actif: bool = True
    contact_aimants: bool = True                 # side contact between magnets of different units
    orientation_aimant: str = 'axiale'           # poles on the flat faces, confirmed by Hugo
    modele_magnetique: str = 'cylindres'          # finite cylinders, or dipoles for comparison
    quadrature_radiale: int = 4                 # accuracy of the magnetised faces
    quadrature_angulaire: int = 16
    mu_aimants: float = 0.05                     # estimate, independent of the shells
    diametre_aimant_ext: float = 0.008            # estimate given by Hugo
    diametre_aimant_int: float = 0.0             # assumed solid; possible hole to confirm
    epaisseur_aimant: float = 0.010              # estimate given by Hugo
    remanence: float = 1.45                      # T, N54 estimate
    facteur_moment: float = 1.0                  # calibration of the effective moment
    retrait_aimant: float = 0.0                  # flush edge, confirmed by Hugo
    adoucissement_magnetique: float = 0.0002     # numerical, to check by convergence
    interactions_internes: bool = False         # magnets of the same robot, to study
    # Dipoles assumed rigidly attached to their rotor; the magnet's own spin is omitted.
    # Triangle, independent motors; no permanent link between neighbours.
    jeu_initial: float = 5e-5                    # m between the shells
    dt: float = 1e-5                            # s, resolves the stiff motor braking
    duree: float = 3.0
    fps: int = 25                               # 40 ms: exact in the GIF format
    frequence_mesures: int = 200                # data separate from the video rate
    iterations_solveur: int = 1000
    solveur: str = 'PSOR'                      # PSOR or APGD, numerical comparison
    tolerance_solveur: float = 1e-9
    vitesse_correction_contact: float = 10.0     # m/s, NUMERICAL cap, not an imposed speed
    # With compliance Ctot, this cap also bounds N ~ v_max*dt/Ctot.
    # The old value 0.05 capped the shells at 2.5 N at dt = 1e-5 s, not enough
    # under ~12 N of magnetic force. 10 avoids this limit in the runs.

    @property
    def masse_corps(self):
        return self.M - self.masse_actif - self.masse_libre - (
            self.masse_roue_libre if self.roue_libre_exterieure else 0)

    @property
    def rayon_aimant(self):
        return self.R - self.diametre_aimant_ext / 2 - self.retrait_aimant

    @property
    def moment_aimant(self):
        volume = math.pi / 4 * (self.diametre_aimant_ext**2 -
                               self.diametre_aimant_int**2) * self.epaisseur_aimant
        return self.facteur_moment * self.remanence * volume / (4 * math.pi * 1e-7)

    def verifier(self):
        if self.nombre_robots not in (2, 3):
            raise ValueError("The bench accepts two or three granulobots")
        if self.solveur not in ('PSOR', 'APGD'):
            raise ValueError('solveur: PSOR or APGD')
        if self.modele_sol not in ('disque_equivalent', 'bullet'):
            raise ValueError('modele_sol: disque_equivalent or bullet')
        if self.orientation_aimant not in ('radiale', 'axiale'):
            raise ValueError('orientation_aimant: radiale or axiale')
        if self.modele_magnetique not in ('cylindres', 'dipoles'):
            raise ValueError('modele_magnetique: cylindres or dipoles')
        if self.modele_magnetique == 'cylindres' and self.orientation_aimant != 'axiale':
            raise ValueError('The cylinder model needs an axial magnetisation')
        if self.quadrature_radiale < 1 or self.quadrature_angulaire < 4:
            raise ValueError('Invalid magnetic quadrature')
        if self.adoucissement_magnetique >= self.diametre_aimant_ext * math.sqrt(2 / 3):
            raise ValueError('Softening too large: the radial force can change sign at contact')
        for name in ("R", "H", "M", "masse_actif", "masse_libre", "dt", "duree",
                     "fps", "resistance_moteur", "rapport_reduction", "kt", "ke",
                     "vitesse_regularisation", "adoucissement_magnetique",
                     "tension_max", "courant_max", "couple_max", "largeur_sol"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive and finite")
        if self.masse_corps <= 0 or self.rayon_aimant <= 0:
            raise ValueError("Impossible mass split or magnet geometry")
        if self.roue_libre_exterieure and (not 0 < self.epaisseur_roue < self.H / 2
                                         or not 0 < self.masse_roue_libre < self.M):
            raise ValueError("Invalid free wheel mass or thickness")
        for mass, inertia, eccentricity in (
                (self.masse_actif, self.inertie_actif_pivot, self.excentricite_actif),
                (self.masse_libre, self.inertie_libre_pivot, self.excentricite_libre)):
            if eccentricity < 0 or inertia <= mass * eccentricity**2:
                raise ValueError("The inertia about the pivot must exceed mass * eccentricity²")
        if self.mode_moteur not in ("vitesse", "tension", "couple"):
            raise ValueError("mode_moteur: vitesse, tension or couple")
        for targets in (self.vitesses_cibles, self.tensions_cibles, self.couples_cibles):
            if len(targets) != 3 or not all(math.isfinite(v) for v in targets):
                raise ValueError("Three finite set points are needed, for A, B and C")
        for name in ("mu_robots", "mu_sol", "gravite", "resistance_translation",
                     "resistance_rotation", "couple_frottement_actif",
                     "couple_frottement_libre", "viscosite_libre", "jeu_initial",
                     "rampe_demarrage", "facteur_moment", "roulement_contact",
                     "pivotement_contact", "mu_aimants", "retrait_aimant",
                     "marge_detection_decrochage", "compliance_coques", "compliance_aimants",
                     "couple_frottement_roue", "viscosite_roue"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) < 0:
                raise ValueError(f"{name} must be positive or zero")
        if not 0 <= self.restitution <= 1 or not 0 < self.rendement_reducteur <= 1:
            raise ValueError("Restitution or gearbox efficiency out of range")
        if not 0 <= self.diametre_aimant_int < self.diametre_aimant_ext:
            raise ValueError("Invalid magnet diameters")
        if self.roulement_contact > 0 and self.pivotement_contact == 0:
            raise ValueError("Chrono recommends a non-zero spinning resistance with rolling resistance")

    def dictionnaire(self):
        return asdict(self)
