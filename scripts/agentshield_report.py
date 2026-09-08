"""Generic AgentShield report generator.

Assess a single agent definition (``.md``) and render a downloadable,
self-contained HTML report driving every dashboard panel from live package
output:

  * ASSESS         -> static assessment findings + assurance posture
  * OBSERVE        -> predicted runtime decision for a representative read
  * Gate R         -> static red-team (declared-defense coverage / residual)
  * Responsible AI -> six-pillar posture (advisory, simulation-only)

Usage::

    python scripts/agentshield_report.py AGENT.md [OUTPUT.html] [--commit-cache]

``OUTPUT.html`` may be omitted or a directory, in which case the file is named
by the ``AgentShield_AI_Report_<AgentName>.html`` convention. A one-line JSON
summary is printed to stdout for programmatic callers (the website API route).
Pass ``--commit-cache`` to auto-commit any newly-written ``enrichment_cache``
entry so the website (container image) and the CLI render identical reports.

Everything is simulation-only: no network call, nothing executed, no credential.
"""

from __future__ import annotations

import json
import os
import subprocess
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
from agentshield.compliance import compliance_to_report  # noqa: E402

NOW = datetime.now(timezone.utc)
CAPS = ["read_definition"]


def _live_enabled() -> bool:
    """Live measurement is opt-in via AGENTSHIELD_LIVE and a configured target.

    Kept off by default so ordinary report generation never sends prompts to a
    real model (no surprise cost, no egress). When enabled but misconfigured, we
    fall back to static rather than fail the report.
    """

    flag = (os.environ.get("AGENTSHIELD_LIVE") or "").strip().lower()
    if flag not in ("1", "true", "yes", "on"):
        return False
    try:
        from agentshield_live import describe_target_config

        return bool(describe_target_config().get("configured"))
    except Exception:  # noqa: BLE001 - never let live wiring break the report
        return False


def _gather_live(subject: str, definition_text: str) -> "dict | None":
    """Run the live lane ONCE, returning all measured blocks (or None).

    Building the adapter and executing probes is done a single time here so the
    red-team and Responsible-AI blocks share the same measurement instead of
    hitting the model three times. Any failure returns ``None`` so callers fall
    back to the static lane.
    """

    if not _live_enabled():
        return None
    try:
        from agentshield_live import build_target_adapter
        from agentshield_live.content_safety_live import (
            content_safety_to_report,
            run_content_safety_probe,
        )
        from agentshield_live.pyrit_engine import (
            PyRITUnavailable,
            pyrit_available,
            run_pyrit_redteam,
        )
        from agentshield_live.redteam_live import run_live_redteam

        adapter = build_target_adapter(allow_mock=False)

        if pyrit_available():
            try:
                rt = run_pyrit_redteam(definition_text, adapter, subject=subject)
            except PyRITUnavailable:
                rt = run_live_redteam(definition_text, adapter, subject=subject)
        else:
            rt = run_live_redteam(definition_text, adapter, subject=subject)

        bundle: dict = {
            "redteam": redteam_to_report_section(rt),
            "content_safety": content_safety_to_report(
                run_content_safety_probe(adapter, subject=subject)
            ),
            "fairness": None,
        }

        dataset_path = (os.environ.get("AGENTSHIELD_FAIRNESS_DATASET") or "").strip()
        if dataset_path:
            from agentshield_live.fairness import (
                fairness_to_report,
                load_fairness_dataset,
                run_fairness_probe,
            )

            cases = load_fairness_dataset(dataset_path)
            fr = run_fairness_probe(
                adapter, cases, subject=subject, system_prompt=definition_text
            )
            bundle["fairness"] = fairness_to_report(fr)
        return bundle
    except Exception as exc:  # noqa: BLE001 - honest fallback to static
        print(
            f"agentshield: live lane unavailable, using static ({exc})",
            file=sys.stderr,
        )
        return None


def _redteam_block(subject: str, definition_text: str, live: "dict | None") -> dict:
    """Red-team block: measured live lane when available, else static inference."""

    if live and live.get("redteam"):
        return live["redteam"]
    return redteam_to_report_section(
        run_static_redteam(definition_text, subject=subject)
    )


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


def _responsible_ai_block(
    subject: str, definition_text: str, live: "dict | None" = None
) -> dict:
    """Derive an honest, evidence-based Responsible AI block.

    Without live measurement, every pillar is unevidenced and the block fails
    closed (RAI-BLOCK) - honest, since fairness/safety cannot be read from a
    definition. With the live lane, measured harm rate, canary leakage, and
    (if a dataset is supplied) fairness disparity are converted into tested
    pillar maturities so the score reflects observed behaviour.
    """

    measured = False
    if live:
        try:
            from agentshield_live.rai_measured import (
                any_measured,
                build_measured_pillars,
            )

            pillars = build_measured_pillars(
                content_safety=live.get("content_safety"),
                redteam=live.get("redteam"),
                fairness=live.get("fairness"),
            )
            measured = any_measured(pillars)
        except Exception as exc:  # noqa: BLE001 - fall back to static pillars
            print(f"agentshield: measured RAI unavailable ({exc})", file=sys.stderr)
            pillars = default_pillars(tested=False)
    else:
        pillars = default_pillars(tested=False)

    result = evaluate_responsible_ai(
        subject=subject,
        pillars=pillars,
        definition_text=definition_text,
    )
    raw = rai_to_report(result, simulation=True)
    a = raw["assurance"]
    block = {
        "posture": a["posture"],
        "score": a["score"],
        "coverage": a["coverage"],
        "confidence": a["confidence"],
        "rai_version": a["audit_version"],
        "pillars": raw["gates"],
        "findings": raw["findings"],
        "coverage_limitations": raw["coverage_limitations"],
        "evidence_mode": "measured" if measured else "declared",
    }

    # Attach the raw measured sub-blocks for transparency in the report.
    if live:
        if live.get("content_safety"):
            block["content_safety"] = live["content_safety"]
        if live.get("fairness"):
            block["fairness"] = live["fairness"]
    return block


