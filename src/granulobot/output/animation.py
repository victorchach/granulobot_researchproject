"""GIF of a run, redrawn from the measured rows; no physics computed.

The text drawn in the GIF is still in French; spec 005 translates it.
"""
from bisect import bisect_left
import math


def animate(rows, p, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.patches import Circle
    # The CSV is recorded at 200 Hz; the video stays at 25 frames/s.
    times = [r['t_s'] for r in rows]
    selection = []
    for k in range(round(times[-1] * p.fps) + 1):
        target = k / p.fps
        i = min(bisect_left(times, target), len(rows) - 1)
        if i and abs(times[i-1] - target) < abs(times[i] - target):
            i -= 1
        selection.append(rows[i])
    rows = selection
    NAMES = tuple(chr(ord("A") + i) for i in range(p.nombre_robots))
    fig, ax = plt.subplots(figsize=(7, 7))
    xs = [r[f"{n}_x_m"] for r in rows for n in NAMES]
    ys = [r[f"{n}_y_m"] for r in rows for n in NAMES]
    xc, yc = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    lim = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 1.5 * p.R
    ax.set(xlim=(xc - lim, xc + lim), ylim=(yc - lim, yc + lim),
           xlabel="x (m)", ylabel="y (m)", aspect="equal")
    circles, markers, trails, actives, frees, labels = [], [], [], [], [], []
    for i, n in enumerate(NAMES):
        c = f"C{i}"
        circle = Circle((0, 0), p.R, facecolor=c, edgecolor=c, alpha=0.2)
        ax.add_patch(circle)
        circles.append(circle)
        markers.append(ax.plot([], [], color=c, lw=2, label="Orientation du corps" if i == 0 else None)[0])
        trails.append(ax.plot([], [], ":", color=c, alpha=0.6)[0])
        for artists, colour, label in ((actives, 'red', 'Aimant motorisé'),
                                       (frees, 'blue', 'Aimant libre')):
            magnet = Circle((0, 0), p.diametre_aimant_ext / 2, facecolor=colour,
                            edgecolor='black', lw=0.7, alpha=0.85,
                            label=label if i == 0 else None)
            ax.add_patch(magnet)
            artists.append(magnet)
        labels.append(ax.text(0, 0, n, ha="center", va="center"))
    ax.legend(loc="upper right", fontsize=8)
    title = ax.set_title("")

    def update(k):
        r = rows[k]
        for i, n in enumerate(NAMES):
            x, y, a = r[f"{n}_x_m"], r[f"{n}_y_m"], r[f"{n}_angle_corps_rad"]
            circles[i].center = (x, y)
            markers[i].set_data([x, x + p.R * math.cos(a)], [y, y + p.R * math.sin(a)])
            trails[i].set_data([e[f"{n}_x_m"] for e in rows[:k + 1]],
                               [e[f"{n}_y_m"] for e in rows[:k + 1]])
            for artist, suffix in ((actives[i], "actif"), (frees[i], "libre")):
                # Exact recorded position, even if the pivot drifts numerically.
                artist.center = (r[f"{n}_aimant_{suffix}_x_m"],
                                 r[f"{n}_aimant_{suffix}_y_m"])
            labels[i].set_position((x, y))
        title.set_text(f"{p.nombre_robots} granulobots — commande en {p.mode_moteur}\nt = {r['t_s']:.2f} s")
        return (*circles, *markers, *trails, *actives, *frees, *labels, title)

    anim = FuncAnimation(fig, update, frames=len(rows), interval=1000 / p.fps)
    anim.save(output.with_suffix(".gif"), writer=PillowWriter(fps=p.fps))
    plt.close(fig)
