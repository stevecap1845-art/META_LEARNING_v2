# Round 1, Phases 2 and 2c: performance matrices and algorithm ranking

Source: main project, tag `v1-final`: `docs/reports/phase2_report.md`,
`docs/reports/phase2c_report.md`, `results/phase2/` and `results/phase2c/`.
Summarised 2026-11-20; not evidence for this repository.

## Question

Does one algorithm win across the BBOB suite? If not, can a per-problem
selector beat always running the single best solver (SBS)?

## The two datasets

| | Phase 2: evaluation matrix | Phase 2c: training matrix |
|---|---|---|
| Problems | 24 BBOB × dims 5/10/20, seed 100 = 72 rows | 24 × dims 5/10/20 × seeds 42 to 51 = 720 rows |
| Algorithms | 22 | 22 |
| Runs per cell | 15 (seeds 1000 to 1014) | 5 (seeds 1000 to 1004) |
| Cells | 1,584 | 15,840 |
| Build time | 8.45 h | 31.25 h |
| Integrity | no missing cells, no NaN/Inf, nothing imputed | same |

Every run had population 50 and 5,000 evaluations, and a cell holds the median
best fitness. The two matrices share no seed, so the training and evaluation
sets are independent. A seed moves the optimum and the rotations, so the rows
are called pseudo-instances; they are not official COCO instances.

## Results

1. The algorithms differ strongly: a Friedman test over 22 algorithms × 72
   rows gives p ≈ 6.27e-139.
2. EO and MPA are jointly strongest, with mean ranks 4.722 and 4.847 that a
   Wilcoxon test cannot separate (p = 0.589). MPA wins outright more often (27
   rows against 9), and EO is steadier. BBO, HHO and AO rank last.
3. The best algorithm depends on dimension. MPA leads at d5 (rank 3.46) and
   falls to 5.96 by d20, EO improves as dimension grows, and PSO collapses at
   d20.
4. There is some room for a selector, but not much. The SBS equals the oracle
   (VBS) on 11 of 72 rows, 13 different algorithms are best somewhere, and the
   normalised gap has a mean of 0.060 and a median of 0.006.
5. No selector beats the SBS (leave-one-function-out, 24 folds, tests on the
   24 function means):

   | Selector | Gap closed, evaluation matrix | Gap closed, training matrix |
   |---|---|---|
   | RF regression | +30.8% (p = 0.053) | −22.9% (p = 0.356) |
   | 3-NN | +20.1% (p = 0.059) | −18.8% (p = 0.064) |
   | 1-NN | −34.8% (p = 0.287) | −33.1% (p = 0.019, worse than SBS) |
   | Random | −233% | −234% |

6. The features hold enough information. A forest allowed to see the
   held-out row closes +97.7% and +96.0% of the gap. The selectors fail when
   they have to transfer to a function they have not seen.

## What round two took from this

- 72 or 720 rows still rest on 24 independent function means, because rows of
  one function are related. Tests therefore pair function means.
- With 5 runs per cell the labels are noisy: the picked best is within 1% of
  the 15-run best only 83.3% of the time, against 97.2% at 10 runs. Round two
  uses 10 runs per training cell and 15 per test cell.
- `F5 LinearSlope` barely discriminates: on some rows 17 or 18 of the 22
  algorithms tie at the optimum.
- Matrix builders must write incrementally, resume safely, and refuse to mix
  settings that are not part of the cell key.
