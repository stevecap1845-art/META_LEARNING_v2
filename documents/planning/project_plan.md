# Project plan

Written 2026-11-20 from [../research/research_gap.md](../research/research_gap.md).
Keys in brackets point to [../research/references.bib](../research/references.bib).
The plan before the restart is kept in
[../archive/project_plan_before_restart.md](../archive/project_plan_before_restart.md)
and is not used.

## Goal

Meta-learner or LLM? Given an unseen continuous optimisation problem, choose an
algorithm and its settings from the problem's pflacco landscape features, once
with a meta-learner trained across many problems and once with an LLM given
the same features. Compare the two at an equal budget, test whether combining
them beats both, and find out where each one wins.

| # | Research question |
|---|---|
| RQ1 | On unseen problems and at an equal budget, how does a pflacco-based meta-learner compare with an LLM given the same features? |
| RQ2 | Does combining them beat both: the LLM's suggestions scored by the surrogate, or the surrogate's uncertainty deciding which recommendation to trust? |
| RQ3 | On which kinds of problems, and in which dimensions, does each one win? |

## How the working plan maps onto the phases

| Step of the working plan | Phase |
|---|---|
| 1. Extract landscape features with pflacco | 4 |
| 2. Run algorithm + setting combinations several times and find the best | 3 (pilot), 5 (full dataset), 6 (best per problem) |
| 3. Build the surrogate and the meta-learner side by side | 7 |
| 4. Give the same features to an LLM and get its recommendation | 8 |
| 5. Compare the two and choose the better one | 9 (on training data), 10 (on unseen problems) |

## Phases at a glance

| Phase | Name | Question it answers | Depends on | Effort (rough) |
|---|---|---|---|---|
| 0 | Environment and code health | Does the code run, and what is broken? | none | 1 to 2 days (setup done) |
| 1 | Experimental rules | What are the rules every later phase follows? | 0 | 1 to 2 days |
| 2 | Code foundations | Can every candidate run fairly, seeded and within budget? | 1 | 1 to 2 weeks |
| 3 | Screening and timing pilot | Which candidates work, and what does the full study cost? | 2 | 3 to 5 days |
| 4 | Landscape features | Are the pflacco features stable and affordable? | 2 | 3 to 5 days |
| 5 | Performance dataset | How does each candidate do on each problem? | 3, 4 | 1 to 2 weeks, mostly compute |
| 6 | Baselines | What is the bar to beat? | 5 | 2 to 3 days |
| 7 | Surrogate and meta-learner | How well does the meta-learner choose on problems it has not seen? | 5, 6 | 1 to 2 weeks |
| 8 | LLM recommender | How well does the LLM choose from features alone? | 4, 6 | 1 to 2 weeks |
| 9 | Combining the two | Which combination works best on training data? | 7, 8 | 1 week |
| 10 | Main experiment | RQ1 to RQ3 on unseen problems, run once | 9 | 1 week |
| 11 | Real-world check and tool (optional) | Do the findings hold on real problems, and does the runner work end to end? | 10 | 1 to 2 weeks |
| 12 | Write-up | Thesis chapters or paper | 10 | 3 to 6 weeks |

Phases 7 and 8 are independent of each other and can run side by side. The
efforts are guesses for one person working part time; Phase 3 replaces the
compute estimates with measured ones.

```
0 → 1 → 2 → 3 ┐
          └→ 4 ┴→ 5 → 6 ┬→ 7 ┐
                        └→ 8 ┴→ 9 → 10 → 11
                                      └→ 12
```

## How every phase is run

- Before starting, write `planning/phase<N>/phase<N>_plan.md`: the tasks in
  more detail, the decisions needed, and the checks that mark it done.
- While working, keep `context/phase<N>_context.md`: what was done, found and
  decided, with dates and commits.
- Results go only into `results/phase<N>/`, and each file is listed in
  `results/README.md`.
- A phase is done when every item under "Done when" holds. Then update
  `CURRENT_STATE.md`, commit and push.
- Seeds everywhere. A failed run is recorded as a failure, never silently
  replaced.
- The test problems built in Phase 5 are not looked at until Phase 10.

## Phase 0: Environment and code health

Show that the environment can be rebuilt and find out what in the code is
broken, before any research. Setup is done (see
[../context/phase0_context.md](../context/phase0_context.md)); the health check
is not.

Tasks:
1. Done: Python 3.11.9 in the project folder, `.venv` and `.venv-pflacco` from
   the pinned files, git and GitHub, baseline tests (54 pass).
2. Done 2026-11-20: Part B of `planning/phase0/phase0_plan.md` rewritten from
   this repository's code, with a defect register (D1 to D14), and run. The
   defects (D1 to D15 after the run) and the phase that fixes each are in the
   Phase 0 context document, §6.
3. Import every module; run every algorithm on a tiny problem twice with the
   same seed and check it finishes, gives a finite result, repeats exactly
   and stays within its budget.
