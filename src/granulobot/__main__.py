"""Trois granulobots : roue motorisée, deux rotors et roue libre, vue de dessus.

Les paramètres SI et leurs origines sont dans parameters.py.
Commande en tension par défaut ; pas de vitesse ni de déplacement imposé.
Le sol fournit la réaction au poids et les frottements NSC. Un guide ne
bloque que le basculement (Rx/Ry), jamais X, Y, Z ou la rotation autour de Z.
Les aimants affleurants de diamètre 8 mm et hauteur 10 mm ont leurs pôles
sur les faces plates. Leur champ plan est calculé par charges surfaciques,
avec quadrature et contact NSC. Les dipôles restent une variante de comparaison.
La rotation propre autour de Z ne change pas une aimantation axiale.
Les aimants restent mécaniquement solidaires du rotor : leur roulement propre
(et son effet sur le frottement de contact), les dents et les collisions
internes entre aimants restent omis.

Exemples (environnement conda chrono, depuis la racine du dépôt) :
    PYTHONPATH=src python -m granulobot
    PYTHONPATH=src python -m granulobot --tensions 1 2 3
    PYTHONPATH=src python -m granulobot --mode vitesse --vitesses 0.3 0.3 0.3
    PYTHONPATH=src python -m granulobot --sans-sol --sans-magnetisme
    PYTHONPATH=src python -m granulobot --duree 0.2 --sans-gif --sortie /chemin/essai

Sorties : GIF à vitesse réelle, CSV de mesures, JSON de paramètres/bilan.
Sans --sortie, elles vont dans runs/sim à la racine du dépôt.
"""
import argparse
import csv
import json
from pathlib import Path

from granulobot import RACINE
from granulobot.output.animation import animation
from granulobot.parameters import Parametres
from granulobot.simulation.loop import simuler

# Modifier ces paramètres pour les essais. Les détails sont dans parameters.py.
PARAMETRES = Parametres()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--robots", type=int, choices=(2, 3))
    parser.add_argument("--liaison-ideale", action="store_true")
    parser.add_argument("--parametres", type=Path, help="JSON de paramètres mesurés/estimés")
    parser.add_argument("--duree", type=float)
    parser.add_argument("--dt", type=float)
    parser.add_argument("--mode", choices=("tension", "vitesse", "couple"))
    parser.add_argument("--tensions", type=float, nargs=3, metavar=("A", "B", "C"))
    parser.add_argument("--vitesses", type=float, nargs=3, metavar=("A", "B", "C"))
    parser.add_argument("--sans-moteurs", action="store_true")
    parser.add_argument("--sans-magnetisme", action="store_true")
    parser.add_argument("--sans-sol", action="store_true")
    parser.add_argument("--sans-gif", action="store_true")
    parser.add_argument("--rejouer", type=Path, help="Régénérer le GIF d'un CSV sans refaire la dynamique")
    parser.add_argument("--sortie", type=Path)
    args = parser.parse_args()
    if args.rejouer:
        meta = json.loads(args.rejouer.with_suffix('.json').read_text(encoding='utf-8'))
        p = Parametres(**meta['parametres'])
        with args.rejouer.open(encoding='utf-8') as f:
            rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
        animation(rows, p, args.sortie or args.rejouer.with_suffix(''))
        print('GIF régénéré à partir des mesures, sans refaire la dynamique.', flush=True)
        return
    p = PARAMETRES
    if args.parametres:
        donnees = json.loads(args.parametres.read_text(encoding="utf-8"))
        for cle, valeur in donnees.get("parametres", donnees).items():
            if cle not in p.dictionnaire():
                raise ValueError(f"Paramètre inconnu : {cle}")
            setattr(p, cle, valeur)
    if args.robots is not None:
        p.nombre_robots = args.robots
    p.liaison_ideale = p.liaison_ideale or args.liaison_ideale
    for option, attribut in ((args.duree, "duree"), (args.dt, "dt"), (args.mode, "mode_moteur"),
                            (args.tensions, "tensions_cibles"), (args.vitesses, "vitesses_cibles")):
        if option is not None:
            setattr(p, attribut, tuple(option) if isinstance(option, list) else option)
    p.moteur_actif = not args.sans_moteurs and p.moteur_actif
    p.magnetisme_actif = not args.sans_magnetisme and p.magnetisme_actif
    p.sol_actif = not args.sans_sol and p.sol_actif
    simuler(p, args.sortie or RACINE / 'runs' / 'sim', not args.sans_gif)


if __name__ == "__main__":
    main()
