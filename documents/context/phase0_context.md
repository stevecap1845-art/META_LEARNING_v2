# Phase 0 context: environment, repository and code health

Plan: [../planning/phase0/phase0_plan.md](../planning/phase0/phase0_plan.md).
Results: [`results/phase0/`](../../results/phase0/).
Status: done on 2026-11-20. Part A (environment) and Part B (health check)
both ran, and every defect has a decision (§6).

## 1. What this code is

The folder came from a Google Drive export dated 2026-08-07
(`Meta_Learning-20260807T110346Z-1-001`). On 2026-11-20 it was compared file by
file, ignoring line endings, with the main project's history:

| Compared with | Identical files (of 15 code, test and README files) |
|---|---|
| main project commit `bd71fa0` (2026-09-03, "API key integration and test_runner") | 13 |
| tag `v1-final` (end of round one) | 5 |
| branch `v2` (round two) | 5 |

Two files differ from `bd71fa0`:

- `aad/llm_designer.py` used the older `google.generativeai` client and had an
  API key hard-coded as a default argument (see §3). `bd71fa0` reads the key
  from `.env` and uses `google.genai`.
- `experiment_runner.py` defaults to a smaller meta-search
  (`meta_generations=3` and `meta_population_size=6`, against 5 and 20).

This is the project's starting code, from before any round-one phase, and none
of round one's fixes are in it. Reading the code confirmed two consequences:

- The registry has 24 mealpy algorithms, including `CMA_ES`, `AOA` and `DE`,
  which round one removed because they do not optimise.
- `build_algorithm` falls back to `"pso"` when a configuration has no
  `algorithm` key (`aad/evolutionary_algorithm.py:221`), although its
  docstring says it returns the EA. `EvaluationFramework.evaluate` builds
  through it (`aad/evaluation.py:67`), while `EA_Designer` builds the EA
  directly (`aad/meta_learner.py:118`). In `experiment_runner.py` the
  meta-learner therefore searches EA settings, and the final evaluation of the
  chosen setting runs PSO.

## 2. Environment (Part A), 2026-11-20

| Step | What was done | Evidence |
|---|---|---|
| Git | `git init -b main`, keeping the existing `.gitignore` (which ignored `results/`, `__pycache__/` and venvs at the time); initial commit; remote `git@github.com:stevecap1845-art/META_LEARNING_v2.git`, pushed over SSH. Later the same day the commit messages were edited and the history rewritten, which changed this commit's hash from `79db7fd` to `606e64d` without changing its files | commit `606e64d` |
| Python | The machine's official CPython 3.11.9 (`tags/v3.11.9:de54cf5`, MSC v.1938, 64-bit) copied into `python-3.11.9/`. Its `site-packages` held only pip 24.0 and setuptools 65.5.0, and nothing had to be downloaded or changed on the system | `results/phase0/environment/python_version.txt` |
| Requirement files | `requirements.txt` (59 pins) and `requirements-pflacco.txt` (25 pins) copied from the main project; they replace this repository's old 3-line `requirements.txt` | the files |
| Two venvs | The two files conflict (numpy 2.4.6 vs 1.24.4, pandas 3.0.5 vs 2.0.3, scikit-learn 1.9.0 vs 1.2.2, matplotlib 3.11.1 vs 3.10.9). `.venv` runs the framework and `.venv-pflacco` the pflacco features, both on the project-local 3.11.9 | `pyvenv.cfg` in each |
| Verification | `pip check` is clean in both; `pip freeze` equals the requirement file exactly in both; pflacco's `calculate_ela_meta` imports | `results/phase0/environment/venv_*_freeze.txt` |
| Baseline tests | `pytest tests`: 54 passed. The first run also gave 1 warning, a `ConvergenceWarning` about the GP kernel's length scale in `test_gp_fit_predict`; the re-run after the clean-up described in §4 gave none. The test fits on unseeded random data (`tests/test_aad.py:312`), so the warning depends on the draw. Not fixed: unseeded tests belong to the Phase 0 defect review | `results/phase0/pytest_baseline.txt` |

