# Briefing pour Claude — Simulation multi-granulobots sous PyChrono

Rédigé pour être collé tel quel à un assistant de codage (Claude). Hugo et Victor, étudiants
4A TC à l'INSA Lyon — Projet de Recherche (PIR) au département du Pr. Baudouin Saintyves.
C'est une **année 2** : le simulateur de l'an dernier doit être refait avec des contacts à
contraintes exactes.

---

## 1. Objectif du projet

Refaire la simulation d'un **agrégat de granulobots** (Groupe "Self-Coordinating Robotic
Aggregate", sujet PIR 15) avec **PyChrono** au lieu du simulateur maison de l'an passé
(force-based, à pénalités). Le but scientifique : reproduire numériquement les comportements
de l'article « A self-organizing robotic aggregate using solid and liquid-like collective
states » (Saintyves, Spenko, Jaeger — *Science Robotics*, 2024), en particulier la
transition solide/liquide (jamming) et l'auto-coordination **de plusieurs dizaines de robots**.

Les granulobots sont des **roues-engrenages magnétiques** : chaque unité est un anneau/cylindre
creux (l = 62 mm de large, 2r = 48 mm de diamètre, 98 g) contenant un rotor interne piloté par
un moteur ; l'aimant du rotor (N54, 3×12×15,5 mm) couple magnétiquement l'unité à ses voisines.
C'est ce couplage qui crée à la fois l'attraction (liaison normale) et l'auto-orientation
(réorientation des agrégats par le couple exercé sur les rotors).

**Pourquoi PyChrono / multiplicateurs de Lagrange** (demande explicite de Baudouin) :
l'ancien simulateur avait des limites documentées — **interpénétrations (overlaps)** trop
importantes, **glissement des marqueurs** bleu/rouge, calibration manuelle des raideurs
(k_norm, k_tan). PyChrono NSC impose les **contacts rigides + friction de Coulomb exacte**
via un solveur complémentarité (système LCP) → pas de réglage de raideurs, pas d'overlap.

---

## 2. Setup technique (déjà en place — ne pas changer)

