"""
evaluation.py
-------------
Comprehensive evaluation framework for EA configurations.

Each EA configuration is evaluated over multiple independent runs so that
performance estimates are robust to stochastic variation.

Metrics computed
----------------
best_fitness     : minimum best-of-run fitness across all runs
mean_fitness     : mean best-of-run fitness
std_fitness      : standard deviation of best-of-run fitness
worst_fitness    : maximum best-of-run fitness
convergence_speed: mean generation index at which 50 % of the total
                   improvement is achieved
stability        : 1 / (std_fitness + ε) – higher is more stable
mean_runtime     : wall-clock seconds per run
histories        : list of convergence curves (one per run)
"""

import time

import numpy as np

from .evolutionary_algorithm import EvolutionaryAlgorithm, build_algorithm


class EvaluationFramework:
    """
    Run-and-measure harness for EA configurations.

    Parameters
    ----------
    n_runs : int, default 5
        Number of independent EA runs per configuration.
    """

    def __init__(self, n_runs: int = 5):
        self.n_runs = n_runs

    # ------------------------------------------------------------------
    # Single configuration evaluation
    # ------------------------------------------------------------------

    def evaluate(self, ea_config: dict, problem, verbose: bool = False) -> dict:
        """
        Evaluate an EA configuration on *problem*.

        Parameters
        ----------
        ea_config : dict   – EA configuration
        problem   : OptimizationProblem
        verbose   : bool   – print per-run summary if True

        Returns
        -------
        dict with keys:
            best_fitness, mean_fitness, std_fitness, worst_fitness,
            convergence_speed, stability, mean_runtime, histories
        """
        best_fitnesses: list = []
        histories: list = []
        runtimes: list = []

        for run in range(1, self.n_runs + 1):
            ea = build_algorithm(ea_config)
            t0 = time.perf_counter()
            _, best_fit = ea.run(problem)
            elapsed = time.perf_counter() - t0

            best_fitnesses.append(best_fit)
            histories.append(ea.history)
            runtimes.append(elapsed)

            if verbose:
                print(
                    f"    run {run}/{self.n_runs}: "
                    f"best={best_fit:.6f}  time={elapsed:.2f}s"
                )

        bf = np.array(best_fitnesses)

        # Convergence speed: generation at which 50 % of total improvement
        # is achieved (averaged over runs)
        speeds: list = []
        for hist in histories:
            if len(hist) > 1 and hist[0] > hist[-1]:
                target = hist[0] - 0.5 * (hist[0] - hist[-1])
                reached = next(
                    (g for g, v in enumerate(hist) if v <= target),
                    len(hist) - 1,
                )
            else:
                reached = 0
            speeds.append(reached)

        return {
            "best_fitness": float(np.min(bf)),
            "mean_fitness": float(np.mean(bf)),
            "std_fitness": float(np.std(bf)),
            "worst_fitness": float(np.max(bf)),
            "convergence_speed": float(np.mean(speeds)),
            "stability": float(1.0 / (np.std(bf) + 1e-10)),
            "mean_runtime": float(np.mean(runtimes)),
            "histories": histories,
        }

    # ------------------------------------------------------------------
    # Multi-configuration comparison
    # ------------------------------------------------------------------

    def compare_configs(
        self, configs: list, problem, verbose: bool = True
    ) -> list:
        """
        Evaluate multiple EA configurations on the same problem and return
        results sorted by best_fitness (ascending).

        Parameters
        ----------
        configs : list of dict
        problem : OptimizationProblem
        verbose : bool

        Returns
        -------
        list of (config, metrics) sorted by best_fitness
        """
        results = []
        for i, cfg in enumerate(configs, start=1):
            if verbose:
                print(f"\n  Config {i}/{len(configs)}: {cfg}")
            metrics = self.evaluate(cfg, problem, verbose=verbose)
            results.append((cfg, metrics))
            if verbose:
                print(
                    f"    -> best={metrics['best_fitness']:.6f}  "
                    f"speed={metrics['convergence_speed']:.1f}  "
                    f"stability={metrics['stability']:.3f}"
                )

        results.sort(key=lambda x: x[1]["best_fitness"])
        return results

    # ------------------------------------------------------------------
    # Summary printing
    # ------------------------------------------------------------------

    @staticmethod
    def summarize(metrics: dict) -> None:
        """Print a human-readable summary of an evaluation result."""
        print(f"    best_fitness    : {metrics['best_fitness']:.6f}")
        print(f"    mean_fitness    : {metrics['mean_fitness']:.6f}")
        print(f"    std_fitness     : {metrics['std_fitness']:.6f}")
        print(f"    convergence_gen : {metrics['convergence_speed']:.1f}")
        print(f"    stability       : {metrics['stability']:.3f}")
        print(f"    mean_runtime    : {metrics['mean_runtime']:.2f}s")
