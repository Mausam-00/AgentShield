"""AgentShield token-optimisation ROUTING / CACHING / SUBAGENTS layer (Phase 4).

Deterministic, reversible, safety-preserving:

  - model routing     : ModelRouter  (input-signal tiering; never downgrades a
                        risky path; the AUTHORIZATION decision always comes from
                        the deterministic engine regardless of model tier).
  - safe caching      : SafeCache     (canonical-key cache; a hit is returned only
                        when the FULL input incl. policy_version matches, so the
                        decision is provably identical; version change => miss).
  - subagent isolation: IsolatedContext / isolate()  (each delegate gets a bounded,
                        independent context; no cross-delegate bleed).

None of this can weaken safety: routing selects a REASONING model, not a decision;
caching returns a previously-computed identical decision; isolation only bounds and
separates context. The harness asserts routed-economy is never used on a non-ALLOW
or high-impact path, and that every cache hit equals a fresh computation.

Standard library only. No new dependency. Does not touch the agentshield package.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


ECONOMY = "economy"
PREMIUM = "premium"

# Relative, clearly-labelled cost model (NOT real prices): a premium reasoning
# call is modelled as 4x an economy call. Used only to express routing savings.
TIER_COST = {ECONOMY: 1.0, PREMIUM: 4.0}

LOW_IMPACT_MAX = 40  # impact score (0-100 scale) at or below this may qualify for economy


@dataclass(frozen=True)
class RouteSignals:
    read_only: bool
    impact_score: int
    production: bool
    security_sensitive: bool = False


@dataclass
class ModelRouter:
    """Deterministic input-signal router. Fail-safe: defaults to PREMIUM."""

    def tier(self, sig: RouteSignals) -> str:
        if (sig.read_only
                and not sig.production
                and not sig.security_sensitive
                and sig.impact_score <= LOW_IMPACT_MAX):
            return ECONOMY
        return PREMIUM  # anything risky or uncertain routes premium

    def is_safe_route(self, tier: str, decision: str, sig: RouteSignals) -> bool:
        """Economy is only ever valid on a low-risk read-only ALLOW path."""
        if tier == PREMIUM:
            return True
        return (decision == "ALLOW"
                and sig.read_only
                and not sig.production
                and not sig.security_sensitive
                and sig.impact_score <= LOW_IMPACT_MAX)


# --------------------------------------------------------------------------- #
# Safe caching
# --------------------------------------------------------------------------- #
def canonical_key(*, action, target, requester_id, impact_score, posture,
                  policy_version, read_only, production, approval_state) -> str:
    payload = {
        "action": action, "target": target, "requester_id": requester_id,
        "impact_score": impact_score, "posture": posture,
        "policy_version": policy_version, "read_only": read_only,
        "production": production, "approval_state": approval_state,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


@dataclass
class SafeCache:
    _store: dict = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    def get_or_compute(self, key: str, compute):
        if key in self._store:
            self.hits += 1
            return self._store[key], True
        self.misses += 1
        value = compute()
        self._store[key] = value
        return value, False

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return round(self.hits / total, 4) if total else 0.0


# --------------------------------------------------------------------------- #
# Subagent isolation
# --------------------------------------------------------------------------- #
@dataclass
class IsolatedContext:
    delegate_id: str
    input_tokens: int
    tool_tokens: int
    # A private, independent payload store - never shared between delegates.
    private: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.tool_tokens


def isolate(delegate_ids, input_tokens, tool_tokens) -> list:
    """Give each delegate its own bounded, independent context (no shared state)."""
    return [IsolatedContext(d, input_tokens, tool_tokens) for d in delegate_ids]


def no_context_bleed(contexts) -> bool:
    """True iff no two delegates share the same mutable ``private`` object."""
    ids = [id(c.private) for c in contexts]
    return len(ids) == len(set(ids))
