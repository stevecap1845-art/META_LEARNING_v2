# Round 1, Phase 5: an LLM as algorithm selector (stopped early)

Source: main project, tag `v1-final`: `docs/planning/phase5/phase5_plan.md` and
commit `27af92d`. The phase did not finish and has no report. Summarised
2026-11-20; not evidence for this repository.

## Question

Given a description of an unseen problem, can an LLM pick an algorithm that
beats the SBS, and which part of the description helps?

## Planned design

Four arms, each changing only what the LLM is told:

| Arm | Told | Tests |
|---|---|---|
| A | function name, dimension, bounds | what the LLM remembers about BBOB |
| B (primary) | dimension, bounds, the 9 landscape features, no name | selection from the features of an unseen problem |
| C | A + B | whether the features add anything to the name |
| D | dimension and bounds only | the LLM's default favourite |

Scoring followed Phase 3b: a pick gets that algorithm's rank on the row from
the existing matrix, so no optimiser runs. The plan fixed the model,
`temperature=0` and the seed, used a JSON schema that allows only the 22
algorithm names, made 3 calls per row and arm, and stored every request and
answer so the analysis can be redone offline. An invalid answer counts as rank
22 and is never silently replaced.

## Problems found in the code first

- `load_dotenv()` ran at import, so `LLMDesigner(api_key=None)` still picked
  up the key from `.env` and offline mode could not be forced.
- On any API error the designer silently returned a rule-based pick. The
  keyword rules matched nothing in the BBOB descriptions, so that pick was an
  unseeded random choice.
- No temperature or seed was set, and only the answer's keys were checked,
  not its values.
- `.env`, which holds the key, had been committed in `bd71fa0` because the
  ignore rule `.env/` only matched a folder. It was untracked on 2026-10-08
  but remains in that commit's history.

## What was done

Commit `27af92d` (2026-11-05) added an offline-safe `LLMDesigner`
(`api_key=None` means offline whatever `.env` holds, `from_env()` switches the
LLM on explicitly, answers are validated, and errors are returned as errors),
a resumable runner `phase5_llm_select.py`, and 18 offline tests with fake API
clients.

The phase stopped after 2 of 480 development calls because the Gemini API
kept answering 503 (high demand). The 2 answers exist only in a local journal
(`results/phase5/phase5_calls_dev.jsonl`, git-ignored and backed up).

## Relevance here

This repository's `LLMDesigner` has the same silent fallback (round two's
defect #10). Its hard-coded key was removed on 2026-11-20, and `api_key` now
defaults to `None`, which means offline.
