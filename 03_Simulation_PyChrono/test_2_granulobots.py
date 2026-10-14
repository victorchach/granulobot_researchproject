"""Banc à deux unités mobiles, une paire actif A / libre B face à face.

Par défaut : un moteur actif à 0,3 V. Les centres restent libres.
    python test_2_granulobots.py --sans-moteurs
    python test_2_granulobots.py --liaison-ideale
    python test_2_granulobots.py --tensions 0.3 0 0

Toutes les options du simulateur commun sont disponibles. Les trois consignes
A/B/C sont conservées pour partager les paramètres avec le triangle ; C est
ignoré dans ce banc. Les résultats ont leur propre nom, sans écraser le triangle.
"""
import sys
from pathlib import Path
import test_3_granulobots as simulateur
from granulobot_physics import Parametres

if __name__ == '__main__':
    simulateur.PARAMETRES = Parametres(nombre_robots=2, tensions_cibles=(0.3, 0, 0))
    if '--sortie' not in sys.argv:
        sys.argv.extend(['--sortie', str(Path(__file__).with_suffix(''))])
    simulateur.main()
