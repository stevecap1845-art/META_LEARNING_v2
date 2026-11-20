# History: work done before this repository

Written 2026-11-20 from the main project's own documents. The code, data and
result files these documents describe are in the main project, not here, so
re-run anything before quoting it as a result of this repository.

## Where the earlier work is

| Round | Location | Code state |
|---|---|---|
| Starting code | main project commit `bd71fa0` (2026-09-03); this repository is that code, see [../context/phase0_context.md](../context/phase0_context.md) | original framework |
| Round 1 (v1), 2026-09 to 2026-11 | main project (`D:\META_LEARNING\Meta_Learning`, remote `github.com/Akash7762/Meta_Learning`), git tag `v1-final` (commit `bf2c22d`) | fixed default path; `CMA_ES`, `AOA` and `DE` removed; equal evaluation budgets; resumable matrix builders |
| Round 2 (v2), from 2026-11-18 | same project, branch `v2` | v1 framework fixes kept, v1 phases dropped; `CMA_ES`, `AOA` and `DE` restored for re-testing |

## Why there was a round 2

Round one asked a narrower question than the README: can landscape features
pick the best algorithm for an unseen problem (algorithm selection)? The
answer was no, at least not better than always running the single best solver.
Round two set the README's full pipeline as the goal: features, then a
surrogate trained across problems, then the meta-learner, then a
configuration. It kept the fixed code, dropped all the data, and turned round
one's methods into rules.

## Documents

### Round 1 (v1)

| Phase | Document | Headline |
|---|---|---|
| 0 | [phase0_scope_and_consistency.md](round1_v1/phase0_scope_and_consistency.md) | Research question fixed on algorithm selection; a broken default path (a missing `algorithm` key ran PSO) found and fixed; equal-evaluation budget protocol |
| 1, 1b | [phase1_baseline_and_screening.md](round1_v1/phase1_baseline_and_screening.md) | PSO beats GA on Sphere (p=3.0e-11, a pipeline check); 21 algorithms screened; `CMA_ES`, `AOA` and `DE` removed |
| 2, 2c | [phase2_performance_matrices.md](round1_v1/phase2_performance_matrices.md) | 72-row evaluation and 720-row training matrices; EO and MPA jointly strongest; no selector beats the SBS |
| 3, 3b | [phase3_feature_selector.md](round1_v1/phase3_feature_selector.md) | Pre-registered test on independent data: +2.1%, p=0.526, so the Phase 3 result does not replicate |
| 4 | [phase4_meta_learner.md](round1_v1/phase4_meta_learner.md) | `EA_Designer` against the SBS at an equal budget: −46.0%, p=0.252, so it does not beat the SBS |
| 5 | [phase5_llm_designer.md](round1_v1/phase5_llm_designer.md) | LLM as selector: planned and coded, stopped after 2 of 480 calls because the API was overloaded |

### Round 2 (v2)

| Phase | Document | Headline |
|---|---|---|
| 0 | [phase0_health_check.md](round2_v2/phase0_health_check.md) | Health check run 2026-11-20: 11 known defects confirmed, 2 ruled out; findings not yet reviewed |

## What carries over to this repository

1. The method: equal evaluation budgets, seeds everywhere, function means as
   the statistical unit, leave-one-function-out validation, pre-registration
   before any confirmatory test, and the SBS as the bar to beat.
2. The known defects: every defect round one found is still in this
   repository's code (see the register in the Phase 0 plan).
3. What to expect: the features identify the best algorithm almost perfectly
   for a function already seen (in-sample ceiling +96 to +98%), but that did
   not carry over to unseen functions. Any new design should be judged against
   that.
