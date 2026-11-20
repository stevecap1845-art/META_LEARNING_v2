# Project plan

Adopted 2026-11-20 for this repository. It follows the main project's
round-two (v2) plan, drafted 2026-11-18, so the phase numbers match. Round-one
results are for reference only; no v1 number counts as evidence here.

## 1. Goal

Make the README's pipeline work, and test it fairly:

```
Problem  →  Landscape Features  →  Meta-Learner  →  Best EA Config  →  Solution
                                        ↑
                               Surrogate Model
                               (cheap screening)
```

> Give the program an unseen problem. It extracts the problem's landscape
> features. A surrogate model, trained on many earlier problems, screens the
> candidate configurations. The meta-learner (`EA_Designer`) picks the best
> one, and the program runs it to give the solution. It counts as a success
> only if it beats always using the single best configuration (SBS) at the
> same total budget, including the evaluations spent on computing the
> features.

## 2. What round one changed in this plan

| Round-one finding | What this plan does about it |
|---|---|
| Defects hid in defaults and wiring (for example, a missing `algorithm` key silently ran PSO) | Phase 0 checks every part before any research |
| Unequal evaluation budgets made comparisons unfair | one counted budget rule, fixed in Phase 1 and enforced in Phase 2 |
| 5 runs per training cell gave a wrong "best algorithm" label about 1 time in 6 | 10 runs per training cell, 15 per test cell |
| Home-made features were mislabelled and did not transfer across functions | both feature sets (home-made after fixes, and pflacco) checked in Phase 3 and chosen on training data in Phase 6 |
| The same test set answered three questions | one fresh test set, used once per question |
| `EA_Designer`'s surrogate learned only inside one problem, where the features never change, so they could not influence the choice | the surrogate is trained across many problems (Phase 6) before the meta-learner uses it (Phase 7) |

The last row is the reason for the phase order. Inside a single problem every
candidate has the same features, so the surrogate can only use them once it
has learned from many problems.

## 3. Phases

| Phase | README part | Question | Main output | Effort |
|---|---|---|---|---|
| 0 | all | Can the environment be rebuilt? Does every part import, connect and run? Where does the code differ from the README? | environment record, health report, defect list with decisions | hours |
| 1 | all | What are the rules? | decision document | discussion |
| 2 | Problem, EA, config space | Do the problems and algorithms follow the rules? | fixed code with tests, algorithm health screen, timing pilot | days |
| 3 | Landscape Features | Are the features correct, cheap and repeatable? | feature files for every problem | days |
| 4 | Evaluation | How does each configuration do on each problem? | training and test datasets, built once | about 1 day of compute (estimate) |
| 5 | Evaluation | What is the bar to beat? | SBS, VBS, random choice, Friedman ranking, top 10 | hours |
| 6 | Surrogate Model | Can it predict performance on a problem it has never seen? | chosen surrogate (RF or GP) and feature set | days |
| 7 | Meta-Learner | Which `EA_Designer` setup works best on training data? | frozen design and its pre-registration | days |
| 8 | whole pipeline | Does it beat the SBS on unseen problems? | the main result, run once | hours |
| 9 (optional) | LLM Designer | Does an LLM propose better configurations than rules or chance? | its own pre-registration and result | days |
| 10 | Runner and plots | Does the README's full loop work as a tool? | the README's outputs, seeded and at equal budgets | days |
| Write-up | | | thesis chapters from the context documents | weeks |

## 4. Decisions for Phase 1 (state on 2026-11-20)

These come from the main project. The ones marked decided were taken there and
still apply unless revisited.