- **Env conda** `chrono`, Python **3.12**, **PyChrono 10.0.0** (canal `projectchrono`).
- Interpréteur : `C:\Users\Hugo\anaconda3\envs\chrono\python.exe`
- Projet : `C:\Users\Hugo\Documents\INSA\4A\Projet Recherche\03_Simulation_PyChrono\`
- Le `.vscode/settings.json` pointe déjà vers cet interpréteur.

### ⚠️ Pièges d'API Chrono 10 (découverts par debug — à respecter absolument)

1. **Il FAUT déclarer le système de collision explicitement**, sinon **0 contact** :
   ```python
   sys.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)
   ```
   Les enum SWIG sont des **symboles plats** : c'est `chrono.ChCollisionSystem.Type_BULLET`
   (pas `ChCollisionSystem.Type.BULLET`). Vieux code à ne pas imiter.
2. Il n'y a **pas** de `SetTimestep()` : le pas se passe à la boucle :
   ```python
   dt = 1e-4
   for k in range(nsteps):
       sys.DoStepDynamics(dt)
   ```
3. **Tunneling** si dt trop grand : à ~4 m/s, un pas de 1e-3 traverse l'enveloppe de contact
   (3 mm). Commencer à `dt = 1e-4`. Pour un simulateur "granulaire à N corps", utiliser
   `sys.GetNumContacts()` en debug.
4. **Pas de visualisation temps-réel** : le module conda de PyChrono 10.0.0 n'inclut PAS
   `vsg3d`/Irrlicht utilisables (le `vsg3d` présent échoue avec `failed loading sdl2 library`).
   → **Simulation headless + post-traitement** (animations matplotlib, export VTK/OBJ).
5. Premier lancement lent (MKL + antivirus) : lancer avec `python -u script.py`.
6. Corps faciles (API exacte vérifiée) :
   ```python
   chrono.ChBodyEasyBox(cx, cy, cz, densite, True, True, material)
   chrono.ChBodyEasySphere(rayon, densite, True, True, material)
   chrono.ChBodyEasyCylinder(chrono.ChAxis_Z, rayon, hauteur, densite, True, True, material)  # axe en 1er arg
   ```
   Collision désactivée par défaut à la création dans certains cas → toujours les derniers
   `True, True` (collide, visual) + `body.SetFixed(bool)` + repositionnement via `body.SetPos(...)`.

---

## 3. Modèle physique d'un granulobot

Données réelles (article) :

| Grandeur | Valeur |
|---|---|
| Rayon roue r | 0,024 m |
| Largeur l | 0,062 m |
| Masse unité | 98 g |
| Aimants rotor | N54, 3×12×15,5 mm |
| Constante moteur Kt | 5,8×10⁻³ N·m/A |
| Couple de friction interne Γf | 0,024 N·m |
| Ratio de réduction moteur β | 5:1 → 1000:1 |
| gravité | g = 9,81 m/s² |

### Forces en jeu (dans l'ordre d'importance pour la sim)

1. **Gravité** : `sys.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, -9.81))` (z est le haut).
2. **Contacts normaux** : avec NSC, la normale est une **contrainte** (impulsion pour empêcher
   l'interpénétration). C'est le cœur du passage "Lagrange". Paramètres physiques utiles :
   `material.SetRestitution(e)` (faible, solides), `chrono.ChMaterialSurfaceNSC().SetContactRecoverySpeed?`
   → en fait se faire guider par les docs. Ne PAS recréer du k_norm/k_tan par pénalités (c'était
   la limitation de l'an dernier).
3. **Friction tangentielle de Coulomb** en NSC : `material.SetFriction(mu)` (μ ≈ 0,5–0,9 pour
   le contact plastique ABS). Le solveur NSC impose `|F_t| ≤ μ |F_n|` **exactement** — c'est ce
   qui manquait à l'ancien simulateur (glissement des marqueurs bleu/rouge).
4. **Magnétisme dipôle–dipôle entre rotors** : chaque rotor porte un moment magnétique m
   (dipôle, perpendiculaire à l'axe du cylindre). Deux rotors i,j interagissent :
   ```
   F_ij = (3 μ0 / 4π r^5) [ (m_i·m_j) r + (m_j·r) m_i + (m_i·r) m_j − (5/r²)(m_i·r)(m_j·r) r ]
   T_ij = (μ0 / 4π r^3) [ (m_i × m_j) + (3/r²)(m_i·r)(m_j × r) ]
   ```
   Cette force s'implémente comme force personnalisée entre les **rotors** de granulobots
   voisins (voir §5). Note : pour le moment, l'ancien simulateur approximait ça par un ressort
   `k_m` + amortisseur `zeta_m` ; à terme on veut la vraie loi dipôle-dipôle.
5. **Actionnement** : le moteur exerce un couple Γ sur le rotor de référence vs la coquille.
   Utiliser `chrono.ChLinkMotorRotationSpeed(...)` (vitesse imposée) ou
   `chrono.ChLinkMotorRotationAngle(...)` (angle imposé) entre 2 corps. Couple interne
   `Γf = 0.024 N·m` pour la friction sèche du train d'engrenages.

### Correspondance ancien simulateur → PyChrono

| Ancien (rapport) | Sens | Équivalent PyChrono |
|---|---|---|
| k_norm, zeta_n | raideur/amortissement normal (pénalité) | **Disparaît** : NSC = contrainte rigide |
| k_tan, zeta_t, mu | glissement tangentiel | `material.SetFriction(mu)` (Coulomb exact) |
| k_m, zeta_m | ressort/amortissement magnétique | Force dipôle-dipôle réelle (à implémenter) |
| dt | pas de temps (stabilité) | `sys.DoStepDynamics(dt)`, dt ≈ 1e-4 |

---

## 4. Comment simuler plusieurs granulobots

**Structurer chaque granulobot en 2 corps + 1 liaison motorisée** (fidèle à l'article) :

- **Coquille** : un `ChBodyEasyCylinder` plein `ChAxis_X` (axe horizontal → il roule comme une
  roue), rayon 0,024, hauteur 0,062, densité ajustée pour ~98 g (vol ≈ 4,5e-4 m³ → ρ ≈ 873 kg/m³).
  (Option plus tard : coquille creuse = deux disques + anneau, ou STL simplifié — les fichiers
  sont dans `04_Design_STL\Granulobot-Design\Mechanical_Design\`.)
- **Rotor** : petit cylindre interne (`ChBodyEasyCylinder`, rayon ~0,005, hauteur 0,04),
  fixes par rapport à la coquille dans le repère, libre en rotation autour de l'axe X.
- **Liaison** : `chrono.ChLinkMotorRotationSpeed()` // rotor ↔ coquille pour imposer la vitesse
  de rotation du rotor ; initialiser avec `chrono.ChFunctionConst(...)`.
- **Magnetique** : N fois 2 rotors → appliquer la force/couple dipôle-dipôle de la §3 sur les
  rotors. Les dipôles m_i pointent radialement et tournent avec le rotor (donc m_i est fonction
  de l'angle rotor).

**Boucle type** :
```python
import pychrono as chrono
sys = chrono.ChSystemNSC()
sys.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)
sys.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, -9.81))
dt = 1e-4

