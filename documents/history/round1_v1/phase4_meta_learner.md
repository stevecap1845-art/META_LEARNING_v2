# Round 1, Phase 4: meta-learner against the SBS at an equal budget

Source: main project, tag `v1-final`: `docs/reports/phase4_report.md`,
`docs/planning/phase4/phase4_plan.md`,
`docs/planning/phase4/phase4_preregistration.md` and `results/phase4/`.
Summarised 2026-11-20; not evidence for this repository.

## Question

Guessing the algorithm from features did not beat the SBS. Does trying
algorithms on the problem itself, with `EA_Designer`, find better solutions
than running the SBS, at the same budget of 15 runs × 5,000 evaluations per
problem?

## How it was tested

- No new optimiser runs were made. When `EA_Designer` asked for algorithm A,
  it got one of A's stored, independently seeded runs from the matrices that it
  had not used before. Both matrices stayed read-only (md5 unchanged).
- `EA_Designer` searched only over which of the 22 algorithms to run, because
  changing population or generations would break the equal budget.
- The SBS was chosen from training data with the test function left out (MPA
  on 69 rows, EO on 3), and scored as the best of its 15 runs.
- Each row was scored from 0 (the best algorithm's median) to 1 (the worst).
  The test was one Wilcoxon on the 24 function means; passing needed p < 0.05
  and a positive gap closed.

## Fixes made to `EA_Designer` first

| Defect | Fix |
|---|---|
| Run budgets varied from 1,000 to 20,000 evaluations | a fixed budget of 15 runs |
| A skipped candidate's guess was multiplied by 1.05, which makes a negative guess look better | the penalty makes a guess 5% worse whatever its sign |
| The surrogate used all cores, and its predictions differed by up to 1.42e-14 | 1 thread |
| Features (300 evaluations) were extracted although they are identical for every candidate on a problem | switched off |

## Result

In Phase 4a (development, on the training matrix) four variants were
compared. v3, which uses the defaults (meta-population 10, surrogate on),
scored best (−0.0116) and went to the test.

In Phase 4b, the pre-registered test, v3 against the SBS closed −46.0% of the
gap, p = 0.252, with 10 functions better and 14 worse. Neither condition was
met: `EA_Designer` does not beat the SBS, and if anything does worse. A
recomputation from the raw matrices, independent of the script, gave
identical figures.

## Why it falls short (descriptive, untested)

- It spreads its runs thin, trying 9.39 algorithms per replay on average,
  while the SBS puts all 15 runs into one strong algorithm.
- The surrogate often stopped letting new candidates through: 849 of 2,160
  replays hit the generation cap with runs unspent.
- With the surrogate off, so that candidates were random, the results were
  about the same (−53.2% and −48.2%). The surrogate added little.
- The SBS is ahead at every dimension.

## What round two took from this

- At 15 runs, exploring costs more than finding the right algorithm saves. An
  earlier simulation found a gain at 2 runs (+29.6%, untested) that shrank to
  +0.2% at 5 runs, so small budgets may behave differently.
- A surrogate that learns only inside one problem cannot use the features.
  Round two therefore trains the surrogate across problems before giving it to
  the meta-learner.
