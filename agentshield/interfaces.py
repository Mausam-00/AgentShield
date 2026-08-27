"""Provider interfaces for AgentShield AI.

These are the logical seams the protocol requires. Real deployments would supply
authenticated, least-privileged implementations behind these interfaces. This
repository ships only synthetic mocks (see ``mock_providers.py``).

The ``ExecutionAdapter`` interface is intentionally present but has no live
implementation. ``CONTROLLED LIVE`` remains disabled by default.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from .models import (
    ActionRequest,
    ApprovalBinding,
    ApprovalRecord,
    AssuranceResult,
    EvidenceRecord,
    IdentityContext,
    ObservedOutcome,
    OperationalImpact,
    PolicyResult,
)


@runtime_checkable
class IdentityProvider(Protocol):
    def resolve(self, requester_id: str) -> IdentityContext: ...


@runtime_checkable
class AssuranceEvidenceProvider(Protocol):
    def latest(self, subject_id: str) -> Optional[AssuranceResult]: ...


@runtime_checkable
class InventoryDependencyProvider(Protocol):
    def impact_for(self, request: ActionRequest) -> OperationalImpact: ...


@runtime_checkable
class DeterministicPolicyProvider(Protocol):
    def evaluate(self, *args, **kwargs) -> PolicyResult: ...


@runtime_checkable
class ApprovalProvider(Protocol):
    def decide(self, binding: ApprovalBinding) -> ApprovalRecord: ...

    def verify(self, record: ApprovalRecord, binding: ApprovalBinding) -> bool: ...


@runtime_checkable
class OutcomeValidator(Protocol):
    def observe(self, request: ActionRequest) -> Optional[ObservedOutcome]: ...


@runtime_checkable
class AppendOnlyEvidenceStore(Protocol):
    def append(self, record: EvidenceRecord) -> None: ...

    def all(self) -> list[EvidenceRecord]: ...


class ExecutionAdapter(Protocol):
    """Future optional adapter. No live implementation is provided.

    An adapter declaration must specify supported actions, supported target
    types, authentication method, required permission scope, dry-run and
    rollback capability, health/timeout behavior, audit events, failure mode,
    and kill-switch behavior before it may be enabled.
    """

    enabled: bool
    supported_actions: list[str]
    supported_target_types: list[str]

    def dry_run(self, *args, **kwargs) -> object: ...

    def execute(self, *args, **kwargs) -> object: ...
