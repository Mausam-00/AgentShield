"""Core AgentShield AI contracts.

These types encode the protocol's foundational separation: assurance posture
(``PASS``/``WARN``/``BLOCK``) is kept distinct from the runtime decision
(``ALLOW``/``TRANSFORM``/``APPROVE``/``ESCALATE``/``DENY``). Nothing in this
module authorizes an action; deterministic policy owns that in ``policy.py``.

All examples that use these types are synthetic. No live system, credential, or
real integration is represented here.
"""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


AUDIT_VERSION = "agentshield-audit-1.0.0"
POLICY_VERSION = "agentshield-policy-1.0.0"


# --------------------------------------------------------------------------- #
# Enumerations
# --------------------------------------------------------------------------- #
class Mode(enum.Enum):
    ASSESS = "ASSESS"
    OBSERVE = "OBSERVE"
    GOVERN = "GOVERN"
    CONTROLLED_LIVE = "CONTROLLED LIVE"


class Posture(enum.Enum):
    """Assurance posture. Never an authorization."""

    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"


class Decision(enum.Enum):
    """Runtime authorization decision, owned by deterministic policy."""

    ALLOW = "ALLOW"
    TRANSFORM = "TRANSFORM"
    APPROVE = "APPROVE"
    ESCALATE = "ESCALATE"
    DENY = "DENY"


