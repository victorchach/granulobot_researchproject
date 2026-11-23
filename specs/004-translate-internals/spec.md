# 004: Translate the code internals to English

Status: merged
Branch: `feature/004-translate-internals`

## Need

The repo rule is "everything written to the repo is in English", but the
code still uses French identifiers, comments and docstrings, kept until a
dedicated spec (`AGENTS.md`, Conventions). Victor decided on 2026-11-23 to
translate everything, in two specs:

- **004 (this one): the internals.** Names of functions, classes, methods,
  attributes and local variables, comments, docstrings, console messages and
  error messages. No output file changes.
- **005: the interface.** `Parametres` and its fields, CLI flags, CSV
  columns, JSON keys and values, the text drawn in the GIF, campaign scenario
  names and summary text, `configs/prototype_hugo.json`. That one breaks old
  run files, on purpose (no compatibility kept, Victor's decision).

Doing the internals first keeps this step verifiable to the byte.

## Expected behaviour

Every output file (CSV, JSON, GIF, campaign summaries) is byte-identical to
`main`. CLI flags are unchanged. Only the code, its comments, and what is
printed to the console change.

### Boundary with spec 005

Stays as it is in this spec, because it ends up in an output file or the CLI:

- the `Parametres` class, its fields, properties (`masse_corps`,
  `rayon_aimant`, `moment_aimant`) and methods (`verifier`, `dictionnaire`);
- every string that becomes a CSV column, a JSON key or value, GIF text,
  a scenario name or a line of `synthese.txt`;
- argparse flags, their `dest` names (`args.sans_gif`, ...) and help texts.

Everything else is translated.

### Glossary (used by 004 and 005)

| French | English | | French | English |
| --- | --- | --- | --- | --- |
| corps | body | | sol | ground |
| actif (rotor) | active (rotor) | | jante | rim |
| libre (rotor) | free (rotor) | | repère | frame |
| roue (libre) | (free) wheel | | sortie | output |
| aimant | magnet | | bilan | summary |
| couple | torque | | mesure | measurement |
| tension | voltage | | paire / appariement | pair / coupled pair |
| courant | current | | accrochage / décrochage | attachment / detachment |
| frottement | friction | | cible | target |
| vitesse | speed | | rampe | ramp |
| unité | unit | | essai | run / scenario |

### Public names

| Module | Before | After |
| --- | --- | --- |
| `__init__` | `RACINE` | `REPO_ROOT` |
| `__main__` | `PARAMETRES` | `PARAMETERS` |
| `chrono_env` | `charger_chrono` | `load_chrono` |
| `chrono_env` | `vect`, `xyz`, `angle`, `omega` | unchanged |
| `model/unit` | `noms`, `paires` | `unit_names`, `unit_pairs` |
| `model/unit` | `Unite`, `creer_unite` | `Unit`, `create_unit` |
| `model/unit` | `Unite.aimant`, `vider_forces`, `corps_dynamiques` | `Unit.magnet`, `clear_forces`, `dynamic_bodies` |
| `model/unit` | fields `corps`, `actif`, `libre`, `roue` | `body`, `active`, `free`, `wheel` |
| `model/unit` | `idx_corps`, `idx_actif`, `idx_libre`, `idx_roue` | `idx_body`, `idx_active`, `idx_free`, `idx_wheel` |
| `model/unit` | `moteur`, `fonction`, `pivot_libre`, `pivot_roue`, `guide` | `motor`, `torque_function`, `free_pivot`, `wheel_pivot`, `guide` |
| `model/unit` | `integrale`, `tension`, `courant`, `couple_moteur`, `couple_transmis` | `integral`, `voltage`, `current`, `motor_torque`, `transmitted_torque` |
| `model/motor` | `frottement`, `moteur_cc`, `appliquer_moteur` | `friction`, `dc_motor`, `apply_motor` |
| `model/magnets` | `CylindresAxiaux`, `evaluer`, `modele`, `pour_parametres` | `AxialCylinders`, `evaluate`, `cached_model`, `for_parameters` |
| `model/magnets` | `appliquer_magnetisme` (`dot`, `cross`, `dipoles`, `direct` unchanged) | `apply_magnetism` |
| `model/contacts` | `ContactsCirculaires`, `contact_jantes`, `contact_petits_aimants` | `CircularContacts`, `rim_contact`, `magnet_contact` |
| `simulation/world` | `appariements`, `creer_systeme` | `coupled_pairs`, `create_system` |
| `simulation/loop` | `simuler` | `simulate` |
| `simulation/recording` | `mesure`, `hypotheses`, `ecrire_sorties` | `measure`, `assumptions`, `write_outputs` |
| `output/analysis` | `analyser`, `derouler` (`rotation` unchanged) | `analyze`, `unwrap` |
| `output/animation` | `animation`, inner `maj` | `animate`, `update` |
| `scripts/campaign` | `executer` (`scenarios` unchanged) | `run_campaign` |
| `tests/test_physics` | `LoisPhysiques` and its test methods | `PhysicsLaws`, test names translated |
| `tests/test_dynamics` | `Dynamique` and its test methods | `Dynamics`, test names translated |

Keyword arguments in signatures follow the same glossary (for example
`simuler(p, sortie, gif=True, verbose=True)` becomes
`simulate(p, output, gif=True, verbose=True)`). Local variables are
translated with the glossary. `p` stays the conventional name for a
`Parametres` instance.

### Comments, docstrings, messages

Translated faithfully, with no new claims. Console messages (`print`) and
exception messages are translated; they are not written to any file. Four
module docstrings double as a `--help` description (`__main__`,
`output/analysis`, `scripts/campaign`, `tests/test_dynamics`); they are
translated too, and their example commands keep the current (French) flags
until spec 005. Per-option `help=` texts stay for spec 005.

## Physics and assumptions

None. Comments that state physical assumptions are translated, not changed.

## Files concerned

All Python files in `src/granulobot/`, `tests/`, `scripts/`. Docs that name
functions or classes: `AGENTS.md` (Architecture), `docs/architecture.md`,
`docs/model.md` if it names a function. `AGENTS.md` Conventions: the sentence
about French identifiers is updated (internals done, interface in spec 005).
`docs/decisions.md`, `specs/README.md`, `specs/IDEES.md` (the translation idea
moves to "covered by 004 and 005").

## Planned tests

References from `main` (`15f9159`): the seven runs of spec 003 (triangle,
2-unit bench, ideal link, speed mode, dipoles, no ground, with GIF), the
`diag` output of the triangle, and a short campaign
(`--essais passif deux_ideal triangle_un_moteur --duree 0.01`).

- Every CSV, JSON and GIF identical to its reference; campaign
  `synthese.json`, `synthese.txt` and per-scenario files identical.
- `make diag` output identical; `make replay` works.
- `make test` (10 tests), `make validate` (7 tests), `make check-env` pass.
- `grep` for the old public names in `src/`, `tests/`, `scripts/` and the
  docs finds nothing outside history entries and the strings kept for 005.
- A check for leftover French words in comments and docstrings (accents and
  common French words), reviewed by hand.

## Out of scope

Everything listed under spec 005. No behaviour or physics change, no
cleanup beyond the translation (long lines, duplicated code stay).

## Review

Independent review by a separate agent (2026-11-24).

- Semantic equivalence: old and new ASTs of all 19 Python files compared with
  docstrings blanked and identifiers ignored: no structural difference, and a
  consistent rename mapping per file. The non-docstring strings that differ
  are console and exception messages and two temporary directory names in the
  tests; none reaches a file.
- Rare paths exercised on `main` and on the branch (torque and speed modes,
  Bullet ground, radial dipoles, internal interactions, no internal friction
  with a rotor perturbation, 2-unit ideal link, no ground, no motors, GIF,
  `--rejouer`, `diag`): all outputs byte-identical. 12 `verifier()` error
  branches raise `ValueError` with the translated message.
- Campaign: same 21 scenarios and parameters; a 7-scenario campaign gives
  identical files.
- No leftover French outside strings that reach files or the CLI; no change
  of physical meaning in the translated comments.
- Findings: (1) the spec only exempted the `__main__` docstring, but the
  `analysis`, `campaign` and `test_dynamics` docstrings are also `--help`
  descriptions. Confirmed; the spec wording now covers them. (2)
  `specs/IDEES.md` still named `appariements` and `analysis.analyser`.
  Confirmed and fixed (now points to the new modules and names).
