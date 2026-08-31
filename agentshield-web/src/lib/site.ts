export type NavChild = { label: string; href: string; desc: string };
export type NavItem = { label: string; href: string; external?: boolean; children?: NavChild[] };

export const site = {
  name: "AgentShield AI",
  tagline: "The deterministic security control plane for AI agents",
  email: "hello@agentshield.example",
  location: "Remote-first",
  repo: "https://github.com/Mausam-00/AgentShield",
};

export const nav: NavItem[] = [
  { label: "Home", href: "/" },
  { label: "Platform", href: "/products" },
  { label: "Dashboard", href: "/#dashboard" },
  { label: "Github Repo", href: site.repo, external: true },
  { label: "Contact", href: "/contact" },
];

/* Honest, project-true headline stats (no invented figures). */
export const heroStats = [
  { value: 7, suffix: "", label: "Governance gates" },
  { value: 21, suffix: "", label: "Deterministic controls" },
  { value: 12, suffix: "/12", label: "Decisions preserved" },
  { value: 0, suffix: "", label: "Unsafe actions" },
];

/* Measured results from the token-optimization programme (12-task workload). */
export const bandStats = [
  { value: 33.4, suffix: "%", label: "Fewer context tokens", decimals: 1 },
  { value: 53.6, suffix: "%", label: "Lower relative cost", decimals: 1 },
  { value: 12, suffix: "", label: "Decisions preserved (of 12)" },
  { value: 0, suffix: "", label: "Approval bypasses" },
];

export const features = [
  {
    icon: "Target",
    title: "BlastRadius — capability & impact mapping",
    body: "Identifies exactly what an agent can do — its tools, permissions and trust boundaries — and predicts how far any action would reach before it runs.",
  },
  {
    icon: "ShieldAlert",
    title: "ChangeShield — safe-change enforcement",
    body: "Governs the changes an agent may make: deterministic policy, meaning-preserving invariants and constrained, reversible plans so no unsafe change reaches a target.",
  },
  {
    icon: "ShieldCheck",
    title: "Deterministic policy engine",
    body: "Versioned controls return exactly one verdict with reason codes. No model can weaken a hard control.",
  },
  {
    icon: "GitBranch",
    title: "Semantic safety invariants",
    body: "add_disk never becomes remove_disk. Meaning is preserved before any action reaches a target.",
  },
  {
    icon: "Radar",
    title: "Adversarial red-team",
    body: "Static, simulation-only probing across nine attack families with an at-a-glance ASR score.",
  },
  {
    icon: "Scale",
    title: "Responsible AI assessment",
    body: "Advisory posture across six pillars that fails closed on missing fairness or safety evidence.",
  },
  {
    icon: "Lock",
    title: "Approval binding",
    body: "Approvals bind requester, action, target, plan hash, policy version and expiry. Expired means zero steps.",
  },
  {
    icon: "ScrollText",
    title: "Evidence & audit trail",
    body: "Every outcome — allow, deny, timeout, failure — is recorded with hashes, coverage and confidence.",
  },
];

