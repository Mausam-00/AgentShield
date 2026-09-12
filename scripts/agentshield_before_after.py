"""AgentShield "Before -> After Remediation" showcase driver.

Runs one deliberately-weak demo agent (InfraBot) and its hardened counterpart
through the *same* AgentShield engine and emits a side-by-side comparison across
four axes:

  1. Assurance posture + score + findings (static ASSESS)
  2. Static red-team: attack-success-rate, refusal, injection-resistance (Gate R)
  3. Runtime decision on a representative action (deterministic policy)
  4. Auto-remediation: the engine-generated fix diff for the weak agent

Outputs (regenerated fresh on every run - safe to demo repeatedly):
  docs/showcase/before_after.json   -> data the website page consumes
  docs/showcase/before_after.html   -> self-contained judge-facing comparison
  docs/showcase/infra-bot.remediated.agent.md / .diff -> engine auto-fix

Everything is simulation-only: no network call, no credential, and the two
source agent definitions are read-only inputs that are never modified.
"""

from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agentshield import (  # noqa: E402
    ActionRequest,
    EntraIdentityProvider,
    ImpactDimension,
    asr_reduction,
    compute_impact,
    evaluate_policy,
    remediate,
    run_static_redteam,
)
from agentshield.static_assess import assess_agent_file  # noqa: E402

SHOWCASE = ROOT / "examples" / "showcase"
BEFORE_AGENT = SHOWCASE / "infra-bot.before.agent.md"
AFTER_AGENT = SHOWCASE / "infra-bot.after.agent.md"
OUT = ROOT / "docs" / "showcase"
NOW = datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _impact(criticality, reversibility, scope, *, destructive=False, irreversible=False):
    return compute_impact(
        dimensions=[
            ImpactDimension("criticality", criticality, "synthetic"),
            ImpactDimension("reversibility", reversibility, "synthetic"),
            ImpactDimension("scope", scope, "synthetic"),
        ],
        destructive=destructive,
        irreversible=irreversible,
    )


def _identity(oid: str, roles: list[str], age: int):
    prov = EntraIdentityProvider()
    prov.add(oid, {
        "oid": oid, "idtyp": "app", "roles": roles, "account_state": "enabled",
        "owner": "infra-ops", "sponsor": "infra-lead", "assurance_age_days": age,
    })
    return prov.resolve(oid)


def _decision(request, identity, impact) -> str:
    return evaluate_policy(request, identity, None, impact).decision.value


def _runtime_before() -> dict:
    """The weak agent tries to auto-remove a production disk -> held, not run."""
    ident = _identity("sp://infra-bot", ["add_disk", "remove_disk",
                                         "provision_server", "decommission_server"], 20)
    req = ActionRequest(
        trace_id="SHOWCASE-B", requester_id="sp://infra-bot",
        requester_type="service-principal", action="remove_disk",
        target="vm/prod-db-01", purpose="auto-remediation of a health alert",
        environment="production", request_timestamp_utc=_iso(NOW),
        declared_capabilities=["remove_disk"], read_only=False)
    return {
        "action": "remove_disk", "target": "vm/prod-db-01", "environment": "production",
        "read_only": False,
        "decision": _decision(req, ident, _impact(3, 0, 2, destructive=True, irreversible=True)),
    }


def _runtime_after() -> dict:
    """The hardened agent runs a read-only diagnostic -> flows through."""
    ident = _identity("sp://infra-bot-ro", ["read_metrics", "read_config"], 10)
    req = ActionRequest(
        trace_id="SHOWCASE-A", requester_id="sp://infra-bot-ro",
        requester_type="service-principal", action="read_metrics",
        target="metrics/prod-db-01", purpose="evidence-based diagnostic",
        environment="production", request_timestamp_utc=_iso(NOW),
        declared_capabilities=["read_metrics"], read_only=True)
    return {
        "action": "read_metrics", "target": "metrics/prod-db-01", "environment": "production",
        "read_only": True,
        "decision": _decision(req, ident, _impact(1, 3, 1)),
    }


def _side(path: Path, runtime: dict) -> dict:
    assessment = assess_agent_file(str(path))
    a = assessment.assurance
    rt = run_static_redteam(assessment.definition_text, subject=assessment.subject)
    return {
        "source": path.name,
        "subject": assessment.subject,
        "assurance": {
            "posture": a.posture.value,
            "score": a.score,
            "coverage": a.coverage,
            "confidence": a.confidence.value,
        },
        "findings": [
            {"id": f.id, "severity": f.severity.value, "title": f.title,
             "observation": f.observation, "remediation": f.remediation}
            for f in assessment.findings
        ],
        "redteam": {
            "overall_asr": round(rt.overall_asr, 3),
            "refusal_rate": round(rt.refusal_rate, 3),
            "injection_resistance": round(rt.injection_resistance, 3),
            "posture_signal": rt.posture_signal,
        },
        "runtime": runtime,
        "_asr": rt.overall_asr,
    }


