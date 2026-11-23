# Phase 0 context: environment, repository and code health

Plan: [../planning/phase0/phase0_plan.md](../planning/phase0/phase0_plan.md).
Results: [`results/phase0/`](../../results/phase0/).
Status: closed on 2026-11-23. Part A (environment), Part B (health check) and
the follow-up audit (§8) ran on 2026-11-20, and every defect has a decision
(§6).

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
| D12 | 9 of the 24 home-made BBOB functions differ from ioh's reference implementation. F3, F6, F13 and F15 are 3.5e9 to 1.3e10 times larger at random points, F7 1.8e5 times and F17 27 times. F5, F19 and F20 go below 0, which the official functions never do, and F20 is also about 18,000 times smaller. Reading the code points to one cause for the scale: `_lam10` (`aad/problems.py:307`) is the ellipsoid's 10^(6·i/(n−1)), but F3, F6, F7, F13, F15 and F17 use it where the official definition has Λ^10, whose largest entry is √10. The C3 runs on F15 therefore used a mis-scaled function | confirmed (C2); the follow-up audit (§8.1) checked all 24: 16 are wrong, 2 differ by a constant, 6 are correct | Phase 2: the study uses ioh's MA-BBOB, and these classes stay only for tests and demos |
| D13 | Tests: `test_gp_fit_predict` is unseeded, and 30 of 53 public names have no test | confirmed (C5) | Phase 2: each fix comes with a test |
| D14 | `experiment_runner.py` uses 2 runs per evaluation, no seeds and unequal budgets, and its evaluations run PSO (D1) | confirmed (C4) | Phase 11 |
| D15 | New: an algorithm's own reported best can be worse than the best point it evaluated (HHO, on both problems). Performance should be measured by counting evaluations and recording the best value seen, not by trusting the algorithm's report | confirmed (C3) | Phase 2 |
| D16 | From the follow-up audit (§8.2): no algorithm is tuned, and every mealpy parameter except population and generations stays at mealpy's default. DE's default F = 0.1 makes DE no better than random search on the sphere, while F = 0.5 puts it among the best. SA ignores the population it is given | confirmed (audit part 2) | Phase 1 decides the fixed settings of each candidate, Phase 2 passes them |
| D17 | From the follow-up audit (§8.2): the algorithms spend different numbers of evaluations per generation (ABC 2 populations, HHO 1.7 to 1.9 and varying, EO 1 population plus 1, SA 1 evaluation), and GWO, WOA, HHO, MVO, SCA, EO and AOA plan their behaviour on the generation count. A fixed budget has to set each algorithm's generation count from the budget; `solve()` takes a seed and a maximum number of evaluations | confirmed (audit part 2) | Phase 2, together with D5 and D6 |
| D18 | From the follow-up audit (§8.2): at 5,000 evaluations in dimension 5, AO and AOA are worse than random search on the sphere, the rotated ellipsoid and the rotated Rastrigin, and mealpy's CMA_ES on the last two. BBO and HHO are worse on the ellipsoid and SA on Rastrigin | confirmed (audit part 2, 5 seeds) | Phase 3 screening, before the candidate list is fixed |

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

## 8. Follow-up audit, 2026-11-20

After Phase 0 the owner asked three things: do the 24 BBOB functions and the
algorithms have correct parameters, are the algorithms tuned, and does
`experiment_runner.py` call them properly? `scripts/phase0_audit.py` ran the
checks, and its output is in `results/phase0/audit_*`. Nothing in `aad/` was
changed. As decided in §6, each finding is fixed in the phase that first uses
that code.

### 8.1 The 24 BBOB functions

How they were checked:

- Seven functions have no rotation in the official definition (F1 to F5, F8
  and F20). Each class was given ioh's optimum for instance 1 and compared
  with ioh at 200 random points in dimensions 5 and 10. Where a class
  differed, the official definition was coded on top of the class's own
  helper transformations. For F3, F4, F5 and F20 it matched ioh to about
  1e-15, which confirms both the reading of the definition and the helpers.
