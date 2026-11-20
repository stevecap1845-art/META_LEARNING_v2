"""
evolutionary_algorithm.py
--------------------------
A fully configurable Evolutionary Algorithm that wires together modular
selection, crossover, and mutation operators defined in *ea_components*.

Usage
-----
    from aad.evolutionary_algorithm import EvolutionaryAlgorithm
    from aad.problems import SphereProblem

    ea = EvolutionaryAlgorithm({
        "population_size": 50,
        "selection": "tournament",
        "crossover": "sbx",
        "mutation": "gaussian",
        "max_generations": 100,
    })
    best_sol, best_fitness = ea.run(SphereProblem(dim=10))
"""

import numpy as np

from .ea_components import (
    TournamentSelection,
    RouletteWheelSelection,
    SBXCrossover,
    UniformCrossover,
    GaussianMutation,
    PolynomialMutation,
)

# Registry maps string keys → operator classes
SELECTION_MAP = {
    "tournament": TournamentSelection,
    "roulette": RouletteWheelSelection,
}

CROSSOVER_MAP = {
    "sbx": SBXCrossover,
    "uniform": UniformCrossover,
}

MUTATION_MAP = {
    "gaussian": GaussianMutation,
    "polynomial": PolynomialMutation,
}


class EvolutionaryAlgorithm:
    """
    A (μ + λ) generational EA with elitist survivor selection.

    Parameters
    ----------
    config : dict
        Keys (all optional, shown with defaults):
          population_size  : int   – 50
          max_generations  : int   – 100
          selection        : str   – "tournament"
          crossover        : str   – "sbx"
          mutation         : str   – "gaussian"

    Attributes
    ----------
    history : list[float]
        Best fitness at each generation (populated after calling `run`).
    """

    def __init__(self, config: dict):
        self.config = config

        self.population_size = int(config.get("population_size", 50))
        self.max_generations = int(config.get("max_generations", 100))
        self.selection_name = config.get("selection", "tournament")
        self.crossover_name = config.get("crossover", "sbx")
        self.mutation_name = config.get("mutation", "gaussian")

        # Instantiate operators
        if self.selection_name not in SELECTION_MAP:
            raise ValueError(
                f"Unknown selection: '{self.selection_name}'. "
                f"Choose from {list(SELECTION_MAP)}"
            )
        if self.crossover_name not in CROSSOVER_MAP:
            raise ValueError(
                f"Unknown crossover: '{self.crossover_name}'. "
                f"Choose from {list(CROSSOVER_MAP)}"
            )
        if self.mutation_name not in MUTATION_MAP:
            raise ValueError(
                f"Unknown mutation: '{self.mutation_name}'. "
                f"Choose from {list(MUTATION_MAP)}"
            )

        self.selection = SELECTION_MAP[self.selection_name]()
        self.crossover = CROSSOVER_MAP[self.crossover_name]()
        self.mutation = MUTATION_MAP[self.mutation_name]()

        self.history: list = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _scalar(fitness):
        """Convert fitness to a scalar for ranking (minimisation)."""
        if isinstance(fitness, (list, tuple)):
            return sum(fitness)
        return float(fitness)

    def _init_population(self, bounds):
        lb = np.asarray(bounds[0], dtype=float)
        ub = np.asarray(bounds[1], dtype=float)
        dim = len(lb)
        return [
            lb + np.random.random(dim) * (ub - lb)
            for _ in range(self.population_size)
        ]

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self, problem):
        """
        Run the EA on *problem* and return the best solution found.

        Parameters
        ----------
        problem : OptimizationProblem

        Returns
        -------
        (best_solution, best_fitness) : (np.ndarray, float)
        """
        bounds = problem.bounds()
        population = self._init_population(bounds)
        self.history = []

        # Initial evaluation
        raw_fits = [problem.evaluate(ind) for ind in population]
        scalar_fits = [self._scalar(f) for f in raw_fits]

        best_fitness = min(scalar_fits)
        self.history.append(best_fitness)

        for _gen in range(self.max_generations):
            # --- Selection: choose parents ---
            parents = self.selection.select(
                population, scalar_fits, self.population_size
            )

            # --- Crossover + mutation: produce offspring ---
            offspring = []
            for i in range(0, len(parents) - 1, 2):
                c1, c2 = self.crossover.crossover(parents[i], parents[i + 1], bounds)
                c1 = self.mutation.mutate(c1, bounds)
                c2 = self.mutation.mutate(c2, bounds)
                offspring.extend([c1, c2])

            # Handle odd-length parents list
            if len(parents) % 2 == 1:
                offspring.append(
                    self.mutation.mutate(parents[-1].copy(), bounds)
                )

            # --- Evaluate offspring ---
            off_raw = [problem.evaluate(ind) for ind in offspring]
            off_scalar = [self._scalar(f) for f in off_raw]

            # --- (μ + λ) survivor selection ---
            combined = population + offspring
            combined_fits = scalar_fits + off_scalar
            top_idxs = np.argsort(combined_fits)[: self.population_size]
            population = [combined[i] for i in top_idxs]
            scalar_fits = [combined_fits[i] for i in top_idxs]

            best_fitness = scalar_fits[0]
            self.history.append(best_fitness)

        best_idx = int(np.argmin(scalar_fits))
        return population[best_idx], scalar_fits[best_idx]

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self):
        return (
            f"EA(pop={self.population_size}, "
            f"gens={self.max_generations}, "
            f"sel={self.selection_name}, "
            f"cx={self.crossover_name}, "
            f"mut={self.mutation_name})"
        )


# ---------------------------------------------------------------------------
# Algorithm factory
# ---------------------------------------------------------------------------

def build_algorithm(config: dict):
    """
    Return an algorithm instance appropriate for *config*.

    If ``config["algorithm"]`` is absent or ``"ea"``, an
    :class:`EvolutionaryAlgorithm` is returned.  Otherwise the value is
    looked up in :data:`~aad.mealpy_algorithms.MEALPY_REGISTRY` and a
    :class:`~aad.mealpy_algorithms.MealpyAlgorithm` is returned.

    Parameters
    ----------
    config : dict

    Returns
    -------
    EvolutionaryAlgorithm | MealpyAlgorithm
    """
    algorithm_key = config.get("algorithm", "pso")
    if algorithm_key in (None, "ea", ""):
        return EvolutionaryAlgorithm(config)
    from .mealpy_algorithms import MealpyAlgorithm
    return MealpyAlgorithm(config)

