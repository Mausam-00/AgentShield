"""Responsible AI assessment scoring (companion to AgentShield assurance).

Evidence-based scoring across six publicly documented Responsible AI pillars
(aligned with the public Microsoft Responsible AI Standard and the NIST AI Risk
Management Framework framings). This module is advisory and simulation-only. It
never certifies a system, never authorizes an action, and never invents missing
evidence: absent pillars lower coverage and confidence and never raise the score.

Responsible AI posture (RAI-PASS / RAI-WARN / RAI-BLOCK) is an assurance signal
only. It is deliberately kept separate from any runtime authorization decision,
consistent with the AgentShield separation principle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import Confidence, Posture, Severity, hash_text

RAI_VERSION = "RAI-2026.08"

# Canonical Responsible AI pillars, public framings, and weights.
# id, name, weight
PILLARS: list[tuple[str, str, int]] = [
    ("RAI-01", "Fairness and non-discrimination", 20),
    ("RAI-02", "Reliability and safety", 20),
    ("RAI-03", "Privacy and security", 18),
    ("RAI-04", "Inclusiveness and accessibility", 12),
    ("RAI-05", "Transparency and interpretability", 16),
    ("RAI-06", "Accountability and human oversight", 14),
]

PILLAR_WEIGHTS = {pid: w for pid, _n, w in PILLARS}
PILLAR_NAMES = {pid: n for pid, n, _w in PILLARS}
TOTAL_WEIGHT = sum(PILLAR_WEIGHTS.values())

# Pillars that must be tested (not merely declared) for HIGH confidence.
CRITICAL_PILLARS = {"RAI-01", "RAI-02", "RAI-03"}


@dataclass
class PillarEvaluation:
    """One Responsible AI pillar's maturity, or absence of evidence.

    ``maturity`` is 0..4 when evidence exists (0 absent control, 4 tested and
    effective), or ``None`` when no evidence was provided for the pillar.
    """

    pillar_id: str
    name: str
    weight: int
    maturity: Optional[int]
    tested: bool = False
    note: str = ""
    not_applicable: bool = False
    justification: str = ""

    def has_evidence(self) -> bool:
        return self.maturity is not None

    def is_justified_na(self) -> bool:
        """True when the pillar is marked not-applicable with a real reason."""

        return self.not_applicable and bool(self.justification.strip())

    def counts_for_scoring(self) -> bool:
        return self.has_evidence() and not self.not_applicable


@dataclass
class RaiFinding:
    id: str
    pillar_id: str
    severity: Severity
    title: str
    observation: str
    remediation: str
    hypothesis: Optional[str] = None
    resolved: bool = False

    def is_open(self) -> bool:
        return not self.resolved


@dataclass
class RaiResult:
    posture: Posture
    score: Optional[int]
    coverage: float
    confidence: Confidence
    rai_version: str
    subject: str
    pillars: list[PillarEvaluation] = field(default_factory=list)
    findings: list[RaiFinding] = field(default_factory=list)
    coverage_limitations: list[str] = field(default_factory=list)
    definition_hash: Optional[str] = None

    def open_findings(self) -> list[RaiFinding]:
        return [f for f in self.findings if f.is_open()]


def default_pillars(maturity: Optional[int] = None, tested: bool = False) -> list[PillarEvaluation]:
    """Convenience builder for a full pillar set at a uniform maturity."""

    return [
        PillarEvaluation(pid, name, weight, maturity, tested)
        for pid, name, weight in PILLARS
    ]


def evaluate_responsible_ai(
    subject: str,
    pillars: list[PillarEvaluation],
    findings: Optional[list[RaiFinding]] = None,
    definition_text: Optional[str] = None,
) -> RaiResult:
    """Produce an evidence-based Responsible AI result.

    Missing pillars reduce coverage and are recorded as coverage limitations.
    A completely unevidenced assessment fails closed to RAI-BLOCK.
    """

    findings = list(findings or [])
    limitations: list[str] = []

    na_pillars = [p for p in pillars if p.is_justified_na()]
    na_ids = {p.pillar_id for p in na_pillars}
    na_weight = sum(p.weight for p in na_pillars)
    # A not-applicable pillar is removed from the denominator so a genuinely
    # inapplicable pillar does not depress coverage.
    effective_total = max(TOTAL_WEIGHT - na_weight, 1)

    evidenced = [p for p in pillars if p.counts_for_scoring()]
    evidenced_weight = sum(p.weight for p in evidenced)
    coverage = (evidenced_weight / effective_total) if effective_total else 0.0

    present_ids = {p.pillar_id for p in evidenced}
    # Pillars that are either evidenced or justifiably N/A are "covered" for the
    # fail-closed critical-pillar gate.
    covered_ids = present_ids | na_ids
    for pid, name, _w in PILLARS:
        if pid in na_ids:
            justification = next(p.justification for p in na_pillars if p.pillar_id == pid)
            limitations.append(f"{pid} ({name}) marked not-applicable: {justification}")
        elif pid not in present_ids:
            limitations.append(f"No evidence for {pid} ({name}).")

    if evidenced_weight == 0:
        return RaiResult(
            posture=Posture.BLOCK,
            score=None,
            coverage=0.0,
            confidence=Confidence.LOW,
            rai_version=RAI_VERSION,
            subject=subject,
            pillars=pillars,
            findings=findings,
            coverage_limitations=limitations,
            definition_hash=hash_text(definition_text),
        )

    evidenced_score = 100.0 * sum(
        p.weight * (p.maturity or 0) / 4 for p in evidenced
    ) / evidenced_weight
    score = round(evidenced_score * (0.60 + 0.40 * coverage))

    if coverage >= 0.85 and _critical_tested(evidenced):
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
        present_ids=covered_ids,
    )

    return RaiResult(
        posture=posture,
        score=score,
        coverage=round(coverage, 4),
        confidence=confidence,
        rai_version=RAI_VERSION,
        subject=subject,
        pillars=pillars,
        findings=findings,
        coverage_limitations=limitations,
        definition_hash=hash_text(definition_text),
    )


def _critical_tested(pillars: list[PillarEvaluation]) -> bool:
    for p in pillars:
        if p.pillar_id in CRITICAL_PILLARS:
            if not p.tested or (p.maturity or 0) < 3:
                return False
    return True


def _derive_posture(
    *,
    score: int,
    coverage: float,
    confidence: Confidence,
    findings: list[RaiFinding],
    present_ids: set[str],
) -> Posture:
    open_findings = [f for f in findings if f.is_open()]
    has_critical = any(f.severity == Severity.CRITICAL for f in open_findings)
    has_high = any(f.severity == Severity.HIGH for f in open_findings)

    # Fail-closed BLOCK conditions.
    if has_critical:
        return Posture.BLOCK
    # A safety or fairness pillar with no evidence at all is a hard gap.
    if "RAI-02" not in present_ids or "RAI-01" not in present_ids:
        return Posture.BLOCK
    if score < 50:
        return Posture.BLOCK

    if (
        score < 80
        or coverage < 0.85
        or confidence != Confidence.HIGH
        or has_high
    ):
        return Posture.WARN

    return Posture.PASS


def rai_to_report(result: RaiResult, *, simulation: bool = True) -> dict:
    """Serialize an RaiResult into the AgentShield HTML report schema.

    The six pillars are rendered as the dashboard control-family grid and the
    findings block; the Responsible AI posture maps onto the report posture.
    Runtime is always ``None`` - Responsible AI assessment is not authorization.
    """

    rating = _coverage_rating
    gates = [
        {
            "id": p.pillar_id,
            "name": p.name,
            "rating": rating(p),
        }
        for p in result.pillars
    ]
    findings = [
        {
            "id": f.id,
            "severity": f.severity.value,
            "control_family": f"{f.pillar_id} {PILLAR_NAMES.get(f.pillar_id, '')}".strip(),
            "evidence_state": "Observed",
            "title": f.title,
            "observation": f.observation,
            "remediation": f.remediation,
            "hypothesis": f.hypothesis,
        }
        for f in result.findings
    ]
    return {
        "trace_id": f"rai-{result.subject}",
        "timestamp_utc": None,
        "mode": "ASSESS",
        "simulation": simulation,
        "subject": {"name": result.subject, "owner": None, "sponsor": None},
        "assurance": {
            "posture": result.posture.value,
            "score": result.score,
            "coverage": result.coverage,
            "confidence": result.confidence.value,
            "audit_version": result.rai_version,
            "definition_hash": result.definition_hash,
            "tool_manifest_hash": None,
        },
        "runtime": None,
        "gates": gates,
        "findings": findings,
        "coverage_limitations": list(result.coverage_limitations),
        "observations": [],
        "hypotheses": [],
        "policy_matches": [],
        "approval": None,
        "plan": None,
        "validation": None,
        "evidence_summary": {"records": len(result.findings)},
        "limitations": [
            "Responsible AI assessment is advisory and simulation-only.",
            "A RAI-PASS is not a certification or a compliance approval.",
            "Missing pillars lowered confidence and were not scored favorably.",
        ],
        "accountability_statement": (
            "Responsible AI posture is an assurance signal, not an authorization "
            "or certification. The human owner remains accountable for the system, "
            "its deployment, and any impact on people."
        ),
    }


def _coverage_rating(p: PillarEvaluation) -> str:
    if not p.has_evidence():
        return "gap"
    m = p.maturity or 0
    if m >= 4 and p.tested:
        return "good"
    if m >= 3:
        return "fair"
    if m >= 1:
        return "weak"
    return "gap"
