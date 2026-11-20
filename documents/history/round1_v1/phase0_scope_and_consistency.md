# Round 1, Phase 0: scope and configuration consistency

Source: main project, tag `v1-final`: `docs/reports/phase0_report.md` and
`docs/planning/phase0/phase0_decision.md`. Summarised 2026-11-20; not evidence
for this repository.

## Question

Before any experiment, what is the research question, and does the code's
default path test it?

## What was done

- The research question was fixed as algorithm selection (which algorithm to
  run on a problem). EA operator tuning became a secondary experiment, pinned
  to `algorithm=["ea"]`.
- `EXTENDED_CONFIG_SPACE` (with the `algorithm` key) became the canonical
  space, and the LLM designer was to propose across the full algorithm set.
- A consistency test was written: `test_phase0_config_consistency.py`.

## What was found

The default path was broken. Several entry points built configurations
without an `algorithm` key, and `config_space.py` defaulted to
`EA_CONFIG_SPACE`. `build_algorithm` then silently defaulted to PSO, so
"default" runs used one hard-coded algorithm instead of the selection space.

## Decisions

| # | Decision |
|---|---|
| 1 | Primary question: algorithm selection, not operator tuning |
| 2 | `EXTENDED_CONFIG_SPACE` is canonical |
| 3 | Operator tuning is secondary, `ea` only |
| 4 | The LLM designer proposes across the full algorithm set |
| 5 | Every entry point passes an explicit `algorithm` key |

The fix: all four `config_space.py` helpers default to
`EXTENDED_CONFIG_SPACE`, and `build_algorithm` raises `ValueError` when the
`algorithm` key is missing.

The budget protocol, binding on every later phase, was `population_size=50`
and `max_fe=5000` evaluations per run (`ea`: `max_generations=100`). Budgets
are equal in evaluations, not generations, because single-solution methods
such as SA spend about one evaluation per step while population methods spend
a whole population.

## Relevance here

This repository's code still has the broken default path
(`aad/evolutionary_algorithm.py:221`); it is defect #0 in the Phase 0 plan.
