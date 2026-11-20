# Research gap and proposed direction (draft for review)

Rewritten 2026-11-20 around the project owner's working plan. Only the
literature in [literature_review.md](literature_review.md) and this
repository's code were used. Keys in brackets point to
[references.bib](references.bib).

## Working title

Meta-learner or LLM? Choosing an optimisation algorithm and its settings from
landscape features for unseen continuous problems.

## 1. The working plan

1. Take an optimisation problem and extract its landscape features with
   pflacco.
2. Run candidate algorithm + setting combinations (population, selection,
   crossover, mutation, max_generations) several times each and find the best
   combination.
3. Build a surrogate model and the meta-learner side by side, so that they
   learn which combination works best and can recommend one.
4. Give the same features to an LLM and get its recommended combination.
5. Compare the meta-learner's and the LLM's answers, and choose the better
   one.

Steps 1 to 3 on their own are per-instance algorithm configuration, which is
well studied [lopezibanez2016irace, belkhir2017piac, long2024landscape].
Steps 4 and 5 are where the gap is (section 3). The plan turns into research
once three conditions from section 4 hold: the meta-learner learns across
problems, it is tested on problems it has never seen, and every method gets
the same budget.

## 2. What the field has established

- Landscape features plus machine learning can pick a good algorithm, and set
  its parameters, for problems that resemble the training problems
  [kerschke2019automated, belkhir2017piac, long2024landscape].
- On problems outside the training distribution, no feature-based selector
  has beaten simply running the single best solver (SBS), with classical ELA
  or with newer learned features (DoE2Vec, TransOptAS, Deep-ELA)
  [cenikj2025wall, vermetten2023mabbob].
- Training on diverse generated problems helps more than training on BBOB
  alone [dietrich2024training, long2024landscape].
- Common evaluation habits overstate how well selectors work: leave-instance-out
  splits and scale-sensitive metrics [petelin2025pitfalls].
- LLMs carry useful knowledge about optimizers. They have generated
  metaheuristics [vanstein2025llamea], picked optimizers from word
  descriptions of a problem [yamada2026bbowp], and adjusted parameters during
  a run from landscape measurements in combinatorial problems [xu2026autoep].

## 3. The gap

Searches on 2026-11-20 found no study that:

1. gives an LLM only the landscape features of a continuous problem (no name,
   no description) and asks it to choose an algorithm and its settings;
2. compares that LLM with a feature-based meta-learner on problems neither has
   seen, at the same evaluation budget, against the SBS and the best possible
   choice;
3. combines the two and tests whether the combination beats both.

This matters for two reasons. Feature-based meta-learners fail on unseen
problems because they only know their training data [cenikj2025wall], while an
LLM brings general knowledge from outside that data. Whether that knowledge
helps where the meta-learner fails has not been measured. The newest static
selection paper also lists "calibrated fallback" (knowing when not to trust a
prediction) as future work [wang2026geopas]; deciding between the
meta-learner and the LLM is one form of it.

## 4. Conditions that make the plan research

1. The meta-learner learns across problems. Every candidate on a single
   problem has the same feature vector, so features cannot help choose between
   candidates there. The surrogate is trained on many problems (features plus
   configuration predict performance) and then used on new ones.
2. Test problems are unseen. Training and test problems come from separate
   problem families, split so that no test family appears in training
   [petelin2025pitfalls].
3. Every method gets the same budget, counted in function evaluations:
   the pflacco sample, any trial runs and the final run. The `ea` evaluates
   its starting population and then one batch of offspring per generation
   (`aad/evolutionary_algorithm.py:143`, `:170`), so a run costs about
   population × (generations + 1): from about 1,000 to 20,000 evaluations in
   the current config space. Without a fixed budget the "best" setting tends
   to be the one that spends the most.
4. The LLM test is fair: the prompt holds only feature values and the
   candidate list, both methods choose from the same candidates, each question
   is asked several times, and every call and answer is stored.

## 5. Research questions

| # | Question | Measure |
|---|---|---|
| RQ1 | On unseen problems and at an equal budget, how does a pflacco-based meta-learner compare with an LLM given the same features? | Share of the SBS-to-VBS gap closed; rank among all candidates; Wilcoxon test on per-function means |
| RQ2 | Does combining them beat both? Two ways are tested: (a) the LLM's suggestions are scored by the surrogate along with the meta-learner's own candidates; (b) the surrogate's uncertainty decides which recommendation to trust | Same measures as RQ1, against each method alone |
| RQ3 | On which kinds of problems, and in which dimensions, does each one win? | Results split by problem family, dimension and surrogate uncertainty |

