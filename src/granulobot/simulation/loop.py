"""La boucle de simulation : mesures, forces, pas Chrono, puis bilan et sorties."""
import json
import math

from granulobot.chrono_env import omega, xyz
from granulobot.model.magnets import appliquer_magnetisme
from granulobot.model.motor import appliquer_moteur
from granulobot.model.unit import noms, paires
from granulobot.output.analysis import analyser
from granulobot.output.animation import animation
from granulobot.simulation.recording import ecrire_sorties, mesure
from granulobot.simulation.world import creer_systeme


def simuler(p, sortie, gif=True, verbose=True):
    p.verifier()
    sys, robots, references = creer_systeme(p)
    NOMS = noms(robots)
    rows, min_distances = [], {paire: 2 * p.R for paire in paires(robots)}
    force_max, vitesse_max, energie_elec = 0.0, 0.0, 0.0
    periode = max(1, round(1 / (p.frequence_mesures * p.dt)))
    nsteps = round(p.duree / p.dt)
    if verbose:
        print(f"Mode={p.mode_moteur}, dt={p.dt:g} s, durée={p.duree:g} s", flush=True)
        print(f"Masse totale/unité={p.M:g} kg ; moment estimé/aimant={p.moment_aimant:.3f} A.m²", flush=True)
    positions_initiales = [xyz(u.corps.GetPos()) for u in robots]
    for k in range(nsteps + 1):
        t = sys.GetChTime()
        if k % periode == 0 or k == nsteps:
            row = mesure(t, sys, robots, p)
            for n, u in zip(noms(robots), robots):
                for actif, suffixe in ((True, "actif"), (False, "libre")):
                    _, _, pos, _ = u.aimant(actif, p)
                    row[f"{n}_aimant_{suffixe}_x_m"] = pos[0]
                    row[f"{n}_aimant_{suffixe}_y_m"] = pos[1]
            rows.append(row)
        for i, j in paires(robots):
            a, b = robots[i].corps.GetPos(), robots[j].corps.GetPos()
            min_distances[i, j] = min(min_distances[i, j], math.hypot(b.x - a.x, b.y - a.y))
        vitesse_max = max(vitesse_max, *(abs(omega(u.corps)) for u in robots))
        if k == nsteps:
            break
        for i, u in enumerate(robots):
            u.vider_forces()
            appliquer_moteur(u, i, t, p)
        _, fm = appliquer_magnetisme(robots, p)
        force_max = max(force_max, fm)
        energie_elec += sum(u.tension * u.courant for u in robots) * p.dt
        sys.DoStepDynamics(p.dt)
        if verbose and (k + 1) % max(1, round(0.5 / p.dt)) == 0:
            print(f"t={sys.GetChTime():.2f} s  contacts(sol compris)={sys.GetNumContacts()}  "
                  f"vitesses corps={[round(omega(u.corps), 3) for u in robots]} rad/s", flush=True)
    bilan = {
        "recouvrement_max_m": {NOMS[i] + NOMS[j]: max(0, 2 * p.R - d) for (i, j), d in min_distances.items()},
        "omega_corps_max_rad_s": vitesse_max, "force_aimant_max_N": force_max,
        "energie_electrique_signee_J": energie_elec,
        "deplacement_final_m": {n: math.hypot(u.corps.GetPos().x - pos[0], u.corps.GetPos().y - pos[1])
                                for n, u, pos in zip(NOMS, robots, positions_initiales)},
        "vitesse_actif_final_rad_s": {n: omega(u.actif) - omega(u.corps) for n, u in zip(noms(robots), robots)},
        "duree_simulee_s": sys.GetChTime(),
    }
    bilan["accrochage"] = analyser(rows, p)
    ecrire_sorties(rows, p, bilan, sortie)
    if gif:
        animation(rows, p, sortie)
    if verbose:
        print(json.dumps(bilan, indent=2, ensure_ascii=False), flush=True)
        print(f"Résultats : {sortie} (.csv, .json" + (", .gif)" if gif else ")"), flush=True)
    return rows, bilan
