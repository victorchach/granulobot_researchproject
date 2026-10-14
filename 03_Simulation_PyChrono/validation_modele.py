"""Vérifications dynamiques PyChrono : réaction moteur et absence de dérive.

Exécuter dans conda chrono : python validation_modele.py
"""
from pathlib import Path
import argparse
import tempfile
import unittest

from granulobot_physics import Parametres
from test_3_granulobots import creer_systeme, appliquer_moteur, omega, simuler


class Dynamique(unittest.TestCase):
    def test_deux_unites_mobiles_et_reference_ideale(self):
        p = Parametres(nombre_robots=2, liaison_ideale=True, duree=0.01,
                       tensions_cibles=(0.3, 0, 0))
        sys, robots, refs = creer_systeme(p)
        self.assertEqual(len(robots), 2)
        self.assertTrue(all(not u.corps.IsFixed() for u in robots))
        with tempfile.TemporaryDirectory() as tmp:
            rows, bilan = simuler(p, Path(tmp) / 'ideal', gif=False)
        paire = bilan['accrochage']['paires']['A_actif/B_libre']
        self.assertLess(abs(paire['distance_finale_m'] - paire['distance_initiale_m']), 1e-6)

    def test_contacts_circulaires_sous_attraction(self):
        # La référence rigide vérifie la géométrie et l'absence de pénétration.
        p = Parametres(duree=0.05, moteur_actif=False,
                       compliance_coques=0, compliance_aimants=0)
        with tempfile.TemporaryDirectory() as tmp:
            rows, bilan = simuler(p, Path(tmp) / "contacts", gif=False)
        self.assertLess(max(bilan["recouvrement_max_m"].values()), 1e-6)
        for n in ("A", "B", "C"):
            self.assertGreaterEqual(rows[-1][f"{n}_z_m"], p.H / 2 - 1e-6)

    def test_deformation_compliante_reste_petite(self):
        p = Parametres(duree=0.05, moteur_actif=False)
        with tempfile.TemporaryDirectory() as tmp:
            rows, bilan = simuler(p, Path(tmp) / 'compliance', gif=False, verbose=False)
        # Avec élasticité, le recouvrement géométrique représente une déformation.
        # Critère de modèle : moins de 0.1 % du rayon, distinct de la référence rigide.
        self.assertLess(max(bilan['recouvrement_max_m'].values()), 0.001 * p.R)

    def test_moteur_interne_conserve_quantite_de_mouvement(self):
        p = Parametres(sol_actif=False, gravite=0, magnetisme_actif=False,
                       frottement_interne_actif=False, mode_moteur="couple",
                       couples_cibles=(0.002, 0, 0), rampe_demarrage=0)
        sys, robots, refs = creer_systeme(p)
        for k in range(500):
            for i, u in enumerate(robots):
                u.vider_forces()
                appliquer_moteur(u, i, sys.GetChTime(), p)
            sys.DoStepDynamics(p.dt)
        u = robots[0]
        self.assertGreater(omega(u.actif), 0)
        self.assertLess(omega(u.corps), 0)
        px = py = lz = 0.0
        for u in robots:
            for b in u.corps_dynamiques():
                pos, vel, m = b.GetPos(), b.GetPosDt(), b.GetMass()
                px += m * vel.x
                py += m * vel.y
                lz += b.GetInertiaXX().z * omega(b) + m * (pos.x * vel.y - pos.y * vel.x)
        self.assertAlmostEqual(px, 0, delta=1e-8)
        self.assertAlmostEqual(py, 0, delta=1e-8)
        self.assertAlmostEqual(lz, 0, delta=2e-8)

    def test_immobile_sans_excitation_et_masse_totale(self):
        p = Parametres(sol_actif=False, gravite=0, moteur_actif=False,
                       magnetisme_actif=False, duree=0.01)
        with tempfile.TemporaryDirectory() as tmp:
            rows, bilan = simuler(p, Path(tmp) / "repos", gif=False)
        for n in ("A", "B", "C"):
            self.assertAlmostEqual(bilan["deplacement_final_m"][n], 0, delta=1e-9)
            self.assertAlmostEqual(rows[-1][f"{n}_omega_corps_rad_s"], 0, delta=1e-9)
        sys, robots, refs = creer_systeme(p)
        for u in robots:
            self.assertAlmostEqual(sum(b.GetMass() for b in u.corps_dynamiques()), p.M)

    def test_roue_exterieure_tourne_independamment(self):
        p = Parametres(sol_actif=False, gravite=0, moteur_actif=False,
                       magnetisme_actif=False, couple_frottement_roue=0,
                       viscosite_roue=0, frottement_interne_actif=False,
                       jeu_initial=0.01)
        sys, robots, refs = creer_systeme(p)
        u = robots[0]
        from chrono_headless import chrono
        self.assertFalse(u.roue.IsFixed())
        u.roue.SetAngVelParent(chrono.ChVector3d(0, 0, 1))
        for _ in range(100):
            sys.DoStepDynamics(p.dt)
        self.assertAlmostEqual(omega(u.roue), 1, delta=1e-6)
        self.assertAlmostEqual(omega(u.corps), 0, delta=1e-6)

    def test_contacts_sous_moteurs_alimentes(self):
        p = Parametres(duree=0.02, rampe_demarrage=0)
        with tempfile.TemporaryDirectory() as tmp:
            rows, bilan = simuler(p, Path(tmp) / 'alimentation', gif=False, verbose=False)
        self.assertLess(max(bilan['recouvrement_max_m'].values()), 0.001 * p.R)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--animation", action="store_true", help="Générer l'animation finale après les tests")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Dynamique)
    resultat = unittest.TextTestRunner(verbosity=2).run(suite)
    if not resultat.wasSuccessful():
        raise SystemExit(1)
    if args.animation:
        simuler(Parametres(), Path(__file__).with_name("test_3_granulobots"))
