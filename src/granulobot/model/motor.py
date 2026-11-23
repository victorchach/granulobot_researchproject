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
    u = max(-p.max_voltage, min(p.max_voltage, voltage))
    current = (u - p.ke * p.gear_ratio * relative_speed) / p.motor_resistance
    current = max(-p.max_current, min(p.max_current, current))
    gain = p.gear_efficiency * p.gear_ratio * p.kt
    torque = max(-p.max_torque, min(p.max_torque, gain * current))
    # Current matching the torque actually transmitted after saturation.
    return torque, torque / gain, u


def apply_motor(u, i, t, p):
    w = omega(u.active) - omega(u.body)
    ramp = min(1, t / p.startup_ramp) if p.startup_ramp else 1
    if p.motor_mode == "speed":
        target = p.target_speeds[i] * ramp
        error = target - w
        # Feed-forward of the electrical braking and losses + PI with anti-windup.
        gain = p.gear_efficiency * p.gear_ratio * p.kt / p.motor_resistance
        dry = p.active_friction_torque if p.internal_friction_enabled else 0
        ff = p.ke * p.gear_ratio * target + dry * math.tanh(target / p.regularisation_speed) / gain
        raw = ff + p.speed_gain_p * error + p.speed_gain_i * u.integral
        if abs(raw) < p.max_voltage or raw * error < 0:
            u.integral += error * p.dt
        voltage = raw
    else:
        voltage = p.target_voltages[i] * ramp
    if p.motors_enabled:
        if p.motor_mode == "torque":
            torque = max(-p.max_torque, min(p.max_torque, p.target_torques[i] * ramp))
            u.voltage = u.current = 0.0  # No electrical model in this mode.
        else:
            torque, u.current, u.voltage = dc_motor(voltage, w, p)
    else:
        torque = 0.0  # Motor disconnected, open circuit; no electrical braking.
        u.voltage = u.current = 0.0
    u.motor_torque = torque
    if p.internal_friction_enabled:
        torque += friction(w, p.active_friction_torque, 0, p.regularisation_speed)
    u.transmitted_torque = torque
    u.torque_function.SetConstant(torque)  # Chrono applies the reaction to the body automatically.
    w_free = omega(u.free) - omega(u.body)
    loss = friction(w_free, p.free_friction_torque, p.free_viscosity,
                    p.regularisation_speed) if p.internal_friction_enabled else 0
    u.free.AccumulateTorque(u.idx_free, chrono.ChVector3d(0, 0, loss), False)
    u.body.AccumulateTorque(u.idx_body, chrono.ChVector3d(0, 0, -loss), False)
    if u.wheel is not None:
        w_wheel = omega(u.wheel) - omega(u.body)
        wheel_torque = friction(w_wheel, p.wheel_friction_torque, p.wheel_viscosity,
                                p.regularisation_speed) if p.internal_friction_enabled else 0
        u.wheel.AccumulateTorque(u.idx_wheel, chrono.ChVector3d(0, 0, wheel_torque), False)
        u.body.AccumulateTorque(u.idx_body, chrono.ChVector3d(0, 0, -wheel_torque), False)
    v = u.body.GetPosDt()
    u.body.AccumulateForce(u.idx_body,
                           chrono.ChVector3d(-p.translation_damping * v.x,
                                             -p.translation_damping * v.y, 0),
                           u.body.GetPos(), False)
    u.body.AccumulateTorque(u.idx_body,
                            chrono.ChVector3d(0, 0, -p.rotation_damping * omega(u.body)), False)