## 6. Method

Offline, once:

1. Generate training problems with MA-BBOB (`ioh.problem.ManyAffine`) in
   dimensions 5, 10 and 20 [vermetten2023mabbob, dietrich2024training].
2. Compute pflacco features for each from a fixed-size Sobol sample
   [renau2020sampling, prager2024pflacco].
3. Run every candidate on every training problem several times with fixed
   seeds. This is step 2 of the working plan; its results are the training
   data.
4. Train the surrogate on those results, and fit the meta-learner
   (`EA_Designer`) to search the candidate space with the surrogate's help.

For each new problem:

1. Compute its pflacco features from the same Sobol sample; the sample can be
   reused as the algorithm's first population [kerschke2019automated].
2. The meta-learner recommends a candidate.
3. The LLM recommends a candidate from the feature values alone.
4. Choose between them, either by a short race of both with the cost counted
   in the budget [lopezibanez2016irace], or by the surrogate's uncertainty
   (RQ2b).
5. Run the chosen candidate with the rest of the budget.

## 7. Search space

Selection, crossover and mutation only affect the built-in `ea`. The mealpy
wrapper passes only population size and generations to mealpy
(`aad/mealpy_algorithms.py:213-235`). The distinct candidates are therefore:

| | Budget set by population × generations | Fixed evaluation budget |
|---|---|---|
| `ea` | 72 (3 populations × 8 operator combinations × 3 generation counts) | 24 (generations follow from the budget) |
| 24 mealpy algorithms | 216 (24 × 3 populations × 3 generation counts) | 72 (24 × 3 populations) |
| Total | 288 | 96 |

Condition 3 implies the fixed-budget column: 96 candidates.

## 8. How the repository supports this

| Need | Already in the repository | Work needed |
|---|---|---|
| Problems | 24 BBOB functions (`aad/problems.py`); MA-BBOB via `ioh.problem.ManyAffine` (ioh 0.3.22) | A seeded generator of training and test problem families |
| Features | pflacco in `.venv-pflacco`; 9 home-made features (`aad/landscape_features.py`) | A fixed Sobol sample; feature cost counted in the budget; a way to pass pflacco results from `.venv-pflacco` to the main environment |
| Candidates | 24 mealpy algorithms plus `ea` (`aad/config_space.py`) | A fixed evaluation budget per run; fix the fallback that runs PSO when a configuration has no `algorithm` key (`aad/evolutionary_algorithm.py:221`) |
| Surrogate | `SurrogateModel`, RF or GP, with `predict_with_uncertainty` | Train it across problems |
| Meta-learner | `EA_Designer` (`aad/meta_learner.py`) | Start it from the trained surrogate |
| LLM | `LLMDesigner` (`aad/llm_designer.py`) | Prompt with feature values only (today `generate_description` puts the problem's name in the prompt); validate answers against the candidate list; report a failed call as a failure instead of silently returning a rule-based pick |
| Evaluation | `EvaluationFramework`, `Visualizer` | Seeds, the fixed budget, scale-free scores |

## 9. Evaluation design

- Baselines: SBS, VBS (the best candidate per problem, as a ceiling), random
  choice, and irace tuned on the training problems [lopezibanez2016irace].
- Tests from easy to hard: unseen problems from training families; held-out
  problem families; and, as a stretch goal, the real-world problems of
  [cenikj2026realworld].
- Scale-free measures (ranks, or the share of the SBS-to-VBS gap closed), and
  statistics on per-function means.
- The final comparison is pre-registered and run once.

## 10. Risks

- The LLM may not reason well from raw feature numbers. RQ1 measures that
  directly, so a negative answer is still a result.
- LLM answers change between model versions, and API access can fail. Every
  call is stored, the claims name the model and version tested, and the
  analysis can be redone offline from the stored answers.
- Compute: 96 candidates × many problems × several runs is large. A timing
  pilot comes before the full build.
- Neither method may beat the SBS on unseen problems; RQ2 and RQ3 then show
  where and why.

## 11. Decisions for you

1. LLM provider and model: the code uses Google Gemini, while the README
   mentions OpenAI.
2. The evaluation budget per run, for example 1,000 × dimension or a single
   fixed number.
3. Dimensions: 5, 10 and 20, or fewer to save compute.
4. What to do with the earlier-round material still in `documents/`
   (`history/`, `archive/`, `planning/phase0/`): delete it,
   move it to an archive folder, or keep it as it is.
