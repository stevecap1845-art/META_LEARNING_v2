# Inherited outputs (snapshot of 2026-08-07): not evidence

These 60 files were in `results/` when the repository was created on
2026-11-20, and were moved here unchanged. They are kept as a record only. Do
not quote them as results.

| File(s) | Count |
|---|---|
| `experiment_results.json` | 1: the 24 BBOB functions |
| `fitness_<Problem>.png` | 29: 24 BBOB + Sphere, Rastrigin, Rosenbrock, Ackley, ZDT1 |
| `meta_<Problem>.png` | 29: same problems |
| `pareto_ZDT1Problem.png` | 1 |

## Why they are not evidence

1. The JSON covers only the 24 BBOB functions, while the plots also cover 5
   classic problems, so the files come from at least two runs.
2. The configurations have no `algorithm` key, and `build_algorithm` then
   falls back to PSO (`aad/evolutionary_algorithm.py:221`). Every
   `final_evaluation` and `llm_designer` metric is therefore a PSO run,
   whatever EA setting it is filed under. The `meta_learning` part did run the
   EA (`aad/meta_learner.py:118`).
3. No seeds were recorded, budgets differ between configurations
   (population × (generations + 1) evaluations), and the exact code version is
   unknown, so the files cannot be reproduced.
4. The Pareto plot shows 200 random points drawn by the runner
   (`experiment_runner.py:274`), not the EA's result.

Section 4 of [documents/context/phase0_context.md](../../../documents/context/phase0_context.md)
has more on how these files were handled.
