"""Physical checks of the laws, without PyChrono dynamics (fast)."""
import math
import unittest
from granulobot.parameters import Parametres
from granulobot.model.magnets import cross, dipoles, for_parameters, AxialCylinders
from granulobot.model.motor import friction, dc_motor
from granulobot.output.analysis import analyze


class PhysicsLaws(unittest.TestCase):
    def test_cylinders_force_gradient_and_dipole_limit(self):
        p = Parametres()
        model = for_parameters(p)
        for d in (0.008, 0.01, 0.02, 0.1):
            h = 1e-7
            gradient = (model.evaluate(d+h)[0] - model.evaluate(d-h)[0]) / (2*h)
            self.assertAlmostEqual(model.evaluate(d)[1], -gradient, delta=1e-6)
        d = 0.2
        limit = 3e-7 * p.moment_aimant**2 / d**4
        self.assertLess(abs(model.evaluate(d)[1] / limit - 1), 0.01)

    def test_cylinders_refined_quadrature(self):
        p = Parametres()
        base = for_parameters(p).direct(p.diametre_aimant_ext)[1]
        fine = AxialCylinders(p.diametre_aimant_ext, p.diametre_aimant_int,
            p.epaisseur_aimant, p.remanence, epsilon=p.adoucissement_magnetique,
            radial=6, angular=24).direct(p.diametre_aimant_ext)[1]
        self.assertLess(abs(base / fine - 1), 0.01)

    def test_flush_geometry_and_axial_attraction(self):
        p = Parametres()
        self.assertAlmostEqual(p.rayon_aimant + p.diametre_aimant_ext / 2, p.R)
        r = (p.diametre_aimant_ext, 0, 0)
        force, _, _, _ = dipoles(r, (0, 0, p.moment_aimant),
                                (0, 0, -p.moment_aimant), p.adoucissement_magnetique)
        self.assertLess(force[0], 0)

    def test_analysis_separates_body_rotation_and_detachment(self):
        p = Parametres(nombre_robots=2, rampe_demarrage=0)
        rows = []
        for t in (0, 0.04):
            r = {'t_s': t}
            for n in ('A', 'B'):
                r.update({f'{n}_angle_corps_rad': -t if n == 'A' else 0,
                          f'{n}_angle_actif_rad': 0, f'{n}_angle_libre_rad': 0,
                          f'{n}_omega_libre_relative_rad_s': 0,
                          f'{n}_x_m': 0, f'{n}_y_m': 0,
                          f'{n}_omega_corps_rad_s': -1 if n == 'A' else 0,
                          f'{n}_omega_actif_relative_rad_s': 1 if n == 'A' else 0})
            r.update({'A_aimant_actif_x_m': 0, 'A_aimant_actif_y_m': 0,
                      'B_aimant_libre_x_m': 0.018, 'B_aimant_libre_y_m': 0})
            rows.append(r)
        summary = analyze(rows, p)
        self.assertEqual(summary['unites']['A']['ratio_rotor_absolu_sur_relatif'], 0)
        self.assertTrue(summary['paires']['A_actif/B_libre']['reste_proche_sur_essai'])
        rows[-1]['B_aimant_libre_x_m'] += 0.004
        self.assertEqual(analyze(rows, p)['paires']['A_actif/B_libre']['premier_eloignement_detecte_s'], 0.04)

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
        p = Parametres()
        self.assertLess(dc_motor(0, 1, p)[0], 0)
        self.assertGreater(dc_motor(0, -1, p)[0], 0)
        for voltage in (-100, 0, 100):
            for w in (-100, 0, 100):
                torque, current, u = dc_motor(voltage, w, p)
                self.assertLessEqual(abs(torque), p.couple_max)
                self.assertLessEqual(abs(current), p.courant_max)
                self.assertLessEqual(abs(u), p.tension_max)

    def test_masses_and_units(self):
        p = Parametres()
        p.verifier()
        self.assertAlmostEqual(p.masse_corps + p.masse_actif + p.masse_libre + p.masse_roue_libre, p.M)
        self.assertGreater(p.moment_aimant, 0)
        self.assertLess(p.rayon_aimant, p.R)
        p.masse_actif = p.M
        with self.assertRaises(ValueError):
            p.verifier()


if __name__ == "__main__":
    unittest.main()
