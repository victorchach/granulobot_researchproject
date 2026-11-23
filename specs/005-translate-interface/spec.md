# 005: Translate the interface to English

Status: merged
Branch: `feature/005-translate-interface`

## Need

Last step of the repository reorganisation (`docs/decisions.md`,
2026-11-23). Spec 004 translated the code internals; what still reaches a
file or the command line is French: the `Parametres` class and its fields,
the CLI flags, the CSV columns, the JSON keys and texts, the GIF text, the
campaign scenarios and summary, and `configs/prototype_hugo.json`.

Victor decided: translate everything, keep **no compatibility** with run
files written before this spec.

## What breaks (accepted)

- `make diag` and `make replay` cannot read a CSV/JSON written before this
  spec (French column names and parameter keys). The files themselves stay
  readable as plain CSV/JSON.
- Every command with an old flag fails (`--duree` is now `--duration`, ...).
- `--parametres` files with French keys are rejected ("Unknown parameter").
  The only versioned one, `configs/prototype_hugo.json`, is translated here.
- Hugo's prototype branch uses the old names. The tables below are the
  dictionary for porting it by hand.

Nothing physical changes: the same run gives the same numbers, under new
names.

## Expected behaviour

The tables below are the complete renaming. The glossary of spec 004 applies.

### `Parametres` becomes `Parameters`

Methods: `verifier` → `check`, `dictionnaire` → `to_dict`. Properties:
`masse_corps` → `body_mass`, `rayon_aimant` → `magnet_radius`,
`moment_aimant` → `magnet_moment`.

| Before | After | | Before | After |
| --- | --- | --- | --- | --- |
| `nombre_robots` | `n_units` | | `moteur_actif` | `motors_enabled` |
| `liaison_ideale` | `ideal_link` | | `mode_moteur` | `motor_mode` |
| `perturbation_rotor_rad` | `rotor_perturbation_rad` | | `rapport_reduction` | `gear_ratio` |
| `marge_detection_decrochage` | `detachment_margin` | | `kt`, `ke` | unchanged |
| `R`, `H`, `M` | unchanged | | `resistance_moteur` | `motor_resistance` |
| `roue_libre_exterieure` | `outer_free_wheel` | | `rendement_reducteur` | `gear_efficiency` |
| `masse_roue_libre` | `wheel_mass` | | `tension_max` | `max_voltage` |
| `epaisseur_roue` | `wheel_thickness` | | `courant_max` | `max_current` |
| `roue_motorisee_en_bas` | `motorised_wheel_at_bottom` | | `couple_max` | `max_torque` |
| `couple_frottement_roue` | `wheel_friction_torque` | | `vitesses_cibles` | `target_speeds` |
| `viscosite_roue` | `wheel_viscosity` | | `tensions_cibles` | `target_voltages` |
| `masse_actif` | `active_rotor_mass` | | `couples_cibles` | `target_torques` |
| `masse_libre` | `free_rotor_mass` | | `gain_p_vitesse` | `speed_gain_p` |
| `inertie_actif_pivot` | `active_rotor_inertia` | | `gain_i_vitesse` | `speed_gain_i` |
| `inertie_libre_pivot` | `free_rotor_inertia` | | `rampe_demarrage` | `startup_ramp` |
| `excentricite_actif` | `active_rotor_eccentricity` | | `frottement_interne_actif` | `internal_friction_enabled` |
| `excentricite_libre` | `free_rotor_eccentricity` | | `couple_frottement_actif` | `active_friction_torque` |
| `facteur_inertie_corps` | `body_inertia_factor` | | `couple_frottement_libre` | `free_friction_torque` |
| `mu_robots` | `mu_shells` | | `viscosite_libre` | `free_viscosity` |
| `compliance_coques` | `compliance_shells` | | `vitesse_regularisation` | `regularisation_speed` |
| `compliance_aimants` | `compliance_magnets` | | `magnetisme_actif` | `magnetism_enabled` |
| `restitution` | unchanged | | `contact_aimants` | `magnet_contact` |
| `roulement_contact` | `rolling_resistance` | | `orientation_aimant` | `magnet_orientation` |
| `pivotement_contact` | `spinning_resistance` | | `modele_magnetique` | `magnet_model` |
| `enveloppe_collision` | `collision_envelope` | | `quadrature_radiale` | `radial_quadrature` |
| `marge_collision` | `collision_margin` | | `quadrature_angulaire` | `angular_quadrature` |
| `sol_actif` | `ground_enabled` | | `mu_aimants` | `mu_magnets` |
| `modele_sol` | `ground_model` | | `diametre_aimant_ext` | `magnet_outer_diameter` |
| `facteur_rayon_frottement_sol` | `ground_friction_radius_factor` | | `diametre_aimant_int` | `magnet_inner_diameter` |
| `gravite` | `gravity` | | `epaisseur_aimant` | `magnet_thickness` |
| `mu_sol` | `mu_ground` | | `remanence` | unchanged |
| `largeur_sol` | `ground_width` | | `facteur_moment` | `moment_factor` |
| `epaisseur_sol` | `ground_thickness` | | `retrait_aimant` | `magnet_recess` |
| `resistance_translation` | `translation_damping` | | `adoucissement_magnetique` | `magnetic_softening` |
| `resistance_rotation` | `rotation_damping` | | `interactions_internes` | `internal_interactions` |
| `dt`, `fps` | unchanged | | `jeu_initial` | `initial_gap` |
| `duree` | `duration` | | `frequence_mesures` | `sample_rate` |
| `solveur` | `solver` | | `iterations_solveur` | `solver_iterations` |
| `tolerance_solveur` | `solver_tolerance` | | `vitesse_correction_contact` | `contact_recovery_speed` |

