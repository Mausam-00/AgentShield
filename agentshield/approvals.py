"""Gate 5: human approval.

An approval is valid only when bound to
``requester + action + target + plan_hash + policy_version + expiry`` and not
expired. Timeout is not approval. Rejection, expiry, or a mismatched binding
permits zero executed steps.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .models import (
    ApprovalBinding,
    ApprovalRecord,
    ApprovalResult,
)


def _parse_utc(ts: str) -> datetime:
    value = ts.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_expired(binding: ApprovalBinding, now: Optional[datetime] = None) -> bool:
    now = now or datetime.now(timezone.utc)
    return now > _parse_utc(binding.expiry_utc)


def bindings_match(a: ApprovalBinding, b: ApprovalBinding) -> bool:
    """Every bound field must match exactly."""

    return a.binding_hash() == b.binding_hash()


def verify_approval(
    record: ApprovalRecord,
    required_binding: ApprovalBinding,
    now: Optional[datetime] = None,
) -> bool:
    """Return True only for a genuine, matching, unexpired approval."""

    if record.result != ApprovalResult.APPROVED:
        return False
    if record.binding is None:
        return False
    if not bindings_match(record.binding, required_binding):
        return False
    if is_expired(record.binding, now=now):
        return False
    return True


def approval_permits_execution(
    record: Optional[ApprovalRecord],
    required_binding: ApprovalBinding,
    now: Optional[datetime] = None,
) -> bool:
    if record is None:
        return False
    return verify_approval(record, required_binding, now=now)