def build_data() -> dict:
    before = _side(BEFORE_AGENT, _runtime_before())
    after = _side(AFTER_AGENT, _runtime_after())

    # Engine auto-remediation of the weak agent (proves it acts, not just reports).
    weak = assess_agent_file(str(BEFORE_AGENT))
    rem = remediate(weak)

    red = asr_reduction(before["_asr"], after["_asr"])
    before.pop("_asr", None)
    after.pop("_asr", None)

    return {
        "generated_utc": _iso(NOW),
        "title": "AgentShield AI - Before / After Remediation",
        "demo_agent": "InfraBot (synthetic cloud-infrastructure agent)",
        "before": before,
        "after": after,
        "deltas": {
            "score_gain": (after["assurance"]["score"] or 0) - (before["assurance"]["score"] or 0),
            "findings_removed": len(before["findings"]) - len(after["findings"]),
            "asr_relative_reduction_pct": int(round(red.relative_reduction * 100)),
            "injection_resistance_gain_pct": int(round(
                (after["redteam"]["injection_resistance"]
                 - before["redteam"]["injection_resistance"]) * 100)),
        },
        "auto_remediation": {
            "applied": rem.applied,
            "skipped": rem.skipped,
            "diff_lines": len(rem.diff.splitlines()),
            "diff": rem.diff,
        },
        "disclaimer": (
            "Simulation-only. Static assessment never certifies: the hardened "
            "agent tops out at WARN because design evidence alone is never proof. "
            "Missing evidence lowers confidence; it is never invented."
        ),
    }


# --------------------------------------------------------------------------- #
# Self-contained comparison HTML (no external assets, no network).
# --------------------------------------------------------------------------- #

_POSTURE_COLOR = {"PASS": "#16a34a", "WARN": "#d97706", "BLOCK": "#dc2626"}
_DECISION_COLOR = {"ALLOW": "#16a34a", "TRANSFORM": "#0891b2", "APPROVE": "#7c3aed",
                   "ESCALATE": "#d97706", "DENY": "#dc2626"}
_SEV_COLOR = {"CRITICAL": "#dc2626", "HIGH": "#ea580c", "MEDIUM": "#d97706",
              "LOW": "#64748b", "INFO": "#64748b"}


def _esc(s) -> str:
    return html.escape(str(s))


def _findings_rows(findings: list[dict]) -> str:
    if not findings:
        return ('<tr><td colspan="3" class="clean">No open findings &mdash; '
                'all remediated.</td></tr>')
    out = []
    for f in findings:
        c = _SEV_COLOR.get(f["severity"], "#64748b")
        out.append(
            f'<tr><td><span class="pill" style="background:{c}">{_esc(f["severity"])}'
            f'</span></td><td class="mono">{_esc(f["id"])}</td>'
            f'<td>{_esc(f["title"])}</td></tr>')
    return "".join(out)


def _card(side: dict, label: str) -> str:
    a = side["assurance"]
    rt = side["redteam"]
    r = side["runtime"]
    pc = _POSTURE_COLOR.get(a["posture"], "#64748b")
    dc = _DECISION_COLOR.get(r["decision"], "#64748b")
    return f"""
    <div class="card">
      <div class="card-h">{_esc(label)}</div>
      <div class="posture" style="border-color:{pc}">
        <div class="posture-badge" style="background:{pc}">{_esc(a["posture"])}</div>
        <div class="posture-meta">
          <div><span class="k">Assurance score</span><span class="v">{_esc(a["score"])}/100</span></div>
          <div><span class="k">Open findings</span><span class="v">{len(side["findings"])}</span></div>
        </div>
      </div>
      <table class="findings">
        <thead><tr><th>Sev</th><th>ID</th><th>Finding</th></tr></thead>
        <tbody>{_findings_rows(side["findings"])}</tbody>
      </table>
      <div class="metrics">
        <div class="metric"><span class="mk">Attack success rate</span>
          <span class="mv">{int(round(rt["overall_asr"]*100))}%</span></div>
        <div class="metric"><span class="mk">Injection resistance</span>
          <span class="mv">{int(round(rt["injection_resistance"]*100))}%</span></div>
        <div class="metric"><span class="mk">Refusal rate</span>
          <span class="mv">{int(round(rt["refusal_rate"]*100))}%</span></div>
      </div>
      <div class="runtime">
        <div class="rt-label">Runtime decision &mdash; <span class="mono">{_esc(r["action"])}</span>
          on <span class="mono">{_esc(r["target"])}</span> ({_esc(r["environment"])})</div>
        <div class="decision" style="background:{dc}">{_esc(r["decision"])}</div>
      </div>
    </div>"""