class Confidence(enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Severity(enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class EvidenceState(enum.Enum):
    OBSERVED = "Observed"
    DECLARED = "Declared"
    TESTED = "Tested"
    INFERRED = "Inferred"
    UNAVAILABLE = "Unavailable"


class Lifecycle(enum.Enum):
    ACTIVE = "Active"
    REVIEW = "Review"
    QUARANTINED = "Quarantined"
    UNKNOWN = "Unknown"


class ApprovalResult(enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED_FOR_REVISION = "RETURNED_FOR_REVISION"
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"


# Ordering used only for explanatory severity comparisons.
SEVERITY_ORDER = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

# Precedence for combining matched runtime controls (most restrictive wins).
DECISION_PRECEDENCE = {
    Decision.DENY: 5,
    Decision.ESCALATE: 4,
    Decision.APPROVE: 3,
    Decision.TRANSFORM: 2,
    Decision.ALLOW: 1,
}


def hash_text(text: Optional[str]) -> Optional[str]:
    """SHA-256 of supplied text, or ``None`` when no evidence is available."""

    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_hash(payload: Any) -> str:
    """Stable hash over canonical JSON, used for plan and binding hashes."""

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Assurance (Gate 0)
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    id: str
    control_family: str
    severity: Severity
    title: str
    condition: str
    evidence_state: EvidenceState
    observation: str
    remediation: str
    evidence_refs: list[str] = field(default_factory=list)
    hypothesis: Optional[str] = None
    impact: str = ""
    owner: Optional[str] = None
    resolved: bool = False

    def is_open(self) -> bool:
        return not self.resolved


@dataclass
class FamilyEvaluation:
    """One assurance control family's maturity, or absence of evidence."""

    family_id: str
    name: str
    weight: int
    maturity: Optional[int]  # 0..4 when evidence exists, else None
    evidence_state: EvidenceState
    note: str = ""

    def has_evidence(self) -> bool:
        return self.maturity is not None


@dataclass
class AssuranceResult:
    posture: Posture
    score: Optional[int]
    coverage: float
    confidence: Confidence
    audit_version: str
    findings: list[Finding] = field(default_factory=list)
    families: list[FamilyEvaluation] = field(default_factory=list)
    coverage_limitations: list[str] = field(default_factory=list)
    definition_hash: Optional[str] = None
    tool_manifest_hash: Optional[str] = None
    subject: str = "unknown-subject"

    def open_findings(self) -> list[Finding]:
        return [f for f in self.findings if f.is_open()]

    def has_open_at_or_above(self, severity: Severity) -> bool:
        threshold = SEVERITY_ORDER[severity]
        return any(
            SEVERITY_ORDER[f.severity] >= threshold for f in self.open_findings()
        )


# --------------------------------------------------------------------------- #
# Runtime request and identity context (Gates 1 & 2)
# --------------------------------------------------------------------------- #
@dataclass
class ActionRequest:
    trace_id: str
    requester_id: str
    requester_type: str
    action: str
    target: str
    purpose: str
    environment: str  # e.g. "production" / "non-production"
    request_timestamp_utc: str
    declared_capabilities: list[str] = field(default_factory=list)
    read_only: bool = False
    change_record: Optional[str] = None

    REQUIRED_FIELDS = (
        "trace_id",
        "requester_id",
        "requester_type",
        "action",
        "target",
        "purpose",
        "environment",
        "request_timestamp_utc",
    )

    def missing_required(self) -> list[str]:
        missing = []
        for name in self.REQUIRED_FIELDS:
            value = getattr(self, name)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(name)
        return missing

    def is_production(self) -> bool:
        return self.environment.strip().lower() == "production"


@dataclass
class IdentityContext:
    requester_id: str
    known: bool
    requester_type: str
    lifecycle: Lifecycle
    owner: Optional[str]
    sponsor: Optional[str]
    platform: Optional[str]
    permitted_capabilities: list[str] = field(default_factory=list)
    assurance_age_days: Optional[float] = None
    tool_manifest_changed: bool = False


# --------------------------------------------------------------------------- #
# Operational impact (Gate 3)
# --------------------------------------------------------------------------- #
@dataclass
class ImpactDimension:
    name: str
    rating: Optional[int]  # 0..4, or None for UNKNOWN
    evidence: str

    def is_unknown(self) -> bool:
        return self.rating is None


@dataclass
class OperationalImpact:
    dimensions: list[ImpactDimension]
    score: int
    limitations: list[str] = field(default_factory=list)
    destructive: bool = False
    irreversible: bool = False
    fleet_wide: bool = False
    tier_zero: bool = False
    identity_impacting: bool = False
    security_sensitive: bool = False
    high_data_sensitivity: bool = False


# --------------------------------------------------------------------------- #
# Deterministic policy (Gate 4)
# --------------------------------------------------------------------------- #
@dataclass
class PolicyMatch:
    control_id: str
    reason_code: str
    decision: Decision
    explanation: str


@dataclass
class PolicyResult:
    decision: Decision
    policy_version: str
    matches: list[PolicyMatch] = field(default_factory=list)
    engine_failed: bool = False

    def reason_codes(self) -> list[str]:
        return [m.reason_code for m in self.matches]


# --------------------------------------------------------------------------- #
# Approval (Gate 5)
# --------------------------------------------------------------------------- #
@dataclass
class ApprovalBinding:
    requester_id: str
    action: str
    target: str
    plan_hash: str
    policy_version: str
    expiry_utc: str

    def binding_hash(self) -> str:
        return canonical_hash(asdict(self))


@dataclass
class ApprovalRecord:
    result: ApprovalResult
    approver: Optional[str]
    binding: Optional[ApprovalBinding]
    issued_at_utc: Optional[str] = None


# --------------------------------------------------------------------------- #
# Constrained safe plan (Gate 6)
# --------------------------------------------------------------------------- #
@dataclass
class PlanStep:
    id: str
    action: str
    target_scope: str
    reason: str
    validation: str
    rollback: str
    stop_condition: str
    required_capability: str


@dataclass
class SafePlan:
    steps: list[PlanStep]
    plan_hash: str
    notes: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Outcome validation (Gate 7)
# --------------------------------------------------------------------------- #
@dataclass
class ObservedOutcome:
    action: str
    target: str
    executed_step_ids: list[str] = field(default_factory=list)
    outcome: str = "unknown"


@dataclass
class ValidationResult:
    action_match: bool
    target_match: bool
    plan_match: bool
    outcome_match: bool
    deviations: list[str] = field(default_factory=list)
    stopped_step: Optional[str] = None

    @property
    def deviated(self) -> bool:
        return bool(self.deviations)


# --------------------------------------------------------------------------- #
# Evidence record (append-only)
# --------------------------------------------------------------------------- #
@dataclass
class EvidenceRecord:
    trace_id: str
    timestamp_utc: str
    mode: str
    requester_id: str
    requester_type: str
    owner: Optional[str]
    sponsor: Optional[str]
    assurance_posture: Optional[str]
    assurance_score: Optional[int]
    coverage: Optional[float]
    confidence: Optional[str]
    audit_version: str
    definition_hash: Optional[str]
    tool_manifest_hash: Optional[str]
    action: Optional[str]
    target: Optional[str]
    purpose: Optional[str]
    environment: Optional[str]
    operational_impact_score: Optional[int]
    coverage_limitations: list[str]
    policy_decision: Optional[str]
    policy_version: Optional[str]
    policy_controls: list[str]
    reason_codes: list[str]
    approval_result: Optional[str]
    approver: Optional[str]
    plan_hash: Optional[str]
    plan_steps: list[str]
    expected_behavior: Optional[str]
    observed_behavior: Optional[str]
    stopped_step: Optional[str]
    outcome: str
    deviations: list[str]
    accountability_statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowResult:
    """Aggregated output of a workflow run across the relevant gates."""

    mode: Mode
    trace_id: str
    assurance: Optional[AssuranceResult] = None
    impact: Optional[OperationalImpact] = None
    policy: Optional[PolicyResult] = None
    approval: Optional[ApprovalRecord] = None
    plan: Optional[SafePlan] = None
    validation: Optional[ValidationResult] = None
    evidence: Optional[EvidenceRecord] = None
    limitations: list[str] = field(default_factory=list)
    nothing_reached_target: bool = True
