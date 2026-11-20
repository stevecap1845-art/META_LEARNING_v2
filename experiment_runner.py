"""
experiment_runner.py
====================
Top-level entry point for the Autonomous Algorithm Design (AAD) framework.

Run directly:
    python experiment_runner.py

Or import and call programmatically:
    from experiment_runner import run_experiment
    results = run_experiment(problems=[SphereProblem(dim=5)], meta_generations=2)

Output
------
- Console logs with per-generation meta-learning progress
- JSON results file  → results/experiment_runner/experiment_results.json
- PNG plots          → results/experiment_runner/*.png
"""

import json
import os
import time

import numpy as np

from aad import (
    EA_Designer,
    EvaluationFramework,
    EvolutionaryAlgorithm,
    LLMDesigner,
    Visualizer,
    AckleyProblem,
    RastriginProblem,
    RosenbrockProblem,
    SphereProblem,
    ZDT1Problem,
    # BBOB suite
    BBOB_F1_Sphere,
    BBOB_F2_EllipsoidalSeparable,
    BBOB_F3_RastriginSeparable,
    BBOB_F4_BucheRastrigin,
    BBOB_F5_LinearSlope,
    BBOB_F6_AttractiveSector,
    BBOB_F7_StepEllipsoidal,
    BBOB_F8_Rosenbrock,
    BBOB_F9_RosenbrockRotated,
    BBOB_F10_EllipsoidalRotated,
    BBOB_F11_Discus,
    BBOB_F12_BentCigar,
    BBOB_F13_SharpRidge,
    BBOB_F14_DifferentPowers,
    BBOB_F15_RastriginRotated,
    BBOB_F16_Weierstrass,
    BBOB_F17_SchaffersF7,
    BBOB_F18_SchaffersF7IllConditioned,
    BBOB_F19_GriewankRosenbrock,
    BBOB_F20_Schwefel,
    BBOB_F21_Gallagher101,
    BBOB_F22_Gallagher21,
    BBOB_F23_Katsuura,
    BBOB_F24_LunacekBiRastrigin,
)

RESULTS_DIR = os.path.join("results", "experiment_runner")


# ---------------------------------------------------------------------------
# Serialisation helper
# ---------------------------------------------------------------------------