- ioh does not expose its rotation matrices. The 15 rotated functions with a
  single formula were therefore compared with the official definition built
  from the class's own optimum and rotations. As a check on that reference,
  its median value over 10 instances overlaps ioh's range over 10 instances
  for all 15 functions.
- F21 and F22 draw their peaks at random, so their parameters were compared
  by reading.

Λ^α below is the official diagonal scaling α^(i/(2(n−1))) for i = 0 to n−1,
so Λ^10 runs from 1 to √10 ≈ 3.16. Several classes use `_lam10`
(`aad/problems.py:307`) as Λ^10, or its square root. `_lam10` holds the F2
ellipsoid weights and runs from 1 to 10^6.

| F | Verdict | What differs from the definition | Evidence in dimension 10 (`results/phase0/audit_bbob.csv`) |
|---|---|---|---|
| 1 | correct | | matches ioh on the same optimum (largest relative difference 3e-16) |
| 2 | correct | | matches ioh (7e-16) |
| 3 | wrong | `_lam10` used as Λ^10 | median value 1.1e10 times ioh's |
| 4 | wrong | Büche scaling: coordinates 1, 3, 5 and so on get 1 instead of √10^(i/(n−1)), and coordinates 0, 2, 4 and so on miss the factor 10 for positive values | differs from ioh by up to 0.98 on the same optimum |
| 5 | constant offset | the constant 5·Σ\|s_i\| is missing | always 204.3 below the definition, so f(xopt) is negative |
| 6 | wrong | `_lam10` used as Λ^10 | differs from the definition by up to 5.5e10 |
| 7 | wrong | Λ^10 replaced by 10^(3i/(n−1)); the rotation Q after rounding is missing | up to 5.6e5 |
| 8 | correct formula | the class draws xopt from [−4, 4]; the definition uses [−3, 3] | matches ioh on the same optimum (5e-16) |
| 9 | correct | | 0 |
| 10 | wrong | the rotation is applied after T_osz instead of before | up to 0.37 |
| 11 | wrong | the same order error as F10 | up to 345 |
| 12 | correct | | 4e-16 |
| 13 | wrong | `_lam10` used as Λ^10 | up to 4.9e8 |
| 14 | correct | | 0 |
| 15 | wrong | `_lam10` used as Λ^10, and T_osz applied before the first rotation | up to 7.1e10 |
| 16 | wrong | Λ^(1/100) is 10^(−2i/(n−1)) instead of 10^(−i/(n−1)) | up to 3.3 |
| 17 | wrong | Λ^10 replaced by 10^(3i/(n−1)); penalty 10/n instead of 10 | up to 130 |
| 18 | wrong | Λ^1000 is 1000^(i/(n−1)) instead of 1000^(i/(2(n−1))); penalty 10/n instead of 10 | up to 30 |
| 19 | constant offset | adds 10/(n−1) instead of 10 | always 8.89 below the definition, so its minimum is −8.89 instead of 0 |
| 20 | wrong | xopt is not ±4.2096874633/2; Λ^10 is missing; the factor 100 covers only part of z; the sum lacks its 1/100; the penalty uses x/100 + 0.5 instead of z/100 | differs from ioh by up to 1.0 on the same optimum; median value 0.0002 times ioh's |
| 21 | wrong, by reading | peak heights random instead of evenly spaced from 1.1 to 9.1; condition numbers 1000^U(0,1) instead of drawn from 1000^(2j/99); the Λ exponent doubled and the α^(−1/4) normalisation missing; a separate rotation for each peak instead of one shared rotation | median value 1.05 times ioh's, so the errors do not show in scale |
| 22 | wrong, by reading | as F21, and the global peak's condition number is 1000 instead of 1000²; peaks in [−5, 5] instead of [−4.9, 4.9] | median value 1.02 times ioh's |
| 23 | wrong | Λ^100 replaced by 10^(3i/(n−1)) | up to 3.5 |
| 24 | wrong | Q and Λ^100 missing from z; the factor s missing on the second sphere; the penalty lacks its 10^4; the stored xopt is 2.5 times the signs instead of 1.25 times, so the optimum is not at xopt | up to 0.69 |

