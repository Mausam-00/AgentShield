# AgentShield AI — Token Optimisation: Final Summary (Phases 0–5)

A measured, deterministic, reversible token-optimisation programme executed
strictly per `AgentShield_Token_Optimisation_Research_Prompt.md`. The governed
`agentshield/` engine and its 21 controls are **byte-identical to the start**;
every decision in every phase is produced by the unmodified engine and asserted
equal to the recorded baseline. No new dependency was added at any point.

## Result at a glance

| Dimension                         | Baseline | Final    | Change     |
| --------------------------------- | -------- | -------- | ---------- |
| Sum tokens (12 tasks, chars/4)    | 244,476  | 162,833  | **−33.4%** |
| Relative compute cost (units)     | 196      | 91       | **−53.6%** |
| Decision agreement vs baseline    | 12 / 12  | 12 / 12  | preserved  |
| Unsafe actions / approval bypasses| 0 / 0    | 0 / 0    | preserved  |
| Min critical-fact retention       | 1.0      | 1.0      | preserved  |

## Phase-by-phase

| Phase | Focus                         | Tokens   | vs base | Key safety property added                |
| ----- | ----------------------------- | -------- | ------- | ---------------------------------------- |
| 1     | Baseline measurement          | 244,476  | —       | regression oracle established            |
| 2     | Low-risk (dedup, contracts, scoped retrieval, gate tools, loop limits) | 167,433 | −31.5% | reversible; retention-guarded |
| 3     | Context & memory (pointers, structured state, compaction, validation) | 162,833 | −33.4% | fail-closed compaction; lossless pointers |
| 4     | Routing, caching, subagents   | 162,833  | −33.4%  | −53.6% cost; no risk downgrade; no bleed |
| 5     | Token governance              | 162,833  | −33.4%  | deterministic budget STOP; policy immutable |

Phases 4–5 hold tokens flat by design (redundancy was already removed in 2–3) and
add cost, latency, and control value instead — an honest accounting, not an
inflated token figure.

## Where the token savings come from (honest attribution)

- **Gate-specific tool loading** — broad per-task floor (full ~1,976-token tool
  surface → only the tools each gate uses).
- **Loop limits + shared context** — task_06 −77.6% (no repeated full context
  reload per delegate); repeated identical calls collapse to cache hits.
- **Scoped retrieval** — task_05 −31.2% (top-k protocol sections vs whole
  protocol).
- **Compaction + evidence pointers** — task_12 −38.1%, task_03 −21.8% (validated
  history summary; bulky audit records moved to a retrievable store).
- **Remove duplicated instructions** — measured **0 duplicate blocks**; reported
  truthfully with no savings claimed (the corpus is already non-redundant).

## Safety, honesty, reversibility

- **Authorization untouched.** No file under `agentshield/` changed; policy
  version unchanged; policy changes still require the deterministic engine and
  human approval.
- **Regression oracle.** Every harness fails closed (non-zero exit) on any
  decision divergence, unsafe action, approval bypass, sub-1.0 retention, pointer
  loss, failed summary validation, unsafe route, inconsistent cache hit, context
  bleed, or missing budget STOP.
- **Disclosed approximation.** Tokens use `chars/4`, not a provider-exact
  tokenizer; cost is a labelled relative model, not real prices. No invented
  metrics or citations.
- **Fully reversible.** The entire stack lives under `evals/`; disabling any
  layer restores prior behaviour, and ignoring `evals/` entirely leaves
  authorisation identical (rollback table in PHASE5.md).

## Artifacts

- Instrumentation: `evals/token_estimate.py`, `evals/context_inventory.py`
- Optimisation layers: `evals/optim.py` (P2), `evals/memory.py` (P3),
  `evals/routing.py` (P4), `evals/governance.py` (P5)
- Harnesses: `evals/run_baseline.py`, `run_optimized.py`, `run_memory.py`,
  `run_final.py`
- Results (JSON): `evals/baseline/`, `evals/optimized/`, `evals/memory/`,
  `evals/final/final_results.json`
- Reports: `BASELINE.md`, `PHASE2.md`, `PHASE3.md`, `final/PHASE4.md`,
  `final/PHASE5.md`, this summary
- Tests: `tests/test_evals_optim.py` (13), `tests/test_evals_memory.py` (8),
  `tests/test_evals_phase45.py` (12) — all passing

## Reproduce

    python evals/run_baseline.py
    python evals/run_optimized.py
    python evals/run_memory.py
    python evals/run_final.py
    python -m unittest tests.test_evals_optim tests.test_evals_memory tests.test_evals_phase45

## Known out-of-scope item

The only failing repo test is pre-existing: a `nodejs.org` URL in
`agentshield-web/README.md` from earlier website work, unrelated to token
optimisation. Recommend fixing separately.
