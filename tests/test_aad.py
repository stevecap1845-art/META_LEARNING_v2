"""
tests/test_aad.py
-----------------
Lightweight unit and integration tests for the AAD framework.
Run with:  python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from aad.problems import (
    SphereProblem,
    RastriginProblem,
    RosenbrockProblem,
    AckleyProblem,
    ZDT1Problem,
    ZDT2Problem,
)
from aad.ea_components import (
    TournamentSelection,
    RouletteWheelSelection,
    SBXCrossover,
    UniformCrossover,
    GaussianMutation,
    PolynomialMutation,
)
from aad.evolutionary_algorithm import EvolutionaryAlgorithm
from aad.config_space import (
    EA_CONFIG_SPACE,
    random_config,
    all_configs,
    config_to_vector,
    vector_to_config,
)
from aad.landscape_features import LandscapeFeatureExtractor
from aad.surrogate_model import SurrogateModel
from aad.meta_learner import EA_Designer
from aad.llm_designer import LLMDesigner
from aad.evaluation import EvaluationFramework
from aad.visualization import Visualizer


# ---------------------------------------------------------------------------
# Problems
# ---------------------------------------------------------------------------

class TestProblems:
    def test_sphere_known_value(self):
        p = SphereProblem(dim=3)
        assert p.evaluate([1.0, 2.0, 3.0]) == pytest.approx(14.0)

    def test_sphere_global_min(self):
        p = SphereProblem(dim=5)
        assert p.evaluate([0.0] * 5) == pytest.approx(0.0)

    def test_rastrigin_global_min(self):
        p = RastriginProblem(dim=4)
        assert p.evaluate([0.0] * 4) == pytest.approx(0.0)

    def test_rosenbrock_global_min(self):
        p = RosenbrockProblem(dim=5)
        assert p.evaluate([1.0] * 5) == pytest.approx(0.0)

    def test_ackley_global_min(self):
        p = AckleyProblem(dim=5)
        assert p.evaluate([0.0] * 5) == pytest.approx(0.0, abs=1e-10)

    def test_bounds_length(self):
        for cls, dim in [(SphereProblem, 7), (RastriginProblem, 7)]:
            p = cls(dim=dim)
            lb, ub = p.bounds()
            assert len(lb) == dim
            assert len(ub) == dim

    def test_zdt1_multiobjective(self):
        p = ZDT1Problem(dim=5)
        assert p.is_multiobjective()
        result = p.evaluate([0.5] * 5)
        assert isinstance(result, list) and len(result) == 2

    def test_zdt2_multiobjective(self):
        p = ZDT2Problem(dim=5)
        assert p.is_multiobjective()
        result = p.evaluate([0.3] * 5)
        assert isinstance(result, list) and len(result) == 2

    def test_name_property(self):
        assert SphereProblem().name == "SphereProblem"

    def test_dimension_property(self):
        assert SphereProblem(dim=8).dimension == 8


# ---------------------------------------------------------------------------
# EA Components
# ---------------------------------------------------------------------------

class TestSelectionOperators:
    def _make_pop(self, n=10, dim=5):
        return [np.random.random(dim) for _ in range(n)]

    def test_tournament_selection_count(self):
        pop = self._make_pop()
        fits = list(range(10))
        sel = TournamentSelection(tournament_size=3)
        selected = sel.select(pop, fits, 5)
        assert len(selected) == 5

    def test_roulette_selection_count(self):
        pop = self._make_pop()
        fits = [float(i) for i in range(10)]
        sel = RouletteWheelSelection()
        selected = sel.select(pop, fits, 7)
        assert len(selected) == 7

    def test_selection_returns_copies(self):
        pop = self._make_pop(5)
        fits = [1.0] * 5
        sel = TournamentSelection()
        selected = sel.select(pop, fits, 3)
        selected[0][0] = 999.0
        assert pop[0][0] != 999.0  # original not modified


class TestCrossoverOperators:
    def _bounds(self, dim=5):
        return ([-5.0] * dim, [5.0] * dim)

    def test_sbx_output_shape(self):
        p1, p2 = np.array([1.0] * 5), np.array([2.0] * 5)
        cx = SBXCrossover()
        c1, c2 = cx.crossover(p1, p2, self._bounds())
        assert c1.shape == (5,) and c2.shape == (5,)

    def test_sbx_within_bounds(self):
        lb, ub = -5.0, 5.0
        cx = SBXCrossover(prob=1.0)
        for _ in range(20):
            p1 = np.random.uniform(lb, ub, 10)
            p2 = np.random.uniform(lb, ub, 10)
            c1, c2 = cx.crossover(p1, p2, ([lb] * 10, [ub] * 10))
            assert np.all(c1 >= lb) and np.all(c1 <= ub)
            assert np.all(c2 >= lb) and np.all(c2 <= ub)

    def test_uniform_crossover_within_bounds(self):
        p1, p2 = np.ones(5), np.zeros(5)
        cx = UniformCrossover(prob=1.0)
        c1, c2 = cx.crossover(p1, p2, ([0.0] * 5, [1.0] * 5))
        assert np.all((c1 == 0) | (c1 == 1))


class TestMutationOperators:
    def _bounds(self, dim=5):
        return ([-5.0] * dim, [5.0] * dim)

    def test_gaussian_within_bounds(self):
        mut = GaussianMutation(prob=1.0, sigma=0.5)
        ind = np.zeros(10)
        result = mut.mutate(ind, ([-5.0] * 10, [5.0] * 10))
        assert np.all(result >= -5.0) and np.all(result <= 5.0)

    def test_polynomial_within_bounds(self):
        mut = PolynomialMutation(prob=1.0)
        ind = np.zeros(10)
        result = mut.mutate(ind, ([-5.0] * 10, [5.0] * 10))
        assert np.all(result >= -5.0) and np.all(result <= 5.0)

    def test_mutation_returns_new_array(self):
        ind = np.array([1.0, 2.0, 3.0])
        mut = GaussianMutation(prob=1.0)
        result = mut.mutate(ind, ([-10.0] * 3, [10.0] * 3))
        assert result is not ind


# ---------------------------------------------------------------------------
# Evolutionary Algorithm
# ---------------------------------------------------------------------------

class TestEvolutionaryAlgorithm:
    def _default_cfg(self, gens=20, pop=10):
        return {
            "population_size": pop,
            "max_generations": gens,
            "selection": "tournament",
            "crossover": "sbx",
            "mutation": "gaussian",
        }

    def test_run_returns_solution_and_fitness(self):
        ea = EvolutionaryAlgorithm(self._default_cfg())
        sol, fit = ea.run(SphereProblem(dim=5))
        assert isinstance(sol, np.ndarray)
        assert isinstance(fit, float)

    def test_history_length(self):
        gens = 15
        ea = EvolutionaryAlgorithm(self._default_cfg(gens=gens))
        ea.run(SphereProblem(dim=3))
        assert len(ea.history) == gens + 1  # gen 0 + gens generations

    def test_history_non_increasing(self):
        ea = EvolutionaryAlgorithm(self._default_cfg(gens=30))
        ea.run(SphereProblem(dim=5))
        for i in range(1, len(ea.history)):
            assert ea.history[i] <= ea.history[i - 1] + 1e-9

    def test_invalid_selection_raises(self):
        with pytest.raises(ValueError):
            EvolutionaryAlgorithm({"selection": "bad_operator"})

    def test_all_operator_combinations(self):
        p = SphereProblem(dim=3)
        for sel in ("tournament", "roulette"):
            for cx in ("sbx", "uniform"):
                for mut in ("gaussian", "polynomial"):
                    cfg = {
                        "population_size": 6,
                        "max_generations": 5,
                        "selection": sel,
                        "crossover": cx,
                        "mutation": mut,
                    }
                    ea = EvolutionaryAlgorithm(cfg)
                    _, fit = ea.run(p)
                    assert np.isfinite(fit)

    def test_multiobjective_run(self):
        ea = EvolutionaryAlgorithm(self._default_cfg())
        _, fit = ea.run(ZDT1Problem(dim=5))
        assert np.isfinite(fit)


# ---------------------------------------------------------------------------
# Config Space
# ---------------------------------------------------------------------------

class TestConfigSpace:
    def test_random_config_keys(self):
        cfg = random_config()
        assert set(cfg.keys()) == set(EA_CONFIG_SPACE.keys())

    def test_random_config_valid_values(self):
        for _ in range(10):
            cfg = random_config()
            for k, v in cfg.items():
                assert v in EA_CONFIG_SPACE[k]

    def test_all_configs_count(self):
        configs = all_configs()
        expected = 1
        for v in EA_CONFIG_SPACE.values():
            expected *= len(v)
        assert len(configs) == expected

    def test_config_to_vector_length(self):
        cfg = random_config()
        vec = config_to_vector(cfg)
        assert len(vec) > 0

    def test_vector_roundtrip(self):
        cfg = random_config()
        vec = config_to_vector(cfg)
        recovered = vector_to_config(vec)
        assert set(recovered.keys()) == set(cfg.keys())


# ---------------------------------------------------------------------------
# Landscape Features
# ---------------------------------------------------------------------------

class TestLandscapeFeatures:
    def test_extract_returns_expected_keys(self):
        ext = LandscapeFeatureExtractor(n_samples=30)
        feats = ext.extract_features(SphereProblem(dim=3))
        expected = {
            "fitness_mean", "fitness_std", "fitness_variance",
            "fitness_min", "fitness_max", "gradient_magnitude",
            "modality", "ruggedness", "dimension",
        }
        assert set(feats.keys()) == expected

    def test_features_to_vector_shape(self):
        ext = LandscapeFeatureExtractor(n_samples=30)
        feats = ext.extract_features(SphereProblem(dim=3))
        vec = ext.features_to_vector(feats)
        assert vec.shape == (len(feats),)

    def test_dimension_feature(self):
        ext = LandscapeFeatureExtractor(n_samples=20)
        feats = ext.extract_features(SphereProblem(dim=7))
        assert feats["dimension"] == pytest.approx(7.0)


# ---------------------------------------------------------------------------
# Surrogate Model
# ---------------------------------------------------------------------------

class TestSurrogateModel:
    def test_rf_fit_predict(self):
        X = np.random.random((20, 5))
        y = np.random.random(20)
        sm = SurrogateModel("rf")
        sm.fit(X, y)
        preds = sm.predict(X[:5])
        assert preds.shape == (5,)

    def test_gp_fit_predict(self):
        X = np.random.random((15, 4))
        y = np.random.random(15)
        sm = SurrogateModel("gp")
        sm.fit(X, y)
        preds = sm.predict(X[:3])
        assert preds.shape == (3,)

    def test_predict_before_fit_raises(self):
        sm = SurrogateModel("rf")
        with pytest.raises(RuntimeError):
            sm.predict(np.random.random((3, 5)))

    def test_predict_1d_input(self):
        X = np.random.random((20, 5))
        y = np.random.random(20)
        sm = SurrogateModel("rf")
        sm.fit(X, y)
        preds = sm.predict(X[0])  # 1-D input
        assert preds.shape == (1,)

    def test_uncertainty_rf(self):
        X = np.random.random((20, 5))
        y = np.random.random(20)
        sm = SurrogateModel("rf")
        sm.fit(X, y)
        means, stds = sm.predict_with_uncertainty(X[:5])
        assert means.shape == stds.shape == (5,)

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            SurrogateModel("bad_type")


# ---------------------------------------------------------------------------
# LLM Designer
# ---------------------------------------------------------------------------

class TestLLMDesigner:
    def test_rule_based_returns_valid_config(self):
        d = LLMDesigner()  # no API key → rule-based
        cfg = d.propose_algorithm("High-dimensional multimodal complex problem.")
        assert cfg["selection"] in EA_CONFIG_SPACE["selection"]
        assert cfg["crossover"] in EA_CONFIG_SPACE["crossover"]
        assert cfg["mutation"] in EA_CONFIG_SPACE["mutation"]

    def test_generate_description_is_string(self):
        d = LLMDesigner()
        desc = d.generate_description(SphereProblem(dim=10))
        assert isinstance(desc, str) and len(desc) > 0

    def test_rule_based_keywords(self):
        d = LLMDesigner()
        cfg = d.propose_algorithm("simple low-dimensional unimodal smooth problem")
        # Heuristic: smooth → polynomial mutation, small pop
        assert cfg["mutation"] == "polynomial"
        assert cfg["population_size"] == 20


# ---------------------------------------------------------------------------
# Evaluation Framework
# ---------------------------------------------------------------------------

class TestEvaluationFramework:
    def _cfg(self):
        return {
            "population_size": 10,
            "max_generations": 10,
            "selection": "tournament",
            "crossover": "sbx",
            "mutation": "gaussian",
        }

    def test_evaluate_keys(self):
        ev = EvaluationFramework(n_runs=2)
        metrics = ev.evaluate(self._cfg(), SphereProblem(dim=3))
        for key in (
            "best_fitness", "mean_fitness", "std_fitness",
            "worst_fitness", "convergence_speed", "stability",
            "mean_runtime", "histories",
        ):
            assert key in metrics

    def test_histories_count(self):
        n = 3
        ev = EvaluationFramework(n_runs=n)
        metrics = ev.evaluate(self._cfg(), SphereProblem(dim=3))
        assert len(metrics["histories"]) == n

    def test_best_le_mean(self):
        ev = EvaluationFramework(n_runs=4)
        metrics = ev.evaluate(self._cfg(), SphereProblem(dim=3))
        assert metrics["best_fitness"] <= metrics["mean_fitness"] + 1e-9


# ---------------------------------------------------------------------------
# Meta-Learner (integration)
# ---------------------------------------------------------------------------

class TestEADesigner:
    def test_evolve_returns_config_and_float(self):
        designer = EA_Designer(
            population_size=3, generations=1, runs_per_eval=1, use_surrogate=False
        )
        cfg, perf = designer.evolve(SphereProblem(dim=3), verbose=False)
        assert isinstance(cfg, dict)
        assert isinstance(perf, float)
        assert np.isfinite(perf)

    def test_meta_convergence_length(self):
        gens = 2
        designer = EA_Designer(
            population_size=3, generations=gens, runs_per_eval=1, use_surrogate=False
        )
        designer.evolve(SphereProblem(dim=3), verbose=False)
        # gen 0 + gens
        assert len(designer.meta_convergence) == gens + 1

    def test_evolve_with_surrogate(self):
        designer = EA_Designer(
            population_size=4, generations=2, runs_per_eval=1, use_surrogate=True
        )
        cfg, perf = designer.evolve(SphereProblem(dim=3), verbose=False)
        assert np.isfinite(perf)

    def test_evolve_multiobjective(self):
        designer = EA_Designer(
            population_size=3, generations=1, runs_per_eval=1, use_surrogate=False
        )
        cfg, perf = designer.evolve(ZDT1Problem(dim=5), verbose=False)
        assert np.isfinite(perf)


# ---------------------------------------------------------------------------
# Visualization (smoke tests – no display, just file creation)
# ---------------------------------------------------------------------------

class TestVisualizer:
    def test_fitness_curves_creates_file(self, tmp_path):
        viz = Visualizer(output_dir=str(tmp_path))
        histories = [[10.0, 5.0, 2.0, 1.0], [8.0, 4.0, 2.5, 1.2]]
        fpath = viz.plot_fitness_curves(histories, filename="fc.png")
        assert os.path.exists(fpath)

    def test_pareto_front_creates_file(self, tmp_path):
        viz = Visualizer(output_dir=str(tmp_path))
        fits = [[i * 0.1, 1 - i * 0.1] for i in range(10)]
        fpath = viz.plot_pareto_front(fits, filename="pf.png")
        assert os.path.exists(fpath)

    def test_meta_convergence_creates_file(self, tmp_path):
        viz = Visualizer(output_dir=str(tmp_path))
        fpath = viz.plot_meta_convergence([5.0, 3.0, 1.5], filename="mc.png")
        assert os.path.exists(fpath)

    def test_algorithm_comparison_creates_file(self, tmp_path):
        viz = Visualizer(output_dir=str(tmp_path))
        results = [
            ({"selection": "tournament"}, {"best_fitness": 0.5}),
            ({"selection": "roulette"}, {"best_fitness": 0.3}),
        ]
        fpath = viz.plot_algorithm_comparison(results, filename="cmp.png")
        assert os.path.exists(fpath)

    def test_pareto_skips_1d(self, tmp_path):
        viz = Visualizer(output_dir=str(tmp_path))
        fpath = viz.plot_pareto_front([[1.0], [2.0]])
        assert fpath == ""
