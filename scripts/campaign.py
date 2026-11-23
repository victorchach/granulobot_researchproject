"""Reproducible test plan: attachment, friction, triangle, convergence.

PYTHONPATH=src python scripts/campaign.py --duration 0.6 --gif
Results kept apart in runs/campaign/: CSV/JSON per scenario, summary.json and
summary.txt. A short campaign checks the mechanisms, not the fidelity to the
prototype. The thresholds found are those OF THE MODEL, not measurements of
the real robot.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
from granulobot import REPO_ROOT
from granulobot.parameters import Parameters
from granulobot.simulation.loop import simulate


def scenarios(base):
    two = replace(base, n_units=2, target_voltages=(0.3, 0, 0))
    ideal = replace(two, ideal_link=True)
    return [
        ('passive', replace(two, motors_enabled=False)),
        ('passive_perturbed', replace(two, motors_enabled=False, rotor_perturbation_rad=0.1)),
        ('two_cylinders_0p3V', two),
        ('two_cylinders_half_dt', replace(two, dt=base.dt / 2)),
        ('two_cylinders_double_iterations', replace(two, solver_iterations=base.solver_iterations * 2)),
        ('two_cylinders_1V', replace(two, target_voltages=(1, 0, 0))),
        ('two_cylinders_1V_half_dt', replace(two, target_voltages=(1, 0, 0), dt=base.dt/2)),
        ('two_cylinders_1V_double_iterations', replace(two, target_voltages=(1, 0, 0),
                     solver_iterations=base.solver_iterations*2)),
        ('two_dipoles_axial', replace(two, magnet_model='dipoles')),
        ('two_dipoles_radial', replace(two, magnet_model='dipoles', magnet_orientation='radial')),
        ('two_cylinders_low_neighbour_friction', replace(two, mu_shells=0.05)),
        ('two_ideal', ideal),
        ('two_ideal_no_neighbour_friction', replace(ideal, mu_shells=0)),
        ('two_ideal_slippery_support', replace(ideal, mu_ground=0.01)),
        ('triangle_one_motor', replace(base, target_voltages=(0.3, 0, 0))),
        ('triangle_two_motors', replace(base, target_voltages=(0.3, 0.3, 0))),
        ('triangle_three_motors', replace(base, target_voltages=(0.3, 0.3, 0.3))),
        ('triangle_cylinders_slippery', replace(base,
                   mu_shells=0.05, target_voltages=(0.3, 0.3, 0.3))),
        ('triangle_ideal_slippery', replace(base, ideal_link=True,
                   mu_shells=0, target_voltages=(0.3, 0.3, 0.3))),
        ('two_ideal_half_dt', replace(ideal, dt=base.dt / 2)),
        ('two_ideal_double_iterations', replace(ideal, solver_iterations=base.solver_iterations * 2)),
    ]


def run_campaign(base, output, gif=False, selection=None):
    output.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, p in scenarios(base):
        if selection and name not in selection:
            continue
        print(f'\nRUN: {name}', flush=True)
        rows, summary = simulate(p, output / name, verbose=False,
            gif=gif and name in ('two_ideal', 'two_cylinders_0p3V', 'triangle_ideal_slippery',
                                 'triangle_cylinders_slippery'))
        print(f"Done: {name}; max body speed={summary['max_body_omega_rad_s']:.3g} rad/s", flush=True)
        results[name] = {'parameters': p.to_dict(), 'summary': summary}
        # Saved as we go: an interruption does not lose the finished runs.
        (output / 'summary.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    lines = ['Attachment campaign: model results, no experimental calibration',
             f'Duration of each run: {base.duration} s; reference step: {base.dt} s',
             'Ideal link = rigid reference, with no physical breaking threshold.',
             'Detachment distance = sampled geometric indicator, not a measured force.', '']
    for name, r in results.items():
        att = r['summary']['attachment']
        close = all(v['stays_close'] for v in att['pairs'].values())
        a = att['units']['A']
        ratio = a['rotor_abs_over_rel_ratio']
        lines.append(f"{name}: pairs close={close}; A body={a['net_body_rotation_turns']:.4f} turn; "
                     f"A max centre={a['max_centre_displacement_m']*1000:.3f} mm; "
                     f"rotor abs/rel ratio={ratio}")
    # Quantify the sensitivity without inventing a universal acceptance threshold.
    for reference in ('two_ideal', 'two_cylinders_0p3V', 'two_cylinders_1V'):
        ref = results.get(reference)
        variants = ('two_ideal_half_dt', 'two_ideal_double_iterations') if reference == 'two_ideal' else (
                    'two_cylinders_half_dt', 'two_cylinders_double_iterations')
        if reference == 'two_cylinders_1V':
            variants = ('two_cylinders_1V_half_dt', 'two_cylinders_1V_double_iterations')
        for name in variants:
            if ref and name in results:
                a = ref['summary']['attachment']['units']['A']
                b = results[name]['summary']['attachment']['units']['A']
                lines.append(f"Convergence {name}: A rotation gap={abs(a['net_body_rotation_turns']-b['net_body_rotation_turns']):.6g} turn; "
                             f"A max displacement gap={abs(a['max_centre_displacement_m']-b['max_centre_displacement_m'])*1000:.6g} mm")
    (output / 'summary.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines), flush=True)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration', type=float, default=0.6, help='simulated time of each run (s)')
    parser.add_argument('--gif', action='store_true', help='make the GIF of the four reference scenarios')
    parser.add_argument('--scenarios', nargs='+', help='names to pick from scenarios()')
    parser.add_argument('--output', type=Path, default=REPO_ROOT / 'runs' / 'campaign')
    args = parser.parse_args()
    if args.scenarios:
        unknown = set(args.scenarios) - {n for n, _ in scenarios(Parameters())}
        if unknown:
            parser.error(f'Unknown scenarios: {unknown}')
    run_campaign(Parameters(duration=args.duration), args.output, args.gif, args.scenarios)
