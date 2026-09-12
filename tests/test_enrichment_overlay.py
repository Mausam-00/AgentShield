"""The LLM enrichment overlay must never move a deterministic verdict.

AgentShield is a deterministic governance tool: a non-deterministic narrator may
enrich wording, but it must not change the assurance score, posture, coverage,
confidence, the finding SET, the runtime decision, or the red-team/RAI verdicts.
These tests pin that contract on ``agent_llm._merge`` directly (no model call).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import agent_llm  # noqa: E402


def _base() -> dict:
    return {
        "subject": {"name": "demo"},
        "assurance": {
            "posture": "WARN",
            "score": 82,
            "coverage": 1.0,
            "confidence": "MEDIUM",
        },
        "runtime": {"decision": "ALLOW"},
        "findings": [
            {"id": "SA-03", "severity": "MEDIUM", "control_family": "ASF-03",
             "title": "Over-privilege", "observation": "det obs", "remediation": "det rem"},
        ],
        "redteam": {"posture_signal": "WARN", "defense_coverage": 0.9, "notes": []},
        "responsible_ai": {"posture": "WARN", "findings": []},
    }


class TestDeterministicAuthoritativeOverlay(unittest.TestCase):
    def test_model_cannot_change_assurance_or_runtime(self):
        patch = {
            "assurance": {"posture": "PASS", "score": 20, "coverage": 0.1, "confidence": "HIGH"},
            "runtime": {"decision": "DENY"},
        }
        out = agent_llm._merge(_base(), patch)
        self.assertEqual(out["assurance"]["score"], 82)
        self.assertEqual(out["assurance"]["posture"], "WARN")
        self.assertEqual(out["assurance"]["coverage"], 1.0)
        self.assertEqual(out["assurance"]["confidence"], "MEDIUM")
        self.assertEqual(out["runtime"]["decision"], "ALLOW")

    def test_model_cannot_add_or_remove_findings(self):
        patch = {"findings": [
            {"id": "AI-99", "severity": "CRITICAL", "title": "invented",
             "observation": "model made this up", "remediation": "x"},
        ]}
        out = agent_llm._merge(_base(), patch)
        ids = {f["id"] for f in out["findings"] if f["id"] != "EXEC"}
        self.assertEqual(ids, {"SA-03"})  # invented finding dropped, det finding kept

    def test_model_may_enrich_wording_of_existing_finding(self):
        patch = {"findings": [
            {"id": "SA-03", "severity": "LOW", "control_family": "WRONG",
             "title": "nicer title", "observation": "clearer observation",
             "remediation": "clearer remediation"},
        ]}
        out = agent_llm._merge(_base(), patch)
        det = next(f for f in out["findings"] if f["id"] == "SA-03")
        # Wording is enriched...
        self.assertEqual(det["title"], "nicer title")
        self.assertEqual(det["observation"], "clearer observation")
        # ...but severity/family (verdict-bearing fields) stay deterministic.
        self.assertEqual(det["severity"], "MEDIUM")
        self.assertEqual(det["control_family"], "ASF-03")

    def test_model_cannot_change_redteam_or_rai_verdict(self):
        patch = {
            "redteam": {"posture_signal": "PASS", "notes": ["some note"]},
            "responsible_ai": {"posture": "BLOCK", "findings": [
                {"id": "X", "severity": "HIGH", "title": "t", "observation": "o", "remediation": "r"}]},
        }
        out = agent_llm._merge(_base(), patch)
        self.assertEqual(out["redteam"]["posture_signal"], "WARN")
        self.assertEqual(out["redteam"]["notes"], ["some note"])  # narrative allowed
        self.assertEqual(out["responsible_ai"]["posture"], "WARN")
        self.assertEqual(out["responsible_ai"]["findings"], [])

    def test_executive_summary_is_additive_only(self):
        out = agent_llm._merge(_base(), {"executive_summary": "high-level summary"})
        self.assertEqual(out["findings"][0]["id"], "EXEC")
        self.assertEqual(out["assurance"]["score"], 82)


if __name__ == "__main__":
    unittest.main()
