"""Gate 6: constrained safe plan.

AgentShield may narrow scope, add validation, prepare rollback, batch changes,
add checkpoints, request approval, or deny. It must never silently substitute a
different operation. Semantic safety invariants are enforced here and will raise
``SafetyInvariantError`` rather than emit an unsafe plan.
"""

from __future__ import annotations

from typing import Optional

from .models import (
    ActionRequest,
    PlanStep,
    SafePlan,
    canonical_hash,
)


class SafetyInvariantError(Exception):
    """Raised when a requested transformation would violate a safety invariant."""


# Operations that must never be silently swapped for their dangerous inverse.
FORBIDDEN_SUBSTITUTIONS = {
    "add_disk": "remove_disk",
    "provision_server": "decommission_server",
}

# Substitutions allowed only when the requester explicitly asked for them.
EXPLICIT_ONLY_SUBSTITUTIONS = {
    "apply_patch": "uninstall_patch",
}


def _plan_hash(steps: list[PlanStep]) -> str:
    canonical = [
        {
            "id": s.id,
            "action": s.action,
            "target_scope": s.target_scope,
            "required_capability": s.required_capability,
        }
        for s in steps
    ]
    return canonical_hash(canonical)


def assert_invariants(
    requested_action: str,
    planned_action: str,
    explicit_request: bool = False,
) -> None:
    """Guard against dangerous operation substitution."""

    if requested_action in FORBIDDEN_SUBSTITUTIONS:
        if planned_action == FORBIDDEN_SUBSTITUTIONS[requested_action]:
            raise SafetyInvariantError(
                f"'{requested_action}' must never become '{planned_action}'."
            )

    if requested_action in EXPLICIT_ONLY_SUBSTITUTIONS:
        if (
            planned_action == EXPLICIT_ONLY_SUBSTITUTIONS[requested_action]
            and not explicit_request
        ):
            raise SafetyInvariantError(
                f"'{requested_action}' must not become '{planned_action}' "
                "unless explicitly requested."
            )


def build_safe_plan(
    request: ActionRequest,
    permitted_capabilities: list[str],
    steps: list[PlanStep],
    *,
    explicit_substitution: bool = False,
    notes: Optional[list[str]] = None,
) -> SafePlan:
    """Validate and finalize a constrained plan.

    Each step must preserve the requested operation's meaning, stay within the
    requester's approved capabilities, and carry a reason. Violations raise
    ``SafetyInvariantError``.
    """

    if not steps:
        raise SafetyInvariantError("a safe plan must contain at least one step")

    permitted = set(permitted_capabilities)
    for step in steps:
        assert_invariants(request.action, step.action, explicit_substitution)

        if step.required_capability not in permitted:
            raise SafetyInvariantError(
                f"step '{step.id}' requires capability "
                f"'{step.required_capability}' outside requester scope."
            )
        if step.action not in permitted:
            raise SafetyInvariantError(
                f"step '{step.id}' action '{step.action}' is outside requester scope."
            )
        if not step.reason.strip():
            raise SafetyInvariantError(f"step '{step.id}' must state why it exists.")
        if not step.stop_condition.strip():
            raise SafetyInvariantError(
                f"step '{step.id}' must define a stop condition."
            )

    return SafePlan(steps=steps, plan_hash=_plan_hash(steps), notes=list(notes or []))


def execute_plan_with_validation(
    plan: SafePlan,
    validators: dict[str, bool],
) -> tuple[list[str], Optional[str]]:
    """Simulate ordered execution where failed validation stops remaining steps.

    ``validators`` maps step id -> whether that step's validation passes. This is
    a synthetic simulation; no target system is contacted. Returns the list of
    executed step ids and the stopped step id (if any).
    """

    executed: list[str] = []
    for step in plan.steps:
        passed = validators.get(step.id, True)
        if not passed:
            return executed, step.id
        executed.append(step.id)
    return executed, None