def render_html(data: dict) -> str:
    d = data["deltas"]
    b = _card(data["before"], "BEFORE  \u2014  as authored")
    a = _card(data["after"], "AFTER  \u2014  remediated")
    applied = "".join(f"<li>{_esc(x)}</li>" for x in data["auto_remediation"]["applied"]) \
        or "<li>(nothing auto-applied)</li>"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(data["title"])}</title>
<style>
  :root {{ --bg:#0b1020; --panel:#121a33; --ink:#e8ecf6; --muted:#9aa6c4; --line:#25304f; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif; }}
  .wrap {{ max-width:1100px; margin:0 auto; padding:40px 24px 64px; }}
  h1 {{ font-size:26px; margin:0 0 4px; letter-spacing:.3px; }}
  .sub {{ color:var(--muted); margin:0 0 6px; }}
  .agent {{ color:#7dd3fc; font-size:13px; margin:0 0 28px; }}
  .deltas {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:0 0 30px; }}
  .delta {{ background:var(--panel); border:1px solid var(--line); border-radius:12px;
    padding:16px; text-align:center; }}
  .delta .big {{ font-size:30px; font-weight:700; color:#4ade80; }}
  .delta .lbl {{ font-size:12px; color:var(--muted); margin-top:4px; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; align-items:start; }}
  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:14px;
    padding:18px 18px 20px; }}
  .card-h {{ font-weight:700; font-size:14px; letter-spacing:1px; color:var(--muted);
    text-transform:uppercase; margin-bottom:14px; }}
  .posture {{ display:flex; align-items:center; gap:16px; border:1px solid; border-radius:12px;
    padding:14px; margin-bottom:14px; background:rgba(255,255,255,.02); }}
  .posture-badge {{ color:#fff; font-weight:800; font-size:18px; padding:8px 16px;
    border-radius:8px; letter-spacing:1px; }}
  .posture-meta {{ display:flex; gap:26px; }}
  .posture-meta .k {{ display:block; font-size:11px; color:var(--muted); }}
  .posture-meta .v {{ display:block; font-size:20px; font-weight:700; }}
  table.findings {{ width:100%; border-collapse:collapse; margin-bottom:14px; font-size:13px; }}
  table.findings th {{ text-align:left; color:var(--muted); font-weight:600; font-size:11px;
    padding:6px 8px; border-bottom:1px solid var(--line); }}
  table.findings td {{ padding:7px 8px; border-bottom:1px solid var(--line); }}
  td.clean {{ color:#4ade80; text-align:center; padding:16px; }}
  .pill {{ color:#fff; font-size:11px; font-weight:700; padding:2px 8px; border-radius:20px; }}
  .mono {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
  .metrics {{ display:flex; gap:10px; margin-bottom:14px; }}
  .metric {{ flex:1; background:rgba(255,255,255,.03); border:1px solid var(--line);
    border-radius:10px; padding:10px; text-align:center; }}
  .metric .mk {{ display:block; font-size:10px; color:var(--muted); margin-bottom:4px; }}
  .metric .mv {{ display:block; font-size:20px; font-weight:700; }}
  .runtime {{ border-top:1px dashed var(--line); padding-top:12px; }}
  .rt-label {{ font-size:12px; color:var(--muted); margin-bottom:8px; }}
  .decision {{ display:inline-block; color:#fff; font-weight:800; letter-spacing:1px;
    padding:8px 18px; border-radius:8px; }}
  .rem {{ background:var(--panel); border:1px solid var(--line); border-radius:14px;
    padding:18px; margin-top:24px; }}
  .rem h2 {{ font-size:15px; margin:0 0 10px; }}
  .rem ul {{ margin:0 0 10px 18px; color:#c9d4f0; }}
  pre {{ background:#0a0f1f; border:1px solid var(--line); border-radius:10px; padding:14px;
    overflow:auto; font-size:12px; line-height:1.5; }}
  pre .add {{ color:#4ade80; }} pre .del {{ color:#f87171; }} pre .hdr {{ color:#7dd3fc; }}
  .disc {{ color:var(--muted); font-size:12px; margin-top:22px; line-height:1.6; }}
  @media (max-width:760px) {{ .grid,.deltas {{ grid-template-columns:1fr 1fr; }} }}
</style></head>
<body><div class="wrap">
  <h1>{_esc(data["title"])}</h1>
  <p class="sub">Same engine. Same evidence rules. One agent, hardened &mdash; and the improvement is provable.</p>
  <p class="agent">Demo subject: {_esc(data["demo_agent"])} &middot; generated {_esc(data["generated_utc"])}</p>

  <div class="deltas">
    <div class="delta"><div class="big">+{_esc(d["score_gain"])}</div><div class="lbl">assurance score</div></div>
    <div class="delta"><div class="big">-{_esc(d["findings_removed"])}</div><div class="lbl">findings resolved</div></div>
    <div class="delta"><div class="big">-{_esc(d["asr_relative_reduction_pct"])}%</div><div class="lbl">attack success rate</div></div>
    <div class="delta"><div class="big">+{_esc(d["injection_resistance_gain_pct"])}%</div><div class="lbl">injection resistance</div></div>
  </div>

  <div class="grid">{b}{a}</div>

  <div class="rem">
    <h2>&#9881; AgentShield auto-remediation &mdash; the engine generates the fix ({_esc(data["auto_remediation"]["diff_lines"])} diff lines)</h2>
    <ul>{applied}</ul>
    <pre>{_diff_html(data["auto_remediation"]["diff"])}</pre>
  </div>

  <p class="disc">{_esc(data["disclaimer"])}</p>
</div></body></html>"""


def _diff_html(diff: str) -> str:
    out = []
    for line in diff.splitlines():
        cls = ""
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            cls = "hdr"
        elif line.startswith("+"):
            cls = "add"
        elif line.startswith("-"):
            cls = "del"
        out.append(f'<span class="{cls}">{_esc(line)}</span>' if cls else _esc(line))
    return "\n".join(out) if out else "(no diff)"


def main() -> int:
    for p in (BEFORE_AGENT, AFTER_AGENT):
        if not p.exists():
            print(f"error: missing demo agent {p}", file=sys.stderr)
            return 2

    emit_stdout = "--stdout" in sys.argv[1:]

    data = build_data()

    # File artifacts are best-effort: in a hardened/read-only deployment (e.g. the
    # container image, where the app tree is read-only to the runtime user) these
    # writes can fail. That must never break the machine-readable --stdout contract
    # the website API depends on, so failures are swallowed in stdout mode.
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "before_after.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        (OUT / "before_after.html").write_text(render_html(data), encoding="utf-8")

        # The engine's auto-remediated definition + diff, regenerated each run.
        weak = assess_agent_file(str(BEFORE_AGENT))
        rem = remediate(weak)
        (OUT / "infra-bot.remediated.agent.md").write_text(rem.patched_text, encoding="utf-8")
        (OUT / "infra-bot.remediated.diff").write_text(rem.diff, encoding="utf-8")
    except OSError as exc:
        if not emit_stdout:
            print(f"error: could not write showcase artifacts to {OUT}: {exc}", file=sys.stderr)
            return 1
        rem = None

    if emit_stdout:
        # Machine-readable single line consumed by the website API route.
        print(json.dumps(data))
        return 0
    assert rem is not None

    b, a, d = data["before"], data["after"], data["deltas"]
    print("AgentShield  Before -> After Remediation  (InfraBot)")
    print("-" * 60)
    print(f"  Assurance : {b['assurance']['posture']} {b['assurance']['score']}/100 "
          f"({len(b['findings'])} findings)  ->  "
          f"{a['assurance']['posture']} {a['assurance']['score']}/100 "
          f"({len(a['findings'])} findings)   [+{d['score_gain']} pts, "
          f"-{d['findings_removed']} findings]")
    print(f"  Red-team  : ASR {int(b['redteam']['overall_asr']*100)}% -> "
          f"{int(a['redteam']['overall_asr']*100)}%   "
          f"inj-resist {int(b['redteam']['injection_resistance']*100)}% -> "
          f"{int(a['redteam']['injection_resistance']*100)}%   "
          f"[-{d['asr_relative_reduction_pct']}% ASR]")
    print(f"  Runtime   : {b['runtime']['action']} -> {b['runtime']['decision']}   ||   "
          f"{a['runtime']['action']} -> {a['runtime']['decision']}")
    print(f"  Auto-fix  : {', '.join(rem.applied) or '(none)'}")
    print("-" * 60)
    print(f"  JSON : {OUT / 'before_after.json'}")
    print(f"  HTML : {OUT / 'before_after.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
