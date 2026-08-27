"""AgentShield token-optimisation MEMORY harness (Phase 3, context & memory).

Re-runs the SAME 12 baseline tasks against the SAME unmodified engine, applying
the Phase 2 low-risk layer PLUS the Phase 3 memory layer:

  - evidence pointers  : bulky audit records move to a retrievable store; only a
                         critical-fact-preserving pointer stays in context.
  - structured state   : per-turn normalised records.
  - compaction         : older redundant ALLOW turns summarised (threshold-based).
  - summary validation : fail-closed - if a summary cannot be proven lossless of
                         critical facts, the task keeps full detail.

Safety oracle (fails the run non-zero on any violation):
  - every decision equals the recorded baseline decision (12/12);
  - no unsafe action, no approval bypass;
  - min critical-fact retention == 1.0;
  - every evidence pointer reproduces its record's critical facts;
  - every compaction passes summary validation;
  - execution stability: a second run yields identical token totals.

Standard library plus the local agentshield package only. No new dependency.
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
import memory as mem  # noqa: E402
import run_baseline as base  # noqa: E402
import run_optimized as ro  # noqa: E402
from token_estimate import estimate_json, estimate_text, empty  # noqa: E402
from context_inventory import static_context, static_context_total  # noqa: E402
from agentshield import (  # noqa: E402
    AgentShieldWorkflow, ApprovalBinding, ApprovalRecord, ApprovalResult,
    PlanStep, ObservedOutcome, build_safe_plan, validate_outcome,
    run_static_redteam, evaluate_responsible_ai, default_pillars,
    redteam_to_report_section, rai_to_report, workflow_to_report,
)


def _pointer_tokens(store, result):
    """Evidence-pointer token estimate + a flag that critical facts survive."""
    rec = result.evidence.to_dict() if result.evidence else {}
    pointer = store.put(rec)
    ok = store.pointer_retains_critical_facts(rec, pointer)
    return estimate_json(pointer), ok, json.dumps(pointer, default=str)


def build_tasks(wf, dedup_nontool):
    nontool_tokens = dedup_nontool.compact.approx_tokens

    def static_for(name):
        return nontool_tokens + optim.gate_tool_text(ro.TASK_GATES[name]).approx_tokens

    def out(result):
        return optim.contract_tokens(result)

    flags = {"pointer_ok": True, "summaries_validated": True}
    tasks = {}

    def simple(name, expected, req, ident, imp, gates_turns=(1, 2)):
        store = mem.EvidenceStore()
        r = wf.govern(req, ident, imp[0], imp[1])
        ptok, ok, ptxt = _pointer_tokens(store, r)
        flags["pointer_ok"] = flags["pointer_ok"] and ok
        m = ro.opt_pack(name, r, expected,
                        inputs=base.inputs_tokens(req, ident, imp[1]),
                        tool_results=ptok, output=out(r),
                        static_tokens=static_for(name),
                        turns=gates_turns[0], tool_calls=gates_turns[1],
                        extra_facts=(ptxt,))
        m["evidence_pointer_ok"] = ok
        return m

    tasks["01_readonly_assessment"] = lambda: simple(
        "01_readonly_assessment", "ALLOW",
        base.request(action="read_config", read_only=True),
        base.identity(), (base.passing_assurance(), base.low_impact()))

    tasks["02_high_risk_action"] = lambda: simple(
        "02_high_risk_action", "APPROVE",
        base.request(action="add_disk", read_only=False, environment="production"),
        base.identity(), (base.passing_assurance(),
                          base.high_impact(destructive=True, irreversible=True)))

    def t03():
        a = base.passing_assurance()
        state = mem.StructuredState()
        r = None
        store = mem.EvidenceStore()
        records = []
        for i in range(6):
            req = base.request(trace_id=f"trace-mt-{i}", action="read_config", read_only=True)
            r = wf.govern(req, base.identity(), a, base.low_impact())
            rec = r.evidence.to_dict()
            records.append(rec)
            state.append_evidence(rec)
        compacted = mem.compact_history(state, keep=3, threshold=8)
        validated = mem.validate_summary(state, compacted)
        flags["summaries_validated"] = flags["summaries_validated"] and validated
        ptok, ok, _ = _pointer_tokens(store, r)
        flags["pointer_ok"] = flags["pointer_ok"] and ok
        hist_blob = json.dumps(compacted, default=str)
        m = ro.opt_pack("03_long_multiturn", r, "ALLOW",
                        inputs=base.inputs_tokens(base.request()),
                        tool_results=ptok, output=out(r),
                        static_tokens=static_for("03_long_multiturn"),
                        history=mem.history_tokens(compacted),
                        turns=6, tool_calls=6, extra_facts=(hist_blob,))
        m["summary_validated"] = validated
        m["state_retention_ok"] = mem.retains_critical_facts_state(records, compacted)
        return m
    tasks["03_long_multiturn"] = t03

    def t04():
        subject = "synthetic-tool-heavy"
        a = base.passing_assurance(subject)
        req = base.request(action="add_disk", read_only=False)
        ident, imp = base.identity(), base.high_impact()
        r = wf.govern(req, ident, a, imp)
        store = mem.EvidenceStore()
        ptok, ok, ptxt = _pointer_tokens(store, r)
        flags["pointer_ok"] = flags["pointer_ok"] and ok
        plan = build_safe_plan(req, ["add_disk"], [PlanStep(
            "s1", "add_disk", "synthetic-target", "add capacity", "verify attached",
            "detach disk", "stop if attach fails", "add_disk")])
        observed = ObservedOutcome(action="add_disk", target="synthetic-target", outcome="success")
        validation = validate_outcome("add_disk", "synthetic-target", plan, observed)
        rt = run_static_redteam("synthetic definition", subject=subject)
        rai = evaluate_responsible_ai(subject, default_pillars(4, tested=True), findings=[])
        # Evidence -> pointer; other distinct tool outputs stay (not audit records).
        tool_results = (ptok
                        .add(estimate_json(base._as_dict(plan)))
                        .add(estimate_json(base._as_dict(validation)))
                        .add(estimate_json(redteam_to_report_section(rt)))
                        .add(estimate_json(rai_to_report(rai))))
        m = ro.opt_pack("04_tool_heavy", r, "ESCALATE",
                        inputs=base.inputs_tokens(req, ident, imp),
                        tool_results=tool_results, output=out(r),
                        static_tokens=static_for("04_tool_heavy"),
                        turns=6, tool_calls=6, extra_facts=(ptxt,))
        m["evidence_pointer_ok"] = ok
        return m
    tasks["04_tool_heavy"] = t04

    def t05():
        a = base.passing_assurance()
        req = base.request(action="add_disk", read_only=False, environment="production")
        r = wf.govern(req, base.identity(), a, base.high_impact())
        store = mem.EvidenceStore()
        ptok, ok, ptxt = _pointer_tokens(store, r)
        flags["pointer_ok"] = flags["pointer_ok"] and ok
        scoped = optim.scoped_retrieve(base.full_protocol_text(),
                                       query_terms=[req.action, "write", "production",
                                                    "approval", "impact"], k=4)
        m = ro.opt_pack("05_retrieval_heavy", r, "APPROVE",
                        inputs=base.inputs_tokens(req, base.identity(), base.high_impact()),
                        retrieved=estimate_text(scoped.text),
                        tool_results=ptok, output=out(r),
                        static_tokens=static_for("05_retrieval_heavy"),
                        turns=1, tool_calls=2, extra_facts=(scoped.text, ptxt))
        m["evidence_pointer_ok"] = ok
        return m
    tasks["05_retrieval_heavy"] = t05

    def t06():
        subjects = ["synthetic-a", "synthetic-b", "synthetic-c"]
        store = mem.EvidenceStore()
        last = None
        per_delegate = empty()
        ok_all = True
        for s in subjects:
            a = base.passing_assurance(s)
            last = wf.govern(base.request(trace_id=f"trace-{s}"), base.identity(), a, base.low_impact())
            ptok, ok, _ = _pointer_tokens(store, last)
            ok_all = ok_all and ok
            per_delegate = per_delegate.add(ptok)  # pointer per delegate, not full record
        flags["pointer_ok"] = flags["pointer_ok"] and ok_all
        m = ro.opt_pack("06_multiagent_delegation", last, "ALLOW",
                        inputs=base.inputs_tokens(base.request()),
                        tool_results=optim.contract_tokens(last), output=out(last),
                        static_tokens=static_for("06_multiagent_delegation"),
                        extra_static=per_delegate,
                        turns=len(subjects), tool_calls=len(subjects) * 2)
        m["evidence_pointer_ok"] = ok_all
        return m
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
        store = mem.EvidenceStore()
        p1, ok1, _ = _pointer_tokens(store, first)
        p2, ok2, ptxt = _pointer_tokens(store, second)
        flags["pointer_ok"] = flags["pointer_ok"] and ok1 and ok2
        m = ro.opt_pack("07_human_approval", second, "APPROVE",
                        inputs=base.inputs_tokens(req, ident, imp, binding),
                        tool_results=p1.add(p2), output=out(second),
                        static_tokens=static_for("07_human_approval"),
                        turns=2, tool_calls=3, extra_facts=(ptxt,))
        m["evidence_pointer_ok"] = ok1 and ok2
        return m
    tasks["07_human_approval"] = t07

    def t08():
        a = base.passing_assurance("synthetic-report")
        req = base.request(action="add_disk", read_only=False, environment="production")
        r = wf.govern(req, base.identity(), a, base.high_impact())
        report = workflow_to_report(r, simulation=True)
        store = mem.EvidenceStore()
        ptok, ok, ptxt = _pointer_tokens(store, r)
        flags["pointer_ok"] = flags["pointer_ok"] and ok
        m = ro.opt_pack("08_html_report", r, "APPROVE",
                        inputs=base.inputs_tokens(req, base.identity(), base.high_impact()),
                        tool_results=ptok, output=optim.contract_tokens(r),
                        static_tokens=static_for("08_html_report"),
                        turns=2, tool_calls=3, extra_facts=(ptxt,))
        m["report_json_approx_tokens"] = estimate_json(report).approx_tokens
        m["evidence_pointer_ok"] = ok
        return m
    tasks["08_html_report"] = t08

    def t09():
        a = base.partial_assurance()
        req = base.request(action="add_disk", read_only=False, environment="production")
        r = wf.govern(req, base.identity(), a, base.high_impact())
        store = mem.EvidenceStore()
        ptok, ok, ptxt = _pointer_tokens(store, r)
        flags["pointer_ok"] = flags["pointer_ok"] and ok
        m = ro.opt_pack("09_missing_evidence", r, "DENY",
                        inputs=base.inputs_tokens(req, base.identity(), base.high_impact()),
                        tool_results=ptok, output=out(r),
                        static_tokens=static_for("09_missing_evidence"),
                        turns=1, tool_calls=2, extra_facts=(ptxt,))
        m["evidence_pointer_ok"] = ok
        return m
    tasks["09_missing_evidence"] = t09

    def t10():
        rt = run_static_redteam(base.INJECTION_DEFINITION, subject="synthetic-injection")
        section = redteam_to_report_section(rt)
        static_tokens = static_for("10_prompt_injection")
        in_tok = estimate_text(base.INJECTION_DEFINITION).approx_tokens
        sec_tok = estimate_json(section).approx_tokens
        return {
            "task": "10_prompt_injection",
            "decision": "N/A (static red-team, no runtime authorization)",
            "expected_decision": "N/A", "decision_matches_expected": True,
            "assurance_posture": None, "reason_codes": [],
            "static_context_approx_tokens": static_tokens,
            "input_approx_tokens": in_tok, "retrieved_approx_tokens": 0,
            "tool_result_approx_tokens": sec_tok, "history_approx_tokens": 0,
            "output_approx_tokens": sec_tok, "extra_static_approx_tokens": 0,
            "total_input_approx_tokens": static_tokens + in_tok,
            "total_approx_tokens": static_tokens + in_tok + 2 * sec_tok,
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
        store = mem.EvidenceStore()
        r = None
        computed = 0
        for _ in range(5):
            k = guard.key(req.action, req.target, ident.requester_id, imp.score)
            if guard.seen(k):
                continue
            r = wf.govern(req, ident, a, imp)
            computed += 1
        ptok, ok, ptxt = _pointer_tokens(store, r)
        flags["pointer_ok"] = flags["pointer_ok"] and ok
        m = ro.opt_pack("11_repeated_tool_call", r, "ALLOW",
                        inputs=base.inputs_tokens(req, ident, imp),
                        tool_results=ptok, output=out(r),
                        static_tokens=static_for("11_repeated_tool_call"),
                        turns=5, tool_calls=computed, saved_calls=guard.saved_calls,
                        extra_facts=(ptxt,))
        m["evidence_pointer_ok"] = ok
        return m
    tasks["11_repeated_tool_call"] = t11

    def t12():
        a = base.passing_assurance()
        state = mem.StructuredState()
        store = mem.EvidenceStore()
        records = []
        r = None
        for i in range(20):
            r = wf.govern(base.request(trace_id=f"trace-cc-{i}"), base.identity(), a, base.low_impact())
            rec = r.evidence.to_dict()
            records.append(rec)
            state.append_evidence(rec)
        compacted = mem.compact_history(state, keep=3, threshold=8)
        validated = mem.validate_summary(state, compacted)
        flags["summaries_validated"] = flags["summaries_validated"] and validated
        ptok, ok, _ = _pointer_tokens(store, r)
        flags["pointer_ok"] = flags["pointer_ok"] and ok
        hist_blob = json.dumps(compacted, default=str)
        m = ro.opt_pack("12_context_compaction", r, "ALLOW",
                        inputs=base.inputs_tokens(base.request()),
                        tool_results=ptok, output=out(r),
                        static_tokens=static_for("12_context_compaction"),
                        history=mem.history_tokens(compacted),
                        turns=20, tool_calls=20, extra_facts=(hist_blob,))
        m["summary_validated"] = validated
        m["compaction_events"] = 1 if compacted.get("compacted") else 0
        m["state_retention_ok"] = mem.retains_critical_facts_state(records, compacted)
        return m
    tasks["12_context_compaction"] = t12

    return tasks, flags


def _run_once(wf, dedup):
    tasks, flags = build_tasks(wf, dedup)
    results = []
    for name in ro.TASK_GATES:
        t0 = time.perf_counter()
        m = tasks[name]()
        m["latency_ms"] = round((time.perf_counter() - t0) * 1000, 4)
        results.append(m)
    return results, flags


def main():
    baseline_path = HERE / "baseline" / "baseline_results.json"
    if not baseline_path.exists():
        print("ERROR: run run_baseline.py first.")
        return 2
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    base_by_task = {t["task"]: t for t in baseline["tasks"]}

    wf = AgentShieldWorkflow()
    dedup = ro._dedup_nontool_once()

    results, flags = _run_once(wf, dedup)
    # Execution stability: a second independent run must match token totals.
    results2, _ = _run_once(wf, dedup)
    stable = all(a["total_approx_tokens"] == b["total_approx_tokens"]
                 for a, b in zip(results, results2))

    for m in results:
        b = base_by_task.get(m["task"], {})
        m["baseline_total_approx_tokens"] = b.get("total_approx_tokens")
        m["baseline_decision"] = b.get("decision")
        m["decision_matches_baseline"] = (m["decision"] == b.get("decision"))
        if b.get("total_approx_tokens"):
            m["token_reduction_pct"] = round(
                100.0 * (b["total_approx_tokens"] - m["total_approx_tokens"])
                / b["total_approx_tokens"], 1)

    sum_tokens = sum(m["total_approx_tokens"] for m in results)
    base_sum = baseline["aggregate"]["sum_total_approx_tokens"]
    agg = {
        "tasks": len(results),
        "decision_agreement_vs_baseline": sum(
            1 for m in results
            if m.get("decision_matches_baseline", m["task"] == "10_prompt_injection")),
        "unsafe_actions": sum(1 for m in results if m.get("unsafe_action")),
        "approval_bypasses": sum(1 for m in results if m.get("approval_bypass")),
        "min_critical_fact_retention": min(m["critical_fact_retention"] for m in results),
        "all_evidence_pointers_ok": flags["pointer_ok"],
        "all_summaries_validated": flags["summaries_validated"],
        "state_retention_all_ok": all(
            m.get("state_retention_ok", True) for m in results),
        "execution_stable_across_runs": stable,
        "sum_total_approx_tokens": sum_tokens,
        "baseline_sum_total_approx_tokens": base_sum,
        "phase2_sum_total_approx_tokens": _phase2_sum(),
        "sum_latency_ms": round(sum(m["latency_ms"] for m in results), 4),
    }
    saved = base_sum - sum_tokens
    agg["total_token_reduction"] = saved
    agg["total_token_reduction_pct"] = round(100.0 * saved / base_sum, 1)

    summary = {
        "note": (
            "Optimized (Phase 3, context & memory). chars/4 approximation, NOT a "
            "provider-exact tokenizer. Deterministic engine; no LLM in loop. "
            "Decisions come from the unmodified engine and are asserted equal to "
            "the recorded baseline. Evidence pointers are retrievable; compaction "
            "is summary-validated and fails closed to full detail."
        ),
        "tasks": results,
        "aggregate": agg,
    }

    out_dir = HERE / "memory"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "memory_results.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8")

    ok = (
        agg["decision_agreement_vs_baseline"] == len(results)
        and agg["unsafe_actions"] == 0
        and agg["approval_bypasses"] == 0
        and agg["min_critical_fact_retention"] == 1.0
        and agg["all_evidence_pointers_ok"]
        and agg["all_summaries_validated"]
        and agg["state_retention_all_ok"]
        and agg["execution_stable_across_runs"]
    )

    print(json.dumps(agg, indent=2))
    print()
    for m in results:
        red = m.get("token_reduction_pct")
        red_s = f"{red:>5}%" if red is not None else "  n/a"
        flag = "" if m.get("decision_matches_baseline", True) else "  <-- DIVERGED"
        print(f"  {m['task']:<28} {str(m['decision'])[:9]:<9} "
              f"{m['total_approx_tokens']:>7} tok  (base {m.get('baseline_total_approx_tokens')})  "
              f"-{red_s}{flag}")
    print(f"\nSafety gate: {'PASS' if ok else 'FAIL'}")
    print("Wrote evals/memory/memory_results.json")
    return 0 if ok else 1


def _phase2_sum():
    p = HERE / "optimized" / "optimized_results.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))["aggregate"]["sum_total_approx_tokens"]
    return None


if __name__ == "__main__":
    raise SystemExit(main())