| # | Decision | Status |
|---|---|---|
| 1 | What "Best EA Config" means | decided: B, the algorithm (24 mealpy + `ea`) plus its settings. The README-only space is the `ea` subset of the same data |
| 2 | Budget rule: the README's population × (generations + 1), or a fixed number of evaluations per run | open. Recommendation: a fixed budget. Under the README rule a setting can come out "best" partly because it spends more evaluations (up to about 20 times more) |
| 3 | Problems | decided: train and test on the 24 BBOB functions × dimensions 5, 10 and 20; the README's 4 single-objective problems as an extra unseen check; ZDT1 and ZDT2 only in the Phase 10 demo |
| 4 | Runs and seeds | recommended: 10 runs per training cell, 15 per test cell, with disjoint seed ranges that a script checks |
| 5 | Features | compute both sets in Phase 3; choose in Phase 6 on training data only |
| 6 | Surrogate | RF or GP; choose in Phase 6 |
| 7 | Statistics | function means as the unit, since rows of one function are not independent; Wilcoxon signed-rank; Bonferroni for multiple tests; pre-registered |
| 8 | LLM provider | the README says OpenAI and the code uses Gemini; decide in Phase 9 |

Configurations per problem (operator settings apply only to `ea`):

| | README budget | fixed budget |
|---|---|---|
| `ea` only | 72 | 24 |
| `ea` + 24 mealpy | 288 | 96 |

## 5. Phase notes

### Phase 0

See [phase0/phase0_plan.md](../planning/phase0/phase0_plan.md).

### Phase 2

Fix what Phase 0 sends here and build what Phase 1 decides, each with a test:
seeded problem instances; `ea` stopping at the evaluation budget; seeds in
every algorithm; operator settings used only by `ea`; failed runs reported,
never replaced by 1e12. Then screen the algorithms, dropping any that do not
optimise (`CMA_ES`, `AOA` and `DE` are re-tested), and run a short pilot to
measure the time per run.

### Phase 3

Two feature sets: the README's extractor after its fixes (each sample point
evaluated once, and names that say what they compute) and pflacco, run in
`.venv-pflacco`. Measure each feature's cost in evaluations, which counts
toward the budget, and its stability across sampling seeds.

### Phase 4

Run every configuration on every problem through `EvaluationFramework`, and
keep best, mean and std fitness, convergence, stability, runtime, evaluations
used and seeds. The build runs in parallel and can resume after an
interruption. With decision 1 = B and a fixed budget, training is 720 problems
× 96 configurations × 10 runs (691,200 runs) and test is 72 × 96 × 15
(103,680 runs). That is roughly 300 CPU-hours at 5,000 evaluations per run;
the Phase 2 pilot will replace this estimate with a measured figure.

### Phase 5

On training data only: Friedman ranking, SBS, VBS (the ceiling), random
choice, the SBS-to-VBS gap overall and by dimension, and the top 10
configurations.

### Phase 6

`SurrogateModel` takes the problem's features plus a configuration and
predicts its performance. Leave one function out at a time: on a function it
has never seen, does it rank the configurations well, and how close does its
top pick get to the VBS? Compare RF with GP and the two feature sets, with
`n_jobs=1` so results repeat exactly.

### Phase 7

Let `EA_Designer` start from the trained surrogate. Compare three variants at
the same total budget: the README's version (surrogate starts empty), a warm
start, and the surrogate alone. The best variant is frozen in a
pre-registration committed before Phase 8.

### Phase 8

Run the frozen pipeline against the SBS on the fresh test set, at the same
total budget including the feature cost. Report a Wilcoxon test on function
means and the share of the SBS-to-VBS gap closed. It runs once, and the result
is reported whatever it is.

### Phase 9

An LLM proposes a configuration from the problem's description and features.
A failed call must first show up as a failure instead of falling back to a
rule-based pick. The LLM is compared with the rule-based designer, random
choice and the SBS under its own pre-registration.

### Phase 10

Rebuild `experiment_runner.py` so it does what the README promises, with
seeds, equal budgets, enough runs, and the SBS result printed beside every
result.

## 6. Working rules

- Plan before running, in `documents/planning/phase<N>/`.
- Keep a context document per phase in `documents/context/`.
- Put results in `results/phase<N>/` and list each one in `results/README.md`.
- Take every number in a document from a result file.
- Commit at the end of each step that produces evidence, and push after
  review.
