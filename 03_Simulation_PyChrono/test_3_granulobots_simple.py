"""Trois granulobots mobiles en triangle, vus de dessus (plan X-Y).

Les contacts avec frottement transmettent les efforts aux deux voisines.
Trois ressorts approximent l'attraction magnétique, sans rigidifier le
triangle. Les cylindres sont lisses, sans dents ni rotors internes :
les couples appliqués sont externes, pas encore ceux d'un moteur interne.
Les liaisons planes bloquent seulement Z et le basculement ; toutes les
unités sont libres en translation X-Y et en rotation autour de Z.
"""
import math
from itertools import combinations
from pathlib import Path

from chrono_headless import chrono
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle

# Unités SI : dimensions mesurées en cm, converties en mètres ; masse en kg.
R, H, M = 3.5e-2, 5e-2, 0.098
RHO = M / (math.pi * R**2 * H)
MU = 0.6
F_MAG = 3.0             # attraction provisoire au contact (N)
K_MAG = 4000.0         # ressort magnétique, distinct du contact NSC (N/m)
D_MAG = 2.0            # amortissement radial (N.s/m)
COUPLES = (0.0001, 0.0001, 0.0001)  # A, B, C (N.m), signe = sens de rotation
T_FIN, DT, PAS_ENREG = 2.5, 1e-4, 200
NOMS = ("A", "B", "C")
PAIRES = tuple(combinations(range(3), 2))

sys = chrono.ChSystemNSC()
sys.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)
sys.SetSolverType(chrono.ChSolver.Type_PSOR)
sys.GetSolver().AsIterative().SetMaxIterations(300)
sys.SetMaxPenetrationRecoverySpeed(0.5)
sys.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, 0))
# Tolérances de collision en mètres, avant création des corps.
chrono.ChCollisionModel.SetDefaultSuggestedEnvelope(1e-5)
chrono.ChCollisionModel.SetDefaultSuggestedMargin(1e-5)
mat = chrono.ChContactMaterialNSC()
mat.SetFriction(MU)
mat.SetRestitution(0.0)

# Repère sans géométrie ni collision, utilisé seulement pour définir le plan.
# Aucun granulobot n'est fixe : les liaisons laissent libres X, Y et rotation Z.
repere = chrono.ChBody()
repere.SetFixed(True)
sys.AddBody(repere)

# Triangle équilatéral de côté 2R, centré à l'origine.
positions = ((-R, -R / math.sqrt(3)), (R, -R / math.sqrt(3)),
             (0, 2 * R / math.sqrt(3)))
robots, plans = [], []
for x, y in positions:
    b = chrono.ChBodyEasyCylinder(chrono.ChAxis_Z, R, H, RHO, True, True, mat)
    b.SetPos(chrono.ChVector3d(x, y, 0))
    b.SetFixed(False)
    sys.AddBody(b)
    plan = chrono.ChLinkLockPlanar()
    plan.Initialize(b, repere, chrono.ChFramed(b.GetPos()))
    sys.AddLink(plan)
    robots.append(b)
    plans.append(plan)

liens = []
for i, j in PAIRES:
    lien = chrono.ChLinkTSDA()
    lien.Initialize(robots[i], robots[j], True,
                    chrono.ChVector3d(0, 0, 0), chrono.ChVector3d(0, 0, 0))
    lien.SetRestLength(2 * R - F_MAG / K_MAG)
    lien.SetSpringCoefficient(K_MAG)
    lien.SetDampingCoefficient(D_MAG)
    sys.AddLink(lien)
    liens.append(lien)
accumulateurs = [b.AddAccumulator() for b in robots]


def etat():
    resultat = []
    for b in robots:
        p, q = b.GetPos(), b.GetRot()
        resultat.append((p.x, p.y, 2 * math.atan2(q.e3, q.e0)))
    return resultat


frames = [(0.0, etat())]
dmin = {paire: 2 * R for paire in PAIRES}
ecart_z = 0.0
for pas in range(1, round(T_FIN / DT) + 1):
    for b, idx, couple in zip(robots, accumulateurs, COUPLES):
        b.EmptyAccumulator(idx)
        b.AccumulateTorque(idx, chrono.ChVector3d(0, 0, couple), False)
    sys.DoStepDynamics(DT)
    points = [b.GetPos() for b in robots]
    ecart_z = max(ecart_z, *(abs(p.z) for p in points))
    distances = {}
    for i, j in PAIRES:
        d = math.hypot(points[j].x - points[i].x, points[j].y - points[i].y)
        distances[i, j] = d
        dmin[i, j] = min(dmin[i, j], d)
    if pas % PAS_ENREG == 0:
        frames.append((sys.GetChTime(), etat()))
    if pas % (5 * PAS_ENREG) == 0:
        mesures = "  ".join(f"{NOMS[i]}{NOMS[j]}={d * 1000:.2f} mm"
                             for (i, j), d in distances.items())
        print(f"t={sys.GetChTime():.2f}  contacts={sys.GetNumContacts()}  {mesures}")

# Cadrage de toutes les trajectoires, sans suivre artificiellement le triangle.
fig, ax = plt.subplots(figsize=(6, 6))
xs = [x for _, e in frames for x, _, _ in e]
ys = [y for _, e in frames for _, y, _ in e]
xc, yc = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
lim = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 1.5 * R
ax.set_xlim(xc - lim, xc + lim)
ax.set_ylim(yc - lim, yc + lim)
ax.set_aspect("equal")
ax.set_xlabel("x (m)")
ax.set_ylabel("y (m)")
cercles, marqueurs, traces, etiquettes = [], [], [], []
for i, nom in enumerate(NOMS):
    couleur = f"C{i}"
    cercle = Circle((0, 0), R, facecolor=couleur, edgecolor=couleur, alpha=0.3)
    ax.add_patch(cercle)
    cercles.append(cercle)
    marqueurs.append(ax.plot([], [], color=couleur, lw=2)[0])
    traces.append(ax.plot([], [], ":", color=couleur, lw=1)[0])
    etiquettes.append(ax.text(0, 0, nom, ha="center", va="center"))
titre = ax.set_title("")


def maj(k):
    t, e = frames[k]
    for i, (x, y, angle) in enumerate(e):
        cercles[i].center = (x, y)
        marqueurs[i].set_data([x, x + R * math.cos(angle)],
                              [y, y + R * math.sin(angle)])
        traces[i].set_data([f[1][i][0] for f in frames[:k + 1]],
                           [f[1][i][1] for f in frames[:k + 1]])
        etiquettes[i].set_position((x, y))
    titre.set_text(f"Trois granulobots mobiles — vue de dessus\nt = {t:.2f} s")
    return (*cercles, *marqueurs, *traces, *etiquettes, titre)


anim = FuncAnimation(fig, maj, frames=len(frames), interval=PAS_ENREG * DT * 1000)
sortie = Path(__file__).with_suffix(".gif")
anim.save(sortie, writer=PillowWriter(fps=round(1 / (PAS_ENREG * DT))))
plt.close(fig)
print(f"Animation enregistrée : {sortie}")
for (i, j), d in dmin.items():
    print(f"Recouvrement maximal {NOMS[i]}{NOMS[j]} : {max(0, 2 * R - d) * 1000:.3f} mm")
print(f"Écart vertical maximal : {ecart_z:.3e} m")
for nom, b, (x0, y0) in zip(NOMS, robots, positions):
    p = b.GetPos()
    print(f"Déplacement final {nom} : {math.hypot(p.x - x0, p.y - y0) * 1000:.2f} mm")
