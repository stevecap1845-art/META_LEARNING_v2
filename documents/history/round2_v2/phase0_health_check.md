# Round 2 (v2), Phase 0: codebase health and connectivity check

Source: main project, branch `v2`: `docs/planning/phase0/phase0_plan.md`,
`phase0_health_check.py`, `results/phase0/health_report.{txt,json}` and
`results/phase0/call_map.csv` (commit `a6ccea1`). The checks ran on the main
project's v2 code, not on this repository's. Summarised 2026-11-20; not
evidence for this repository.

## Question

Before any v2 research, does every part import, connect and run, and where
does the code differ from the README?

## Decisions taken before running (2026-11-18 to 2026-11-20)

| # | Decision |
|---|---|
| D1 | Report only; fix in Phase 0 only what blocks the checks |
| D2 | `user_model_runner.py` and `test_runner.py`: static checks only; `experiment_runner.py` run for real |
| D3 | Keep `test_phase0_config_consistency.py` and call it from the health check |
| D4 | Check `.venv-pflacco` too |
| D5 | Run the README's examples as written, in a temporary folder |

## Result (run 2026-11-20, Python 3.11.9, 1.5 minutes)

| Check | Outcome |
|---|---|
| C1 imports | 12 of 12 modules import in fresh processes; 53 exported names, none missing; every script compiles |
| C2 dependencies | 1 FAIL: the BBOB values are identical in both venvs for only 13 of 72 problem fingerprints (numpy 2.4.6 vs 1.24.4), with a largest relative difference of 1.24e-10 |
| C3 call map | 3 warnings (unused or untested items) |
| C4 fit between modules | 7 of 7 contracts hold |
| C5 tiny runs | 30 pass and 3 exceptions: `ea` ignores `max_fe` (1,020 evaluations for a 2,000 budget), and HHO and ABC go over budget by 10 and 20 evaluations |
| C6 defect register | 11 confirmed, 2 ruled out, 1 not reproduced, 1 not checked, 1 error (`CMA_ES`: `LinAlgError`, matrix not positive definite) |
| C7 test suites | both pass |
| C8 README check | 8 differences, 4 examples that need undefined names to run, 5 matches |

The confirmed defects: features evaluate each point twice (600 + 50 × dim
evaluations instead of 300); `ea` ignores `max_fe`; failed runs silently become
1e12; the surrogate with `n_jobs=-1` is not bit-repeatable; three feature
names mislead; `experiment_runner.py` has no seeds, unequal budgets and 2 runs
per evaluation; LLM failures silently become rule-based picks; 4 methods are
unused; the ZDT problems are optimised as f1 + f2; the Pareto plot shows
random points; and `EA_Designer`'s surrogate sees identical features for every
candidate.

Two suspected defects were ruled out. Operator settings do not leak into
mealpy results (mealpy ignores them, though the surrogate still encodes them),
and the algorithm lists agree.

Five of the 8 README differences matter most for later phases. (The other
three are the missing modules in the README's file tree and the two ZDT
defects above.) `EA_Designer` searches 25
algorithms by default, while the README describes the EA space only. The
result keys differ (`convergence_speed` in the code, `convergence_gen` in the
README). The LLM uses Gemini, where the README says OpenAI. Quick Start runs
24 BBOB problems, where the README says 5. The README's dependency list is out
of date.

## State on 2026-11-20

The results were committed (`a6ccea1`). Step 3 of that plan, reviewing each
finding and deciding whether to fix it now, fix it in Phase 2, or leave it,
had not happened yet, and no Phase 0 report was written.

## Relevance here

This is the most recent record of the defects. The same register, plus defect
#0 (which v2 had already fixed), is the starting point for Part B of this
repository's Phase 0.
