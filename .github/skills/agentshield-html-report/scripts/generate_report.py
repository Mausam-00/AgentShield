#!/usr/bin/env python3
"""AgentShield AI HTML report generator.

Renders a standalone HTML report from an existing evidence/assessment JSON
document. This script is invoked only through the ``agentshield-html-report``
skill, which triggers exclusively on an explicit end-user report request.

Safety properties enforced here:

- every dynamic value is HTML-escaped;
- credential-like fields are recursively redacted;
- missing optional evidence renders as ``No evidence available``;
- assurance posture and runtime decision stay in separate sections;
- output is self-contained: embedded CSS only, no JavaScript, remote fonts,
  trackers, iframes, or network calls;
- simulations are labelled and ``PASS is not certification`` is always stated.

The generator never invents evidence. Malformed required fields fail loudly.

Usage:
    python generate_report.py INPUT_JSON OUTPUT_HTML
"""

from __future__ import annotations

import html
import json
import re
import sys
from typing import Any


NO_EVIDENCE = "No evidence available"
REDACTED = "[REDACTED]"

REQUIRED_ROOT_FIELDS = (
    "trace_id",
    "timestamp_utc",
    "mode",
    "simulation",
    "subject",
    "assurance",
    "runtime",
    "findings",
    "coverage_limitations",
    "observations",
    "hypotheses",
    "policy_matches",
    "approval",
    "plan",
    "validation",
    "evidence_summary",
    "limitations",
    "accountability_statement",
)

# Field-name fragments treated as credential-like and redacted recursively.
SECRET_KEY_PATTERN = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|private[_-]?key|"
    r"credential|authorization|auth[_-]?header|cookie|session[_-]?key|"
    r"access[_-]?key|client[_-]?secret|bearer)",
    re.IGNORECASE,
)


class ReportError(Exception):
    """Raised for malformed input or unsafe rendering conditions."""


