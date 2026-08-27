"""AgentShield AI workflow orchestrator.

Wires the seven gates across the ASSESS, OBSERVE, and GOVERN modes. AgentShield
itself never executes against a target; GOVERN produces an authorization
decision and a constrained plan but does not run it. CONTROLLED LIVE is disabled.

Every governance path produces an append-only evidence record.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from . import approvals as approvals_mod
from .evidence import InMemoryEvidenceStore, build_evidence
from .impact import compute_impact
from .models import (
    ActionRequest,
    ApprovalBinding,
    ApprovalRecord,
    ApprovalResult,
    AssuranceResult,
    Decision,
    FamilyEvaluation,
    Finding,
    IdentityContext,
    Mode,
    OperationalImpact,
    SafePlan,
    WorkflowResult,
)
from .policy import PolicyConfig, evaluate_policy
from .assurance import evaluate_assurance


class AgentShieldWorkflow:
    def __init__(
        self,
        evidence_store: Optional[InMemoryEvidenceStore] = None,
        policy_config: Optional[PolicyConfig] = None,
    ) -> None:
        self.evidence_store = (
            evidence_store if evidence_store is not None else InMemoryEvidenceStore()
        )
        self.policy_config = policy_config or PolicyConfig()

    # ------------------------------------------------------------------ #
    # Gate 0 (ASSESS)
    # ------------------------------------------------------------------ #
    def assess(
        self,
        subject: str,
        families: list[FamilyEvaluation],
        findings: Optional[list[Finding]] = None,
        definition_text: Optional[str] = None,
        tool_manifest_text: Optional[str] = None,
        write_capable: bool = True,
    ) -> AssuranceResult:
        return evaluate_assurance(
            subject=subject,
            families=families,
            findings=findings,
            definition_text=definition_text,
            tool_manifest_text=tool_manifest_text,
            write_capable=write_capable,
        )

    # ------------------------------------------------------------------ #
    # Gates 1-4 shared evaluation
    # ------------------------------------------------------------------ #
    def _evaluate(
        self,
        request: ActionRequest,
        identity: IdentityContext,
        assurance: Optional[AssuranceResult],
        impact: OperationalImpact,
        *,
        approval_rejected_or_expired: bool = False,
        observed_deviation: bool = False,
        adapter_failed: bool = False,
        large_reversible_batchable: bool = False,
    ):
        return evaluate_policy(
            request,
            identity,
            assurance,
            impact,
            config=self.policy_config,
            approval_rejected_or_expired=approval_rejected_or_expired,
            observed_deviation=observed_deviation,
            adapter_failed=adapter_failed,
            large_reversible_batchable=large_reversible_batchable,
            # A read-only operation is not affected by a write-capability
            # critical finding; write operations remain gated by ASP-004.
            critical_finding_affects_action=not request.read_only,
        )

    # ------------------------------------------------------------------ #
    # OBSERVE mode (no enforcement, no execution)
    # ------------------------------------------------------------------ #
    def observe(
        self,
        request: ActionRequest,
        identity: IdentityContext,
        assurance: Optional[AssuranceResult],
        impact: OperationalImpact,
        **kwargs,
    ) -> WorkflowResult:
        policy = self._evaluate(request, identity, assurance, impact, **kwargs)
        evidence = build_evidence(
            mode=Mode.OBSERVE,
            request=request,
            identity=identity,
            assurance=assurance,
            impact=impact,
            policy=policy,
            approval=None,
            plan=None,
            validation=None,
            outcome=f"predicted:{policy.decision.value}",
            expected_behavior=f"{request.action} on {request.target}",
        )
        self.evidence_store.append(evidence)
        return WorkflowResult(
            mode=Mode.OBSERVE,
            trace_id=request.trace_id,
            assurance=assurance,
            impact=impact,
            policy=policy,
            evidence=evidence,
            nothing_reached_target=True,
        )

    # ------------------------------------------------------------------ #
    # GOVERN mode (enforce policy, route approval, no execution)
    # ------------------------------------------------------------------ #
    def govern(
        self,
        request: ActionRequest,
        identity: IdentityContext,
        assurance: Optional[AssuranceResult],
        impact: OperationalImpact,
        *,
        plan: Optional[SafePlan] = None,
        approval: Optional[ApprovalRecord] = None,
        large_reversible_batchable: bool = False,
        now: Optional[datetime] = None,
    ) -> WorkflowResult:
        # Gate 1: interception contract validation.
        missing = request.missing_required()
        limitations: list[str] = []
        if missing:
            limitations.append(
                "Incomplete request contract: " + ", ".join(missing)
            )

        # Gate 4: deterministic policy (initial pass).
        policy = self._evaluate(
            request,
            identity,
            assurance,
            impact,
            large_reversible_batchable=large_reversible_batchable,
        )

        approval_record = approval
        # Gate 5: if approval is required, verify binding & expiry.
        if policy.decision == Decision.APPROVE:
            binding = self._binding_for(request, plan, now=now)
            if not approvals_mod.approval_permits_execution(
                approval_record, binding, now=now
            ):
                # Re-evaluate with approval failure to force DENY.
                rejected = (
                    approval_record is not None
                    and approval_record.result
                    in (ApprovalResult.REJECTED, ApprovalResult.PENDING,
                        ApprovalResult.RETURNED_FOR_REVISION)
                )
                expired = approval_record is not None and (
                    approval_record.binding is not None
                    and approvals_mod.is_expired(approval_record.binding, now=now)
                )
                policy = self._evaluate(
                    request,
                    identity,
                    assurance,
                    impact,
                    approval_rejected_or_expired=rejected or expired,
                    large_reversible_batchable=large_reversible_batchable,
                )

        outcome = f"decision:{policy.decision.value}"
        evidence = build_evidence(
            mode=Mode.GOVERN,
            request=request,
            identity=identity,
            assurance=assurance,
            impact=impact,
            policy=policy,
            approval=approval_record,
            plan=plan if policy.decision in (Decision.ALLOW, Decision.TRANSFORM) else plan,
            validation=None,
            outcome=outcome,
            expected_behavior=f"{request.action} on {request.target}",
        )
        self.evidence_store.append(evidence)

        result = WorkflowResult(
            mode=Mode.GOVERN,
            trace_id=request.trace_id,
            assurance=assurance,
            impact=impact,
            policy=policy,
            approval=approval_record,
            plan=plan,
            evidence=evidence,
            limitations=limitations,
            nothing_reached_target=True,
        )
        return result

    def _binding_for(
        self,
        request: ActionRequest,
        plan: Optional[SafePlan],
        now: Optional[datetime] = None,
    ) -> ApprovalBinding:
        now = now or datetime.now(timezone.utc)
        expiry = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return ApprovalBinding(
            requester_id=request.requester_id,
            action=request.action,
            target=request.target,
            plan_hash=plan.plan_hash if plan else "no-plan",
            policy_version=self.policy_config.version,
            expiry_utc=expiry,
        )
