# AgentShield AI — Token Optimisation Phase 2 (Low-Risk) Results

Deterministic, reversible, offline optimisations evaluated against the SAME 12
baseline tasks. The governed `agentshield/` engine and its authorization controls
are **byte-identical** to Phase 1 — decisions are produced by the unmodified
engine and asserted equal to the recorded baseline. No new dependency added.

## Headline

| Metric                              | Baseline | Optimized | Change      |
| ----------------------------------- | -------- | --------- | ----------- |
| Sum total approx tokens (12 tasks)  | 244,476  | 167,445   | **−31.5%**  |
| Decision agreement vs baseline      | 12 / 12  | 12 / 12   | preserved   |
| Unsafe actions                      | 0        | 0         | preserved   |
| Approval bypasses                   | 0        | 0         | preserved   |
| Min critical-fact retention         | 1.0      | 1.0       | preserved   |
| Redundant identical calls avoided   | —        | 4         | new saving  |
| Engine latency (sum ms)             | ~158     | ~56       | lower       |

Safety gate: **PASS**. The harness exits non-zero if any decision diverges, any
unsafe action or approval bypass appears, or retention drops below 1.0.

## Per-task token reduction

| Task                       | Decision  | Baseline | Optimized | Reduction |
| -------------------------- | --------- | -------- | --------- | --------- |
| 01_readonly_assessment     | ALLOW     | 15,117   | 13,358    | −11.6%    |
| 02_high_risk_action        | APPROVE   | 15,130   | 13,371    | −11.6%    |
| 03_long_multiturn          | ALLOW     | 16,795   | 14,110    | −16.0%    |
| 04_tool_heavy              | ESCALATE  | 16,932   | 15,631    | −7.7%     |
| 05_retrieval_heavy         | APPROVE   | 20,294   | 14,214    | −30.0%    |
| 06_multiagent_delegation   | ALLOW     | 58,446   | 13,324    | −77.2%    |
| 07_human_approval          | APPROVE   | 15,474   | 13,715    | −11.4%    |
| 08_html_report             | APPROVE   | 17,542   | 13,428    | −23.5%    |
| 09_missing_evidence        | DENY      | 15,239   | 13,480    | −11.5%    |
| 10_prompt_injection        | N/A       | 17,234   | 15,343    | −11.0%    |
| 11_repeated_tool_call      | ALLOW     | 15,117   | 13,358    | −11.6%    |
| 12_context_compaction      | ALLOW     | 21,156   | 14,113    | −33.3%    |

Every task's decision equals its recorded baseline decision.

## Technique-by-technique (honest attribution)

1. **Remove duplicated instructions** (`dedup_blocks`) — implemented as
   deterministic, byte-for-byte reversible exact-block dedup with an `expand()`
   inverse. **Measured result: 0 duplicate blocks found** in the current
   always-on context (12,529 → 12,528 tokens). This is a genuine finding: the
   instruction corpus is already non-redundant at block granularity. No savings
   are claimed here; the mechanism is in place and unit-tested for future/other
   content. (No fuzzy/near-duplicate removal — that would not be reversible.)

2. **Gate-specific tool loading** (`gate_tool_text` / `GATE_TOOLS`) — the largest
   broad-based win. Instead of the full ~1,976-token tool surface on every turn,
   each task loads only the tool definitions its gates use. This drives the
   ~11.6% floor visible on the simplest tasks. Unknown gates fall back to the
   full surface (context fail-open only — never an authorization fail-open).

3. **Scoped retrieval** (`scoped_retrieve`) — task_05 previously retrieved the
   entire protocol; bounded top-k section selection (deterministic term-frequency,
   stable tie-break, never-empty fallback) cut it −30.0%.

4. **Deterministic loop limits** (`LoopGuard`) —
   - task_06 (−77.2%): identical always-on instruction context is assembled once
     and shared across delegates instead of reloaded in full per delegate; each
     delegate contributes only its distinct compact result. (Full subagent
     isolation is deferred to Phase 4; this is the dedup/shared-context subset.)
   - task_11: 4 identical governance calls collapse to 1 computed call + 3 cache
     hits (the engine is deterministic, so a repeat cannot legitimately differ).
   - task_03 / task_12 (−16% / −33%): turn history is bounded to the last N
     entries plus an elision count — an explicit, deterministic cap.

5. **Compact output contract** (`compact_contract`) — a strict fixed-schema
   agent-facing result carrying decision, posture, impact score, ALL reason
   codes, approval-required, evidence pointer, and trace id. It is a superset of
   the critical-fact retention check, so it cannot silently drop a control
   outcome. Marginal token effect; primary value is guaranteed completeness.

## Safety, reversibility, and honesty guarantees

- **Authorization untouched.** No file under `agentshield/` changed; the seven
  gates and 21 controls are identical to Phase 1. Optimisations affect only how
  context / retrieval / output are assembled and how redundant identical work is
  skipped — never what the engine decides.
- **Regression oracle.** Optimized decisions are asserted equal to the recorded
  baseline decisions per task (12/12); the run fails closed otherwise.
- **Retention guard.** `retains_critical_facts` verifies decision + every reason
  code + impact score survive each compaction; min retention = 1.0.
- **Reversible.** Dedup is byte-for-byte reversible (`is_reversible()` = True);
  scoped retrieval, gate loading, and loop limits all have deterministic full
  fallbacks. Every change is toggleable.
- **Approximation disclosed.** Tokens use the `chars/4` heuristic, not a
  provider-exact tokenizer; figures are comparable across phases, not absolute.
- **No invented numbers.** The 0-duplicate-blocks result is reported as-is.

## Tests

- `tests/test_evals_optim.py` — 13 tests: dedup reversibility (with and without a
  planted duplicate), scoped-retrieval relevance/determinism/never-empty fallback,
  gate-tool subset vs full-fallback, LoopGuard dedupe/stop/bounded-history,
  contract completeness, retention true-and-detects-loss, and a harness check that
  every task preserves decisions with retention 1.0.
- Full suite: 87 tests. The only failure is the pre-existing `nodejs.org` URL in
  `agentshield-web/README.md` (earlier website work, out of scope for this task).

## Reproduce

    python evals/run_baseline.py       # writes evals/baseline/baseline_results.json
    python evals/run_optimized.py      # writes evals/optimized/optimized_results.json
    python -m unittest tests.test_evals_optim -v

## Next (Phase 3, on approval)

Structured state, validated compaction, and evidence pointers — deeper context
and memory reductions with critical-fact-retention and execution-stability tests.
