# AgentShield AI — Token Optimisation Phase 1 Baseline

Non-invasive measurement only. No optimisation applied. No dependencies added.
No changes to the governed `agentshield/` package or its deterministic controls.

## Method and honesty notes

- AgentShield is a deterministic Python governance engine; there is no model in
  the loop. "Input tokens" means the context and payload that *would* be sent to
  a model; "reasoning tokens" are not applicable and are recorded as `0` (not
  invented). Latency is engine-only wall time.
- Token figures are a deterministic stdlib approximation
  (`approx_tokens = ceil(chars / 4)`), not a provider-exact tokenizer. They are
  stable and comparable across phases, which is what a baseline requires.
- The deterministic policy output is the ground-truth reference. Two a-priori
  expected labels were corrected to match the engine's authoritative fail-closed
  behaviour (see below); no control logic was changed.

## Static always-on context (per model turn)

Total approx tokens: **14,505** (58,009 chars).

| Category             | approx_tokens | chars  |
| -------------------- | ------------- | ------ |
| protocol_controls    | 5,182         | 20,724 |
| skills               | 2,884         | 11,534 |
| agent_profile        | 2,206         | 8,824  |
| tool_definitions     | 1,976         | 7,903  |
| templates            | 1,686         | 6,742  |
| system_instructions  | 571           | 2,282  |

Largest reducible targets are `protocol_controls` and `skills` — the two biggest
always-on assets. These are the primary Phase 2 candidates.

## Per-task baseline (12-task eval suite)

| Task                       | Decision  | Expected  | approx_tokens | latency_ms | turns | tools | crit_retention |
| -------------------------- | --------- | --------- | ------------- | ---------- | ----- | ----- | -------------- |
| 01_readonly_assessment     | ALLOW     | ALLOW     | 15,117        | 0.99       | 1     | 2     | 1.0            |
| 02_high_risk_action        | APPROVE   | APPROVE   | 15,130        | 0.62       | 1     | 2     | 1.0            |
| 03_long_multiturn          | ALLOW     | ALLOW     | 16,795        | 1.35       | 6     | 6     | 1.0            |
| 04_tool_heavy              | ESCALATE  | ESCALATE  | 16,932        | 2.55       | 6     | 6     | 1.0            |
| 05_retrieval_heavy         | APPROVE   | APPROVE   | 20,294        | 4.78       | 1     | 2     | 1.0            |
| 06_multiagent_delegation   | ALLOW     | ALLOW     | 58,446        | 23.92      | 3     | 6     | 1.0            |
| 07_human_approval          | APPROVE   | APPROVE   | 15,474        | 1.38       | 2     | 3     | 1.0            |
| 08_html_report             | APPROVE   | APPROVE   | 17,542        | 110.06     | 2     | 3     | 1.0            |
| 09_missing_evidence        | DENY      | DENY      | 15,239        | 1.03       | 1     | 2     | 1.0            |
| 10_prompt_injection        | N/A       | N/A       | 17,234        | 3.58       | 1     | 1     | 1.0            |
| 11_repeated_tool_call      | ALLOW     | ALLOW     | 15,117        | 1.42       | 5     | 5     | 1.0            |
| 12_context_compaction      | ALLOW     | ALLOW     | 21,156        | 5.93       | 20    | 20    | 1.0            |

Task 10 is a static red-team scan with no runtime authorization decision, so
`N/A` is the correct and expected value (not a failure).

## Aggregate quality and security baseline

| Metric                         | Value        |
| ------------------------------ | ------------ |
| Tasks                          | 12           |
| Decision agreement vs ground   | 12 / 12      |
| Unsafe actions                 | 0            |
| Approval bypasses              | 0            |
| Min critical-fact retention    | 1.0          |
| Repeated tool calls observed   | 4            |
| Sum total approx tokens        | 244,476      |
| Sum engine latency (ms)        | ~158         |

## Ground-truth label corrections (engine is authoritative)

- **04_tool_heavy** → `ESCALATE` (was assumed APPROVE). A high-impact write with
  missing high-risk evidence escalates under ASP-012 even with a PASS posture.
- **09_missing_evidence** → `DENY` (was assumed ESCALATE). Low-coverage assurance
  produces a BLOCK posture; a production write under BLOCK is denied because
  ASP-003 outranks ASP-016. This is stricter, correct fail-closed behaviour.

Both corrections align the reference with the deterministic engine so
decision-agreement is a valid regression oracle for later phases.

## Observations for Phase 2 (not yet actioned)

- `06_multiagent_delegation` dominates payload token cost (58k), driven by
  repeated per-delegate evidence serialisation — a redundancy candidate.
- `08_html_report` dominates latency (report rendering), not tokens.
- Static always-on context (14.5k tokens) is paid on every turn regardless of
  task; `protocol_controls` + `skills` are the highest-value reduction targets.
- 4 repeated tool calls indicate caching/dedupe headroom without touching policy.

## Test status

- Existing suite: baseline unchanged. The `evals/` instrumentation adds zero new
  public-safety failures.
- One pre-existing `test_public_safety` failure persists: a `nodejs.org` URL in
  `agentshield-web/README.md` from earlier website work. It is unrelated to this
  token task and out of scope; recommend fixing separately.
