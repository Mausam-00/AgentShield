"""Tests for the Responsible AI companion agent scoring and reporting."""

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agentshield import (
    PillarEvaluation,
    RaiFinding,
    default_pillars,
    evaluate_responsible_ai,
    rai_to_report,
)
from agentshield.models import Confidence, Posture, Severity
from agentshield.responsible_ai import PILLARS, TOTAL_WEIGHT


class ScoringTests(unittest.TestCase):
    def test_total_weight_is_100(self):
        self.assertEqual(TOTAL_WEIGHT, 100)
        self.assertEqual(len(PILLARS), 6)

    def test_full_tested_maturity_passes(self):
        r = evaluate_responsible_ai(
            "strong-system", default_pillars(maturity=4, tested=True)
        )
        self.assertEqual(r.posture, Posture.PASS)
        self.assertEqual(r.confidence, Confidence.HIGH)
        self.assertEqual(r.coverage, 1.0)
        self.assertGreaterEqual(r.score, 80)

    def test_no_evidence_fails_closed(self):
        r = evaluate_responsible_ai("empty", default_pillars(maturity=None))
        self.assertEqual(r.posture, Posture.BLOCK)
        self.assertIsNone(r.score)
        self.assertEqual(r.confidence, Confidence.LOW)
        self.assertEqual(len(r.coverage_limitations), 6)

    def test_missing_fairness_blocks(self):
        pillars = default_pillars(maturity=4, tested=True)
        # Remove fairness evidence (RAI-01) entirely.
        pillars[0] = PillarEvaluation("RAI-01", pillars[0].name, pillars[0].weight, None)
        r = evaluate_responsible_ai("no-fairness", pillars)
        self.assertEqual(r.posture, Posture.BLOCK)

    def test_missing_safety_blocks(self):
        pillars = default_pillars(maturity=4, tested=True)
        pillars[1] = PillarEvaluation("RAI-02", pillars[1].name, pillars[1].weight, None)
        r = evaluate_responsible_ai("no-safety", pillars)
        self.assertEqual(r.posture, Posture.BLOCK)

    def test_critical_finding_blocks(self):
        finding = RaiFinding(
            id="R-1", pillar_id="RAI-01", severity=Severity.CRITICAL,
            title="Unmitigated discriminatory outcome",
            observation="Fictional disparate impact with no mitigation.",
            remediation="Measure and mitigate group disparities.",
        )
        r = evaluate_responsible_ai(
            "biased", default_pillars(maturity=4, tested=True), findings=[finding]
        )
        self.assertEqual(r.posture, Posture.BLOCK)

    def test_partial_coverage_warns(self):
        pillars = default_pillars(maturity=3, tested=True)
        # Drop two non-critical pillars to lower coverage below 0.85.
        pillars[3] = PillarEvaluation("RAI-04", pillars[3].name, pillars[3].weight, None)
        pillars[4] = PillarEvaluation("RAI-05", pillars[4].name, pillars[4].weight, None)
        r = evaluate_responsible_ai("partial", pillars)
        self.assertEqual(r.posture, Posture.WARN)
        self.assertLess(r.coverage, 0.85)

    def test_missing_evidence_never_raises_score(self):
        full = evaluate_responsible_ai("a", default_pillars(maturity=4, tested=True))
        pillars = default_pillars(maturity=4, tested=True)
        pillars[5] = PillarEvaluation("RAI-06", pillars[5].name, pillars[5].weight, None)
        partial = evaluate_responsible_ai("b", pillars)
        self.assertLessEqual(partial.score, full.score)


class ReportBridgeTests(unittest.TestCase):
    def test_report_schema_shape(self):
        r = evaluate_responsible_ai("sys", default_pillars(maturity=2))
        report = rai_to_report(r)
        for key in (
            "trace_id", "timestamp_utc", "mode", "simulation", "subject",
            "assurance", "runtime", "findings", "coverage_limitations",
            "observations", "hypotheses", "policy_matches", "approval",
            "plan", "validation", "evidence_summary", "limitations",
            "accountability_statement",
        ):
            self.assertIn(key, report)
        self.assertIsNone(report["runtime"])  # assessment is not authorization
        self.assertEqual(len(report["gates"]), 6)
        self.assertEqual(report["assurance"]["audit_version"], r.rai_version)

    def test_report_renders_in_dashboard(self):
        dash = _load_dashboard()
        finding = RaiFinding(
            id="R-2", pillar_id="RAI-05", severity=Severity.MEDIUM,
            title="No user disclosure of AI use",
            observation="No transparency artifact provided.",
            remediation="Add a clear AI-use disclosure.",
        )
        r = evaluate_responsible_ai(
            "demo-system", default_pillars(maturity=3, tested=True), findings=[finding]
        )
        html = dash.build_html(rai_to_report(r))
        self.assertIn("demo-system", html)
        self.assertIn("Control Families", html)
        for token in ("http://", "https://", "<script", "<iframe"):
            self.assertNotIn(token, html.lower())


def _load_dashboard():
    path = (ROOT / ".github" / "skills" / "agentshield-html-report"
            / "scripts" / "dashboard_report.py")
    spec = importlib.util.spec_from_file_location("dashboard_report", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
