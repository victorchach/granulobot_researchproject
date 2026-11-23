"""Reproducible test plan: attachment, friction, triangle, convergence.

PYTHONPATH=src python scripts/campaign.py --duree 0.6 --animation
Results kept apart in runs/campaign/: CSV/JSON, JSON and text summaries.
A short campaign checks the mechanisms, not the fidelity to the prototype.
The thresholds found are those OF THE MODEL, not measurements of the real robot.
Scenario names and the text of synthese.txt are still in French; spec 005
translates them.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
from granulobot import REPO_ROOT
from granulobot.parameters import Parametres
from granulobot.simulation.loop import simulate


def scenarios(base):
    two = replace(base, nombre_robots=2, tensions_cibles=(0.3, 0, 0))
    ideal = replace(two, liaison_ideale=True)
    return [
        ('passif', replace(two, moteur_actif=False)),
        ('passif_perturbe', replace(two, moteur_actif=False, perturbation_rotor_rad=0.1)),
        ('deux_cylindres_03V', two),
        ('deux_cylindres_dt_divise_2', replace(two, dt=base.dt / 2)),
        ('deux_cylindres_iterations_doublees', replace(two, iterations_solveur=base.iterations_solveur * 2)),
        ('deux_cylindres_10V', replace(two, tensions_cibles=(1, 0, 0))),
        ('deux_cylindres_10V_dt_divise_2', replace(two, tensions_cibles=(1, 0, 0), dt=base.dt/2)),
        ('deux_cylindres_10V_iterations_doublees', replace(two, tensions_cibles=(1, 0, 0),
                     iterations_solveur=base.iterations_solveur*2)),
        ('deux_dipoles_axiaux', replace(two, modele_magnetique='dipoles')),
        ('deux_dipoles_radiaux', replace(two, modele_magnetique='dipoles', orientation_aimant='radiale')),
        ('deux_cylindres_friction_voisins_faible', replace(two, mu_robots=0.05)),
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


def run_campaign(base, output, gif=False, selection=None):
    output.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, p in scenarios(base):
        if selection and name not in selection:
            continue
        print(f'\nRUN: {name}', flush=True)
        rows, summary = simulate(p, output / name, verbose=False,
            gif=gif and name in ('deux_ideal', 'deux_cylindres_03V', 'triangle_ideal_glissant',
                                 'triangle_cylindres_glissant'))
        print(f"Done: {name}; max body speed={summary['omega_corps_max_rad_s']:.3g} rad/s", flush=True)
        results[name] = {'parametres': p.dictionnaire(), 'bilan': summary}
        # Saved as we go: an interruption does not lose the finished runs.
        (output / 'synthese.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    lines = ['Campagne d\'accrochage — résultats du modèle, sans calibration expérimentale',
             f'Durée de chaque essai : {base.duree} s ; pas de référence : {base.dt} s',
             'Attache idéale = référence indéformable, sans seuil de rupture physique.',
             'Distance de décrochage = indicateur géométrique échantillonné, pas force mesurée.', '']
    for name, r in results.items():
        att = r['bilan']['accrochage']
        close = all(v['reste_proche_sur_essai'] for v in att['paires'].values())
        a = att['unites']['A']
        ratio = a['ratio_rotor_absolu_sur_relatif']
        lines.append(f"{name}: paires proches={close}; A corps={a['rotation_corps_nette_tours']:.4f} tour; "
                     f"A centre max={a['deplacement_centre_max_m']*1000:.3f} mm; "
                     f"ratio rotor absolu/relatif={ratio}")
    # Quantify the sensitivity without inventing a universal acceptance threshold.
    for reference in ('deux_ideal', 'deux_cylindres_03V', 'deux_cylindres_10V'):
        ref = results.get(reference)
        variants = ('deux_ideal_dt_divise_2', 'deux_ideal_iterations_doublees') if reference == 'deux_ideal' else (
                    'deux_cylindres_dt_divise_2', 'deux_cylindres_iterations_doublees')
        if reference == 'deux_cylindres_10V':
            variants = ('deux_cylindres_10V_dt_divise_2', 'deux_cylindres_10V_iterations_doublees')
        for name in variants:
            if ref and name in results:
                a = ref['bilan']['accrochage']['unites']['A']
                b = results[name]['bilan']['accrochage']['unites']['A']
                lines.append(f"Convergence {name}: écart rotation A={abs(a['rotation_corps_nette_tours']-b['rotation_corps_nette_tours']):.6g} tour; "
                             f"écart déplacement max A={abs(a['deplacement_centre_max_m']-b['deplacement_centre_max_m'])*1000:.6g} mm")
    (output / 'synthese.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines), flush=True)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duree', type=float, default=0.6)
    parser.add_argument('--animation', action='store_true')
    parser.add_argument('--essais', nargs='+', help='Noms à sélectionner parmi scenarios()')
    parser.add_argument('--sortie', type=Path, default=REPO_ROOT / 'runs' / 'campaign')
    args = parser.parse_args()
    if args.essais:
        unknown = set(args.essais) - {n for n, _ in scenarios(Parametres())}
        if unknown:
            parser.error(f'Unknown runs: {unknown}')
    run_campaign(Parametres(duree=args.duree), args.sortie, args.animation, args.essais)
