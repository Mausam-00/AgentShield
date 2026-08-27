# AgentShield HTML Report Schema

## Root object

| Field | Type | Required | Rule |
|---|---|---:|---|
| `trace_id` | string | yes | Non-secret correlation identifier |
| `timestamp_utc` | string | yes | ISO 8601 UTC timestamp |
| `mode` | string | yes | `ASSESS`, `OBSERVE`, `GOVERN`, or `CONTROLLED LIVE` |
| `simulation` | boolean | yes | Must be true unless genuine live evidence exists |
| `subject` | object | yes | Subject identity and ownership |
| `assurance` | object | yes | Assurance result only |
| `runtime` | object or null | yes | Runtime decision, separate from assurance |
| `findings` | array | yes | May be empty |
| `coverage_limitations` | array | yes | May be empty |
| `observations` | array | yes | Evidence-backed statements |
| `hypotheses` | array | yes | Explicitly non-evidentiary statements |
| `policy_matches` | array | yes | Versioned control results |
| `approval` | object or null | yes | Approval and binding data |
| `plan` | object or null | yes | Ordered constrained plan |
| `validation` | object or null | yes | Expected-versus-observed comparison |
| `evidence_summary` | object | yes | Append-only record summary |
| `limitations` | array | yes | May be empty but must be rendered |
| `accountability_statement` | string | yes | Human accountability statement |

## Assurance object

Required fields:

- `posture`: `PASS`, `WARN`, or `BLOCK`;
- `score`: integer from 0 through 100, or null when unavailable;
- `coverage`: number from 0 through 1;
- `confidence`: `HIGH`, `MEDIUM`, or `LOW`;
- `audit_version`;
- `definition_hash`, nullable; and
- `tool_manifest_hash`, nullable.

The renderer must not infer a runtime decision from posture.

## Runtime object

When present, required fields are:

- `decision`: `ALLOW`, `TRANSFORM`, `APPROVE`, `ESCALATE`, or `DENY`;
- `policy_version`;
- `action`;
- `target`;
- `purpose`;
- `environment`;
- `operational_impact_score`, nullable; and
- `nothing_reached_target`: boolean.

## Finding object

Required fields are `id`, `severity`, `control_family`, `evidence_state`,
`title`, `observation`, `impact`, and `remediation`. `hypothesis` is optional
and must be visually distinguished from observations.

## Approval object

When present, include `result`, `approver`, `requester`, `action`, `target`,
`plan_hash`, `policy_version`, and `expiry`. The renderer must show missing
values as `No evidence available`.

## Plan object

Include `plan_hash` and ordered `steps`. Each step includes `id`, `action`,
`target_scope`, `reason`, `validation`, `rollback`, `stop_condition`, and
`required_capability`.

## Safe rendering requirements

- Escape `&`, `<`, `>`, `"`, and `'` in all dynamic values.
- Recursively redact keys matching credential-like terms such as `password`,
  `passwd`, `secret`, `token`, `api_key`, `private_key`, `credential`,
  `authorization`, and `cookie`.
- Render null or absent optional evidence as `No evidence available`.
- Use embedded CSS only.
- Do not include JavaScript, remote fonts, trackers, iframes, or network calls.
- Clearly label simulations.
- State: `PASS is not certification.`
- Keep assurance posture and runtime decision in separate sections and fields.


## Red-team object (optional) — Gate R

An optional top-level `redteam` object drives the dashboard "Adversarial
Red-Team" panel. It is produced by `agentshield.redteam.redteam_to_report_section`
and is ignored by the classic renderer, so one JSON drives both renderers.

| Field | Type | Rule |
|---|---|---|
| `mode` | string | `static` (live mode is disabled in this build) |
| `subject` | string | Target agent name |
| `overall_asr` | number | Attack Success Rate (undefended families), 0 through 1 |
| `refusal_rate` | number | 0 through 1 |
| `leakage_rate` | number | Canary leakage, 0 through 1 |
| `injection_resistance` | number | 0 through 1 |
| `defense_coverage` | number | Weighted declared-defense coverage (strong=1, weak=0.5), 0 through 1 |
| `residual_exposure` | number | `1 - defense_coverage`; the honest headline risk, 0 through 1 |
| `strong_defense_rate` | number | Fraction of families with a strong declared defense |
| `weak_defense_rate` | number | Fraction of families with only a weak/partial mention |
| `weak_critical_families` | array | Critical families defended by weak-only mentions |
| `posture_signal` | string | `PASS`, `WARN`, or `BLOCK` (static is capped at WARN) |
| `families` | array | Per-family metrics |
| `probes` | array | Per-probe classification (inert; never executed) |
| `notes` | array | Simulation / containment notes |

Each `families` entry: `id`, `name`, `stage`, `severity`, `attempts`,
`resisted`, `partial`, `success`, `asr`.

Each `probes` entry: `id`, `family`, `stage`, `severity`, `classification`
(`resisted` / `partial` / `success`), `confidence`, `evidence`, `description`.

Red-team classifications are static inference from the target definition's
declared defenses, not live attack outcomes. Probe payloads are inert data.
The red-team `posture_signal` combines with the assurance posture by
max-severity via `agentshield.redteam.combine_posture`.