/* Unique selling points — each expands via "click for more info". */
export const usps = [
  {
    icon: "Lock",
    title: "Deterministic, never probabilistic",
    summary: "Authorization comes only from versioned policy — an LLM can advise, but never grant access.",
    detail:
      "A model may extract facts, describe uncertainty and recommend constraints. It can never weaken a hard control or authorize an action. Every decision is produced by deterministic, versioned policy, so it is reproducible and reviewable.",
  },
  {
    icon: "GitBranch",
    title: "Judgement is separate from authority",
    summary: "Advisory posture (PASS/WARN/BLOCK) is kept strictly apart from the authorization verdict.",
    detail:
      "An assurance PASS is never a certification, and a WARN never blocks on its own. Authorization is a separate decision: ALLOW, TRANSFORM, APPROVE, ESCALATE or DENY — with DENY outranking every other verdict.",
  },
  {
    icon: "Radar",
    title: "Fails closed by design",
    summary: "Unknown identity, unavailable policy, invalid approval or high-risk missing evidence all deny.",
    detail:
      "Safety is the default rather than an afterthought. When any precondition is unmet, the control plane denies or escalates instead of guessing — and records the reason.",
  },
  {
    icon: "ScrollText",
    title: "Provable, auditable evidence",
    summary: "Every outcome — including denials and failures — is recorded with coverage and confidence.",
    detail:
      "Instead of asserting safety, AgentShield proves it. Each decision leaves an immutable, hashed evidence record you can export for auditors and incident review.",
  },
  {
    icon: "Gauge",
    title: "Efficient without compromise",
    summary: "A non-invasive optimization layer cut tokens 33.4% and relative cost 53.6% — with zero safety change.",
    detail:
      "The optimization work lives entirely outside the governed engine. Every optimized decision is produced by the unmodified engine and asserted equal to the recorded baseline, so efficiency never trades against safety.",
  },
  {
    icon: "Workflow",
    title: "Fully reversible",
    summary: "Every layer is componentized and can be disabled to restore prior behaviour exactly.",
    detail:
      "Nothing is a one-way door. Disable any optimization layer and authorization is byte-identical to before — measured, not assumed.",
  },
];

/* Business value — benefit cards with expand-for-more. */
export const businessValue = [
  {
    icon: "Coins",
    metric: "−53.6%",
    title: "Lower operating cost",
    summary: "Roughly half the relative compute cost per governed request.",
    detail:
      "Redundant context, broad tool surfaces and repeated reloads are removed so each governed action carries less payload — compounding across every agent action at scale.",
  },
  {
    icon: "TrendingDown",
    metric: "−33.4%",
    title: "Leaner context footprint",
    summary: "A third fewer tokens across the 12-task governance workload.",
    detail:
      "Scoped retrieval, gate-specific tools, history compaction and evidence pointers shrink the context that would go to a model — without dropping a single critical fact (retention held at 1.0).",
  },
  {
    icon: "ShieldCheck",
    metric: "100%",
    title: "Audit-ready governance",
    summary: "Every decision is recorded and versioned for compliance review.",
    detail:
      "A complete, hashed evidence trail turns 'trust us' into 'here is the record' — accelerating audits and shortening incident investigations.",
  },
  {
    icon: "Scale",
    metric: "0",
    title: "No safety trade-off",
    summary: "Decisions, unsafe-action count and approval bypasses all unchanged.",
    detail:
      "Optimization never feeds different inputs to the engine. Decision agreement stayed 12/12, unsafe actions and approval bypasses stayed at zero, and the engine itself was never modified.",
  },
];

export const gates = [
  { id: "G0", name: "Assurance audit", body: "Design-time posture: PASS, WARN or BLOCK." },
  { id: "G1", name: "Action interception", body: "Hold the proposed action before execution." },
  { id: "G2", name: "Identity & context", body: "Resolve who is acting and under what trust." },
  { id: "G3", name: "Operational impact", body: "BlastRadius: predict capability reach, blast radius and reversibility." },
  { id: "G4", name: "Deterministic policy", body: "ChangeShield: the only gate that authorizes. Fails closed." },
  { id: "G5", name: "Human approval", body: "Bounded approval bound to hash and expiry." },
  { id: "G6", name: "Constrained plan", body: "ChangeShield: scope narrowing, checkpoints and rollback." },
  { id: "G7", name: "Outcome validation", body: "Verify results and preserve evidence." },
];

