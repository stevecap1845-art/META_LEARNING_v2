# Round 1, Phases 3 and 3b: learned per-instance selector and its pre-registered test

Source: main project, tag `v1-final`: `docs/reports/phase3_report.md`,
`docs/reports/phase3b_report.md`,
`docs/planning/phase3b/phase3_preregistration.md`, `results/phase3/` and
`results/phase3b/`. Summarised 2026-11-20; not evidence for this repository.

## Question

Does a better selector design beat the SBS, and does it hold on independent
data?

## Phase 3: the selector and an ablation (training matrix only)

The selector was one random forest over the 9 landscape features plus a
one-hot encoding of the algorithm. It predicted each algorithm's rank on a row
and picked the lowest predicted rank. Validation left one function out at a
time (24 folds, with all 30 rows of a function held out together). Scores
were averaged as ranks because raw fitness spans many orders of magnitude.

In step 11 the selector's mean rank was 5.533 against the SBS's 5.521, a gap
closed of −0.3% (p = 0.677), so the two tie.

Step 12 crossed the target (rank or normalised score) with the architecture
(one forest or 22 per-algorithm forests) and scored each design on both
scales. All 8 cells were near zero or negative and none was significant; the
best was +0.8% (p = 0.823). Two cross-checks reproduced earlier scripts
exactly. The rank-trained selectors usually picked an algorithm near the top,
but their wrong picks lost much more fitness than the SBS would have.

## Phase 3b: the pre-registered confirmation

The rank target had been chosen after it won an ablation, so a p-value
computed from that choice would overstate the evidence. The method was
therefore written down in advance and run once:

- train on the 720-row matrix and evaluate on the independent 72-row matrix
  (seed 100), leaving one function out across both files;
- run one two-sided Wilcoxon test on the 24 function means, with a pass rule
  fixed in advance: p < 0.05 and a positive gap closed;
- log the one data change (the rebuilt matrices) in the pre-registration's
  append-only section, and commit it before the run.

The selector's mean rank was 5.139 against the SBS's 5.222: a gap closed of
+2.1%, p = 0.526, with 13 functions better, 7 worse and 4 tied. By the rule
fixed in advance, the Phase 3 result does not replicate.

A look at the rows, with no test attached: the selector differs from the SBS
on 49 of 72 rows, winning 28 and losing 19, but a loss costs more (6.63 ranks)
than a win gains (4.71). It does worse than the SBS at d5 and better at d20,
which fits MPA (the usual SBS) being strongest in low dimensions. That pattern
was noticed after the fact and has not been tested.

## What round two took from this

- Pre-register before any confirmatory test, and log changes append-only.
- A non-significant result does not prove the effect is zero, but a benefit of
  0.08 ranks is too small to matter.
- In-sample, the features identify the best algorithm (+96 to +98% of the gap
  closed). With these features and this model, that does not transfer to
  unseen functions.
