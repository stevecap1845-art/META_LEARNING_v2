# Round 1, Phases 1 and 1b: baseline comparison and algorithm health screen

Source: main project, tag `v1-final`: `docs/reports/phase1_report.md`,
`docs/reports/phase1b_report.md` and `results/phase1b/`. Summarised
2026-11-20; not evidence for this repository.

## Phase 1: PSO against GA

Phase 1 checked whether the measurement pipeline gives a statistically sound
comparison on the smallest possible case.

It ran PSO and GA on `BBOB_F1_Sphere` (dimension 10, problem seed 42) with
population 50 and 100 generations, 30 runs each. The seed ranges were disjoint
(1000 to 1029 and 2000 to 2029) so the two samples were independent, and the
test was a two-sided Mann-Whitney U.

PSO's median was 9.34e-10 against GA's 5.80e-02: U = 0.0, p = 3.02e-11,
rank-biserial r = 1.0, so every PSO run beat every GA run. Re-runs gave
identical output.

That outcome is expected on a trivial unimodal function. The run checks
seeding, budget enforcement and the statistical test; it is not a research
result. It also showed that seeds have to travel through the config dict,
because mealpy seeds its own generator and ignores the global numpy seed.

## Phase 1b: algorithm health screen

Some mealpy algorithms run without error, return finite values and never
improve, so a crash test cannot catch them. Phase 1b checked which algorithms
optimise at all.

It ran 21 mealpy algorithms on `BBOB_F1_Sphere` d10 with population 50,
5,000 evaluations and 3 seeds each. `ea` was left out because it could not be
seeded at the time. Verdicts were set on median fitness: excellent below 1e-6,
moderate below 0.01, poor at 0.01 or above.

| Verdict | Algorithms |
|---|---|
| excellent | EO, PSO |
| moderate | SHADE, L_SHADE, JADE, MPA, MVO, RIME, GWO, SMA |
| poor | ARO, HBA, SA, ABC, GA, BBO, WOA, SCA, GJO, HHO, AO |

None failed outright. "Poor" here means the default settings do not refine
finely on an easy problem.

Three algorithms were removed because ten times the budget did not improve
their result:

| Algorithm | Evidence |
|---|---|
| `CMA_ES` | the covariance collapses while the step size never adapts; it stays 3.34 from the optimum at 5k, 20k and 50k evaluations, and mealpy exposes no parameter to fix it |
| `AOA` | returns the same value at every budget |
| `DE` | stagnates near 0.73; 2,000 and 20,000 evaluations differ only in the fifth decimal |

That left 22 algorithms: 21 mealpy plus `ea`.

SA was the slowest at 8.16 s per run, about 40 times the fastest, because it
spends about one evaluation per step.

## Relevance here

This repository still registers `CMA_ES`, `AOA` and `DE`. Round two restored
them for re-testing, and its health check found that `CMA_ES` can crash
(`LinAlgError: Matrix is not positive definite`). The Phase 2 algorithm screen
should re-test all three.