/* Interactive dashboard data — real, measured, honestly disclosed. */
export const dashboard = {
  metrics: [
    {
      label: "Context tokens",
      before: 244476,
      after: 162833,
      unit: "",
      change: "−33.4%",
      detail:
        "Sum of context + payload that would be sent to a model across all 12 governance tasks, approximated as characters ÷ 4.",
    },
    {
      label: "Relative compute cost",
      before: 196,
      after: 91,
      unit: " units",
      change: "−53.6%",
      detail:
        "A labelled relative cost model (premium model = 4× economy). Routing keeps high-impact work on the premium tier and moves low-impact reads to economy.",
    },
  ],
  preserved: [
    { label: "Decision agreement", value: "12 / 12" },
    { label: "Unsafe actions / bypasses", value: "0 / 0" },
    { label: "Critical-fact retention", value: "1.0" },
    { label: "Engine changes", value: "0 · byte-identical" },
  ],
  savings: [
    {
      title: "Gate-specific tool loading",
      tag: "floor cut",
      detail:
        "Each gate loads only the tools it uses instead of the full ~1,976-token tool surface on every task.",
    },
    {
      title: "Loop limits + shared context",
      tag: "task_06 −77.6%",
      detail:
        "Delegated sub-tasks reuse context instead of full reloads, and repeated identical calls collapse to cache hits.",
    },
    {
      title: "Scoped retrieval",
      tag: "task_05 −31.2%",
      detail:
        "Retrieve the top-k relevant protocol sections rather than the entire protocol document.",
    },
    {
      title: "Compaction + evidence pointers",
      tag: "task_12 −38.1% · task_03 −21.8%",
      detail:
        "Validated history summaries replace bulky inline history; large audit records move to a retrievable store referenced by pointer.",
    },
  ],
  disclaimer:
    "Tokens approximated as chars/4 (not provider-exact); cost is a labelled relative model. Deduplication found 0 duplicate blocks — no savings claimed there.",
};

/* Synthetic, simulation-only scenarios for the live demo. No real engine call. */
export const demoScenarios = [
  {
    id: "read-low",
    label: "Read service config",
    request: "agent.read('service-config')",
    identity: "svc-analyst · verified",
    assurance: "PASS",
    impact: "Low · read-only · reversible",
    decision: "ALLOW",
    control: "ASP-001",
    rationale:
      "Verified identity performing a low-impact, reversible read. Policy permits with no added constraints.",
    evidence: { coverage: "full", confidence: "high", missing: "none" },
  },
  {
    id: "bulk-transform",
    label: "Bulk delete records",
    request: "agent.delete('records/*')",
    identity: "svc-automation · verified",
    assurance: "WARN",
    impact: "Medium · write · partially reversible",
    decision: "TRANSFORM",
    control: "ASP-007",
    rationale:
      "Unbounded delete is narrowed to a scoped, checkpointed batch with rollback before it can reach the target.",
    evidence: { coverage: "partial", confidence: "medium", missing: "none" },
  },
  {
    id: "prod-write-approve",
    label: "Production config change",
    request: "agent.write('prod/gateway-config')",
    identity: "svc-deployer · verified",
    assurance: "PASS",
    impact: "High · write · reversible with plan",
    decision: "APPROVE",
    control: "ASP-016",
    rationale:
      "High-impact production write with adequate assurance requires a bounded human approval bound to plan hash and expiry.",
    evidence: { coverage: "full", confidence: "high", missing: "none" },
  },
  {
    id: "high-missing-evidence",
    label: "High-impact write, evidence gap",
    request: "agent.write('billing/ledger')",
    identity: "svc-automation · verified",
    assurance: "PASS",
    impact: "High · write · hard to reverse",
    decision: "ESCALATE",
    control: "ASP-012",
    rationale:
      "Assurance posture is PASS, but a high-risk evidence requirement is missing — so the action escalates for human judgement rather than proceeding.",
    evidence: { coverage: "partial", confidence: "medium", missing: "high-risk safety evidence" },
  },
  {
    id: "low-assurance-deny",
    label: "Low-assurance production write",
    request: "agent.write('prod/payments')",
    identity: "svc-automation · verified",
    assurance: "BLOCK",
    impact: "High · production write",
    decision: "DENY",
    control: "ASP-003",
    rationale:
      "Low coverage drives a BLOCK posture. DENY outranks APPROVE by decision precedence, so the action is refused and recorded.",
    evidence: { coverage: "low", confidence: "low", missing: "coverage threshold" },
  },
  {
    id: "unknown-identity",
    label: "Unknown identity",
    request: "agent.read('service-config')",
    identity: "unresolved",
    assurance: "WARN",
    impact: "Unknown",
    decision: "DENY",
    control: "ASP-000",
    rationale:
      "Identity cannot be resolved. The control plane fails closed on unknown identities and records the denial.",
    evidence: { coverage: "none", confidence: "n/a", missing: "verified identity" },
  },
];