def _provenance_summary(assessment) -> list[dict]:
    """Serialize deterministic per-finding provenance + confidence weighting.

    Derived only from the static assessment (never the model narrative), so the
    evidence-provenance view is stable and honest regardless of enrichment.
    """

    rows = []
    for f in assessment.findings:
        rows.append(
            {
                "id": f.id,
                "title": f.title,
                "control_family": f.control_family,
                "severity": f.severity.value,
                "effective_severity": f.effective_severity().value,
                "provenance": f.provenance.value,
                "confidence": round(f.weight(), 2),
            }
        )
    return rows


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

    # Run the live lane once (if enabled); both blocks share the measurement.
    live = _gather_live(assessment.subject, assessment.definition_text)

    redteam = _redteam_block(assessment.subject, assessment.definition_text, live)

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
        assessment.subject, assessment.definition_text, live
    )
    report["compliance"] = compliance_to_report(assessment.assurance)
    # Deterministic evidence-provenance summary, taken from the static findings
    # BEFORE any LLM enrichment can rewrite the findings list. This guarantees
    # the provenance / confidence weighting (#1) is always visible in the report
    # even when the narrative findings are model-authored.
    report["provenance_summary"] = _provenance_summary(assessment)
    report["subject"]["name"] = assessment.subject

    # Optional: let the AgentShield agent (Azure OpenAI) author the analysis,
    # overlaying its findings onto this validated deterministic skeleton. Any
    # failure falls back to the deterministic report so the site never breaks.
    enrichment = {"status": "deterministic"}
    if agent_llm.llm_available():
        try:
            report = agent_llm.build_llm_report(assessment.definition_text, report)
            enrichment = dict(agent_llm.LAST_ENRICHMENT) or {"status": "unknown"}
        except Exception as exc:  # noqa: BLE001 - deterministic fallback
            print(f"agentshield: LLM enrichment skipped ({exc})", file=sys.stderr)
            enrichment = {"status": "error", "detail": type(exc).__name__}

    report["_meta_enrichment"] = enrichment
    return report


def _snapshot_cache() -> set[Path]:
    """Return the set of enrichment-cache files that exist right now."""

    cache_dir = getattr(agent_llm, "ENRICH_CACHE_DIR", None)
    if not cache_dir or not Path(cache_dir).is_dir():
        return set()
    return set(Path(cache_dir).rglob("*.json"))


def _commit_new_cache(new_files: set[Path], subject: str) -> None:
    """Stage and commit only the newly-written cache entries.

    This makes web/CLI report parity automatic: the content-addressed LLM
    narrative that the CLI just produced is committed so it ships in the
    container image and the website hits the same cache entry. Only the specific
    new ``enrichment_cache/*.json`` files are staged - never the whole tree - and
    the commit is never pushed. Failures (no git, detached tree, read-only fs)
    are reported but never abort report generation.
    """

    if not new_files:
        print("cache: no new enrichment entries to commit.", file=sys.stderr)
        return

    paths = [str(p) for p in sorted(new_files)]
    try:
        subprocess.run(
            ["git", "-C", str(ROOT), "add", "--", *paths],
            check=True, capture_output=True, text=True,
        )
        message = f"cache: enrichment for {subject}"
        subprocess.run(
            ["git", "-C", str(ROOT), "commit", "-m", message, "--", *paths],
            check=True, capture_output=True, text=True,
        )
    except FileNotFoundError:
        print("cache: git not available; skipped auto-commit.", file=sys.stderr)
        return
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        print(f"cache: auto-commit skipped ({detail})", file=sys.stderr)
        return
    print(
        f"cache: committed {len(paths)} new enrichment entr"
        f"{'y' if len(paths) == 1 else 'ies'}; run 'git push' to redeploy the "
        "website with matching reports.",
        file=sys.stderr,
    )


def generate(
    agent_path: str, output: str | None, *, commit_cache: bool = False
) -> tuple[str, dict]:
    """Compose and render. Returns (html_path, summary)."""

    before = _snapshot_cache() if commit_cache else set()
    report = build_report(agent_path)

    # Pop private telemetry before rendering so the report JSON stays clean.
    enrichment = report.pop("_meta_enrichment", {"status": "unknown"})

    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as handle:
        json.dump(report, handle)
        json_path = handle.name
    try:
        html_path = dashboard_report.generate(json_path, output)
    finally:
        Path(json_path).unlink(missing_ok=True)

    if commit_cache:
        new_files = _snapshot_cache() - before
        _commit_new_cache(new_files, report["subject"]["name"])

    summary = {
        "subject": report["subject"]["name"],
        "assurance_posture": report["assurance"]["posture"],
        "assurance_score": report["assurance"]["score"],
        "runtime_decision": report["runtime"]["decision"],
        "redteam_posture": report["redteam"]["posture_signal"],
        "defense_coverage": report["redteam"].get("defense_coverage"),
        "residual_exposure": report["redteam"].get("residual_exposure"),
        "rai_posture": report["responsible_ai"]["posture"],
        "enrichment": enrichment,
        "html_path": html_path,
    }
    return html_path, summary


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--commit-cache"]
    commit_cache = "--commit-cache" in argv
    if len(args) < 1:
        print(
            "usage: agentshield_report.py AGENT.md [OUTPUT.html] [--commit-cache]",
            file=sys.stderr,
        )
        return 2
    agent_path = args[0]
    output = args[1] if len(args) > 1 else None
    _, summary = generate(agent_path, output, commit_cache=commit_cache)
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
