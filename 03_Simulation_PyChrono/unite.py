import pychrono as chrono

# --- Paramètres (valeurs provisoires, à remplacer par celles de l'article) ---
R      = 0.03    # rayon de l'unité (m)
H      = 0.02    # épaisseur (m)
M_DISQ = 0.05    # masse du disque (kg)
M_ROT  = 0.03    # masse du rotor excentré (kg)
E      = 0.02    # excentricité du rotor (m)
COUPLE = 0.007    # couple moteur (N.m), doit dépasser M_ROT*g*E ~ 0.006
MU     = 0.8     # frottement disque / sol

sys = chrono.ChSystemNSC()
sys.SetGravitationalAcceleration(chrono.ChVector3d(0, -9.81, 0))

mat = chrono.ChContactMaterialNSC()
mat.SetFriction(MU)

# Sol fixe, dessus à y = 0
sol = chrono.ChBodyEasyBox(1.0, 0.02, 0.2, 1000, True, True, mat)
sol.SetPos(chrono.ChVector3d(0, -0.01, 0))
sol.SetFixed(True)
sys.AddBody(sol)

# Corps de l'unité : cylindre d'axe Z
volume = 3.14159 * R**2 * H
disque = chrono.ChBodyEasyCylinder(chrono.ChAxis_Z, R, H, M_DISQ / volume, True, True, mat)
disque.SetPos(chrono.ChVector3d(0, R, 0))
sys.AddBody(disque)

# Rotor excentré (pas de collision)
rotor = chrono.ChBody()
rotor.SetMass(M_ROT)
rotor.SetInertiaXX(chrono.ChVector3d(1e-6, 1e-6, 1e-6))
rotor.SetPos(chrono.ChVector3d(E, R, 0))
sys.AddBody(rotor)

# Moteur à couple entre disque et rotor, axe Z, centré sur l'axe du disque
moteur = chrono.ChLinkMotorRotationTorque()
moteur.Initialize(rotor, disque, chrono.ChFramed(chrono.ChVector3d(0, R, 0)))
moteur.SetTorqueFunction(chrono.ChFunctionConst(COUPLE))
sys.AddLink(moteur)

import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle

# --- Simulation : on enregistre l'état toutes les 20 ms ---
dt = 1e-3
T_FIN = 0.5
historique = []
pas = 0
while sys.GetChTime() < T_FIN:
    sys.DoStepDynamics(dt)
    pas += 1
    if pas % 10 == 0:
        p = disque.GetPos()
        q = disque.GetRot()
        angle = 2 * math.atan2(q.e3, q.e0)   # rotation autour de Z
        r = rotor.GetPos()
        historique.append((p.x, p.y, angle, r.x, r.y))

# --- Animation ---
fig, ax = plt.subplots(figsize=(8, 3))
x_max = max(h[0] for h in historique) + 0.1
x_min = min(h[0] for h in historique) - 0.1
ax.set_xlim(x_min, x_max)
ax.set_ylim(-0.02, 2 * R + 0.04)
ax.set_aspect("equal")
ax.axhline(0, color="k")

cercle = Circle((0, R), R, fill=False, lw=2)
ax.add_patch(cercle)
repere, = ax.plot([], [], "b-", lw=2)          # trait qui montre la rotation
masse,  = ax.plot([], [], "ro", ms=8)          # rotor excentré
titre = ax.set_title("")

def maj(i):
    x, y, a, rx, ry = historique[i]
    cercle.center = (x, y)
    repere.set_data([x, x + R * math.cos(a)], [y, y + R * math.sin(a)])
    masse.set_data([rx], [ry])
    titre.set_text(f"t = {i * 10 * dt:.2f} s")
    return cercle, repere, masse, titre

anim = FuncAnimation(fig, maj, frames=len(historique), interval=60)
anim.save("unite.gif", writer=PillowWriter(fps=15))
print("Animation enregistrée : unite.gif")