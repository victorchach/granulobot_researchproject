"""Mesures d'un run (lignes du CSV à 200 Hz) et écriture des sorties CSV/JSON."""
import csv
import json
import math

from granulobot.chrono_env import angle, omega, xyz
from granulobot.model.unit import noms, paires


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


def hypotheses(p):
    return {
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
        "sources": ["references/scirobotics.adh4130.txt, prototype et fig. 8",
                    "https://api.projectchrono.org/motors.html",
                    "https://api.projectchrono.org/10.0.0/tutorial_demo_friction.html"],
    }


def ecrire_sorties(rows, p, bilan, sortie):
    """Écrit <sortie>.csv (une ligne par mesure) et <sortie>.json (paramètres, hypothèses, bilan)."""
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with sortie.with_suffix(".csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    sortie.with_suffix(".json").write_text(json.dumps({"parametres": p.dictionnaire(),
                                                      "hypotheses": hypotheses(p), "bilan": bilan},
                                                     indent=2, ensure_ascii=False), encoding="utf-8")