export const services = [
  {
    icon: "ShieldCheck",
    title: "Agent Governance",
    body: "Deploy the seven-gate control plane in front of any agent, orchestrator or MCP tool.",
    points: ["Pre-execution interception", "Versioned deterministic policy", "Fail-closed defaults"],
    more: "The control plane sits inline: every proposed action passes through identity, policy, impact, approval and evidence gates before a single tool call executes. The model can advise, but only deterministic, versioned policy returns the verdict.",
  },
  {
    icon: "Radar",
    title: "Adversarial Assurance",
    body: "Continuous red-team probing that quantifies attack success rate before agents ship.",
    points: ["Nine attack families", "Refusal & leakage metrics", "Injection resistance"],
    more: "Simulation-only probes across nine attack families produce an attack-success-rate signal with refusal and leakage metrics, so you can gate a release on measured resistance rather than a subjective review.",
  },
  {
    icon: "Scale",
    title: "Responsible AI",
    body: "Repeatable RAI posture aligned to public standards across six weighted pillars.",
    points: ["Fairness & safety evidence", "Transparency scoring", "Accountability trail"],
    more: "Six weighted pillars — fairness, safety, transparency, accountability, privacy and reliability — are scored with a fail-closed posture, so missing evidence lowers the score instead of being silently assumed.",
  },
  {
    icon: "Workflow",
    title: "Safe Plan Engineering",
    body: "Constrained plans with batching, checkpoints, rollback and explicit stop conditions.",
    points: ["Scope narrowing", "Human-in-the-loop", "Rollback by design"],
    more: "High-impact work is decomposed into batched, checkpointed steps with explicit rollback and stop conditions, so an agent narrows its own blast radius before it ever reaches a live target.",
  },
  {
    icon: "Activity",
    title: "Monitoring & Evidence",
    body: "Immutable, hashed audit records for every decision — including denials and failures.",
    points: ["Coverage & confidence", "Immutable hashes", "Exportable reports"],
    more: "Every decision — allow, transform, approve, escalate or deny — is written to a hashed, immutable record with coverage and confidence indices, and missing evidence is preserved as a coverage limitation rather than invented.",
  },
  {
    icon: "Cpu",
    title: "Integration & Enablement",
    body: "Reference architectures and enablement to embed AgentShield across your stack.",
    points: ["MCP / A2A ready", "Reference blueprints", "Team enablement"],
    more: "Reference blueprints for MCP and agent-to-agent topologies, plus enablement so your own teams can own, extend and audit the control plane rather than depend on a black box.",
  },
];

