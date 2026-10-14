"""Mesures d'accrochage depuis le CSV ; aucune dépendance PyChrono.

Le seuil de distance est un indicateur d'éloignement, pas une loi de rupture.
Les événements sont détectés aux instants enregistrés ; le pas réel des
mesures est reporté, indépendamment du nombre d'images du GIF.
Une liaison idéale stable ne démontre pas la validité du modèle magnétique.
"""
import argparse
import csv
import json
import math
from pathlib import Path
from granulobot_physics import Parametres


def derouler(angles):
    cumul = [angles[0]]
    for a, b in zip(angles, angles[1:]):
        cumul.append(cumul[-1] + (b - a + math.pi) % (2 * math.pi) - math.pi)
    return cumul


def analyser(rows, p):
    noms = tuple(chr(65 + i) for i in range(p.nombre_robots))
    apparies = ((0, 1),) if p.nombre_robots == 2 else ((0, 1), (1, 2), (2, 0))
    pas = [b['t_s'] - a['t_s'] for a,b in zip(rows, rows[1:])]
    result = {'resolution_temporelle_s': max(pas) if pas else 0,
              'liaison_ideale': p.liaison_ideale,
              'criteres': {'marge_eloignement_m': p.marge_detection_decrochage,
                          'ratio_rotor_absolu_sur_relatif_pour_retenue': 0.1},
              'unites': {}, 'paires': {}}
    regime = [r for r in rows if r['t_s'] >= p.rampe_demarrage] or rows[-1:]
    for n in noms:
        corps = derouler([r[f'{n}_angle_corps_rad'] for r in rows])
        rotor = derouler([r[f'{n}_angle_actif_rad'] for r in rows])
        libre = derouler([r[f'{n}_angle_libre_rad'] for r in rows])
        r0 = rows[0]
        distances = [math.hypot(r[f'{n}_x_m'] - r0[f'{n}_x_m'],
                               r[f'{n}_y_m'] - r0[f'{n}_y_m']) for r in rows]
        rel = sum(abs(r[f'{n}_omega_actif_relative_rad_s']) for r in regime) / len(regime)
        absolu = sum(abs(r[f'{n}_omega_actif_relative_rad_s'] + r[f'{n}_omega_corps_rad_s'])
                     for r in regime) / len(regime)
        result['unites'][n] = {
            'rotation_corps_nette_tours': (corps[-1] - corps[0]) / (2 * math.pi),
            'rotation_corps_parcourue_tours': sum(abs(b - a) for a, b in zip(corps, corps[1:])) / (2 * math.pi),
            'rotation_rotor_absolue_nette_tours': (rotor[-1] - rotor[0]) / (2 * math.pi),
            'rotation_libre_absolue_nette_tours': (libre[-1] - libre[0]) / (2 * math.pi),
            'deplacement_centre_max_m': max(distances),
            'omega_actif_relative_moyenne_abs_rad_s': rel,
            'omega_actif_absolue_moyenne_abs_rad_s': absolu,
            'omega_libre_absolue_moyenne_abs_rad_s': sum(abs(r[f'{n}_omega_libre_relative_rad_s'] +
                r[f'{n}_omega_corps_rad_s']) for r in regime) / len(regime),
            'ratio_rotor_absolu_sur_relatif': absolu / rel if rel > 1e-6 else None,
        }
    for i, j in apparies:
        a, b = noms[i], noms[j]
        ds = [math.hypot(r[f'{a}_aimant_actif_x_m'] - r[f'{b}_aimant_libre_x_m'],
                         r[f'{a}_aimant_actif_y_m'] - r[f'{b}_aimant_libre_y_m']) for r in rows]
        seuil = ds[0] + p.marge_detection_decrochage
        rupture = next((r['t_s'] for r, d in zip(rows, ds) if d > seuil), None)
        result['paires'][a + '_actif/' + b + '_libre'] = {
            'distance_initiale_m': ds[0], 'distance_min_m': min(ds),
            'distance_max_m': max(ds), 'distance_finale_m': ds[-1],
            'jeu_lateral_max_m': max(0, max(ds) - p.diametre_aimant_ext),
            'fraction_echantillons_en_contact': sum(d <= p.diametre_aimant_ext +
                2*p.enveloppe_collision for d in ds) / len(ds),
            'seuil_eloignement_m': seuil, 'premier_eloignement_detecte_s': rupture,
            'reste_proche_sur_essai': rupture is None,
        }
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    args = parser.parse_args()
    meta = json.loads(args.csv.with_suffix('.json').read_text(encoding='utf-8'))
    p = Parametres(**meta['parametres'])
    with args.csv.open(encoding='utf-8') as f:
        rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
    print(json.dumps(analyser(rows, p), ensure_ascii=False, indent=2))
