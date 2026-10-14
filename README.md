#granulobot_researchproject

## Prérequis

- [conda](https://docs.conda.io/) ou [Miniforge](https://github.com/conda-forge/miniforge) (recommandé sur Mac Apple Silicon)
- PyChrono n'est distribué que via conda : `pip install` ne fonctionne pas.

## Installation

Créer un environnement dédié et y installer PyChrono :

```bash
conda create -n chrono python=3.11
conda activate chrono
conda install -c projectchrono -c conda-forge pychrono
```

Vérifier que l'installation fonctionne :

```bash
python 03_Simulation_PyChrono/chrono_headless.py
```

## Utilisation

À chaque nouvelle session de terminal, activer l'environnement avant de lancer le projet :

```bash
conda activate chrono
python 03_Simulation_PyChrono/test_3_granulobots.py
```

Le test simule trois unités mobiles en triangle, avec une roue motorisée,
un rotor actif, un rotor libre et une seconde roue extérieure libre par unité.
Les moteurs agissent entre rotor actif et
corps, avec leur réaction, plutôt que par un couple externe sur l'agrégat.
Le sol fournit la réaction au poids et les frottements ; les aimants exercent
des forces et des couples entre unités, sans ressort de liaison permanent.
Les contacts latéraux des cylindres parallèles utilisent une géométrie
circulaire analytique, transmise au solveur NSC. Le support plan utilise une
réaction normale, Coulomb et une résistance de torsion `mu_sol * N * 2R/3`.
Le contact au sol Bullet reste sélectionnable par `modele_sol="bullet"`.
Le support équivalent suppose une pression uniforme et sépare les limites
de translation et torsion ; il doit être calibré en mouvement combiné.
Une très faible compliance NSC différencie les coques plastiques et les aimants
métalliques : leurs contacts affleurants parfaitement rigides donnent un
partage de charge ambigu. Les valeurs `compliance_coques=1e-7` et
`compliance_aimants=1e-8` m/N sont des hypothèses à mesurer, pas un ajustement
expérimental. Mettre les deux à zéro permet de reproduire la référence rigide.

Les paramètres se trouvent dans
[`granulobot_physics.py`](03_Simulation_PyChrono/granulobot_physics.py), dans
`Parametres`. Pour un essai ponctuel, on peut aussi les modifier dans
`PARAMETRES = Parametres(...)` au début du script. Toutes les unités sont SI :
mètres, kilogrammes, secondes, radians, newtons, N·m, volts et ampères.

```bash
# Tensions indépendantes pour A, B et C
python 03_Simulation_PyChrono/test_3_granulobots.py --tensions 1 2 3
# Commande en vitesse relative rotor/corps (rad/s), limitée en tension et couple
python 03_Simulation_PyChrono/test_3_granulobots.py --mode vitesse --vitesses 0.3 0.3 0.3
# Isoler le couplage interne en retirant le sol ou le magnétisme
python 03_Simulation_PyChrono/test_3_granulobots.py --sans-sol --sans-magnetisme
```

Le GIF, le CSV des mesures et le JSON des paramètres/hypothèses sont enregistrés
à côté du script. Le GIF utilise le temps physique de la simulation.
`--sans-gif`, `--duree`, `--dt` et `--sortie` permettent des essais plus courts.
L'ancien modèle avec ressorts est conservé dans `test_3_granulobots_simple.py`.

| Paramètres | Origine / limite |
| --- | --- |
| `R=0.035`, `H=0.050` | Dimensions données par Hugo, converties depuis les cm |
| `M=0.098`, masse/inertie active | Article local, à vérifier sur le prototype actuel |
| Réduction 379, Kt, Ke, résistance 9.6 Ω, frottement actif 0.024 N·m | Article, fig. 8 ; pas une calibration du moteur actuel |
| Tensions 3.25 V | Estimation d'un rotor libre à environ un tour en 2 s avec ces paramètres |
| `mu_sol`, `mu_robots`, masses/inerties restantes, excentricités | Estimations à mesurer |
| Aimants Ø8 mm, hauteur 10 mm, affleurants, pôles sur faces plates | Estimations/précisions de Hugo ; centres à 31 mm de l'axe |
| Rémanence et trou éventuel | Rémanence 1.45 T et aimants pleins supposés ; à confirmer |
| Adoucissement magnétique, dt, tolérances de collision | Paramètres numériques, à vérifier par convergence |

Ce modèle conserve une géométrie cylindrique lisse, avec axes verticaux pour
la vue de dessus et un guide contre le basculement. Il ne représente pas
encore les dents ni les collisions internes entre aimants. Le champ des
cylindres à aimantation axiale uniforme est calculé par quadrature des charges
sur les faces, avec interpolation du potentiel pour garder `F=-grad(U)`.
Les centres magnétiques sont supposés à la même hauteur ; l'aimantation et
la force réelle restent à mesurer. Le frottement interne est lissé et ne
reproduit pas un seuil statique exact. Le moteur néglige son inductance et
l'inertie réfléchie de son réducteur. Les effets de roulement/pivotement NSC
et les résistances visqueuses supplémentaires sont disponibles mais nuls
par défaut, pour éviter de compter deux fois une résistance inconnue.
Les aimants sont mécaniquement solidaires de leurs rotors ; leur rotation
propre sur roulements ne change pas le champ axial, mais peut changer le
frottement de contact et reste à modéliser après vérification du prototype.

Les lois moteur et les contraintes utilisent la
[documentation Chrono](https://api.projectchrono.org/motors.html) ; les
paramètres du prototype viennent de `01_Sujet_et_rapports/scirobotics.adh4130.txt`.
Pour vérifier les lois et la réaction du moteur :

```bash
python -m unittest discover -s 03_Simulation_PyChrono -p test_granulobot_physics.py
python 03_Simulation_PyChrono/validation_modele.py
```

## Banc d'accrochage et plan d'essais

Le chargement par `chrono_headless.py` bloque temporairement les imports
optionnels pendant l'import du coeur PyChrono. Il évite le chargement de VSG,
SDL2 et des autres extensions inutilisées, sans modifier l'installation conda.

```bash
# Deux unités mobiles : un moteur actif à 0.3 V, C ignoré
python 03_Simulation_PyChrono/test_2_granulobots.py
# Essai passif, puis attache idéale servant de référence cinématique
python 03_Simulation_PyChrono/test_2_granulobots.py --sans-moteurs
python 03_Simulation_PyChrono/test_2_granulobots.py --liaison-ideale
# Campagne : perturbation, tensions, frottements, 1/2/3 moteurs et convergence
python 03_Simulation_PyChrono/campagne_accrochage.py --duree 0.6 --animation --sortie 03_Simulation_PyChrono/essais_plan
# Analyser un essai enregistré sans importer PyChrono
python 03_Simulation_PyChrono/diagnostic_accrochage.py 03_Simulation_PyChrono/test_3_granulobots.csv
```

Une attache idéale maintient la pose relative des rotors voisins avec une
liaison interne indéformable : aucun centre de granulobot n'est fixé à la
table. Elle n'a ni force d'arrachement ni seuil de rupture et ne valide donc
pas le magnétisme réel. Les sorties de chaque essai sont isolées ; les
résultats antérieurs et le triangle initial restent disponibles pour comparer.

Les bilans distinguent rotation nette/parcourue du corps, rotations absolues
des rotors actif/libre, déplacement des centres, distances des paires,
fraction des images en contact et premier éloignement détecté. Le seuil
d'éloignement de 3 mm est un diagnostic, pas une loi physique de rupture.
Les données sont enregistrées à 200 Hz et le GIF à 25 images/s : une
oscillation rapide ne doit pas être diagnostiquée depuis la seule vidéo.
Le CSV contient aussi les forces et les couples de contact des corps/rotors.

La synthèse de campagne quantifie la sensibilité à `dt` et aux itérations sans
déclarer automatiquement le modèle convergé. Les essais de 0.6 s sont un
premier dépistage ; les cas retenus doivent être prolongés et comparés au réel.
`prototype_hugo.json` conserve les dimensions/pôles fournis séparément des
paramètres encore estimés. `validation/historique/` contient les campagnes
intermédiaires ; `validation/convergence_physique/` mesure la sensibilité du modèle fini.
Les campagnes antérieures à l'ajout de la seconde roue conservent explicitement
`roue_libre_exterieure=false` dans leurs paramètres.

Le prototype comporte deux roues extérieures indépendantes. La roue libre
est désormais un corps dynamique supplémentaire lié par un pivot ; ses
contacts avec les voisins sont distincts de ceux de la roue motorisée.
La vue affiche seulement la partie motorisée. L'épaisseur de 4 mm, la masse
de 8 g et le frottement du pivot restent des estimations ; cette masse est
incluse dans les 98 g de l'unité. `roue_motorisee_en_bas` permet de comparer
les deux orientations sur le support. L'étagement réel des aimants et les
interactions magnétiques entre étages restent à préciser : le champ actuel
suppose leurs centres dans un même plan.
Pour cette étude plane, les centres de masse et les contacts latéraux des
roues sont projetés dans le plan commun : les forces XY et couples Z sont
conservés, les moments de basculement sont omis. Les formes de collision
gardent les deux hauteurs pour le contact au sol Bullet. Le premier essai
avec leviers verticaux et guides Rx/Ry, archivé dans
`validation/diagnostic_deux_roues_3D/`, présentait une pénétration de 1.6 mm
sous moteur ; il sert de diagnostic numérique et ne constitue pas un résultat
physique utilisable.
La limite numérique de correction des pénétrations vaut désormais 10 m/s,
sans imposer une vitesse aux robots. Avec compliance, Chrono plafonne aussi
la réaction à environ `v_correction * dt / C_total` : l'ancienne limite de
0.05 m/s réduisait la réaction des coques à environ 2.5 N alors que les
forces magnétiques estimées atteignent 12 N. Cela causait un enfoncement
artificiel et rendait ce défaut sensible au pas de temps. Voir le
[code des contacts Chrono 10](https://github.com/projectchrono/chrono/blob/10.0.0/src/chrono/physics/ChContactNSC.cpp#L129-L147).
Les campagnes enregistrées avec la limite 0.05 conservent cette valeur ;
elles ne valident pas le modèle corrigé.
`solveur` permet de comparer `PSOR` et `APGD` sans modifier les paramètres
physiques. Le banc de démarrage brutal corrigé est dans
`validation/convergence_contacts_corriges/` : les contrôles courts à pas
nominal passent, mais le cas PSOR à pas divisé par deux atteint encore
90 µm de recouvrement et une rotation différente. La convergence reste
une condition à résoudre avant une prédiction quantitative.

L'essai `validation/triangle_deux_roues_1V.gif` utilise la mécanique plane
corrigée, 1 V par moteur et `mu_robots=0.05`. Sur 0.6 s, les parties motorisées
tournent d'environ 14.5°, les centres dérivent de moins de 0.04 mm et les
rotors actifs ont une vitesse absolue environ 100 fois plus faible que leur
vitesse relative au corps. Les aimants appariés sont au contact après la
mise en place ; le recouvrement maximal des coques est de 3.8 µm.
Ce régime correspond qualitativement à l'observation décrite, avec des
frottements encore estimés. Pour reproduire l'essai :

```bash
python 03_Simulation_PyChrono/test_3_granulobots.py --parametres 03_Simulation_PyChrono/validation/triangle_deux_roues_1V.parametres.json --duree 0.6 --sortie 03_Simulation_PyChrono/validation/triangle_deux_roues_1V
```

La convergence physique n'est pas acquise : à 1 V sur le banc à deux unités,
la campagne `validation/convergence_compliance_1V/` (avant seconde roue)
trouve encore des écarts de déplacement maximal de l'ordre de 1 mm lorsque
le pas est divisé par deux ou les itérations doublées. Les contrôles de
conservation et de géométrie ne remplacent pas cette vérification.
La commande `--rejouer fichier.csv` régénère le GIF depuis les mesures sans
relancer la dynamique, en dessinant les aimants avec leur diamètre physique.

Pour calibrer : relever force d'arrachement et couple de décrochage des
aimants, tension/vitesse du moteur à vide et sous charge, résistance à la
rotation sur la table et au glissement entre coques. `--parametres fichier.json`
charge un objet contenant les champs de `Parametres` (ou la clé `parametres`
d'un bilan existant) ; les champs inconnus sont rejetés. Ne pas reprendre
un réglage uniquement parce que son animation semble correcte.

La méthode de champ fini suit la représentation par charges surfaciques des
[cylindres uniformément aimantés](https://doi.org/10.1016/j.jmmm.2022.169482).
Les calculs vérifient le gradient du potentiel, la limite dipolaire à grande
distance et la sensibilité au raffinement de la quadrature.

## Versions testées

- PyChrono 10.0.0
- Python 3.11
- macOS (Apple Silicon, M4)

Les vérifications de dynamique ajoutées ont également été exécutées avec
Python 3.12 / PyChrono 10 dans l'environnement Windows `chrono` de Hugo,
sans charger les extensions graphiques SDL2.

> Remarque : les noms de classes ont changé entre PyChrono 8 et 9 (par exemple `ChVectorD` est devenu `ChVector3d`). Ce projet est écrit pour la version 10 et peut ne pas fonctionner avec une version plus ancienne.

## Limitations sur Mac Apple Silicon

Les modules `pychrono.fsi`, `pychrono.sensor` et `pychrono.pardisomkl` ne sont pas disponibles sur Mac Apple Silicon.