Six classes match the definition (F1, F2, F8, F9, F12 and F14), although F8
draws its optimum from a wider box. Two differ only by a constant (F5 and
F19), and 16 are wrong. This completes D12. The study uses ioh's functions,
so the decision stands.

### 8.2 Algorithm settings and tuning

No algorithm is tuned. `MealpyAlgorithm` passes mealpy only `epoch` (from
`max_generations`) and `pop_size` (from `population_size`)
(`aad/mealpy_algorithms.py:233`). Every other parameter stays at mealpy's
default, no seed is passed, and there is no evaluation budget. The only
settings that vary are population size and the number of generations, plus
the three operators of the built-in EA.

Three of mealpy's defaults (`results/phase0/audit_algorithm_defaults.csv`)
stand out:

- DE: the scale factor F (`wf`) is 0.1, with CR 0.9 and the DE/rand/1
  mutation. F is usually 0.5 or more (Storn and Price 1997). With F = 0.1
  the mutation steps are small and the population can converge early.
- PSO: inertia w = 0.4 with c1 = c2 = 2.05. The usual settings are the
  constriction values w = 0.7298 with c1 = c2 = 1.49618 (Clerc and Kennedy
  2002), or w falling from 0.9 to 0.4 over the run.
- SA works on a single solution, and mealpy's own docstring says the
  population size does not matter (`mealpy/physics_based/SA.py:6`). The
  framework still passes 20 to 100, which only adds evaluations at the start.

Evaluations per generation through the framework
(`results/phase0/audit_evaluations_per_epoch.csv`): the EA and 20 of the 24
mealpy algorithms spend one population of evaluations at the start and one per
generation, as the framework assumes. ABC spends two populations per
generation, EO one population plus 1, HHO 1.7 to 1.9 populations (a
different number each run), and SA 1 evaluation whatever the population. At population
20 and 20 generations that is 420 evaluations for most algorithms, 820 for
ABC, 440 for EO, 754 for HHO in one run, and 40 for SA.

Many mealpy algorithms also plan their behaviour on the number of generations
they are given. GWO, WOA, HHO, MVO, SCA, EO and AOA all compute a coefficient
from `epoch / self.epoch` (for example `mealpy/swarm_based/GWO.py:63`). So a
fixed evaluation budget cannot be imposed by giving every algorithm many
generations and stopping it early: each algorithm's generation count has to
be set from the budget. mealpy's `solve()` already takes a `seed` and a
`termination` with a maximum number of evaluations.

A quick equal-budget check (`results/phase0/audit_equal_budget_runs.csv`)
shows whether each algorithm works with these settings. Every candidate got
5,000 evaluations (1,000 × d) on three of ioh's functions in dimension 5: the
sphere F1, the rotated ellipsoid F10 and the rotated Rastrigin F15, with 5
seeds each and population 20. mealpy was called directly with a seed and with
a generation count set from the budget. Random search with the same budget is
the bar. Median best f − fopt, where 0 means the gap fell below floating-point
resolution:

| Candidate | F1 | F10 | F15 |
|---|---|---|---|
| random search | 1.88 | 5,570 | 29.3 |
| AO | 5.31 | 13,100 | 36 |
| AOA | 8.76 | 127,000 | 125 |
| CMA_ES | 1.48 | 18,000 | 78.9 |
| DE, mealpy default (F = 0.1) | 2.13 | 5,470 | 25.2 |
| DE with F = 0.5 | 0 | 12.7 | 2.01 |
| PSO, mealpy default | 0 | 8.84 | 6.96 |
| PSO with constriction values | 1.3e-4 | 1,650 | 22.1 |
| SHADE | 0 | 1.1e-13 | 2.31 |
| EA with roulette, SBX and polynomial mutation (best of the 8 EA variants on F10 and F15) | 7.0e-6 | 108 | 8.97 |

