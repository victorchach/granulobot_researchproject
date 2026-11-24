"""Physical checks of the laws, without PyChrono dynamics (fast)."""
import json
import math
import unittest
from pathlib import Path
from granulobot.parameters import Parameters
from granulobot.model.magnets import cross, dipoles, for_parameters, AxialCylinders
from granulobot.model.motor import friction, dc_motor
from granulobot.output.analysis import analyze
from granulobot.simulation.layout import coupled_pairs, ring_positions


class PhysicsLaws(unittest.TestCase):
    def test_cylinders_force_gradient_and_dipole_limit(self):
        p = Parameters()
        model = for_parameters(p)
        for d in (0.008, 0.01, 0.02, 0.1):
            h = 1e-7
            gradient = (model.evaluate(d+h)[0] - model.evaluate(d-h)[0]) / (2*h)
            self.assertAlmostEqual(model.evaluate(d)[1], -gradient, delta=1e-6)
        d = 0.2
        limit = 3e-7 * p.magnet_moment**2 / d**4
        self.assertLess(abs(model.evaluate(d)[1] / limit - 1), 0.01)

    def test_cylinders_refined_quadrature(self):
        p = Parameters()
        base = for_parameters(p).direct(p.magnet_outer_diameter)[1]
        fine = AxialCylinders(p.magnet_outer_diameter, p.magnet_inner_diameter,
            p.magnet_thickness, p.remanence, epsilon=p.magnetic_softening,
            radial=6, angular=24).direct(p.magnet_outer_diameter)[1]
        self.assertLess(abs(base / fine - 1), 0.01)

    def test_flush_geometry_and_axial_attraction(self):
        p = Parameters()
        self.assertAlmostEqual(p.magnet_radius + p.magnet_outer_diameter / 2, p.R)
        r = (p.magnet_outer_diameter, 0, 0)
        force, _, _, _ = dipoles(r, (0, 0, p.magnet_moment),
                                (0, 0, -p.magnet_moment), p.magnetic_softening)
        self.assertLess(force[0], 0)

    def test_analysis_separates_body_rotation_and_detachment(self):
        p = Parameters(n_units=2, startup_ramp=0)
        rows = []
        for t in (0, 0.04):
            r = {'t_s': t}
            for n in ('A', 'B'):
                r.update({f'{n}_body_angle_rad': -t if n == 'A' else 0,
                          f'{n}_active_angle_rad': 0, f'{n}_free_angle_rad': 0,
                          f'{n}_free_rel_omega_rad_s': 0,
                          f'{n}_x_m': 0, f'{n}_y_m': 0,
                          f'{n}_body_omega_rad_s': -1 if n == 'A' else 0,
                          f'{n}_active_rel_omega_rad_s': 1 if n == 'A' else 0})
            r.update({'A_active_magnet_x_m': 0, 'A_active_magnet_y_m': 0,
                      'B_free_magnet_x_m': 0.018, 'B_free_magnet_y_m': 0})
            rows.append(r)
        summary = analyze(rows, p)
        self.assertEqual(summary['units']['A']['rotor_abs_over_rel_ratio'], 0)
        self.assertTrue(summary['pairs']['A_active/B_free']['stays_close'])
        rows[-1]['B_free_magnet_x_m'] += 0.004
        self.assertEqual(analyze(rows, p)['pairs']['A_active/B_free']['first_separation_s'], 0.04)

    def test_force_gradient_energy(self):
        r, mi, mj = (0.021, -0.013, 0.004), (0.2, 0.1, 0.02), (-0.12, 0.21, 0.03)
        f, _, _, _ = dipoles(r, mi, mj, 0.008)
        h = 1e-7
        for k in range(3):
            rp, rm = list(r), list(r)
            rp[k] += h
            rm[k] -= h
            gradient = (dipoles(rp, mi, mj, 0.008)[3] - dipoles(rm, mi, mj, 0.008)[3]) / (2 * h)
            self.assertAlmostEqual(f[k], -gradient, delta=1e-7)

    def test_action_reaction_and_total_moment(self):
        r, mi, mj = (0.021, -0.013, 0.004), (0.2, 0.1, 0.02), (-0.12, 0.21, 0.03)
        f, ti, tj, _ = dipoles(r, mi, mj, 0.008)
        inverse = dipoles(tuple(-x for x in r), mj, mi, 0.008)[0]
        orbital = cross(r, f)
        for k in range(3):
            self.assertAlmostEqual(f[k], -inverse[k], places=12)
            self.assertAlmostEqual(ti[k] + tj[k] + orbital[k], 0, places=12)

    def test_torque_orientation_gradient(self):
        r, mi, mj = (0.022, 0.01, 0), (0.2, 0.1, 0), (0.1, -0.2, 0)
        _, ti, _, _ = dipoles(r, mi, mj, 0.008)
        h = 1e-6
        def rotation(phi):
            return (mi[0] * math.cos(phi) - mi[1] * math.sin(phi),
                    mi[0] * math.sin(phi) + mi[1] * math.cos(phi), 0)
        gradient = (dipoles(r, rotation(h), mj, 0.008)[3] -
                    dipoles(r, rotation(-h), mj, 0.008)[3]) / (2 * h)
        self.assertAlmostEqual(ti[2], -gradient, places=10)

    def test_friction_dissipates(self):
        for w in (-10, -0.1, 0, 0.1, 10):
            self.assertLessEqual(w * friction(w, 0.024, 0.01, 0.05), 0)

    def test_motor_braking_and_limits(self):
        p = Parameters()
        self.assertLess(dc_motor(0, 1, p)[0], 0)
        self.assertGreater(dc_motor(0, -1, p)[0], 0)
        for voltage in (-100, 0, 100):
            for w in (-100, 0, 100):
                torque, current, u = dc_motor(voltage, w, p)
                self.assertLessEqual(abs(torque), p.max_torque)
                self.assertLessEqual(abs(current), p.max_current)
                self.assertLessEqual(abs(u), p.max_voltage)

    def test_masses_and_units(self):
        p = Parameters()
        p.check()
        self.assertAlmostEqual(p.body_mass + p.active_rotor_mass + p.free_rotor_mass + p.wheel_mass, p.M)
        self.assertGreater(p.magnet_moment, 0)
        self.assertLess(p.magnet_radius, p.R)
        p.active_rotor_mass = p.M
        with self.assertRaises(ValueError):
            p.check()


