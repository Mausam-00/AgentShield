"""Prototype: SARIF 2.1.0 export for CI/CD and GitHub code scanning.

Turning assessment output into SARIF lets AgentShield run inside a pull-request
pipeline and surface findings directly in GitHub's Security tab. This makes the
tool *usable* today, not just demonstrable.

The exporter maps :class:`Finding` objects (assurance) and Responsible AI
findings onto SARIF ``results``, and encodes the assurance posture / runtime
decision as run-level properties so a CI gate can fail the build.
"""

from __future__ import annotations

from typing import Optional

from .models import AssuranceResult, Finding, Posture, Severity

SARIF_VERSION = "2.1.0"
# Schema identifier only (no live URL, per the package's public-safety rules).
SARIF_SCHEMA = "sarif-schema-2.1.0.json"
TOOL_NAME = "AgentShield AI"
TOOL_VERSION = "1.0.0"

# SARIF only defines error / warning / note / none.
_SEVERITY_TO_LEVEL = {
    Severity.CRITICAL: "error",
    Severity.HIGH: "error",
    Severity.MEDIUM: "warning",
    Severity.LOW: "note",
    Severity.INFO: "note",
}
# security-severity is a GitHub extension (0.0-10.0) driving the Security tab.
_SEVERITY_TO_SCORE = {
    Severity.CRITICAL: "9.5",
    Severity.HIGH: "8.0",
    Severity.MEDIUM: "5.0",
    Severity.LOW: "2.0",
    Severity.INFO: "0.0",
}


def _rule(finding: Finding) -> dict:
    return {
        "id": finding.id,
        "name": finding.title.replace(" ", ""),
        "shortDescription": {"text": finding.title},
        "fullDescription": {"text": finding.condition or finding.title},
        "defaultConfiguration": {"level": _SEVERITY_TO_LEVEL[finding.severity]},
        "properties": {
            "security-severity": _SEVERITY_TO_SCORE[finding.severity],
            "control-family": finding.control_family,
            "tags": ["agentshield", "ai-governance", finding.control_family.split()[0]],
        },
        "help": {"text": finding.remediation},
    }


def _result(finding: Finding, artifact_uri: str) -> dict:
    message = finding.observation
    if finding.impact:
        message += f"\nImpact: {finding.impact}"
    message += f"\nRemediation: {finding.remediation}"
    return {
        "ruleId": finding.id,
        "level": _SEVERITY_TO_LEVEL[finding.severity],
        "message": {"text": message},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": artifact_uri},
                    "region": {"startLine": 1},
                }
            }
        ],
        "properties": {
            "evidence-state": finding.evidence_state.value,
            "control-family": finding.control_family,
        },
    }


def assurance_to_sarif(
    assurance: AssuranceResult,
    artifact_uri: str,
    *,
    extra_findings: Optional[list[Finding]] = None,
    runtime_decision: Optional[str] = None,
) -> dict:
    """Build a SARIF 2.1.0 log from an assurance result and its findings."""

    findings = list(assurance.findings) + list(extra_findings or [])
    # De-duplicate rules by id while preserving order.
    rules: dict[str, dict] = {}
    for f in findings:
        rules.setdefault(f.id, _rule(f))

    run = {
        "tool": {
            "driver": {
                "name": TOOL_NAME,
                "version": TOOL_VERSION,
                "rules": list(rules.values()),
            }
        },
        "results": [_result(f, artifact_uri) for f in findings],
        "properties": {
            "assurance_posture": assurance.posture.value,
            "assurance_score": assurance.score,
            "coverage": assurance.coverage,
            "confidence": assurance.confidence.value,
            "runtime_decision": runtime_decision,
            "note": "Assurance posture is not runtime authorization.",
        },
    }
    return {"version": SARIF_VERSION, "$schema": SARIF_SCHEMA, "runs": [run]}


def gate_should_fail(
    assurance: AssuranceResult,
    *,
    fail_on: str = "BLOCK",
) -> bool:
    """CI gate helper: should the pipeline fail for this posture?

    ``fail_on`` is ``BLOCK`` (default) or ``WARN`` (stricter).
    """

    order = {Posture.PASS: 0, Posture.WARN: 1, Posture.BLOCK: 2}
    threshold = {"BLOCK": 2, "WARN": 1}.get(fail_on.upper(), 2)
    return order[assurance.posture] >= threshold
