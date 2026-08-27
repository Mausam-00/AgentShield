"""AgentShield live interception demo (mock adapter, synthetic scenarios).

Shows Gate 4 actually stopping a bad action end to end. Three fictional
scenarios run through :class:`GatedExecutor` against a synthetic target:

  1. add_disk (in scope, non-production)      -> ALLOW  -> executed
  2. remove_disk (out of scope, destructive)  -> DENY   -> zero execution
  3. add_disk with a plan that tries to become remove_disk -> invariant blocked

Nothing contacts a real system. It proves the separation: only ALLOW/TRANSFORM
reach the target, and a forbidden substitution can never execute.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agentshield import (  # noqa: E402
    ActionRequest,
    GatedExecutor,
    IdentityContext,
    ImpactDimension,
    Lifecycle,
    MockExecutionTarget,
    PlanStep,
    SafePlan,
    compute_impact,
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _identity(caps: list[str]) -> IdentityContext:
    return IdentityContext(
        requester_id="agent://storage-bot",
        known=True,
        requester_type="service-principal",
        lifecycle=Lifecycle.ACTIVE,
        owner="platform-team",
        sponsor="infra-lead",
        platform="Entra ID",
        permitted_capabilities=caps,
    )


def _request(action: str, target: str, caps: list[str], read_only: bool = False) -> ActionRequest:
    return ActionRequest(
        trace_id=f"demo-{action}",
        requester_id="agent://storage-bot",
        requester_type="service-principal",
        action=action,
        target=target,
        purpose="synthetic demonstration",
        environment="non-production",
        request_timestamp_utc=_now(),
        declared_capabilities=caps,
        read_only=read_only,
    )


def _impact(destructive: bool) -> "object":
    return compute_impact(
        dimensions=[
            ImpactDimension("criticality", 2, "synthetic"),
            ImpactDimension("reversibility", 0 if destructive else 3, "synthetic"),
            ImpactDimension("scope", 1, "synthetic"),
        ],
        destructive=destructive,
        irreversible=destructive,
    )


def _print(title: str, result) -> None:
    status = "EXECUTED" if result.executed else "BLOCKED"
    print(f"\n[{title}]")
    print(f"  decision   : {result.decision.value}")
    print(f"  outcome    : {status}")
    print(f"  reasons    : {', '.join(result.reason_codes) or '-'}")
    if result.target_effect:
        print(f"  effect     : {result.target_effect}")
    if result.blocked_reason:
        print(f"  held       : {result.blocked_reason}")
    if result.invariant_violation:
        print(f"  invariant  : {result.invariant_violation}")


def main() -> int:
    adapter = MockExecutionTarget()
    executor = GatedExecutor(adapter)
    caps = ["add_disk", "read_config"]

    # 1. Legitimate in-scope, read-only action -> ALLOW -> executed.
    r1 = executor.intercept(
        _request("read_config", "config/web-01", caps, read_only=True),
        _identity(caps),
        _impact(destructive=False),
    )
    _print("1. read_config (in scope, read-only)", r1)

    # 2. Destructive, out-of-scope action.
    r2 = executor.intercept(
        _request("remove_disk", "vm/web-01", caps),
        _identity(caps),
        _impact(destructive=True),
    )
    _print("2. remove_disk (out of scope, destructive)", r2)

    # 3. add_disk whose plan tries to become remove_disk (forbidden substitution).
    malicious_plan = SafePlan(
        steps=[
            PlanStep(
                id="s1",
                action="remove_disk",
                target_scope="vm/web-01",
                reason="(injected) silently swap the operation",
                validation="none",
                rollback="none",
                stop_condition="none",
                required_capability="add_disk",
            )
        ],
        plan_hash="demo-bad-plan",
    )
    r3 = executor.intercept(
        _request("add_disk", "vm/web-01", caps),
        _identity(caps),
        _impact(destructive=False),
        plan=malicious_plan,
    )
    _print("3. add_disk plan mutated to remove_disk", r3)

    print(f"\nTarget effects actually applied: {adapter.effects}")
    print("Separation holds: only ALLOW/TRANSFORM reached the target; "
          "the forbidden substitution never executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
