"""AgentShield AI - dark dashboard HTML report generator.

Reusable, data-driven renderer that turns a standard AgentShield report JSON
(same schema as generate_report.py) into a dark, dashboard-style HTML page with
a sticky section navigation, clickable KPI cards, and an optional adversarial
red-team panel surfaced in the overview.

Output is fully self-contained: embedded CSS and inline SVG only. No JavaScript,
remote fonts, trackers, iframes, or network calls. In-page navigation uses plain
anchor fragment links with CSS smooth scrolling. Assurance posture and runtime
decision are always rendered as separate fields.

Usage:
    python dashboard_report.py <input.json> [output.html | output_dir]

When the output argument is omitted or names an existing directory, the file is
named by the convention AgentShield_AI_Report_<AgentName>.html, derived from the
report subject (see report_filename).
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
from typing import Any

NO_EVIDENCE = "No evidence available"
REDACTED = "[REDACTED]"

REQUIRED_ROOT_FIELDS = (
    "trace_id", "timestamp_utc", "mode", "simulation", "subject",
    "assurance", "runtime", "findings", "coverage_limitations",
    "observations", "hypotheses", "policy_matches", "approval",
    "plan", "validation", "evidence_summary", "limitations",
    "accountability_statement",
)

SECRET_KEY_PATTERN = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|private[_-]?key|"
    r"credential|authorization|auth[_-]?header|cookie|session[_-]?key|"
    r"access[_-]?key|client[_-]?secret|bearer)",
    re.IGNORECASE,
)

POSTURE_PILL = {
    "PASS": "p-pass", "WARN": "p-warn", "BLOCK": "p-block",
    "RAI-PASS": "p-pass", "RAI-WARN": "p-warn", "RAI-BLOCK": "p-block",
}
POSTURE_COLOR = {
    "PASS": "var(--pass)", "WARN": "var(--warn)", "BLOCK": "var(--block)",
    "RAI-PASS": "var(--pass)", "RAI-WARN": "var(--warn)", "RAI-BLOCK": "var(--block)",
}
GATE_CLASS = {"good": "g-good", "fair": "g-fair", "weak": "g-weak", "gap": "g-gap"}


class ReportError(Exception):
    """Raised for malformed input or unsafe rendering conditions."""


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
        if runtime["decision"] not in {"ALLOW", "TRANSFORM", "APPROVE", "ESCALATE", "DENY"}:
            raise ReportError(f"invalid runtime decision: {runtime['decision']!r}")


def redact(value: Any, key_hint: str = "") -> Any:
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


# Neutralize ("defang") constructs that the self-contained guard forbids so that
# benign occurrences inside an uploaded agent definition (e.g. a documentation
# URL) are shown inertly instead of crashing rendering. html.escape() already
# disarms "<script"/"<iframe" by escaping "<"; these patterns cover the tokens
# that survive HTML escaping. The result contains no live/clickable reference.
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
    if value is None or value == "":
        return html.escape(NO_EVIDENCE, quote=True)
    return _defang(html.escape(str(value), quote=True))


def esc_raw(value: Any) -> str:
    return _defang(html.escape(str(value), quote=True))


def sev_class(sev: Any) -> str:
    s = str(sev).upper()
    if s in ("CRITICAL", "HIGH"):
        return "high"
    if s == "MEDIUM":
        return "med"
    return "low"


def _pct(x: Any) -> int:
    try:
        return int(round(float(x) * 100))
    except (TypeError, ValueError):
        return 0


def _asr_color(p: int) -> str:
    return "var(--block)" if p >= 50 else ("var(--warn)" if p >= 20 else "var(--pass)")


def _cov_color(p: int) -> str:
    """Higher coverage is better (green); low coverage is a risk (red)."""
    return "var(--pass)" if p >= 70 else ("var(--warn)" if p >= 40 else "var(--block)")


CSS = """
:root{
  --bg0:#0b1437; --bg1:#060b28; --card:#0c1330; --card2:#0a1020;
  --card-a:rgba(6,11,40,.94); --card-b:rgba(10,14,35,.70);
  --line:rgba(226,232,240,.12); --ink:#ffffff; --mut:#a0aec0; --dim:#718096;
  --primary:#4318ff; --primary2:#9f7aea; --info:#0075ff; --info2:#21d4fd;
  --pass:#01b574; --warn:#ffb547; --block:#e31a1a;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:'Plus Jakarta Sans','Segoe UI',system-ui,-apple-system,Arial,sans-serif;
  color:var(--ink);background:#060b28;
  min-height:100vh;position:relative;overflow-x:hidden;-webkit-font-smoothing:antialiased;}
