"""Moteur CC et frottements internes d'une unité.

Moteur CC en régime électrique quasi stationnaire (inductance négligée).
appliquer_moteur calcule le couple de chaque unité à chaque pas et l'applique
entre le rotor actif et le corps, avec les frottements des pièces libres.
"""
import math

from granulobot.chrono_env import chrono, omega


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