# --------------------------------------------------------------------------- #
# Validation and redaction
# --------------------------------------------------------------------------- #
def validate(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ReportError("report input must be a JSON object")
    missing = [f for f in REQUIRED_ROOT_FIELDS if f not in data]
    if missing:
        raise ReportError(f"missing required report fields: {', '.join(missing)}")

    assurance = data.get("assurance")
    if not isinstance(assurance, dict) or "posture" not in assurance:
        raise ReportError("assurance object must include a posture")
    if assurance["posture"] not in ("PASS", "WARN", "BLOCK"):
        raise ReportError(f"invalid assurance posture: {assurance['posture']!r}")

    runtime = data.get("runtime")
    if runtime is not None:
        if not isinstance(runtime, dict) or "decision" not in runtime:
            raise ReportError("runtime object must include a decision")
        valid = {"ALLOW", "TRANSFORM", "APPROVE", "ESCALATE", "DENY"}
        if runtime["decision"] not in valid:
            raise ReportError(f"invalid runtime decision: {runtime['decision']!r}")


def redact(value: Any, key_hint: str = "") -> Any:
    """Recursively redact credential-like fields by key name."""

    if isinstance(value, dict):
        return {
            k: (REDACTED if SECRET_KEY_PATTERN.search(str(k)) else redact(v, str(k)))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(item, key_hint) for item in value]
    if key_hint and SECRET_KEY_PATTERN.search(key_hint):
        return REDACTED
    return value


# --------------------------------------------------------------------------- #
# Escaping helpers
# --------------------------------------------------------------------------- #
# Neutralize ("defang") constructs the self-contained guard forbids so benign
# occurrences inside caller-supplied evidence (e.g. a documentation URL) render
# inertly instead of crashing. html.escape() already disarms "<script"/"<iframe"
# by escaping "<"; these patterns cover tokens that survive HTML escaping.
_DEFANG_PATTERNS = (
    (re.compile(r"(https?)://", re.IGNORECASE), r"\1[://]"),
    (re.compile(r"//(fonts\.)", re.IGNORECASE), r"[//]\1"),
    (re.compile(r"(javascript):", re.IGNORECASE), r"\1[:]"),
    (re.compile(r"(onerror|onload|srcset)=", re.IGNORECASE), r"\1[=]"),
)


def _defang(text: str) -> str:
    for pattern, replacement in _DEFANG_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def esc(value: Any) -> str:
    """HTML-escape any value (including quotes). Missing -> No evidence."""

    if value is None or value == "":
        return html.escape(NO_EVIDENCE, quote=True)
    return _defang(html.escape(str(value), quote=True))


def esc_raw(value: Any) -> str:
    """Escape without the No-evidence substitution (for known-present values)."""

    return _defang(html.escape(str(value), quote=True))


# --------------------------------------------------------------------------- #
# Section rendering
# --------------------------------------------------------------------------- #
def _list_or_none(items: Any, empty: str = "None recorded.") -> str:
    if not items:
        return f"<p class='muted'>{esc_raw(empty)}</p>"
    rows = "".join(f"<li>{esc(item)}</li>" for item in items)
    return f"<ul>{rows}</ul>"


def render_assurance(a: dict[str, Any]) -> str:
    score = a.get("score")
    score_text = esc(score) if score is not None else esc(None)
    coverage = a.get("coverage")
    coverage_text = (
        f"{float(coverage):.0%}" if isinstance(coverage, (int, float)) else NO_EVIDENCE
    )
    return f"""
    <section class="card assurance">
      <h2>Assurance posture</h2>
      <p class="badge posture-{esc_raw(a.get('posture'))}">{esc(a.get('posture'))}</p>
      <table>
        <tr><th>Assurance score</th><td>{score_text}</td></tr>
        <tr><th>Evidence coverage</th><td>{esc_raw(coverage_text)}</td></tr>
        <tr><th>Confidence</th><td>{esc(a.get('confidence'))}</td></tr>
        <tr><th>Audit version</th><td>{esc(a.get('audit_version'))}</td></tr>
        <tr><th>Definition hash</th><td>{esc(a.get('definition_hash'))}</td></tr>
        <tr><th>Tool-manifest hash</th><td>{esc(a.get('tool_manifest_hash'))}</td></tr>
      </table>
      <p class="note">Assurance posture is not a runtime authorization.
      <strong>PASS is not certification.</strong></p>
    </section>
    """


def render_runtime(r: Any) -> str:
    if r is None:
        return """
    <section class="card runtime">
      <h2>Runtime decision</h2>
      <p class="muted">No runtime decision in this record (assessment only).</p>
    </section>
    """
    return f"""
    <section class="card runtime">
      <h2>Runtime decision</h2>
      <p class="badge decision-{esc_raw(r.get('decision'))}">{esc(r.get('decision'))}</p>
      <table>
        <tr><th>Policy version</th><td>{esc(r.get('policy_version'))}</td></tr>
        <tr><th>Action</th><td>{esc(r.get('action'))}</td></tr>
        <tr><th>Target</th><td>{esc(r.get('target'))}</td></tr>
        <tr><th>Purpose</th><td>{esc(r.get('purpose'))}</td></tr>
        <tr><th>Environment</th><td>{esc(r.get('environment'))}</td></tr>
        <tr><th>Operational-impact score</th><td>{esc(r.get('operational_impact_score'))}</td></tr>
        <tr><th>Nothing reached target</th><td>{esc(r.get('nothing_reached_target'))}</td></tr>
      </table>
      <p class="note">The runtime decision is owned by deterministic policy and is
      separate from assurance posture.</p>
    </section>
    """


def render_findings(findings: list[Any]) -> str:
    if not findings:
        return "<section class='card'><h2>Findings</h2><p class='muted'>None recorded.</p></section>"
    rows = ""
    for f in findings:
        hypo = f.get("hypothesis")
        hypo_row = (
            f"<tr><td colspan='6' class='hypothesis'>Hypothesis (not evidence): {esc(hypo)}</td></tr>"
            if hypo
            else ""
        )
        prov = f.get("provenance") or "-"
        conf = f.get("confidence")
        prov_cell = esc(prov) if conf is None else f"{esc(prov)} ({esc(conf)})"
        rows += f"""
        <tr>
          <td>{esc(f.get('id'))}</td>
          <td>{esc(f.get('severity'))}</td>
          <td>{esc(f.get('control_family'))}</td>
          <td>{esc(f.get('evidence_state'))}</td>
          <td>{prov_cell}</td>
          <td>{esc(f.get('title'))}</td>
        </tr>
        <tr><td colspan='6' class='detail'>Observation: {esc(f.get('observation'))}<br>
        Remediation: {esc(f.get('remediation'))}</td></tr>
        {hypo_row}
        """
    return f"""
    <section class="card">
      <h2>Assurance findings</h2>
      <table>
        <thead><tr><th>ID</th><th>Severity</th><th>Family</th>
        <th>Evidence state</th><th>Source (confidence)</th><th>Finding</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    """


def render_compliance(compliance: Any) -> str:
    if not isinstance(compliance, dict) or not compliance.get("frameworks"):
        return ""
    blocks = ""
    for fw in compliance.get("frameworks") or []:
        rows = ""
        for c in fw.get("controls") or []:
            fams = ", ".join(c.get("families") or [])
            rows += (
                f"<tr><td>{esc(c.get('control_id'))} {esc(c.get('control_title'))}</td>"
                f"<td>{esc(fams)}</td><td>{esc(c.get('status'))}</td>"
                f"<td>{esc(c.get('note'))}</td></tr>"
            )
        blocks += f"""
        <h3>{esc(fw.get('name'))} (v{esc(fw.get('version'))})</h3>
        <table>
          <thead><tr><th>Mapped control</th><th>Families</th>
          <th>Coverage</th><th>Note</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        """
    return f"""
    <section class="card">
      <h2>Compliance framework mapping</h2>
      <p class="note">{esc(compliance.get('disclaimer'))}</p>
      {blocks}
      <p class="muted">Mapping version: {esc(compliance.get('map_version'))}</p>
    </section>
    """


def render_policy(matches: list[Any]) -> str:
    if not matches:
        return "<section class='card'><h2>Policy controls</h2><p class='muted'>None recorded.</p></section>"
    rows = "".join(
        f"<tr><td>{esc(m.get('control_id'))}</td>"
        f"<td>{esc(m.get('reason_code'))}</td>"
        f"<td>{esc(m.get('decision'))}</td>"
        f"<td>{esc(m.get('explanation'))}</td></tr>"
        for m in matches
    )
    return f"""
    <section class="card">
      <h2>Deterministic policy controls</h2>
      <table>
        <thead><tr><th>Control ID</th><th>Reason code</th>
        <th>Decision</th><th>Explanation</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    """


def render_approval(approval: Any) -> str:
    if approval is None:
        return "<section class='card'><h2>Approval</h2><p class='muted'>Not required for this record.</p></section>"
    return f"""
    <section class="card">
      <h2>Human approval</h2>
      <table>
        <tr><th>Result</th><td>{esc(approval.get('result'))}</td></tr>
        <tr><th>Approver</th><td>{esc(approval.get('approver'))}</td></tr>
        <tr><th>Bound requester</th><td>{esc(approval.get('requester'))}</td></tr>
        <tr><th>Bound action</th><td>{esc(approval.get('action'))}</td></tr>
        <tr><th>Bound target</th><td>{esc(approval.get('target'))}</td></tr>
        <tr><th>Bound plan hash</th><td>{esc(approval.get('plan_hash'))}</td></tr>
        <tr><th>Bound policy version</th><td>{esc(approval.get('policy_version'))}</td></tr>
        <tr><th>Expiry</th><td>{esc(approval.get('expiry'))}</td></tr>
      </table>
      <p class="note">Timeout is not approval. Rejection or invalid binding permits
      zero executed steps.</p>
    </section>
    """


def render_plan(plan: Any) -> str:
    if plan is None:
        return "<section class='card'><h2>Constrained safe plan</h2><p class='muted'>No plan in this record.</p></section>"
    steps = plan.get("steps") or []
    if not steps:
        body = "<p class='muted'>No steps recorded.</p>"
    else:
        rows = "".join(
            f"<tr><td>{esc(s.get('id'))}</td><td>{esc(s.get('action'))}</td>"
            f"<td>{esc(s.get('target_scope'))}</td><td>{esc(s.get('reason'))}</td>"
            f"<td>{esc(s.get('validation'))}</td><td>{esc(s.get('rollback'))}</td>"
            f"<td>{esc(s.get('stop_condition'))}</td></tr>"
            for s in steps
        )
        body = (
            "<table><thead><tr><th>Step</th><th>Action</th><th>Scope</th>"
            "<th>Reason</th><th>Validation</th><th>Rollback</th>"
            f"<th>Stop condition</th></tr></thead><tbody>{rows}</tbody></table>"
        )
    return f"""
    <section class="card">
      <h2>Constrained safe plan</h2>
      <p><strong>Plan hash:</strong> {esc(plan.get('plan_hash'))}</p>
      {body}
    </section>
    """


def render_validation(v: Any) -> str:
    if v is None:
        return "<section class='card'><h2>Outcome validation</h2><p class='muted'>Not performed in this record.</p></section>"
    rows = ""
    for label, exp, obs, match in (
        ("Action", v.get("expected_action"), v.get("observed_action"), v.get("action_match")),
        ("Target", v.get("expected_target"), v.get("observed_target"), v.get("target_match")),
        ("Outcome", v.get("expected_outcome"), v.get("observed_outcome"), v.get("outcome_match")),
    ):
        rows += (
            f"<tr><td>{esc_raw(label)}</td><td>{esc(exp)}</td>"
            f"<td>{esc(obs)}</td><td>{esc(match)}</td></tr>"
        )
    return f"""
    <section class="card">
      <h2>Outcome validation</h2>
      <table>
        <thead><tr><th>Comparison</th><th>Expected</th><th>Observed</th><th>Match</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p><strong>Stopped step:</strong> {esc(v.get('stopped_step'))}</p>
      <h3>Deviations</h3>
      {_list_or_none(v.get('deviations'), 'None detected.')}
    </section>
    """


# --------------------------------------------------------------------------- #
# Document assembly
# --------------------------------------------------------------------------- #
CSS = """
:root{
  --ink:#111827;--muted:#6b7280;--line:#e6ebf1;--card:#ffffff;
  --brand1:#2563eb;--brand2:#7c3aed;--brand3:#0ea5a4;
  --shadow:0 10px 30px rgba(17,24,39,.08);
}
*{box-sizing:border-box;}
body{margin:0;
  font-family:"Segoe UI",-apple-system,BlinkMacSystemFont,Roboto,Helvetica,Arial,
  "Helvetica Neue",sans-serif;
  color:var(--ink);background:radial-gradient(1200px 600px at 10% -10%,#eef2ff,#f6f8fb 60%);
  line-height:1.55;-webkit-font-smoothing:antialiased;}
header{position:relative;overflow:hidden;color:#fff;padding:34px 30px 40px;
  background:linear-gradient(120deg,#1e3a8a 0%,#4f46e5 42%,#7c3aed 72%,#0ea5a4 120%);}
header::after{content:"";position:absolute;right:-80px;top:-80px;width:280px;height:280px;
  background:radial-gradient(circle,rgba(255,255,255,.18),transparent 60%);}
.brand{display:flex;align-items:center;gap:16px;position:relative;z-index:1;}
.brand .logo{width:56px;height:56px;filter:drop-shadow(0 6px 14px rgba(0,0,0,.25));}
.brand h1{margin:0;font-size:26px;font-weight:800;letter-spacing:.3px;}
.brand .tag{margin:2px 0 0;font-size:13px;color:#dbe4ff;letter-spacing:1.6px;
  text-transform:uppercase;font-weight:600;}
.brand .ai{background:rgba(255,255,255,.16);padding:2px 8px;border-radius:8px;
  font-size:12px;font-weight:700;margin-left:6px;vertical-align:middle;}
main{max-width:980px;margin:-18px auto 0;padding:0 20px 20px;position:relative;z-index:2;}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;
  padding:20px 22px;margin:16px 0;box-shadow:var(--shadow);}
.card.assurance{border-top:4px solid var(--brand1);}
.card.runtime{border-top:4px solid var(--brand2);}
h2{font-size:15px;margin:0 0 14px;padding-bottom:8px;letter-spacing:.4px;
  text-transform:uppercase;color:#374151;border-bottom:1px solid var(--line);}
h3{font-size:13px;margin:14px 0 6px;color:#374151;text-transform:uppercase;letter-spacing:.4px;}
table{width:100%;border-collapse:separate;border-spacing:0;font-size:13.5px;}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top;}
tr:last-child th,tr:last-child td{border-bottom:none;}
th{color:var(--muted);font-weight:600;width:30%;}
thead th{color:#4b5563;font-size:11px;text-transform:uppercase;letter-spacing:.5px;
  background:#f8fafc;border-bottom:2px solid var(--line);}
.badge{display:inline-block;padding:7px 18px;border-radius:999px;font-weight:800;
  font-size:15px;color:#fff;letter-spacing:.6px;box-shadow:var(--shadow);}
.posture-PASS{background:linear-gradient(135deg,#16a34a,#15803d);}
.posture-WARN{background:linear-gradient(135deg,#f59e0b,#b45309);}
.posture-BLOCK{background:linear-gradient(135deg,#ef4444,#b91c1c);}
.decision-ALLOW{background:linear-gradient(135deg,#16a34a,#15803d);}
.decision-TRANSFORM{background:linear-gradient(135deg,#3b82f6,#2563eb);}
.decision-APPROVE{background:linear-gradient(135deg,#8b5cf6,#6d28d9);}
.decision-ESCALATE{background:linear-gradient(135deg,#f59e0b,#b45309);}
.decision-DENY{background:linear-gradient(135deg,#ef4444,#b91c1c);}
.muted{color:var(--muted);font-style:italic;}
.note{color:var(--muted);font-size:12px;margin-top:12px;}
.detail{color:#4b5563;font-size:12px;background:#f8fafc;}
.hypothesis{color:#6d28d9;font-size:12px;background:#f5f3ff;}
ul{margin:8px 0 0;padding-left:18px;}
li{margin:3px 0;}
.sim{background:linear-gradient(135deg,#fff7ed,#ffedd5);border:1px solid #fdba74;
  color:#9a3412;padding:12px 16px;border-radius:12px;margin:18px 0;font-weight:700;
  box-shadow:var(--shadow);}
footer{max-width:980px;margin:0 auto;padding:18px 22px 44px;color:var(--muted);font-size:12px;}
"""


# Inline shield logo (no xmlns so the HTML parser renders it and no URL appears).
LOGO_SVG = """
<svg class="logo" viewBox="0 0 64 64" role="img" aria-label="AgentShield AI logo">
  <defs>
    <linearGradient id="asShield" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#60a5fa"/>
      <stop offset="0.5" stop-color="#818cf8"/>
      <stop offset="1" stop-color="#5eead4"/>
    </linearGradient>
  </defs>
  <path d="M32 3 L57 12 V31 C57 45 46 56 32 61 C18 56 7 45 7 31 V12 Z"
        fill="url(#asShield)" stroke="#ffffff" stroke-width="2"/>
  <path d="M21 32 l7 8 l15 -17" fill="none" stroke="#0f172a"
        stroke-width="5" stroke-linecap="round" stroke-linejoin="round"
        opacity="0.85"/>
  <path d="M21 32 l7 8 l15 -17" fill="none" stroke="#ffffff"
        stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def build_html(data: dict[str, Any]) -> str:
    validate(data)
    safe = redact(data)

    subject = safe.get("subject") or {}
    simulation = bool(safe.get("simulation"))
    sim_banner = (
        "<div class='sim'>SIMULATION: this report reflects a simulated evaluation. "
        "No live target system was contacted.</div>"
        if simulation
        else ""
    )

    parts = [
        "<!DOCTYPE html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<title>AgentShield AI Report {esc_raw(safe.get('trace_id'))}</title>",
        f"<style>{CSS}</style></head><body>",
        f"<header><div class='brand'>{LOGO_SVG}"
        "<div><h1>AgentShield<span class='ai'>AI</span></h1>"
        "<p class='tag'>Predict &middot; Govern &middot; Approve &middot; Execute Safely &middot; Audit</p>"
        "</div></div></header>",
        "<main>",
        sim_banner,
        "<section class='card'><h2>Overview</h2><table>",
        f"<tr><th>Trace ID</th><td>{esc(safe.get('trace_id'))}</td></tr>",
        f"<tr><th>Timestamp (UTC)</th><td>{esc(safe.get('timestamp_utc'))}</td></tr>",
        f"<tr><th>Mode</th><td>{esc(safe.get('mode'))}</td></tr>",
        f"<tr><th>Subject</th><td>{esc(subject.get('name') if isinstance(subject, dict) else subject)}</td></tr>",
        f"<tr><th>Owner</th><td>{esc(subject.get('owner') if isinstance(subject, dict) else None)}</td></tr>",
        f"<tr><th>Sponsor</th><td>{esc(subject.get('sponsor') if isinstance(subject, dict) else None)}</td></tr>",
        "</table></section>",
        render_assurance(safe.get("assurance") or {}),
        render_runtime(safe.get("runtime")),
        "<section class='card'><h2>Observations</h2>"
        + _list_or_none(safe.get("observations"))
        + "</section>",
        "<section class='card'><h2>Hypotheses (not evidence)</h2>"
        + _list_or_none(safe.get("hypotheses"), "None recorded.")
        + "</section>",
        render_findings(safe.get("findings") or []),
        render_compliance(safe.get("compliance")),
        "<section class='card'><h2>Coverage limitations</h2>"
        + _list_or_none(safe.get("coverage_limitations"), "None recorded.")
        + "</section>",
        render_policy(safe.get("policy_matches") or []),
        render_approval(safe.get("approval")),
        render_plan(safe.get("plan")),
        render_validation(safe.get("validation")),
        "<section class='card'><h2>Limitations</h2>"
        + _list_or_none(safe.get("limitations"), "None recorded.")
        + "</section>",
        "<section class='card'><h2>Accountability</h2>"
        f"<p>{esc(safe.get('accountability_statement'))}</p>"
        "<p class='note'>AgentShield AI provides assurance and governance support, "
        "not certification, compliance approval, or a guarantee of safety. "
        "<strong>PASS is not certification.</strong></p></section>",
        "</main>",
        "<footer>Generated by AgentShield AI from existing evidence only. "
        "Self-contained report: embedded CSS only, no scripts or network calls.</footer>",
        "</body></html>",
    ]
    document = "\n".join(parts)
    _assert_self_contained(document)
    return document


def _assert_self_contained(document: str) -> None:
    """Fail closed if the rendered document contains unsafe constructs."""

    lowered = document.lower()
    forbidden = ["<script", "javascript:", "onerror=", "onload=", "<iframe",
                 "http://", "https://", "//fonts.", "srcset="]
    hits = [token for token in forbidden if token in lowered]
    if hits:
        raise ReportError(f"unsafe content in report output: {', '.join(hits)}")


def generate(input_path: str, output_path: str) -> str:
    with open(input_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    document = build_html(data)
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(document)
    return output_path


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        sys.stderr.write("usage: python generate_report.py INPUT_JSON OUTPUT_HTML\n")
        return 2
    try:
        generate(argv[1], argv[2])
    except (ReportError, json.JSONDecodeError, OSError) as exc:
        sys.stderr.write(f"report generation failed: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
