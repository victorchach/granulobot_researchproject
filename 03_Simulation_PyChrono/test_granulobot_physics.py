"""Vérifications physiques des lois, sans installation de PyChrono."""
import math
import unittest
from dataclasses import replace
from granulobot_physics import Parametres, cross, dipoles, frottement, moteur_cc, frottement_jantes
from analyse_simulation import analyser
from magnetic_cylinders import pour_parametres, CylindresAxiaux


class LoisPhysiques(unittest.TestCase):
    def test_rim_engagement_requires_local_attractive_contact(self):
        p = Parametres()
        a, b = (0, 0, 0), (2*p.R, 0, 0)
        ma = [((p.rayon_aimant, 0, 0), (0, 0, 1))]
        mb = [((2*p.R-p.rayon_aimant, 0, 0), (0, 0, -1))]
        mu, poids = frottement_jantes(a, b, ma, mb, p)
        self.assertAlmostEqual(mu, p.mu_magnetique)
        self.assertAlmostEqual(poids, 1)
        self.assertEqual(frottement_jantes(b, a, mb, ma, p), (mu, poids))
        cases = [
            (a, b, ma, [(mb[0][0], (0, 0, 1))], p),  # Repulsive polarities.
            (a, b, ma, mb, replace(p, magnetisme_actif=False)),
            (a, b, ma, mb, replace(p, facteur_moment=0)),
            (a, b, ma, mb, replace(p, liaison_ideale=True)),
            (a, (2*p.R+0.01, 0, 0), ma, mb, p),  # Rims separated.
            (a, b, [((-p.rayon_aimant, 0, 0), (0, 0, 1))], mb, p),
            (a, b, ma, [((mb[0][0][0], 0, p.epaisseur_aimant), (0, 0, -1))], p),
        ]
        for args in cases:
            self.assertEqual(frottement_jantes(*args), (p.mu_sterique, 0))
        legacy = replace(p, frottements_differencies=False, mu_robots=0.37)
        self.assertEqual(frottement_jantes(a, b, ma, mb, legacy), (0.37, 0))
        radial = replace(p, modele_magnetique='dipoles', orientation_aimant='radiale')
        self.assertAlmostEqual(frottement_jantes(a, b, [(ma[0][0], (1, 0, 0))],
                              [(mb[0][0], (1, 0, 0))], radial)[0], p.mu_magnetique)

    def test_rim_engagement_fades_with_gap_and_misalignment(self):
        p = Parametres()
        a, b = (0, 0, 0), (2*p.R, 0, 0)
        def result(gap=0, lateral=0):
            ma = [((p.rayon_aimant-gap/2, lateral, 0), (0, 0, 1))]
            mb = [((2*p.R-p.rayon_aimant+gap/2, lateral, 0), (0, 0, -1))]
            return frottement_jantes(a, b, ma, mb, p)
        values = [result(gap=p.portee_engagement_magnetique*i/10)[0] for i in range(11)]
        self.assertTrue(all(x >= y for x, y in zip(values, values[1:])))
        self.assertAlmostEqual(values[5], (p.mu_sterique+p.mu_magnetique)/2)
        self.assertAlmostEqual(values[-1], p.mu_sterique)
        self.assertGreater(result(lateral=p.diametre_aimant_ext/4)[0], p.mu_sterique)
        self.assertEqual(result(lateral=p.diametre_aimant_ext/2), (p.mu_sterique, 0))

    def test_rim_parameters_reject_invalid_values(self):
        for changes in ({'mu_sterique': -1}, {'mu_magnetique': float('nan')},
                        {'mu_magnetique': 0.01}, {'portee_engagement_magnetique': 0},
                        {'portee_engagement_magnetique': float('inf')}):
            with self.assertRaises(ValueError):
                replace(Parametres(), **changes).verifier()

    def test_cylindres_force_gradient_et_limite_dipolaire(self):
        p = Parametres()
        modele = pour_parametres(p)
        for d in (0.008, 0.01, 0.02, 0.1):
            h = 1e-7
            gradient = (modele.evaluer(d+h)[0] - modele.evaluer(d-h)[0]) / (2*h)
            self.assertAlmostEqual(modele.evaluer(d)[1], -gradient, delta=1e-6)
        d = 0.2
        limite = 3e-7 * p.moment_aimant**2 / d**4
        self.assertLess(abs(modele.evaluer(d)[1] / limite - 1), 0.01)

    def test_cylindres_quadrature_raffinee(self):
        p = Parametres()
        base = pour_parametres(p).direct(p.diametre_aimant_ext)[1]
        fin = CylindresAxiaux(p.diametre_aimant_ext, p.diametre_aimant_int,
            p.epaisseur_aimant, p.remanence, epsilon=p.adoucissement_magnetique,
            radial=6, angulaire=24).direct(p.diametre_aimant_ext)[1]
        self.assertLess(abs(base / fin - 1), 0.01)

    def test_geometrie_affleurante_et_attraction_axiale(self):
        p = Parametres()
        self.assertAlmostEqual(p.rayon_aimant + p.diametre_aimant_ext / 2, p.R)
        r = (p.diametre_aimant_ext, 0, 0)
        force, _, _, _ = dipoles(r, (0, 0, p.moment_aimant),
                                (0, 0, -p.moment_aimant), p.adoucissement_magnetique)
        self.assertLess(force[0], 0)

    def test_diagnostic_distingue_rotation_corps_et_decrochage(self):
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
        bilan = analyser(rows, p)
        self.assertEqual(bilan['unites']['A']['ratio_rotor_absolu_sur_relatif'], 0)
        self.assertTrue(bilan['paires']['A_actif/B_libre']['reste_proche_sur_essai'])
        rows[-1]['B_aimant_libre_x_m'] += 0.004
        self.assertEqual(analyser(rows, p)['paires']['A_actif/B_libre']['premier_eloignement_detecte_s'], 0.04)

    def test_force_gradient_energie(self):
        r, mi, mj = (0.021, -0.013, 0.004), (0.2, 0.1, 0.02), (-0.12, 0.21, 0.03)
        f, _, _, _ = dipoles(r, mi, mj, 0.008)
        h = 1e-7
        for k in range(3):
            rp, rm = list(r), list(r)
            rp[k] += h
            rm[k] -= h
            gradient = (dipoles(rp, mi, mj, 0.008)[3] - dipoles(rm, mi, mj, 0.008)[3]) / (2 * h)
            self.assertAlmostEqual(f[k], -gradient, delta=1e-7)

    def test_action_reaction_et_moment_total(self):
        r, mi, mj = (0.021, -0.013, 0.004), (0.2, 0.1, 0.02), (-0.12, 0.21, 0.03)
        f, ti, tj, _ = dipoles(r, mi, mj, 0.008)
        inverse = dipoles(tuple(-x for x in r), mj, mi, 0.008)[0]
        orbital = cross(r, f)
        for k in range(3):
            self.assertAlmostEqual(f[k], -inverse[k], places=12)
            self.assertAlmostEqual(ti[k] + tj[k] + orbital[k], 0, places=12)

    def test_couple_gradient_orientation(self):
        r, mi, mj = (0.022, 0.01, 0), (0.2, 0.1, 0), (0.1, -0.2, 0)
        _, ti, _, _ = dipoles(r, mi, mj, 0.008)
        h = 1e-6
        def rotation(phi):
            return (mi[0] * math.cos(phi) - mi[1] * math.sin(phi),
                    mi[0] * math.sin(phi) + mi[1] * math.cos(phi), 0)
        gradient = (dipoles(r, rotation(h), mj, 0.008)[3] -
                    dipoles(r, rotation(-h), mj, 0.008)[3]) / (2 * h)
        self.assertAlmostEqual(ti[2], -gradient, places=10)

    def test_frottement_dissipe(self):
        for w in (-10, -0.1, 0, 0.1, 10):
            self.assertLessEqual(w * frottement(w, 0.024, 0.01, 0.05), 0)

    def test_moteur_freinage_et_limites(self):
        p = Parametres()
        self.assertLess(moteur_cc(0, 1, p)[0], 0)
        self.assertGreater(moteur_cc(0, -1, p)[0], 0)
        for voltage in (-100, 0, 100):
            for w in (-100, 0, 100):
                couple, courant, u = moteur_cc(voltage, w, p)
                self.assertLessEqual(abs(couple), p.couple_max)
                self.assertLessEqual(abs(courant), p.courant_max)
                self.assertLessEqual(abs(u), p.tension_max)

    def test_masses_et_unites(self):
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