`python-3.11.9/`, `.venv/` and `.venv-pflacco/` are git-ignored. The plan
gives the commands to rebuild them.

## 3. Security incident: hard-coded API key

`aad/llm_designer.py` had a Google Gemini API key as the default value of
`LLMDesigner.__init__(api_key=...)`. The key went into the first commit and was
pushed to the public GitHub repository on 2026-11-20. The secret scan run
before that commit missed it: its pattern expected `api_key = "..."`, and the
code had a type annotation in between (`api_key: str = "..."`). The key was
found the same day while comparing this code with the main project, then
confirmed with a pattern for the key itself (`AIza…`).

Because the default was a key, every `LLMDesigner()` call was in LLM mode and
tried the API first. That included the 3 tests written for the offline
rule-based mode.

Steps taken on 2026-11-20:

1. The default became `api_key=None`, which is the rule-based mode the
   docstring describes. To use the API, pass a key at run time, for example
   `LLMDesigner(api_key=os.environ["GEMINI_API_KEY"])`. Importing `aad` reads
   no secrets (round two's defect #6 does not apply).
2. `.env` is git-ignored, so a key file copied over from the main project
   cannot be committed.
3. With the user's approval, the single commit was amended and force-pushed.
   The old commit was purged locally (reflog expired, `gc --prune=now`).
   `git grep` over every reachable commit finds no key, and the remote's
   `main` is the new commit `79db7fd` (now `606e64d`, see §2).
4. All 54 tests still pass.

Only the key's owner can finish this: revoke the key in Google AI Studio. It
was public, and GitHub may keep the old commit reachable by its hash for a
while, so rewriting history does not make the key safe again.

For later phases: scan for the secret's value pattern (for example
`AIza[0-9A-Za-z_-]{20,}`) instead of the way it is assigned.

## 4. Repository layout, 2026-11-20

- `documents/` has `planning/`, `context/` and `history/`, an index, and
  `CURRENT_STATE.md`, which is updated after every session.
- `results/` has one folder per phase, a manifest (`results/README.md`), and
  `inherited/` for files that arrived with the code.
- `results/` is tracked in git (it used to be ignored), apart from the
  runner's scratch output.
- `experiment_runner.py` writes to `results/experiment_runner/`, which git
  ignores, instead of the root of `results/`.

Later the same day the code changes were cut back to what the task needed: a
`LLMDesigner.from_env()` helper, `.env.example` and several `.gitignore`
patterns for files this repository never writes were removed. Tests: 54
passed.

### The inherited result files

The 60 files that were in `results/` were moved unchanged to
`results/inherited/snapshot_2026-08-07/`. They are not evidence for any phase:

- the JSON covers the 24 BBOB functions, but the PNGs also cover Sphere,
  Rastrigin, Rosenbrock, Ackley and ZDT1, so they come from at least two runs;
- the configurations in the JSON have no `algorithm` key, so by §1 every
  "final evaluation" and "LLM designer" metric in it comes from a PSO run,
  whatever EA setting it is listed under;
- no seeds were recorded, and the exact code that produced them is unknown.

## 5. Health check (Part B), 2026-11-20

The plan's Part B was rewritten from this repository's code and approved the
same day. `scripts/phase0_health_check.py` ran checks C1 to C5 in `.venv` in
under a minute (seed 0, on commit `79db7fd`, now `606e64d`, plus the
uncommitted changes of this session). It changed nothing in `aad/`.

Result: 70 checks passed, 72 were flagged, none failed
(`results/phase0/health_report.txt`). Most flags are expected: 48 of them are
the 24 mealpy algorithms on 2 problems, which do not repeat with the same seed.

