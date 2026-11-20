"""
mealpy_algorithms.py
--------------------
Adapter layer that connects the `mealpy` meta-heuristic library
(https://github.com/thieu1995/mealpy) to the AAD framework's
`OptimizationProblem` interface.

Classes
-------
MealpyAlgorithm  : Drop-in replacement for `EvolutionaryAlgorithm` that
                   runs any algorithm registered in `MEALPY_REGISTRY`.

Constants
---------
MEALPY_REGISTRY  : dict mapping short algorithm keys to
                   (module_path, class_name, extra_kwargs).
MEALPY_ALGORITHM_KEYS : sorted list of all registered keys.

Usage
-----
    from aad.mealpy_algorithms import MealpyAlgorithm

    cfg = {"algorithm": "PSO", "population_size": 50, "max_generations": 100}
    alg = MealpyAlgorithm(cfg)
    best_sol, best_fit = alg.run(problem)
    print(alg.history)        # convergence curve (one value per epoch)
"""

import importlib

import numpy as np

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
# Each entry: key -> (module_path, class_name, extra_kwargs)
#
# extra_kwargs are passed to the constructor *in addition* to
# epoch=max_generations and pop_size=population_size.
#
# Algorithms suspected of plagiarism (as flagged on the mealpy README) are
# intentionally excluded.

MEALPY_REGISTRY: dict = {
    # ------------------------------------------------------------------ #
    # Evolutionary-based                                                   #
    # ------------------------------------------------------------------ #
    "GA": (
        "mealpy.evolutionary_based.GA",
        "BaseGA",
        {},
    ),
    "DE": (
        "mealpy.evolutionary_based.DE",
        "OriginalDE",
        {},
    ),
    "JADE": (
        "mealpy.evolutionary_based.DE",
        "JADE",
        {},
    ),
    "CMA_ES": (
        "mealpy.evolutionary_based.ES",
        "CMA_ES",
        {},
    ),
    "SHADE": (
        "mealpy.evolutionary_based.SHADE",
        "OriginalSHADE",
        {},
    ),
    "L_SHADE": (
        "mealpy.evolutionary_based.SHADE",
        "L_SHADE",
        {},
    ),
    # ------------------------------------------------------------------ #
    # Swarm-based                                                          #
    # ------------------------------------------------------------------ #
    "PSO": (
        "mealpy.swarm_based.PSO",
        "OriginalPSO",
        {},
    ),
    "GWO": (
        "mealpy.swarm_based.GWO",
        "OriginalGWO",
        {},
    ),
    "WOA": (
        "mealpy.swarm_based.WOA",
        "OriginalWOA",
        {},
    ),
    "HHO": (
        "mealpy.swarm_based.HHO",
        "OriginalHHO",
        {},
    ),
    "ABC": (
        "mealpy.swarm_based.ABC",
        "OriginalABC",
        {},
    ),
    "GJO": (
        "mealpy.swarm_based.GJO",
        "OriginalGJO",
        {},
    ),
    "ARO": (
        "mealpy.swarm_based.ARO",
        "OriginalARO",
        {},
    ),
    "AO": (
        "mealpy.swarm_based.AO",
        "OriginalAO",
        {},
    ),
    "MPA": (
        "mealpy.swarm_based.MPA",
        "OriginalMPA",
        {},
    ),
    "HBA": (
        "mealpy.swarm_based.HBA",
        "OriginalHBA",
        {},
    ),
    # ------------------------------------------------------------------ #
    # Physics-based                                                        #
    # ------------------------------------------------------------------ #
    "SA": (
        "mealpy.physics_based.SA",
        "OriginalSA",
        {},
    ),
    "EO": (
        "mealpy.physics_based.EO",
        "OriginalEO",
        {},
    ),
    "MVO": (
        "mealpy.physics_based.MVO",
        "OriginalMVO",
        {},
    ),
    "RIME": (
        "mealpy.physics_based.RIME",
        "OriginalRIME",
        {},
    ),
    # ------------------------------------------------------------------ #
    # Bio-inspired                                                         #
    # ------------------------------------------------------------------ #
    "SMA": (
        "mealpy.bio_based.SMA",
        "OriginalSMA",
        {},
    ),
    "BBO": (
        "mealpy.bio_based.BBO",
        "OriginalBBO",
        {},
    ),
    # ------------------------------------------------------------------ #
    # Math-based                                                           #
    # ------------------------------------------------------------------ #
    "SCA": (
        "mealpy.math_based.SCA",
        "OriginalSCA",
        {},
    ),
    "AOA": (
        "mealpy.math_based.AOA",
        "OriginalAOA",
        {},
    ),
}

MEALPY_ALGORITHM_KEYS: list = sorted(MEALPY_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Adapter class
# ---------------------------------------------------------------------------

class MealpyAlgorithm:
    """
    Wraps any mealpy optimizer with the same interface as
    `EvolutionaryAlgorithm`, so it can be used transparently by the
    evaluation and meta-learning layers.

    Parameters
    ----------
    config : dict
        Required key:
          algorithm        : str  – key into MEALPY_REGISTRY (e.g. "PSO")
        Optional keys (shared with EvolutionaryAlgorithm):
          population_size  : int  – passed as ``pop_size`` to mealpy (default 50)
          max_generations  : int  – passed as ``epoch``    to mealpy (default 100)

    Attributes
    ----------
    history : list[float]
        Global-best fitness at each epoch (populated after `run`).
    """

    def __init__(self, config: dict):
        self.config = config
        self.algorithm_key = config.get("algorithm", "PSO")
        self.population_size = int(config.get("population_size", 50))
        self.max_generations = int(config.get("max_generations", 100))

        if self.algorithm_key not in MEALPY_REGISTRY:
            raise ValueError(
                f"Unknown mealpy algorithm: '{self.algorithm_key}'. "
                f"Available: {MEALPY_ALGORITHM_KEYS}"
            )

        self.history: list = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_model(self):
        """Instantiate the mealpy optimizer from the registry."""
        module_path, class_name, extra_kwargs = MEALPY_REGISTRY[self.algorithm_key]
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls(
            epoch=self.max_generations,
            pop_size=self.population_size,
            **extra_kwargs,
        )

    @staticmethod
    def _scalar(fitness):
        """Collapse multi-objective fitness to a scalar (sum)."""
        if isinstance(fitness, (list, tuple)):
            return sum(fitness)
        return float(fitness)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, problem):
        """
        Run the wrapped mealpy algorithm on *problem*.

        Parameters
        ----------
        problem : OptimizationProblem

        Returns
        -------
        (best_solution, best_fitness) : (np.ndarray, float)
        """
        from mealpy import FloatVar  # local import keeps mealpy optional at module load

        lb, ub = problem.bounds()

        def _obj(solution):
            return self._scalar(problem.evaluate(solution))

        mealpy_problem = {
            "obj_func": _obj,
            "bounds": FloatVar(lb=tuple(lb), ub=tuple(ub)),
            "minmax": "min",
            "log_to": None,   # suppress mealpy console output
        }

        model = self._make_model()
        g_best = model.solve(mealpy_problem)

        # Convergence history: one float per epoch
        self.history = [float(v) for v in model.history.list_global_best_fit]

        return np.asarray(g_best.solution, dtype=float), float(g_best.target.fitness)

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self):
        return (
            f"MealpyAlgorithm(alg={self.algorithm_key}, "
            f"pop={self.population_size}, "
            f"epochs={self.max_generations})"
        )
