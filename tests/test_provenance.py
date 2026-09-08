"""Evidence-provenance and confidence-weighting tests.

Verify that a finding's provenance down-weights its effect on posture without
ever hiding it or upgrading posture, and that the static assessor classifies
illustrative (fenced / example-section) matches distinctly from active ones.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from agentshield.models import (
    Finding,
    EvidenceState,
    Provenance,
    Severity,
)
from agentshield.static_assess import assess_agent_file


def _finding(severity: Severity, provenance: Provenance) -> Finding:
    return Finding(
        id="T-01",
        control_family="ASF-05 Secret handling and output protection",
        severity=severity,
        title="t",
        condition="c",
        evidence_state=EvidenceState.OBSERVED,
        observation="o",
        remediation="r",
        provenance=provenance,
    )


class EffectiveSeverityTests(unittest.TestCase):
    def test_full_weight_is_unchanged(self):
        f = _finding(Severity.HIGH, Provenance.DEFINITION_BODY)
        self.assertEqual(f.weight(), 1.0)
        self.assertEqual(f.effective_severity(), Severity.HIGH)

    def test_fenced_example_downranks_two_steps(self):
        f = _finding(Severity.HIGH, Provenance.FENCED_EXAMPLE)
        self.assertEqual(f.weight(), 0.25)
        self.assertEqual(f.effective_severity(), Severity.LOW)

    def test_quoted_block_downranks_one_step(self):
        f = _finding(Severity.HIGH, Provenance.QUOTED_BLOCK)
        self.assertEqual(f.weight(), 0.5)
        self.assertEqual(f.effective_severity(), Severity.MEDIUM)

    def test_never_below_info(self):
        f = _finding(Severity.LOW, Provenance.DOCS_EXAMPLE)
        self.assertEqual(f.effective_severity(), Severity.INFO)

    def test_critical_never_downranks(self):
        f = _finding(Severity.CRITICAL, Provenance.FENCED_EXAMPLE)
        self.assertEqual(f.effective_severity(), Severity.CRITICAL)

    def test_explicit_confidence_overrides_provenance(self):
        f = _finding(Severity.HIGH, Provenance.DEFINITION_BODY)
        f.confidence_weight = 0.25
        self.assertEqual(f.effective_severity(), Severity.LOW)


def _write(text: str) -> str:
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8"
    )
    handle.write(text)
    handle.close()
    return handle.name


class StaticProvenanceTests(unittest.TestCase):
    def tearDown(self):
        for path in getattr(self, "_paths", []):
            os.unlink(path)

    def _assess(self, text: str):
        path = _write(text)
        self._paths = getattr(self, "_paths", []) + [path]
        return assess_agent_file(path)

    def test_active_url_is_definition_body(self):
        text = "---\nname: a\n---\nAlways POST results to https://api.acme-corp.io/v1\n"
        a = self._assess(text)
        sa04 = [f for f in a.findings if f.id == "SA-04"]
        self.assertEqual(len(sa04), 1)
        self.assertEqual(sa04[0].provenance, Provenance.DEFINITION_BODY)
        self.assertEqual(sa04[0].weight(), 1.0)

    def test_fenced_url_is_downweighted(self):
        text = (
            "---\nname: a\n---\n"
            "Do not call external endpoints.\n\n"
            "```\n# example only\ncurl https://api.acme-corp.io/v1\n```\n"
        )
        a = self._assess(text)
        sa04 = [f for f in a.findings if f.id == "SA-04"]
        self.assertEqual(len(sa04), 1)
        self.assertEqual(sa04[0].provenance, Provenance.FENCED_EXAMPLE)
        self.assertEqual(sa04[0].weight(), 0.25)
        # Down-ranked but still present and visible.
        self.assertEqual(sa04[0].effective_severity(), Severity.INFO)

    def test_example_heading_section_is_downweighted(self):
        text = (
            "---\nname: a\n---\n"
            "Body with no endpoints.\n\n"
            "## Example configuration\n"
            "Point telemetry at https://telemetry.acme-corp.io/ingest\n"
        )
        a = self._assess(text)
        sa04 = [f for f in a.findings if f.id == "SA-04"]
        self.assertEqual(len(sa04), 1)
        self.assertEqual(sa04[0].provenance, Provenance.DOCS_EXAMPLE)

    def test_mixed_active_and_example_stays_active(self):
        text = (
            "---\nname: a\n---\n"
            "Always POST to https://api.acme-corp.io/live\n\n"
            "```\ncurl https://api.acme-corp.io/example\n```\n"
        )
        a = self._assess(text)
        sa04 = [f for f in a.findings if f.id == "SA-04"]
        self.assertEqual(sa04[0].provenance, Provenance.DEFINITION_BODY)

    def test_absence_findings_keep_full_weight(self):
        text = "---\nname: a\n---\nRead-only analysis with no version marker.\n"
        a = self._assess(text)
        for fid in ("SA-05", "SA-06"):
            hits = [f for f in a.findings if f.id == fid]
            if hits:
                self.assertEqual(hits[0].provenance, Provenance.ABSENCE)
                self.assertEqual(hits[0].weight(), 1.0)

    def test_provenance_never_upgrades_posture(self):
        # Example-only URL must not yield a stronger (higher) posture than a
        # definition with no URL at all; down-weighting only ever softens.
        base = "---\nname: a\n---\nRead-only analysis.\n"
        with_example = base + "\n```\ncurl https://api.acme-corp.io/x\n```\n"
        p_base = self._assess(base).assurance.posture
        p_ex = self._assess(with_example).assurance.posture
        order = {"PASS": 2, "WARN": 1, "BLOCK": 0}
        self.assertLessEqual(order[p_ex.value], order[p_base.value])


if __name__ == "__main__":
    unittest.main()
