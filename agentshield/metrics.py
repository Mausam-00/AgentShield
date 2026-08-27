"""Prototype: governance metrics that quantify value.

Judges reward measurable impact. This module aggregates the evidence stream and
red-team results into the numbers a demo needs: how many high-risk actions were
blocked, the runtime-decision mix, mean time to a governance decision, and the
attack-success-rate reduction achieved by applying AgentShield's constraints.

All inputs are the package's own synthetic records. No external telemetry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Optional

from .models import EvidenceRecord

_BLOCKING_DECISIONS = {"DENY", "ESCALATE", "APPROVE"}
_EXECUTABLE_DECISIONS = {"ALLOW", "TRANSFORM"}


def _parse(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


@dataclass
class GovernanceMetrics:
    total_actions: int
    decision_mix: dict[str, int]
    high_risk_blocked: int
    executable: int
    block_rate: float
    mean_time_to_govern_s: Optional[float]
    coverage_gap_rate: float
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "total_actions": self.total_actions,
            "decision_mix": self.decision_mix,
            "high_risk_blocked": self.high_risk_blocked,
            "executable": self.executable,
            "block_rate": round(self.block_rate, 4),
            "mean_time_to_govern_s": self.mean_time_to_govern_s,
            "coverage_gap_rate": round(self.coverage_gap_rate, 4),
            "notes": self.notes,
        }


def compute_metrics(
    records: Iterable[EvidenceRecord],
    request_times: Optional[dict[str, str]] = None,
) -> GovernanceMetrics:
    """Aggregate an evidence stream into governance metrics.

    ``request_times`` optionally maps ``trace_id`` -> ISO request timestamp so
    that mean-time-to-govern can be computed as (evidence_time - request_time).
    """

    records = list(records)
    total = len(records)
    mix: dict[str, int] = {}
    high_risk_blocked = 0
    executable = 0
    coverage_gaps = 0
    durations: list[float] = []
    request_times = request_times or {}

    for r in records:
        decision = r.policy_decision or "UNKNOWN"
        mix[decision] = mix.get(decision, 0) + 1
        impact = r.operational_impact_score or 0
        if decision in _BLOCKING_DECISIONS and impact >= 2:
            high_risk_blocked += 1
        if decision in _EXECUTABLE_DECISIONS:
            executable += 1
        if r.coverage_limitations:
            coverage_gaps += 1

        rt = _parse(request_times.get(r.trace_id))
        et = _parse(r.timestamp_utc)
        if rt and et and et >= rt:
            durations.append((et - rt).total_seconds())

    blocking = sum(mix.get(d, 0) for d in _BLOCKING_DECISIONS)
    block_rate = (blocking / total) if total else 0.0
    mttg = (sum(durations) / len(durations)) if durations else None
    gap_rate = (coverage_gaps / total) if total else 0.0

    return GovernanceMetrics(
        total_actions=total,
        decision_mix=mix,
        high_risk_blocked=high_risk_blocked,
        executable=executable,
        block_rate=block_rate,
        mean_time_to_govern_s=mttg,
        coverage_gap_rate=gap_rate,
    )


@dataclass
class AsrReduction:
    baseline_asr: float
    governed_asr: float
    absolute_reduction: float
    relative_reduction: float


def asr_reduction(baseline_asr: float, governed_asr: float) -> AsrReduction:
    """Attack-success-rate reduction from applying AgentShield constraints."""

    baseline_asr = max(0.0, min(1.0, baseline_asr))
    governed_asr = max(0.0, min(1.0, governed_asr))
    absolute = round(baseline_asr - governed_asr, 4)
    relative = round(absolute / baseline_asr, 4) if baseline_asr > 0 else 0.0
    return AsrReduction(baseline_asr, governed_asr, absolute, relative)
