---
name: agentshield-html-report
description: Generate a standalone AgentShield AI HTML report from existing evidence only after an explicit end-user report request.
---

# AgentShield AI HTML Report

## Trigger

Use this skill only when the end user explicitly asks to generate, create,
export, save, or view an HTML, web, audit, assurance, assessment, or evidence
report.

Do not trigger automatically after an assessment, governance decision, denial,
approval, or validation.

## Inputs

- Existing AgentShield evidence record or assessment data.
- Desired output path, if supplied.
- Report title, if supplied.

Do not rerun an assessment to fill missing fields. Do not request or accept
credentials as report inputs.

## Procedure

1. Validate input against `references/report-schema.md`.
2. Preserve assurance posture and runtime decision as separate fields.
3. Replace unavailable optional evidence with `No evidence available`.
4. Redact credential-like field names and values.
5. HTML-escape every dynamic value before rendering.
6. Render a standalone document with embedded CSS only.
7. Include a simulation label whenever no live connector produced the evidence.
8. Include coverage, limitations, accountability, and the statement that
   `PASS` is not certification.
9. Reject output that contains external scripts, fonts, trackers, links to
   executable resources, or network calls.

## Output naming convention (required)

Every generated report MUST be named:

```text
AgentShield_AI_Report_<AgentName>.html
```

`<AgentName>` is the name of the agent/subject the report runs on. The
`dashboard_report.py` generator produces this name automatically when the output
argument is omitted or is a directory (it reads `subject.name`, replaces
whitespace with `_`, and drops characters outside `[A-Za-z0-9._-]`). Examples:

| Subject (`subject.name`) | Generated file name |
|---|---|
| `dr.SHA` | `AgentShield_AI_Report_dr.SHA.html` |
| `TroubleshootBuddy` | `AgentShield_AI_Report_TroubleshootBuddy.html` |
| `Contoso Ops Agent` | `AgentShield_AI_Report_Contoso_Ops_Agent.html` |

```text
# auto-named into the docs directory
python scripts/dashboard_report.py assessment.json docs
```

## Output

Two self-contained renderers share the same input schema
(`references/report-schema.md`). Both validate, redact, escape, and fail closed
on unsafe output. **`dashboard_report.py` (the Vision UI dashboard) is the
default renderer for all report generation** — use it unless the user explicitly
asks for the classic print layout. The live web app renders every report through
`dashboard_report.py`.

### 1. Vision UI dashboard (default)

```text
scripts/dashboard_report.py INPUT_JSON OUTPUT_HTML
```

The Vision UI dark dashboard: a deep-navy glassmorphism layout with an icon
sidebar, KPI cards (posture pill, conic-gradient score ring, coverage gauge,
severity breakdown), a subject panel, a separate runtime panel, an optional
control-family grid, severity-coded finding cards, a policy table, and ranked
remediations. Fully responsive. This is the standard output for AgentShield
reports.

### 2. Classic document (light, print-friendly — opt-in)

```text
scripts/generate_report.py INPUT_JSON OUTPUT_HTML
```

Sectioned light report layout. Use only when the user explicitly requests a
print-friendly or long-form archival document.

Both renderers produce embedded CSS and inline SVG only: no JavaScript, remote
fonts, trackers, iframes, or network calls.

### Optional schema field for the dashboard grid

The dashboard renders a control-family grid when the input includes an optional
top-level `gates` array. Each entry:

```json
{ "id": "ASF-05", "name": "Data boundary & sensitivity", "rating": "gap" }
```

`rating` is one of `good`, `fair`, `weak`, or `gap`. The field is optional and
ignored by the classic renderer, so a single JSON drives both.

### Example

```text
python scripts/dashboard_report.py assessment.json report-dashboard.html
```

## Failure behavior

Fail explicitly for malformed required fields or unsafe output paths. Never
invent evidence, silently omit validation errors, or produce a success-shaped
report after a rendering failure.


