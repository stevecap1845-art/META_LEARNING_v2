"""
landscape_features.py
---------------------
Lightweight Exploratory Landscape Analysis (ELA)-inspired features for
characterising optimisation problems without requiring many evaluations.

These features allow the meta-learner to describe a problem numerically so
that algorithm performance can be predicted or transferred across problems.

Features computed
-----------------
fitness_mean        : arithmetic mean of sampled fitness values
fitness_std         : standard deviation
fitness_variance    : coefficient of variation (std / |mean|)
fitness_min         : minimum sampled fitness
fitness_max         : maximum sampled fitness
gradient_magnitude  : mean gradient norm estimated via finite differences
modality            : skewness of the fitness distribution
ruggedness          : mean absolute change between consecutive samples
dimension           : number of decision variables
"""

import numpy as np


class LandscapeFeatureExtractor:
    """
    Extracts ELA-inspired features from an :class:`OptimizationProblem`.

    Parameters
    ----------
    n_samples : int, default 300
        Number of random samples used to characterise the landscape.
    """

    def __init__(self, n_samples: int = 300):
        self.n_samples = n_samples

    # ------------------------------------------------------------------
    # Sampling
    # ------------------------------------------------------------------

    def sample_landscape(self, problem):
        """
        Draw *n_samples* uniform random points and evaluate them.

        Returns
        -------
        samples  : np.ndarray of shape (n_samples, dim)
        fitnesses: np.ndarray of shape (n_samples,)  – scalar values
        """
        lb = np.asarray(problem.bounds()[0], dtype=float)
        ub = np.asarray(problem.bounds()[1], dtype=float)
        dim = len(lb)

        samples = lb + np.random.random((self.n_samples, dim)) * (ub - lb)
        fitnesses = np.array([
            sum(problem.evaluate(s)) if isinstance(problem.evaluate(s), list)
            else float(problem.evaluate(s))
            for s in samples
        ])
        return samples, fitnesses

    # ------------------------------------------------------------------
    # Individual feature computations
    # ------------------------------------------------------------------

    @staticmethod
    def fitness_variance(fitnesses: np.ndarray) -> float:
        """Coefficient of variation of sampled fitness values."""
        mean = np.mean(fitnesses)
        std = np.std(fitnesses)
        return float(std / (abs(mean) + 1e-10))

    @staticmethod
    def gradient_approximation(problem, samples: np.ndarray,
                                fitnesses: np.ndarray) -> float:
        """
        Approximate the mean gradient magnitude over a subset of samples
        using forward finite differences.
        """
        lb = np.asarray(problem.bounds()[0], dtype=float)
        ub = np.asarray(problem.bounds()[1], dtype=float)
        dim = len(lb)
        eps = 1e-5 * (ub - lb)

        grad_norms = []
        subset = samples[:min(50, len(samples))]
        subset_fits = fitnesses[:len(subset)]

        for i, s in enumerate(subset):
            grad = np.zeros(dim)
            for j in range(dim):
                s_fwd = s.copy()
                s_fwd[j] += eps[j]
                s_fwd = np.clip(s_fwd, lb, ub)
                f_fwd = problem.evaluate(s_fwd)
                f_fwd = sum(f_fwd) if isinstance(f_fwd, list) else float(f_fwd)
                grad[j] = (f_fwd - subset_fits[i]) / (eps[j] + 1e-14)
            grad_norms.append(float(np.linalg.norm(grad)))

        return float(np.mean(grad_norms)) if grad_norms else 0.0

    @staticmethod
    def modality_indicator(fitnesses: np.ndarray) -> float:
        """
        Skewness of the fitness distribution as a proxy for multimodality.

        A unimodal symmetric distribution has skewness ≈ 0.
        Multimodal landscapes tend to produce non-zero skewness.
        """
        mean = np.mean(fitnesses)
        std = np.std(fitnesses)
        if std < 1e-10:
            return 0.0
        return float(np.mean(((fitnesses - mean) / std) ** 3))

    @staticmethod
    def ruggedness(fitnesses: np.ndarray) -> float:
        """
        Mean absolute difference between consecutive sample fitness values,
        normalised by the standard deviation.  A high value suggests a
        rugged landscape.
        """
        diffs = np.abs(np.diff(fitnesses))
        std = np.std(fitnesses)
        return float(np.mean(diffs) / (std + 1e-10))

    # ------------------------------------------------------------------
    # Composite feature extraction
    # ------------------------------------------------------------------

    def extract_features(self, problem) -> dict:
        """
        Extract all landscape features for *problem*.

        Returns
        -------
        dict with keys:
            fitness_mean, fitness_std, fitness_variance, fitness_min,
            fitness_max, gradient_magnitude, modality, ruggedness, dimension
        """
        samples, fitnesses = self.sample_landscape(problem)

        return {
            "fitness_mean": float(np.mean(fitnesses)),
            "fitness_std": float(np.std(fitnesses)),
            "fitness_variance": self.fitness_variance(fitnesses),
            "fitness_min": float(np.min(fitnesses)),
            "fitness_max": float(np.max(fitnesses)),
            "gradient_magnitude": self.gradient_approximation(
                problem, samples, fitnesses
            ),
            "modality": self.modality_indicator(fitnesses),
            "ruggedness": self.ruggedness(fitnesses),
            "dimension": float(len(problem.bounds()[0])),
        }

    @staticmethod
    def features_to_vector(features: dict) -> np.ndarray:
        """
        Convert a feature dict (from :meth:`extract_features`) to a
        sorted numpy array suitable for ML model input.

        Keys are sorted alphabetically to ensure a consistent ordering.
        """
        keys = sorted(features.keys())
        return np.array([features[k] for k in keys], dtype=float)
