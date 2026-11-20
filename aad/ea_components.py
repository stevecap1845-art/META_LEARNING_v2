"""
ea_components.py
----------------
Modular, plug-and-play EA operators.

Selection
---------
TournamentSelection   : k-tournament selection (default k=3).
RouletteWheelSelection: Fitness-proportionate selection.

Crossover
---------
SBXCrossover   : Simulated Binary Crossover (real-valued).
UniformCrossover: Uniform (bit-flip style) crossover.

Mutation
--------
GaussianMutation  : Additive Gaussian noise per gene.
PolynomialMutation: Polynomial mutation (real-valued, boundary-aware).
"""

from abc import ABC, abstractmethod

import numpy as np


# ---------------------------------------------------------------------------
# Selection operators
# ---------------------------------------------------------------------------

class SelectionOperator(ABC):
    """Abstract base class for selection operators."""

    @abstractmethod
    def select(self, population, fitnesses, num_selected: int):
        """
        Select *num_selected* individuals from *population*.

        Parameters
        ----------
        population   : list of np.ndarray
        fitnesses    : list of float (lower = better, minimisation assumed)
        num_selected : int

        Returns
        -------
        list of np.ndarray (copies of selected individuals)
        """


class TournamentSelection(SelectionOperator):
    """
    k-tournament selection.

    Parameters
    ----------
    tournament_size : int, default 3
        Number of individuals that compete in each tournament.
    """

    def __init__(self, tournament_size: int = 3):
        self.tournament_size = tournament_size

    def select(self, population, fitnesses, num_selected: int):
        selected = []
        n = len(population)
        for _ in range(num_selected):
            idxs = np.random.choice(n, self.tournament_size, replace=False)
            winner = idxs[int(np.argmin([fitnesses[i] for i in idxs]))]
            selected.append(population[winner].copy())
        return selected


class RouletteWheelSelection(SelectionOperator):
    """
    Roulette-wheel (fitness-proportionate) selection.

    Fitness values are inverted so that lower fitness → higher probability.
    """

    def select(self, population, fitnesses, num_selected: int):
        fits = np.array(fitnesses, dtype=float)
        # Shift so all values are > 0, then invert for minimisation
        shifted = fits.max() - fits + 1e-10
        probs = shifted / shifted.sum()
        idxs = np.random.choice(len(population), num_selected, p=probs)
        return [population[i].copy() for i in idxs]


# ---------------------------------------------------------------------------
# Crossover operators
# ---------------------------------------------------------------------------

class CrossoverOperator(ABC):
    """Abstract base class for crossover operators."""

    @abstractmethod
    def crossover(self, parent1: np.ndarray, parent2: np.ndarray, bounds):
        """
        Produce two children from two parents.

        Parameters
        ----------
        parent1, parent2 : np.ndarray  of shape (dim,)
        bounds           : (lb, ub) – lists/arrays of length *dim*

        Returns
        -------
        (child1, child2) : tuple of np.ndarray
        """


class SBXCrossover(CrossoverOperator):
    """
    Simulated Binary Crossover (SBX) for real-valued representations.

    Parameters
    ----------
    eta  : float, default 15  – distribution index (larger = closer to parents)
    prob : float, default 0.9 – crossover probability
    """

    def __init__(self, eta: float = 15.0, prob: float = 0.9):
        self.eta = eta
        self.prob = prob

    def crossover(self, parent1: np.ndarray, parent2: np.ndarray, bounds):
        if np.random.random() > self.prob:
            return parent1.copy(), parent2.copy()

        lb = np.asarray(bounds[0], dtype=float)
        ub = np.asarray(bounds[1], dtype=float)
        child1, child2 = parent1.copy(), parent2.copy()

        for i in range(len(parent1)):
            if np.random.random() <= 0.5 and abs(parent2[i] - parent1[i]) > 1e-14:
                x_lo = min(parent1[i], parent2[i])
                x_hi = max(parent1[i], parent2[i])
                spread = x_hi - x_lo

                # beta values based on distance to bounds
                beta_lo = 1.0 + 2.0 * (x_lo - lb[i]) / spread
                beta_hi = 1.0 + 2.0 * (ub[i] - x_hi) / spread
                exp = self.eta + 1.0

                alpha_lo = 2.0 - beta_lo ** (-exp)
                alpha_hi = 2.0 - beta_hi ** (-exp)

                def _betaq(alpha):
                    u = np.random.random()
                    if u <= 1.0 / alpha:
                        return (u * alpha) ** (1.0 / exp)
                    return (1.0 / (2.0 - u * alpha)) ** (1.0 / exp)

                bq1 = _betaq(alpha_lo)
                bq2 = _betaq(alpha_hi)
                mid = 0.5 * (x_lo + x_hi)
                child1[i] = np.clip(mid - 0.5 * bq1 * spread, lb[i], ub[i])
                child2[i] = np.clip(mid + 0.5 * bq2 * spread, lb[i], ub[i])

        return child1, child2


