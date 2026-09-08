"""Compliance framework-mapping tests.

Verify the mapping is complete, versioned, honest (never asserts certification),
and that coverage status is derived only from existing assurance evidence.
"""

from __future__ import annotations

import unittest

from agentshield.assurance import CONTROL_FAMILIES, evaluate_assurance
from agentshield.compliance import (
    COMPLIANCE_MAP_VERSION,
    FAMILY_TO_CONTROLS,
    FRAMEWORKS,
    STATUS_EVIDENCED,
    STATUS_GAP,
    STATUS_UNEVIDENCED,
    build_compliance_coverage,
    compliance_to_report,
)
from agentshield.models import (
    AssuranceResult,
    Confidence,
    EvidenceState,
    FamilyEvaluation,
    Finding,
    Posture,
    Severity,
)

ALLOWED_STATUSES = {
    "Evidenced",
    "Partial",
    "Declared (not tested)",
    "Gap",
    "Unevidenced",
}

FORBIDDEN_WORDS = ("certified", "certification", "compliant", "attestation", "approved")


def _assurance(families, findings=None):
    return AssuranceResult(
        posture=Posture.WARN,
        score=60,
        coverage=0.5,
        confidence=Confidence.MEDIUM,
        audit_version="v1",
        findings=findings or [],
        families=families,
    )


class MappingCompletenessTests(unittest.TestCase):
    def test_every_family_is_mapped(self):
        for fid, _name, _weight in CONTROL_FAMILIES:
            self.assertIn(fid, FAMILY_TO_CONTROLS)
            self.assertTrue(FAMILY_TO_CONTROLS[fid])

    def test_mapping_is_versioned(self):
        self.assertTrue(COMPLIANCE_MAP_VERSION.startswith("agentshield-compliance-map-"))

    def test_expected_frameworks_present(self):
        keys = set(FRAMEWORKS)
        self.assertIn("owasp_llm", keys)
        self.assertIn("nist_ai_rmf", keys)
        self.assertIn("eu_ai_act", keys)

    def test_control_refs_point_to_known_frameworks(self):
        for refs in FAMILY_TO_CONTROLS.values():
            for ref in refs:
                self.assertIn(ref.framework, FRAMEWORKS)


class CoverageStatusTests(unittest.TestCase):
    def test_no_evidence_is_unevidenced(self):
        coverage = build_compliance_coverage(_assurance(families=[]))
        for fw in coverage:
            for c in fw.controls:
                self.assertEqual(c.status, STATUS_UNEVIDENCED)

    def test_tested_family_is_evidenced(self):
        families = [
            FamilyEvaluation(fid, name, weight, 4, EvidenceState.TESTED)
            for fid, name, weight in CONTROL_FAMILIES
        ]
        coverage = build_compliance_coverage(_assurance(families=families))
        statuses = {c.status for fw in coverage for c in fw.controls}
        self.assertIn(STATUS_EVIDENCED, statuses)

    def test_open_medium_finding_creates_gap(self):
        families = [
            FamilyEvaluation(fid, name, weight, 4, EvidenceState.TESTED)
            for fid, name, weight in CONTROL_FAMILIES
        ]
        finding = Finding(
            id="F1",
            control_family="ASF-01 Instruction hierarchy and untrusted-content isolation",
            severity=Severity.HIGH,
            title="t",
            condition="c",
            evidence_state=EvidenceState.OBSERVED,
            observation="o",
            remediation="r",
        )
        coverage = build_compliance_coverage(
            _assurance(families=families, findings=[finding])
        )
        owasp = next(fw for fw in coverage if fw.key == "owasp_llm")
        llm01 = next(c for c in owasp.controls if c.control_id == "LLM01")
        self.assertEqual(llm01.status, STATUS_GAP)

    def test_downweighted_finding_does_not_force_gap(self):
        # A fenced-example HIGH finding on ASF-01 has effective severity LOW and
        # must not degrade the mapped control to Gap.
        from agentshield.models import Provenance

        families = [
            FamilyEvaluation(fid, name, weight, 4, EvidenceState.TESTED)
            for fid, name, weight in CONTROL_FAMILIES
        ]
        finding = Finding(
            id="F1",
            control_family="ASF-01 Instruction hierarchy and untrusted-content isolation",
            severity=Severity.HIGH,
            title="t",
            condition="c",
            evidence_state=EvidenceState.OBSERVED,
            observation="o",
            remediation="r",
            provenance=Provenance.FENCED_EXAMPLE,
        )
        coverage = build_compliance_coverage(
            _assurance(families=families, findings=[finding])
        )
        owasp = next(fw for fw in coverage if fw.key == "owasp_llm")
        llm01 = next(c for c in owasp.controls if c.control_id == "LLM01")
        self.assertNotEqual(llm01.status, STATUS_GAP)


class HonestyTests(unittest.TestCase):
    def test_statuses_are_from_allowed_set(self):
        families = [
            FamilyEvaluation(fid, name, weight, 3, EvidenceState.DECLARED)
            for fid, name, weight in CONTROL_FAMILIES
        ]
        report = compliance_to_report(_assurance(families=families))
        for fw in report["frameworks"]:
            for c in fw["controls"]:
                self.assertIn(c["status"], ALLOWED_STATUSES)

    def test_no_certification_language(self):
        families = [
            FamilyEvaluation(fid, name, weight, 4, EvidenceState.TESTED)
            for fid, name, weight in CONTROL_FAMILIES
        ]
        report = compliance_to_report(_assurance(families=families))
        # Control statuses and notes must never assert a compliance claim; the
        # disclaimer is allowed to use these words in negation.
        for fw in report["frameworks"]:
            for c in fw["controls"]:
                blob = (str(c["status"]) + " " + str(c["note"])).lower()
                for word in FORBIDDEN_WORDS:
                    self.assertNotIn(word, blob)

    def test_report_shape(self):
        report = compliance_to_report(_assurance(families=[]))
        self.assertEqual(report["map_version"], COMPLIANCE_MAP_VERSION)
        self.assertIn("disclaimer", report)
        self.assertTrue(report["frameworks"])
        for fw in report["frameworks"]:
            self.assertIn("summary", fw)
            self.assertIn("controls", fw)


if __name__ == "__main__":
    unittest.main()
