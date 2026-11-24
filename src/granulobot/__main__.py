"""Granulobots (2 facing units, or a ring of 3 to 26): motorised wheel, two
rotors and free wheel, top view.

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
    PYTHONPATH=src python -m granulobot --voltages 1 2 3
    PYTHONPATH=src python -m granulobot --mode speed --speeds 0.3 0.3 0.3
    PYTHONPATH=src python -m granulobot --no-ground --no-magnetism
    PYTHONPATH=src python -m granulobot --duration 0.2 --no-gif --output /path/run
    PYTHONPATH=src python -m granulobot --params configs/prototype_hugo.json
    PYTHONPATH=src python -m granulobot --params configs/ring6_alternating.json
    PYTHONPATH=src python -m granulobot --units 4 --voltages 1 -1 1 -1

Outputs: GIF in real time, CSV of measurements, JSON of parameters/summary.
Without --output, they go to runs/sim at the repo root.
"""
import argparse
import csv
import json
from pathlib import Path

from granulobot import REPO_ROOT
from granulobot.output.animation import animate
from granulobot.parameters import Parameters
from granulobot.simulation.loop import simulate

# Change these parameters for trials. Details are in parameters.py.
PARAMETERS = Parameters()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--units", type=int, metavar="N",
                        help="number of units, 2 to 26 (2: facing pair; N >= 3: ring, 3: triangle)")
    parser.add_argument("--ideal-link", action="store_true", help="rigid reference link between coupled magnets")
    parser.add_argument("--params", type=Path, help="JSON file of measured/estimated parameters")
    parser.add_argument("--duration", type=float, help="simulated time (s)")
    parser.add_argument("--dt", type=float, help="time step (s)")
    parser.add_argument("--mode", choices=("voltage", "speed", "torque"), help="motor control mode")
    parser.add_argument("--voltages", type=float, nargs="+", metavar="V",
                        help="target voltages (V), one per unit in order A, B, ...")
    parser.add_argument("--speeds", type=float, nargs="+", metavar="W",
                        help="target speeds (rad/s), one per unit, speed mode")
    parser.add_argument("--no-motors", action="store_true")
    parser.add_argument("--no-magnetism", action="store_true")
    parser.add_argument("--no-ground", action="store_true")
    parser.add_argument("--no-gif", action="store_true")
    parser.add_argument("--replay", type=Path, help="rebuild the GIF of a CSV without rerunning the dynamics")
    parser.add_argument("--output", type=Path, help="output path without extension (default: runs/sim)")
    args = parser.parse_args()
    if args.replay:
        meta = json.loads(args.replay.with_suffix('.json').read_text(encoding='utf-8'))
        p = Parameters(**meta['parameters'])
        with args.replay.open(encoding='utf-8') as f:
            rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
        animate(rows, p, args.output or args.replay.with_suffix(''))
        print('GIF rebuilt from the measurements, without rerunning the dynamics.', flush=True)
        return
    p = PARAMETERS
    if args.params:
        data = json.loads(args.params.read_text(encoding="utf-8"))
        for key, value in data.get("parameters", data).items():
            if key not in p.to_dict():
                raise ValueError(f"Unknown parameter: {key}")
            setattr(p, key, value)
    if args.units is not None:
        p.n_units = args.units
    p.ideal_link = p.ideal_link or args.ideal_link
    for option, attribute in ((args.duration, "duration"), (args.dt, "dt"), (args.mode, "motor_mode"),
                              (args.voltages, "target_voltages"), (args.speeds, "target_speeds")):
        if option is not None:
            setattr(p, attribute, tuple(option) if isinstance(option, list) else option)
    p.motors_enabled = not args.no_motors and p.motors_enabled
    p.magnetism_enabled = not args.no_magnetism and p.magnetism_enabled
    p.ground_enabled = not args.no_ground and p.ground_enabled
    simulate(p, args.output or REPO_ROOT / 'runs' / 'sim', not args.no_gif)


if __name__ == "__main__":
    main()
