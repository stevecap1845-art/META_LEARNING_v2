# Results manifest

This file lists every result file in the repository: what it is, whether it is
current evidence, and what it costs to rebuild. Add a row whenever a phase
writes a file.

## Layout

```
results/
├── README.md               this manifest
├── phase<N>/               output of phase N only (tracked in git)
├── inherited/              files that arrived with the code; NOT evidence
└── experiment_runner/      scratch output of experiment_runner.py (git-ignored)
```

Everything here is tracked in git except `experiment_runner/`. If a phase later
writes files that git should not track, such as crash journals, add a
`.gitignore` rule then, and back up any journal that holds the only copy of
something (for example paid API answers).

## Phase 0

| File | What it is | Current? | Cost to rebuild |
|---|---|---|---|
| `phase0/environment/python_version.txt` | Python build used by both venvs (3.11.9, `tags/v3.11.9:de54cf5`) | yes | seconds |
| `phase0/environment/venv_main_freeze.txt` | `pip freeze` of `.venv`; equals `requirements.txt` exactly | yes | seconds |
| `phase0/environment/venv_pflacco_freeze.txt` | `pip freeze` of `.venv-pflacco`; equals `requirements-pflacco.txt` exactly | yes | seconds |
| `phase0/pytest_baseline.txt` | `pytest tests -v`: 54 passed, no warnings | yes, re-run 2026-11-20 on the current code | about 10 s |
| `phase0/health_report.{txt,json}` | health check C1 to C5 from `scripts/phase0_health_check.py`: 70 pass, 72 flag, 0 fail | yes, 2026-11-20, seed 0, commit `79db7fd` (now `606e64d`, same files) plus uncommitted changes | about 1 min, all four files together |
| `phase0/algorithm_runs.csv` | C3: one row per run, 32 algorithms × 2 problems × 2 runs (evaluations counted, best reported and best evaluated, seconds) | yes, same run | with the above |
| `phase0/pytest_runs.txt` | C5: full output of `pytest tests` run three times | yes, same run | with the above |

## Inherited (not evidence)

| Folder | What it is |
|---|---|
| `inherited/snapshot_2026-08-07/` | 60 files (1 JSON, 59 PNGs) found in `results/` when the repository was created. They come from at least two runs of earlier code with no seeds recorded, and every "final evaluation" in them ran PSO. They are kept for the record only; [`inherited/snapshot_2026-08-07/README.md`](inherited/snapshot_2026-08-07/README.md) gives the details. |
