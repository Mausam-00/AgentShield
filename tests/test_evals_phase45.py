"""Tests for the Phase 4 (routing/caching/subagents) and Phase 5 (governance)
layers, plus the composed final harness. Standard-library unittest only; no
network, no secrets, no URLs.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
for p in (str(ROOT), str(EVALS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import routing as rt  # noqa: E402
import governance as gov  # noqa: E402
import run_final as rf  # noqa: E402


class RouterTests(unittest.TestCase):
    def test_low_read_only_routes_economy(self):
        r = rt.ModelRouter()
        sig = rt.RouteSignals(read_only=True, impact_score=25, production=False)
        self.assertEqual(r.tier(sig), rt.ECONOMY)

    def test_risky_paths_route_premium(self):
        r = rt.ModelRouter()
        for sig in (
            rt.RouteSignals(False, 25, False),                       # write
            rt.RouteSignals(True, 88, False),                        # high impact
            rt.RouteSignals(True, 25, True),                         # production
            rt.RouteSignals(True, 25, False, security_sensitive=True),
        ):
            self.assertEqual(r.tier(sig), rt.PREMIUM)

    def test_is_safe_route_rejects_economy_on_non_allow(self):
        r = rt.ModelRouter()
        sig = rt.RouteSignals(True, 25, False)
        self.assertFalse(r.is_safe_route(rt.ECONOMY, "DENY", sig))
        self.assertTrue(r.is_safe_route(rt.ECONOMY, "ALLOW", sig))
        self.assertTrue(r.is_safe_route(rt.PREMIUM, "DENY", sig))


class SafeCacheTests(unittest.TestCase):
    def _key(self, version):
        return rt.canonical_key(
            action="read_config", target="t", requester_id="svc",
            impact_score=25, posture="PASS", policy_version=version,
            read_only=True, production=False, approval_state="none")

    def test_hit_returns_same_and_counts(self):
        c = rt.SafeCache()
        k = self._key("v1")
        v1, hit1 = c.get_or_compute(k, lambda: "ALLOW")
        v2, hit2 = c.get_or_compute(k, lambda: "SHOULD-NOT-RECOMPUTE")
        self.assertFalse(hit1)
        self.assertTrue(hit2)
        self.assertEqual(v2, "ALLOW")
        self.assertEqual(c.hit_rate, 0.5)

    def test_policy_version_change_misses(self):
        c = rt.SafeCache()
        c.get_or_compute(self._key("v1"), lambda: "ALLOW")
        _v, hit = c.get_or_compute(self._key("v2"), lambda: "RECOMPUTED")
        self.assertFalse(hit)


class IsolationTests(unittest.TestCase):
    def test_no_context_bleed(self):
        ctx = rt.isolate(["a", "b", "c"], 100, 200)
        ctx[0].private["x"] = 1
        self.assertTrue(rt.no_context_bleed(ctx))
        self.assertNotIn("x", ctx[1].private)
        self.assertEqual(ctx[0].total_tokens, 300)


class BudgetTests(unittest.TestCase):
    def test_warn_then_ok(self):
        b = gov.TokenBudget(per_task_limit=100, session_limit=10000, warn_ratio=0.8)
        self.assertEqual(b.charge("t", 50), gov.OK)
        self.assertEqual(b.charge("t", 90), gov.WARN)

    def test_per_task_stop(self):
        b = gov.TokenBudget(per_task_limit=100, session_limit=10000)
        self.assertEqual(b.charge("t", 101), gov.STOP)
        self.assertTrue(b.stopped())

    def test_session_stop(self):
        b = gov.TokenBudget(per_task_limit=10000, session_limit=100)
        b.charge("t", 80)
        self.assertEqual(b.charge("t", 80), gov.STOP)
        self.assertTrue(b.stopped())


class TelemetryEvidenceTests(unittest.TestCase):
    def test_records_and_totals(self):
        tm = gov.Telemetry()
        tm.record(task="a", tokens=10)
        tm.record(task="b", tokens=15)
        self.assertEqual(tm.total("tokens"), 25)
        self.assertEqual(len(tm.records), 2)

    def test_efficiency_evidence_shape(self):
        ev = gov.efficiency_evidence(
            baseline_sum=100, phase2_sum=80, phase3_sum=70, final_sum=60,
            cost_baseline=40, cost_routed=20, cache_hit_rate=0.5,
            budget_events=[], telemetry=gov.Telemetry())
        self.assertEqual(ev["token_reduction_pct_vs_baseline"], 40.0)
        self.assertEqual(ev["relative_cost_reduction_pct"], 50.0)


class FinalHarnessTests(unittest.TestCase):
    def test_composed_safety_gate_passes(self):
        self.assertEqual(rf.main(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