- AO and AOA are worse than random search on all three functions. mealpy's
  CMA_ES is worse on F10 and F15 and barely better on the sphere, where a
  working CMA-ES gets close to zero with this budget. All three need a check
  in Phase 3 before they join the candidate list. One possible cause, a bias
  toward the centre of the search space, can be tested there by moving the
  optimum.
- DE with mealpy's default F = 0.1 is no better than random search on the
  sphere. With F = 0.5 it is among the best, so the problem is the default,
  not DE.
- PSO's unusual defaults work well here, better than the constriction
  values, so they need no change.
- BBO and HHO are worse than random search on F10, and SA on F15. HHO used
  4,864 to 4,996 evaluations, because its cost per generation varies.
- All 8 EA variants beat random search on all three functions. Polynomial
  mutation beats Gaussian mutation on F1 and F10 in every pairing.

Five seeds on three functions is a sanity check, not the Phase 3 screening.

The EA's operators (`aad/ea_components.py`) are implemented correctly, with
textbook values: tournament size 3; SBX with η = 15, crossover probability
0.9 and each variable crossed with probability 0.5; uniform crossover;
polynomial mutation with η = 20 and probability 1/n. Three properties are
worth knowing for the screening in Phase 3. Gaussian mutation uses a fixed
step of 10% of the range with no adaptation, which limits how precisely the
EA can close in on an optimum. Roulette selection weights each individual by
the worst fitness minus its own, so one very bad individual makes the choice
nearly uniform. SBX always gives the first child the lower value, where most
implementations swap the children at random.

### 8.3 What `experiment_runner.py` runs

`run_experiment` was run on each of its 24 default problems, with the
meta-search cut to 2 configurations, 1 generation and 1 run so that it
finishes in minutes (`results/phase0/audit_runner_trace.csv`). The cut
changes how many candidates are tried, not which code runs.

- All 24 BBOB problems are built in dimension 10 and run to the end without
  an error. The runner never passes a seed, so every function is the single
  instance given by the default seed 42 (`aad/problems.py:292`).
- The meta-search (`EA_Designer`) ran the built-in EA for every candidate.
  Its configurations come from `EA_CONFIG_SPACE`, which has no `algorithm`
  key, so none of the 24 mealpy algorithms is ever searched.
- The rule-based LLM designer proposed the same EA configuration for all 24
  problems (population 50, SBX, Gaussian mutation, 100 generations, and a
  random choice of selection), because the descriptions it reads differ only
  in the problem's name. That configuration was then evaluated as PSO with
  population 50 for 100 generations.
- The final evaluation of the configuration the meta-search found also ran
  PSO, with that configuration's population and generation count, instead of
  the EA it describes.

So of the 25 algorithms, the main program runs two: the EA inside the
meta-search, and PSO, by accident through D1, for both evaluations whose
numbers it reports. The other 23 never run. This confirms D1, D2, D3 and D14
on the full problem list and needs no new defect.

## 9. Open items

| Item | Next action |
|---|---|
| Revoke the leaked key | owner |
| Defects D1 to D18 | fixed in the phase named in §6 |

## 10. Closing, 2026-11-23

Nothing was rerun. The project plan now marks Phase 0's tasks done, and the
Phase 0 plan has a dated note above its original text. The audit script and
its six result files were committed with these notes. On the machine that ran
it, the script was last changed at 23:09:32 on 2026-11-20 and the result files
were written from 23:09:50 to 23:15:58, so the committed script is the one
that produced them, in about six minutes. The open items in §9 carry over;
Phase 1 starts with decision R2 in `CURRENT_STATE.md`.
