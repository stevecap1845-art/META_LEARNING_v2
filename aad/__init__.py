"""
Autonomous Algorithm Design (AAD) Framework
============================================
A meta-learning system that automatically generates, evaluates, and improves
Evolutionary Algorithms for arbitrary optimisation problems.

Modules
-------
problems        : Optimisation problem interface and benchmark functions
ea_components   : Modular EA operators (selection, crossover, mutation)
evolutionary_algorithm : Configurable EA runner
config_space    : EA configuration space and encoding utilities
landscape_features : ELA-inspired problem characterisation
surrogate_model : Random Forest / Gaussian Process surrogate model
meta_learner    : EA_Designer – meta-optimiser over algorithm configurations
llm_designer    : LLM-based (or rule-based) algorithm proposer
evaluation      : Multi-run evaluation and metrics framework
visualization   : Fitness curves, Pareto front, and meta-convergence plots
"""

from .problems import (
    OptimizationProblem,
    SphereProblem,
    RastriginProblem,
    RosenbrockProblem,
    AckleyProblem,
    ZDT1Problem,
    ZDT2Problem,
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
from .ea_components import (
    TournamentSelection,
    RouletteWheelSelection,
    SBXCrossover,
    UniformCrossover,
    GaussianMutation,
    PolynomialMutation,
)
from .evolutionary_algorithm import EvolutionaryAlgorithm, build_algorithm
from .config_space import (
    EA_CONFIG_SPACE,
    EXTENDED_CONFIG_SPACE,
    MEALPY_ALGORITHM_KEYS,
    random_config,
    all_configs,
    config_to_vector,
)
from .mealpy_algorithms import MealpyAlgorithm, MEALPY_REGISTRY
from .landscape_features import LandscapeFeatureExtractor
from .surrogate_model import SurrogateModel
from .meta_learner import EA_Designer
from .llm_designer import LLMDesigner
from .evaluation import EvaluationFramework
from .visualization import Visualizer

__all__ = [
    "OptimizationProblem",
    "SphereProblem",
    "RastriginProblem",
    "RosenbrockProblem",
    "AckleyProblem",
    "ZDT1Problem",
    "ZDT2Problem",
    # BBOB suite
    "BBOB_F1_Sphere",
    "BBOB_F2_EllipsoidalSeparable",
    "BBOB_F3_RastriginSeparable",
    "BBOB_F4_BucheRastrigin",
    "BBOB_F5_LinearSlope",
    "BBOB_F6_AttractiveSector",
    "BBOB_F7_StepEllipsoidal",
    "BBOB_F8_Rosenbrock",
    "BBOB_F9_RosenbrockRotated",
    "BBOB_F10_EllipsoidalRotated",
    "BBOB_F11_Discus",
    "BBOB_F12_BentCigar",
    "BBOB_F13_SharpRidge",
    "BBOB_F14_DifferentPowers",
    "BBOB_F15_RastriginRotated",
    "BBOB_F16_Weierstrass",
    "BBOB_F17_SchaffersF7",
    "BBOB_F18_SchaffersF7IllConditioned",
    "BBOB_F19_GriewankRosenbrock",
    "BBOB_F20_Schwefel",
    "BBOB_F21_Gallagher101",
    "BBOB_F22_Gallagher21",
    "BBOB_F23_Katsuura",
    "BBOB_F24_LunacekBiRastrigin",
    "TournamentSelection",
    "RouletteWheelSelection",
    "SBXCrossover",
    "UniformCrossover",
    "GaussianMutation",
    "PolynomialMutation",
    "EvolutionaryAlgorithm",
    "build_algorithm",
    "MealpyAlgorithm",
    "MEALPY_REGISTRY",
    "MEALPY_ALGORITHM_KEYS",
    "EA_CONFIG_SPACE",
    "EXTENDED_CONFIG_SPACE",
    "random_config",
    "all_configs",
    "config_to_vector",
    "LandscapeFeatureExtractor",
    "SurrogateModel",
    "EA_Designer",
    "LLMDesigner",
    "EvaluationFramework",
    "Visualizer",
]
