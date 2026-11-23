# Model decisions

## 2026-11-10: remove the optional campaign runner

Hugo intentionally deleted `run_simulation_campaign.py` and confirmed that its
README entry and command should also be removed. Do not restore this optional
runner. The simulator, analysis and physical-law tests remain independent of it.
References below describe the historical campaign workflow, not an available
current command.

## 2026-11-10: name scripts after their purpose

At Hugo's request, rename the remaining modules without changing physical laws,
parameters or the CSV/JSON/GIF formats:

| Previous name | Current name |
| --- | --- |
| `test_granulobots.py` (formerly `test_3_granulobots.py`) | `simulate_granulobots.py` |
| `campagne_accrochage.py` | `run_simulation_campaign.py` |
| `diagnostic_accrochage.py` | `analyse_simulation.py` |
| `chrono_headless.py` | `chrono_loader.py` |
| `magnet_cylinders.py` | `magnetic_cylinders.py` |

`granulobot_physics.py` and `test_granulobot_physics.py` keep their descriptive
names. Update Python imports and README commands together. Use `--robots 2`
on the main simulator for the two-unit bench; the old wrapper was already
absent at the time of this rename. Parameter inputs and saved results retain
their names and contents. Old command lines using the renamed scripts must
use the new names; no duplicate compatibility wrappers are retained.

## 2026-11-10: remove the standalone dynamic-check script

At Hugo's explicit request, delete `validation_modele.py` and remove its command
from the README. It was a separate optional verification tool, not a dependency
of the simulator. Keep `test_granulobot_physics.py` for the physical-law tests.
The removed dynamic checks no longer form part of the available test suite.

## 2026-11-10: remove the unused tooth-count parameter

Remove `nombre_dents` from `Parametres`, its validation and new output metadata:
it never affected forces, contact geometry or diagnostics. The tentative count
reported by Hugo remains documented below, but is not a simulation setting.
The simulator and CSV diagnostic ignore this one retired field when reading
old run JSON files, including GIF replay; other unknown parameters still fail.
Existing result files are not edited. Parameters for alternative control modes,
disabled optional forces and numerical settings are retained because they have
implemented uses, even when inactive in the default simulation.

## 2026-11-10: keep executable verification separate from generated results

At Hugo's request, remove the generated historical `validation/` directory,
obsolete `unite.py` and `test_3_granulobots_simple.py` prototypes, outdated
`BRIEF_CLAUDE.md`, old media and default outputs beside the source files.
The two parameter inputs formerly under `validation/` are preserved byte for
byte under `03_Simulation_PyChrono/parametres/`. Historical tracked files remain
available in git history. The five recent experiments in `runs/` are preserved.

At this cleanup stage both verification scripts were kept; the standalone
dynamic-check script was subsequently removed as recorded above. Keep the
simulator and two-unit bench, all physics/import
modules, diagnostics and the campaign runner. Their tests generate temporary
data and do not depend on the removed historical results. Reference documents,
CAD, current model decisions, git metadata and editor settings are retained.

Default output prefixes are now `runs/simulation`, `runs/deux_granulobots`,
`runs/campagne`, resolved from the project root.
Explicit `--sortie` remains supported. Ignore generated outputs in git; keep
parameter inputs outside `runs/`. The README lists the retained files and
commands. This cleanup changes output locations, not physical laws or settings.

## 2026-11-10: alternate the six-unit reference motor biases

Hugo observed same-direction body rotation in `runs/reference_frottements`
(2 s, dt=1e-4). Its JSON confirms six positive 3.25 V commands. That run was
an equal-bias test, not the intended alternating liquid-state reference.

The simulator's `PARAMETRES` now selects biases +3.25, -3.25, +3.25, -3.25,
+3.25, -3.25 V. The explicit inputs `reference_alternee.json` and
`perturbation_1deg.json` use the same alternating commands; the latter adds
only a +1 degree initial offset of A's active rotor. Existing outputs are not
overwritten. The base dataclass targets remain unchanged for historical benches.
Source: Hugo's correction in this session and paper eq. 8 / the agreed roadmap.

Opposite voltages are controls, not imposed body velocities or gear joints.
Rolling contact must be checked using the relative tangential velocity of the
contact points, including centre translation. Opposite absolute body speeds
follow for fixed centres and equal radii; moving centres add an orbital term.
No-slip behaviour, numerical convergence and long-term stability still require
separate checks. A larger Coulomb coefficient alone is not an exact tooth mesh.

## 2026-11-10: effective friction for shallow toothed rims

Source: Hugo's description of the supervisor's advice in this session: steric
contacts must slip much more easily than magnetically coupled contacts; shallow
teeth engage under magnetic attraction. Hugo reports approximately 21 teeth,
unconfirmed, and provides a gear photograph as a qualitative reference only.
This supersedes the earlier assumption that magnetic normal force alone is
sufficient to represent the two regimes.

- The default is now `frottements_differencies=true`. `mu_sterique=0.05` and
  `mu_magnetique=1.0` are **exploratory effective coefficients**, not measurements
  or values inferred from the photograph. The ratio is 20 at equal normal load;
  magnetic compression also raises the available tangential contact force.
- The old `mu_robots=0.6` is retained unchanged. Setting
  `frottements_differencies=false` restores uniform rim friction with that value.
  Historical campaign scenarios explicitly use this uniform model so that
  their existing friction sweeps still mean what their names describe.
- For each pair of touching rims, use
  `mu = mu_sterique + w * (mu_magnetique - mu_sterique)`.
  The Coulomb bound remains `|Ft| <= mu * N`, solved by Chrono NSC. There is
  no added tangential spring, permanent link or rolling resistance.
- The engagement weight `w` is the maximum over attractive magnet pairs on
  the two units, recomputed from their current positions. Both magnets must
  face the rim contact, with lateral offsets below a magnet radius. Their
  vertical extents must overlap. Attraction is determined by axial polarity
  for finite cylinders or by the closing dipole force for the dipole variant.
- Weight decreases smoothly with magnet surface gap and the lateral offset
  of each magnet. Each factor is `1 - 3*x^2 + 2*x^3` for a normalized offset
  clamped to [0, 1]. The maximum surface gap is
  `portee_engagement_magnetique=0.001 m`, an **estimated modelling range**.
  No attractive field, zero magnetic moment, ideal-link mode, or separated
  rims gives no magnetic boost. Initial neighbour labels are not used.
- The same effective coefficient is applied to both rim planes. Real tooth
  profiles, phase, backlash, engagement depth, and vertical stacking are not
  represented. These need actual geometry/measurements before a geometric
  tooth-contact model can be justified. The tentative count of 21 is only a
  documented observation; it does not affect forces. No fabricated 21-fold
  torque or gear constraint is added.
- `mu_aimants` still concerns direct magnet-to-magnet contact, not rim teeth.
  Ground and internal friction and magnetic force laws remain unchanged.

CSV files add `<pair>_mu_jantes` and `<pair>_engagement_magnetique` for all robot
pairs. These describe the instantaneous coefficient and geometric engagement
at the recorded state; they do not measure contact force, prove static sticking,
or assert that a solver contact is active. Old CSV files can still be replayed.
Run JSON files record all new parameters and the effective-tooth assumption.

Use short timestep-convergence and tangential-load checks before interpreting
long trajectories. Calibrate steric sliding and coupled breakaway/rolling
behaviour experimentally. This implementation is not experimental validation.

Chrono API: [SetFriction sets both static and sliding friction](https://api.projectchrono.org/10.0.0/classchrono_1_1_ch_contact_material.html).
