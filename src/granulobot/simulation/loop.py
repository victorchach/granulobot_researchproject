"""The simulation loop: measurements, forces, Chrono step, then summary and outputs."""
import json
import math

from granulobot.chrono_env import omega, xyz
from granulobot.model.magnets import apply_magnetism
from granulobot.model.motor import apply_motor
from granulobot.model.unit import unit_names, unit_pairs
from granulobot.output.analysis import analyze
from granulobot.output.animation import animate
from granulobot.simulation.recording import measure, write_outputs
from granulobot.simulation.world import create_system


def simulate(p, output, gif=True, verbose=True):
    p.check()
    sys, units, references = create_system(p)
    NAMES = unit_names(units)
    rows, min_distances = [], {pair: 2 * p.R for pair in unit_pairs(units)}
    max_force, max_speed, electrical_energy = 0.0, 0.0, 0.0
    period = max(1, round(1 / (p.sample_rate * p.dt)))
    nsteps = round(p.duration / p.dt)
    if verbose:
        print(f"Mode={p.motor_mode}, dt={p.dt:g} s, duration={p.duration:g} s", flush=True)
        print(f"Total mass/unit={p.M:g} kg; estimated moment/magnet={p.magnet_moment:.3f} A.m²", flush=True)
    initial_positions = [xyz(u.body.GetPos()) for u in units]
    for k in range(nsteps + 1):
        t = sys.GetChTime()
        if k % period == 0 or k == nsteps:
            row = measure(t, sys, units, p)
            for n, u in zip(unit_names(units), units):
                for active, prefix in ((True, "active"), (False, "free")):
                    _, _, pos, _ = u.magnet(active, p)
                    row[f"{n}_{prefix}_magnet_x_m"] = pos[0]
                    row[f"{n}_{prefix}_magnet_y_m"] = pos[1]
            rows.append(row)
        for i, j in unit_pairs(units):
            a, b = units[i].body.GetPos(), units[j].body.GetPos()
            min_distances[i, j] = min(min_distances[i, j], math.hypot(b.x - a.x, b.y - a.y))
        max_speed = max(max_speed, *(abs(omega(u.body)) for u in units))
        if k == nsteps:
            break
        for i, u in enumerate(units):
            u.clear_forces()
            apply_motor(u, i, t, p)
        _, fm = apply_magnetism(units, p)
        max_force = max(max_force, fm)
        electrical_energy += sum(u.voltage * u.current for u in units) * p.dt
        sys.DoStepDynamics(p.dt)
        if verbose and (k + 1) % max(1, round(0.5 / p.dt)) == 0:
            print(f"t={sys.GetChTime():.2f} s  contacts(ground included)={sys.GetNumContacts()}  "
                  f"body speeds={[round(omega(u.body), 3) for u in units]} rad/s", flush=True)
    summary = {
        "max_overlap_m": {NAMES[i] + NAMES[j]: max(0, 2 * p.R - d) for (i, j), d in min_distances.items()},
        "max_body_omega_rad_s": max_speed, "max_magnet_force_N": max_force,
        "signed_electrical_energy_J": electrical_energy,
        "final_displacement_m": {n: math.hypot(u.body.GetPos().x - pos[0], u.body.GetPos().y - pos[1])
                                for n, u, pos in zip(NAMES, units, initial_positions)},
        "final_active_rel_omega_rad_s": {n: omega(u.active) - omega(u.body) for n, u in zip(unit_names(units), units)},
        "simulated_duration_s": sys.GetChTime(),
    }
    summary["attachment"] = analyze(rows, p)
    write_outputs(rows, p, summary, output)
    if gif:
        animate(rows, p, output)
    if verbose:
        print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
        print(f"Results: {output} (.csv, .json" + (", .gif)" if gif else ")"), flush=True)
    return rows, summary
