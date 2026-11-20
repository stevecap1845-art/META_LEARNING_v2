# Current state of the work

Update this file at the end of every working session.
Last updated: 2026-11-20.

## Summary

The project restarted on 2026-11-20 from the code in this repository; earlier
rounds of work are not used. The environment can be rebuilt exactly (a
project-local Python 3.11.9 and two virtual environments matching their pinned
requirement files, 54 tests passing). The research direction follows the
owner's working plan: pflacco features, a search for the best algorithm and
settings, a surrogate and meta-learner trained across problems, and a
comparison with an LLM given the same features
([research/research_gap.md](research/research_gap.md)). The project is split
into 13 phases in [planning/project_plan.md](planning/project_plan.md). Phase 0
was finished on 2026-11-20: the health check found 15 defects, and each will
be fixed when the work first needs that part of the code.

## Done

| Date | What | Evidence |
|---|---|---|
| 2026-11-20 | Git repository created and pushed to `github.com/stevecap1845-art/META_LEARNING_v2` (public) | commit `606e64d` |
| 2026-11-20 | Security fix: a Google Gemini API key was hard-coded in `aad/llm_designer.py` and briefly public on GitHub. The key was removed, the commit rewritten and force-pushed, and no reachable commit contains it. `api_key` now defaults to `None` (offline rule-based mode) | [phase0_context.md §3](context/phase0_context.md#3-security-incident-hard-coded-api-key) |
| 2026-11-20 | Python 3.11.9 placed in `python-3.11.9/` (project-local, git-ignored) | `results/phase0/environment/python_version.txt` |
| 2026-11-20 | `.venv` (main) and `.venv-pflacco` (pflacco features) built from the pinned files; `pip freeze` equals the pins in both | `results/phase0/environment/` |
| 2026-11-20 | Baseline test run: 54 passed. A GP `ConvergenceWarning` appears on some runs only, because `test_gp_fit_predict` uses unseeded random data | `results/phase0/pytest_baseline.txt` |
| 2026-11-20 | Literature review (36 references, BibTeX) | [research/](research/) |
| 2026-11-20 | Research gap rewritten around the owner's plan: meta-learner vs LLM, both choosing an algorithm and its settings from pflacco features, on unseen problems at an equal budget | [research/research_gap.md](research/research_gap.md) |
| 2026-11-20 | Project plan in 13 phases (0 to 12), each with tasks, outputs and a "done when" check; the plan from before the restart moved to `archive/` | [planning/project_plan.md](planning/project_plan.md) |
| 2026-11-20 | Phase 0 health check (C1 to C6), its plan rewritten from this repository's code: 70 checks pass, 72 flagged, 0 fail; tests pass 3 times out of 3; 15 defects confirmed and each given the phase that fixes it | [phase0_context.md §5 to §7](context/phase0_context.md#5-health-check-part-b-2026-11-20), `results/phase0/health_report.txt` |

## Waiting on you

| # | Decision | Where |
|---|---|---|
| R1 | Review the project plan and its phases | [planning/project_plan.md](planning/project_plan.md) |
| R2 | LLM provider and model, evaluation budget per run, and dimensions (can wait until Phase 1) | [project_plan.md, Phase 1](planning/project_plan.md) |
| R3 | Delete, archive or keep the material from before the restart: `history/` and `archive/` | this folder |
| R4 | Revoke the leaked Gemini key in Google AI Studio | only you can do this |

## Next steps

1. Phase 1, the rules document (`planning/phase1/rules.md`), starting with
   decision R2.

## Known problems in this code

Confirmed by the Phase 0 health check on 2026-11-20. Nothing is fixed yet: by
the owner's decision, each defect is fixed when the work first uses that part
of the code. Details and evidence are in
[phase0_context.md §6](context/phase0_context.md#6-defects-and-decisions).

| Fix in | Defects |
|---|---|
| Phase 2 | D1 a configuration without `algorithm` runs PSO; D2 `EA_Designer` always runs the EA; D3 defaults to the space without `algorithm`; D5 no seeds (mealpy never repeats); D6 no evaluation budget (30 to 420 evaluations for the same settings); D10 failed runs not recorded, best-of-runs reported; D12 9 of 24 home-made BBOB functions wrong (use ioh instead); D13 missing and unseeded tests; D15 an algorithm can report a worse best than it evaluated |
| Phase 4 | D7 home-made features: double evaluation, misleading names (only if they are used) |
| Phase 7 | D8 surrogate predictions treated as measured results; D9 uncertainty in the wrong units, RF not exactly repeatable |
| Phase 8 | D4 the Gemini client is not installed, so every LLM call silently becomes a rule-based pick; the problem's name is in the prompt |
| Phase 11 | D11 ZDT summed and random Pareto plot; D14 `experiment_runner.py` |
