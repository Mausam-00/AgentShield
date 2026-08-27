"""Shared synthetic fixtures for AgentShield workflow tests.

All identities, targets, and records are fictional.
"""

from __future__ import annotations

from agentshield import (
    ActionRequest,
    AssuranceResult,
    Confidence,
    EvidenceState,
    FamilyEvaluation,
    Finding,
    IdentityContext,
    ImpactDimension,
    Lifecycle,
    OperationalImpact,
    Posture,
    Severity,
    compute_impact,
    evaluate_assurance,
)
from agentshield.assurance import CONTROL_FAMILIES


def full_families(maturity: int = 4, state: EvidenceState = EvidenceState.TESTED):
    return [
        FamilyEvaluation(fid, name, weight, maturity, state)
        for fid, name, weight in CONTROL_FAMILIES
    ]


def passing_assurance(subject: str = "synthetic-agent") -> AssuranceResult:
    return evaluate_assurance(
        subject=subject,
        families=full_families(),
        findings=[],
        definition_text="synthetic definition",
        tool_manifest_text="synthetic manifest",
    )


def evaluate_assurance_partial(subject: str = "synthetic-agent") -> AssuranceResult:
    """Assurance with only two families evidenced -> low coverage."""

    fams = [
        FamilyEvaluation(fid, name, weight, 3, EvidenceState.DECLARED)
        for fid, name, weight in CONTROL_FAMILIES[:2]
    ]
    return evaluate_assurance(subject=subject, families=fams, findings=[])


def blocking_assurance(subject: str = "synthetic-agent") -> AssuranceResult:
    critical = Finding(
        id="F-CRIT-1",
        control_family="ASF-03",
        severity=Severity.CRITICAL,
        title="Unauthenticated write capability",
        condition="Write tool exposed without authentication.",
        evidence_state=EvidenceState.OBSERVED,
        observation="Synthetic finding.",
        remediation="Require authentication.",
    )
    return evaluate_assurance(
        subject=subject,
        families=full_families(),
        findings=[critical],
    )


def identity(
    requester_id: str = "svc-synthetic",
    lifecycle: Lifecycle = Lifecycle.ACTIVE,
    capabilities=None,
    known: bool = True,
    assurance_age_days: float = 1.0,
    tool_manifest_changed: bool = False,
) -> IdentityContext:
    return IdentityContext(
        requester_id=requester_id,
        known=known,
        requester_type="service-agent",
        lifecycle=lifecycle,
        owner="synthetic-owner",
        sponsor="synthetic-sponsor",
        platform="synthetic-platform",
        permitted_capabilities=capabilities
        if capabilities is not None
        else ["read_config", "add_disk"],
        assurance_age_days=assurance_age_days,
        tool_manifest_changed=tool_manifest_changed,
    )


def request(
    action: str = "read_config",
    target: str = "synthetic-target",
    environment: str = "non-production",
    read_only: bool = True,
    capabilities=None,
    trace_id: str = "trace-0001",
    requester_id: str = "svc-synthetic",
) -> ActionRequest:
    return ActionRequest(
        trace_id=trace_id,
        requester_id=requester_id,
        requester_type="service-agent",
        action=action,
        target=target,
        purpose="synthetic purpose",
        environment=environment,
        request_timestamp_utc="2026-01-01T00:00:00Z",
        declared_capabilities=capabilities or [],
        read_only=read_only,
    )


def low_impact(target: str = "synthetic-target") -> OperationalImpact:
    dims = [
        ImpactDimension("target criticality", 1, "synthetic"),
        ImpactDimension("dependency reach", 1, "synthetic"),
        ImpactDimension("data sensitivity", 1, "synthetic"),
        ImpactDimension("reversibility", 1, "synthetic"),
    ]
    return compute_impact(dims)


def high_impact(
    *,
    destructive: bool = False,
    irreversible: bool = False,
    fleet_wide: bool = False,
    tier_zero: bool = False,
    identity_impacting: bool = False,
    security_sensitive: bool = False,
    high_data_sensitivity: bool = False,
    unknown_dim: bool = False,
) -> OperationalImpact:
    dims = [
        ImpactDimension("target criticality", 4, "synthetic"),
        ImpactDimension("dependency reach", 3, "synthetic"),
        ImpactDimension(
            "data sensitivity", None if unknown_dim else 3, "synthetic"
        ),
        ImpactDimension("reversibility", 4, "synthetic"),
    ]
    return compute_impact(
        dims,
        destructive=destructive,
        irreversible=irreversible,
        fleet_wide=fleet_wide,
        tier_zero=tier_zero,
        identity_impacting=identity_impacting,
        security_sensitive=security_sensitive,
        high_data_sensitivity=high_data_sensitivity,
    )