String values: `motor_mode` `tension`/`vitesse`/`couple` →
`voltage`/`speed`/`torque`; `ground_model` `disque_equivalent`/`bullet` →
`equivalent_disc`/`bullet`; `magnet_orientation` `axiale`/`radiale` →
`axial`/`radial`; `magnet_model` `cylindres`/`dipoles` →
`cylinders`/`dipoles`; `solver` unchanged (`PSOR`/`APGD`).

Defaults and their origin comments do not change.

### CLI flags

| `python -m granulobot` | | `scripts/campaign.py` | |
| --- | --- | --- | --- |
| `--robots {2,3}` | `--units {2,3}` | `--duree` | `--duration` |
| `--liaison-ideale` | `--ideal-link` | `--animation` | `--gif` |
| `--parametres FILE` | `--params FILE` | `--essais` | `--scenarios` |
| `--duree` | `--duration` | `--sortie` | `--output` |
| `--dt` | unchanged | | |
| `--mode {tension,vitesse,couple}` | `--mode {voltage,speed,torque}` | | |
| `--tensions A B C` | `--voltages A B C` | | |
| `--vitesses A B C` | `--speeds A B C` | | |
| `--sans-moteurs` | `--no-motors` | | |
| `--sans-magnetisme` | `--no-magnetism` | | |
| `--sans-sol` | `--no-ground` | | |
| `--sans-gif` | `--no-gif` | | |
| `--rejouer CSV` | `--replay CSV` | | |
| `--sortie PATH` | `--output PATH` | | |

`tests/test_dynamics.py --animation` keeps its name. Help texts are
translated. `make` targets and their variables (`NAME`, `ARGS`, `CSV`) do not
change; the Makefile passes `--output` and `--replay`.

### CSV columns (per unit X, and per pair XY)

| Before | After |
| --- | --- |
| `t_s`, `X_x_m`, `X_y_m`, `X_z_m`, `XY_distance_m` | unchanged |
| `contacts_total_sol_compris` | `n_contacts_incl_ground` |
| `X_angle_corps_rad`, `X_angle_actif_rad`, `X_angle_libre_rad`, `X_angle_roue_libre_rad` | `X_body_angle_rad`, `X_active_angle_rad`, `X_free_angle_rad`, `X_wheel_angle_rad` |
| `X_omega_corps_rad_s`, `X_omega_roue_libre_rad_s` | `X_body_omega_rad_s`, `X_wheel_omega_rad_s` |
| `X_omega_actif_relative_rad_s`, `X_omega_libre_relative_rad_s` | `X_active_rel_omega_rad_s`, `X_free_rel_omega_rad_s` |
| `X_vitesse_m_s` | `X_speed_m_s` |
| `X_tension_V`, `X_courant_A` | `X_voltage_V`, `X_current_A` |
| `X_couple_moteur_Nm`, `X_couple_transmis_Nm` | `X_motor_torque_Nm`, `X_transmitted_torque_Nm` |
| `X_contact_{corps,actif,libre,roue_libre}_F{x,y,z}_N` | `X_contact_{body,active,free,wheel}_F{x,y,z}_N` |
| `X_contact_{...}_couple_z_Nm` | `X_contact_{...}_torque_z_Nm` |
| `X_aimant_actif_{x,y}_m`, `X_aimant_libre_{x,y}_m` | `X_active_magnet_{x,y}_m`, `X_free_magnet_{x,y}_m` |

