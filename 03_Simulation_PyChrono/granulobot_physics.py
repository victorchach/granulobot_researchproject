"""Lois physiques indépendantes de PyChrono ; toutes les unités sont SI.

Dipôles ponctuels avec potentiel régularisé : approximation des aimants finis,
non valable comme prédiction quantitative à très courte distance sans calibration.
Moteur CC en régime électrique quasi stationnaire (inductance négligée).
"""
from dataclasses import dataclass, asdict
import math


@dataclass
class Parametres:
    nombre_robots: int = 3                       # 2 : banc d'essai ; 3 : triangle
    liaison_ideale: bool = False                 # référence cinématique, PAS modèle réel
    perturbation_rotor_rad: float = 0.0          # rotor actif A, test de rappel passif
    marge_detection_decrochage: float = 0.003     # critère diagnostic, pas loi physique
    # Mesures fournies par Hugo ; M reste à peser sur le prototype actuel.
    R: float = 0.035                 # rayon extérieur (m)
    H: float = 0.050                 # hauteur (m)
    M: float = 0.098                 # masse TOTALE, rotors compris (kg)
    roue_libre_exterieure: bool = True           # mécanique confirmée : seconde roue libre
    masse_roue_libre: float = 0.008              # estimation incluse dans M
    epaisseur_roue: float = 0.004                # épaisseur des deux jantes, à mesurer
    roue_motorisee_en_bas: bool = True          # disposition de l'article, à vérifier
    couple_frottement_roue: float = 0.0001       # roulement roue/corps, estimation N.m
    viscosite_roue: float = 0.00001              # N.m.s/rad
    # Répartition estimée ; masse/inertie du rotor actif issues de la fig. 8.
    masse_actif: float = 0.036
    masse_libre: float = 0.010
    inertie_actif_pivot: float = 0.036 * 0.020**2  # kg.m²
    inertie_libre_pivot: float = 0.010 * 0.020**2  # estimation
    excentricite_actif: float = 0.008             # COM décalé, estimation (m)
    excentricite_libre: float = 0.004             # estimation (m)
    facteur_inertie_corps: float = 0.65           # Izz = facteur * M_corps * R²
    # Contact NSC avec compliance paramétrable ; pas de force de ressort ajoutée.
    mu_robots: float = 0.6                       # à mesurer
    compliance_coques: float = 1e-7             # m/N par matériau, plastique estimé
    compliance_aimants: float = 1e-8             # m/N par matériau, métal estimé
    # Faible déformation NSC : partage de charge entre contacts affleurants.
    # Mettre les deux à zéro reproduit la référence parfaitement rigide.
    restitution: float = 0.0
    roulement_contact: float = 0.0               # résistance au roulement NSC, option
    pivotement_contact: float = 0.0             # résistance au pivotement NSC, option
    enveloppe_collision: float = 1e-5            # paramètre numérique (m)
    marge_collision: float = 1e-5
    # Sol réel : gravité + réaction normale + Coulomb calculés par Chrono.
    sol_actif: bool = True
    modele_sol: str = 'disque_equivalent'        # contact NSC central + résistance torsion
    facteur_rayon_frottement_sol: float = 2/3    # disque à pression uniforme : R_eff=2R/3
    gravite: float = 9.81
    mu_sol: float = 0.10                         # estimation, support à préciser
    largeur_sol: float = 2.0                     # m
    epaisseur_sol: float = 0.05
    # Résistances supplémentaires, désactivées pour éviter de doubler Coulomb.
    resistance_translation: float = 0.0          # N.s/m, option air/fluide/support
    resistance_rotation: float = 0.0             # N.m.s/rad
    # Moteur de l'article, fig. 8D ; à recalibrer pour le moteur utilisé.
    moteur_actif: bool = True
    mode_moteur: str = "tension"                 # tension, vitesse, couple
    rapport_reduction: float = 379.0
    kt: float = 5.8e-3                           # N.m/A, AVANT réducteur
    ke: float = 2.65e-3                          # V.s/rad, AVANT réducteur
    resistance_moteur: float = 9.6               # ohms
    rendement_reducteur: float = 1.0             # modèle ajusté de l'article
    tension_max: float = 6.0
    courant_max: float = 0.4                     # limite estimée, à mesurer
    couple_max: float = 0.10                     # protection mécanique estimée
    vitesses_cibles: tuple = (math.pi, math.pi, math.pi)  # 1 tour/2 s, mode vitesse
    tensions_cibles: tuple = (3.25, 3.25, 3.25)  # estimation ~30 tr/min à vide
    couples_cibles: tuple = (5e-5, 5e-5, 5e-5)  # N.m, mode couple seulement
    gain_p_vitesse: float = 1.0                  # V / (rad/s), estimation
    gain_i_vitesse: float = 0.5                  # V / rad, estimation
    rampe_demarrage: float = 0.5                 # s
    # Frottement sec régularisé : oppose la vitesse, pas de vrai blocage statique.
    frottement_interne_actif: bool = True
    couple_frottement_actif: float = 0.024       # N.m, article fig. 8
    couple_frottement_libre: float = 0.0002      # N.m, estimation roulement
    viscosite_libre: float = 0.0001              # N.m.s/rad, estimation
    vitesse_regularisation: float = 0.05        # rad/s, numérique, à raffiner
    # Aimants cylindriques : diamètre/affleurement estimés par Hugo ;
    # hauteur 10 mm et pôles axiaux fournis ; perçage et rémanence à confirmer.
    magnetisme_actif: bool = True
    contact_aimants: bool = True                 # contact latéral, aimants entre unités
    orientation_aimant: str = 'axiale'           # pôles sur faces plates confirmés par Hugo
    modele_magnetique: str = 'cylindres'          # cylindres finis ou dipoles de comparaison
    quadrature_radiale: int = 4                 # précision des faces aimantées
    quadrature_angulaire: int = 16
    mu_aimants: float = 0.05                     # estimation, indépendant des coques
    diametre_aimant_ext: float = 0.008            # estimation donnée par Hugo
    diametre_aimant_int: float = 0.0             # plein supposé ; trou éventuel à confirmer
    epaisseur_aimant: float = 0.010              # estimation donnée par Hugo
    remanence: float = 1.45                      # T, estimation N54
    facteur_moment: float = 1.0                  # calibration du moment effectif
    retrait_aimant: float = 0.0                  # tranche affleurante confirmée par Hugo
    adoucissement_magnetique: float = 0.0002     # numérique, à vérifier par convergence
    interactions_internes: bool = False         # aimants du même robot, à étudier
    # Dipôles supposés solidaires de leur rotor ; rotation propre de l'aimant omise.
    # Triangle, moteurs indépendants ; pas de lien permanent entre voisins.
    jeu_initial: float = 5e-5                    # m entre les coques
    dt: float = 1e-5                            # s, résout le freinage moteur raide
    duree: float = 3.0
    fps: int = 25                               # 40 ms : exact au format GIF
    frequence_mesures: int = 200                # données distinctes du rythme vidéo
    iterations_solveur: int = 1000
    solveur: str = 'PSOR'                      # PSOR ou APGD, comparaison numérique
    tolerance_solveur: float = 1e-9
    vitesse_correction_contact: float = 10.0     # m/s, plafond NUMÉRIQUE, pas une vitesse imposée
    # Avec compliance Ctot, ce plafond borne aussi N ~ v_max*dt/Ctot.
    # L'ancienne valeur 0.05 plafonnait les coques à 2.5 N au pas 1e-5 s,
    # insuffisant sous ~12 N magnétiques. 10 évite ce bridage dans les essais.

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
            raise ValueError("Le banc accepte deux ou trois granulobots")
        if self.solveur not in ('PSOR', 'APGD'):
            raise ValueError('solveur : PSOR ou APGD')
        if self.modele_sol not in ('disque_equivalent', 'bullet'):
            raise ValueError('modele_sol : disque_equivalent ou bullet')
        if self.orientation_aimant not in ('radiale', 'axiale'):
            raise ValueError('orientation_aimant : radiale ou axiale')
        if self.modele_magnetique not in ('cylindres', 'dipoles'):
            raise ValueError('modele_magnetique : cylindres ou dipoles')
        if self.modele_magnetique == 'cylindres' and self.orientation_aimant != 'axiale':
            raise ValueError('Le modèle de cylindres nécessite une aimantation axiale')
        if self.quadrature_radiale < 1 or self.quadrature_angulaire < 4:
            raise ValueError('Quadrature magnétique invalide')
        if self.adoucissement_magnetique >= self.diametre_aimant_ext * math.sqrt(2 / 3):
            raise ValueError('Adoucissement trop grand : la force radiale peut changer de signe au contact')
        for nom in ("R", "H", "M", "masse_actif", "masse_libre", "dt", "duree",
                    "fps", "resistance_moteur", "rapport_reduction", "kt", "ke",
                    "vitesse_regularisation", "adoucissement_magnetique",
                    "tension_max", "courant_max", "couple_max", "largeur_sol"):
            if not math.isfinite(getattr(self, nom)) or getattr(self, nom) <= 0:
                raise ValueError(f"{nom} doit être positif et fini")
        if self.masse_corps <= 0 or self.rayon_aimant <= 0:
            raise ValueError("Répartition des masses ou géométrie des aimants impossible")
        if self.roue_libre_exterieure and (not 0 < self.epaisseur_roue < self.H / 2
                                         or not 0 < self.masse_roue_libre < self.M):
            raise ValueError("Masse ou épaisseur de la roue libre invalide")
        for masse, inertie, excentricite in (
                (self.masse_actif, self.inertie_actif_pivot, self.excentricite_actif),
                (self.masse_libre, self.inertie_libre_pivot, self.excentricite_libre)):
            if excentricite < 0 or inertie <= masse * excentricite**2:
                raise ValueError("L'inertie au pivot doit dépasser masse * excentricité²")
        if self.mode_moteur not in ("vitesse", "tension", "couple"):
            raise ValueError("mode_moteur : vitesse, tension ou couple")
        for cibles in (self.vitesses_cibles, self.tensions_cibles, self.couples_cibles):
            if len(cibles) != 3 or not all(math.isfinite(v) for v in cibles):
                raise ValueError("Il faut trois consignes finies, pour A, B et C")
        for nom in ("mu_robots", "mu_sol", "gravite", "resistance_translation",
                    "resistance_rotation", "couple_frottement_actif",
                    "couple_frottement_libre", "viscosite_libre", "jeu_initial",
                    "rampe_demarrage", "facteur_moment", "roulement_contact",
                    "pivotement_contact", "mu_aimants", "retrait_aimant",
                    "marge_detection_decrochage", "compliance_coques", "compliance_aimants",
                    "couple_frottement_roue", "viscosite_roue"):
            if not math.isfinite(getattr(self, nom)) or getattr(self, nom) < 0:
                raise ValueError(f"{nom} doit être positif ou nul")
        if not 0 <= self.restitution <= 1 or not 0 < self.rendement_reducteur <= 1:
            raise ValueError("Restitution ou rendement hors limites")
        if not 0 <= self.diametre_aimant_int < self.diametre_aimant_ext:
            raise ValueError("Diamètres de l'aimant invalides")
        if self.roulement_contact > 0 and self.pivotement_contact == 0:
            raise ValueError("Chrono recommande un pivotement non nul avec le roulement")

    def dictionnaire(self):
        return asdict(self)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def dipoles(r, mi, mj, epsilon):
    """r = position_j - position_i ; retourne F sur j, couples i/j et énergie.

    Force = -gradient_r U. La force sur i vaut -F. Chaque force doit être
    appliquée AU POINT de l'aimant ; les couples retournés sont des couples
    purs (orientation du dipôle), supplémentaires au moment de cette force.
    Le même potentiel adouci sert aux forces et aux couples, sans plafonnement.
    """
    s2 = dot(r, r) + epsilon**2
    s3, s5, s7 = s2**1.5, s2**2.5, s2**3.5
    a, b, c = dot(mi, r), dot(mj, r), dot(mi, mj)
    force = tuple(3e-7 * ((c * rk + b * mik + a * mjk) / s5 -
                         5 * a * b * rk / s7)
                  for rk, mik, mjk in zip(r, mi, mj))
    bi = tuple(1e-7 * (3 * rk * b / s5 - mjk / s3) for rk, mjk in zip(r, mj))
    bj = tuple(1e-7 * (3 * rk * a / s5 - mik / s3) for rk, mik in zip(r, mi))
    return force, cross(mi, bi), cross(mj, bj), 1e-7 * (c / s3 - 3 * a * b / s5)


def frottement(vitesse, sec, visqueux, epsilon):
    """Couple dissipatif lissé ; ne représente pas exactement la friction statique."""
    return -sec * math.tanh(vitesse / epsilon) - visqueux * vitesse


def moteur_cc(tension, vitesse_relative, p):
    """U - Ke * beta * omega = R_elec * I ; couple en sortie du réducteur.

    Le courant peut être négatif : freinage électrique / moteur rétro-entraîné.
    Pas de facteur de rendement supplémentaire caché dans le freinage.
    """
    u = max(-p.tension_max, min(p.tension_max, tension))
    courant = (u - p.ke * p.rapport_reduction * vitesse_relative) / p.resistance_moteur
    courant = max(-p.courant_max, min(p.courant_max, courant))
    gain = p.rendement_reducteur * p.rapport_reduction * p.kt
    couple = max(-p.couple_max, min(p.couple_max, gain * courant))
    # Courant correspondant au couple effectivement transmis après saturation.
    return couple, couple / gain, u
