"""
meta_learner.py
---------------
EA_Designer – a meta-optimiser that searches over the space of
Evolutionary Algorithm configurations to find the best EA for a
given optimisation problem.

Strategy: Evolution of EAs  (a (μ + λ)-style search in config space)
  1. Initialise a population of EA configurations.
  2. Evaluate each by running the EA on the target problem N times.
  3. Evolve the meta-population through crossover + mutation.
  4. Optionally use a surrogate model to pre-screen candidates.

Meta-level convergence and configuration history are tracked for analysis.
"""

import random

import numpy as np

from .config_space import EA_CONFIG_SPACE, random_config, config_to_vector
from .evolutionary_algorithm import EvolutionaryAlgorithm
from .landscape_features import LandscapeFeatureExtractor
from .surrogate_model import SurrogateModel


class EA_Designer:
    """
    Meta-optimiser that searches over EA design configurations.

    Parameters
    ----------
    config_space : dict, optional
        Configuration space to search over.  Defaults to
        :data:`~aad.config_space.EA_CONFIG_SPACE`.
    population_size : int, default 10
        Number of EA configurations in the meta-population.
    generations : int, default 5
        Number of meta-evolution generations.
    runs_per_eval : int, default 3
        Independent EA runs per configuration (for stable performance
        estimates).
    use_surrogate : bool, default True
        If True, a Random Forest surrogate is used to pre-screen
        candidate configurations, reducing expensive evaluations.
    surrogate_type : str, default ``"rf"``
        Surrogate backend passed to :class:`~aad.surrogate_model.SurrogateModel`.

    Attributes
    ----------
    meta_convergence : list[float]
        Best EA performance at each meta-generation (lower is better).
    best_config_history : list[dict]
        Best configuration at each meta-generation.
    """

    def __init__(
        self,
        config_space: dict = None,
        population_size: int = 10,
        generations: int = 5,
        runs_per_eval: int = 3,
        use_surrogate: bool = True,
        surrogate_type: str = "rf",
    ):
        self.config_space = config_space or EA_CONFIG_SPACE
        self.population_size = population_size
        self.generations = generations
        self.runs_per_eval = runs_per_eval
        self.use_surrogate = use_surrogate

        self._surrogate = (
            SurrogateModel(model_type=surrogate_type) if use_surrogate else None
        )
        self._feature_extractor = LandscapeFeatureExtractor()

        # Memory for surrogate fitting: (combined_feature_vector, performance)
        self._mem_X: list = []
        self._mem_y: list = []

        # Meta-level tracking
        self.meta_convergence: list = []
        self.best_config_history: list = []

    # ------------------------------------------------------------------
    # Candidate generation / variation
    # ------------------------------------------------------------------

    def generate_candidate(self) -> dict:
        """Sample a random EA configuration from the config space."""
        return random_config(self.config_space)

    def _mutate_config(self, config: dict) -> dict:
        """Mutate one randomly selected parameter."""
        new_config = config.copy()
        key = random.choice(list(self.config_space.keys()))
        new_config[key] = random.choice(self.config_space[key])
        return new_config

    def _crossover_configs(self, config1: dict, config2: dict) -> dict:
        """Uniform crossover: each parameter inherited from parent1 or parent2."""
        return {
            key: (config1[key] if random.random() < 0.5 else config2[key])
            for key in self.config_space
        }

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate_candidate(self, ea_config: dict, problem) -> float:
        """
        Run the EA described by *ea_config* on *problem* for
        *runs_per_eval* independent trials and return the mean best fitness.
        """
        scores = []
        for _ in range(self.runs_per_eval):
            ea = EvolutionaryAlgorithm(ea_config)
            _, best_fit = ea.run(problem)
            scores.append(best_fit)
        return float(np.mean(scores))

    def _should_evaluate(
        self,
        config: dict,
        feature_vec: np.ndarray,
        meta_fitnesses: list,
    ) -> bool:
        """
        Return True if the candidate should be fully evaluated.

        If the surrogate is fitted, only configurations whose predicted
        performance is below the median of the current meta-population are
        evaluated in full; others are rejected cheaply.
        """
        if self._surrogate is None or not self._surrogate.is_fitted:
            return True

        config_vec = config_to_vector(config, self.config_space)
        combined = np.concatenate([feature_vec, config_vec])
        predicted = float(self._surrogate.predict(combined)[0])
        threshold = float(np.median(meta_fitnesses))
        return predicted <= threshold

    def _update_surrogate(self) -> None:
        """Re-fit the surrogate on all accumulated memory."""
        if (
            self._surrogate is not None
            and len(self._mem_X) >= 5
        ):
            self._surrogate.fit(self._mem_X, self._mem_y)

    # ------------------------------------------------------------------
    # Main meta-evolution loop
    # ------------------------------------------------------------------

    def evolve(self, problem, verbose: bool = True) -> tuple:
        """
        Run the meta-evolution loop to find the best EA for *problem*.

        Parameters
        ----------
        problem : OptimizationProblem
        verbose : bool, default True

        Returns
        -------
        (best_config, best_performance) : (dict, float)
        """
        if verbose:
            sep = "=" * 60
            print(f"\n{sep}")
            print(f"  AAD Meta-Learning  |  Problem: {problem.name}")
            print(sep)

        # --- Extract problem features ---
        if verbose:
            print("  Extracting landscape features …")
        features = self._feature_extractor.extract_features(problem)
        feature_vec = self._feature_extractor.features_to_vector(features)

        if verbose:
            print(
                f"  dim={features['dimension']:.0f}  "
                f"variance={features['fitness_variance']:.3f}  "
                f"modality={features['modality']:.3f}  "
                f"ruggedness={features['ruggedness']:.3f}"
            )

        # --- Initialise meta-population ---
        meta_pop = [self.generate_candidate() for _ in range(self.population_size)]

        if verbose:
            print(
                f"\n  Evaluating initial meta-population "
                f"({self.population_size} configs) …"
            )

        meta_fits: list = []
        for cfg in meta_pop:
            perf = self.evaluate_candidate(cfg, problem)
            meta_fits.append(perf)
            cfg_vec = config_to_vector(cfg, self.config_space)
            self._mem_X.append(list(feature_vec) + cfg_vec)
            self._mem_y.append(perf)

        self._update_surrogate()

        best_idx = int(np.argmin(meta_fits))
        best_cfg, best_perf = meta_pop[best_idx], meta_fits[best_idx]
        self.meta_convergence.append(best_perf)
        self.best_config_history.append(best_cfg.copy())

        if verbose:
            print(f"  Gen 0  best={best_perf:.6f}  cfg={best_cfg}")

        # --- Meta-evolution ---
        for gen in range(1, self.generations + 1):
            new_pop: list = []
            new_fits: list = []

            for _ in range(self.population_size):
                # Variation
                p1, p2 = random.choices(meta_pop, k=2)
                child = self._crossover_configs(p1, p2)
                child = self._mutate_config(child)

                # Surrogate pre-screening
                if self._should_evaluate(child, feature_vec, meta_fits):
                    perf = self.evaluate_candidate(child, problem)
                else:
                    # Use surrogate prediction (slightly pessimistic)
                    cfg_vec = config_to_vector(child, self.config_space)
                    combined = np.concatenate([feature_vec, cfg_vec])
                    perf = float(self._surrogate.predict(combined)[0]) * 1.05

                new_pop.append(child)
                new_fits.append(perf)

                # Store in memory for surrogate
                cfg_vec = config_to_vector(child, self.config_space)
                self._mem_X.append(list(feature_vec) + cfg_vec)
                self._mem_y.append(perf)

            # Elitist (μ + λ) selection
            combined_pop = meta_pop + new_pop
            combined_fits = meta_fits + new_fits
            top_idxs = np.argsort(combined_fits)[: self.population_size]
            meta_pop = [combined_pop[i] for i in top_idxs]
            meta_fits = [combined_fits[i] for i in top_idxs]

            self._update_surrogate()

            best_cfg, best_perf = meta_pop[0], meta_fits[0]
            self.meta_convergence.append(best_perf)
            self.best_config_history.append(best_cfg.copy())

            if verbose:
                print(f"  Gen {gen}  best={best_perf:.6f}  cfg={best_cfg}")

        if verbose:
            print(f"\n  [OK] Best config : {best_cfg}")
            print(f"  [OK] Performance : {best_perf:.6f}")
            print("=" * 60)

        return best_cfg, best_perf