class UniformCrossover(CrossoverOperator):
    """
    Uniform crossover: each gene is independently swapped with probability 0.5.

    Parameters
    ----------
    prob : float, default 0.9 – probability that crossover is applied at all
    """

    def __init__(self, prob: float = 0.9):
        self.prob = prob

    def crossover(self, parent1: np.ndarray, parent2: np.ndarray, bounds):
        if np.random.random() > self.prob:
            return parent1.copy(), parent2.copy()

        mask = np.random.random(len(parent1)) < 0.5
        child1 = np.where(mask, parent1, parent2).astype(float)
        child2 = np.where(mask, parent2, parent1).astype(float)
        return child1, child2


# ---------------------------------------------------------------------------
# Mutation operators
# ---------------------------------------------------------------------------

class MutationOperator(ABC):
    """Abstract base class for mutation operators."""

    @abstractmethod
    def mutate(self, individual: np.ndarray, bounds) -> np.ndarray:
        """
        Mutate an individual in-place (returns a new array).

        Parameters
        ----------
        individual : np.ndarray of shape (dim,)
        bounds     : (lb, ub)

        Returns
        -------
        np.ndarray of shape (dim,)
        """


class GaussianMutation(MutationOperator):
    """
    Additive Gaussian mutation.

    Each gene is mutated with probability *prob*.  The noise is scaled
    proportionally to the range of the corresponding dimension.

    Parameters
    ----------
    prob  : float, default 0.1  – per-gene mutation probability
    sigma : float, default 0.1  – noise scale as fraction of range
    """

    def __init__(self, prob: float = 0.1, sigma: float = 0.1):
        self.prob = prob
        self.sigma = sigma

    def mutate(self, individual: np.ndarray, bounds) -> np.ndarray:
        lb = np.asarray(bounds[0], dtype=float)
        ub = np.asarray(bounds[1], dtype=float)
        child = individual.copy()
        mask = np.random.random(len(child)) < self.prob
        noise = np.random.normal(0.0, self.sigma * (ub - lb), len(child))
        child += mask * noise
        return np.clip(child, lb, ub)


class PolynomialMutation(MutationOperator):
    """
    Polynomial mutation for real-valued representations.

    Parameters
    ----------
    prob : float | None – per-gene probability; if None defaults to 1/dim
    eta  : float, default 20  – distribution index
    """

    def __init__(self, prob=None, eta: float = 20.0):
        self.prob = prob
        self.eta = eta

    def mutate(self, individual: np.ndarray, bounds) -> np.ndarray:
        lb = np.asarray(bounds[0], dtype=float)
        ub = np.asarray(bounds[1], dtype=float)
        child = individual.copy()
        n = len(child)
        prob = self.prob if self.prob is not None else 1.0 / n
        mut_pow = 1.0 / (self.eta + 1.0)

        for i in range(n):
            if np.random.random() >= prob:
                continue
            range_i = ub[i] - lb[i]
            if range_i < 1e-14:
                continue
            delta1 = (child[i] - lb[i]) / range_i
            delta2 = (ub[i] - child[i]) / range_i
            u = np.random.random()
            if u < 0.5:
                xy = max(0.0, 1.0 - delta1)
                val = 2.0 * u + (1.0 - 2.0 * u) * (xy ** (self.eta + 1.0))
                deltaq = val ** mut_pow - 1.0
            else:
                xy = max(0.0, 1.0 - delta2)
                val = 2.0 * (1.0 - u) + 2.0 * (u - 0.5) * (xy ** (self.eta + 1.0))
                deltaq = 1.0 - val ** mut_pow

            child[i] = np.clip(child[i] + deltaq * range_i, lb[i], ub[i])

        return child