body::before{content:"";position:fixed;inset:-25%;z-index:-3;pointer-events:none;
  background:
   radial-gradient(620px 520px at 8% 0%,rgba(67,24,255,.28),transparent 55%),
   radial-gradient(720px 620px at 92% 4%,rgba(0,117,255,.22),transparent 55%),
   radial-gradient(680px 640px at 50% 112%,rgba(159,122,234,.16),transparent 60%),
   linear-gradient(160deg,#0b1437 0%,#060b28 60%);
  filter:blur(30px);animation:drift 24s ease-in-out infinite alternate}
@keyframes drift{0%{transform:translate3d(0,0,0) scale(1)}
  50%{transform:translate3d(2.5%,-2%,0) scale(1.06)}
  100%{transform:translate3d(-2.5%,2%,0) scale(1.04)}}
.aibg{position:fixed;top:26px;right:26px;width:320px;height:280px;z-index:-1;opacity:.14;pointer-events:none}
.aibg .nde{animation:pulse 3.2s ease-in-out infinite}
.aibg .nde:nth-child(2){animation-delay:.4s}
.aibg .nde:nth-child(3){animation-delay:.8s}
.aibg .nde:nth-child(4){animation-delay:1.2s}
.aibg .nde:nth-child(5){animation-delay:1.6s}
.aibg .nde:nth-child(6){animation-delay:2s}
.aibg .nde:nth-child(7){animation-delay:2.4s}
.aibg .edg{animation:flow 4s linear infinite}
@keyframes pulse{0%,100%{opacity:.3}50%{opacity:1}}
@keyframes flow{0%{stroke-dashoffset:24}100%{stroke-dashoffset:0}}
.app{display:flex;gap:24px;max-width:1500px;margin:0 auto;padding:22px;position:relative;z-index:1}
.sb{width:252px;flex:none;position:sticky;top:22px;align-self:flex-start;
  max-height:calc(100vh - 44px);overflow:auto;
  background:linear-gradient(160deg,var(--card-a),var(--card-b));
  border:1px solid var(--line);border-radius:22px;padding:20px 14px;
  backdrop-filter:blur(16px);box-shadow:0 24px 60px -30px rgba(0,0,0,.9)}
.sb .sbhead{display:flex;align-items:center;gap:12px;padding:6px 8px 16px;
  border-bottom:1px solid var(--line);margin-bottom:14px}
.sb .sbhead b{font-size:15px;font-weight:700;letter-spacing:.2px}
.sb .sbhead b span{background:linear-gradient(90deg,var(--info2),var(--primary2));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.main{flex:1;min-width:0;position:relative}
section[id]{scroll-margin-top:22px}
.topbar{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:22px}
.logo{width:44px;height:44px;flex:none;filter:drop-shadow(0 6px 14px rgba(0,117,255,.5))}
.brand h1{margin:0;font-size:22px;letter-spacing:.3px;font-weight:700}
.brand h1 span{background:linear-gradient(90deg,var(--info2),var(--primary2));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.brand p{margin:4px 0 0;color:var(--mut);font-size:13px}
.tags{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}
.chip{font-size:12px;font-weight:600;padding:7px 13px;border-radius:12px;
  border:1px solid var(--line);background:rgba(255,255,255,.05);color:var(--ink)}
.chip.mode{background:linear-gradient(135deg,var(--info),var(--primary));border:0;color:#fff}
.chip.sim{background:rgba(255,181,71,.16);color:#ffce8a;border-color:rgba(255,181,71,.4)}
.nav{display:flex;flex-direction:column;gap:4px}
.nav a{display:flex;align-items:center;gap:12px;font-size:14px;font-weight:600;color:var(--mut);
  text-decoration:none;padding:10px 11px;border-radius:14px;transition:.16s}
.nav a .ic{width:34px;height:34px;flex:none;border-radius:11px;display:grid;place-items:center;
  background:rgba(255,255,255,.06);color:var(--info2);transition:.16s}
.nav a .ic svg{width:18px;height:18px}
.nav a:hover{color:#fff;background:rgba(255,255,255,.04)}
.nav a:hover .ic{background:linear-gradient(135deg,var(--info),var(--info2));color:#fff}
.nav a.home{color:#fff}
.nav a.home .ic{background:linear-gradient(135deg,var(--info),var(--info2));color:#fff;
  box-shadow:0 8px 18px -8px rgba(0,117,255,.8)}
.panel{display:none}
.panel:target{display:block;animation:fadeUp .45s cubic-bezier(.2,.7,.2,1)}
@keyframes fadeUp{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:none}}
.backbar{display:flex;align-items:center;gap:12px;margin-bottom:4px}
.back{font-size:12px;font-weight:600;color:var(--info2);text-decoration:none;
  border:1px solid rgba(0,117,255,.35);padding:8px 14px;border-radius:12px;
  background:rgba(0,117,255,.1);transition:.15s}
.back:hover{background:rgba(0,117,255,.2);transform:translateX(-3px)}
.hint{margin:22px 0 2px;text-align:center;color:var(--dim);font-size:13px;letter-spacing:.02em}
.hint b{color:var(--info2)}
.cols{grid-template-columns:1fr 1fr;gap:20px}
.panel.cols:target{display:grid}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(212px,1fr));gap:20px;margin-top:4px}
.card{background:linear-gradient(160deg,var(--card-a),var(--card-b));
  border:1px solid var(--line);border-radius:20px;padding:20px;
  backdrop-filter:blur(8px);box-shadow:0 18px 44px -28px rgba(0,0,0,.92)}
.cardlink{text-decoration:none;color:inherit;display:block;
  transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease}
.cardlink:hover{transform:translateY(-4px);border-color:rgba(33,212,253,.5);
  box-shadow:0 28px 58px -24px rgba(0,117,255,.5)}
.k-title{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:var(--mut);margin:0 0 12px;font-weight:600}
.ring{width:118px;height:118px;border-radius:50%;margin:0 auto;
  display:grid;place-items:center;position:relative}
.ring::before{content:"";position:absolute;inset:10px;border-radius:50%;
  background:radial-gradient(circle at 50% 35%,#111a3f,#0a1130)}
.ring b{position:relative;font-size:26px;font-weight:700}
.ring small{position:relative;display:block;text-align:center;color:var(--mut);font-size:11px;margin-top:2px}
.big{font-size:34px;font-weight:800;margin:6px 0 2px}
.sub{color:var(--mut);font-size:13px}
.gauge{height:10px;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden;margin-top:14px}
.gauge i{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,var(--info),var(--info2))}
.posture-pill{display:inline-block;padding:8px 18px;border-radius:12px;font-weight:800;
  letter-spacing:.08em;font-size:15px}
.p-warn{background:linear-gradient(135deg,#ffb547,#f79009);color:#231603}
.p-pass{background:linear-gradient(135deg,#01b574,#019d64);color:#04140a}
.p-block{background:linear-gradient(135deg,#e31a1a,#b3140f);color:#fff}
.sev-mini{display:flex;gap:6px;margin-top:14px}
.sev-mini span{flex:1;text-align:center;border-radius:10px;padding:8px 4px;font-size:12px;font-weight:700}
.s-high{background:rgba(227,26,26,.16);color:#ff9d9d}
.s-med{background:rgba(255,181,71,.16);color:#ffce8a}
.s-low{background:rgba(0,117,255,.18);color:#7cc4ff}
.decision{font-size:26px;font-weight:800;color:var(--mut)}
.section{margin-top:26px}
.section h2{font-size:16px;margin:0 0 14px;display:flex;align-items:center;gap:10px}
.section h2::before{content:"";width:10px;height:22px;border-radius:4px;
  background:linear-gradient(180deg,var(--info2),var(--info),var(--primary))}
.gates{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
.gate{display:flex;align-items:center;gap:12px;background:linear-gradient(160deg,var(--card-a),var(--card-b));
  border:1px solid var(--line);border-radius:14px;padding:12px 14px}
.dot{width:12px;height:12px;border-radius:50%;flex:none;box-shadow:0 0 12px currentColor}
.g-good{color:var(--pass)} .g-fair{color:var(--info2)} .g-weak{color:var(--warn)} .g-gap{color:var(--block)}
.gate b{font-size:13px}
.gate span{color:var(--mut);font-size:12px;margin-left:auto}
.finds{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.find{background:linear-gradient(160deg,var(--card-a),var(--card-b));border:1px solid var(--line);
  border-radius:18px;padding:16px;position:relative;overflow:hidden}
.find::before{content:"";position:absolute;left:0;top:0;bottom:0;width:5px}
.find.high::before{background:linear-gradient(180deg,#e31a1a,#b3140f)}
.find.med::before{background:linear-gradient(180deg,#ffb547,#f79009)}
.find.low::before{background:linear-gradient(180deg,#21d4fd,#0075ff)}
.find .row{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.badge{font-size:11px;font-weight:800;padding:4px 10px;border-radius:999px;letter-spacing:.05em}
.b-high{background:rgba(227,26,26,.18);color:#ff9d9d}
.b-med{background:rgba(255,181,71,.18);color:#ffce8a}
.b-low{background:rgba(0,117,255,.2);color:#7cc4ff}
.fam{font-size:11px;color:var(--mut);border:1px solid var(--line);border-radius:999px;padding:4px 10px}
.fid{font-weight:800;color:var(--ink)}
.find h3{margin:2px 0 8px;font-size:15px}
.find p{margin:6px 0;font-size:13px;color:var(--mut);line-height:1.5}
.find p b{color:var(--ink)}
.prov{font-size:11px;color:var(--mut);border:1px dashed var(--line);border-radius:8px;padding:4px 8px;display:inline-block}
.cframe{margin:14px 0}
.cframe h3{margin:6px 0;font-size:15px}
.cframe .tags{margin:8px 0}
table{width:100%;border-collapse:collapse;background:linear-gradient(160deg,var(--card-a),var(--card-b));
  border-radius:16px;overflow:hidden;border:1px solid var(--line);font-size:13px}
th,td{padding:11px 14px;text-align:left;border-bottom:1px solid var(--line)}
th{background:rgba(255,255,255,.04);color:var(--mut);text-transform:uppercase;font-size:11px;letter-spacing:.1em}
tr:last-child td{border-bottom:0}
.tag{font-weight:700;padding:3px 9px;border-radius:8px;font-size:12px}
.t-warn{background:rgba(255,181,71,.18);color:#ffce8a}
.t-allow{background:rgba(1,181,116,.18);color:#7ff0c0}
.t-deny{background:rgba(227,26,26,.18);color:#ff9d9d}
.t-other{background:rgba(148,163,184,.18);color:#cbd5e1}
.lst{list-style:none;padding:0;margin:0;display:grid;gap:8px}
.lst li{background:linear-gradient(160deg,var(--card-a),var(--card-b));border:1px solid var(--line);border-radius:12px;padding:11px 14px;
  font-size:13px;color:var(--mut);position:relative;padding-left:32px}
.lst li::before{content:"";position:absolute;left:14px;top:15px;width:8px;height:8px;border-radius:50%;
  background:linear-gradient(90deg,var(--info),var(--info2))}
.foot{margin-top:26px;background:rgba(255,181,71,.08);border:1px solid rgba(255,181,71,.28);
  border-radius:18px;padding:18px 20px;color:#ffce8a;font-size:13px;line-height:1.6}
.foot b{color:#ffe0b0}
.meta{color:var(--dim);font-size:12px;margin-top:10px}
.rt-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-top:8px}
.rtrow{display:flex;align-items:center;gap:12px;margin:10px 0}
.rtrow .lab{width:230px;font-size:13px;line-height:1.3}
.track{flex:1;height:14px;border-radius:999px;background:rgba(255,255,255,.07);overflow:hidden}
.track i{display:block;height:100%;border-radius:999px}
.rtval{width:150px;text-align:right;font-size:12px;color:var(--mut)}
.sv{font-size:10px;padding:2px 7px;border-radius:6px;font-weight:700}
.sv-crit{background:rgba(227,26,26,.2);color:#ff9d9d}
.sv-high{background:rgba(255,181,71,.2);color:#ffce8a}
.sv-med{background:rgba(0,117,255,.2);color:#7cc4ff}
.rc{font-weight:700;padding:3px 9px;border-radius:8px;font-size:12px}
.rc-resisted{background:rgba(1,181,116,.18);color:#7ff0c0}
.rc-partial{background:rgba(255,181,71,.18);color:#ffce8a}
.rc-success{background:rgba(227,26,26,.18);color:#ff9d9d}
@media(max-width:980px){
  .app{flex-direction:column;padding:14px;gap:16px}
  .sb{width:auto;position:static;max-height:none}
  .sb .nav{flex-direction:row;flex-wrap:wrap}
  .nav a{padding:8px 10px}
}
@media(max-width:860px){.finds{grid-template-columns:1fr}
  .gates{grid-template-columns:1fr}.rtrow .lab{width:150px}.cols{grid-template-columns:1fr !important}}
"""

LOGO = (
    '<svg class="logo" viewBox="0 0 64 64" fill="none">'
    '<defs><linearGradient id="asL" x1="0" y1="0" x2="64" y2="64">'
    '<stop offset="0" stop-color="#21d4fd"/><stop offset=".5" stop-color="#0075ff"/>'
    '<stop offset="1" stop-color="#4318ff"/></linearGradient></defs>'
    '<path d="M32 4 54 12v18c0 15-9.5 24-22 30C19.5 54 10 45 10 30V12L32 4Z" fill="url(#asL)"/>'
    '<path d="M22 32l7 7 13-14" stroke="#0b1020" stroke-width="4.5" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>'
)


def render_kpis(data: dict[str, Any]) -> str:
    a = data.get("assurance") or {}
    posture = str(a.get("posture") or "")
    pill = POSTURE_PILL.get(posture, "p-warn")
    color = POSTURE_COLOR.get(posture, "var(--warn)")
    score = a.get("score")
    val = score if isinstance(score, (int, float)) else 0
    score_txt = esc_raw(score) if score is not None else "n/a"
    coverage = a.get("coverage")
    cov_pct = int(round(float(coverage) * 100)) if isinstance(coverage, (int, float)) else 0
    confidence = esc(a.get("confidence"))
    findings = data.get("findings") or []
    highs = sum(1 for f in findings if sev_class(f.get("severity")) == "high")
    meds = sum(1 for f in findings if sev_class(f.get("severity")) == "med")
    lows = sum(1 for f in findings if sev_class(f.get("severity")) == "low")

    cards = []
    rt = data.get("redteam")
    if rt:
        cov = _pct(rt.get("defense_coverage"))
        ccol = _cov_color(cov)
        cards.append(
            f'<a class="card cardlink" href="#redteam">'
            f'<p class="k-title">Defense Coverage</p>'
            f'<div class="ring" style="background:conic-gradient({ccol} calc({cov}*3.6deg),rgba(255,255,255,.07) 0)">'
            f'<b>{cov}%</b><small>weighted</small></div>'
            f'<p class="sub" style="text-align:center;margin-top:8px">Red-team &middot; tap to view</p></a>'
        )
    cards.append(
        f'<a class="card cardlink" href="#findings">'
        f'<p class="k-title">Assurance Posture</p>'
        f'<div style="text-align:center;padding:12px 0 6px"><span class="posture-pill {pill}">{esc(posture)}</span></div>'
        f'<p class="sub" style="text-align:center;margin-top:12px">Not authorization &middot; tap for findings</p></a>'
    )
    rai = data.get("responsible_ai")
    if rai:
        rposture = str(rai.get("posture") or "")
        rpill = POSTURE_PILL.get(rposture, "p-warn")
        rscore = rai.get("score")
        rscore_txt = esc_raw(rscore) if rscore is not None else "n/a"
        cards.append(
            f'<a class="card cardlink" href="#responsible-ai">'
            f'<p class="k-title">Responsible AI Posture</p>'
            f'<div style="text-align:center;padding:12px 0 6px"><span class="posture-pill {rpill}">{esc(rposture)}</span></div>'
            f'<p class="sub" style="text-align:center;margin-top:12px">Advisory &middot; {rscore_txt}/100 &middot; tap to view</p></a>'
        )
    cards.append(
        f'<a class="card cardlink" href="#families">'
        f'<p class="k-title">Assurance Score</p>'
        f'<div class="ring" style="background:conic-gradient({color} calc({val}*3.6deg),rgba(255,255,255,.07) 0)">'
        f'<b>{score_txt}</b><small>/ 100</small></div></a>'
    )
    cards.append(
        f'<div class="card"><p class="k-title">Coverage &amp; Confidence</p>'
        f'<div class="big">{cov_pct}%</div>'
        f'<div class="gauge"><i style="width:{cov_pct}%"></i></div>'
        f'<p class="sub" style="margin-top:12px">Confidence: <b style="color:#fcd34d">{confidence}</b></p></div>'
    )
    cards.append(
        f'<a class="card cardlink" href="#findings"><p class="k-title">Findings</p>'
        f'<div class="big">{len(findings)}</div>'
        f'<div class="sev-mini"><span class="s-high">{highs} High</span>'
        f'<span class="s-med">{meds} Med</span><span class="s-low">{lows} Low</span></div></a>'
    )
    return (f'<section id="overview" class="kpis">{"".join(cards)}</section>')


def render_subject_runtime(data: dict[str, Any]) -> str:
    subject = data.get("subject") or {}
    if isinstance(subject, dict):
        name = esc(subject.get("name"))
        owner = esc(subject.get("owner"))
        sponsor = esc(subject.get("sponsor"))
    else:
        name, owner, sponsor = esc(subject), esc(None), esc(None)
    a = data.get("assurance") or {}
    ver = esc(a.get("audit_version"))
    runtime = data.get("runtime")
    if isinstance(runtime, dict):
        decision = esc(runtime.get("decision"))
        rline = (f"Action: <b>{esc(runtime.get('action'))}</b> &middot; "
                 f"Target: <b>{esc(runtime.get('target'))}</b> &middot; "
                 f"Env: <b>{esc(runtime.get('environment'))}</b>")
        dec_html = f'<div class="decision" style="color:var(--ink)">{decision}</div><p class="sub">{rline}</p>'
    else:
        dec_html = ('<div class="decision">N / A</div>'
                    '<p class="sub">No action submitted in this mode. Posture and decision are kept separate.</p>')
    return f"""
  <section class="kpis" style="grid-template-columns:2fr 1fr">
    <div class="card">
      <p class="k-title">Subject Under Assessment</p>
      <div class="big" style="font-size:24px">{name}</div>
      <p class="sub">Owner: <b>{owner}</b> &middot; Sponsor: <b>{sponsor}</b> &middot; Audit version: <b>{ver}</b></p>
    </div>
    <div class="card">
      <p class="k-title">Runtime Decision</p>
      {dec_html}
    </div>
  </section>"""


BACKBAR = '<div class="backbar"><a class="back" href="#overview">&larr; Back to dashboard</a></div>'


def render_redteam(data: Any) -> str:
    rt = data.get("redteam") if isinstance(data, dict) else None
    if not rt:
        return ""
    asr = _pct(rt.get("overall_asr"))
    cov = _pct(rt.get("defense_coverage"))
    cov_col = _cov_color(cov)
    residual = _pct(rt.get("residual_exposure"))
    strong = _pct(rt.get("strong_defense_rate"))
    weak = _pct(rt.get("weak_defense_rate"))
    leak = _pct(rt.get("leakage_rate"))
    injr = _pct(rt.get("injection_resistance"))
    signal = str(rt.get("posture_signal") or "")
    pill = POSTURE_PILL.get(signal, "p-warn")
    weak_crit = rt.get("weak_critical_families") or []
    weak_crit_note = (
        f'<p class="sub" style="margin-top:10px;color:#fca5a5">Weak-only defenses on '
        f'critical families: <b>{esc(", ".join(weak_crit))}</b> &mdash; passing mentions, '
        f'not assured controls.</p>' if weak_crit else ""
    )

    sev_cls = {"CRITICAL": "sv-crit", "HIGH": "sv-high", "MEDIUM": "sv-med", "LOW": "sv-med"}
    bars = []
    for f in rt.get("families") or []:
        fa = _pct(f.get("asr"))
        sv = sev_cls.get(str(f.get("severity")).upper(), "sv-med")
        bars.append(
            f'<div class="rtrow"><div class="lab">{esc(f.get("id"))} '
            f'<span class="sv {sv}">{esc(f.get("severity"))}</span><br>'
            f'<span style="color:var(--dim);font-size:11px">{esc(f.get("name"))}</span></div>'
            f'<div class="track"><i style="width:{fa}%;background:{_asr_color(fa)}"></i></div>'
            f'<div class="rtval">ASR {fa}% &middot; {esc(f.get("success"))}/{esc(f.get("attempts"))}</div></div>'
        )

    rc_map = {"resisted": "rc-resisted", "partial": "rc-partial", "success": "rc-success"}
    rows = []
    for p in rt.get("probes") or []:
        cls = str(p.get("classification") or "")
        rc = rc_map.get(cls, "rc-partial")
        rows.append(
            f"<tr><td>{esc(p.get('id'))}</td><td>{esc(p.get('family'))}</td>"
            f"<td>{esc(p.get('severity'))}</td>"
            f"<td><span class='rc {rc}'>{esc(cls)}</span></td>"
            f"<td>{esc(p.get('confidence'))}</td><td>{esc(p.get('evidence'))}</td></tr>"
        )

    notes = "".join(f"<li>{esc(n)}</li>" for n in (rt.get("notes") or []))
    return f"""
  <section id="redteam" class="panel section">
    {BACKBAR}
    <h2>Adversarial Red-Team <span class="sub" style="font-weight:400">&middot; static inference from declared defenses, not a live attack</span></h2>
    <div class="rt-kpis">
      <div class="card"><p class="k-title">Defense Coverage</p>
        <div class="ring" style="background:conic-gradient({cov_col} calc({cov}*3.6deg),rgba(255,255,255,.07) 0)"><b>{cov}%</b><small>weighted</small></div>
        <p class="sub" style="text-align:center;margin-top:8px">Strong {strong}% &middot; Weak {weak}%</p></div>
      <div class="card"><p class="k-title">Residual Exposure</p><div class="big" style="color:#fca5a5">{residual}%</div>
        <div class="gauge"><i style="width:{residual}%;background:linear-gradient(90deg,#ef4444,#f97316)"></i></div>
        <p class="sub" style="margin-top:8px">1 &minus; coverage</p></div>
      <div class="card"><p class="k-title">Injection Resistance</p><div class="big">{injr}%</div>
        <div class="gauge"><i style="width:{injr}%;background:linear-gradient(90deg,#22c55e,#5eead4)"></i></div></div>
      <div class="card"><p class="k-title">Undefended Families (ASR)</p><div class="big">{asr}%</div>
        <div class="gauge"><i style="width:{asr}%;background:linear-gradient(90deg,#ef4444,#f97316)"></i></div>
        <p class="sub" style="margin-top:8px">Leakage {leak}%</p></div>
      <div class="card"><p class="k-title">Red-Team Signal</p>
        <div style="padding:14px 0 6px;text-align:center"><span class="posture-pill {pill}">{esc(signal)}</span></div>
        <p class="sub" style="text-align:center">Feeds posture (max-severity)</p></div>
    </div>
    {weak_crit_note}
    <h2 style="font-size:14px;margin-top:22px">Per-Family Attack Success</h2>
    <div class="card">{''.join(bars)}</div>
    <h2 style="font-size:14px;margin-top:22px">Probe Matrix &middot; inert data, never executed</h2>
    <table><tr><th>Probe</th><th>Family</th><th>Severity</th><th>Result</th><th>Confidence</th><th>Evidence</th></tr>
    {''.join(rows)}</table>
    <ul class="lst" style="margin-top:12px">{notes}</ul>
  </section>"""


def render_rai(data: dict[str, Any]) -> str:
    rai = data.get("responsible_ai") if isinstance(data, dict) else None
    if not rai:
        return ""
    posture = str(rai.get("posture") or "")
    pill = POSTURE_PILL.get(posture, "p-warn")
    color = POSTURE_COLOR.get(posture, "var(--warn)")
    score = rai.get("score")
    val = score if isinstance(score, (int, float)) else 0
    score_txt = esc_raw(score) if score is not None else "n/a"
    coverage = rai.get("coverage")
    cov_pct = int(round(float(coverage) * 100)) if isinstance(coverage, (int, float)) else 0
    confidence = esc(rai.get("confidence"))
    ver = esc(rai.get("rai_version"))

    cells = []
    for g in rai.get("pillars") or []:
        rating = str(g.get("rating") or "").lower()
        cls = GATE_CLASS.get(rating, "g-weak")
        cells.append(
            f'<div class="gate"><span class="dot {cls}"></span>'
            f'<b>{esc(g.get("id"))} {esc(g.get("name"))}</b>'
            f'<span>{esc(g.get("rating"))}</span></div>'
        )
    grid = f'<div class="gates">{"".join(cells)}</div>' if cells else ""

    fcards = []
    for f in rai.get("findings") or []:
        sc = sev_class(f.get("severity"))
        badge = {"high": "b-high", "med": "b-med", "low": "b-low"}[sc]
        hypo = f.get("hypothesis")
        hypo_html = f'<p><b>Hypothesis:</b> <i>{esc(hypo)}</i></p>' if hypo else ""
        fcards.append(f"""
      <div class="find {sc}">
        <div class="row"><span class="fid">{esc(f.get('id'))}</span>
          <span class="badge {badge}">{esc(f.get('severity'))}</span>
          <span class="fam">{esc(f.get('control_family'))}</span></div>
        <h3>{esc(f.get('title'))}</h3>
        <p><b>Observation:</b> {esc(f.get('observation'))}</p>
        {hypo_html}
        <p><b>Remediation:</b> {esc(f.get('remediation'))}</p>
      </div>""")
    finds = f'<div class="finds">{"".join(fcards)}</div>' if fcards else "<p class='sub'>No Responsible AI findings recorded.</p>"
    limits = _ul(rai.get("coverage_limitations"))

    return f"""
  <section id="responsible-ai" class="panel section">
    {BACKBAR}
    <h2>Responsible AI Assessment <span class="sub" style="font-weight:400">&middot; advisory &amp; simulation-only, not certification</span></h2>
    <div class="rt-kpis">
      <div class="card"><p class="k-title">Responsible AI Posture</p>
        <div style="padding:14px 0 6px;text-align:center"><span class="posture-pill {pill}">{esc(posture)}</span></div>
        <p class="sub" style="text-align:center">Assurance signal &middot; not authorization</p></div>
      <div class="card"><p class="k-title">RAI Score</p>
        <div class="ring" style="background:conic-gradient({color} calc({val}*3.6deg),rgba(255,255,255,.07) 0)"><b>{score_txt}</b><small>/ 100</small></div></div>
      <div class="card"><p class="k-title">Coverage</p><div class="big">{cov_pct}%</div>
        <div class="gauge"><i style="width:{cov_pct}%"></i></div></div>
      <div class="card"><p class="k-title">Confidence</p>
        <div class="big" style="font-size:22px;color:#fcd34d">{confidence}</div>
        <p class="sub">Pillar framework: <b>{ver}</b></p></div>
    </div>
    <h2 style="font-size:14px;margin-top:22px">Six Responsible AI Pillars</h2>
    {grid}
    <h2 style="font-size:14px;margin-top:22px">Responsible AI Findings</h2>
    {finds}
    <h2 style="font-size:14px;margin-top:22px">Responsible AI Coverage Limitations</h2>
    {limits}
  </section>"""


def render_gates(data: dict[str, Any]) -> str:
    gates = data.get("gates")
    if not gates:
        return ""
    cells = []
    for g in gates:
        rating = str(g.get("rating") or "").lower()
        cls = GATE_CLASS.get(rating, "g-weak")
        cells.append(
            f'<div class="gate"><span class="dot {cls}"></span>'
            f'<b>{esc(g.get("id"))} {esc(g.get("name"))}</b>'
            f'<span>{esc(g.get("rating"))}</span></div>'
        )
    return f"""
  <section id="families" class="panel section">
    {BACKBAR}
    <h2>Control Families</h2>
    <div class="gates">{''.join(cells)}</div>
  </section>"""


def render_findings(data: dict[str, Any]) -> str:
    findings = data.get("findings") or []
    if not findings:
        return ('<section id="findings" class="panel section"><div class="backbar">'
                '<a class="back" href="#overview">&larr; Back to dashboard</a></div>'
                '<h2>Findings &amp; Evidence</h2>'
                '<p class="sub">No findings recorded.</p></section>')
    cards = []
    for f in findings:
        sc = sev_class(f.get("severity"))
        badge = {"high": "b-high", "med": "b-med", "low": "b-low"}[sc]
        hypo = f.get("hypothesis")
        hypo_html = f'<p><b>Hypothesis:</b> <i>{esc(hypo)}</i></p>' if hypo else ""
        impact = f.get("impact")
        impact_html = f'<p><b>Impact:</b> {esc(impact)}</p>' if impact else ""
        prov = f.get("provenance")
        conf = f.get("confidence")
        eff = f.get("effective_severity")
        prov_bits = []
        if prov:
            prov_bits.append(f"Source: {esc(prov)}")
        if conf is not None:
            prov_bits.append(f"confidence {esc(conf)}")
        if eff and eff != f.get("severity"):
            prov_bits.append(f"effective {esc(eff)}")
        prov_html = (
            f'<p class="prov">{" &middot; ".join(prov_bits)}</p>' if prov_bits else ""
        )
        cards.append(f"""
      <div class="find {sc}">
        <div class="row"><span class="fid">{esc(f.get('id'))}</span>
          <span class="badge {badge}">{esc(f.get('severity'))}</span>
          <span class="fam">{esc(f.get('control_family'))}</span></div>
        <h3>{esc(f.get('title'))}</h3>
        {prov_html}
        <p><b>Observation:</b> {esc(f.get('observation'))}</p>
        {impact_html}{hypo_html}
        <p><b>Remediation:</b> {esc(f.get('remediation'))}</p>
      </div>""")
    return f"""
  <section id="findings" class="panel section">
    {BACKBAR}
    <h2>Findings &amp; Evidence</h2>
    <div class="finds">{''.join(cards)}</div>
  </section>"""


_COMPLIANCE_STATUS_CLASS = {
    "Evidenced": "g-good",
    "Partial": "g-fair",
    "Declared (not tested)": "g-fair",
    "Gap": "g-weak",
    "Unevidenced": "g-gap",
}


def render_compliance(data: dict[str, Any]) -> str:
    compliance = data.get("compliance")
    if not compliance or not compliance.get("frameworks"):
        return ""
    blocks = []
    for fw in compliance.get("frameworks") or []:
        rows = []
        for c in fw.get("controls") or []:
            status = str(c.get("status") or "")
            cls = _COMPLIANCE_STATUS_CLASS.get(status, "g-gap")
            fams = ", ".join(c.get("families") or [])
            rows.append(
                f"<tr><td><b>{esc(c.get('control_id'))}</b> {esc(c.get('control_title'))}</td>"
                f"<td>{esc(fams)}</td>"
                f"<td><span class='dot {cls}'></span>{esc(status)}</td>"
                f"<td>{esc(c.get('note'))}</td></tr>"
            )
        summary = fw.get("summary") or {}
        chips = " ".join(
            f"<span class='chip'>{esc(k)}: {esc(v)}</span>"
            for k, v in summary.items()
            if v
        )
        blocks.append(f"""
      <div class="cframe">
        <h3>{esc(fw.get('name'))} <span class="sub">v{esc(fw.get('version'))}</span></h3>
        <div class="tags">{chips}</div>
        <table><tr><th>Mapped control</th><th>Families</th><th>Coverage</th><th>Note</th></tr>
        {''.join(rows)}</table>
      </div>""")
    disclaimer = esc(compliance.get("disclaimer"))
    version = esc(compliance.get("map_version"))
    return f"""
  <section id="compliance" class="panel section">
    {BACKBAR}
    <h2>Compliance Framework Mapping</h2>
    <p class="sub">Advisory &middot; not certification &middot; map {version}</p>
    {''.join(blocks)}
    <p class="note">{disclaimer}</p>
  </section>"""


def render_policy(data: dict[str, Any]) -> str:
    rows = data.get("policy_matches") or []
    if not rows:
        return ""
    tag_map = {"WARN": "t-warn", "ALLOW": "t-allow", "DENY": "t-deny"}
    body = []
    for m in rows:
        d = str(m.get("decision") or "")
        tag = tag_map.get(d, "t-other")
        body.append(
            f"<tr><td>{esc(m.get('control_id'))}</td><td>{esc(m.get('reason_code'))}</td>"
            f"<td><span class='tag {tag}'>{esc(d)}</span></td>"
            f"<td>{esc(m.get('explanation'))}</td></tr>"
        )
    return f"""
  <section id="policy" class="panel section">
    {BACKBAR}
    <h2>Matched Policy Controls</h2>
    <table><tr><th>Control</th><th>Reason code</th><th>Decision</th><th>Explanation</th></tr>
    {''.join(body)}</table>
  </section>"""


def _ul(items: Any, empty: str = "None recorded.") -> str:
    if not items:
        return f"<p class='sub'>{esc_raw(empty)}</p>"
    return "<ul class='lst'>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"


def render_cols(data: dict[str, Any]) -> str:
    findings = data.get("findings") or []
    remediations = [f.get("remediation") for f in findings if f.get("remediation")]
    return f"""
  <section id="remediations" class="panel section cols">
    {BACKBAR}
    <div><h2>Remediations</h2>{_ul(remediations)}</div>
    <div><h2>Coverage Limitations</h2>{_ul(data.get('coverage_limitations'))}</div>
  </section>"""


def render_capabilities(data: dict[str, Any]) -> str:
    cap = data.get("platform_capabilities") if isinstance(data, dict) else None
    if not cap:
        return ""

    det = cap.get("determinism") or {}
    led = cap.get("ledger") or {}
    met = cap.get("metrics") or {}

    def _yn(flag: Any) -> str:
        ok = bool(flag)
        cls = "g-good" if ok else "g-gap"
        txt = "verified" if ok else "unverified"
        return f'<span class="dot {cls}"></span>{txt}'

    kpis = f"""
    <div class="rt-kpis">
      <div class="card"><p class="k-title">Deterministic Policy</p>
        <div class="big" style="font-size:18px">{esc(det.get('deterministic') and 'YES' or 'NO')}</div>
        <p class="sub">{esc(det.get('replay_runs'))} replays &middot; 1 distinct outcome</p>
        <p class="sub">bundle <b>{esc(str(det.get('policy_bundle_hash') or '')[:16])}…</b></p></div>
      <div class="card"><p class="k-title">Audit Ledger</p>
        <div class="big" style="font-size:18px">{_yn(led.get('verified'))}</div>
        <p class="sub">{esc(led.get('entries'))} entries &middot; hash-chained</p>
        <p class="sub">head <b>{esc(str(led.get('head_hash') or '')[:16])}…</b></p></div>
      <div class="card"><p class="k-title">Governance Metrics</p>
        <div class="big">{esc(met.get('block_rate_pct'))}%</div>
        <p class="sub">high-risk actions blocked</p>
        <p class="sub">{esc(met.get('high_risk_blocked'))} of {esc(met.get('total_actions'))} actions</p></div>
      <div class="card"><p class="k-title">ASR Reduction</p>
        <div class="big">{esc(met.get('asr_reduction_relative_pct'))}%</div>
        <p class="sub">relative, undefended &rarr; defended</p>
        <p class="sub">Gate R static red-team</p></div>
    </div>"""

    tamper = led.get("tamper_demo")
    tamper_html = (
        f'<p class="sub" style="margin-top:10px">Tamper check: a mutated record was '
        f'detected at <b>entry #{esc(tamper.get("broken_at"))}</b> '
        f'(reason: <b>{esc(tamper.get("reason"))}</b>) &mdash; the chain fails closed.</p>'
        if isinstance(tamper, dict) else ""
    )

    pipeline = _ul(cap.get("pipeline"), empty="No pipeline capabilities listed.")
    integrations = _ul(cap.get("integrations"), empty="No integrations listed.")

    return f"""
  <section id="capabilities" class="panel section">
    {BACKBAR}
    <h2>Platform Capabilities <span class="sub" style="font-weight:400">&middot; deterministic controls, audit ledger &amp; enterprise integrations</span></h2>
    {kpis}
    {tamper_html}
    <div class="cols" style="margin-top:18px">
      <div><h2 style="font-size:14px">Governance Pipeline</h2>{pipeline}</div>
      <div><h2 style="font-size:14px">Microsoft-Ecosystem Integrations (offline)</h2>{integrations}</div>
    </div>
  </section>"""


ICONS = {
    "grid": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>',
    "target": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/></svg>',
    "badge": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 4 6v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V6l-8-4z"/><path d="M9 12l2 2 4-4"/></svg>',
    "layers": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
    "alert": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 2 20h20L12 3z"/><path d="M12 9v5"/><path d="M12 17h.01"/></svg>',
    "doc": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6"/><path d="M9 13h6"/><path d="M9 17h6"/></svg>',
    "cpu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6" rx="1"/><path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2"/></svg>',
    "tools": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a4 4 0 0 1-5.3 5.3L4 17v3h3l5.4-5.4a4 4 0 0 1 5.3-5.3l-2.7 2.7-2-2 2.7-2.7z"/></svg>',
}


def _nav(data: dict[str, Any]) -> str:
    items = [("#overview", "Overview", "grid")]
    if data.get("redteam"):
        items.append(("#redteam", "Red-Team", "target"))
    if data.get("responsible_ai"):
        items.append(("#responsible-ai", "Responsible AI", "badge"))
    if data.get("gates"):
        items.append(("#families", "Families", "layers"))
    if data.get("findings"):
        items.append(("#findings", "Findings", "alert"))
    if data.get("compliance"):
        items.append(("#compliance", "Compliance", "doc"))
    if data.get("policy_matches"):
        items.append(("#policy", "Policy", "doc"))
    if data.get("platform_capabilities"):
        items.append(("#capabilities", "Capabilities", "cpu"))
    items.append(("#remediations", "Remediations", "tools"))
    links = "".join(
        f'<a class="{"home" if h == "#overview" else ""}" href="{h}">'
        f'<span class="ic">{ICONS.get(ic, "")}</span><span>{esc_raw(t)}</span></a>'
        for h, t, ic in items
    )
    return f'<nav class="nav">{links}</nav>'


NEURAL_SVG = (
    '<svg class="aibg" viewBox="0 0 340 300" fill="none" aria-hidden="true">'
    '<g stroke="#0075ff" stroke-width="1" stroke-dasharray="6 4" opacity=".7">'
    '<line class="edg" x1="40" y1="60" x2="170" y2="40"/>'
    '<line class="edg" x1="40" y1="60" x2="170" y2="150"/>'
    '<line class="edg" x1="40" y1="150" x2="170" y2="150"/>'
    '<line class="edg" x1="40" y1="150" x2="170" y2="250"/>'
    '<line class="edg" x1="40" y1="240" x2="170" y2="150"/>'
    '<line class="edg" x1="40" y1="240" x2="170" y2="250"/>'
    '<line class="edg" x1="170" y1="40" x2="300" y2="110"/>'
    '<line class="edg" x1="170" y1="150" x2="300" y2="110"/>'
    '<line class="edg" x1="170" y1="150" x2="300" y2="190"/>'
    '<line class="edg" x1="170" y1="250" x2="300" y2="190"/>'
    '</g>'
    '<g fill="#21d4fd">'
    '<circle class="nde" cx="40" cy="60" r="7"/>'
    '<circle class="nde" cx="40" cy="150" r="7"/>'
    '<circle class="nde" cx="40" cy="240" r="7"/>'
    '<circle class="nde" cx="170" cy="40" r="8" fill="#9f7aea"/>'
    '<circle class="nde" cx="170" cy="150" r="8" fill="#9f7aea"/>'
    '<circle class="nde" cx="170" cy="250" r="8" fill="#9f7aea"/>'
    '<circle class="nde" cx="300" cy="110" r="9" fill="#0075ff"/>'
    '<circle class="nde" cx="300" cy="190" r="9" fill="#0075ff"/>'
    '</g></svg>'
)


def build_html(data: dict[str, Any]) -> str:
    validate(data)
    safe = redact(data)
    simulation = bool(safe.get("simulation"))
    sim_chip = '<span class="chip sim">SIMULATION</span>' if simulation else ""
    evidence = safe.get("evidence_summary") or {}
    records = evidence.get("records") if isinstance(evidence, dict) else None
    meta = (f"Mode: {esc_raw(safe.get('mode'))} &middot; "
            f"Audit version: {esc(( safe.get('assurance') or {}).get('audit_version'))} &middot; "
            f"Generated {esc(safe.get('timestamp_utc'))} &middot; "
            f"Evidence records: {esc(records)} (append-only)")
    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AgentShield AI Dashboard {esc_raw(safe.get('trace_id'))}</title>
<style>{CSS}</style>
</head>
<body>
{NEURAL_SVG}
<div class="app">
  <aside class="sb">
    <div class="sbhead">
      {LOGO}
      <b>AgentShield <span>AI</span></b>
    </div>
    {_nav(safe)}
  </aside>
  <main class="main">
    <header class="topbar">
      <div class="brand">
        <h1>AgentShield <span>AI</span> &middot; Assessment Dashboard</h1>
        <p>Predict &middot; Govern &middot; Approve &middot; Execute Safely &middot; Audit</p>
      </div>
      <div class="tags">
        <span class="chip mode">{esc(safe.get('mode'))}</span>
        {sim_chip}
        <span class="chip">trace: {esc(safe.get('trace_id'))}</span>
      </div>
    </header>
    {render_kpis(safe)}
    {render_subject_runtime(safe)}
    <p class="hint">Your dashboard is the home view &middot; <b>click any card or tab</b> to open a detailed section, then use <b>&larr; Back to dashboard</b> to return.</p>
    {render_redteam(safe)}
    {render_rai(safe)}
    {render_gates(safe)}
    {render_findings(safe)}
    {render_compliance(safe)}
    {render_policy(safe)}
    {render_capabilities(safe)}
    {render_cols(safe)}
    <footer class="foot">
      <b>PASS is not certification. WARN is not authorization.</b> {esc(safe.get('accountability_statement'))}
      <div class="meta">{meta}</div>
    </footer>
  </main>
</div>
</body>
</html>"""
    _assert_self_contained(document)
    return document


def _assert_self_contained(document: str) -> None:
    lowered = document.lower()
    forbidden = ["<script", "javascript:", "onerror=", "onload=", "<iframe",
                 "http://", "https://", "//fonts.", "srcset="]
    hits = [token for token in forbidden if token in lowered]
    if hits:
        raise ReportError(f"unsafe constructs in output: {', '.join(hits)}")


def subject_name(data: dict[str, Any]) -> str:
    subject = data.get("subject")
    if isinstance(subject, dict):
        return str(subject.get("name") or "agent")
    return str(subject or "agent")


def report_filename(name: str) -> str:
    """Canonical report file name: AgentShield_AI_Report_<AgentName>.html.

    The agent name is sanitized for safe file systems: whitespace becomes
    underscores and characters outside [A-Za-z0-9._-] are dropped.
    """

    base = re.sub(r"\s+", "_", str(name).strip())
    base = re.sub(r"[^A-Za-z0-9._-]", "", base)
    base = re.sub(r"_{2,}", "_", base).strip("._") or "agent"
    return f"AgentShield_AI_Report_{base}.html"


def generate(input_path: str, output_path: str | None = None) -> str:
    """Render the dashboard. When output_path is omitted or is an existing
    directory, the file is named by the AgentShield_AI_Report_<AgentName>
    convention derived from the report subject."""

    with open(input_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if output_path is None or os.path.isdir(output_path):
        fname = report_filename(subject_name(data))
        output_path = os.path.join(output_path, fname) if output_path else fname
    document = build_html(data)
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(document)
    return output_path


def main(argv: list[str]) -> int:
    if len(argv) not in (1, 2):
        sys.stderr.write(
            "usage: python dashboard_report.py <input.json> [output.html | output_dir]\n"
            "  If output is omitted or a directory, the file is named "
            "AgentShield_AI_Report_<AgentName>.html\n"
        )
        return 2
    try:
        written = generate(argv[0], argv[1] if len(argv) == 2 else None)
    except (ReportError, json.JSONDecodeError, OSError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1
    sys.stdout.write(written + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
