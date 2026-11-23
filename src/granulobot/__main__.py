"""Three granulobots: motorised wheel, two rotors and free wheel, top view.

The SI parameters and their origins are in parameters.py.
Voltage control by default; no imposed speed or displacement.
The ground provides the reaction to the weight and the NSC friction. A guide
only blocks tipping (Rx/Ry), never X, Y, Z or the rotation about Z.
The flush magnets, 8 mm in diameter and 10 mm high, have their poles on the
flat faces. Their planar field is computed from surface charges, with
quadrature and NSC contact. Dipoles remain a comparison variant.
A spin about Z does not change an axial magnetisation.
The magnets stay rigidly attached to the rotor: their own bearing (and its
effect on contact friction), the gear teeth and the internal collisions
between magnets are left out.

Examples (conda env chrono, from the repo root):
    PYTHONPATH=src python -m granulobot
    PYTHONPATH=src python -m granulobot --tensions 1 2 3
    PYTHONPATH=src python -m granulobot --mode vitesse --vitesses 0.3 0.3 0.3
    PYTHONPATH=src python -m granulobot --sans-sol --sans-magnetisme
    PYTHONPATH=src python -m granulobot --duree 0.2 --sans-gif --sortie /path/run

Outputs: GIF in real time, CSV of measurements, JSON of parameters/summary.
Without --sortie, they go to runs/sim at the repo root.
"""
import argparse
import csv
import json
from pathlib import Path

from granulobot import REPO_ROOT
from granulobot.output.animation import animate
from granulobot.parameters import Parametres
from granulobot.simulation.loop import simulate

# Change these parameters for trials. Details are in parameters.py.
PARAMETERS = Parametres()


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
        animate(rows, p, args.sortie or args.rejouer.with_suffix(''))
        print('GIF rebuilt from the measurements, without rerunning the dynamics.', flush=True)
        return
    p = PARAMETERS
    if args.parametres:
        data = json.loads(args.parametres.read_text(encoding="utf-8"))
        for key, value in data.get("parametres", data).items():
            if key not in p.dictionnaire():
                raise ValueError(f"Unknown parameter: {key}")
            setattr(p, key, value)
    if args.robots is not None:
        p.nombre_robots = args.robots
    p.liaison_ideale = p.liaison_ideale or args.liaison_ideale
    for option, attribute in ((args.duree, "duree"), (args.dt, "dt"), (args.mode, "mode_moteur"),
                              (args.tensions, "tensions_cibles"), (args.vitesses, "vitesses_cibles")):
        if option is not None:
            setattr(p, attribute, tuple(option) if isinstance(option, list) else option)
    p.moteur_actif = not args.sans_moteurs and p.moteur_actif
    p.magnetisme_actif = not args.sans_magnetisme and p.magnetisme_actif
    p.sol_actif = not args.sans_sol and p.sol_actif
    simulate(p, args.sortie or REPO_ROOT / 'runs' / 'sim', not args.sans_gif)


if __name__ == "__main__":
    main()
