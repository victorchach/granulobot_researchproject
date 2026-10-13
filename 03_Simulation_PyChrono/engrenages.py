import math
import pychrono as chrono
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle

# --- Paramètres du granulobot (briefing / article) ---
R, H, M = 0.024, 0.062, 0.098
RHO = M / (math.pi * R**2 * H)
MU = 0.6
F_MAG = 3.0       # attraction magnétique entre voisines (N), provisoire
TAU = 0.0005      # couple d'entraînement de la paire (N.m), provisoire
T_FIN = 2.5

sys = chrono.ChSystemNSC()
sys.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)
try:
    sys.SetSolverType(chrono.ChSolver.Type_PSOR)
    sys.GetSolver().AsIterative().SetMaxIterations(300)
    print("solveur : 300 itérations")
except Exception as e:
    print("solveur non réglé :", e)

try:
    sys.SetMaxPenetrationRecoverySpeed(0.5)
    print("vitesse de correction réglée")
except Exception as e:
    print("recovery non réglé :", e)
sys.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, 0))   # test sans gravité

mat = chrono.ChContactMaterialNSC()
mat.SetFriction(MU)
mat.SetRestitution(0.0)

def unite(y, z, fixe=False):
    b = chrono.ChBodyEasyCylinder(chrono.ChAxis_X, R, H, RHO, True, True, mat)
    b.SetPos(chrono.ChVector3d(0, y, z))
    b.SetFixed(fixe)
    sys.AddBody(b)
    return b

A = unite(0, 0.2, fixe=True)
B = unite(2 * R, 0.2)

k = 4000.0
lien = chrono.ChLinkTSDA()
lien.Initialize(A, B, True, chrono.ChVector3d(0, 0, 0), chrono.ChVector3d(0, 0, 0))
lien.SetRestLength(2 * R - F_MAG / k)
lien.SetSpringCoefficient(k)
lien.SetDampingCoefficient(2.0)
sys.AddLink(lien)

idxA = A.AddAccumulator()
idxB = B.AddAccumulator()

def deroule(angle, precedent, cumul):
    d = (angle - precedent + math.pi) % (2 * math.pi) - math.pi
    return cumul + d

def angle_spin(b):
    q = b.GetRot()
    return 2 * math.atan2(q.e1, q.e0)      # rotation autour de X

def angle_orbite():
    pA, pB = A.GetPos(), B.GetPos()
    return math.atan2(pB.z - pA.z, pB.y - pA.y)

dt = 1e-4
pas_enreg = 200                     # une image toutes les 20 ms
pas = 0
spin_prec, orb_prec = angle_spin(B), angle_orbite()
spin = orbite = 0.0
frames = []                         # (yA, zA, yB, zB, spinB_brut, t)
dmin = 1e9

while sys.GetChTime() < T_FIN:
    A.EmptyAccumulator(idxA); B.EmptyAccumulator(idxB)
    B.AccumulateTorque(idxB, chrono.ChVector3d(TAU, 0, 0), False)
    A.AccumulateTorque(idxA, chrono.ChVector3d(-TAU, 0, 0), False)
    sys.DoStepDynamics(dt)
    pA, pB = A.GetPos(), B.GetPos()
    dmin = min(dmin, math.hypot(pB.y - pA.y, pB.z - pA.z))
    pas += 1

    s, o = angle_spin(B), angle_orbite()
    spin = deroule(s, spin_prec, spin);     spin_prec = s
    orbite = deroule(o, orb_prec, orbite);  orb_prec = o

    if pas % pas_enreg == 0:
        pA, pB = A.GetPos(), B.GetPos()
        frames.append((pA.y, pA.z, pB.y, pB.z, s, sys.GetChTime()))
        ratio = spin / orbite if abs(orbite) > 0.05 else float("nan")
        dist = math.hypot(pB.y - pA.y, pB.z - pA.z) / (2 * R)
        print(f"t={sys.GetChTime():.2f}  contacts={sys.GetNumContacts()}  "
              f"orbite={orbite:+.2f}  spin={spin:+.2f}  "
              f"spin/orbite={ratio:+.2f}  dist={dist:.3f}x2R")

# --- Animation (plan Y-Z) ---
fig, ax = plt.subplots(figsize=(6, 6))
lim = 3.5 * R
yc, zc = frames[0][0] + R, frames[0][1]
ax.set_xlim(yc - lim, yc + lim)
ax.set_ylim(zc - lim, zc + lim)
ax.set_aspect("equal")
ax.set_xlabel("y (m)"); ax.set_ylabel("z (m)")

cA = Circle((0, 0), R, fill=False, lw=2, color="k")
cB = Circle((0, 0), R, fill=False, lw=2, color="C0")
ax.add_patch(cA); ax.add_patch(cB)
mA, = ax.plot([], [], "k-", lw=2)      # repère de rotation de A
mB, = ax.plot([], [], "C0-", lw=2)     # repère de rotation de B
trace, = ax.plot([], [], ":", color="gray", lw=1)
titre = ax.set_title("")
chemin = []

def maj(i):
    yA, zA, yB, zB, sB, t = frames[i]
    cA.center = (yA, zA); cB.center = (yB, zB)
    mA.set_data([yA, yA + R], [zA, zA])
    mB.set_data([yB, yB + R * math.cos(sB)], [zB, zB + R * math.sin(sB)])
    chemin.append((yB, zB))
    trace.set_data([p[0] for p in chemin], [p[1] for p in chemin])
    titre.set_text(f"t = {t:.2f} s")
    return cA, cB, mA, mB, trace, titre

anim = FuncAnimation(fig, maj, frames=len(frames), interval=60)
anim.save("engrenages.gif", writer=PillowWriter(fps=15))
print("Animation enregistrée : engrenages.gif")
print(f"Recouvrement maximal : {max(0.0, 2 * R - dmin) * 1000:.2f} mm")