mat = chrono.ChContactMaterialNSC()
mat.SetFriction(0.6)
mat.SetRestitution(0.0)

floor = chrono.ChBodyEasyBox(3, 3, 0.1, 3000, True, True, mat)
floor.SetFixed(True)
floor.SetPos(chrono.ChVector3d(0, 0, -0.05))
sys.Add(floor)

N = 30
robots = []
for i in range(N):
    rotor_vel_target = ...  # à définir
    shell = chrono.ChBodyEasyCylinder(chrono.ChAxis_X, 0.024, 0.062, 873, True, True, mat)
    shell.SetPos(chrono.ChVector3d((i % 6) * 0.05 - 0.125, (i // 6) * 0.05, 0.12 + 0.05 * (i // 6)))
    shell.SetRot(chrono.Q_ROTATE_Y_TO_X)
    sys.Add(shell)
    # + rotor + ChLinkMotorRotationSpeed(rotor, shell)
    robots.append(shell)

traj = []
for k in range(12000):
    sys.DoStepDynamics(dt)
    if k % 200 == 0:
        traj.append([b.GetPos() for b in robots])   # print/plot XZ
# → exporter en .npy puis animer avec matplotlib
```
Penser à :
- **Pattern d'empilement initial** (grille/chaîne/cercle) selon l'expérience à reproduire
  (empilement, marche, chaîne qui roule, anneau...).
- **Faire tourner les rotors de manière coordonnée** pour reproduire le "rolling/escape" :
  sinon sans magnétisme actif et sans moteur, N cylindres ne font que tomber et s'empiler.
- **Chaîne connectée** : placer les robots en contact géométrique (intervalle ≈ 2r) avec une
  légère pré-rotation des rotors pour créer l'attraction initiale.
- **Botteledge performance** : commencer petit (N=10–30), passer à `Type_MULTICORE` et
  `sys.SetNumThreads(...)` seulement après validation physique.

---

## 5. Conseils pour écrire le code

- Suivre les tutos officiels Chrono 10 (API ChVector3d/Quat) :
  https://api.projectchrono.org/tutorials.html — surtout les exemples Python du repo :
  https://github.com/projectchrono/chrono/tree/main/src/demos/python
  (reprendre la structure d'un demo "bricks"/"falling" pour le scaffold multi-corps).
- Docs d'installation (qui précisent que vsg3d n'est pas dans le build conda) :
  https://api.projectchrono.org/10.0.0/pychrono_installation.html
- Documenter dans le code les choix de modélisation (NSC vs SMC, où est le nombre de sous-pas,
  validation).

## 6. Références (fichiers locaux dispos pour lecture)

- `01_Sujet_et_rapports\Sujet_15_PIR_Granulobots_2026.txt` — énoncé du projet.
- `01_Sujet_et_rapports\Rapport_Simulation.txt` — rapport an 1 (limites + params k_m, zeta_m,
  k_tan, zeta_t, mu, k_norm, zeta_n, dt).
- `01_Sujet_et_rapports\scirobotics.adh4130.txt` — article Science Robotics (modèle, params).
- `04_Design_STL\Granulobot-Design\Mechanical_Design\` — STL SolidWorks d'un granulobot
  (à simplifier un jour, pas bloquant).
- Liens annexe du rapport : code http… `drive.google.com/drive/folders/1IwOuEOFEglOjtnz79DD0KLrB8zAPVfoY`,
  vidéos `drive.google.com/drive/folders/1S5lYZyB8FJcPLe9GMYsxXxGFUk_ReVzL`.