"""HTML report security and behavior tests (behaviors 18, 19, 21 support).

Loads the report generator from the skill scripts directory and verifies
escaping, redaction, self-containment, explicit-trigger separation, and correct
mapping from workflow evidence.
"""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

import fixtures as fx

from agentshield import AgentShieldWorkflow, workflow_to_report


ROOT = Path(__file__).resolve().parents[1]
GEN_PATH = (
    ROOT
    / ".github"
    / "skills"
    / "agentshield-html-report"
    / "scripts"
    / "generate_report.py"
)


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_report", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _base_report(**overrides):
    data = {
        "trace_id": "trace-xyz",
        "timestamp_utc": "2026-01-01T00:00:00Z",
        "mode": "GOVERN",
        "simulation": True,
        "subject": {"name": "synthetic-agent", "owner": "owner", "sponsor": "sponsor"},
        "assurance": {
            "posture": "WARN",
            "score": 72,
            "coverage": 0.8,
            "confidence": "MEDIUM",
            "audit_version": "v1",
            "definition_hash": "abc",
            "tool_manifest_hash": "def",
        },
        "runtime": {
            "decision": "APPROVE",
            "policy_version": "v1",
            "action": "add_disk",
            "target": "synthetic-target",
            "purpose": "demo",
            "environment": "production",
            "operational_impact_score": 60,
            "nothing_reached_target": True,
        },
        "findings": [],
        "coverage_limitations": [],
        "observations": ["synthetic observation"],
        "hypotheses": [],
        "policy_matches": [],
        "approval": None,
        "plan": None,
        "validation": None,
        "evidence_summary": {"outcome": "decision:APPROVE", "reason_codes": []},
        "limitations": [],
        "accountability_statement": "Owner remains accountable.",
    }
    data.update(overrides)
    return data


class EscapingTests(unittest.TestCase):
    def test_19_values_are_html_escaped(self):
        data = _base_report(
            observations=["<script>alert('xss')</script>"],
            subject={"name": "<b>evil</b>", "owner": None, "sponsor": None},
        )
        doc = GEN.build_html(data)
        self.assertNotIn("<script>alert", doc)
        self.assertIn("&lt;script&gt;", doc)
        self.assertIn("&lt;b&gt;evil&lt;/b&gt;", doc)

    def test_19_secrets_are_redacted(self):
        # Unit level: redaction replaces credential-like keys recursively.
        redacted = GEN.redact(
            {
                "name": "synthetic-agent",
                "api_key": "SHOULD-NOT-APPEAR",
                "password": "SHOULD-NOT-APPEAR",
                "nested": {"client_secret": "SHOULD-NOT-APPEAR"},
            }
        )
        self.assertEqual(redacted["api_key"], "[REDACTED]")
        self.assertEqual(redacted["password"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["client_secret"], "[REDACTED]")

        # Document level: no secret value survives into rendered output.
        data = _base_report()
        data["subject"] = {
            "name": "synthetic-agent",
            "owner": "owner",
            "sponsor": "sponsor",
            "api_key": "SHOULD-NOT-APPEAR",
            "password": "SHOULD-NOT-APPEAR",
            "nested": {"client_secret": "SHOULD-NOT-APPEAR"},
        }
        doc = GEN.build_html(data)
        self.assertNotIn("SHOULD-NOT-APPEAR", doc)

    def test_no_network_or_scripts_in_output(self):
        doc = GEN.build_html(_base_report())
        lowered = doc.lower()
        for token in ("<script", "http://", "https://", "javascript:", "<iframe"):
            self.assertNotIn(token, lowered)

    def test_unsafe_output_fails_closed(self):
        # Inject an unsafe token that survives escaping only if a bug exists;
        # here we call the guard directly to prove it raises.
        with self.assertRaises(GEN.ReportError):
            GEN._assert_self_contained("<html><script>bad()</script></html>")

    def test_missing_optional_evidence_renders_placeholder(self):
        data = _base_report(runtime=None)
        data["subject"] = {"name": "synthetic-agent", "owner": None, "sponsor": None}
        doc = GEN.build_html(data)
        self.assertIn("No evidence available", doc)

    def test_pass_is_not_certification_present(self):
        doc = GEN.build_html(_base_report())
        self.assertIn("PASS is not certification", doc)

    def test_posture_and_decision_are_separate_sections(self):
        doc = GEN.build_html(_base_report())
        self.assertIn("Assurance posture", doc)
        self.assertIn("Runtime decision", doc)

    def test_invalid_posture_rejected(self):
        data = _base_report()
        data["assurance"]["posture"] = "GREAT"
        with self.assertRaises(GEN.ReportError):
            GEN.build_html(data)

    def test_missing_required_field_rejected(self):
        data = _base_report()
        del data["assurance"]
        with self.assertRaises(GEN.ReportError):
            GEN.build_html(data)


class ExplicitTriggerTests(unittest.TestCase):
    def test_18_report_generation_is_separate_from_governance(self):
        # Governing an action must not produce any HTML file on its own.
        wf = AgentShieldWorkflow()
        result = wf.govern(
            fx.request(action="read_config", read_only=True),
            fx.identity(),
            fx.passing_assurance(),
            fx.low_impact(),
        )
        # The workflow returns evidence but no HTML artifact.
        self.assertIsNotNone(result.evidence)
        self.assertFalse(hasattr(result, "html"))

    def test_bridge_maps_evidence_without_inventing(self):
        wf = AgentShieldWorkflow()
        result = wf.govern(
            fx.request(action="read_config", read_only=True),
            fx.identity(),
            fx.passing_assurance(),
            fx.low_impact(),
        )
        report = workflow_to_report(result)
        # Posture and decision are present and separate.
        self.assertEqual(report["assurance"]["posture"], "PASS")
        self.assertEqual(report["runtime"]["decision"], "ALLOW")
        self.assertTrue(report["simulation"])
        # No approval was needed -> stays None, not fabricated.
        self.assertIsNone(report["approval"])
        # Rendered document is valid and self-contained.
        doc = GEN.build_html(report)
        self.assertIn("AgentShield AI", doc)


class EndToEndFileTests(unittest.TestCase):
    def test_generate_writes_valid_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            in_path = os.path.join(tmp, "in.json")
            out_path = os.path.join(tmp, "out.html")
            with open(in_path, "w", encoding="utf-8") as handle:
                json.dump(_base_report(), handle)
            rc = GEN.main(["generate_report.py", in_path, out_path])
            self.assertEqual(rc, 0)
            content = Path(out_path).read_text(encoding="utf-8")
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("SIMULATION", content)


if __name__ == "__main__":
    unittest.main()
