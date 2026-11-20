# Meta-Learning & Auto-ML: Autonomous Algorithm Design (AAD)

A complete, modular Python framework for **Autonomous Algorithm Design** —
a system that automatically generates, evaluates, and improves Evolutionary
Algorithms (EAs) for arbitrary optimisation problems.

---

## Overview

The framework implements the full loop described by *Algorithm Selection* and
*No Free Lunch* research: instead of picking one EA by hand, the system
*learns* which EA works best for the problem at hand.

```
Problem  →  Landscape Features  →  Meta-Learner  →  Best EA Config  →  Solution
                                        ↑
                               Surrogate Model
                               (cheap screening)
```

---

## Repository Structure

```
.
├── aad/                           # Main framework package
│   ├── __init__.py
│   ├── problems.py                # Problem interface + benchmarks
│   ├── ea_components.py           # Modular EA operators
│   ├── evolutionary_algorithm.py  # Configurable EA runner
│   ├── config_space.py            # EA config space + encoding
│   ├── landscape_features.py      # ELA-inspired feature extraction
│   ├── surrogate_model.py         # RF / GP surrogate model
│   ├── meta_learner.py            # EA_Designer meta-optimiser
│   ├── llm_designer.py            # LLM / rule-based algorithm proposer
│   ├── evaluation.py              # Multi-run evaluation framework
│   └── visualization.py           # Plotting utilities
├── experiment_runner.py           # Top-level experiment entry point
├── requirements.txt
└── results/                       # Auto-created; plots + JSON logs go here
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the full experiment

```bash
python experiment_runner.py
```

This will:
- Run the AAD meta-learning loop on 5 benchmark problems
- Log all results to `results/experiment_results.json`
- Save fitness-curve, meta-convergence, and (for ZDT1) Pareto-front plots
  under `results/`

### 3. Minimal example

```python
from aad import EA_Designer, SphereProblem, EvaluationFramework

problem = SphereProblem(dim=10)

# Auto-design the best EA for this problem
designer = EA_Designer(population_size=6, generations=3, runs_per_eval=2)
best_config, best_perf = designer.evolve(problem, verbose=True)

# Fully evaluate the winner
evaluator = EvaluationFramework(n_runs=5)
metrics = evaluator.evaluate(best_config, problem, verbose=True)
EvaluationFramework.summarize(metrics)
```

---

## Components

### Problem Interface

All benchmark problems inherit from `OptimizationProblem`:

| Class | Type | Notes |
|---|---|---|
| `SphereProblem` | single-obj | Unimodal baseline |
| `RastriginProblem` | single-obj | Highly multimodal |
| `RosenbrockProblem` | single-obj | Narrow curved valley |
| `AckleyProblem` | single-obj | Deceptive flat outer region |
| `ZDT1Problem` | multi-obj | Convex Pareto front |
| `ZDT2Problem` | multi-obj | Non-convex Pareto front |

Custom problems need only three methods:

```python
class MyProblem(OptimizationProblem):
    def evaluate(self, solution): ...   # returns float or [f1, f2, ...]
    def bounds(self): ...               # returns (lb_list, ub_list)
    def is_multiobjective(self): ...    # returns bool
```

### EA Configuration Space

```python
EA_CONFIG_SPACE = {
    "population_size": [20, 50, 100],
    "selection":       ["tournament", "roulette"],
    "crossover":       ["sbx", "uniform"],
    "mutation":        ["gaussian", "polynomial"],
    "max_generations": [50, 100, 200],
}
```

### EA_Designer (Meta-Learner)

```python
from aad import EA_Designer

designer = EA_Designer(
    population_size=10,   # meta-population size
    generations=5,        # meta-evolution rounds
    runs_per_eval=3,      # EA runs per config (for stable estimates)
    use_surrogate=True,   # Random Forest pre-screening
)
best_config, best_perf = designer.evolve(problem)
```

### LLM Designer

```python
from aad import LLMDesigner

# Without API key → rule-based heuristic (no network needed)
designer = LLMDesigner()
config = designer.propose_algorithm("High-dimensional multimodal continuous problem.")

# With OpenAI key → real LLM call
designer = LLMDesigner(api_key="sk-...", model="gpt-4")
config = designer.propose_algorithm(designer.generate_description(problem))
```

### Surrogate Model

```python
from aad import SurrogateModel

surrogate = SurrogateModel(model_type="rf")   # or "gp"
surrogate.fit(X_train, y_train)
predictions = surrogate.predict(X_test)
means, stds = surrogate.predict_with_uncertainty(X_test)
```

---

## Sample Output

```
======================================================================
  AUTONOMOUS ALGORITHM DESIGN (AAD) – Experiment Runner
======================================================================
  Problems        : ['SphereProblem', 'RastriginProblem', ...]
  Meta-generations: 3
  Meta-pop-size   : 6
  Runs per eval   : 2
  Surrogate       : True
======================================================================

##########  Problem: SphereProblem  (dim=10, multi-obj=False)  ##########

  AAD Meta-Learning  |  Problem: SphereProblem
  Gen 0  best=0.012345  cfg={'population_size': 100, ...}
  Gen 1  best=0.003421  cfg={'population_size': 100, ...}
  ...
  ✓ Best config : {'population_size': 100, 'selection': 'tournament', ...}
  ✓ Performance : 0.000412

  [Results] SphereProblem
    best_fitness    : 0.000412
    mean_fitness    : 0.000623
    std_fitness     : 0.000091
    convergence_gen : 28.4
    stability       : 1823.5
    mean_runtime    : 0.35s
```

Plots saved to `results/`:
- `fitness_SphereProblem.png` — convergence curves per run + mean
- `meta_SphereProblem.png` — meta-level best performance per generation
- `pareto_ZDT1Problem.png` — objective-space scatter (multi-obj only)
- `experiment_results.json` — full numeric results

---

## Advanced Extensions

| Feature | Status |
|---|---|
| Surrogate-assisted screening | ✅ enabled by default |
| Meta-level convergence tracking | ✅ `designer.meta_convergence` |
| Parallel surrogate (RF) | ✅ `n_jobs=-1` |
| Fitness curve visualisation | ✅ |
| Pareto front visualisation | ✅ |
| LLM integration (OpenAI) | ✅ (API key optional) |
| Custom problem plug-in | ✅ |

---

## Dependencies

- Python ≥ 3.8
- NumPy ≥ 1.21
- scikit-learn ≥ 1.0
- Matplotlib ≥ 3.4

Optional (for LLM mode):
- `openai` Python package + valid OpenAI API key
