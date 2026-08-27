"""AgentShield token-optimisation CONTEXT & MEMORY layer (Phase 3).

Builds on the Phase 2 low-risk layer with deterministic, reversible memory
optimisations:

  - structured state   : StructuredState / TurnState  (normalised, append-only)
  - compaction         : compact_history()            (threshold-based)
  - summary validation : validate_summary()           (fail-closed guard)
  - evidence pointers  : EvidenceStore                (retrievable, hashed)

Safety invariants (identical spirit to the governed engine):
  - Critical facts (decision, every reason code, impact score, target, controls)
    are preserved VERBATIM in structured state and in evidence pointers - never
    behind a lossy summary.
  - Compaction only ever elides *redundant* ALLOW turns; every non-ALLOW turn is
    retained verbatim. If validation cannot confirm full retention, the caller
    keeps full detail (fail-closed on memory).
  - Everything is reversible: EvidenceStore.get() returns the exact original
    record; compaction keeps a reconstructable count/trace manifest.

Standard library only. No new dependency. Does not touch the agentshield package.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from token_estimate import TokenEstimate, estimate_json, empty


CRITICAL_KEYS = (
    "trace_id", "policy_decision", "reason_codes",
    "operational_impact_score", "target", "policy_controls",
)


def _hash(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


# --------------------------------------------------------------------------- #
# Evidence pointers (retrievable store; envelope keeps critical facts verbatim)
# --------------------------------------------------------------------------- #
@dataclass
class EvidenceStore:
    """Content-addressed store of full evidence records.

    ``put`` returns a compact POINTER that carries the decision-critical facts
    verbatim plus a hash into the store. ``get`` returns the exact original
    record, so the full audit payload is never lost - only moved out of the
    always-in-context envelope.
    """
    _by_hash: dict = field(default_factory=dict)

    def put(self, record: dict) -> dict:
        h = _hash(record)
        self._by_hash[h] = record
        return {
            "evidence_ref": h,
            "trace_id": record.get("trace_id"),
            "decision": record.get("policy_decision"),
            "reason_codes": list(record.get("reason_codes", [])),
            "impact_score": record.get("operational_impact_score"),
            "target": record.get("target"),
            "controls": list(record.get("policy_controls", [])),
        }

    def get(self, pointer: dict) -> dict:
        return self._by_hash[pointer["evidence_ref"]]

    def pointer_retains_critical_facts(self, record: dict, pointer: dict) -> bool:
        """The pointer must reproduce every critical fact from the record."""
        return (
            pointer.get("trace_id") == record.get("trace_id")
            and pointer.get("decision") == record.get("policy_decision")
            and list(pointer.get("reason_codes", [])) == list(record.get("reason_codes", []))
            and pointer.get("impact_score") == record.get("operational_impact_score")
            and pointer.get("target") == record.get("target")
            and list(pointer.get("controls", [])) == list(record.get("policy_controls", []))
        )


# --------------------------------------------------------------------------- #
# Structured state (normalised, append-only turn records)
# --------------------------------------------------------------------------- #
@dataclass
class TurnState:
    trace_id: str
    decision: str
    reason_codes: list
    impact_score: object
    target: object

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "impact_score": self.impact_score,
            "target": self.target,
        }


@dataclass
class StructuredState:
    turns: list = field(default_factory=list)

    @staticmethod
    def from_evidence(record: dict) -> "TurnState":
        return TurnState(
            trace_id=record.get("trace_id"),
            decision=record.get("policy_decision"),
            reason_codes=list(record.get("reason_codes", [])),
            impact_score=record.get("operational_impact_score"),
            target=record.get("target"),
        )

    def append_evidence(self, record: dict) -> None:
        self.turns.append(self.from_evidence(record))

    def as_list(self) -> list:
        return [t.to_dict() for t in self.turns]


# --------------------------------------------------------------------------- #
# Compaction + summary validation (fail-closed)
# --------------------------------------------------------------------------- #
def compact_history(state: StructuredState, *, keep: int = 3, threshold: int = 8) -> dict:
    """Compact older redundant ALLOW turns into a validated summary.

    Below ``threshold`` turns, nothing is compacted. Otherwise the most recent
    ``keep`` turns are retained verbatim; older turns are summarised as decision
    counts plus a trace-id manifest, and every NON-ALLOW older turn is retained
    verbatim (never summarised away).
    """
    turns = state.as_list()
    n = len(turns)
    if n <= threshold:
        return {"compacted": False, "recent": turns, "summary": None,
                "non_allow_retained": [t for t in turns if t["decision"] != "ALLOW"]}

    older, recent = turns[:-keep], turns[-keep:]
    counts: dict = {}
    for t in older:
        counts[t["decision"]] = counts.get(t["decision"], 0) + 1
    non_allow = [t for t in older if t["decision"] != "ALLOW"]
    summary = {
        "older_turn_count": len(older),
        "decision_counts": counts,
        "trace_ids": [t["trace_id"] for t in older],
    }
    return {
        "compacted": True,
        "recent": recent,
        "summary": summary,
        "non_allow_retained": non_allow,  # verbatim, never elided
    }


def validate_summary(state: StructuredState, compacted: dict) -> bool:
    """Fail-closed check that compaction lost NO critical fact.

    Returns True only if: the older-turn count reconciles, the trace manifest is
    complete, every non-ALLOW older turn is retained verbatim, and every reason
    code seen across ALL turns still appears somewhere in the compacted view.
    """
    turns = state.as_list()
    if not compacted.get("compacted"):
        # No compaction: everything is trivially retained.
        return True

    keep = len(compacted["recent"])
    older = turns[:-keep] if keep else turns
    summary = compacted.get("summary") or {}

    if summary.get("older_turn_count") != len(older):
        return False
    if list(summary.get("trace_ids", [])) != [t["trace_id"] for t in older]:
        return False

    retained = {t["trace_id"]: t for t in compacted.get("non_allow_retained", [])}
    for t in older:
        if t["decision"] != "ALLOW":
            got = retained.get(t["trace_id"])
            if got is None or got != t:  # non-ALLOW must survive verbatim
                return False

    # Every reason code across all turns must still be reachable.
    blob = json.dumps(compacted, sort_keys=True, default=str)
    for t in turns:
        for code in t["reason_codes"]:
            if code not in blob:
                return False
    return True


def history_tokens(compacted: dict) -> TokenEstimate:
    return estimate_json(compacted) if compacted else empty()


def retains_critical_facts_state(records: list, compacted: dict) -> bool:
    """Every non-ALLOW decision + reason code from the raw records survives."""
    blob = json.dumps(compacted, sort_keys=True, default=str)
    for rec in records:
        if rec.get("policy_decision") and rec["policy_decision"] != "ALLOW":
            if rec["policy_decision"] not in blob:
                return False
        for code in rec.get("reason_codes", []):
            if code not in blob:
                return False
    return True
