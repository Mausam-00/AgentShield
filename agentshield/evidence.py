"""Append-only evidence store and record construction.

Every workflow outcome, including denial, rejection, timeout, and failure, must
produce an evidence record. The in-memory store here is synthetic and rejects
mutation of existing records.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Optional

from .models import (
    AUDIT_VERSION,
    ActionRequest,
    ApprovalRecord,
    AssuranceResult,
    EvidenceRecord,
    IdentityContext,
    Mode,
    OperationalImpact,
    PolicyResult,
    SafePlan,
    ValidationResult,
)


ACCOUNTABILITY_STATEMENT = (
    "AgentShield AI provides assurance and governance support only. It does not "
    "certify compliance or guarantee safety. The named owner and approver remain "
    "accountable for this action and its outcome."
)


class InMemoryEvidenceStore:
    """Synthetic append-only evidence store."""

    def __init__(self) -> None:
        self._records: list[EvidenceRecord] = []

    def append(self, record: EvidenceRecord) -> None:
        # Store a deep copy so callers cannot mutate persisted evidence.
        self._records.append(copy.deepcopy(record))

    def all(self) -> list[EvidenceRecord]:
        return [copy.deepcopy(r) for r in self._records]

    def __len__(self) -> int:
        return len(self._records)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_evidence(
    *,
    mode: Mode,
    request: Optional[ActionRequest],
    identity: Optional[IdentityContext],
    assurance: Optional[AssuranceResult],
    impact: Optional[OperationalImpact],
    policy: Optional[PolicyResult],
    approval: Optional[ApprovalRecord],
    plan: Optional[SafePlan],
    validation: Optional[ValidationResult],
    outcome: str,
    expected_behavior: Optional[str] = None,
    observed_behavior: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> EvidenceRecord:
    """Assemble a complete evidence record for any outcome."""

    coverage_limitations: list[str] = []
    if assurance is not None:
        coverage_limitations.extend(assurance.coverage_limitations)
    if impact is not None:
        coverage_limitations.extend(impact.limitations)

    resolved_trace = trace_id or (request.trace_id if request else "no-trace")

    return EvidenceRecord(
        trace_id=resolved_trace,
        timestamp_utc=utc_now_iso(),
        mode=mode.value,
        requester_id=request.requester_id if request else "unknown",
        requester_type=request.requester_type if request else "unknown",
        owner=identity.owner if identity else None,
        sponsor=identity.sponsor if identity else None,
        assurance_posture=assurance.posture.value if assurance else None,
        assurance_score=assurance.score if assurance else None,
        coverage=assurance.coverage if assurance else None,
        confidence=assurance.confidence.value if assurance else None,
        audit_version=assurance.audit_version if assurance else AUDIT_VERSION,
        definition_hash=assurance.definition_hash if assurance else None,
        tool_manifest_hash=assurance.tool_manifest_hash if assurance else None,
        action=request.action if request else None,
        target=request.target if request else None,
        purpose=request.purpose if request else None,
        environment=request.environment if request else None,
        operational_impact_score=impact.score if impact else None,
        coverage_limitations=coverage_limitations,
        policy_decision=policy.decision.value if policy else None,
        policy_version=policy.policy_version if policy else None,
        policy_controls=[m.control_id for m in policy.matches] if policy else [],
        reason_codes=policy.reason_codes() if policy else [],
        approval_result=approval.result.value if approval else None,
        approver=approval.approver if approval else None,
        plan_hash=plan.plan_hash if plan else None,
        plan_steps=[s.id for s in plan.steps] if plan else [],
        expected_behavior=expected_behavior,
        observed_behavior=observed_behavior,
        stopped_step=validation.stopped_step if validation else None,
        outcome=outcome,
        deviations=validation.deviations if validation else [],
        accountability_statement=ACCOUNTABILITY_STATEMENT,
    )