| Check | Outcome |
|---|---|
| C1 imports and packages | All 13 modules import in a fresh process; the 53 names in `aad.__all__` exist. One package is missing: `google.generativeai`, imported at `aad/llm_designer.py:117`, is not installed |
| C2 wiring | The 24 mealpy algorithms are all reachable and the three name lists agree. A configuration with no `algorithm` key builds PSO. `EA_Designer` ran the EA for all 8 candidates, although every one named a mealpy algorithm, and returned `CMA_ES` as its best. All 30 problems give finite values and the 9 features are finite for all 28 single-objective problems. 9 of the 24 home-made BBOB functions differ from ioh's reference (D12 below) |
| C3 algorithm runs | All 64 algorithm-problem pairs ran without an error and gave finite values. The `ea` repeats exactly with the same seed and spends exactly population × (generations + 1) = 220 evaluations. None of the 24 mealpy algorithms repeats. Most spend 220 evaluations, but ABC spends 420, EO 230, SA 30, and HHO between 376 and 394, a different number each run. On both problems HHO reported a best value worse than the best point it had evaluated (on F1, 13.38 against 12.80) (`results/phase0/algorithm_runs.csv`) |
| C4 components | See D4, D7 to D10 and D14 below. The four plots are written |
| C5 tests | 54 passed in each of 3 runs. The GP `ConvergenceWarning` from the unseeded `test_gp_fit_predict` appeared in runs 1 and 2 but not in run 3 (`results/phase0/pytest_runs.txt`). 30 of the 53 public names are never mentioned in the tests: `OptimizationProblem`, the 24 BBOB classes, `build_algorithm`, `MealpyAlgorithm`, `MEALPY_REGISTRY`, `MEALPY_ALGORITHM_KEYS` and `EXTENDED_CONFIG_SPACE` |

## 6. Defects and decisions

Decision by the project owner on 2026-11-20: nothing is fixed in Phase 0. Each
defect is fixed when the work first uses that part of the code, or when the
phase that owns it starts. The phase named below is where that happens.

| # | Defect | Status after the health check | Fix in |
|---|---|---|---|
| D1 | A configuration with no `algorithm` key builds PSO. In `run_experiment`, both the LLM designer's configuration and the final evaluation ran as PSO (pop 20 for 50 epochs, and pop 50 for 200 epochs) | confirmed (C2, C4) | Phase 2 |
| D2 | `EA_Designer` always runs the EA, whatever the `algorithm` key says | confirmed (C2): 8 of 8 candidates | Phase 2 |
| D3 | The helpers, `EA_Designer` and `LLMDesigner` default to `EA_CONFIG_SPACE`, which has no `algorithm` key, so their configurations reach D1 | confirmed (C4: the rule-based proposal builds PSO) | Phase 2 |
| D4 | LLM mode imports `google.generativeai`, which is not installed, so every LLM call returns a rule-based pick with only a printed message. The prompt contains the problem's name. Answers are checked for their keys, not their values | confirmed (C1, C4); the value check was confirmed by reading | Phase 8 |
| D5 | No seeds. With the same global seeds the `ea` repeats exactly, but none of the 24 mealpy algorithms does, because mealpy's `solve` gets no seed | confirmed (C3) | Phase 2 |
| D6 | No evaluation budget: with the same population and generations, the algorithms spend between 30 (SA) and 420 (ABC) evaluations | confirmed (C3) | Phase 2 |
| D7 | Feature sampling evaluates each point twice: 850 evaluations for 300 points in dimension 5, against 550 if each were evaluated once. Three feature names mislead, and several features depend on the scale of f | confirmed (C4); the names by reading | Phase 4, only if the home-made features are used |
| D8 | In a tiny `EA_Designer` run with the surrogate on, 12 of 18 candidates were scored by the surrogate's prediction × 1.05 instead of being run. Those scores entered selection and the surrogate's training data. The returned best happened to be a measured result in this run. The feature vector is the same for every candidate of one problem | confirmed (C4); the feature vector by reading | Phase 7 |
| D9 | `predict_with_uncertainty` gives the mean in the units of y but the spread in standardised units: for the RF, 0.45 is really 335 in the units of y. RF predictions differ by up to 2.3e-13 (on values near 1,928) between two fits, and even when one model predicts twice, because of `n_jobs=-1`; with `n_jobs=1` they are identical. The GP gave identical fits in this test, so its missing `random_state` caused no visible difference | confirmed (C4) for the units and the RF; not seen for the GP | Phase 7 |
| D10 | `EvaluationFramework` reports the best of its runs as `best_fitness`. A problem that always returns NaN gives `best_fitness = nan` with no error or failure flag, and `compare_configs` still ranks it. An exception in one run stops the whole evaluation | confirmed (C4) | Phase 2 |
| D11 | ZDT1 and ZDT2 are optimised as f1 + f2, and `pareto_*.png` plots random points | by reading; not run, since the study is single-objective | Phase 11, if the runner keeps ZDT |
| D12 | 9 of the 24 home-made BBOB functions differ from ioh's reference implementation. F3, F6, F13 and F15 are 3.5e9 to 1.3e10 times larger at random points, F7 1.8e5 times and F17 27 times. F5, F19 and F20 go below 0, which the official functions never do, and F20 is also about 18,000 times smaller. Reading the code points to one cause for the scale: `_lam10` (`aad/problems.py:307`) is the ellipsoid's 10^(6·i/(n−1)), but F3, F6, F7, F13, F15 and F17 use it where the official definition has Λ^10, whose largest entry is √10. The C3 runs on F15 therefore used a mis-scaled function | confirmed (C2) | Phase 2: the study uses ioh's MA-BBOB, and these classes stay only for tests and demos |
| D13 | Tests: `test_gp_fit_predict` is unseeded, and 30 of 53 public names have no test | confirmed (C5) | Phase 2: each fix comes with a test |
| D14 | `experiment_runner.py` uses 2 runs per evaluation, no seeds and unequal budgets, and its evaluations run PSO (D1) | confirmed (C4) | Phase 11 |
| D15 | New: an algorithm's own reported best can be worse than the best point it evaluated (HHO, on both problems). Performance should be measured by counting evaluations and recording the best value seen, not by trusting the algorithm's report | confirmed (C3) | Phase 2 |