Column order does not change.

### JSON

Top level: `parametres` → `parameters`, `hypotheses` → `assumptions`,
`bilan` → `summary`.

`summary`: `recouvrement_max_m` → `max_overlap_m`, `omega_corps_max_rad_s` →
`max_body_omega_rad_s`, `force_aimant_max_N` → `max_magnet_force_N`,
`energie_electrique_signee_J` → `signed_electrical_energy_J`,
`deplacement_final_m` → `final_displacement_m`, `vitesse_actif_final_rad_s` →
`final_active_rel_omega_rad_s`, `duree_simulee_s` → `simulated_duration_s`,
`accrochage` → `attachment`.

`attachment` (from `analyze`, also printed by `make diag`):
`resolution_temporelle_s` → `time_resolution_s`, `liaison_ideale` →
`ideal_link`, `criteres` → `criteria` (`marge_eloignement_m` →
`separation_margin_m`, `ratio_rotor_absolu_sur_relatif_pour_retenue` →
`hold_ratio_threshold`), `unites` → `units`, `paires` → `pairs`.

- Per unit: `rotation_corps_nette_tours` → `net_body_rotation_turns`,
  `rotation_corps_parcourue_tours` → `total_body_rotation_turns`,
  `rotation_rotor_absolue_nette_tours` → `net_active_rotation_turns`,
  `rotation_libre_absolue_nette_tours` → `net_free_rotation_turns`,
  `deplacement_centre_max_m` → `max_centre_displacement_m`,
  `omega_actif_relative_moyenne_abs_rad_s` → `mean_abs_active_rel_omega_rad_s`,
  `omega_actif_absolue_moyenne_abs_rad_s` → `mean_abs_active_omega_rad_s`,
  `omega_libre_absolue_moyenne_abs_rad_s` → `mean_abs_free_omega_rad_s`,
  `ratio_rotor_absolu_sur_relatif` → `rotor_abs_over_rel_ratio`.
- Pair keys `A_actif/B_libre` → `A_active/B_free`; per pair:
  `distance_initiale_m` → `initial_distance_m`, `distance_min_m` →
  `min_distance_m`, `distance_max_m` → `max_distance_m`, `distance_finale_m`
  → `final_distance_m`, `jeu_lateral_max_m` → `max_side_gap_m`,
  `fraction_echantillons_en_contact` → `contact_sample_fraction`,
  `seuil_eloignement_m` → `separation_threshold_m`,
  `premier_eloignement_detecte_s` → `first_separation_s`,
  `reste_proche_sur_essai` → `stays_close`.

`assumptions`: keys `geometrie` → `geometry` (`rayon_m` → `radius_m`,
`hauteur_m` → `height_m`, `seconde_roue_libre` → `second_free_wheel`,
`epaisseur_jante_estimee_m` → `estimated_rim_thickness_m`,
`roue_motorisee_en_bas_hypothese` → `motorised_wheel_at_bottom_assumed`,
`vue` → `view`), `moteur` → `motor`, `aimants` → `magnets`, `frottement` →
`friction`, `liaison_ideale` → `ideal_link`; `prototype`,
`projection_plane`, `contact`, `validation`, `sources` unchanged. The texts
are translated faithfully, with no new claim.

### GIF

Legend "Orientation du corps" → "Body orientation", "Aimant motorisé" →
"Active magnet", "Aimant libre" → "Free magnet"; title
"N granulobots — commande en MODE" → "N granulobots — MODE control".

### Campaign

Files `synthese.json`, `synthese.txt` → `summary.json`, `summary.txt`, text
translated. Scenario names:

| Before | After | | Before | After |
| --- | --- | --- | --- | --- |
| `passif` | `passive` | | `deux_ideal` | `two_ideal` |
| `passif_perturbe` | `passive_perturbed` | | `deux_ideal_sans_friction_voisins` | `two_ideal_no_neighbour_friction` |
| `deux_cylindres_03V` | `two_cylinders_0p3V` | | `deux_ideal_support_glissant` | `two_ideal_slippery_support` |
| `deux_cylindres_dt_divise_2` | `two_cylinders_half_dt` | | `deux_ideal_dt_divise_2` | `two_ideal_half_dt` |
| `deux_cylindres_iterations_doublees` | `two_cylinders_double_iterations` | | `deux_ideal_iterations_doublees` | `two_ideal_double_iterations` |
| `deux_cylindres_10V` | `two_cylinders_1V` | | `triangle_un_moteur` | `triangle_one_motor` |
| `deux_cylindres_10V_dt_divise_2` | `two_cylinders_1V_half_dt` | | `triangle_deux_moteurs` | `triangle_two_motors` |
| `deux_cylindres_10V_iterations_doublees` | `two_cylinders_1V_double_iterations` | | `triangle_trois_moteurs` | `triangle_three_motors` |
| `deux_dipoles_axiaux` | `two_dipoles_axial` | | `triangle_cylindres_glissant` | `triangle_cylinders_slippery` |
| `deux_dipoles_radiaux` | `two_dipoles_radial` | | `triangle_ideal_glissant` | `triangle_ideal_slippery` |
| `deux_cylindres_friction_voisins_faible` | `two_cylinders_low_neighbour_friction` | | | |

