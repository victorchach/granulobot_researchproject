"""Measurements of a run (CSV rows at 200 Hz) and writing of the CSV/JSON outputs."""
import csv
import json
import math

from granulobot.chrono_env import angle, omega, xyz
from granulobot.model.unit import unit_names, unit_pairs


def measure(t, sys, units, p):
    sys.GetContactContainer().ComputeContactForces()
    row = {"t_s": t, "n_contacts_incl_ground": sys.GetNumContacts()}
    for name, u in zip(unit_names(units), units):
        pos, vel = u.body.GetPos(), u.body.GetPosDt()
        row.update({f"{name}_x_m": pos.x, f"{name}_y_m": pos.y, f"{name}_z_m": pos.z,
                    f"{name}_body_angle_rad": angle(u.body),
                    f"{name}_active_angle_rad": angle(u.active), f"{name}_free_angle_rad": angle(u.free),
                    f"{name}_body_omega_rad_s": omega(u.body),
                    f"{name}_active_rel_omega_rad_s": omega(u.active) - omega(u.body),
                    f"{name}_free_rel_omega_rad_s": omega(u.free) - omega(u.body),
                    f"{name}_speed_m_s": math.hypot(vel.x, vel.y),
                    f"{name}_voltage_V": u.voltage, f"{name}_current_A": u.current,
                    f"{name}_motor_torque_Nm": u.motor_torque,
                    f"{name}_transmitted_torque_Nm": u.transmitted_torque})
        parts = [('body', u.body), ('active', u.active), ('free', u.free)]
        if u.wheel is not None:
            parts.append(('wheel', u.wheel))
        for part, b in parts:
            force, torque = b.GetContactForce(), b.GetContactTorque()
            for axis, val in zip('xyz', xyz(force)):
                row[f'{name}_contact_{part}_F{axis}_N'] = val
            row[f'{name}_contact_{part}_torque_z_Nm'] = torque.z
        if u.wheel is not None:
            row[f'{name}_wheel_omega_rad_s'] = omega(u.wheel)
            row[f'{name}_wheel_angle_rad'] = angle(u.wheel)
    for i, j in unit_pairs(units):
        a, b = units[i].body.GetPos(), units[j].body.GetPos()
        row[f"{unit_names(units)[i]}{unit_names(units)[j]}_distance_m"] = math.hypot(b.x - a.x, b.y - a.y)
    if not all(math.isfinite(v) for v in row.values()):
        raise RuntimeError("Non-finite state: check the parameters and reduce dt")
    return row


def assumptions(p):
    return {
        "geometry": {
            "radius_m": p.R, "height_m": p.H,
            "second_free_wheel": p.outer_free_wheel,
            "estimated_rim_thickness_m": p.wheel_thickness,
            "motorised_wheel_at_bottom_assumed": p.motorised_wheel_at_bottom,
            "view": "Motorised part only; vertical axes, tipping blocked",
        },
        "prototype": "The total mass and the motor parameters from the paper are not yet measured on this prototype",
        "projection_plane": "Centres of mass and side contacts in a common plane; XY forces and Z torques kept, tipping moments dropped; shape heights kept for the Bullet ground",
        "motor": "Quasi-static electrics, motor inductance and reflected inertia omitted",
        "contact": "Side NSC contact with a small estimated plastic/metal compliance to regularise flush contacts; zero = rigid reference. Equivalent disc support (normal, Coulomb translation, torsion mu*N*2R/3) or Bullet; translation/torsion limits separate, to calibrate in combined motion",
        "magnets": "Diameter 8 mm, height 10 mm, flush edge and axial poles estimated/confirmed by Hugo; remanence and hole to confirm; uniformly magnetised cylinders by face quadrature, or dipoles for comparison; coplanar magnetic centres in the finite model",
        "friction": "Smoothed internal friction; no exact static threshold; real support to be specified",
        "ideal_link": p.ideal_link,
        "validation": "Compare several dt and calibrate the forces before any quantitative comparison",
        "sources": ["references/scirobotics.adh4130.txt, prototype and fig. 8",
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
    output.with_suffix(".json").write_text(json.dumps({"parameters": p.to_dict(),
                                                       "assumptions": assumptions(p), "summary": summary},
                                                      indent=2, ensure_ascii=False), encoding="utf-8")
