"""Measurements of a run (CSV rows at 200 Hz) and writing of the CSV/JSON outputs.

Column names, JSON keys and the assumption texts are still in French; spec 005
translates them.
"""
import csv
import json
import math

from granulobot.chrono_env import angle, omega, xyz
from granulobot.model.unit import unit_names, unit_pairs


def measure(t, sys, units, p):
    sys.GetContactContainer().ComputeContactForces()
    row = {"t_s": t, "contacts_total_sol_compris": sys.GetNumContacts()}
    for name, u in zip(unit_names(units), units):
        pos, vel = u.body.GetPos(), u.body.GetPosDt()
        row.update({f"{name}_x_m": pos.x, f"{name}_y_m": pos.y, f"{name}_z_m": pos.z,
                    f"{name}_angle_corps_rad": angle(u.body),
                    f"{name}_angle_actif_rad": angle(u.active), f"{name}_angle_libre_rad": angle(u.free),
                    f"{name}_omega_corps_rad_s": omega(u.body),
                    f"{name}_omega_actif_relative_rad_s": omega(u.active) - omega(u.body),
                    f"{name}_omega_libre_relative_rad_s": omega(u.free) - omega(u.body),
                    f"{name}_vitesse_m_s": math.hypot(vel.x, vel.y),
                    f"{name}_tension_V": u.voltage, f"{name}_courant_A": u.current,
                    f"{name}_couple_moteur_Nm": u.motor_torque,
                    f"{name}_couple_transmis_Nm": u.transmitted_torque})
        parts = [('corps', u.body), ('actif', u.active), ('libre', u.free)]
        if u.wheel is not None:
            parts.append(('roue_libre', u.wheel))
        for part, b in parts:
            force, torque = b.GetContactForce(), b.GetContactTorque()
            for axis, val in zip('xyz', xyz(force)):
                row[f'{name}_contact_{part}_F{axis}_N'] = val
            row[f'{name}_contact_{part}_couple_z_Nm'] = torque.z
        if u.wheel is not None:
            row[f'{name}_omega_roue_libre_rad_s'] = omega(u.wheel)
            row[f'{name}_angle_roue_libre_rad'] = angle(u.wheel)
    for i, j in unit_pairs(units):
        a, b = units[i].body.GetPos(), units[j].body.GetPos()
        row[f"{unit_names(units)[i]}{unit_names(units)[j]}_distance_m"] = math.hypot(b.x - a.x, b.y - a.y)
    if not all(math.isfinite(v) for v in row.values()):
        raise RuntimeError("Non-finite state: check the parameters and reduce dt")
    return row


def assumptions(p):
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


def write_outputs(rows, p, summary, output):
    """Write <output>.csv (one row per measurement) and <output>.json (parameters, assumptions, summary)."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix(".csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    output.with_suffix(".json").write_text(json.dumps({"parametres": p.dictionnaire(),
                                                       "hypotheses": assumptions(p), "bilan": summary},
                                                      indent=2, ensure_ascii=False), encoding="utf-8")