Note: the old `10V` meant 1.0 V (French decimal comma), and `03V` meant
0.3 V; the new names say so.

### Files

- `configs/prototype_hugo.json`: keys and values translated (`parameters`,
  `origin`, `to_confirm`, `to_calibrate`, `comparisons_to_make`), texts
  translated.
- `results/2026-10-14-triangle-3-units/`: kept as is (Victor's choice). Its
  README gets an "old format" note: the files use the pre-005 names, the
  tools no longer read them, the spec 005 tables map the names, and the run
  can be regenerated with `make sim NAME=triangle` as long as the defaults are
  unchanged (its JSON holds every parameter otherwise).

## Physics and assumptions

None. No default, law or numeric path changes.

## Files concerned

All Python files in `src/granulobot/`, `tests/`, `scripts/`; `Makefile`;
`configs/prototype_hugo.json`; `results/2026-10-14-triangle-3-units/README.md`;
docs that show flags, parameters or columns: `AGENTS.md`, `CLAUDE.md`,
`README.md`, `docs/model.md`, `docs/architecture.md`, `.agents/skills/run-sim`,
`.agents/skills/feature` if needed; `docs/decisions.md`, `specs/IDEES.md`,
`specs/README.md`.

## Planned tests

References: the outputs recorded for spec 004 on `main` (seven runs, `diag`,
a three-scenario campaign).

- Values unchanged: each new CSV equals the reference after renaming its
  header with the column table (same rows, same bytes); each new JSON equals
  the reference after renaming keys and enum values, except the
  `assumptions` texts; `make diag` likewise; the campaign files likewise,
  scenario names mapped.
- The GIF is rebuilt and checked by eye on one frame (text changed, drawing
  unchanged).
- A 3 s triangle run (in `runs/`, not replacing the kept result) matches
  `results/2026-10-14-triangle-3-units/` after renaming (CSV values
  identical), which checks a full-length run.
- `make test`, `make validate`, `make check-env` pass; `make replay` works;
  `--params configs/prototype_hugo.json` works.
- `grep` finds no French flag, field, column or key left in code and docs,
  outside history entries.

## Out of scope

Generalising to N units, any physics change, renaming `configs/prototype_hugo.json`.

## Review

Independent review by a separate agent (2026-11-24).

- Mapping checked independently of the rename script: all 82 fields (same
  order, same defaults apart from the four enum strings), properties,
  methods, enum values, CSV headers (3-unit, 2-unit and no-wheel layouts),
  JSON keys and the 21 scenario names match the spec tables. No old name
  left in code, configs, Makefile or docs, outside history entries and the
  kept 2026-10-14 files.
- No accidental replacement; `args.*` names match the flags. `--replay`,
  `--params` (with and without the `parameters` wrapper), `diag` and the
  campaign options work; old flags, keys and scenario names are rejected.
- Rare paths run on `main` (old flags) and on the branch (new flags): torque
  mode, uneven speed mode, Bullet ground with APGD, radial dipoles with
  internal interactions, rotor perturbation and wheel on top, 2 units with
  ideal link, no ground/no magnetism at dt 2e-5, no motors, no outer wheel
  with dampings and rolling/spinning resistance, `prototype_hugo.json`, a
  4-scenario campaign: values identical after mapping.
- Translations of the assumptions, campaign summary, help texts, config and
  GIF are faithful.
- Findings: (1) `.gitignore` comment still named `--sortie`. Fixed.
  (2) The results README note and the decisions entry stated that the 3 s
  rerun matched before that run had finished. Checked after it finished:
  `runs/spec005/triangle3s` matches `results/2026-10-14-triangle-3-units`
  (601 rows, CSV and JSON identical after mapping), so both statements hold.
