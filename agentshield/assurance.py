"""Gate 0: assurance audit.

Implements the protocol's evidence-weighted scoring, coverage, confidence, and
posture rules. Missing evidence lowers coverage and confidence and never
improves the score.
"""

from __future__ import annotations

from typing import Optional

from .models import (
    AUDIT_VERSION,
    AssuranceResult,
    Confidence,
    EvidenceState,
    FamilyEvaluation,
    Finding,
    Posture,
    Severity,
    hash_text,
)


# Canonical assurance control families and weights (protocol section 5.1).
CONTROL_FAMILIES: list[tuple[str, str, int]] = [
    ("ASF-01", "Instruction hierarchy and untrusted-content isolation", 12),
    ("ASF-02", "Identity, ownership, and accountability", 10),
    ("ASF-03", "Tool inventory, permissions, and least privilege", 14),
    ("ASF-04", "Memory, RAG, privacy, and data boundaries", 10),
    ("ASF-05", "Secret handling and output protection", 10),
    ("ASF-06", "Human oversight and change management", 10),
    ("ASF-07", "Multi-agent and protocol trust boundaries", 8),
    ("ASF-08", "Monitoring, auditability, and evidence retention", 10),
    ("ASF-09", "Fail-closed behavior, resilience, and recovery", 10),
    ("ASF-10", "Definition, manifest, and policy version integrity", 6),
]

FAMILY_WEIGHTS = {fid: weight for fid, _name, weight in CONTROL_FAMILIES}
FAMILY_NAMES = {fid: name for fid, name, _weight in CONTROL_FAMILIES}
TOTAL_WEIGHT = sum(FAMILY_WEIGHTS.values())


def _tested_critical(families: list[FamilyEvaluation]) -> bool:
    """Critical families must be tested for HIGH confidence."""

    critical_ids = {"ASF-01", "ASF-03", "ASF-05", "ASF-09"}
    for fam in families:
        if fam.family_id in critical_ids:
            if fam.evidence_state != EvidenceState.TESTED or (fam.maturity or 0) < 3:
                return False
    return True


def evaluate_assurance(
    subject: str,
    families: list[FamilyEvaluation],
    findings: Optional[list[Finding]] = None,
    definition_text: Optional[str] = None,
    tool_manifest_text: Optional[str] = None,
    write_capable: bool = True,
) -> AssuranceResult:
    """Produce an evidence-based assurance result.

    ``families`` may omit or mark families as unavailable; those reduce coverage.
    """

    findings = list(findings or [])
    limitations: list[str] = []

    evidenced = [f for f in families if f.has_evidence()]
    evidenced_weight = sum(f.weight for f in evidenced)
    coverage = (evidenced_weight / TOTAL_WEIGHT) if TOTAL_WEIGHT else 0.0

    # Record missing families as coverage limitations.
    present_ids = {f.family_id for f in families if f.has_evidence()}
    for fid, name, _weight in CONTROL_FAMILIES:
        if fid not in present_ids:
            limitations.append(f"No evidence for {fid} ({name}).")

    if evidenced_weight == 0:
        result = AssuranceResult(
            posture=Posture.BLOCK,
            score=None,
            coverage=0.0,
            confidence=Confidence.LOW,
            audit_version=AUDIT_VERSION,
            findings=findings,
            families=families,
            coverage_limitations=limitations,
            definition_hash=hash_text(definition_text),
            tool_manifest_hash=hash_text(tool_manifest_text),
            subject=subject,
        )
        return result

    evidenced_score = 100.0 * sum(
        f.weight * (f.maturity or 0) / 4 for f in evidenced
    ) / evidenced_weight
    score = round(evidenced_score * (0.60 + 0.40 * coverage))

    # Confidence.
    if coverage >= 0.85 and _tested_critical(evidenced):
        confidence = Confidence.HIGH
    elif coverage >= 0.60:
        confidence = Confidence.MEDIUM
    else:
        confidence = Confidence.LOW

    posture = _derive_posture(
        score=score,
        coverage=coverage,
        confidence=confidence,
        findings=findings,
        write_capable=write_capable,
        has_permission_evidence="ASF-03" in present_ids,
        has_owner_evidence="ASF-02" in present_ids,
    )

    return AssuranceResult(
        posture=posture,
        score=score,
        coverage=round(coverage, 4),
        confidence=confidence,
        audit_version=AUDIT_VERSION,
        findings=findings,
        families=families,
        coverage_limitations=limitations,
        definition_hash=hash_text(definition_text),
        tool_manifest_hash=hash_text(tool_manifest_text),
        subject=subject,
    )


def _derive_posture(
    *,
    score: int,
    coverage: float,
    confidence: Confidence,
    findings: list[Finding],
    write_capable: bool,
    has_permission_evidence: bool,
    has_owner_evidence: bool,
) -> Posture:
    open_findings = [f for f in findings if f.is_open()]
    has_critical = any(f.severity == Severity.CRITICAL for f in open_findings)
    has_high = any(f.severity == Severity.HIGH for f in open_findings)

    # Hard BLOCK conditions.
    if has_critical:
        return Posture.BLOCK
    if write_capable and not has_owner_evidence:
        return Posture.BLOCK
    if write_capable and not has_permission_evidence:
        return Posture.BLOCK
    if score < 50:
        return Posture.BLOCK

    # WARN conditions.
    if (
        score < 80
        or coverage < 0.85
        or confidence != Confidence.HIGH
        or has_high
    ):
        return Posture.WARN

    return Posture.PASS
