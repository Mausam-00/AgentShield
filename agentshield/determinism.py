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

import hashlib
import inspect
from dataclasses import dataclass
from typing import Callable

from .models import Decision, canonical_hash
from . import policy as _policy
from .policy import CONTROL_CATALOGUE, POLICY_VERSION


def _policy_logic_fingerprint() -> str:
    """SHA-256 over the *actual* source of the decision logic.

    Hashing the source of :func:`evaluate_policy` (plus the private helpers it
    depends on) means any edit to a decision - changing a control's outcome,
    reordering precedence, adding or removing a branch - alters the bundle
    hash. This closes the gap where a hand-mirrored catalogue could drift from
    the real logic while the fingerprint stayed constant.
    """

    sources: list[str] = []
    for name in sorted(dir(_policy)):
        obj = getattr(_policy, name)
        if inspect.isfunction(obj) and obj.__module__ == _policy.__name__:
            try:
                sources.append(inspect.getsource(obj))
            except (OSError, TypeError):  # pragma: no cover - defensive
                sources.append(f"<unavailable:{name}>")
    joined = "\n".join(sources)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


@dataclass
class ReplayReport:
    runs: int
    deterministic: bool
    distinct_decisions: list[str]
    policy_bundle_hash: str
    policy_version: str


def policy_bundle_hash() -> str:
    """Stable fingerprint of the versioned policy contract *and* its logic.

    The hash binds three things together: the policy version, the authoritative
    control catalogue (single-sourced from :mod:`agentshield.policy`), and a
    fingerprint of the real decision-logic source. Changing any one of them
    changes the bundle hash, so the fingerprint cannot silently diverge from the
    code that actually authorizes actions.
    """

    return canonical_hash(
        {
            "policy_version": POLICY_VERSION,
            "controls": CONTROL_CATALOGUE,
            "logic_fingerprint": _policy_logic_fingerprint(),
        }
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
