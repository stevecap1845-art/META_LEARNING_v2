# Phase 0 plan: reproducible environment and code health

Drafted 2026-11-20. Part B was rewritten the same day from a reading of this
repository's code only; nothing from earlier rounds is used. Part A
(environment) is done. Part B (health check) is waiting for review.

Phase 0 produces no research result. It shows that the tools work and lists
what in the code is broken, so that Phase 2 knows what to fix.

## Goal

Before any experiment, show with evidence that:

1. the environment can be rebuilt exactly from files in the repository;
2. every module imports, and every package the code imports is installed;
3. the modules fit together: each caller builds the algorithm it means to;
4. every algorithm and main component runs on a tiny case, and we know how
   many evaluations it spends and whether the same seed repeats it;
5. every defect in the register below is confirmed or ruled out, and each has
   a decision.

Phase 0 does not fix code (that is Phase 2, unless you decide otherwise for a
defect) and does not judge which algorithms optimise well (that is the
Phase 3 screening).

## Part A: environment (done 2026-11-20)

| Step | Passes when | Status |
|---|---|---|
| A1 | Git repository whose `.gitignore` covers caches, venvs, the local Python and `.env`; pushed to GitHub | done |
| A2 | Python 3.11.9 inside the project folder (`python-3.11.9/`); 3.11 is required by the pflacco pins (numpy 1.24.4) | done |
| A3 | `.venv` from `requirements.txt` and `.venv-pflacco` from `requirements-pflacco.txt`; they cannot share one environment (numpy 2.4.6 vs 1.24.4, pandas 3.0.5 vs 2.0.3, scikit-learn 1.9.0 vs 1.2.2) | done |
| A4 | `pip freeze` in each venv equals its requirement file; `pip check` clean | done |
| A5 | Baseline test run recorded | done: 54 passed |
| A6 | No secrets in tracked files | done after a fix (see the context document) |

### Rebuilding the environment on another machine

```powershell
# 1. any Python 3.11.9 (python.org installer, or copy a 3.11.9 install into python-3.11.9\)
python-3.11.9\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
python-3.11.9\python.exe -m venv .venv-pflacco
.venv-pflacco\Scripts\python.exe -m pip install -r requirements-pflacco.txt
.venv\Scripts\python.exe -m pytest -q tests
```

## Part B: health check (to run)

One script, `scripts/phase0_health_check.py`, runs C1 to C5 in `.venv` and
writes its results to `results/phase0/`. It reads the code and runs it; it
changes nothing in `aad/`. Expected run time: a few minutes. C6 is done by
reading.

| # | Check | Passes when |
|---|---|---|
| C1 | Imports and packages: each `aad` module and `experiment_runner.py` imports in a fresh process; every name in `aad.__all__` exists; every third-party module the code imports is installed in `.venv` and pinned in `requirements.txt` | all pass, or each failure is in the register |
| C2 | Wiring: what `build_algorithm` builds for `"ea"`, for each of the 24 mealpy keys, and for a configuration with no `algorithm` key; the two lists of 24 mealpy names (`config_space.py:37`, `mealpy_algorithms.py:182`) agree; which algorithm `EA_Designer` actually runs when given `EXTENDED_CONFIG_SPACE`; all 30 problem classes have `evaluate`, `bounds`, `is_multiobjective` and `name` and give finite values inside their bounds; each BBOB class's value at its `xopt`; the feature extractor gives the same 9 finite features for every single-objective problem; the surrogate accepts the vectors `EA_Designer` builds | every row recorded; each surprise is in the register |
| C3 | Algorithm runs: `ea` with each of its 8 operator combinations, and each of the 24 mealpy algorithms, on BBOB F1 and F15 in dimension 5 with population 20 and 10 generations, twice with the same global seeds (`random.seed`, `np.random.seed`). For each run: finished or the error; best value finite; evaluations counted by a wrapper around `evaluate`, against population × (generations + 1); same result both times; seconds per run | all 64 algorithm-problem pairs have a row; failures are listed, not fixed |
| C4 | Other components on tiny cases: the feature extractor (evaluations counted); `EA_Designer` with population 4 and 1 generation, surrogate on and off; `LLMDesigner` rule-based, and in LLM mode with a dummy key to see what a failed call returns (no request reaches the API, because the client import fails first, see D4); `EvaluationFramework` with 2 runs, plus one problem that returns NaN to see how a failed run is handled; `SurrogateModel` RF and GP each fitted twice on the same data, comparing predictions, and the units of `predict_with_uncertainty`; `Visualizer`'s four plots and `run_experiment` on one problem with the smallest settings, both writing to a temporary folder | every component has a row; surprises go to the register |
| C5 | Tests: `pytest tests` three times; list the public parts that no test runs | all pass every time, or the failure is in the register |
| C6 | README: where the root `README.md` and the code disagree (reading only; the README is not edited) | every difference listed in the context document |

## Defect register

Found by reading this repository's code on 2026-11-20. The health check
confirms each item or rules it out. The proposed decisions follow the project
plan's phases; you make the final call on each.

