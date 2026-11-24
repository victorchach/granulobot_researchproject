"""Attachment measurements from the CSV; no PyChrono dependency.

The distance threshold is an indicator of separation, not a breaking law.
Events are detected at the recorded instants; the real measurement step is
reported, independently of the number of GIF frames.
A stable ideal link does not prove that the magnetic model is valid.
"""
import argparse
import csv
import json
import math
from pathlib import Path
from granulobot.parameters import Parameters
from granulobot.simulation.layout import coupled_pairs


def unwrap(angles):
    total = [angles[0]]
    for a, b in zip(angles, angles[1:]):
        total.append(total[-1] + (b - a + math.pi) % (2 * math.pi) - math.pi)
    return total


def analyze(rows, p):
    names = tuple(chr(65 + i) for i in range(p.n_units))
    coupled = coupled_pairs(p.n_units)
    steps = [b['t_s'] - a['t_s'] for a,b in zip(rows, rows[1:])]
    result = {'time_resolution_s': max(steps) if steps else 0,
              'ideal_link': p.ideal_link,
              'criteria': {'separation_margin_m': p.detachment_margin,
                          'hold_ratio_threshold': 0.1},
              'units': {}, 'pairs': {}}
    steady = [r for r in rows if r['t_s'] >= p.startup_ramp] or rows[-1:]
    for n in names:
        body = unwrap([r[f'{n}_body_angle_rad'] for r in rows])
        rotor = unwrap([r[f'{n}_active_angle_rad'] for r in rows])
        free = unwrap([r[f'{n}_free_angle_rad'] for r in rows])
        r0 = rows[0]
        distances = [math.hypot(r[f'{n}_x_m'] - r0[f'{n}_x_m'],
                               r[f'{n}_y_m'] - r0[f'{n}_y_m']) for r in rows]
        rel = sum(abs(r[f'{n}_active_rel_omega_rad_s']) for r in steady) / len(steady)
        absolute = sum(abs(r[f'{n}_active_rel_omega_rad_s'] + r[f'{n}_body_omega_rad_s'])
                       for r in steady) / len(steady)
        result['units'][n] = {
            'net_body_rotation_turns': (body[-1] - body[0]) / (2 * math.pi),
            'total_body_rotation_turns': sum(abs(b - a) for a, b in zip(body, body[1:])) / (2 * math.pi),
            'net_active_rotation_turns': (rotor[-1] - rotor[0]) / (2 * math.pi),
            'net_free_rotation_turns': (free[-1] - free[0]) / (2 * math.pi),
            'max_centre_displacement_m': max(distances),
            'mean_abs_active_rel_omega_rad_s': rel,
            'mean_abs_active_omega_rad_s': absolute,
            'mean_abs_free_omega_rad_s': sum(abs(r[f'{n}_free_rel_omega_rad_s'] +
                r[f'{n}_body_omega_rad_s']) for r in steady) / len(steady),
            'rotor_abs_over_rel_ratio': absolute / rel if rel > 1e-6 else None,
        }
    for i, j in coupled:
        a, b = names[i], names[j]
        ds = [math.hypot(r[f'{a}_active_magnet_x_m'] - r[f'{b}_free_magnet_x_m'],
                         r[f'{a}_active_magnet_y_m'] - r[f'{b}_free_magnet_y_m']) for r in rows]
        threshold = ds[0] + p.detachment_margin
        detachment = next((r['t_s'] for r, d in zip(rows, ds) if d > threshold), None)
        result['pairs'][a + '_active/' + b + '_free'] = {
            'initial_distance_m': ds[0], 'min_distance_m': min(ds),
            'max_distance_m': max(ds), 'final_distance_m': ds[-1],
            'max_side_gap_m': max(0, max(ds) - p.magnet_outer_diameter),
            'contact_sample_fraction': sum(d <= p.magnet_outer_diameter +
                2*p.collision_envelope for d in ds) / len(ds),
            'separation_threshold_m': threshold, 'first_separation_s': detachment,
            'stays_close': detachment is None,
        }
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    args = parser.parse_args()
    meta = json.loads(args.csv.with_suffix('.json').read_text(encoding='utf-8'))
    p = Parameters(**meta['parameters'])
    with args.csv.open(encoding='utf-8') as f:
        rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
    print(json.dumps(analyze(rows, p), ensure_ascii=False, indent=2))
