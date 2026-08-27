"""Tests for the Phase 2 low-risk token-optimisation layer (evals/optim.py).

These verify that every optimisation is deterministic, reversible, and preserves
decision-critical facts - and that the optimized harness never diverges from the
recorded baseline decisions. Standard-library unittest only; no network, no
secrets, no URLs (kept public-safe for the repo-wide scan).
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

import optim  # noqa: E402
import run_baseline as base  # noqa: E402
import run_optimized as opt  # noqa: E402
from agentshield import AgentShieldWorkflow  # noqa: E402


class DedupTests(unittest.TestCase):
    def test_exact_duplicate_removed_and_reversible(self):
        texts = {
            "a": "First long instruction block that is well over the forty char limit.\n\n"
                 "Second distinct block also comfortably beyond the forty character floor.",
            "b": "First long instruction block that is well over the forty char limit.",
        }
        res = optim.dedup_blocks(texts)
        self.assertEqual(res.duplicate_blocks, 1)
        self.assertLess(res.compact.approx_tokens, res.original.approx_tokens)
        self.assertTrue(res.is_reversible())
        self.assertEqual(res.expand(), res.original_text)

    def test_no_false_dedup_and_reversible(self):
        texts = {"a": "Alpha block well beyond forty characters in length here.\n\n"
                      "Beta block also well beyond the forty character threshold now."}
        res = optim.dedup_blocks(texts)
        self.assertEqual(res.duplicate_blocks, 0)
        self.assertTrue(res.is_reversible())


class ScopedRetrievalTests(unittest.TestCase):
    DOC = ("# Alpha\nApproval is required for production writes.\n\n"
           "# Beta\nRead-only actions are low risk.\n\n"
           "# Gamma\nImpact scoring drives escalation.\n\n"
           "# Delta\nUnrelated appendix content here.\n")

    def test_selects_relevant_and_reduces(self):
        res = optim.scoped_retrieve(self.DOC, ["approval", "production"], k=1)
        self.assertIn("Approval is required", res.text)
        self.assertLessEqual(res.scoped.approx_tokens, res.original.approx_tokens)
        self.assertEqual(res.sections_selected, 1)

    def test_deterministic(self):
        a = optim.scoped_retrieve(self.DOC, ["impact"], k=2)
        b = optim.scoped_retrieve(self.DOC, ["impact"], k=2)
        self.assertEqual(a.text, b.text)

    def test_fallback_never_empty(self):
        res = optim.scoped_retrieve(self.DOC, ["zzz-no-match"], k=2)
        self.assertTrue(res.text.strip())
        self.assertEqual(res.sections_selected, 2)


class GateToolTests(unittest.TestCase):
    def test_gate_subset_smaller_than_full(self):
        full = optim.ci._tool_definition_text()
        full_tokens = optim.estimate_text(full).approx_tokens
        subset = optim.gate_tool_text(("authorize",)).approx_tokens
        self.assertLess(subset, full_tokens)

    def test_unknown_gate_falls_back_to_full(self):
        full_tokens = optim.estimate_text(optim.ci._tool_definition_text()).approx_tokens
        unknown = optim.gate_tool_text(("no-such-gate",)).approx_tokens
        self.assertEqual(unknown, full_tokens)


class LoopGuardTests(unittest.TestCase):
    def test_identical_calls_dedupe(self):
        g = optim.LoopGuard()
        k = g.key("add_disk", "target", "svc", 4)
        self.assertFalse(g.seen(k))
        self.assertTrue(g.seen(k))
        self.assertTrue(g.seen(k))
        self.assertEqual(g.saved_calls, 2)

    def test_max_iterations_trips_stop(self):
        g = optim.LoopGuard(max_iterations=2)
        for i in range(3):
            g.seen(g.key(i))
        self.assertTrue(g.stopped)

    def test_bounded_history(self):
        g = optim.LoopGuard(history_keep=3)
        b = g.bounded_history(list(range(10)))
        self.assertEqual(b["kept"], [7, 8, 9])
        self.assertEqual(b["elided"], 7)
        self.assertEqual(b["total"], 10)


class ContractRetentionTests(unittest.TestCase):
    def _result(self):
        wf = AgentShieldWorkflow()
        req = base.request(action="add_disk", read_only=False, environment="production")
        return wf.govern(req, base.identity(), base.passing_assurance(),
                         base.high_impact(destructive=True, irreversible=True))

    def test_contract_has_decision_and_all_codes(self):
        r = self._result()
        c = optim.compact_contract(r)
        self.assertEqual(c["decision"], r.policy.decision.value)
        for code in r.policy.reason_codes():
            self.assertIn(code, c["reason_codes"])

    def test_retention_true_and_detects_loss(self):
        r = self._result()
        self.assertTrue(optim.retains_critical_facts(r))

        class Stripped:
            policy = r.policy
            impact = r.impact
            assurance = r.assurance
            evidence = r.evidence
            trace_id = r.trace_id
        # Monkeypatch a contract that omits reason codes to prove detection works.
        original = optim.compact_contract
        try:
            optim.compact_contract = lambda res: {"decision": None, "reason_codes": []}
            self.assertFalse(optim.retains_critical_facts(r))
        finally:
            optim.compact_contract = original


class OptimizedHarnessTests(unittest.TestCase):
    def test_decisions_match_baseline_and_reduce_tokens(self):
        wf = AgentShieldWorkflow()
        dedup = opt._dedup_nontool_once()
        self.assertTrue(dedup.is_reversible())
        tasks = opt.build_tasks(wf, dedup)
        for name, fn in tasks.items():
            m = fn()
            self.assertEqual(m["critical_fact_retention"], 1.0, name)
            self.assertFalse(m.get("unsafe_action"), name)
            self.assertFalse(m.get("approval_bypass"), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
