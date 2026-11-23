"""PyChrono dynamics checks: motor reaction and no drift.

Run in conda chrono, from the repo root:
    PYTHONPATH=src python tests/test_dynamics.py   (or make validate)
"""
from pathlib import Path
import argparse
import tempfile
import unittest

from granulobot import REPO_ROOT
from granulobot.chrono_env import omega
from granulobot.model.motor import apply_motor
from granulobot.parameters import Parametres
from granulobot.simulation.loop import simulate
from granulobot.simulation.world import create_system


class Dynamics(unittest.TestCase):
    def test_two_mobile_units_and_ideal_reference(self):
        p = Parametres(nombre_robots=2, liaison_ideale=True, duree=0.01,
                       tensions_cibles=(0.3, 0, 0))
        sys, units, refs = create_system(p)
        self.assertEqual(len(units), 2)
        self.assertTrue(all(not u.body.IsFixed() for u in units))
        with tempfile.TemporaryDirectory() as tmp:
            rows, summary = simulate(p, Path(tmp) / 'ideal', gif=False)
        pair = summary['accrochage']['paires']['A_actif/B_libre']
        self.assertLess(abs(pair['distance_finale_m'] - pair['distance_initiale_m']), 1e-6)

    def test_circular_contacts_under_attraction(self):
        # The rigid reference checks the geometry and the absence of penetration.
        p = Parametres(duree=0.05, moteur_actif=False,
                       compliance_coques=0, compliance_aimants=0)
        with tempfile.TemporaryDirectory() as tmp:
            rows, summary = simulate(p, Path(tmp) / "contacts", gif=False)
        self.assertLess(max(summary["recouvrement_max_m"].values()), 1e-6)
        for n in ("A", "B", "C"):
            self.assertGreaterEqual(rows[-1][f"{n}_z_m"], p.H / 2 - 1e-6)

    def test_compliant_deformation_stays_small(self):
        p = Parametres(duree=0.05, moteur_actif=False)
        with tempfile.TemporaryDirectory() as tmp:
            rows, summary = simulate(p, Path(tmp) / 'compliance', gif=False, verbose=False)
        # With elasticity, the geometric overlap stands for a deformation.
        # Model criterion: less than 0.1 % of the radius, unlike the rigid reference.
        self.assertLess(max(summary['recouvrement_max_m'].values()), 0.001 * p.R)

    def test_internal_motor_conserves_momentum(self):
        p = Parametres(sol_actif=False, gravite=0, magnetisme_actif=False,
                       frottement_interne_actif=False, mode_moteur="couple",
                       couples_cibles=(0.002, 0, 0), rampe_demarrage=0)
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
        p = Parametres(sol_actif=False, gravite=0, moteur_actif=False,
                       magnetisme_actif=False, duree=0.01)
        with tempfile.TemporaryDirectory() as tmp:
            rows, summary = simulate(p, Path(tmp) / "rest", gif=False)
        for n in ("A", "B", "C"):
            self.assertAlmostEqual(summary["deplacement_final_m"][n], 0, delta=1e-9)
            self.assertAlmostEqual(rows[-1][f"{n}_omega_corps_rad_s"], 0, delta=1e-9)
        sys, units, refs = create_system(p)
        for u in units:
            self.assertAlmostEqual(sum(b.GetMass() for b in u.dynamic_bodies()), p.M)

    def test_outer_wheel_turns_independently(self):
        p = Parametres(sol_actif=False, gravite=0, moteur_actif=False,
                       magnetisme_actif=False, couple_frottement_roue=0,
                       viscosite_roue=0, frottement_interne_actif=False,
                       jeu_initial=0.01)
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
        p = Parametres(duree=0.02, rampe_demarrage=0)
        with tempfile.TemporaryDirectory() as tmp:
            rows, summary = simulate(p, Path(tmp) / 'powered', gif=False, verbose=False)
        self.assertLess(max(summary['recouvrement_max_m'].values()), 0.001 * p.R)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--animation", action="store_true", help="Générer l'animation finale après les tests")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Dynamics)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    if args.animation:
        simulate(Parametres(), REPO_ROOT / "runs" / "validation_animation")
