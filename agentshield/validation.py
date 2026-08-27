"""Gate 7: outcome validation.

Compares approved action, target, and plan against observed behavior. On
deviation, work stops, evidence is preserved, and a finding is raised for human
investigation. Policy is never automatically rewritten.
"""

from __future__ import annotations

from typing import Optional

from .models import (
    EvidenceState,
    Finding,
    ObservedOutcome,
    SafePlan,
    Severity,
    ValidationResult,
)


def validate_outcome(
    approved_action: str,
    approved_target: str,
    plan: SafePlan,
    observed: ObservedOutcome,
    expected_outcome: str = "success",
) -> ValidationResult:
    deviations: list[str] = []

    action_match = approved_action == observed.action
    if not action_match:
        deviations.append(
            f"Action deviation: approved '{approved_action}', "
            f"observed '{observed.action}'."
        )

    target_match = approved_target == observed.target
    if not target_match:
        deviations.append(
            f"Target deviation: approved '{approved_target}', "
            f"observed '{observed.target}'."
        )

    planned_ids = [s.id for s in plan.steps]
    # Observed steps must be a prefix of the approved plan (a stop is allowed,
    # extra or reordered steps are deviations).
    plan_match = observed.executed_step_ids == planned_ids[
        : len(observed.executed_step_ids)
    ]
    if not plan_match:
        deviations.append(
            "Plan deviation: observed steps are not an ordered prefix of the "
            "approved plan."
        )

    outcome_match = observed.outcome == expected_outcome
    if not outcome_match:
        deviations.append(
            f"Outcome deviation: expected '{expected_outcome}', "
            f"observed '{observed.outcome}'."
        )

    return ValidationResult(
        action_match=action_match,
        target_match=target_match,
        plan_match=plan_match,
        outcome_match=outcome_match,
        deviations=deviations,
    )


def deviation_finding(
    validation: ValidationResult, trace_id: str
) -> Optional[Finding]:
    """Create an assurance finding when a deviation is detected."""

    if not validation.deviated:
        return None

    severity = Severity.CRITICAL if (
        not validation.action_match or not validation.target_match
    ) else Severity.HIGH

    return Finding(
        id=f"DEV-{trace_id}",
        control_family="ASF-08",
        severity=severity,
        title="Observed behavior deviated from approved action",
        condition="Approved and observed behavior did not match.",
        evidence_state=EvidenceState.OBSERVED,
        observation="; ".join(validation.deviations),
        remediation=(
            "Stop further work, preserve evidence, and require human "
            "investigation before any further action."
        ),
        impact="Potential unauthorized or unexpected change.",
    )


def lifecycle_recommendation(validation: ValidationResult) -> str:
    """Recommend a lifecycle change based on deviation severity."""

    if not validation.deviated:
        return "Active"
    if not validation.action_match or not validation.target_match:
        return "Quarantined"
    return "Review"