## Gate R — Adversarial red-team panel

When the input JSON includes an optional top-level `redteam` object (see
`references/report-schema.md`), the dark dashboard renders an **Adversarial
Red-Team** panel led by a **Defense Coverage** ring (weighted: strong
declared-defense = 1.0, weak/partial mention = 0.5) with a strong/weak split, a
**Residual Exposure** figure (`1 − coverage`, the honest headline), injection
resistance, an **Undefended Families (ASR)** metric, a red-team posture-signal
pill, a weak-only-critical-families note, per-family bars, and an inert probe
matrix. Build the object with:

```python
from agentshield import run_static_redteam, redteam_to_report_section, workflow_to_report

rt = run_static_redteam(definition_text, subject="TargetAgent")
report = workflow_to_report(result, redteam=redteam_to_report_section(rt))
```

Red-team analysis is static, simulation-only inference over the target's
declared defenses. Probe payloads are inert data and are never executed.

**Reporting honesty (required).** Do not lead with or headline "0% ASR". ASR
counts only *undefended* families (no defense signal at all), so a definition
that merely mentions defenses can score 0% ASR while still being weakly
defended. Always lead with **Defense Coverage** and **Residual Exposure**, and
surface any critical family (injection, tool-misuse, exfiltration) that is
defended by weak-only mentions. Static red-team posture is capped at **WARN** and
drops to WARN whenever a critical family has weak-only coverage — it must never
report **PASS**. The classic renderer ignores the `redteam` field.


## Dashboard navigation & overview (v3 — single-view panels)

The dark dashboard opens as a **dashboard-first single view**: on load only the
KPI cards, subject summary, and a sticky **tab bar** are visible. Every detail
section is a hidden **panel** rendered on demand.

- Clicking a **KPI card** or a **tab** reveals just that one section (pure-CSS
  `:target` panels with a fade-up animation) and hides the others.
- Each panel has a **← Back to dashboard** control; the **Overview** tab also
  returns to the dashboard-only view.
- This uses only CSS `:target` and anchor fragments — **no JavaScript** — so the
  output stays fully self-contained. Panel ids: `#overview`, `#redteam`,
  `#responsible-ai`, `#families`, `#findings`, `#policy`, `#remediations`.

The theme is a near-black security/AI aesthetic with an animated background:
drifting aurora gradients, a slow-panning masked grid, a sweeping scan line, and
a pulsing inline-SVG neural-network watermark — all CSS keyframes / inline SVG,
no external assets.

When a `redteam` object is present, its **Defense Coverage** is the first KPI
card and opens the **Adversarial Red-Team** panel (never labelled "Gate R" in
output). Do not headline the Attack Success Rate; ASR appears inside the panel as
**Undefended Families**. When a `responsible_ai` object is present, its posture is a
KPI card opening the **Responsible AI Assessment** panel (six-pillar grid, RAI
findings, RAI coverage limitations) — advisory and simulation-only, kept separate
from assurance posture and the runtime decision.

### Optional `responsible_ai` block

```json
{
  "responsible_ai": {
    "posture": "RAI-WARN",
    "score": 62,
    "coverage": 0.7,
    "confidence": "MEDIUM",
    "rai_version": "RAI-2026.08",
    "pillars": [{ "id": "RAI-01", "name": "Fairness and non-discrimination", "rating": "gap" }],
    "findings": [{ "id": "RF-1", "severity": "HIGH", "control_family": "RAI-01 Fairness",
                   "title": "...", "observation": "...", "remediation": "..." }],
    "coverage_limitations": ["No evidence for RAI-04 (Inclusiveness and accessibility)."]
  }
}
```

Build it from `agentshield.rai_to_report(...)`: map `assurance`→posture/score/
coverage/confidence/`audit_version`→`rai_version`, `gates`→`pillars`, and reuse
`findings` and `coverage_limitations`. The classic renderer ignores this field.
