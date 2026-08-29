"""Generic AgentShield report generator.

Assess a single agent definition (``.md``) and render a downloadable,
self-contained HTML report driving every dashboard panel from live package
output:

  * ASSESS         -> static assessment findings + assurance posture
  * OBSERVE        -> predicted runtime decision for a representative read
  * Gate R         -> static red-team (declared-defense coverage / residual)
  * Responsible AI -> six-pillar posture (advisory, simulation-only)

Usage::

    python scripts/agentshield_report.py AGENT.md [OUTPUT.html]

``OUTPUT.html`` may be omitted or a directory, in which case the file is named
by the ``AgentShield_AI_Report_<AgentName>.html`` convention. A one-line JSON
summary is printed to stdout for programmatic callers (the website API route).

Everything is simulation-only: no network call, nothing executed, no credential.
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
SKILL_SCRIPTS = ROOT / ".github" / "skills" / "agentshield-html-report" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

import dashboard_report  # noqa: E402
import agent_llm  # noqa: E402

from agentshield import (  # noqa: E402
    ActionRequest,
    AgentShieldWorkflow,
    ImpactDimension,
    Lifecycle,
    IdentityContext,
    compute_impact,
    evaluate_responsible_ai,
    rai_to_report,
    redteam_to_report_section,
    run_static_redteam,
    workflow_to_report,
)
from agentshield.responsible_ai import default_pillars  # noqa: E402
from agentshield.static_assess import assess_agent_file  # noqa: E402

NOW = datetime.now(timezone.utc)
CAPS = ["read_definition"]


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _identity() -> IdentityContext:
    """A minimal, known, read-only offline identity for the OBSERVE gate."""

    return IdentityContext(
        requester_id="agent://uploaded-subject",
        known=True,
        requester_type="custom-agent",
        lifecycle=Lifecycle.ACTIVE,
        owner="report-requester",
        sponsor=None,
        platform="offline",
        permitted_capabilities=CAPS,
        assurance_age_days=None,
    )


def _impact():
    return compute_impact(
        dimensions=[
            ImpactDimension("criticality", 1, "read-only definition inspection"),
            ImpactDimension("reversibility", 3, "no state change"),
            ImpactDimension("scope", 1, "single definition"),
        ],
        destructive=False,
        irreversible=False,
    )


def _responsible_ai_block(subject: str, definition_text: str) -> dict:
    """Derive an honest, evidence-based Responsible AI block.

    No external RAI evidence (model cards, fairness metrics) is supplied with a
    bare agent definition, so untested default pillars fail closed and missing
    pillars lower coverage -- exactly as the protocol requires.
    """

    result = evaluate_responsible_ai(
        subject=subject,
        pillars=default_pillars(tested=False),
        definition_text=definition_text,
    )
    raw = rai_to_report(result, simulation=True)
    a = raw["assurance"]
    return {
        "posture": a["posture"],
        "score": a["score"],
        "coverage": a["coverage"],
        "confidence": a["confidence"],
        "rai_version": a["audit_version"],
        "pillars": raw["gates"],
        "findings": raw["findings"],
        "coverage_limitations": raw["coverage_limitations"],
    }


def build_report(agent_path: str) -> dict:
    assessment = assess_agent_file(agent_path)

    # OBSERVE a representative read-only inspection -> predicted runtime decision.
    request = ActionRequest(
        trace_id="REPORT-OBSERVE",
        requester_id="agent://uploaded-subject",
        requester_type="custom-agent",
        action="read_definition",
        target=f"definition/{assessment.subject}",
        purpose="assurance report generation",
        environment="non-production",
        request_timestamp_utc=_iso(NOW),
        declared_capabilities=CAPS,
        read_only=True,
    )
    workflow = AgentShieldWorkflow()
    result = workflow.observe(request, _identity(), assessment.assurance, _impact())

    redteam = redteam_to_report_section(
        run_static_redteam(assessment.definition_text, subject=assessment.subject)
    )

    report = workflow_to_report(
        result,
        simulation=True,
        redteam=redteam,
        observations=[
            f"Static assessment read {len(assessment.findings)} finding(s) from the "
            "uploaded definition.",
            "OBSERVE predicted the runtime decision for a read-only inspection; "
            "nothing was executed against a target.",
        ],
    )

    report["responsible_ai"] = _responsible_ai_block(
        assessment.subject, assessment.definition_text
    )
    report["subject"]["name"] = assessment.subject

    # Optional: let the AgentShield agent (Azure OpenAI) author the analysis,
    # overlaying its findings onto this validated deterministic skeleton. Any
    # failure falls back to the deterministic report so the site never breaks.
    if agent_llm.llm_available():
        try:
            report = agent_llm.build_llm_report(assessment.definition_text, report)
        except Exception as exc:  # noqa: BLE001 - deterministic fallback
            print(f"agentshield: LLM enrichment skipped ({exc})", file=sys.stderr)

    return report


def generate(agent_path: str, output: str | None) -> tuple[str, dict]:
    """Compose and render. Returns (html_path, summary)."""

    report = build_report(agent_path)

    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as handle:
        json.dump(report, handle)
        json_path = handle.name
    try:
        html_path = dashboard_report.generate(json_path, output)
    finally:
        Path(json_path).unlink(missing_ok=True)

    summary = {
        "subject": report["subject"]["name"],
        "assurance_posture": report["assurance"]["posture"],
        "assurance_score": report["assurance"]["score"],
        "runtime_decision": report["runtime"]["decision"],
        "redteam_posture": report["redteam"]["posture_signal"],
        "defense_coverage": report["redteam"].get("defense_coverage"),
        "residual_exposure": report["redteam"].get("residual_exposure"),
        "rai_posture": report["responsible_ai"]["posture"],
        "html_path": html_path,
    }
    return html_path, summary


def main(argv: list[str]) -> int:
    if len(argv) < 1:
        print("usage: agentshield_report.py AGENT.md [OUTPUT.html]", file=sys.stderr)
        return 2
    agent_path = argv[0]
    output = argv[1] if len(argv) > 1 else None
    _, summary = generate(agent_path, output)
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