export const solutions = [
  {
    sector: "Financial Services",
    title: "Govern autonomous trading & ops agents",
    body: "Bind every high-impact action to policy and approval, with a full evidence trail for auditors.",
    metric: "DENY",
    metricLabel: "outranks every verdict",
    more: "Wherever an agent can move money or change a position, the impact gate predicts blast radius and the approval gate binds the action to a valid, versioned authorization — and because DENY outranks every other verdict, a single failing control blocks execution.",
  },
  {
    sector: "Healthcare",
    title: "Safe clinical & back-office automation",
    body: "Semantic invariants keep automation inside its lane; fail-closed on missing safety evidence.",
    metric: "6",
    metricLabel: "RAI pillars enforced",
    more: "Semantic invariants constrain what an agent may touch, and the Responsible AI gate scores six pillars with a fail-closed posture — missing safety evidence lowers the score and can block the action instead of being assumed away.",
  },
  {
    sector: "Critical Infrastructure",
    title: "Guardrails for operational technology",
    body: "Predict blast radius and require constrained plans before any change reaches a live target.",
    metric: "G3",
    metricLabel: "impact gate pre-check",
    more: "The impact gate (G3) estimates blast radius before execution and demands a constrained, checkpointed plan with rollback and stop conditions, so no change reaches a live operational target without a reversible path back.",
  },
  {
    sector: "Technology & SaaS",
    title: "Ship agentic features with confidence",
    body: "Red-team every release and gate rollout on a measurable attack success rate.",
    metric: "9",
    metricLabel: "attack families probed",
    more: "Simulation-only adversarial probing across nine attack families produces a measurable attack-success-rate signal, so a rollout can be gated on demonstrated resistance rather than a subjective sign-off.",
  },
];

export const products = [
  {
    name: "Control Plane",
    tier: "Core",
    body: "The seven-gate runtime that intercepts, evaluates and authorizes agent actions.",
    features: ["Deterministic policy", "Approval binding", "Fail-closed runtime"],
    accent: "blue",
    more: "The core runtime intercepts every proposed action and runs it through the seven gates. Authorization comes only from deterministic, versioned policy — the model advises but never grants access or weakens a hard control.",
  },
  {
    name: "Red-Team Engine",
    tier: "Assurance",
    body: "Simulation-only adversarial probing that produces an at-a-glance ASR dashboard.",
    features: ["Nine families", "Probe matrix", "Refusal / leakage"],
    accent: "magenta",
    more: "A simulation-only probe matrix exercises nine attack families and reports attack success rate alongside refusal and leakage metrics — assurance evidence, kept strictly separate from the runtime authorization path.",
  },
  {
    name: "Responsible AI",
    tier: "Assurance",
    body: "Six-pillar RAI scoring with fail-closed posture and exportable evidence.",
    features: ["Fairness & safety", "Transparency", "Accountability"],
    accent: "violet",
    more: "Scores six weighted RAI pillars with a fail-closed posture: missing evidence is preserved as a coverage limitation and lowers the score, rather than being silently treated as a pass.",
  },
  {
    name: "Evidence Vault",
    tier: "Platform",
    body: "Immutable, hashed record of every decision with coverage and confidence.",
    features: ["Hashed outcomes", "Coverage index", "One-click export"],
    accent: "teal",
    more: "Every outcome — including denials and failures — is written to a hashed, immutable record with coverage and confidence indices, and reports are generated only on explicit request with credential-like fields redacted.",
  },
];

export const values = [
  { title: "Fail closed", body: "When in doubt, deny. Safety is the default, never an afterthought.", more: "Unknown identities, unavailable policy, invalid approvals and high-risk missing evidence all resolve to denial. The safe state is reached by default, not by remembering to add a check." },
  { title: "Evidence over claims", body: "Every outcome is recorded. We prove, we do not assert.", more: "Each decision produces a hashed, immutable record. Where evidence is absent we preserve it as a coverage limitation instead of inventing it — the absence itself is part of the audit trail." },
  { title: "Judgement ≠ authority", body: "AI advises; deterministic policy decides. Always.", more: "A model's recommendation is never treated as permission. Authorization comes only from deterministic, versioned controls, so no prompt or output can grant access or weaken a hard control." },
  { title: "Humans accountable", body: "The control plane augments people; it never replaces accountability.", more: "High-impact actions bind to explicit human approval, and every escalation routes to a person. The system makes accountability enforceable — it does not absorb it." },
];