def _serializable(obj):
    """Recursively convert numpy scalars / arrays to plain Python types."""
    if isinstance(obj, dict):
        return {k: _serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serializable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def log_results(results: dict, filename: str = "experiment_results.json") -> str:
    """Write *results* as pretty-printed JSON to *RESULTS_DIR*."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    fpath = os.path.join(RESULTS_DIR, filename)
    with open(fpath, "w") as fh:
        json.dump(_serializable(results), fh, indent=2)
    print(f"\n  [Logger] Results saved -> {fpath}")
    return fpath


# ---------------------------------------------------------------------------
# Main experiment function
# ---------------------------------------------------------------------------

def run_experiment(
    problems=None,
    meta_generations: int = 3,
    meta_population_size: int = 6,
    runs_per_eval: int = 2,
    use_surrogate: bool = True,
    use_llm_designer: bool = True,
    verbose: bool = True,
) -> dict:
    """
    Run the full AAD experiment pipeline.

    For each problem:
      1. Meta-learning search (EA_Designer) to find the best EA config.
      2. LLM / rule-based designer proposes an independent config.
      3. Full evaluation of the best config (multiple runs, metrics).
      4. Visualisation (fitness curves, meta-convergence, Pareto front).

    Parameters
    ----------
    problems : list of OptimizationProblem, optional
        Defaults to Sphere, Rastrigin, Rosenbrock, Ackley, ZDT1.
    meta_generations : int
        Meta-evolution generations.
    meta_population_size : int
        EA configurations in the meta-population.
    runs_per_eval : int
        EA runs per configuration evaluation.
    use_surrogate : bool
        Enable surrogate-assisted screening.
    use_llm_designer : bool
        Also propose a config with the LLM/rule-based designer.
    verbose : bool
        Print progress to stdout.

    Returns
    -------
    dict  –  nested results keyed by problem name.
    """
    if problems is None:
        problems = [
            #SphereProblem(dim=10),
            #RastriginProblem(dim=10),
            #RosenbrockProblem(dim=10),
            #AckleyProblem(dim=10),
            #ZDT1Problem(dim=10),
            # BBOB suite (all 24 functions, dim=10)
            BBOB_F1_Sphere(dim=10),
            BBOB_F2_EllipsoidalSeparable(dim=10),
            BBOB_F3_RastriginSeparable(dim=10),
            BBOB_F4_BucheRastrigin(dim=10),
            BBOB_F5_LinearSlope(dim=10),
            BBOB_F6_AttractiveSector(dim=10),
            BBOB_F7_StepEllipsoidal(dim=10),
            BBOB_F8_Rosenbrock(dim=10),
            BBOB_F9_RosenbrockRotated(dim=10),
            BBOB_F10_EllipsoidalRotated(dim=10),
            BBOB_F11_Discus(dim=10),
            BBOB_F12_BentCigar(dim=10),
            BBOB_F13_SharpRidge(dim=10),
            BBOB_F14_DifferentPowers(dim=10),
            BBOB_F15_RastriginRotated(dim=10),
            BBOB_F16_Weierstrass(dim=10),
            BBOB_F17_SchaffersF7(dim=10),
            BBOB_F18_SchaffersF7IllConditioned(dim=10),
            BBOB_F19_GriewankRosenbrock(dim=10),
            BBOB_F20_Schwefel(dim=10),
            BBOB_F21_Gallagher101(dim=10),
            BBOB_F22_Gallagher21(dim=10),
            BBOB_F23_Katsuura(dim=10),
            BBOB_F24_LunacekBiRastrigin(dim=10),
        ]

    evaluator = EvaluationFramework(n_runs=runs_per_eval)
    visualizer = Visualizer(output_dir=RESULTS_DIR)
    llm_designer = LLMDesigner() if use_llm_designer else None

    # ── Banner ────────────────────────────────────────────────────────
    sep = "=" * 70
    print(f"\n{sep}")
    print("  AUTONOMOUS ALGORITHM DESIGN (AAD) – Experiment Runner")
    print(sep)
    print(f"  Problems        : {[p.name for p in problems]}")
    print(f"  Meta-generations: {meta_generations}")
    print(f"  Meta-pop-size   : {meta_population_size}")
    print(f"  Runs per eval   : {runs_per_eval}")
    print(f"  Surrogate       : {use_surrogate}")
    print(f"  LLM designer    : {use_llm_designer}")
    print(sep)

    all_results: dict = {}

    for problem in problems:
        pname = problem.name
        dim = len(problem.bounds()[0])
        is_mo = problem.is_multiobjective()

        print(f"\n{'#' * 70}")
        print(f"#  Problem : {pname}  (dim={dim}, multi-obj={is_mo})")
        print(f"{'#' * 70}")

        prob_results: dict = {}

        # ── 1. Meta-learning search ───────────────────────────────────
        designer = EA_Designer(
            population_size=meta_population_size,
            generations=meta_generations,
            runs_per_eval=runs_per_eval,
            use_surrogate=use_surrogate,
        )
        t0 = time.perf_counter()
        best_config, best_perf = designer.evolve(problem, verbose=verbose)
        elapsed = time.perf_counter() - t0

        prob_results["meta_learning"] = {
            "best_config": best_config,
            "best_performance": float(best_perf),
            "meta_convergence": [float(v) for v in designer.meta_convergence],
            "elapsed_seconds": round(elapsed, 2),
        }

        # ── 2. LLM / rule-based designer ─────────────────────────────
        if llm_designer is not None:
            desc = llm_designer.generate_description(problem)
            llm_config = llm_designer.propose_algorithm(desc)
            print(f"\n  [LLM Designer] description  : {desc}")
            print(f"  [LLM Designer] proposed cfg : {llm_config}")

            llm_metrics = evaluator.evaluate(llm_config, problem, verbose=False)
            print(
                f"  [LLM Designer] best fitness : {llm_metrics['best_fitness']:.6f}"
            )
            prob_results["llm_designer"] = {
                "config": llm_config,
                "metrics": {
                    k: v
                    for k, v in llm_metrics.items()
                    if k != "histories"
                },
            }

        # ── 3. Full evaluation of best config ─────────────────────────
        print(f"\n  [Evaluation] Full evaluation of best config …")
        full_metrics = evaluator.evaluate(best_config, problem, verbose=verbose)

        prob_results["final_evaluation"] = {
            "config": best_config,
            "metrics": {
                k: v for k, v in full_metrics.items() if k != "histories"
            },
        }

        print(f"\n  [Results] {pname}")
        EvaluationFramework.summarize(full_metrics)

        # ── 4. Visualisation ──────────────────────────────────────────
        visualizer.plot_fitness_curves(
            full_metrics["histories"],
            title=f"Fitness Convergence – {pname}",
            filename=f"fitness_{pname}.png",
        )
        visualizer.plot_meta_convergence(
            designer.meta_convergence,
            title=f"Meta-Learning Convergence – {pname}",
            filename=f"meta_{pname}.png",
        )

        if is_mo:
            # Run the best EA once more to collect the final population
            # and plot its objective-space projection as a Pareto front.
            _ea = EvolutionaryAlgorithm({**best_config, "max_generations": 50})
            _ea.run(problem)
            lb = np.asarray(problem.bounds()[0])
            ub = np.asarray(problem.bounds()[1])
            rng_pop = lb + np.random.random((200, len(lb))) * (ub - lb)
            pareto_fits = [problem.evaluate(ind) for ind in rng_pop]
            visualizer.plot_pareto_front(
                pareto_fits,
                title=f"Pareto Front – {pname}",
                filename=f"pareto_{pname}.png",
            )

        all_results[pname] = prob_results

    # ── Log all results ───────────────────────────────────────────────
    log_results(all_results)

    # ── Summary table ─────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  EXPERIMENT SUMMARY")
    print(sep)
    for pname, pres in all_results.items():
        best = pres["final_evaluation"]["metrics"]["best_fitness"]
        cfg = pres["final_evaluation"]["config"]
        print(f"  {pname:<28s}  best={best:.6f}")
        print(f"  {'':28s}  cfg={cfg}")
    print(sep)

    return all_results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_experiment()