Not a defect, noted for Phase 2: `aad/evaluation.py:26` imports
`EvolutionaryAlgorithm` without using it.

## 7. README compared with the code (C6, by reading)

The root `README.md` is not edited. Where it and the code disagree:

1. The LLM section says to pass an OpenAI key and `model="gpt-4"`. The code
   uses Gemini through a client that is not installed (D4), so that example
   falls back to rule-based picks.
2. `python experiment_runner.py` is said to run 5 problems (Sphere to ZDT1)
   and write a ZDT1 Pareto plot. The code runs the 24 BBOB functions in
   dimension 10, with the classic problems commented out, so no Pareto plot is
   made.
3. Results are said to go to `results/`. Since 2026-11-20 the runner writes
   to `results/experiment_runner/`.
4. The minimal example passes `EA_Designer`'s best configuration to
   `EvaluationFramework`, which runs PSO instead of the designed EA (D1, D3).
5. The overview says the meta-learner learns from landscape features. The
   features are computed, but they are the same for every candidate of one
   problem, so they cannot change the choice (D8).
6. The repository tree leaves out `mealpy_algorithms.py`, `tests/`,
   `scripts/`, `documents/` and `requirements-pflacco.txt`. The component list
   leaves out the 24 BBOB classes, the 24 mealpy algorithms and
   `EXTENDED_CONFIG_SPACE`.
7. The dependency list (Python 3.8 or later, NumPy, scikit-learn, Matplotlib,
   optional `openai`) leaves out mealpy, which the code needs. The pinned
   environment uses Python 3.11.9 and a second environment for pflacco.
8. Small differences in printed output: the code prints `[OK]` where the
   sample output shows a tick, and prints an "LLM designer" line that the
   sample banner does not have.

The README is right that a custom problem needs only `evaluate`, `bounds` and
`is_multiobjective`.

## 8. Open items

| Item | Next action |
|---|---|
| Revoke the leaked key | owner |
| Defects D1 to D15 | fixed in the phase named in §6 |
