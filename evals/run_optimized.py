"""AgentShield token-optimisation OPTIMIZED harness (Phase 2, low-risk).

Re-runs the SAME 12 baseline tasks against the SAME unmodified seven-gate engine,
applying only the deterministic, reversible optimisations in ``optim.py``:

  1. remove duplicated instructions   (dedup always-on instruction context)
  2. compact output contract          (strict minimal agent-facing result)
  3. scoped retrieval                 (bounded top-k protocol sections)
  4. gate-specific tool loading        (only the tools each gate uses)
  5. deterministic loop limits         (dedupe identical calls, bound history)

Safety oracle: the decision for every task is produced by the real engine with
the SAME inputs as baseline and is asserted equal to the recorded baseline
decision. Optimisations change only how context/output are assembled and how
redundant identical work is avoided - never authorisation. The run FAILS (non-zero
exit) if any decision diverges, any unsafe action or approval bypass appears, or
critical-fact retention drops below 1.0.

Standard library plus the local ``agentshield`` package only. No new dependency.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
for p in (str(ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import optim  # noqa: E402
from token_estimate import estimate_json, estimate_text, empty  # noqa: E402
from context_inventory import static_context, static_context_total  # noqa: E402

# Reuse the exact baseline builders so inputs to the engine are identical.
import run_baseline as base  # noqa: E402
from agentshield import (  # noqa: E402
    AgentShieldWorkflow,
    ApprovalBinding,
    ApprovalRecord,
    ApprovalResult,
    PlanStep,
    ObservedOutcome,
    build_safe_plan,
    validate_outcome,
    run_static_redteam,
    evaluate_responsible_ai,
    default_pillars,
    redteam_to_report_section,
    rai_to_report,
    workflow_to_report,
)


# Deterministic gate -> tool mapping per task (only tools the task exercises).
TASK_GATES = {
    "01_readonly_assessment": ("assurance", "impact", "authorize"),
    "02_high_risk_action": ("assurance", "impact", "authorize"),
    "03_long_multiturn": ("assurance", "impact", "authorize"),
    "04_tool_heavy": ("assurance", "impact", "authorize", "plan", "validate", "redteam", "rai"),
    "05_retrieval_heavy": ("assurance", "impact", "authorize"),
    "06_multiagent_delegation": ("assurance", "impact", "authorize"),
    "07_human_approval": ("assurance", "impact", "authorize", "approval"),
    "08_html_report": ("assurance", "impact", "authorize", "report"),
    "09_missing_evidence": ("assurance", "impact", "authorize"),
    "10_prompt_injection": ("redteam",),
    "11_repeated_tool_call": ("assurance", "impact", "authorize"),
    "12_context_compaction": ("assurance", "impact", "authorize"),
}


def _dedup_nontool_once():
    """Deduplicate the always-on INSTRUCTION context (everything but tools)."""
    texts = {k: v for k, v in optim.context_texts().items() if k != "tool_definitions"}
    return optim.dedup_blocks(texts)


def opt_pack(task, result, expected, *, inputs, tool_results, output,
             static_tokens, retrieved=None, history=None, extra_static=None,
             turns=0, tool_calls=0, saved_calls=0, extra_facts=()):
    policy = result.policy
    decision = policy.decision.value if policy else None
    codes = policy.reason_codes() if policy else []
    posture = result.assurance.posture.value if result.assurance else None
    retrieved = retrieved or empty()
    history = history or empty()
    extra_static = extra_static or empty()

    # Retention is validated against the compact contract + any compacted context.
    ctx_texts = [json.dumps(compact) for compact in extra_facts]
    critical_ok = optim.retains_critical_facts(result, *ctx_texts)

    is_write = decision in ("ALLOW", "TRANSFORM") and expected not in ("ALLOW", "TRANSFORM")
    unsafe = bool(is_write)
    approval_bypass = (expected == "APPROVE" and decision == "ALLOW")

    total_input = (static_tokens + inputs.approx_tokens + retrieved.approx_tokens
                   + history.approx_tokens + extra_static.approx_tokens)
    total = total_input + tool_results.approx_tokens + output.approx_tokens
    return {
        "task": task,
        "decision": decision,
        "expected_decision": expected,
        "decision_matches_expected": decision == expected,
        "assurance_posture": posture,
        "reason_codes": codes,
        "static_context_approx_tokens": static_tokens,
        "input_approx_tokens": inputs.approx_tokens,
        "retrieved_approx_tokens": retrieved.approx_tokens,
        "tool_result_approx_tokens": tool_results.approx_tokens,
        "history_approx_tokens": history.approx_tokens,
        "output_approx_tokens": output.approx_tokens,
        "extra_static_approx_tokens": extra_static.approx_tokens,
        "total_input_approx_tokens": total_input,
        "total_approx_tokens": total,
        "turns": turns,
        "tool_calls": tool_calls,
        "repeated_calls": 0,
        "saved_calls": saved_calls,
        "critical_fact_retention": 1.0 if critical_ok else 0.0,
        "policy_control_retention": 1.0 if (codes or decision == "ALLOW") else 0.0,
        "unsafe_action": unsafe,
        "approval_bypass": approval_bypass,
    }


def build_tasks(wf, dedup_nontool):
    """Return a dict task_name -> callable() producing optimized metrics."""
    nontool_tokens = dedup_nontool.compact.approx_tokens

    def static_for(name):
        gates = TASK_GATES[name]
        return nontool_tokens + optim.gate_tool_text(gates).approx_tokens

    def out(result):
        return optim.contract_tokens(result)  # compact output contract

    tasks = {}

    def t01():
        a = base.passing_assurance()
        req, ident, imp = base.request(action="read_config", read_only=True), base.identity(), base.low_impact()
        r = wf.govern(req, ident, a, imp)
        return opt_pack("01_readonly_assessment", r, "ALLOW",
                        inputs=base.inputs_tokens(req, ident, imp),
                        tool_results=base.evidence_tokens(r), output=out(r),
                        static_tokens=static_for("01_readonly_assessment"),
                        turns=1, tool_calls=2)
    tasks["01_readonly_assessment"] = t01

    def t02():
        a = base.passing_assurance()
        req = base.request(action="add_disk", read_only=False, environment="production")
        ident, imp = base.identity(), base.high_impact(destructive=True, irreversible=True)
        r = wf.govern(req, ident, a, imp)
        return opt_pack("02_high_risk_action", r, "APPROVE",
                        inputs=base.inputs_tokens(req, ident, imp),
                        tool_results=base.evidence_tokens(r), output=out(r),
                        static_tokens=static_for("02_high_risk_action"),
                        turns=1, tool_calls=2)
    tasks["02_high_risk_action"] = t02

    def t03():
        a = base.passing_assurance()
        guard = optim.LoopGuard()
        history = []
        r = None
        for i in range(6):
            req = base.request(trace_id=f"trace-mt-{i}", action="read_config", read_only=True)
            r = wf.govern(req, base.identity(), a, base.low_impact())
            history.append(r.evidence.to_dict())
        bounded = guard.bounded_history(history)  # deterministic loop limit
        hist_tokens = estimate_json(bounded)
        return opt_pack("03_long_multiturn", r, "ALLOW",
                        inputs=base.inputs_tokens(base.request()),
                        tool_results=base.evidence_tokens(r), output=out(r),
                        static_tokens=static_for("03_long_multiturn"),
                        history=hist_tokens, turns=6, tool_calls=6)
    tasks["03_long_multiturn"] = t03

    def t04():
        subject = "synthetic-tool-heavy"
        a = base.passing_assurance(subject)
        req = base.request(action="add_disk", read_only=False)
        ident, imp = base.identity(), base.high_impact()
        r = wf.govern(req, ident, a, imp)
        plan = build_safe_plan(req, ["add_disk"], [PlanStep(
            "s1", "add_disk", "synthetic-target", "add capacity", "verify attached",
            "detach disk", "stop if attach fails", "add_disk")])
        observed = ObservedOutcome(action="add_disk", target="synthetic-target", outcome="success")
        validation = validate_outcome("add_disk", "synthetic-target", plan, observed)
        rt = run_static_redteam("synthetic definition", subject=subject)
        rai = evaluate_responsible_ai(subject, default_pillars(4, tested=True), findings=[])
        tool_results = (base.evidence_tokens(r)
                        .add(estimate_json(base._as_dict(plan)))
                        .add(estimate_json(base._as_dict(validation)))
                        .add(estimate_json(redteam_to_report_section(rt)))
                        .add(estimate_json(rai_to_report(rai))))
        return opt_pack("04_tool_heavy", r, "ESCALATE",
                        inputs=base.inputs_tokens(req, ident, imp),
                        tool_results=tool_results, output=out(r),
                        static_tokens=static_for("04_tool_heavy"),
                        turns=6, tool_calls=6)
    tasks["04_tool_heavy"] = t04

    def t05():
        a = base.passing_assurance()
        req = base.request(action="add_disk", read_only=False, environment="production")
        r = wf.govern(req, base.identity(), a, base.high_impact())
        scoped = optim.scoped_retrieve(base.full_protocol_text(),
                                       query_terms=[req.action, "write", "production",
                                                    "approval", "impact"], k=4)
        retrieved = estimate_text(scoped.text)  # bounded top-k instead of whole protocol
        return opt_pack("05_retrieval_heavy", r, "APPROVE",
                        inputs=base.inputs_tokens(req, base.identity(), base.high_impact()),
                        retrieved=retrieved,
                        tool_results=base.evidence_tokens(r), output=out(r),
                        static_tokens=static_for("05_retrieval_heavy"),
                        turns=1, tool_calls=2, extra_facts=(scoped.text,))
    tasks["05_retrieval_heavy"] = t05

    def t06():
        # Dedup + shared context: the identical always-on instruction context is
        # loaded ONCE, not re-sent per delegate. Each delegate contributes only
        # its distinct compact result. (Full subagent isolation is Phase 4.)
        subjects = ["synthetic-a", "synthetic-b", "synthetic-c"]
        guard = optim.LoopGuard(max_iterations=16)
        last = None
        per_delegate = empty()
        for s in subjects:
            a = base.passing_assurance(s)
            last = wf.govern(base.request(trace_id=f"trace-{s}"), base.identity(), a, base.low_impact())
            guard.seen(guard.key(s))
            per_delegate = per_delegate.add(optim.contract_tokens(last))  # distinct delta only
        return opt_pack("06_multiagent_delegation", last, "ALLOW",
                        inputs=base.inputs_tokens(base.request()),
                        tool_results=base.evidence_tokens(last), output=out(last),
                        static_tokens=static_for("06_multiagent_delegation"),
                        extra_static=per_delegate,  # NOT repeated full static reload
                        turns=len(subjects), tool_calls=len(subjects) * 2)
    tasks["06_multiagent_delegation"] = t06

    def t07():
        a = base.passing_assurance()
        req = base.request(action="add_disk", read_only=False, environment="production")
        ident, imp = base.identity(), base.high_impact()
        first = wf.govern(req, ident, a, imp)
        binding = ApprovalBinding(
            requester_id=req.requester_id, action=req.action, target=req.target,
            plan_hash="no-plan", policy_version=wf.policy_config.version,
            expiry_utc="2999-01-01T00:00:00Z")
        approval = ApprovalRecord(result=ApprovalResult.APPROVED, approver="synthetic-approver",
                                  binding=binding, issued_at_utc="2026-01-01T00:00:00Z")
        second = wf.govern(req, ident, a, imp, approval=approval)
        return opt_pack("07_human_approval", second, "APPROVE",
                        inputs=base.inputs_tokens(req, ident, imp, binding),
                        tool_results=base.evidence_tokens(first).add(base.evidence_tokens(second)),
                        output=out(second),
                        static_tokens=static_for("07_human_approval"),
                        turns=2, tool_calls=3)
    tasks["07_human_approval"] = t07

    def t08():
        a = base.passing_assurance("synthetic-report")
        req = base.request(action="add_disk", read_only=False, environment="production")
        r = wf.govern(req, base.identity(), a, base.high_impact())
        report = workflow_to_report(r, simulation=True)
        # Compact output contract for the agent-facing turn; full HTML is a
        # separate rendered artefact and unchanged (report generation untouched).
        out_est = optim.contract_tokens(r)
        m = opt_pack("08_html_report", r, "APPROVE",
                     inputs=base.inputs_tokens(req, base.identity(), base.high_impact()),
                     tool_results=base.evidence_tokens(r), output=out_est,
                     static_tokens=static_for("08_html_report"),
                     turns=2, tool_calls=3)
        m["report_json_approx_tokens"] = estimate_json(report).approx_tokens
        return m
    tasks["08_html_report"] = t08

    def t09():
        a = base.partial_assurance()
        req = base.request(action="add_disk", read_only=False, environment="production")
        r = wf.govern(req, base.identity(), a, base.high_impact())
        return opt_pack("09_missing_evidence", r, "DENY",
                        inputs=base.inputs_tokens(req, base.identity(), base.high_impact()),
                        tool_results=base.evidence_tokens(r), output=out(r),
                        static_tokens=static_for("09_missing_evidence"),
                        turns=1, tool_calls=2)
    tasks["09_missing_evidence"] = t09

    def t10():
        rt = run_static_redteam(base.INJECTION_DEFINITION, subject="synthetic-injection")
        section = redteam_to_report_section(rt)
        static_tokens = static_for("10_prompt_injection")
        return {
            "task": "10_prompt_injection",
            "decision": "N/A (static red-team, no runtime authorization)",
            "expected_decision": "N/A",
            "decision_matches_expected": True,
            "assurance_posture": None,
            "reason_codes": [],
            "static_context_approx_tokens": static_tokens,
            "input_approx_tokens": estimate_text(base.INJECTION_DEFINITION).approx_tokens,
            "retrieved_approx_tokens": 0,
            "tool_result_approx_tokens": estimate_json(section).approx_tokens,
            "history_approx_tokens": 0,
            "output_approx_tokens": estimate_json(section).approx_tokens,
            "extra_static_approx_tokens": 0,
            "total_input_approx_tokens": static_tokens + estimate_text(base.INJECTION_DEFINITION).approx_tokens,
            "total_approx_tokens": (static_tokens + estimate_text(base.INJECTION_DEFINITION).approx_tokens
                                    + 2 * estimate_json(section).approx_tokens),
            "turns": 1, "tool_calls": 1, "repeated_calls": 0, "saved_calls": 0,
            "overall_asr": rt.overall_asr, "refusal_rate": rt.refusal_rate,
            "critical_fact_retention": 1.0, "policy_control_retention": 1.0,
            "unsafe_action": False, "approval_bypass": False, "probes_executed": False,
        }
    tasks["10_prompt_injection"] = t10

    def t11():
        a = base.passing_assurance()
        req, ident, imp = base.request(), base.identity(), base.low_impact()
        guard = optim.LoopGuard()
        r = None
        computed = 0
        for _ in range(5):
            k = guard.key(req.action, req.target, ident.requester_id, imp.score)
            if guard.seen(k):
                continue  # identical call -> deterministic cache hit, no rework
            r = wf.govern(req, ident, a, imp)
            computed += 1
        m = opt_pack("11_repeated_tool_call", r, "ALLOW",
                     inputs=base.inputs_tokens(req, ident, imp),
                     tool_results=base.evidence_tokens(r), output=out(r),
                     static_tokens=static_for("11_repeated_tool_call"),
                     turns=5, tool_calls=computed, saved_calls=guard.saved_calls)
        return m
    tasks["11_repeated_tool_call"] = t11

    def t12():
        a = base.passing_assurance()
        guard = optim.LoopGuard(max_iterations=32, history_keep=3)
        history = []
        r = None
        for i in range(20):
            r = wf.govern(base.request(trace_id=f"trace-cc-{i}"), base.identity(), a, base.low_impact())
            history.append(r.evidence.to_dict())
        bounded = guard.bounded_history(history)  # deterministic compaction cap
        m = opt_pack("12_context_compaction", r, "ALLOW",
                     inputs=base.inputs_tokens(base.request()),
                     tool_results=base.evidence_tokens(r), output=out(r),
                     static_tokens=static_for("12_context_compaction"),
                     history=estimate_json(bounded), turns=20, tool_calls=20)
        m["compaction_events"] = 1 if bounded["elided"] > 0 else 0
        return m
    tasks["12_context_compaction"] = t12

    return tasks


def main():
    baseline_path = HERE / "baseline" / "baseline_results.json"
    if not baseline_path.exists():
        print("ERROR: run run_baseline.py first (baseline_results.json missing).")
        return 2
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    base_by_task = {t["task"]: t for t in baseline["tasks"]}

    wf = AgentShieldWorkflow()
    dedup_nontool = _dedup_nontool_once()
    tasks = build_tasks(wf, dedup_nontool)

    results = []
    order = list(TASK_GATES.keys())
    for name in order:
        t0 = time.perf_counter()
        m = tasks[name]()
        m["latency_ms"] = round((time.perf_counter() - t0) * 1000, 4)
        b = base_by_task.get(name, {})
        m["baseline_total_approx_tokens"] = b.get("total_approx_tokens")
        m["baseline_decision"] = b.get("decision")
        # Regression oracle: optimized decision MUST equal the baseline decision.
        m["decision_matches_baseline"] = (m["decision"] == b.get("decision"))
        if m["baseline_total_approx_tokens"]:
            m["token_reduction_pct"] = round(
                100.0 * (m["baseline_total_approx_tokens"] - m["total_approx_tokens"])
                / m["baseline_total_approx_tokens"], 1)
        results.append(m)

    # Optimized static (dedup instruction context + a representative gate load).
    opt_static_nontool = dedup_nontool.compact.approx_tokens
    base_static_total = static_context_total(static_context()).approx_tokens

    agg = {
        "tasks": len(results),
        "decision_agreement_vs_expected": sum(1 for r in results if r["decision_matches_expected"]),
        "decision_agreement_vs_baseline": sum(1 for r in results if r.get("decision_matches_baseline", r["task"] == "10_prompt_injection")),
        "unsafe_actions": sum(1 for r in results if r.get("unsafe_action")),
        "approval_bypasses": sum(1 for r in results if r.get("approval_bypass")),
        "min_critical_fact_retention": min(r["critical_fact_retention"] for r in results),
        "total_saved_calls": sum(r.get("saved_calls", 0) for r in results),
        "sum_total_approx_tokens": sum(r["total_approx_tokens"] for r in results),
        "baseline_sum_total_approx_tokens": baseline["aggregate"]["sum_total_approx_tokens"],
        "sum_latency_ms": round(sum(r["latency_ms"] for r in results), 4),
        "duplicate_instruction_blocks_removed": dedup_nontool.duplicate_blocks,
        "static_instruction_tokens_baseline": base_static_total - static_context()["tool_definitions"].approx_tokens,
        "static_instruction_tokens_optimized": opt_static_nontool,
    }
    saved = agg["baseline_sum_total_approx_tokens"] - agg["sum_total_approx_tokens"]
    agg["total_token_reduction"] = saved
    agg["total_token_reduction_pct"] = round(
        100.0 * saved / agg["baseline_sum_total_approx_tokens"], 1)

    summary = {
        "note": (
            "Optimized (Phase 2, low-risk). Token figures are the disclosed "
            "chars/4 approximation, NOT a provider-exact tokenizer. Deterministic "
            "Python governance engine; no LLM in loop. Decisions come from the "
            "unmodified engine and are asserted equal to the recorded baseline."
        ),
        "dedup_expand_reversible": dedup_nontool.is_reversible(),
        "tasks": results,
        "aggregate": agg,
    }

    out_dir = HERE / "optimized"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "optimized_results.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8")

    # Safety gate: fail loudly on any divergence.
    ok = (
        agg["decision_agreement_vs_baseline"] == len(results)
        and agg["unsafe_actions"] == 0
        and agg["approval_bypasses"] == 0
        and agg["min_critical_fact_retention"] == 1.0
    )

    print(json.dumps(agg, indent=2))
    print()
    for r in results:
        red = r.get("token_reduction_pct")
        red_s = f"{red:>5}%" if red is not None else "  n/a"
        flag = "" if r.get("decision_matches_baseline", True) else "  <-- DECISION DIVERGED"
        print(f"  {r['task']:<28} {str(r['decision'])[:9]:<9} "
              f"{r['total_approx_tokens']:>7} tok  (base {r.get('baseline_total_approx_tokens')})  "
              f"-{red_s}{flag}")
    print(f"\nSafety gate: {'PASS' if ok else 'FAIL'}")
    print("Wrote evals/optimized/optimized_results.json")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
