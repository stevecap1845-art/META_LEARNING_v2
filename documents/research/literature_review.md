# Literature review

Compiled 2026-11-20 for a fresh start of the project. Each paper was checked
at abstract level against arXiv, the publisher, DBLP or a university
repository; full texts were not read, so read a paper before relying on a
detail from it. BibTeX keys in brackets point to [references.bib](references.bib).
The gap these papers leave open is argued in [research_gap.md](research_gap.md).

The project's pipeline (from a problem to its landscape features, then through
a surrogate and a meta-learner to a configuration, compared with an LLM)
touches five research areas. Each table says what a paper does and what this
project can take from it.

## 1. Foundations

| Paper | What it does | What we can use |
|---|---|---|
| Rice 1976 [rice1976algorithm] | Defines the algorithm selection problem: problem space, feature space, algorithm space, performance space | The formal framing for the thesis introduction |
| Wolpert and Macready 1997 [wolpert1997nfl] | No algorithm is best on all problems | The motivation for per-problem selection |
| Kerschke et al. 2019 [kerschke2019survey] | Survey of per-instance selection, discrete and continuous, with open challenges | Terminology (SBS, VBS, per-instance selection) and the related-work skeleton |
| Hansen et al. 2021 [hansen2021coco] | COCO platform; runtime counted as function evaluations, target-based measures | The budget accounting and performance measures to follow |
| López-Ibáñez et al. 2016 [lopezibanez2016irace] | irace, iterated racing for offline configuration | A standard configurator baseline, and racing as one way to choose between the meta-learner's and the LLM's recommendation |
| Van Thieu and Mirjalili 2023 [vanthieu2023mealpy] | The mealpy library our portfolio uses | The citation for our algorithm portfolio (the PyPI citation block is wrong) |
| Ma et al. 2025 [ma2025metabbo] | MetaBBO survey: selection, configuration, solution manipulation, generation; training distributions and meta-objectives | Places our work in a taxonomy; its benchmarking guidance |
| Adriaensen et al. 2022 [adriaensen2022dac] | Dynamic algorithm configuration: changing parameters during a run | Out of scope for now; cite as the dynamic counterpart of our static choice |

## 2. Landscape features

| Paper | What it does | What we can use |
|---|---|---|
| Mersmann et al. 2011 [mersmann2011ela] | Introduces exploratory landscape analysis (ELA) features from a sample of the function | The feature concept our `landscape_features.py` imitates |
| Prager and Trautmann 2024 [prager2024pflacco] | pflacco: native Python ELA, information content, dispersion, cell mapping and more | Already installed in `.venv-pflacco`; replaces or complements our 9 home-made features |
| Renau et al. 2020 [renau2020sampling] | Feature values depend on the sampling strategy; Sobol samples gave the most accurate classifiers | Use Sobol sampling and fix the sample size, and report both |
| van Stein et al. 2023 [vanstein2023doe2vec] | DoE2Vec: autoencoder features from a design of experiments; best combined with ELA | A pip package (`doe2vec`) with pretrained models; an optional third feature set |
| Seiler et al. 2025 [seiler2025deepela] | Deep-ELA: transformers pretrained on millions of random problems; invariant to shift, scale and rotation | Pretrained features without training our own; ships as a pflacco extension |
| Cenikj et al. 2024 [cenikj2024transoptas] | TransOptAS: a transformer that predicts each algorithm's performance from raw samples | A feature-free baseline to compare against |

## 3. Feature-based selection and configuration

| Paper | What it does | What we can use |
|---|---|---|
| Kerschke and Trautmann 2019 [kerschke2019automated] | ELA + ML selector on BBOB; needs under half the SBS's resources; the feature sample is reused as the initial population | Reuse the feature sample as the first population, so the feature cost is not wasted |
| Belkhir et al. 2017 [belkhir2017piac] | Per-instance configuration of CMA-ES from features via an empirical performance model | The template for predicting a configuration, not just an algorithm |
| Jankovic and Doerr 2020 [jankovic2020fixedbudget] | Fixed-budget performance regression and selection for modular CMA-ES, with small budgets (500 evaluations) | Fixed-budget framing; small feature samples are workable |
| Long et al. 2024 [long2024landscape] | Selects an algorithm and its hyperparameters jointly with multi-output neural networks; training on random functions + MA-BBOB worked best | The closest prior work on joint selection and configuration; its training-set recipe |
| Kostovska et al. 2022 [kostovska2022perrun] | Start with a default optimizer, extract features from its trajectory, then switch and warm-start | Warm-starting the chosen algorithm; trajectory features as a cheaper alternative to a separate sample |

## 4. Generalisation to unseen problems, and how to evaluate it

This is the area where the field is stuck, and where this project can
contribute.