4. List every defect found, including the four known ones in
   `CURRENT_STATE.md`, and decide for each: fix in Phase 2, or leave.

Outputs: `results/phase0/health_report.txt`, a defect list with decisions in
the Phase 0 context document.

Done when: every module imports, every algorithm has been run, and every
defect has a decision.

## Phase 1: Experimental rules

Fix the rules before any data exists, so that no choice is made after seeing
results. This phase is a decision document, with no code.

Decisions, with a recommendation for each:

| # | Decision | Recommendation |
|---|---|---|
| 1 | Candidates | The 96 distinct candidates under a fixed budget: 24 `ea` operator settings and 24 mealpy algorithms × 3 population sizes (research_gap.md §7) |
| 2 | Budget per run | A fixed number of function evaluations that grows with dimension, for example 1,000 × d, confirmed after the Phase 3 timing pilot |
| 3 | Dimensions | 5 and 10 first; add 20 only if Phase 3 shows there is time |
| 4 | Problems | MA-BBOB (`ioh.problem.ManyAffine`) for training and test [vermetten2023mabbob, dietrich2024training] |
| 5 | Train/test split | By problem family, so that no test family is seen in training [petelin2025pitfalls]. How a family is defined (for example, every combination whose largest weight is on a held-out BBOB function) is decided here |
| 6 | Runs per candidate and problem | Set from the run-to-run variance measured in Phase 3, more for test than for training |
| 7 | Seeds | Separate, recorded seed ranges for problems, features, runs and LLM calls, checked so they never overlap |
| 8 | Features | pflacco feature groups and a fixed Sobol sample size, for example 50 × d points [renau2020sampling]; the sample counts toward the budget |
| 9 | Performance measure | Scale-free: rank among candidates, or the share of the SBS-to-VBS gap closed |
| 10 | Statistics | Per-function means as the unit; Wilcoxon signed-rank; Holm correction for multiple tests; the Phase 10 test pre-registered |
| 11 | LLM | Provider and model (Gemini and OpenAI clients are both pinned), temperature 0, a fixed number of repeats per question, every call stored |

Outputs: `planning/phase1/rules.md`.

Done when: every decision above has an answer and the rules file is committed.

## Phase 2: Code foundations

Make the code able to run the study fairly. Every change comes with a test.

Tasks:
1. Fix the defects that Phase 0 sent here, starting with the PSO fallback in
   `build_algorithm` (`aad/evolutionary_algorithm.py:221`).
2. A fixed evaluation budget for every candidate, `ea` and mealpy alike, with
   a check that counts real evaluations.
3. Seeds passed to every algorithm, so that the same seed gives the same
   result.
4. The candidate list from Phase 1 as one module that every later phase
   imports.
5. A seeded problem generator for MA-BBOB families, with the train/test split
   from Phase 1.
6. A bridge to `.venv-pflacco`: run pflacco there and write the features to a
   file the main environment reads.
7. Failed runs recorded as failures (today a failure becomes 1e12 with no
   warning).
8. Scoring helpers for the Phase 1 performance measure.

Outputs: code changes and tests, `results/phase2/test_report.txt`.

Done when: all tests pass, and every candidate runs on a tiny problem within
budget and repeats exactly with the same seed.

## Phase 3: Screening and timing pilot

Find out which candidates are worth keeping and what the full study will cost,
before spending the compute.

Tasks:
1. Run every candidate on a small pilot set (for example the 24 plain BBOB
   functions in dimension 5) with a few seeds.
2. Drop candidates that crash or do not improve on a random search at the same
   budget. Each one dropped is listed with its evidence.
3. Measure the time per run and the spread of results between seeds.
4. From those, set the number of runs (Phase 1, decision 6) and estimate the
   compute for Phase 5. Shrink the problem set or the dimensions if it does
   not fit.

Outputs: `results/phase3/screening.json`, a timing table, a cost estimate,
the final candidate list.

Done when: the candidate list is final and the Phase 5 cost fits the time
available.

## Phase 4: Landscape features

Compute pflacco features for every training and test problem, and check that
they are stable and affordable.

Tasks:
1. Compute the Phase 1 feature groups from the fixed Sobol sample for every
   problem.
2. Recompute them with several sample seeds and measure how much each feature
   moves. Drop features that are unstable, constant or often missing.
3. Record each feature group's cost in function evaluations.

Outputs: `results/phase4/features_train.csv`, `results/phase4/features_test.csv`,
a stability table.

Done when: every problem has a complete feature row, and the kept features
and their cost are listed.

## Phase 5: Performance dataset

Step 2 of the working plan at full scale: run every candidate on every problem
several times. This dataset feeds every later phase.

Tasks:
1. A runner that runs in parallel, writes each result as soon as it finishes,
   and resumes after an interruption.
2. Build the training set: every candidate × every training problem × the
   Phase 1 number of runs.
