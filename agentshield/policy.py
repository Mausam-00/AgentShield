"""Gate 4: deterministic policy.

This module is the sole authorization owner. It evaluates versioned controls
against deterministic facts, never against AI judgement, and never lets a
numerical score weaken a hard control. When multiple controls match, the most
restrictive decision wins (DENY > ESCALATE > APPROVE > TRANSFORM > ALLOW).

A policy-engine failure fails closed to DENY.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import (
    POLICY_VERSION,
    ActionRequest,
    AssuranceResult,
    Decision,
    DECISION_PRECEDENCE,
    IdentityContext,
    Lifecycle,
    OperationalImpact,
    PolicyMatch,
    PolicyResult,
    Posture,
    Severity,
)


# Default freshness window for production writes (days). Absence of a configured
# window must fail closed for production writes.
DEFAULT_ASSURANCE_MAX_AGE_DAYS = 30.0


# Authoritative versioned control catalogue. This is the single source of truth
# for the deterministic contract: every control emitted by ``evaluate_policy``
# is declared here as ``(control_id, reason_code, decision, tier)``. The
# determinism layer fingerprints this table *and* the source of
# ``evaluate_policy`` (see :mod:`agentshield.determinism`), so neither the
# declared contract nor the decision logic can change without altering the
# policy bundle hash.
CONTROL_CATALOGUE: list[tuple[str, str, str, str]] = [
    ("ASP-001", "IDENTITY_UNKNOWN", "DENY", "deny"),
    ("ASP-002", "LIFECYCLE", "DENY", "deny"),
    ("ASP-003", "BLOCK_POSTURE_WRITE", "DENY", "deny"),
    ("ASP-004", "UNRESOLVED_CRITICAL_FINDING", "DENY", "deny"),
    ("ASP-005", "OUT_OF_SCOPE", "DENY", "deny"),
    ("ASP-006", "APPROVAL_REJECTED_OR_EXPIRED", "DENY", "deny"),
    ("ASP-007", "POLICY_ENGINE_FAILURE", "DENY", "deny"),
    ("ASP-008", "ADAPTER_FAILURE", "DENY", "deny"),
    ("ASP-009", "OBSERVED_DEVIATION", "DENY", "deny"),
    ("ASP-010", "REVIEW_STATE_WRITE", "ESCALATE", "escalate"),
    ("ASP-011", "STALE_ASSURANCE_PROD_WRITE", "ESCALATE", "escalate"),
    ("ASP-012", "MISSING_HIGH_RISK_EVIDENCE", "ESCALATE", "escalate"),
    ("ASP-013", "TOOL_MANIFEST_CHANGED", "ESCALATE", "escalate"),
    ("ASP-014", "TIER_ZERO_OR_IDENTITY", "ESCALATE", "escalate"),
    ("ASP-015", "DESTRUCTIVE_OR_IRREVERSIBLE", "APPROVE", "approve"),
    ("ASP-016", "PRODUCTION_WRITE", "APPROVE", "approve"),
    ("ASP-017", "SECURITY_SENSITIVE_CHANGE", "APPROVE", "approve"),
    ("ASP-018", "HIGH_DATA_SENSITIVITY", "APPROVE", "approve"),
    ("ASP-019", "FLEET_WIDE_CHANGE", "APPROVE", "approve"),
    ("ASP-020", "LARGE_REVERSIBLE_BATCHABLE", "TRANSFORM", "transform"),
    ("ASP-021", "READ_ONLY_IN_SCOPE", "ALLOW", "allow"),
]


@dataclass
class PolicyConfig:
    version: str = POLICY_VERSION
    assurance_max_age_days: Optional[float] = DEFAULT_ASSURANCE_MAX_AGE_DAYS
    engine_healthy: bool = True


def _is_write(request: ActionRequest) -> bool:
    return not request.read_only


def _in_scope(request: ActionRequest, identity: IdentityContext) -> bool:
    caps = set(identity.permitted_capabilities)
    return request.action in caps


def evaluate_policy(
    request: ActionRequest,
    identity: IdentityContext,
    assurance: Optional[AssuranceResult],
    impact: OperationalImpact,
    *,
    config: Optional[PolicyConfig] = None,
    approval_rejected_or_expired: bool = False,
    observed_deviation: bool = False,
    adapter_failed: bool = False,
    critical_finding_affects_action: bool = True,
    large_reversible_batchable: bool = False,
) -> PolicyResult:
    """Evaluate all controls and return the most restrictive decision."""

    config = config or PolicyConfig()

    # Fail closed if the deterministic engine is unhealthy.
    if not config.engine_healthy:
        return PolicyResult(
            decision=Decision.DENY,
            policy_version=config.version,
            engine_failed=True,
            matches=[
                PolicyMatch(
                    "ASP-007",
                    "POLICY_ENGINE_FAILURE",
                    Decision.DENY,
                    "Deterministic policy engine reported unhealthy; failing closed.",
                )
            ],
        )

    matches: list[PolicyMatch] = []

    def add(control_id: str, reason: str, decision: Decision, why: str) -> None:
        matches.append(PolicyMatch(control_id, reason, decision, why))

    is_write = _is_write(request)
    production = request.is_production()

    # --- DENY controls -----------------------------------------------------
    if not identity.known:
        add("ASP-001", "IDENTITY_UNKNOWN", Decision.DENY,
            "Requester identity could not be resolved.")

    if identity.lifecycle in (Lifecycle.QUARANTINED, Lifecycle.UNKNOWN):
        add("ASP-002", f"LIFECYCLE_{identity.lifecycle.value.upper()}", Decision.DENY,
            "Lifecycle state forbids execution.")

    if assurance is not None and assurance.posture == Posture.BLOCK and is_write:
        add("ASP-003", "BLOCK_POSTURE_WRITE", Decision.DENY,
            "BLOCK assurance posture cannot perform write operations.")

    if (
        assurance is not None
        and assurance.has_open_at_or_above(Severity.CRITICAL)
        and critical_finding_affects_action
    ):
        add("ASP-004", "UNRESOLVED_CRITICAL_FINDING", Decision.DENY,
            "An unresolved critical finding affects this action.")

    if not _in_scope(request, identity):
        add("ASP-005", "OUT_OF_SCOPE", Decision.DENY,
            "Action is outside the requester's declared permission scope.")

    if approval_rejected_or_expired:
        add("ASP-006", "APPROVAL_REJECTED_OR_EXPIRED", Decision.DENY,
            "Approval was rejected or has expired.")

    if adapter_failed:
        add("ASP-008", "ADAPTER_FAILURE", Decision.DENY,
            "Execution adapter failed; stopping.")

    if observed_deviation:
        add("ASP-009", "OBSERVED_DEVIATION", Decision.DENY,
            "Observed behavior materially deviated from the approved action.")

    # --- ESCALATE controls -------------------------------------------------
    if identity.lifecycle == Lifecycle.REVIEW and is_write:
        add("ASP-010", "REVIEW_STATE_WRITE", Decision.ESCALATE,
            "Review-state requester attempted a write operation.")

    if production and is_write:
        stale = _is_stale(identity, config)
        if stale:
            add("ASP-011", "STALE_ASSURANCE_PROD_WRITE", Decision.ESCALATE,
                "Production write with stale or unverifiable assurance freshness.")

    missing_high_risk_evidence = _missing_high_risk_evidence(assurance, impact)
    if missing_high_risk_evidence:
        add("ASP-012", "MISSING_HIGH_RISK_EVIDENCE", Decision.ESCALATE,
            "Required high-risk evidence is missing.")

    if identity.tool_manifest_changed and is_write:
        add("ASP-013", "TOOL_MANIFEST_CHANGED", Decision.ESCALATE,
            "Tool manifest changed after assurance; re-audit required before write.")

    if impact.tier_zero or impact.identity_impacting:
        add("ASP-014", "TIER_ZERO_OR_IDENTITY", Decision.ESCALATE,
            "Action affects tier-zero or identity systems.")

    # --- APPROVE controls --------------------------------------------------
    if (impact.destructive or impact.irreversible) and is_write:
        add("ASP-015", "DESTRUCTIVE_OR_IRREVERSIBLE", Decision.APPROVE,
            "Destructive or irreversible action requires approval.")

    if production and is_write:
        add("ASP-016", "PRODUCTION_WRITE", Decision.APPROVE,
            "Production write requires approval.")

    if impact.security_sensitive:
        add("ASP-017", "SECURITY_SENSITIVE_CHANGE", Decision.APPROVE,
            "Security-sensitive change requires approval.")

    if impact.high_data_sensitivity:
        add("ASP-018", "HIGH_DATA_SENSITIVITY", Decision.APPROVE,
            "High-sensitivity data affected; approval required.")

    if impact.fleet_wide:
        add("ASP-019", "FLEET_WIDE_CHANGE", Decision.APPROVE,
            "Fleet-wide change requires approval.")

    # --- TRANSFORM control -------------------------------------------------
    if large_reversible_batchable and is_write:
        add("ASP-020", "LARGE_REVERSIBLE_BATCHABLE", Decision.TRANSFORM,
            "Large reversible change can be narrowed or batched.")

    # --- ALLOW control -----------------------------------------------------
    if request.read_only and _in_scope(request, identity) and identity.known:
        add("ASP-021", "READ_ONLY_IN_SCOPE", Decision.ALLOW,
            "In-scope, eligible, low-risk read-only action.")

    # If nothing matched, fail closed to ESCALATE (never silently ALLOW).
    if not matches:
        add("ASP-012", "MISSING_HIGH_RISK_EVIDENCE", Decision.ESCALATE,
            "No control matched; failing closed for review.")

    winning = max(matches, key=lambda m: DECISION_PRECEDENCE[m.decision]).decision

    return PolicyResult(
        decision=winning,
        policy_version=config.version,
        matches=matches,
    )


def _is_stale(identity: IdentityContext, config: PolicyConfig) -> bool:
    if config.assurance_max_age_days is None:
        # No configured freshness policy: fail closed for production writes.
        return True
    if identity.assurance_age_days is None:
        return True
    return identity.assurance_age_days > config.assurance_max_age_days


def _missing_high_risk_evidence(
    assurance: Optional[AssuranceResult], impact: OperationalImpact
) -> bool:
    high_risk = (
        impact.destructive
        or impact.irreversible
        or impact.tier_zero
        or impact.identity_impacting
        or impact.security_sensitive
        or impact.high_data_sensitivity
        or impact.fleet_wide
    )
    if not high_risk:
        return False
    if assurance is None:
        return True
    if assurance.score is None:
        return True
    # Unknown impact dimensions on a high-risk action are treated as missing.
    return any(d.is_unknown() for d in impact.dimensions)