class RingLayout(unittest.TestCase):
    """Spec 006: any number of units, 2 facing or on a regular ring."""
    side = 2 * 0.035 + 5e-5

    def test_triangle_and_pair_unchanged(self):
        s = self.side
        old = ((-s / 2, -s / (2 * math.sqrt(3))), (s / 2, -s / (2 * math.sqrt(3))),
               (0, s / math.sqrt(3)))
        for new, ref in zip(ring_positions(3, s), old):
            for a, b in zip(new, ref):
                self.assertAlmostEqual(a, b, delta=1e-15)
        self.assertEqual(ring_positions(2, s), ((-s / 2, 0), (s / 2, 0)))

    def test_hexagon_is_regular_and_centred(self):
        s, pos = self.side, ring_positions(6, self.side)
        self.assertEqual(len(pos), 6)
        for i in range(6):
            self.assertAlmostEqual(math.dist(pos[i], pos[(i + 1) % 6]), s, delta=1e-15)
            self.assertAlmostEqual(math.dist(pos[i], pos[(i + 2) % 6]), math.sqrt(3) * s, delta=1e-15)
        self.assertAlmostEqual(sum(x for x, _ in pos), 0, delta=1e-15)
        self.assertAlmostEqual(sum(y for _, y in pos), 0, delta=1e-15)

    def test_coupled_pairs(self):
        self.assertEqual(coupled_pairs(2), ((0, 1),))
        self.assertEqual(coupled_pairs(3), ((0, 1), (1, 2), (2, 0)))
        pairs = coupled_pairs(6)
        self.assertEqual(len(pairs), 6)
        self.assertEqual(pairs[-1], (5, 0))

    def test_check_unit_count_and_set_points(self):
        six = (3.25, -3.25, 3.25, -3.25, 3.25, -3.25)
        p = Parameters(n_units=6, target_voltages=six)
        p.check()  # target_speeds keeps 3 values: unused in voltage mode
        self.assertEqual(len(p.target_speeds), 3)
        Parameters(n_units=2, target_voltages=(0.3, 0, 0)).check()
        Parameters(n_units=26, target_voltages=(1,) * 26).check()
        for changes in ({'n_units': 1}, {'n_units': 27}, {'n_units': 6},
                        {'n_units': 6, 'target_voltages': six, 'motor_mode': 'speed'},
                        {'n_units': 6, 'motor_mode': 'torque'},
                        {'n_units': 6, 'target_voltages': six, 'ground_width': 0.2}):
            with self.subTest(**changes), self.assertRaises(ValueError):
                Parameters(**changes).check()

    def test_ring6_config_loads(self):
        path = Path(__file__).resolve().parent.parent / 'configs' / 'ring6_alternating.json'
        values = json.loads(path.read_text(encoding='utf-8'))['parameters']
        self.assertTrue(set(values) <= set(Parameters().to_dict()))
        p = Parameters(**values)
        p.check()
        self.assertEqual(p.n_units, 6)
        self.assertEqual(list(p.target_voltages), [3.25 * (-1)**i for i in range(6)])

    def test_analysis_of_a_hexagon(self):
        p = Parameters(n_units=6, startup_ramp=0)
        names = 'ABCDEF'
        rows = []
        for t in (0, 0.04):
            r = {'t_s': t}
            for n in names:
                r.update({f'{n}_body_angle_rad': 0, f'{n}_active_angle_rad': 0,
                          f'{n}_free_angle_rad': 0, f'{n}_free_rel_omega_rad_s': 0,
                          f'{n}_x_m': 0, f'{n}_y_m': 0, f'{n}_body_omega_rad_s': 0,
                          f'{n}_active_rel_omega_rad_s': 0,
                          f'{n}_active_magnet_x_m': 0, f'{n}_active_magnet_y_m': 0,
                          f'{n}_free_magnet_x_m': 0.008, f'{n}_free_magnet_y_m': 0})
            rows.append(r)
        pairs = analyze(rows, p)['pairs']
        self.assertEqual(len(pairs), 6)
        self.assertIn('F_active/A_free', pairs)
        self.assertEqual(len(analyze(rows, p)['units']), 6)


if __name__ == "__main__":
    unittest.main()
