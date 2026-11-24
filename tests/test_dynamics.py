"""PyChrono dynamics checks: motor reaction and no drift.

Run in conda chrono, from the repo root:
    PYTHONPATH=src python tests/test_dynamics.py   (or make validate)
"""
from pathlib import Path
import argparse
import math
import tempfile
import unittest

from granulobot import REPO_ROOT
from granulobot.chrono_env import omega
from granulobot.model.motor import apply_motor
from granulobot.parameters import Parameters
from granulobot.simulation.loop import simulate
from granulobot.simulation.world import create_system


class Dynamics(unittest.TestCase):
    def test_two_mobile_units_and_ideal_reference(self):
        p = Parameters(n_units=2, ideal_link=True, duration=0.01,
                       target_voltages=(0.3, 0, 0))
        sys, units, refs = create_system(p)
        self.assertEqual(len(units), 2)
        self.assertTrue(all(not u.body.IsFixed() for u in units))
        with tempfile.TemporaryDirectory() as tmp:
            rows, summary = simulate(p, Path(tmp) / 'ideal', gif=False)
        pair = summary['attachment']['pairs']['A_active/B_free']
        self.assertLess(abs(pair['final_distance_m'] - pair['initial_distance_m']), 1e-6)

    def test_circular_contacts_under_attraction(self):
        # The rigid reference checks the geometry and the absence of penetration.
        p = Parameters(duration=0.05, motors_enabled=False,
                       compliance_shells=0, compliance_magnets=0)
        with tempfile.TemporaryDirectory() as tmp:
            rows, summary = simulate(p, Path(tmp) / "contacts", gif=False)
        self.assertLess(max(summary["max_overlap_m"].values()), 1e-6)
        for n in ("A", "B", "C"):
            self.assertGreaterEqual(rows[-1][f"{n}_z_m"], p.H / 2 - 1e-6)

    def test_compliant_deformation_stays_small(self):
        p = Parameters(duration=0.05, motors_enabled=False)
        with tempfile.TemporaryDirectory() as tmp:
            rows, summary = simulate(p, Path(tmp) / 'compliance', gif=False, verbose=False)
        # With elasticity, the geometric overlap stands for a deformation.
        # Model criterion: less than 0.1 % of the radius, unlike the rigid reference.
        self.assertLess(max(summary['max_overlap_m'].values()), 0.001 * p.R)

    def test_internal_motor_conserves_momentum(self):
        p = Parameters(ground_enabled=False, gravity=0, magnetism_enabled=False,
                       internal_friction_enabled=False, motor_mode="torque",
                       target_torques=(0.002, 0, 0), startup_ramp=0)
        sys, units, refs = create_system(p)
        for k in range(500):
            for i, u in enumerate(units):
                u.clear_forces()
                apply_motor(u, i, sys.GetChTime(), p)
            sys.DoStepDynamics(p.dt)
        u = units[0]
        self.assertGreater(omega(u.active), 0)
        self.assertLess(omega(u.body), 0)
        px = py = lz = 0.0
        for u in units:
            for b in u.dynamic_bodies():
                pos, vel, m = b.GetPos(), b.GetPosDt(), b.GetMass()
                px += m * vel.x
                py += m * vel.y
                lz += b.GetInertiaXX().z * omega(b) + m * (pos.x * vel.y - pos.y * vel.x)
        self.assertAlmostEqual(px, 0, delta=1e-8)
        self.assertAlmostEqual(py, 0, delta=1e-8)
        self.assertAlmostEqual(lz, 0, delta=2e-8)

    def test_still_without_excitation_and_total_mass(self):
        p = Parameters(ground_enabled=False, gravity=0, motors_enabled=False,
                       magnetism_enabled=False, duration=0.01)
        with tempfile.TemporaryDirectory() as tmp:
            rows, summary = simulate(p, Path(tmp) / "rest", gif=False)
        for n in ("A", "B", "C"):
            self.assertAlmostEqual(summary["final_displacement_m"][n], 0, delta=1e-9)
            self.assertAlmostEqual(rows[-1][f"{n}_body_omega_rad_s"], 0, delta=1e-9)
        sys, units, refs = create_system(p)
        for u in units:
            self.assertAlmostEqual(sum(b.GetMass() for b in u.dynamic_bodies()), p.M)

    def test_outer_wheel_turns_independently(self):
        p = Parameters(ground_enabled=False, gravity=0, motors_enabled=False,
                       magnetism_enabled=False, wheel_friction_torque=0,
                       wheel_viscosity=0, internal_friction_enabled=False,
                       initial_gap=0.01)
        sys, units, refs = create_system(p)
        u = units[0]
        from granulobot.chrono_env import chrono
        self.assertFalse(u.wheel.IsFixed())
        u.wheel.SetAngVelParent(chrono.ChVector3d(0, 0, 1))
        for _ in range(100):
            sys.DoStepDynamics(p.dt)
        self.assertAlmostEqual(omega(u.wheel), 1, delta=1e-6)
        self.assertAlmostEqual(omega(u.body), 0, delta=1e-6)

    def test_contacts_with_powered_motors(self):
        p = Parameters(duration=0.02, startup_ramp=0)
        with tempfile.TemporaryDirectory() as tmp:
            rows, summary = simulate(p, Path(tmp) / 'powered', gif=False, verbose=False)
        self.assertLess(max(summary['max_overlap_m'].values()), 0.001 * p.R)

    def test_hexagon_ring_magnets_face_their_neighbours(self):
        # Spec 006: same magnet gap as the triangle, active magnet towards unit i+1.
        def gaps(p):
            sys, units, refs = create_system(p)
            n, out = len(units), []
            for i, u in enumerate(units):
                _, _, a, _ = u.magnet(True, p)
                _, _, b, _ = units[(i + 1) % n].magnet(False, p)
                c, c_next = u.body.GetPos(), units[(i + 1) % n].body.GetPos()
                to_next = (c_next.x - c.x, c_next.y - c.y)
                to_magnet = (a[0] - c.x, a[1] - c.y)
                cross = to_next[0] * to_magnet[1] - to_next[1] * to_magnet[0]
                dot = to_next[0] * to_magnet[0] + to_next[1] * to_magnet[1]
                self.assertAlmostEqual(cross, 0, delta=1e-12)
                self.assertGreater(dot, 0)
                out.append(math.dist(a[:2], b[:2]))
            return units, out
        six = (3.25, -3.25, 3.25, -3.25, 3.25, -3.25)
        units, hexagon = gaps(Parameters(n_units=6, target_voltages=six))
        self.assertEqual(len(units), 6)
        _, triangle = gaps(Parameters())
        for g in hexagon:
            self.assertAlmostEqual(g, triangle[0], delta=1e-12)

    def test_hexagon_alternating_short_run(self):
        p = Parameters(n_units=6, target_voltages=(3.25, -3.25, 3.25, -3.25, 3.25, -3.25),
                       duration=0.003, startup_ramp=0)
        with tempfile.TemporaryDirectory() as tmp:
            rows, summary = simulate(p, Path(tmp) / 'ring6', gif=False, verbose=False)
        self.assertEqual(len(summary['attachment']['pairs']), 6)
        self.assertLess(max(summary['max_overlap_m'].values()), 0.001 * p.R)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--animation", action="store_true", help="make the final animation after the tests")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Dynamics)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    if args.animation:
        simulate(Parameters(), REPO_ROOT / "runs" / "validation_animation")
