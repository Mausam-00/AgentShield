# AgentShield AI — Token Optimisation Phase 5 (Token Governance)

Deterministic budgets, telemetry, warnings, hard stop controls, efficiency
evidence, and rollback. Evaluated against the SAME 12 baseline tasks. The
governed `agentshield/` engine is byte-identical; no optimisation layer can alter
policy or authorisation. No new dependency.

## Controls

1. **Token budgets** (`TokenBudget`) — per-task and per-session ceilings with a
   warn ratio. `charge()` returns `OK` / `WARN` / `STOP`. **STOP is a
   deterministic control**, not advisory: it mirrors the engine's fail-closed
   philosophy — spend halts rather than silently continuing. In the run, the
   session budget correctly raised a `WARN` on the final large task, and a
   synthetic over-budget charge fired a hard `STOP` (`budget_stop_control_fires =
   true`).

2. **Telemetry** (`Telemetry`) — structured, append-only per-task records
   (tokens, model tier, decision, latency, budget status). Auditable and
   deterministic.

3. **Efficiency evidence** (`efficiency_evidence`) — consolidated measured
   savings, written to `evals/final/final_results.json`:
   - token reduction vs baseline: **−33.4%** (244,476 → 162,833)
   - relative cost reduction: **−53.6%** (labelled premium = 4× economy model)
   - cache hit rate, budget warn/stop counts, telemetry task count.
   No figure is extrapolated; all use the disclosed `chars/4` approximation.

4. **Human approval for policy changes preserved** — the optimisation stack
   exposes no path that mutates `policy_version` or a decision. The harness
   asserts `policy_version_unchanged = true`; policy changes remain the
   deterministic engine's authority and require human approval, exactly as in the
   protocol.

## Rollback (every optimisation is reversible)

The optimisation stack lives entirely under `evals/` and is layered — disabling
any layer restores the prior behaviour with no change to the governed package:

| Layer            | Disable by                                   | Restores           |
| ---------------- | -------------------------------------------- | ------------------ |
| Dedup            | skip `dedup_blocks` (or `expand()` the text) | full instructions  |
| Scoped retrieval | pass full protocol instead of `scoped_retrieve` | whole protocol  |
| Gate tools       | use `ci._tool_definition_text()`             | full tool surface  |
| Loop limits      | drop `LoopGuard`                             | unbounded loop     |
| Evidence pointers| inline `evidence.to_dict()` (or `store.get()`)| full records      |
| Compaction       | `keep`/`threshold` large; validation fails → full detail | full history |
| Routing          | force `PREMIUM` for all                       | all-premium        |
| Caching          | bypass `SafeCache`                            | always recompute   |

Because the governed engine is untouched, the ultimate rollback is simply to
ignore the `evals/` layer entirely — authorisation behaviour is identical either
way.

## Safety summary (composed final gate — all true)

`decision_agreement_vs_baseline = 12/12`, `unsafe_actions = 0`,
`approval_bypasses = 0`, `min_critical_fact_retention = 1.0`,
`all_evidence_pointers_ok`, `all_summaries_validated`,
`routing_never_downgrades_risk`, `cache_hit_consistent`, `subagent_isolation_ok`,
`budget_stop_control_fires`, `policy_version_unchanged`.

## Tests

`tests/test_evals_phase45.py` — budget WARN/STOP (per-task and session),
telemetry totals, efficiency-evidence shape, and the composed harness safety gate
(`run_final.main() == 0`).
