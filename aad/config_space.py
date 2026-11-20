"""
config_space.py
---------------
EA configuration space definition and utility functions.

The config space defines all hyperparameters that the meta-optimiser can
tune.  Helper functions convert configs to numeric vectors suitable for
surrogate models.
"""

import itertools
import random
from typing import Dict, List, Any

import numpy as np

# ---------------------------------------------------------------------------
# Default configuration space
# ---------------------------------------------------------------------------

EA_CONFIG_SPACE: Dict[str, List[Any]] = {
    "population_size": [20, 50, 100],
    "selection": ["tournament", "roulette"],
    "crossover": ["sbx", "uniform"],
    "mutation": ["gaussian", "polynomial"],
    "max_generations": [50, 100, 200],
}

# ---------------------------------------------------------------------------
# Extended configuration space – includes mealpy algorithms
# ---------------------------------------------------------------------------
# When ``algorithm`` is "ea" the built-in EvolutionaryAlgorithm is used and
# the selection / crossover / mutation keys are respected.  For any other
# value the corresponding mealpy optimizer is used and those three keys are
# ignored (only population_size and max_generations are forwarded).

MEALPY_ALGORITHM_KEYS: List[str] = [
    # Evolutionary
    "GA", "DE", "JADE", "CMA_ES", "SHADE", "L_SHADE",
    # Swarm
    "PSO", "GWO", "WOA", "HHO", "ABC",
    "GJO", "ARO", "AO", "MPA", "HBA",
    # Physics
    "SA", "EO", "MVO", "RIME",
    # Bio / Math
    "SMA", "BBO", "SCA", "AOA",
]

EXTENDED_CONFIG_SPACE: Dict[str, List[Any]] = {
    "algorithm": ["ea"] + MEALPY_ALGORITHM_KEYS,
    "population_size": [20, 50, 100],
    "selection": ["tournament", "roulette"],
    "crossover": ["sbx", "uniform"],
    "mutation": ["gaussian", "polynomial"],
    "max_generations": [50, 100, 200],
}


# ---------------------------------------------------------------------------
# Sampling utilities
# ---------------------------------------------------------------------------

def random_config(config_space: dict = None) -> dict:
    """
    Sample one random EA configuration from *config_space*.

    Parameters
    ----------
    config_space : dict, optional
        Mapping ``{param_name: [value1, value2, ...]}``.
        Defaults to :data:`EA_CONFIG_SPACE`.

    Returns
    -------
    dict  –  one value chosen uniformly at random per parameter.
    """
    if config_space is None:
        config_space = EA_CONFIG_SPACE
    return {k: random.choice(v) for k, v in config_space.items()}


def all_configs(config_space: dict = None) -> list:
    """
    Enumerate every possible configuration in *config_space*.

    Returns
    -------
    list of dict
    """
    if config_space is None:
        config_space = EA_CONFIG_SPACE
    keys = list(config_space.keys())
    values = list(config_space.values())
    return [dict(zip(keys, combo)) for combo in itertools.product(*values)]


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def config_to_vector(config: dict, config_space: dict = None) -> list:
    """
    Encode an EA configuration as a flat numeric vector.

    Numeric parameters (int/float) are passed through as floats.
    Categorical parameters are one-hot encoded using the order defined in
    *config_space*.

    Parameters
    ----------
    config       : dict  –  an EA configuration
    config_space : dict, optional  –  defaults to :data:`EA_CONFIG_SPACE`

    Returns
    -------
    list of float
    """
    if config_space is None:
        config_space = EA_CONFIG_SPACE

    vec = []
    for key, options in config_space.items():
        val = config.get(key, options[0])
        if isinstance(options[0], (int, float)):
            # Numeric parameter: normalise to [0, 1] within known range
            lo, hi = float(min(options)), float(max(options))
            normalised = (float(val) - lo) / (hi - lo + 1e-10)
            vec.append(normalised)
        else:
            # Categorical: one-hot
            vec.extend([1.0 if val == o else 0.0 for o in options])

    return vec


def vector_to_config(vector: list, config_space: dict = None) -> dict:
    """
    Decode a numeric vector back into an EA configuration (nearest match).

    This is the inverse of :func:`config_to_vector` under a nearest-
    neighbour rounding scheme.

    Parameters
    ----------
    vector       : list of float
    config_space : dict, optional

    Returns
    -------
    dict
    """
    if config_space is None:
        config_space = EA_CONFIG_SPACE

    config = {}
    idx = 0
    for key, options in config_space.items():
        if isinstance(options[0], (int, float)):
            # Denormalise and pick closest option
            lo, hi = float(min(options)), float(max(options))
            raw = vector[idx] * (hi - lo) + lo
            config[key] = min(options, key=lambda o: abs(float(o) - raw))
            idx += 1
        else:
            # One-hot: pick the highest-scoring option
            scores = vector[idx: idx + len(options)]
            config[key] = options[int(np.argmax(scores))]
            idx += len(options)

    return config
