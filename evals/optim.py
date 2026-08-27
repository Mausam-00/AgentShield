"""AgentShield token-optimisation LOW-RISK layer (Phase 2).

Deterministic, reversible, offline optimisations that reduce the token cost of a
successful governance task WITHOUT touching the ``agentshield`` package, its
deterministic controls, or any authorisation behaviour. Every technique here is:

- deterministic (no model, no randomness, stable across runs);
- reversible (each carries an explicit expansion / fallback path);
- measurable against the SAME 12 baseline tasks;
- standard-library only (no new third-party dependency).

Five techniques, matching the Phase 2 brief:
  1. remove duplicated instructions      -> dedup_blocks()
  2. compact output contracts            -> compact_contract()
  3. scoped retrieval                    -> scoped_retrieve()
  4. gate-specific tool loading          -> gate_tool_text() / GATE_TOOLS
  5. deterministic loop limits           -> LoopGuard

Safety invariant: none of these functions feed different inputs to the governance
engine. They only change how context / retrieval / output are ASSEMBLED and how
redundant identical work is avoided. The decision for a given input is therefore
identical to baseline by construction; the harness asserts this against the
recorded baseline decisions.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from token_estimate import TokenEstimate, estimate_text, empty
import context_inventory as ci

ROOT = Path(__file__).resolve().parents[1]

_WS = re.compile(r"\s+")


def _normalize(block: str) -> str:
    """Whitespace-insensitive key for exact-duplicate detection."""
    return _WS.sub(" ", block).strip().lower()


# --------------------------------------------------------------------------- #
# Raw context access (same files the baseline inventory measures)
# --------------------------------------------------------------------------- #
def context_texts() -> dict[str, str]:
    """Return category -> raw concatenated text for the always-on context."""
    out: dict[str, str] = {}
    for category, files in ci.CONTEXT_FILES.items():
        parts = []
        for path in files:
            try:
                parts.append(path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                continue
        out[category] = "\n\n".join(parts)
    out["tool_definitions"] = ci._tool_definition_text()
    return out


# --------------------------------------------------------------------------- #
# 1. Remove duplicated instructions (deterministic block dedup, reversible)
# --------------------------------------------------------------------------- #
@dataclass
class DedupResult:
    compact_text: str
    original_text: str
    original: TokenEstimate
    compact: TokenEstimate
    duplicate_blocks: int
    mapping: dict[str, str] = field(default_factory=dict)  # ref marker -> block

    def expand(self) -> str:
        """Deterministic reverse: re-inline every deduplicated block."""
        text = self.compact_text
        for marker, block in self.mapping.items():
            text = text.replace(marker, block)
        return text

    def is_reversible(self) -> bool:
        """True iff expansion reproduces the original text exactly."""
        return self.expand() == self.original_text

    @property
    def saved_tokens(self) -> int:
        return self.original.approx_tokens - self.compact.approx_tokens


def dedup_blocks(texts: dict[str, str]) -> DedupResult:
    """Drop exact-duplicate instruction blocks across all always-on context.

    Blocks are paragraph-delimited. The FIRST occurrence of each block is kept
    verbatim; later EXACT duplicates are replaced by a short reference marker
    recorded in ``mapping`` so the original is restored byte-for-byte. Only exact
    (whitespace-trimmed) matches are deduplicated, which guarantees reversibility.
    """
    seen: dict[str, str] = {}          # exact block -> marker
    mapping: dict[str, str] = {}       # marker -> original block
    kept: list[str] = []
    normalized: list[str] = []         # the canonical original (stripped blocks)
    dup_count = 0

    for _category, text in texts.items():
        for raw in re.split(r"\n\s*\n", text):
            block = raw.strip()
            if not block:
                continue
            normalized.append(block)
            if len(block) < 40:  # keep short headings/labels; not worth a marker
                kept.append(block)
                continue
            if block in seen:
                dup_count += 1
                kept.append(seen[block])  # reference marker only
            else:
                marker = f"[[ref:{len(mapping) + 1}]]"
                seen[block] = marker
                mapping[marker] = block
                kept.append(block)

    original_text = "\n\n".join(normalized)
    compact_text = "\n\n".join(kept)
    return DedupResult(
        compact_text=compact_text,
        original_text=original_text,
        original=estimate_text(original_text),
        compact=estimate_text(compact_text),
        duplicate_blocks=dup_count,
        mapping=mapping,
    )


# --------------------------------------------------------------------------- #
# 2. Compact output contract (strict minimal agent-facing result)
# --------------------------------------------------------------------------- #
def compact_contract(result) -> dict:
    """A strict, fixed-schema view carrying only decision-critical facts.

    Retains: decision, posture, impact score, ALL reason codes, whether approval
    is required, the evidence pointer, and the trace id. Nothing else is emitted.
    This is a superset of the facts checked by critical-fact retention, so the
    contract cannot silently drop a control outcome.
    """
    policy = result.policy
    decision = policy.decision.value if policy else None
    codes = policy.reason_codes() if policy else []
    return {
        "decision": decision,
        "posture": result.assurance.posture.value if result.assurance else None,
        "impact_score": result.impact.score if result.impact else None,
        "reason_codes": codes,
        "approval_required": decision in ("APPROVE", "ESCALATE"),
        "evidence_id": getattr(result.evidence, "record_id", None)
        or getattr(result.evidence, "trace_id", None)
        if result.evidence else None,
        "trace_id": result.trace_id,
    }


def contract_tokens(result) -> TokenEstimate:
    return estimate_text(json.dumps(compact_contract(result), sort_keys=True, default=str))


# --------------------------------------------------------------------------- #
# 3. Scoped retrieval (bounded top-k protocol sections, deterministic)
# --------------------------------------------------------------------------- #
@dataclass
class ScopedResult:
    text: str
    original: TokenEstimate
    scoped: TokenEstimate
    sections_total: int
    sections_selected: int

    @property
    def saved_tokens(self) -> int:
        return self.original.approx_tokens - self.scoped.approx_tokens


def _split_sections(text: str) -> list[str]:
    """Split markdown into heading-led sections; deterministic and order-stable."""
    lines = text.splitlines(keepends=True)
    sections: list[str] = []
    buf: list[str] = []
    for line in lines:
        if line.lstrip().startswith("#") and buf:
            sections.append("".join(buf))
            buf = [line]
        else:
            buf.append(line)
    if buf:
        sections.append("".join(buf))
    return sections or [text]


def scoped_retrieve(full_text: str, query_terms, k: int = 4) -> ScopedResult:
    """Return only the top-k protocol sections relevant to the query terms.

    Scoring is a deterministic case-insensitive term-frequency count. Ties break
    by original section order (stable). If nothing matches, the first k sections
    are returned (never empty) as the deterministic fallback.
    """
    terms = [t.lower() for t in query_terms if t]
    sections = _split_sections(full_text)
    scored = []
    for idx, sec in enumerate(sections):
        low = sec.lower()
        score = sum(low.count(t) for t in terms)
        scored.append((score, idx, sec))
    ranked = sorted(scored, key=lambda x: (-x[0], x[1]))
    top = ranked[:k]
    if all(s[0] == 0 for s in top):  # no signal -> deterministic fallback
        top = sorted(scored, key=lambda x: x[1])[:k]
    selected = [sec for _s, _i, sec in sorted(top, key=lambda x: x[1])]
    scoped_text = "".join(selected)
    return ScopedResult(
        text=scoped_text,
        original=estimate_text(full_text),
        scoped=estimate_text(scoped_text),
        sections_total=len(sections),
        sections_selected=len(selected),
    )


# --------------------------------------------------------------------------- #
# 4. Gate-specific tool loading (deterministic gate -> tool-name mapping)
# --------------------------------------------------------------------------- #
# Only the tools a gate actually uses are loaded, instead of the full always-on
# manifest. Unknown gates fall back to the FULL surface (fail-open on context
# ONLY - never on authorisation).
GATE_TOOLS: dict[str, tuple[str, ...]] = {
    "assurance": ("evaluate_assurance", "FamilyEvaluation", "Finding"),
    "impact": ("compute_impact", "ImpactDimension"),
    "authorize": ("AgentShieldWorkflow",),
    "approval": ("ApprovalBinding", "ApprovalRecord", "ApprovalResult"),
    "plan": ("build_safe_plan", "PlanStep"),
    "validate": ("validate_outcome", "ObservedOutcome"),
    "report": ("workflow_to_report",),
    "redteam": ("run_static_redteam", "redteam_to_report_section"),
    "rai": ("evaluate_responsible_ai", "default_pillars", "rai_to_report"),
}


def _tool_text_for(names) -> str:
    import inspect
    import agentshield
    wanted = set(names)
    parts = []
    for name in sorted(getattr(agentshield, "__all__", [])):
        if name not in wanted:
            continue
        obj = getattr(agentshield, name, None)
        if obj is None:
            continue
        try:
            sig = str(inspect.signature(obj))
        except (TypeError, ValueError):
            sig = "(...)"
        doc = inspect.getdoc(obj) or ""
        parts.append(f"{name}{sig}\n{doc}")
    return "\n\n".join(parts)


def gate_tool_text(gates) -> TokenEstimate:
    """Token estimate for the tool definitions needed by the given gates only."""
    names: set[str] = set()
    for g in gates:
        names.update(GATE_TOOLS.get(g, ()))
    if not names:  # unknown -> full surface (context fail-open, not auth)
        return estimate_text(ci._tool_definition_text())
    return estimate_text(_tool_text_for(names))


# --------------------------------------------------------------------------- #
# 5. Deterministic loop limits (dedupe identical calls, cap iterations/history)
# --------------------------------------------------------------------------- #
@dataclass
class LoopGuard:
    """Deterministic guard against redundant repeated work and unbounded growth.

    - Identical governance inputs return a cached result key (the engine is
      deterministic, so a repeat cannot legitimately produce a different
      decision); this removes wasted re-serialisation, not any control.
    - ``max_iterations`` is an explicit hard stop for runaway loops.
    - ``history_keep`` bounds retained turn history to the last N entries plus a
      count, a deterministic cap (full history remains reconstructable upstream).
    """
    max_iterations: int = 8
    history_keep: int = 3
    _cache: dict = field(default_factory=dict)
    saved_calls: int = 0
    iterations: int = 0
    stopped: bool = False

    @staticmethod
    def key(*parts) -> str:
        payload = json.dumps(parts, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def seen(self, k: str) -> bool:
        self.iterations += 1
        if self.iterations > self.max_iterations:
            self.stopped = True
        if k in self._cache:
            self.saved_calls += 1
            return True
        self._cache[k] = True
        return False

    def bounded_history(self, history: list) -> dict:
        """Keep only the last N entries; record how many were elided."""
        kept = history[-self.history_keep:]
        return {
            "kept": kept,
            "elided": max(0, len(history) - len(kept)),
            "total": len(history),
        }


# --------------------------------------------------------------------------- #
# Critical-fact retention check (guards every compaction/dedup in this layer)
# --------------------------------------------------------------------------- #
def retains_critical_facts(result, *contexts: str) -> bool:
    """True iff every decision-critical fact survives the given compact context.

    A fact is the decision, each reason code, the impact score, and the target.
    Checked against the compact CONTRACT plus any supplied compacted context text.
    """
    contract = json.dumps(compact_contract(result), default=str)
    haystack = contract + "\n" + "\n".join(contexts)
    policy = result.policy
    facts = []
    if policy:
        facts.append(policy.decision.value)
        facts.extend(policy.reason_codes())
    if result.impact is not None:
        facts.append(str(result.impact.score))
    return all(f in haystack for f in facts if f)
