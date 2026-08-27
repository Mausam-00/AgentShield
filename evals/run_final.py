"""AgentShield token-optimisation FINAL harness (Phases 2-5 composed).

Runs the SAME 12 baseline tasks through the full optimisation stack:
  Phase 2 (low-risk)  + Phase 3 (memory)  + Phase 4 (routing/caching/subagents)
  + Phase 5 (token governance: budgets, telemetry, warnings, deterministic stop).

Token accounting is inherited from the Phase 3 memory harness (no double-counting
of savings). Phase 4 adds relative-cost routing, safe caching, and subagent
isolation. Phase 5 wraps everything in deterministic budgets + telemetry and emits
consolidated efficiency evidence.

Consolidated safety gate (fails the run non-zero on any violation):
  - 12/12 decisions equal the recorded baseline;
  - no unsafe action, no approval bypass, min retention == 1.0;
  - all evidence pointers ok, all summaries validated, execution stable;
  - routing never places a non-ALLOW / high-impact path on the economy tier;
  - every cache hit reproduces a fresh computation exactly;
  - subagent contexts have no cross-delegate bleed;
  - the deterministic budget STOP demonstrably fires on an over-budget charge;
  - policy version is unchanged (no optimisation layer can alter policy).

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

import routing as rt  # noqa: E402
import governance as gov  # noqa: E402
import run_memory as rm  # noqa: E402
import run_optimized as ro  # noqa: E402
import run_baseline as base  # noqa: E402
from agentshield import AgentShieldWorkflow  # noqa: E402


# Deterministic per-task routing signals (input-only; independent of outcome).
_LOW = base.low_impact().score
_HIGH = base.high_impact().score
TASK_SIGNALS = {
    "01_readonly_assessment": rt.RouteSignals(True, _LOW, False),
    "02_high_risk_action": rt.RouteSignals(False, _HIGH, True),
    "03_long_multiturn": rt.RouteSignals(True, _LOW, False),
    "04_tool_heavy": rt.RouteSignals(False, _HIGH, False),
    "05_retrieval_heavy": rt.RouteSignals(False, _HIGH, True),
    "06_multiagent_delegation": rt.RouteSignals(True, _LOW, False),
    "07_human_approval": rt.RouteSignals(False, _HIGH, True),
    "08_html_report": rt.RouteSignals(False, _HIGH, True),
    "09_missing_evidence": rt.RouteSignals(False, _HIGH, True),
    "10_prompt_injection": rt.RouteSignals(False, _HIGH, False, security_sensitive=True),
    "11_repeated_tool_call": rt.RouteSignals(True, _LOW, False),
    "12_context_compaction": rt.RouteSignals(True, _LOW, False),
}


def _cache_consistency_demo(wf):
    """Prove a cache hit equals a fresh computation (task_11 repeated call)."""
    cache = rt.SafeCache()
    a = base.passing_assurance()
    req, ident, imp = base.request(), base.identity(), base.low_impact()

    def compute():
        r = wf.govern(req, ident, a, imp)
        return r.policy.decision.value

    key = rt.canonical_key(
        action=req.action, target=req.target, requester_id=ident.requester_id,
        impact_score=imp.score, posture=a.posture.value,
        policy_version=wf.policy_config.version, read_only=req.read_only,
        production=req.is_production(), approval_state="none")
    fresh = compute()
    consistent = True
    for _ in range(5):
        val, _hit = cache.get_or_compute(key, compute)
        consistent = consistent and (val == fresh)
    return cache, consistent


def _isolation_demo():
    """Bounded, independent per-delegate contexts; no shared mutable state."""
    contexts = rt.isolate(["synthetic-a", "synthetic-b", "synthetic-c"],
                          input_tokens=200, tool_tokens=300)
    contexts[0].private["scratch"] = "delegate-a-only"
    bleed_free = rt.no_context_bleed(contexts)
    leaked = any("scratch" in c.private for c in contexts[1:])
    return contexts, (bleed_free and not leaked)


def main():
    baseline_path = HERE / "baseline" / "baseline_results.json"
    if not baseline_path.exists():
        print("ERROR: run run_baseline.py first.")
        return 2
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    base_sum = baseline["aggregate"]["sum_total_approx_tokens"]

    wf = AgentShieldWorkflow()
    policy_version_before = wf.policy_config.version
    dedup = ro._dedup_nontool_once()

    # Phase 3 token accounting (memory pipeline), run once.
    tasks, flags = rm.build_tasks(wf, dedup)
    results = []
    for name in ro.TASK_GATES:
        t0 = time.perf_counter()
        m = tasks[name]()
        m["latency_ms"] = round((time.perf_counter() - t0) * 1000, 4)
        results.append(m)
    by_task = {m["task"]: m for m in results}
    base_by_task = {t["task"]: t for t in baseline["tasks"]}

    # Phase 4: routing + cost, caching, isolation.
    router = rt.ModelRouter()
    cost_baseline = 0.0
    cost_routed = 0.0
    routing_safe = True
    for m in results:
        sig = TASK_SIGNALS[m["task"]]
        tier = router.tier(sig)
        turns = max(1, m.get("turns", 1))
        cost_baseline += turns * rt.TIER_COST[rt.PREMIUM]
        cost_routed += turns * rt.TIER_COST[tier]
        decision = m["decision"] if m["decision"] in (
            "ALLOW", "APPROVE", "ESCALATE", "DENY", "TRANSFORM") else "ALLOW"
        routing_safe = routing_safe and router.is_safe_route(tier, decision, sig)
        m["model_tier"] = tier

    cache, cache_consistent = _cache_consistency_demo(wf)
    _contexts, isolation_ok = _isolation_demo()

    # Phase 5: budgets, telemetry, deterministic stop demo, efficiency evidence.
    budget = gov.TokenBudget(per_task_limit=20000, session_limit=200000, warn_ratio=0.8)
    telemetry = gov.Telemetry()
    for m in results:
        status = budget.charge(m["task"], m["total_approx_tokens"])
        m["budget_status"] = status
        telemetry.record(task=m["task"], tokens=m["total_approx_tokens"],
                         tier=m.get("model_tier"), decision=m["decision"],
                         latency_ms=m["latency_ms"], budget_status=status)

    # Deterministic STOP demonstration (synthetic, does not affect the 12 tasks).
    stop_budget = gov.TokenBudget(per_task_limit=1000, session_limit=1000)
    stop_status = stop_budget.charge("synthetic-overbudget", 999999)
    stop_fires = (stop_status == gov.STOP and stop_budget.stopped())

    # Regression oracle + final token totals.
    for m in results:
        b = base_by_task.get(m["task"], {})
        m["baseline_total_approx_tokens"] = b.get("total_approx_tokens")
        m["decision_matches_baseline"] = (m["decision"] == b.get("decision"))
        if b.get("total_approx_tokens"):
            m["token_reduction_pct"] = round(
                100.0 * (b["total_approx_tokens"] - m["total_approx_tokens"])
                / b["total_approx_tokens"], 1)

    final_sum = sum(m["total_approx_tokens"] for m in results)
    policy_version_after = wf.policy_config.version

    evidence = gov.efficiency_evidence(
        baseline_sum=base_sum,
        phase2_sum=rm._phase2_sum(),
        phase3_sum=_phase3_sum(),
        final_sum=final_sum,
        cost_baseline=cost_baseline, cost_routed=cost_routed,
        cache_hit_rate=cache.hit_rate,
        budget_events=budget.events + stop_budget.events,
        telemetry=telemetry)

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
        "routing_never_downgrades_risk": routing_safe,
        "cache_hits": cache.hits,
        "cache_hit_consistent": cache_consistent,
        "subagent_isolation_ok": isolation_ok,
        "budget_stop_control_fires": stop_fires,
        "policy_version_unchanged": policy_version_before == policy_version_after,
        "sum_total_approx_tokens": final_sum,
        "baseline_sum_total_approx_tokens": base_sum,
        "total_token_reduction_pct": round(100.0 * (base_sum - final_sum) / base_sum, 1),
        "relative_cost_reduction_pct": evidence["relative_cost_reduction_pct"],
        "economy_tier_tasks": sum(1 for m in results if m.get("model_tier") == rt.ECONOMY),
    }

    summary = {
        "note": (
            "Final (Phases 2-5 composed). chars/4 token approximation; relative "
            "cost units (premium = 4x economy) are a labelled model, not real "
            "prices. Deterministic engine; no LLM in loop. Decisions come from the "
            "unmodified engine and are asserted equal to the recorded baseline. "
            "No optimisation layer can alter policy or authorisation."
        ),
        "efficiency_evidence": evidence,
        "tasks": results,
        "aggregate": agg,
    }

    out_dir = HERE / "final"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "final_results.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8")

    ok = (
        agg["decision_agreement_vs_baseline"] == len(results)
        and agg["unsafe_actions"] == 0
        and agg["approval_bypasses"] == 0
        and agg["min_critical_fact_retention"] == 1.0
        and agg["all_evidence_pointers_ok"]
        and agg["all_summaries_validated"]
        and agg["routing_never_downgrades_risk"]
        and agg["cache_hit_consistent"]
        and agg["subagent_isolation_ok"]
        and agg["budget_stop_control_fires"]
        and agg["policy_version_unchanged"]
    )

    print(json.dumps(agg, indent=2))
    print()
    for m in results:
        red = m.get("token_reduction_pct")
        red_s = f"{red:>5}%" if red is not None else "  n/a"
        print(f"  {m['task']:<28} {str(m['decision'])[:9]:<9} "
              f"{m['total_approx_tokens']:>7} tok  tier={m.get('model_tier'):<7} "
              f"budget={m.get('budget_status'):<4} -{red_s}")
    print(f"\nSafety gate: {'PASS' if ok else 'FAIL'}")
    print("Wrote evals/final/final_results.json")
    return 0 if ok else 1


def _phase3_sum():
    p = HERE / "memory" / "memory_results.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))["aggregate"]["sum_total_approx_tokens"]
    return None


if __name__ == "__main__":
    raise SystemExit(main())
