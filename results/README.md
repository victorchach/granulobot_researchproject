# Six-unit simulation runs

These five saved runs contain the original CSV measurements, JSON metadata,
and GIFs. Directory dates come from the saved files. The source tree on this
branch records the local research snapshot. The exact source revision used to
generate each run is unknown.

| Run | Duration (s) | Time step (s) | Initial rotor offset |
| --- | ---: | ---: | ---: |
| [hexagone_dt_1e4](2026-11-09-hexagone_dt_1e4/) | 10 | 0.001 | 0 degrees |
| [reference_alternee](2026-11-10-reference_alternee/) | 2 | 0.0001 | 0 degrees |
| [reference_alternee_dt_1e5](2026-11-10-reference_alternee_dt_1e5/) | 1 | 0.00001 | 0 degrees |
| [perturbation_alternee_1deg](2026-11-10-perturbation_alternee_1deg/) | 2 | 0.0001 | 1 degree |
| [perturbation_alternee_11deg](2026-11-10-perturbation_alternee_11deg/) | 2 | 0.0001 | 1 degree |

The table uses the JSON metadata. The effective time step for
`hexagone_dt_1e4` and the effective offset for
`perturbation_alternee_11deg` differ from their filenames. Each JSON file
records its run parameters, assumptions, and summary under `bilan`.
