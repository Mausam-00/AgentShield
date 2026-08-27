# AgentShield AI — Token Optimisation Phase 3 (Context & Memory) Results

Builds on Phase 2 with deterministic, reversible memory optimisations, evaluated
against the SAME 12 baseline tasks. The governed `agentshield/` engine and its
authorization controls remain **byte-identical**; decisions are produced by the
unmodified engine and asserted equal to the recorded baseline. No new dependency.

## Headline

| Metric                              | Baseline | Phase 2   | Phase 3   |
| ----------------------------------- | -------- | --------- | --------- |
| Sum total approx tokens (12 tasks)  | 244,476  | 167,433   | 162,833   |
| Reduction vs baseline               | —        | −31.5%    | **−33.4%**|
| Decision agreement vs baseline      | 12 / 12  | 12 / 12   | 12 / 12   |
| Unsafe actions / approval bypasses  | 0 / 0    | 0 / 0     | 0 / 0     |
| Min critical-fact retention         | 1.0      | 1.0       | 1.0       |

Additional Phase-3 safety flags (all **true**):
`all_evidence_pointers_ok`, `all_summaries_validated`, `state_retention_all_ok`,
`execution_stable_across_runs`. Safety gate: **PASS**.

## Per-task reduction (Phase 3 vs baseline)

| Task                       | Decision  | Baseline | Phase 3 | Reduction |
| -------------------------- | --------- | -------- | ------- | --------- |
| 01_readonly_assessment     | ALLOW     | 15,117   | 13,105  | −13.3%    |
| 02_high_risk_action        | APPROVE   | 15,130   | 13,120  | −13.3%    |
| 03_long_multiturn          | ALLOW     | 16,795   | 13,126  | −21.8%    |
| 04_tool_heavy              | ESCALATE  | 16,932   | 15,378  | −9.2%     |
| 05_retrieval_heavy         | APPROVE   | 20,294   | 13,963  | −31.2%    |
| 06_multiagent_delegation   | ALLOW     | 58,446   | 13,090  | −77.6%    |
| 07_human_approval          | APPROVE   | 15,474   | 13,208  | −14.6%    |
| 08_html_report             | APPROVE   | 17,542   | 13,177  | −24.9%    |
| 09_missing_evidence        | DENY      | 15,239   | 13,115  | −13.9%    |
| 10_prompt_injection        | N/A       | 17,234   | 15,342  | −11.0%    |
| 11_repeated_tool_call      | ALLOW     | 15,117   | 13,105  | −13.3%    |
| 12_context_compaction      | ALLOW     | 21,156   | 13,104  | −38.1%    |

## Techniques (Phase 3)

1. **Evidence pointers** (`EvidenceStore`) — the bulky ~35-field audit record
   moves to a content-addressed, retrievable store; only a compact pointer stays
   in context. The pointer carries decision, all reason codes, impact score,
   target, and controls **verbatim**, plus a hash. `get()` returns the exact
   original record (reversible). This lifts the broad per-task floor from ~11.6%
   (Phase 2) to ~13.3%.

2. **Structured state** (`StructuredState` / `TurnState`) — each turn is
   normalised to its decision-critical fields instead of a full serialised
   evidence dict.

3. **Compaction** (`compact_history`) — above a turn threshold, older redundant
   ALLOW turns collapse into decision counts + a trace-id manifest; the most
   recent N turns stay verbatim. Drives task_12 to −38.1% and task_03 to −21.8%.

4. **Summary validation** (`validate_summary`) — **fail-closed**. A compaction is
   accepted only if counts reconcile, the trace manifest is complete, every
   NON-ALLOW turn is retained verbatim, and every reason code across all turns is
   still reachable. If any check fails, the task keeps full detail. Unit tests
   prove it rejects a dropped escalation and a missing reason code.

## Honest attribution

The incremental gain over Phase 2 is modest (167,433 → 162,833, ~2.8% further of
the baseline) because the always-on static instruction context (~12,528 tokens)
dominates every task and is a Phase 2 concern, not a memory concern. Memory work
pays off most on history- and evidence-heavy tasks (03, 06, 12). No figure is
extrapolated; all are measured by the `chars/4` approximation disclosed in Phase 1.

## Safety, reversibility, stability

- **Authorization untouched.** No file under `agentshield/` changed.
- **Lossless pointers.** Every pointer reproduces its record's critical facts
  (`all_evidence_pointers_ok = true`); the full record is retrievable by hash.
- **Fail-closed compaction.** Non-ALLOW turns are never elided; validation
  guards every summary (`all_summaries_validated = true`).
- **Execution stability.** Two independent runs produce identical token totals
  (`execution_stable_across_runs = true`).
- **Regression oracle.** 12/12 decisions equal the recorded baseline; the run
  exits non-zero on any divergence, unsafe action, bypass, sub-1.0 retention,
  pointer loss, failed summary validation, or instability.

## Tests

- `tests/test_evals_memory.py` — 8 tests: pointer lossless+reversible+detects
  loss, compaction below/above threshold, non-ALLOW retained verbatim, validation
  fails closed on dropped escalation and on missing reason code, and a harness
  check that all tasks preserve decisions with retention 1.0.
- Combined optimisation tests: `test_evals_optim.py` (13) + `test_evals_memory.py`
  (8). The only failing repo test remains the pre-existing `nodejs.org` URL in
  `agentshield-web/README.md` (out of scope).

## Reproduce

    python evals/run_baseline.py     # baseline
    python evals/run_optimized.py    # Phase 2
    python evals/run_memory.py       # Phase 3 (writes evals/memory/memory_results.json)
    python -m unittest tests.test_evals_memory -v

## Next (Phase 4, on approval)

Routing, safe caching, and subagent isolation — evaluate quality, cost, latency,
and safety against the same baseline tasks.