3. Build the test set the same way, then leave it unopened until Phase 10.
4. Integrity checks: no missing cells, every failure recorded, seeds as
   planned.

Outputs: `results/phase5/performance_train.json`,
`results/phase5/performance_test.json`, an integrity report.

Done when: both sets are complete and pass the integrity checks.

## Phase 6: Baselines

Set the bar the meta-learner and the LLM have to beat, on training data only.

Tasks:
1. SBS: the single candidate that is best on average.
2. VBS: the best candidate for each problem. It is the ceiling, and it is what
   step 2 of the working plan finds when it tries everything.
3. Random choice.
4. The gap between SBS and VBS, overall, by family and by dimension. A small
   gap means there is little to win.
5. Optionally, irace tuned on the training problems [lopezibanez2016irace].

Outputs: `results/phase6/baselines.json` and a short report.

Done when: SBS, VBS and random are computed and the size of the gap is known.

## Phase 7: Surrogate and meta-learner (RQ1)

Step 3 of the working plan. Train a surrogate across problems and use it to
recommend a candidate for problems it has not seen.

Tasks:
1. Train `SurrogateModel` on (features, candidate) → performance, with random
   forest and Gaussian process versions.
2. Evaluate by leaving whole problem families out of training, inside the
   training set only.
3. Check whether the surrogate's uncertainty (`predict_with_uncertainty`) is
   higher where its recommendation is wrong. RQ2b depends on this.
4. Start `EA_Designer` from the trained surrogate and compare two variants: the
   surrogate's top pick directly, and the surrogate plus a short search on the
   problem, with the search cost counted in the budget.
5. Freeze the chosen surrogate and variant.

Outputs: `results/phase7/cv_results.json`, the frozen model, a report.

Done when: one surrogate and one meta-learner variant are chosen on training
data and saved, with the evidence for the choice.

## Phase 8: LLM recommender (RQ1)

Step 4 of the working plan. The LLM recommends a candidate from the feature
values alone.

Tasks:
1. A prompt with the feature values, what each feature measures, the
   candidate list and the budget, and no problem name.
2. Validate each answer against the candidate list. An invalid or failed
   answer is recorded as such, never replaced by a rule-based pick.
3. Store every call: prompt, settings, raw answer, parsed pick, model version,
   time and tokens.
4. Develop the prompt on a small part of the training set only. Then measure
   accuracy on the training families, how often repeated calls agree, the
   invalid-answer rate and the cost.
5. Freeze the prompt and model.

Outputs: `results/phase8/llm_calls_train.jsonl` (backed up, since it is the
only copy of paid answers), a report, the frozen prompt.

Done when: the prompt is frozen and the training-set results and costs are
known.

## Phase 9: Combining the two (RQ2)

Step 5 of the working plan, decided on training data.

Variants:
1. The LLM's suggestions are added to the meta-learner's candidates and the
   surrogate scores them all.
2. The surrogate's uncertainty decides which recommendation to trust.
3. Both recommendations run for a short time and the better one gets the rest
   of the budget, with the race counted in the budget.

Tasks:
1. Evaluate each variant by leaving families out within the training set.
2. Choose one combined method.
3. Write the pre-registration for Phase 10: the exact methods, measures,
   tests and decision rules. It is not edited once committed.

Outputs: `results/phase9/combination_cv.json`,
`planning/phase10/preregistration.md`.

Done when: the pre-registration is committed.

## Phase 10: Main experiment (RQ1, RQ2, RQ3)

Run the frozen methods once on the test problems, as pre-registered.

Tasks:
1. Open the Phase 5 test set.
2. Run the meta-learner, the LLM, the combined method, the SBS and random
   choice at the same budget, and compare with the VBS.
3. RQ1 and RQ2: the pre-registered tests.
4. RQ3: results by family, by dimension and by surrogate uncertainty. These
   are described, not tested.
5. Report every result, whatever it shows.

Outputs: `results/phase10/`, a full report.

Done when: every pre-registered analysis is reported.

## Phase 11 (optional): Real-world check and tool

Tasks:
1. Apply the frozen methods to real-world problems, for example the robotics
   and UAV path-planning sets of [cenikj2026realworld].
2. Rebuild `experiment_runner.py` so that one command takes a problem and runs
   the full pipeline: features, both recommendations, the combined choice,
   the final run, with the SBS result shown alongside.

Done when: both are reported, or skipped with a note on why.

## Phase 12: Write-up

Turn the context documents and reports into thesis chapters or a paper:
introduction and related work from the literature review, method from Phases
1, 2 and 7 to 9, results from Phase 10, and limitations. Every number comes
from a file in `results/`.

## Decisions needed before Phase 1

Open since [../research/research_gap.md](../research/research_gap.md) §11. They
can be settled at the start of Phase 1:

1. LLM provider and model.
2. Budget per run.
3. Dimensions.
4. What to do with the material from before the restart: `history/`,
   `planning/phase0/` and `archive/`.
