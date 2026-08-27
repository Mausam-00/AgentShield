"""AgentShield token-optimisation GOVERNANCE layer (Phase 5).

Deterministic token budgets, telemetry, warnings, and hard stop controls, plus
efficiency evidence generation. Mirrors the engine's fail-closed philosophy: when
a budget is exhausted the response is a deterministic STOP, never a silent
continue.

  - TokenBudget       : per-task and per-session budgets with WARN and STOP.
  - Telemetry         : structured, append-only per-task records.
  - efficiency_evidence: consolidated, measured savings vs the baseline.
  - policy immutability: this layer NEVER changes policy or a decision; policy
                        changes remain the deterministic engine's authority and
                        require human approval (asserted by the harness/tests).

Standard library only. No new dependency. Does not touch the agentshield package.
"""

from __future__ import annotations

from dataclasses import dataclass, field


OK = "OK"
WARN = "WARN"
STOP = "STOP"


@dataclass
class BudgetEvent:
    scope: str          # "task" or "session"
    name: str
    status: str
    charged: int
    limit: int
    used: int


@dataclass
class TokenBudget:
    """Deterministic token budget with a warn threshold and a hard stop.

    ``charge`` returns OK / WARN / STOP. STOP means the limit is exhausted and the
    caller must halt - a deterministic control, not advisory. Nothing here mutates
    any authorization decision; it only governs continued token spend.
    """
    per_task_limit: int
    session_limit: int
    warn_ratio: float = 0.8
    session_used: int = 0
    events: list = field(default_factory=list)

    def charge(self, name: str, tokens: int) -> str:
        status = OK
        # Per-task ceiling.
        if tokens > self.per_task_limit:
            status = STOP
            self.events.append(BudgetEvent("task", name, STOP, tokens,
                                           self.per_task_limit, tokens))
        elif tokens >= self.per_task_limit * self.warn_ratio:
            status = WARN
            self.events.append(BudgetEvent("task", name, WARN, tokens,
                                           self.per_task_limit, tokens))
        # Session ceiling (only accrue if the task itself was not a hard STOP).
        if status != STOP:
            self.session_used += tokens
            if self.session_used > self.session_limit:
                status = STOP
                self.events.append(BudgetEvent("session", name, STOP, tokens,
                                               self.session_limit, self.session_used))
            elif self.session_used >= self.session_limit * self.warn_ratio and status == OK:
                status = WARN
                self.events.append(BudgetEvent("session", name, WARN, tokens,
                                               self.session_limit, self.session_used))
        return status

    def stopped(self) -> bool:
        return any(e.status == STOP for e in self.events)


@dataclass
class Telemetry:
    records: list = field(default_factory=list)

    def record(self, **fields) -> None:
        self.records.append(dict(fields))

    def total(self, key: str) -> float:
        return sum(r.get(key, 0) for r in self.records)


def efficiency_evidence(*, baseline_sum, phase2_sum, phase3_sum, final_sum,
                        cost_baseline, cost_routed, cache_hit_rate,
                        budget_events, telemetry) -> dict:
    """Consolidated, measured efficiency evidence (no extrapolated numbers)."""
    def pct(a, b):
        return round(100.0 * (a - b) / a, 1) if a else None

    return {
        "token_reduction_pct_vs_baseline": pct(baseline_sum, final_sum),
        "tokens_baseline": baseline_sum,
        "tokens_phase2": phase2_sum,
        "tokens_phase3": phase3_sum,
        "tokens_final": final_sum,
        "relative_cost_baseline_units": round(cost_baseline, 2),
        "relative_cost_routed_units": round(cost_routed, 2),
        "relative_cost_reduction_pct": pct(cost_baseline, cost_routed),
        "cache_hit_rate": cache_hit_rate,
        "budget_warn_events": sum(1 for e in budget_events if e.status == WARN),
        "budget_stop_events": sum(1 for e in budget_events if e.status == STOP),
        "telemetry_task_count": len(telemetry.records),
        "note": (
            "Token figures are the disclosed chars/4 approximation; cost units are "
            "a labelled relative model (premium = 4x economy), NOT real prices. "
            "All values are measured over the 12 baseline tasks."
        ),
    }