The health check ran on 2026-11-20. The register as it stands after the run,
with one new item (D15) and the decision for each, is in
[phase0_context.md §6](../../context/phase0_context.md#6-defects-and-decisions).

| # | Defect | Where | Confirmed by | Proposed decision |
|---|---|---|---|---|
| D1 | A configuration without an `algorithm` key builds PSO, although the docstring promises the EA. `EvaluationFramework` builds through this path, so in `experiment_runner.py` the final evaluation and the LLM designer's configuration both run PSO | `aad/evolutionary_algorithm.py:221`, `aad/evaluation.py:67` | C2 | fix in Phase 2 |
| D2 | `EA_Designer` always builds the EA, so the `algorithm` key in `EXTENDED_CONFIG_SPACE` has no effect while it searches | `aad/meta_learner.py:118` | C2 | fix in Phase 2 |
| D3 | `random_config`, `all_configs`, `config_to_vector`, `EA_Designer` and `LLMDesigner` default to `EA_CONFIG_SPACE`, which has no `algorithm` key | `aad/config_space.py:77`, `aad/meta_learner.py:66`, `aad/llm_designer.py:47` | reading | Phase 2: replaced by the candidate module |
| D4 | LLM mode imports `google.generativeai`, which is not installed (`google-genai` is pinned instead), so every LLM call fails and silently returns a rule-based pick. The prompt also contains the problem's name, and answers are checked for their keys but not their values | `aad/llm_designer.py:117`, `:156`, `:203`, `:150` | C1, C4 | fix in Phase 8 |
| D5 | No seeds: the EA and its operators use the global `np.random`; mealpy's `solve` gets no seed; feature sampling, `EA_Designer` and the rule-based proposal are unseeded | `aad/ea_components.py`, `aad/mealpy_algorithms.py:277`, `aad/landscape_features.py:56`, `aad/meta_learner.py:96`, `aad/llm_designer.py:82` | C3, C4 | fix in Phase 2 |
| D6 | No evaluation budget: `ea` spends population × (generations + 1) and mealpy whatever its `epoch` and `pop_size` imply, so candidates spend different amounts | `aad/evolutionary_algorithm.py:143`, `:170`, `aad/mealpy_algorithms.py:233` | C3 | fix in Phase 2 |
| D7 | Feature sampling evaluates each sample point twice, and the gradient step adds 50 × d more, so the default 300 points cost 600 + 50 × d evaluations. Three names mislead: `fitness_variance` is std/\|mean\|, `modality` is a skewness, and `ruggedness` compares independent random points in arbitrary order. Several features change with the scale of f | `aad/landscape_features.py:57`, `:88`, `:69`, `:105`, `:119` | C4 | leave: the study uses pflacco (Phase 4); fix only if Phase 4 keeps these features |
| D8 | `EA_Designer` gives a candidate the surrogate rejects its prediction × 1.05 as its score. That score enters selection and the surrogate's training data, and the returned best may be a prediction instead of a measured result. For a negative prediction the 5% makes it look better. The feature vector is the same for every candidate of one problem, so features cannot change the choice | `aad/meta_learner.py:232`, `:241`, `:179` | C4 | Phase 7 |
| D9 | `predict_with_uncertainty` returns the mean in the original units and the spread in standardised units. The GP has no `random_state`, so its restarts depend on the global random state; the RF uses `n_jobs=-1` | `aad/surrogate_model.py:134`, `:54`, `:50` | C4 | Phase 7 (the uncertainty is needed for RQ2b) |
| D10 | `EvaluationFramework` reports and ranks by the best run of several (`best_fitness` is the minimum), which rewards a lucky run. How a failed run (an exception or NaN) is handled is not known | `aad/evaluation.py:99`, `:143` | C4 | fix in Phase 2 (failure recording and scoring) |
| D11 | Multi-objective problems (ZDT1, ZDT2) are optimised as f1 + f2, and `pareto_*.png` plots 200 random points instead of the EA's result | `aad/evolutionary_algorithm.py:107`, `aad/mealpy_algorithms.py:240`, `experiment_runner.py:270` | reading | leave: the study is single-objective; revisit in Phase 11 |
| D12 | The home-made BBOB functions have never been checked against the official definitions. A quick check found F19 returning a value below its official minimum of 0 | `aad/problems.py:274` onward | C2 | leave: the study uses ioh's MA-BBOB (Phase 2); keep these only for tests and demos |
| D13 | Tests: `test_gp_fit_predict` uses unseeded random data; no test runs the 24 BBOB classes, the 24 mealpy algorithms or `build_algorithm` | `tests/test_aad.py:312` | C5 | Phase 2: each fix comes with a test |
| D14 | `experiment_runner.py` uses 2 runs per evaluation, no seeds and unequal budgets, and its results come from PSO (D1) | `experiment_runner.py:100` | reading | Phase 11 rebuilds the runner |

Not a defect, noted for Phase 2: `aad/evaluation.py:26` imports
`EvolutionaryAlgorithm` without using it.

## Outputs

| File | What it is |
|---|---|
| `results/phase0/environment/` | Python version, `pip freeze` of both venvs (done) |
| `results/phase0/pytest_baseline.txt` | baseline test run (done) |
| `scripts/phase0_health_check.py` | the health-check script |
| `results/phase0/health_report.txt`, `.json` | results of C1 to C5 |
| `results/phase0/algorithm_runs.csv` | one row per C3 run |
| `documents/context/phase0_context.md` | what was found, the README differences (C6) and the decision for each defect |

## Done when

Every module imports, every algorithm has a recorded run, every defect has a
decision in the context document, and every new result file is listed in
`results/README.md`.

## Stop points

| Step | Ask before going on? |
|---|---|
| Approve this plan | yes |
| Write and run the health check | no (minutes) |
| Decide each defect: fix now, fix in a later phase, or leave | yes |
| Close Phase 0: final context entry, update `CURRENT_STATE.md`, commit and push | yes |