| Paper | What it does | What we can use |
|---|---|---|
| Vermetten et al. 2023 [vermetten2023mabbob], journal version [vermetten2024mabbobgen] | MA-BBOB: affine combinations of the 24 BBOB functions; selectors trained on BBOB transfer poorly to it | The generator is already installed (`ioh.problem.ManyAffine` in ioh 0.3.22); our source of training and test problems |
| Dietrich et al. 2024 [dietrich2024training] | Training on BBOB alone generalises badly; random MA-BBOB instances do best overall | Train on random MA-BBOB instances, not on BBOB alone |
| Cenikj et al. 2025 [cenikj2025wall] | Compares ELA, topological and deep features (DoE2Vec, TransOptAS, Deep-ELA): on out-of-distribution data, "none of the feature-based AS models outperform" the SBS | The central evidence for our gap: better features alone do not fix generalisation |
| Petelin and Cenikj 2025 [petelin2025pitfalls] | Leave-instance-out evaluation lets non-informative features look accurate; scale-sensitive metrics flatter meta-models | Evaluate by leaving whole functions or problem families out, and use scale-free metrics |
| Cenikj et al. 2026 [cenikj2026realworld] | Tests selectors trained on BBOB and CEC on real problems (robot trajectories, UAV path planning) | A ready-made real-world test set, with data on Zenodo |
| Wang et al. 2026 [wang2026geopas] | GeoPAS: geometric probing for static selection; names "calibrated fallback" as future work | Choosing between two recommendations is a form of this fallback, which the paper proposes without testing |

## 5. LLMs in algorithm design and selection

| Paper | What it does | What we can use |
|---|---|---|
| Romera-Paredes et al. 2024 [romeraparedes2024funsearch] | FunSearch: an LLM writes programs inside an evolutionary loop with an automatic evaluator | Background for LLM-in-the-loop search |
| Liu et al. 2024 [liu2024eoh] | EoH: evolves heuristic "thoughts" and code together; far fewer LLM queries than FunSearch | Prompting with a short natural-language rationale before the answer |
| van Stein and Bäck 2025 [vanstein2025llamea] | LLaMEA: LLM generates and mutates whole metaheuristics; beats CMA-ES and DE on 5-D BBOB | Shows LLMs carry useful optimisation knowledge; open-source code |
| van Stein et al. 2025 [vanstein2025blade] | BLADE: benchmark for LLM-driven algorithm design, with MA-BBOB, SBOX-COST and logging | A harness and baselines if we add LLM-generated algorithms later |
| Huang et al. 2026 [huang2026priors] | LLM-designed algorithms improve most when the prompt contains strong example code | Give the LLM concrete examples (algorithm descriptions, past results), not just a task |
| Yin et al. 2026 [yin2026landscape] | Uses ELA to build cheap proxy problems matching a real problem, then designs algorithms on the proxies with LLaMEA | ELA as the bridge between real and generated problems |
| Lian et al. 2025 [lian2025opal] | OPAL: a GNN reads a short DE trajectory, and a meta-learner outputs a per-instance operator schedule | A learned per-instance design baseline on CEC 2017 |
| Xu et al. 2026 [xu2026autoep] | AutoEP: online ELA measurements feed a chain of LLMs that adjusts hyperparameters during the run; combinatorial benchmarks | Precedent for giving an LLM landscape numbers; it is online and combinatorial, so our static continuous setting is open |
| Wu et al. 2024 [wu2024asllm] | AS-LLM: an LLM embeds algorithm code to represent algorithms for selection | An algorithm-side representation; we would add a problem-side one |
| Yamada et al. 2026 [yamada2026bbowp] | BBOWP-Bench: LLMs choose an optimizer and a search space from a word description; reasonable at picking algorithms | Evidence that LLMs can pick optimizers, but from text, not from landscape features |

## What this means for the project

1. Selecting or configuring from landscape features works in-distribution but
   has not beaten the SBS out of distribution with any feature type tried so
   far [cenikj2025wall, vermetten2023mabbob].
2. How an experiment is evaluated decides the conclusion
   [petelin2025pitfalls]: split by function or problem family, use scale-free
   measures, and train on diverse generated problems [dietrich2024training].
3. LLMs have been given landscape numbers for online hyperparameter control in
   combinatorial problems [xu2026autoep] and word descriptions for optimizer
   choice [yamada2026bbowp]. No search turned up an LLM that selects and
   configures a continuous optimizer from landscape features alone, or a
   comparison of such an LLM with a feature-based meta-learner on unseen
   problems. That is the gap in [research_gap.md](research_gap.md).
4. Knowing when not to trust a selector's prediction is named as future work
   and untested [wang2026geopas]. Choosing between the meta-learner's and the
   LLM's recommendation is one way to build it.
