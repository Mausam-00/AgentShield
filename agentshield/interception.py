"""Prototype: live Gate-4 interception with a mock execution adapter.

This is the answer to "does it actually stop a bad action?". A proposed
tool-call is intercepted *before* it reaches a target. AgentShield builds an
:class:`ActionRequest`, runs the deterministic policy (Gate 4), enforces the
safety invariants (Gate 6), and only then may the adapter execute. Any decision
other than ``ALLOW``/``TRANSFORM`` results in **zero execution**.

The :class:`MockExecutionTarget` is a synthetic, in-memory target. It performs
no real I/O and contacts no network - ``CONTROLLED LIVE`` remains disabled. It
exists solely to demonstrate, end to end, that the policy gate is enforced and
that safety invariants cannot be violated (``add_disk`` never becomes
``remove_disk``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .models import (
    ActionRequest,
    AssuranceResult,
    Decision,
    IdentityContext,
    OperationalImpact,
    PolicyResult,
    SafePlan,
)
from .planning import SafetyInvariantError, assert_invariants
from .policy import PolicyConfig, evaluate_policy

# Operations that must never be silently substituted for one another.
FORBIDDEN_SUBSTITUTIONS = {
    "add_disk": "remove_disk",
    "provision_server": "decommission_server",
    "apply_patch": "uninstall_patch",
}


@dataclass
class ExecutionResult:
    executed: bool
    decision: Decision
    reason_codes: list[str]
    target_effect: Optional[str]
    blocked_reason: Optional[str] = None
    adapter_output: Optional[str] = None
    invariant_violation: Optional[str] = None


@dataclass
class MockExecutionTarget:
    """Synthetic target. Records effects instead of performing real I/O."""

    enabled: bool = True
    supported_actions: list[str] = field(
        default_factory=lambda: ["add_disk", "read_config", "apply_patch"]
    )
    supported_target_types: list[str] = field(default_factory=lambda: ["vm", "config"])
    effects: list[str] = field(default_factory=list)

    def dry_run(self, action: str, target: str) -> str:
        return f"DRY-RUN ok: {action} -> {target}"

    def execute(self, action: str, target: str) -> str:
        if not self.enabled:
            raise RuntimeError("adapter disabled")
        if action not in self.supported_actions:
            raise RuntimeError(f"unsupported action: {action}")
        effect = f"{action} applied to {target}"
        self.effects.append(effect)
        return effect


class GatedExecutor:
    """Wraps an execution adapter behind the deterministic policy gate."""

    def __init__(
        self,
        adapter: MockExecutionTarget,
        *,
        policy_config: Optional[PolicyConfig] = None,
    ) -> None:
        self.adapter = adapter
        self.policy_config = policy_config or PolicyConfig()

    def intercept(
        self,
        request: ActionRequest,
        identity: IdentityContext,
        impact: OperationalImpact,
        assurance: Optional[AssuranceResult] = None,
        *,
        plan: Optional[SafePlan] = None,
        approved: bool = False,
    ) -> ExecutionResult:
        """Intercept a proposed action and enforce policy before execution."""

        policy: PolicyResult = evaluate_policy(
            request,
            identity,
            assurance,
            impact,
            config=self.policy_config,
            critical_finding_affects_action=not request.read_only,
        )
        reasons = policy.reason_codes()

        # Gate 6 safety invariant: the executed action must equal the requested
        # action and stay within approved capabilities. If a plan is supplied,
        # verify every step preserves the operation and no forbidden
        # substitution slipped in.
        try:
            permitted = set(identity.permitted_capabilities)
            if plan is not None:
                for step in plan.steps:
                    assert_invariants(request.action, step.action)
                    if step.required_capability not in permitted:
                        raise SafetyInvariantError(
                            f"step '{step.id}' requires capability "
                            f"'{step.required_capability}' outside requester scope."
                        )
            self._assert_no_substitution(request, plan)
        except SafetyInvariantError as exc:
            return ExecutionResult(
                executed=False,
                decision=Decision.DENY,
                reason_codes=reasons + ["SAFETY_INVARIANT_VIOLATION"],
                target_effect=None,
                blocked_reason=str(exc),
                invariant_violation=str(exc),
            )

        # Only ALLOW and TRANSFORM may reach the target. TRANSFORM implies the
        # plan was already narrowed/batched upstream.
        if policy.decision in (Decision.ALLOW, Decision.TRANSFORM):
            output = self.adapter.execute(request.action, request.target)
            return ExecutionResult(
                executed=True,
                decision=policy.decision,
                reason_codes=reasons,
                target_effect=output,
                adapter_output=output,
            )

        # APPROVE may execute only with a genuine approval; otherwise it holds.
        if policy.decision == Decision.APPROVE and approved:
            output = self.adapter.execute(request.action, request.target)
            return ExecutionResult(
                executed=True,
                decision=policy.decision,
                reason_codes=reasons,
                target_effect=output,
                adapter_output=output,
            )

        blocked = {
            Decision.DENY: "Policy denied the action; nothing reached the target.",
            Decision.ESCALATE: "Action escalated for human review; execution held.",
            Decision.APPROVE: "Approval required and not present; execution held.",
        }.get(policy.decision, "Execution held.")
        return ExecutionResult(
            executed=False,
            decision=policy.decision,
            reason_codes=reasons,
            target_effect=None,
            blocked_reason=blocked,
        )

    @staticmethod
    def _assert_no_substitution(
        request: ActionRequest, plan: Optional[SafePlan]
    ) -> None:
        forbidden = FORBIDDEN_SUBSTITUTIONS.get(request.action)
        if not plan or forbidden is None:
            return
        for step in plan.steps:
            if step.action == forbidden:
                raise SafetyInvariantError(
                    f"forbidden substitution: requested '{request.action}' but plan "
                    f"step '{step.id}' performs '{forbidden}'"
                )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
