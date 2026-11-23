"""GIF d'un run, redessiné à partir des lignes mesurées ; aucun calcul physique."""
from bisect import bisect_left
import math


def animation(rows, p, sortie):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.patches import Circle
    # Le CSV est enregistré à 200 Hz ; la vidéo reste à 25 images/s.
    temps = [r['t_s'] for r in rows]
    selection = []
    for k in range(round(temps[-1] * p.fps) + 1):
        cible = k / p.fps
        i = min(bisect_left(temps, cible), len(rows) - 1)
        if i and abs(temps[i-1] - cible) < abs(temps[i] - cible):
            i -= 1
        selection.append(rows[i])
    rows = selection
    NOMS = tuple(chr(ord("A") + i) for i in range(p.nombre_robots))
    fig, ax = plt.subplots(figsize=(7, 7))
    xs = [r[f"{n}_x_m"] for r in rows for n in NOMS]
    ys = [r[f"{n}_y_m"] for r in rows for n in NOMS]
    xc, yc = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    lim = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 1.5 * p.R
    ax.set(xlim=(xc - lim, xc + lim), ylim=(yc - lim, yc + lim),
           xlabel="x (m)", ylabel="y (m)", aspect="equal")
    cercles, reperes, traces, actifs, libres, etiquettes = [], [], [], [], [], []
    for i, n in enumerate(NOMS):
        c = f"C{i}"
        cercle = Circle((0, 0), p.R, facecolor=c, edgecolor=c, alpha=0.2)
        ax.add_patch(cercle)
        cercles.append(cercle)
        reperes.append(ax.plot([], [], color=c, lw=2, label="Orientation du corps" if i == 0 else None)[0])
        traces.append(ax.plot([], [], ":", color=c, alpha=0.6)[0])
        for liste, couleur, etiquette in ((actifs, 'red', 'Aimant motorisé'),
                                           (libres, 'blue', 'Aimant libre')):
            aimant = Circle((0, 0), p.diametre_aimant_ext / 2, facecolor=couleur,
                            edgecolor='black', lw=0.7, alpha=0.85,
                            label=etiquette if i == 0 else None)
            ax.add_patch(aimant)
            liste.append(aimant)
        etiquettes.append(ax.text(0, 0, n, ha="center", va="center"))
    ax.legend(loc="upper right", fontsize=8)
    titre = ax.set_title("")

    def maj(k):
        r = rows[k]
        for i, n in enumerate(NOMS):
            x, y, a = r[f"{n}_x_m"], r[f"{n}_y_m"], r[f"{n}_angle_corps_rad"]
            cercles[i].center = (x, y)
            reperes[i].set_data([x, x + p.R * math.cos(a)], [y, y + p.R * math.sin(a)])
            traces[i].set_data([e[f"{n}_x_m"] for e in rows[:k + 1]],
                               [e[f"{n}_y_m"] for e in rows[:k + 1]])
            for artiste, suffixe in ((actifs[i], "actif"), (libres[i], "libre")):
                # Position exacte enregistrée, même si le pivot dérive numériquement.
                artiste.center = (r[f"{n}_aimant_{suffixe}_x_m"],
                                   r[f"{n}_aimant_{suffixe}_y_m"])
            etiquettes[i].set_position((x, y))
        titre.set_text(f"{p.nombre_robots} granulobots — commande en {p.mode_moteur}\nt = {r['t_s']:.2f} s")
        return (*cercles, *reperes, *traces, *actifs, *libres, *etiquettes, titre)

    anim = FuncAnimation(fig, maj, frames=len(rows), interval=1000 / p.fps)
    anim.save(sortie.with_suffix(".gif"), writer=PillowWriter(fps=p.fps))
    plt.close(fig)
