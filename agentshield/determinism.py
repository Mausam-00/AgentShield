"""Prototype: determinism proof for the deterministic-policy layer.

AgentShield's core claim is that runtime authorization is *deterministic*: the
same facts always yield the same decision, unlike an LLM that can drift. This
module makes that claim testable.

- :func:`policy_bundle_hash` produces a stable hash over the versioned control
  table, so any change to the policy logic changes the fingerprint.
- :func:`replay` runs the same decision N times and asserts a single distinct
  outcome, returning a :class:`ReplayReport` suitable for CI evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .models import Decision, canonical_hash
from .policy import POLICY_VERSION

# The versioned control catalogue, mirrored here as the deterministic contract.
# (control_id, reason_code, decision, tier) - the tuple that must not change
# without a policy-version bump.
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
class ReplayReport:
    runs: int
    deterministic: bool
    distinct_decisions: list[str]
    policy_bundle_hash: str
    policy_version: str


def policy_bundle_hash() -> str:
    """Stable fingerprint of the versioned policy contract."""

    return canonical_hash(
        {"policy_version": POLICY_VERSION, "controls": CONTROL_CATALOGUE}
    )


def replay(decision_fn: Callable[[], Decision], runs: int = 100) -> ReplayReport:
    """Run ``decision_fn`` ``runs`` times and verify a single distinct outcome."""

    if runs < 1:
        raise ValueError("runs must be >= 1")
    seen: list[str] = []
    for _ in range(runs):
        seen.append(decision_fn().value)
    distinct = sorted(set(seen))
    return ReplayReport(
        runs=runs,
        deterministic=len(distinct) == 1,
        distinct_decisions=distinct,
        policy_bundle_hash=policy_bundle_hash(),
        policy_version=POLICY_VERSION,
    )
