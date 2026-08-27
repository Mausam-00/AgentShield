"""Synthetic mock providers for AgentShield AI.

These implementations are for tests and demonstrations only. They contain no
real identities, credentials, hostnames, or integrations. No ``ExecutionAdapter``
is implemented; ``CONTROLLED LIVE`` stays disabled.
"""

from __future__ import annotations

from typing import Optional

from .models import (
    ActionRequest,
    ApprovalBinding,
    ApprovalRecord,
    ApprovalResult,
    AssuranceResult,
    IdentityContext,
    Lifecycle,
    ObservedOutcome,
    OperationalImpact,
)


class MockIdentityProvider:
    def __init__(self, directory: dict[str, IdentityContext]) -> None:
        self._directory = directory

    def resolve(self, requester_id: str) -> IdentityContext:
        if requester_id in self._directory:
            return self._directory[requester_id]
        # Unknown requesters fail closed.
        return IdentityContext(
            requester_id=requester_id,
            known=False,
            requester_type="unknown",
            lifecycle=Lifecycle.UNKNOWN,
            owner=None,
            sponsor=None,
            platform=None,
            permitted_capabilities=[],
        )


class MockAssuranceEvidenceProvider:
    def __init__(self, records: dict[str, AssuranceResult]) -> None:
        self._records = records

    def latest(self, subject_id: str) -> Optional[AssuranceResult]:
        return self._records.get(subject_id)


class MockInventoryDependencyProvider:
    def __init__(self, impacts: dict[str, OperationalImpact]) -> None:
        self._impacts = impacts

    def impact_for(self, request: ActionRequest) -> OperationalImpact:
        if request.target not in self._impacts:
            raise KeyError(f"no synthetic impact registered for {request.target}")
        return self._impacts[request.target]


class MockApprovalProvider:
    """Deterministic approval decisions keyed by requester for tests."""

    def __init__(
        self,
        decisions: dict[str, ApprovalResult],
        approver: str = "synthetic-approver",
    ) -> None:
        self._decisions = decisions
        self._approver = approver

    def decide(self, binding: ApprovalBinding) -> ApprovalRecord:
        result = self._decisions.get(binding.requester_id, ApprovalResult.PENDING)
        approver = self._approver if result != ApprovalResult.PENDING else None
        return ApprovalRecord(
            result=result,
            approver=approver,
            binding=binding if result == ApprovalResult.APPROVED else None,
        )

    def verify(self, record: ApprovalRecord, binding: ApprovalBinding) -> bool:
        from .approvals import verify_approval

        return verify_approval(record, binding)


class MockOutcomeValidator:
    def __init__(self, outcomes: dict[str, ObservedOutcome]) -> None:
        self._outcomes = outcomes

    def observe(self, request: ActionRequest) -> Optional[ObservedOutcome]:
        return self._outcomes.get(request.trace_id)
