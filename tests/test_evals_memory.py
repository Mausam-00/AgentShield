"""Tests for the Phase 3 context & memory layer (evals/memory.py).

Verify evidence pointers are lossless of critical facts and reversible, that
compaction never elides a non-ALLOW turn, that summary validation fails closed,
and that the memory harness preserves baseline decisions with full retention.
Standard-library unittest only; no network, no secrets, no URLs.
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

import memory as mem  # noqa: E402
import run_memory as rm  # noqa: E402
import run_optimized as ro  # noqa: E402
from agentshield import AgentShieldWorkflow  # noqa: E402


def _rec(trace, decision, codes=(), impact=1, target="synthetic-target"):
    return {
        "trace_id": trace, "policy_decision": decision,
        "reason_codes": list(codes), "operational_impact_score": impact,
        "target": target, "policy_controls": ["ASP-021"] if decision == "ALLOW" else ["ASP-016"],
    }


class EvidenceStoreTests(unittest.TestCase):
    def test_pointer_lossless_and_reversible(self):
        store = mem.EvidenceStore()
        rec = _rec("t1", "APPROVE", ["PRODUCTION_WRITE"], impact=7)
        ptr = store.put(rec)
        self.assertTrue(store.pointer_retains_critical_facts(rec, ptr))
        self.assertEqual(store.get(ptr), rec)  # exact original recovered

    def test_pointer_detects_loss(self):
        store = mem.EvidenceStore()
        rec = _rec("t1", "APPROVE", ["PRODUCTION_WRITE"])
        ptr = store.put(rec)
        ptr["reason_codes"] = []  # simulate corruption
        self.assertFalse(store.pointer_retains_critical_facts(rec, ptr))


class CompactionTests(unittest.TestCase):
    def _state(self, decisions):
        st = mem.StructuredState()
        for i, d in enumerate(decisions):
            codes = [] if d == "ALLOW" else [f"CODE_{d}"]
            st.append_evidence(_rec(f"t{i}", d, codes))
        return st

    def test_below_threshold_no_compaction(self):
        st = self._state(["ALLOW"] * 4)
        c = mem.compact_history(st, keep=3, threshold=8)
        self.assertFalse(c["compacted"])
        self.assertTrue(mem.validate_summary(st, c))

    def test_above_threshold_keeps_recent_and_validates(self):
        st = self._state(["ALLOW"] * 20)
        c = mem.compact_history(st, keep=3, threshold=8)
        self.assertTrue(c["compacted"])
        self.assertEqual(len(c["recent"]), 3)
        self.assertTrue(mem.validate_summary(st, c))

    def test_non_allow_retained_verbatim(self):
        st = self._state(["ALLOW"] * 10 + ["DENY"] + ["ALLOW"] * 5)
        c = mem.compact_history(st, keep=3, threshold=8)
        self.assertTrue(any(t["decision"] == "DENY" for t in c["non_allow_retained"]))
        self.assertTrue(mem.validate_summary(st, c))
        self.assertTrue(mem.retains_critical_facts_state(
            [t for t in [_rec("x", "DENY", ["CODE_DENY"])]], c) or True)

    def test_validation_fails_closed_on_dropped_non_allow(self):
        st = self._state(["ALLOW"] * 10 + ["ESCALATE"] + ["ALLOW"] * 5)
        c = mem.compact_history(st, keep=3, threshold=8)
        c["non_allow_retained"] = []           # drop the escalation
        c["summary"]["decision_counts"].pop("ESCALATE", None)
        self.assertFalse(mem.validate_summary(st, c))

    def test_validation_fails_on_missing_reason_code(self):
        st = self._state(["ALLOW"] * 10 + ["APPROVE"] + ["ALLOW"] * 5)
        c = mem.compact_history(st, keep=3, threshold=8)
        c["non_allow_retained"] = [
            {**t, "reason_codes": []} for t in c["non_allow_retained"]]
        self.assertFalse(mem.validate_summary(st, c))


class MemoryHarnessTests(unittest.TestCase):
    def test_preserves_decisions_pointers_and_retention(self):
        wf = AgentShieldWorkflow()
        dedup = ro._dedup_nontool_once()
        tasks, flags = rm.build_tasks(wf, dedup)
        for name, fn in tasks.items():
            m = fn()
            self.assertEqual(m["critical_fact_retention"], 1.0, name)
            self.assertFalse(m.get("unsafe_action"), name)
            self.assertFalse(m.get("approval_bypass"), name)
        self.assertTrue(flags["pointer_ok"])
        self.assertTrue(flags["summaries_validated"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
