# AgentShield AI

<img src="docs/Thumbnail.jpg" alt="AgentShield AI logo" width="360">

**The Security Control Plane for the Agentic Enterprise**

> Predict. Govern. Approve. Execute Safely. Audit.

AgentShield AI is a governance and assurance agent for AI agents, agentic
solutions, and deployment or orchestration systems. It audits an agent's design,
evaluates a proposed action before it reaches a target, predicts operational
impact, applies deterministic policy, routes human approval, produces a
constrained safe plan, validates observed behavior, and preserves evidence.

AgentShield keeps two decisions strictly separate:

| Assurance posture | Runtime decision |
|---|---|
| `PASS` / `WARN` / `BLOCK` | `ALLOW` / `TRANSFORM` / `APPROVE` / `ESCALATE` / `DENY` |
| Confidence in design and controls | Authorization for one proposed action |

**`PASS` is not certification.** An agent may pass assurance and still have a
dangerous action denied. A `WARN` agent may still perform an eligible low-risk
read-only operation. A `BLOCK` agent must not perform write operations.

## What this repository contains

```text
.github/agents/agentshield.agent.md      Custom-agent definition
.github/skills/agentshield-html-report/  Explicit-trigger HTML report skill
.github/copilot-instructions.md          Repository guardrails
Protocols/AGENTSHIELD-PROTOCOL.md        Authoritative protocol
Templates/agentshield-assessment-report.md  Assessment report template
docs/agentshield-flow.html               Self-contained visual workflow
agentshield/                             Working assessment/governance engine
tests/                                   Synthetic, mock-backed test suite
```

## Operating modes

1. **ASSESS** &mdash; evidence-based assurance posture; no target execution.
2. **OBSERVE** &mdash; predict impact and show the decision that would occur.
3. **GOVERN** &mdash; enforce deterministic policy and route approval; no
   execution by AgentShield.
4. **CONTROLLED LIVE** &mdash; future production mode, **disabled by default** and
   unavailable without a genuine, approved, least-privileged adapter.

## Seven gates

0. Assurance audit &rarr; 1. Action interception &rarr; 2. Identity & assurance
context &rarr; 3. Operational impact &rarr; 4. Deterministic policy &rarr;
5. Human approval &rarr; 6. Constrained safe plan &rarr; 7. Outcome validation.

See `docs/agentshield-flow.html` for the visual workflow and
`Protocols/AGENTSHIELD-PROTOCOL.md` for authoritative behavior.

## Quick start (synthetic)

```python
from agentshield import (
    AgentShieldWorkflow, evaluate_assurance, compute_impact,
    ImpactDimension, FamilyEvaluation, EvidenceState,
)
from agentshield.assurance import CONTROL_FAMILIES

# Gate 0: assurance from synthetic evidence.
families = [
    FamilyEvaluation(fid, name, weight, 4, EvidenceState.TESTED)
    for fid, name, weight in CONTROL_FAMILIES
]
assurance = evaluate_assurance("synthetic-agent", families, findings=[])

# Gate 3: operational impact.
impact = compute_impact([
    ImpactDimension("target criticality", 1, "synthetic"),
    ImpactDimension("reversibility", 1, "synthetic"),
])

# Gates 1-4: govern a proposed action (nothing reaches a target).
from agentshield import ActionRequest, IdentityContext, Lifecycle

request = ActionRequest(
    trace_id="trace-0001", requester_id="svc-synthetic",
    requester_type="service-agent", action="read_config",
    target="synthetic-target", purpose="demo",
    environment="non-production", request_timestamp_utc="2026-01-01T00:00:00Z",
    read_only=True,
)
identity = IdentityContext(
    requester_id="svc-synthetic", known=True, requester_type="service-agent",
    lifecycle=Lifecycle.ACTIVE, owner="synthetic-owner", sponsor="synthetic-sponsor",
    platform="synthetic-platform", permitted_capabilities=["read_config"],
    assurance_age_days=1.0,
)

wf = AgentShieldWorkflow()
result = wf.govern(request, identity, assurance, impact)
print(result.assurance.posture, result.policy.decision)  # separate outputs
```

## Generating an HTML report

HTML report generation is **explicit-request only**. Ask AgentShield to
generate, create, export, save, or view a report; the
`agentshield-html-report` skill then renders existing evidence:

```bash
python .github/skills/agentshield-html-report/scripts/generate_report.py \
    report-input.json report.html
```

The report escapes all values, redacts credential-like fields, embeds CSS only,
makes no network calls, labels simulations, and states that `PASS` is not
certification.

## Running the tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The suite is fully synthetic. It contains no real credentials, hostnames, or
integrations.

## Responsible use and limitations

AgentShield AI provides security assurance and governance **support**, not
certification, legal advice, compliance approval, or a guarantee of safety. It
evaluates only supplied and accessible evidence, distinguishes design intent from
implemented and tested controls, fails closed on high-risk uncertainty, and never
lets an LLM grant authorization. Human owners remain accountable for their
systems, approvals, and production changes.

All identities, targets, hostnames, and records in this repository are fictional.
