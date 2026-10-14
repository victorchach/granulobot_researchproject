"""Plan d'essais reproductible : accrochage, frottements, triangle, convergence.

python campagne_accrochage.py --duree 0.6 --animation
Résultats isolés dans essais_accrochage/ : CSV/JSON, synthèse JSON et texte.
Une campagne courte vérifie les mécanismes, pas la fidélité au prototype.
Les seuils trouvés sont ceux DU MODELE, pas des mesures du robot réel.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
from granulobot_physics import Parametres
from test_3_granulobots import simuler


def scenarios(base):
    deux = replace(base, nombre_robots=2, tensions_cibles=(0.3, 0, 0))
    ideal = replace(deux, liaison_ideale=True)
    return [
        ('passif', replace(deux, moteur_actif=False)),
        ('passif_perturbe', replace(deux, moteur_actif=False, perturbation_rotor_rad=0.1)),
        ('deux_cylindres_03V', deux),
        ('deux_cylindres_dt_divise_2', replace(deux, dt=base.dt / 2)),
        ('deux_cylindres_iterations_doublees', replace(deux, iterations_solveur=base.iterations_solveur * 2)),
        ('deux_cylindres_10V', replace(deux, tensions_cibles=(1, 0, 0))),
        ('deux_cylindres_10V_dt_divise_2', replace(deux, tensions_cibles=(1, 0, 0), dt=base.dt/2)),
        ('deux_cylindres_10V_iterations_doublees', replace(deux, tensions_cibles=(1, 0, 0),
                     iterations_solveur=base.iterations_solveur*2)),
        ('deux_dipoles_axiaux', replace(deux, modele_magnetique='dipoles')),
        ('deux_dipoles_radiaux', replace(deux, modele_magnetique='dipoles', orientation_aimant='radiale')),
        ('deux_cylindres_friction_voisins_faible', replace(deux, mu_robots=0.05)),
        ('deux_ideal', ideal),
        ('deux_ideal_sans_friction_voisins', replace(ideal, mu_robots=0)),
        ('deux_ideal_support_glissant', replace(ideal, mu_sol=0.01)),
        ('triangle_un_moteur', replace(base, tensions_cibles=(0.3, 0, 0))),
        ('triangle_deux_moteurs', replace(base, tensions_cibles=(0.3, 0.3, 0))),
        ('triangle_trois_moteurs', replace(base, tensions_cibles=(0.3, 0.3, 0.3))),
        ('triangle_cylindres_glissant', replace(base,
                   mu_robots=0.05, tensions_cibles=(0.3, 0.3, 0.3))),
        ('triangle_ideal_glissant', replace(base, liaison_ideale=True,
                   mu_robots=0, tensions_cibles=(0.3, 0.3, 0.3))),
        ('deux_ideal_dt_divise_2', replace(ideal, dt=base.dt / 2)),
        ('deux_ideal_iterations_doublees', replace(ideal, iterations_solveur=base.iterations_solveur * 2)),
    ]


def executer(base, sortie, gif=False, selection=None):
    sortie.mkdir(parents=True, exist_ok=True)
    resultats = {}
    for nom, p in scenarios(base):
        if selection and nom not in selection:
            continue
        print(f'\nESSAI : {nom}', flush=True)
        rows, bilan = simuler(p, sortie / nom, verbose=False,
            gif=gif and nom in ('deux_ideal', 'deux_cylindres_03V', 'triangle_ideal_glissant',
                               'triangle_cylindres_glissant'))
        print(f"Terminé : {nom}; vitesse corps max={bilan['omega_corps_max_rad_s']:.3g} rad/s", flush=True)
        resultats[nom] = {'parametres': p.dictionnaire(), 'bilan': bilan}
        # Sauvegarde progressive : une interruption ne perd pas les essais terminés.
        (sortie / 'synthese.json').write_text(json.dumps(resultats, indent=2, ensure_ascii=False), encoding='utf-8')
    lignes = ['Campagne d\'accrochage — résultats du modèle, sans calibration expérimentale',
              f'Durée de chaque essai : {base.duree} s ; pas de référence : {base.dt} s',
              'Attache idéale = référence indéformable, sans seuil de rupture physique.',
              'Distance de décrochage = indicateur géométrique échantillonné, pas force mesurée.', '']
    for nom, r in resultats.items():
        acc = r['bilan']['accrochage']
        proches = all(v['reste_proche_sur_essai'] for v in acc['paires'].values())
        a = acc['unites']['A']
        ratio = a['ratio_rotor_absolu_sur_relatif']
        lignes.append(f"{nom}: paires proches={proches}; A corps={a['rotation_corps_nette_tours']:.4f} tour; "
                      f"A centre max={a['deplacement_centre_max_m']*1000:.3f} mm; "
                      f"ratio rotor absolu/relatif={ratio}")
    # Quantifier la sensibilité sans fabriquer un seuil universel d'acceptation.
    for reference in ('deux_ideal', 'deux_cylindres_03V', 'deux_cylindres_10V'):
        ref = resultats.get(reference)
        variantes = ('deux_ideal_dt_divise_2', 'deux_ideal_iterations_doublees') if reference == 'deux_ideal' else (
                    'deux_cylindres_dt_divise_2', 'deux_cylindres_iterations_doublees')
        if reference == 'deux_cylindres_10V':
            variantes = ('deux_cylindres_10V_dt_divise_2', 'deux_cylindres_10V_iterations_doublees')
        for nom in variantes:
            if ref and nom in resultats:
                a = ref['bilan']['accrochage']['unites']['A']
                b = resultats[nom]['bilan']['accrochage']['unites']['A']
                lignes.append(f"Convergence {nom}: écart rotation A={abs(a['rotation_corps_nette_tours']-b['rotation_corps_nette_tours']):.6g} tour; "
                              f"écart déplacement max A={abs(a['deplacement_centre_max_m']-b['deplacement_centre_max_m'])*1000:.6g} mm")
    (sortie / 'synthese.txt').write_text('\n'.join(lignes) + '\n', encoding='utf-8')
    print('\n'.join(lignes), flush=True)
    return resultats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duree', type=float, default=0.6)
    parser.add_argument('--animation', action='store_true')
    parser.add_argument('--essais', nargs='+', help='Noms à sélectionner parmi scenarios()')
    parser.add_argument('--sortie', type=Path, default=Path(__file__).with_name('essais_plan'))
    args = parser.parse_args()
    if args.essais:
        inconnus = set(args.essais) - {n for n, _ in scenarios(Parametres())}
        if inconnus:
            parser.error(f'Essais inconnus : {inconnus}')
    executer(Parametres(duree=args.duree), args.sortie, args.animation, args.essais)
