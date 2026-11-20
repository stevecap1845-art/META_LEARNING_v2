# Project documents

This folder holds the plans, lab notes and history of the Autonomous Algorithm
Design (AAD) meta-learning project in
`github.com/stevecap1845-art/META_LEARNING_v2`. The root `README.md`
describes the framework as first written. It stays unchanged, and the
differences between it and the code are recorded here.

[CURRENT_STATE.md](CURRENT_STATE.md) says where the work stands and what comes
next. The project restarted on 2026-11-20. The research direction is in
[research/research_gap.md](research/research_gap.md) and the phases in
[planning/project_plan.md](planning/project_plan.md). `history/` and
`archive/` predate the restart and wait on decision R3 in CURRENT_STATE.md.

## Layout

```
documents/
├── README.md              this index
├── CURRENT_STATE.md       living status: what is done, what is open, next step
├── research/              literature review, research gap, references.bib
├── planning/              written BEFORE a phase runs
│   ├── project_plan.md    the whole project, every phase
│   └── phase<N>/          plans, decisions, pre-registrations for phase N
├── context/               written WHILE and AFTER a phase runs
│   └── phase<N>_context.md   what was done, found and decided
├── history/               the work done before this repository existed
│   ├── README.md          how the earlier rounds relate to this one
│   ├── round1_v1/         one context document per round-one phase
│   └── round2_v2/         the round-two (v2) work done in the main project
└── archive/               documents replaced at the restart (not used)

results/                   (at the repository root, not in documents/)
├── README.md              manifest: every result file, whether it is current, cost to rebuild
├── phase<N>/              one folder per phase
├── inherited/             outputs that arrived with the code; not evidence
└── experiment_runner/     scratch output of experiment_runner.py (git-ignored)
```

## Rules

1. A phase gets `planning/phase<N>/` before anything runs. Pre-registrations
   are never edited once committed; later changes are appended as dated
   entries.
2. `context/phase<N>_context.md` is the phase's lab notebook: what was done
   (with dates and commits), what was found (with the result file each number
   comes from), and what was decided and why.
3. Every figure in a context document points to a file under
   `results/phase<N>/`. Recalled or hand-computed numbers are not used.
4. A phase writes only into `results/phase<N>/`, and every file it writes is
   listed in `results/README.md`.
5. Runs are seeded and record their seeds. A failed run is reported, never
   silently replaced.
6. API keys never go in source code. Pass a key to
   `LLMDesigner(api_key=...)` at run time; a local `.env` file is git-ignored.

## Phases of this repository

The full plan, with tasks and "done when" checks for each phase, is in
[planning/project_plan.md](planning/project_plan.md).

| Phase | Name | Planning | Context | Results | Status |
|---|---|---|---|---|---|
| 0 | Environment and code health | [phase0_plan.md](planning/phase0/phase0_plan.md) | [phase0_context.md](context/phase0_context.md) | [results/phase0/](../results/phase0/) | done 2026-11-20: health check run, 15 defects each assigned to a phase |
| 1 | Experimental rules | in project plan | none yet | none yet | not started |
| 2 | Code foundations | in project plan | none yet | none yet | not started |
| 3 | Screening and timing pilot | in project plan | none yet | none yet | not started |
| 4 | Landscape features | in project plan | none yet | none yet | not started |
| 5 | Performance dataset | in project plan | none yet | none yet | not started |
| 6 | Baselines | in project plan | none yet | none yet | not started |
| 7 | Surrogate and meta-learner (RQ1) | in project plan | none yet | none yet | not started |
| 8 | LLM recommender (RQ1) | in project plan | none yet | none yet | not started |
| 9 | Combining the two (RQ2) | in project plan | none yet | none yet | not started |
| 10 | Main experiment (RQ1 to RQ3) | in project plan | none yet | none yet | not started |
| 11 | Real-world check and tool (optional) | in project plan | none yet | none yet | not started |
| 12 | Write-up | in project plan | none yet | none yet | not started |

## Earlier work

| Round | Where it ran | Context documents | Headline |
|---|---|---|---|
| Round 1 (v1) | main project, tag `v1-final` | [history/round1_v1/](history/round1_v1/) | Neither a feature-based selector (+2.1%, p=0.526) nor `EA_Designer` (−46.0%, p=0.252) beat always running the single best solver |
| Round 2 (v2), Phase 0 | main project, branch `v2` | [history/round2_v2/](history/round2_v2/) | Health check run 2026-11-20: 11 known defects confirmed, 2 checks need attention; findings not yet reviewed |

[history/README.md](history/README.md) explains how that work relates to the
code in this repository.
