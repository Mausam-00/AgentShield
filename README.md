# AgentShield AI

<img src="docs/Thumbnail.jpg" alt="AgentShield AI logo" width="1000">

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

## How it fits together

AgentShield is organised into two strictly separated lanes plus the surfaces
that drive them:

- **Deterministic core (`agentshield/`)** &mdash; the offline, network-free
  assessment and governance engine. It never makes outbound calls, so its verdicts
  are reproducible and safe to run anywhere. This is what authorizes or denies an
  action.
- **Live measurement lane (`agentshield_live/`)** &mdash; opt-in adapters that
  gather *real* signals (red-team probes, content-safety checks, fairness/RAI
  measurements). All networking lives here and never leaks into the core.
- **Surfaces** &mdash; a Copilot **custom agent** (`.github/agents/`), a report
  **pipeline** (`scripts/`), and a **Next.js website** (`agentshield-web/`)
  deployed to Azure Container Apps.

<img src="docs/agentshield-architecture.png" alt="AgentShield architecture" width="900">

## Repository structure

```text
AgentShield/
├── agentshield/                  Deterministic assessment & governance engine (offline, no network)
│   ├── workflow.py               Orchestrates the seven gates end to end
│   ├── assurance.py              Gate 0 — control-family scoring → PASS / WARN / BLOCK
│   ├── interception.py           Gate 1 — capture & hold a proposed action
│   ├── impact.py                 Gate 3 — operational-impact scoring
│   ├── policy.py                 Gate 4 — deterministic ALLOW/TRANSFORM/APPROVE/ESCALATE/DENY
│   ├── approvals.py              Gate 5 — approval binding (requester, action, plan hash, expiry)
│   ├── planning.py               Gate 6 — constrained safe plan with stop conditions
│   ├── validation.py             Gate 7 — expected-vs-observed outcome validation
│   ├── redteam.py                Static red-team scoring (defense coverage, residual exposure)
│   ├── responsible_ai.py         Six-pillar Responsible AI posture (RAI-PASS/WARN/BLOCK)
│   ├── static_assess.py          Parse an agent definition into evidence
│   ├── remediation.py            Finding → concrete remediation suggestions
│   ├── sarif.py                  SARIF export for code-scanning dashboards
│   ├── evidence.py · ledger.py   Evidence records + tamper-evident audit ledger
│   ├── determinism.py · metrics.py · models.py · interfaces.py   Core primitives
│   ├── mock_providers.py         Synthetic providers (keeps the core testable & offline)
│   └── integrations/             Optional Entra ID / Content Safety hooks
├── agentshield_live/             Live-measurement lane (all networking is isolated here)
│   ├── redteam_live.py           Live adversarial probes
│   ├── pyrit_engine.py           PyRIT-backed attack generation
│   ├── content_safety_live.py    Azure AI Content Safety checks
│   ├── fairness.py · rai_measured.py   Measured fairness & Responsible AI metrics
│   ├── judge.py · canary.py · adapters.py   Scoring, canaries, provider adapters
│   └── data/                     Sample datasets (bring-your-own-dataset)
├── scripts/                      Report pipeline & CLI entry points
│   ├── agentshield_report.py     Full assessment → HTML evidence report
│   ├── agent_llm.py              LLM enrichment + content-addressed narrative cache
│   ├── agentshield_scan.py       Static scan of an agent definition
│   ├── agentshield_observe.py    OBSERVE mode — predicted impact + would-be decision
│   ├── agentshield_intercept.py  Action interception demo
│   ├── agentshield_governance.py GOVERN mode runner
│   ├── agentshield_showcase.py   End-to-end showcase
│   └── agentshield_banner*.py    CLI banner (ANSI + PNG)
├── enrichment_cache/             Committed LLM narratives, namespaced by prompt version
│   └── v1/                       Ensures the website and CLI render identical reports
├── agentshield-web/              Next.js website (Azure Container Apps) — upload an agent, get a report
├── deploy/                       Azure Container Apps deployment scripts (ps1 / sh / portal guide)
├── Protocols/                    Authoritative behavioural protocols (governance + Responsible AI)
├── Templates/                    Assessment & Responsible AI report templates
├── examples/                     Sample assessment inputs/outputs (dr-sha, troubleshootbuddy…)
├── evals/                        Evaluation harness & baseline/optimized result sets
├── reference-agent/             Structural/quality reference agent (audit report + flow)
├── docs/                         Architecture image, banner, generated reports, LIVE-ASSESSMENT.md
├── tests/                        Synthetic, mock-backed test suite (161 tests)
├── .github/
│   ├── agents/agentshield.agent.md          Custom Copilot agent definition
│   ├── skills/agentshield-html-report/      Explicit-trigger HTML report skill
│   ├── workflows/                           CI: deploy + enrichment-parity gate
│   └── copilot-instructions.md              Repository guardrails
├── Dockerfile · DEPLOYMENT.md    Container build + deployment guide
├── AGENTS.md                     Contributor/agent operating notes
└── AgentShield.txt               Original build brief
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

See the architecture diagram above for the visual workflow and
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
python -m pytest -q          # full synthetic suite (161 tests)
# or, standard-library only:
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
