"""AgentShield AI — synthetic end-to-end demonstration.

Runs several fictional scenarios through the seven-gate workflow and prints the
assurance posture and runtime decision for each, showing that the two remain
separate. With ``--report PATH`` it writes an HTML report for the last scenario
using the explicit-trigger generator (simulating a user's explicit request).

Nothing here contacts a live system. All identities and targets are fictional.

Usage:
    python examples/demo.py
    python examples/demo.py --report demo-report.html
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

# Make the package importable when run from the repo root or elsewhere.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agentshield import (  # noqa: E402
    ActionRequest,
    AgentShieldWorkflow,
    ApprovalRecord,
    ApprovalResult,
    EvidenceState,
    FamilyEvaluation,
    Finding,
    IdentityContext,
    ImpactDimension,
    Lifecycle,
    ObservedOutcome,
    PlanStep,
    Severity,
    build_safe_plan,
    compute_impact,
    deviation_finding,
    evaluate_assurance,
    lifecycle_recommendation,
    validate_outcome,
    workflow_to_report,
)
from agentshield.assurance import CONTROL_FAMILIES  # noqa: E402


def _families(maturity=4, state=EvidenceState.TESTED):
    return [
        FamilyEvaluation(fid, name, weight, maturity, state)
        for fid, name, weight in CONTROL_FAMILIES
    ]


def _identity(**kw):
    base = dict(
        requester_id="svc-fictional",
        known=True,
        requester_type="service-agent",
        lifecycle=Lifecycle.ACTIVE,
        owner="fictional-owner",
        sponsor="fictional-sponsor",
        platform="fictional-platform",
        permitted_capabilities=["read_config", "add_disk"],
        assurance_age_days=2.0,
        tool_manifest_changed=False,
    )
    base.update(kw)
    return IdentityContext(**base)


def _request(**kw):
    base = dict(
        trace_id="trace-demo",
        requester_id="svc-fictional",
        requester_type="service-agent",
        action="read_config",
        target="fictional-target",
        purpose="demonstration",
        environment="non-production",
        request_timestamp_utc="2026-01-01T00:00:00Z",
        read_only=True,
    )
    base.update(kw)
    return ActionRequest(**base)


def _low_impact(**kw):
    return compute_impact(
        [
            ImpactDimension("target criticality", 1, "fictional"),
            ImpactDimension("reversibility", 1, "fictional"),
        ],
        **kw,
    )


def _high_impact(**kw):
    return compute_impact(
        [
            ImpactDimension("target criticality", 4, "fictional"),
            ImpactDimension("data sensitivity", 3, "fictional"),
            ImpactDimension("reversibility", 4, "fictional"),
        ],
        **kw,
    )


def banner(title):
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)


def show(result):
    posture = result.assurance.posture.value if result.assurance else "n/a"
    decision = result.policy.decision.value if result.policy else "n/a"
    codes = ", ".join(result.policy.reason_codes()) if result.policy else ""
    print(f"  Assurance posture : {posture}")
    print(f"  Runtime decision  : {decision}")
    print(f"  Reason codes      : {codes}")


def main(argv):
    parser = argparse.ArgumentParser(description="AgentShield AI demo")
    parser.add_argument("--report", metavar="PATH", help="explicit HTML report path")
    args = parser.parse_args(argv)

    wf = AgentShieldWorkflow()
    passing = evaluate_assurance("fictional-agent", _families(), findings=[])
    last_result = None

    banner("Scenario 1 - read-only, in-scope (expect ALLOW)")
    last_result = wf.govern(
        _request(action="read_config", read_only=True),
        _identity(),
        passing,
        _low_impact(),
    )
    show(last_result)

    banner("Scenario 2 - BLOCK posture attempts a write (expect DENY)")
    critical = Finding(
        id="F-CRIT-DEMO",
        control_family="ASF-03",
        severity=Severity.CRITICAL,
        title="Unauthenticated write capability",
        condition="Write tool exposed without authentication.",
        evidence_state=EvidenceState.OBSERVED,
        observation="Fictional critical finding.",
        remediation="Require authentication.",
    )
    blocking = evaluate_assurance("fictional-agent", _families(), findings=[critical])
    last_result = wf.govern(
        _request(action="add_disk", read_only=False, environment="non-production"),
        _identity(),
        blocking,
        _low_impact(),
    )
    show(last_result)

    banner("Scenario 3 - production write, rejected approval (expect DENY)")
    last_result = wf.govern(
        _request(action="add_disk", read_only=False, environment="production"),
        _identity(),
        passing,
        _high_impact(),
        approval=ApprovalRecord(
            result=ApprovalResult.REJECTED, approver="fictional-approver", binding=None
        ),
    )
    show(last_result)

    banner("Scenario 4 - safe plan + observed deviation (expect QUARANTINE advice)")
    req = _request(action="add_disk", read_only=False)
    plan = build_safe_plan(
        req,
        ["add_disk"],
        [
            PlanStep(
                "s1", "add_disk", "fictional-target",
                "add capacity per request", "verify disk attached",
                "detach disk", "stop if attach fails", "add_disk",
            )
        ],
    )
    observed = ObservedOutcome(
        action="remove_disk", target="fictional-target", outcome="success"
    )
    validation = validate_outcome("add_disk", "fictional-target", plan, observed)
    finding = deviation_finding(validation, req.trace_id)
    print(f"  Deviated          : {validation.deviated}")
    print(f"  Deviation finding : {finding.severity.value} - {finding.title}")
    print(f"  Lifecycle advice  : {lifecycle_recommendation(validation)}")

    # Explicit report generation only when the user asks for it.
    if args.report:
        banner("Explicit request - generating HTML report for Scenario 3")
        report = workflow_to_report(last_result, simulation=True)
        gen = _load_generator()
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as handle:
            json.dump(report, handle)
            json_path = handle.name
        gen.generate(json_path, args.report)
        Path(json_path).unlink(missing_ok=True)
        print(f"  Report written    : {args.report}")

    print("\nAll scenarios are simulated. PASS is not certification.")
    return 0


def _load_generator():
    path = (
        ROOT
        / ".github"
        / "skills"
        / "agentshield-html-report"
        / "scripts"
        / "generate_report.py"
    )
    spec = importlib.util.spec_from_file_location("generate_report", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
