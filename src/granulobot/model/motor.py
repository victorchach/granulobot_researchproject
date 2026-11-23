"""DC motor and internal friction of a unit.

DC motor in a quasi-static electrical regime (inductance neglected).
apply_motor computes each unit's torque at every step and applies it
between the active rotor and the body, together with the friction of the
free parts.
"""
import math

from granulobot.chrono_env import chrono, omega


def friction(speed, dry, viscous, epsilon):
    """Smoothed dissipative torque; does not exactly reproduce static friction."""
    return -dry * math.tanh(speed / epsilon) - viscous * speed


def dc_motor(voltage, relative_speed, p):
    """U - Ke * beta * omega = R_elec * I; torque at the gearbox output.

    The current can be negative: electrical braking / back-driven motor.
    No extra efficiency factor is hidden in the braking.
    """
    u = max(-p.tension_max, min(p.tension_max, voltage))
    current = (u - p.ke * p.rapport_reduction * relative_speed) / p.resistance_moteur
    current = max(-p.courant_max, min(p.courant_max, current))
    gain = p.rendement_reducteur * p.rapport_reduction * p.kt
    torque = max(-p.couple_max, min(p.couple_max, gain * current))
    # Current matching the torque actually transmitted after saturation.
    return torque, torque / gain, u


def apply_motor(u, i, t, p):
    w = omega(u.active) - omega(u.body)
    ramp = min(1, t / p.rampe_demarrage) if p.rampe_demarrage else 1
    if p.mode_moteur == "vitesse":
        target = p.vitesses_cibles[i] * ramp
        error = target - w
        # Feed-forward of the electrical braking and losses + PI with anti-windup.
        gain = p.rendement_reducteur * p.rapport_reduction * p.kt / p.resistance_moteur
        dry = p.couple_frottement_actif if p.frottement_interne_actif else 0
        ff = p.ke * p.rapport_reduction * target + dry * math.tanh(target / p.vitesse_regularisation) / gain
        raw = ff + p.gain_p_vitesse * error + p.gain_i_vitesse * u.integral
        if abs(raw) < p.tension_max or raw * error < 0:
            u.integral += error * p.dt
        voltage = raw
    else:
        voltage = p.tensions_cibles[i] * ramp
    if p.moteur_actif:
        if p.mode_moteur == "couple":
            torque = max(-p.couple_max, min(p.couple_max, p.couples_cibles[i] * ramp))
            u.voltage = u.current = 0.0  # No electrical model in this mode.
        else:
            torque, u.current, u.voltage = dc_motor(voltage, w, p)
    else:
        torque = 0.0  # Motor disconnected, open circuit; no electrical braking.
        u.voltage = u.current = 0.0
    u.motor_torque = torque
    if p.frottement_interne_actif:
        torque += friction(w, p.couple_frottement_actif, 0, p.vitesse_regularisation)
    u.transmitted_torque = torque
    u.torque_function.SetConstant(torque)  # Chrono applies the reaction to the body automatically.
    w_free = omega(u.free) - omega(u.body)
    loss = friction(w_free, p.couple_frottement_libre, p.viscosite_libre,
                    p.vitesse_regularisation) if p.frottement_interne_actif else 0
    u.free.AccumulateTorque(u.idx_free, chrono.ChVector3d(0, 0, loss), False)
    u.body.AccumulateTorque(u.idx_body, chrono.ChVector3d(0, 0, -loss), False)
    if u.wheel is not None:
        w_wheel = omega(u.wheel) - omega(u.body)
        wheel_torque = friction(w_wheel, p.couple_frottement_roue, p.viscosite_roue,
                                p.vitesse_regularisation) if p.frottement_interne_actif else 0
        u.wheel.AccumulateTorque(u.idx_wheel, chrono.ChVector3d(0, 0, wheel_torque), False)
        u.body.AccumulateTorque(u.idx_body, chrono.ChVector3d(0, 0, -wheel_torque), False)
    v = u.body.GetPosDt()
    u.body.AccumulateForce(u.idx_body,
                           chrono.ChVector3d(-p.resistance_translation * v.x,
                                             -p.resistance_translation * v.y, 0),
                           u.body.GetPos(), False)
    u.body.AccumulateTorque(u.idx_body,
                            chrono.ChVector3d(0, 0, -p.resistance_rotation * omega(u.body)), False)
