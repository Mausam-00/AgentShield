AGENTSHIELD AI TOKEN OPTIMISATION RESEARCH AND DESIGN TASK
=========================================================

ROLE

Act as a senior agent architect, context-engineering specialist, and AI
efficiency researcher.

The task is to design a token-optimisation capability for the new AgentShield AI
agent being developed in this repository.

CRITICAL SCOPE BOUNDARY

Do not inspect, mention, import, reuse, migrate, or depend on any previous
AgentShield prototype, agentshield.py file, related Python modules, previous JSON
files, or other earlier implementation.

Treat the current AgentShield agent package in this repository as the only
AgentShield implementation.

Do not modify any files during the first research and design phase.

OBJECTIVE

Research proven methods for reducing the token usage, latency, loop count, and
context growth of an AI agent without weakening:

- deterministic policy;
- safety controls;
- human approval;
- audit evidence;
- security findings;
- accountability;
- decision quality;
- tool restrictions;
- fail-closed behaviour.

The goal is not simply to minimise tokens.

The goal is:

    maximise useful work, evidence quality, and safety per token.

A token-saving change must not be accepted if it causes the agent to:

- omit critical evidence;
- forget approval conditions;
- ignore policy controls;
- select the wrong tool;
- change the requested action;
- lose traceability;
- produce unsupported conclusions;
- increase operational risk.

RESEARCH SOURCES

Locate and review the following publications by exact title, identifier, or
research-project name.

PRIMARY RESEARCH

1. “ACON: Optimizing Context Compression for Long-horizon LLM Agents”
   - arXiv:2510.00615
   - ICML 2026
   - Focus: optimisation of observation and interaction-history compression for
     long-horizon agents.

2. “Prompt Compression for Large Language Models: A Survey”
   - arXiv:2410.12388
   - Focus: hard-prompt compression, soft-prompt compression, mechanisms,
     applications, limitations, and research gaps.

3. “LLMLingua: Compressing Prompts for Accelerated Inference of Large Language
   Models”
   - Focus: removing low-information tokens with a smaller language model.

4. “LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via
   Prompt Compression”
   - Focus: question-aware compression, long-context information density, and
     position of important information.

5. “LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic
   Prompt Compression”
   - Focus: learned task-agnostic compression with fidelity preservation.

6. “TACO-RL: Task Aware Prompt Compression Optimization with Reinforcement
   Learning”
   - Focus: optimisation of compression against downstream task performance
     rather than token reduction alone.

7. “TeaRAG: A Token-Efficient Agentic Retrieval-Augmented Generation Framework”
   - arXiv:2511.05385
   - Focus: compression of retrieved knowledge and reasoning steps in agentic
     RAG.

8. “Dynamic Model Routing and Cascading for Efficient LLM Inference: A Survey”
   - arXiv:2603.04445
   - Focus: selecting models by query difficulty, uncertainty, preferences,
     clustering, reinforcement learning, and cascading.

9. “Memento: Teaching LLMs to Manage Their Own Context”
   - Focus: model-managed context compaction and mid-generation reasoning
     compression.

10. “AgentOpt v0.1 Technical Report: Client-Side Optimization for LLM-Based
    Agent”
    - Focus: client-side efficiency when agents combine tools, APIs, local
      operations, and different models.

11. “Toward Reliable Context Compression for Long-Horizon Agents: An Empirical
    Study of Execution Instability”
    - arXiv:2608.06503
    - Focus: reliability risks introduced by recurrent context compression,
      repeated exploration, blocked actions, and execution instability.

12. “Maximizing RAG Efficiency: A Comparative Analysis of RAG Methods”
    - Focus: retrieval methods, contextual compression, token consumption,
      runtime, embeddings, and similarity trade-offs.

13. Microsoft Research project:
    “Efficient AI Applications: Context Engineering and Agents”
    - Focus: structured and unstructured context pruning, hybrid retrieval,
      memory, intelligent compression, and quality-per-cost.

14. Microsoft Research:
    “Tool-space interference in the MCP era: Designing for agent compatibility
    at scale”
    - Focus: tool proliferation, overlapping tools, large tool responses, tool
      selection, and context impact.

15. Microsoft Research:
    “Terminus-4B: Can a Smaller Model Replace Frontier LLMs at Agentic Execution
    Tasks?”
    - Focus: specialised smaller models and context isolation for bounded
      agentic execution tasks.

OPTIONAL SUPPORTING SOURCES

Also search for credible publications covering:

- context engineering;
- prompt caching;
- semantic caching;
- exact-response caching;
- tool-result caching;
- dynamic few-shot selection;
- retrieval reranking;
- retrieval deduplication;
- graph-based retrieval;
- agent-managed memory;
- structured state;
- hierarchical memory;
- sliding-window memory;
- subagent context isolation;
- model routing;
- constrained reasoning;
- early-exit policies;
- tool-call budgets;
- loop and retry limits;
- speculative execution;
- quantisation;
- distillation;
- sparse attention;
- KV-cache optimisation.

SOURCE QUALITY RULES

Prefer sources in this order:

1. Peer-reviewed conference or journal paper.
2. Authoritative research organisation publication.
3. Official project or technical report.
4. Official implementation repository.
5. Reputable engineering documentation.

Do not use an unsourced blog claim as proof.

For every paper or source record:

- exact title;
- authors;
- publication venue;
- publication year;
- DOI or arXiv identifier, when available;
- source location;
- optimisation method;
- reported evaluation setting;
- reported token, latency, memory, or cost result;
- reported quality result;
- limitations;
- relevance to AgentShield;
- implementation maturity.

Do not invent performance numbers.

If a source does not report a number, write:

    Not quantified in the reviewed source.

If a source is a preprint, label it:

    Preprint, not treated as peer-reviewed evidence.

If a claimed result applies only to a specific benchmark or model, state the
scope explicitly. Do not represent benchmark results as universal guarantees.

RESEARCH QUESTIONS

Answer the following questions.

1. Which parts of an agent consume the most input tokens?

2. Which parts cause repeated token growth across turns?

3. Which techniques reduce:
   - system-prompt tokens;
   - tool-definition tokens;
   - retrieved-context tokens;
   - conversation-history tokens;
   - tool-output tokens;
   - reasoning-output tokens;
   - repeated agent-loop tokens?

4. Which methods are:
   - deterministic;
   - model-assisted;
   - model-trained;
   - retrieval-based;
   - architecture-based;
   - provider-specific?

5. Which methods can be implemented without training a model?

6. Which methods preserve auditability and exact policy language?

7. Which compression methods risk losing:
   - negative evidence;
   - exact thresholds;
   - resource identifiers;
   - approval conditions;
   - policy versions;
   - safety exceptions;
   - rollback requirements?

8. How should compression quality be verified?

9. When should an agent use:
   - a small model;
   - a medium model;
   - a frontier reasoning model?

10. How should tool descriptions and tool results be made token-efficient?

11. How should the agent stop runaway loops, repeated exploration, and duplicate
    tool calls?

12. Which context should remain immutable and never be summarised?

13. What should be externalised into retrievable memory?

14. How should token optimisation interact with:
    - assurance posture;
    - runtime policy;
    - approval;
    - evidence;
    - report generation?

TOKEN-CONSUMPTION MODEL

Create an AgentShield token-consumption model covering:

    total tokens
      = system instructions
      + agent profile
      + protocol controls
      + skills
      + tool definitions
      + retrieved evidence
      + conversation history
      + tool results
      + subagent messages
      + reasoning output
      + final response

For each category, specify:

- whether the category is static or dynamic;
- whether the category is cacheable;
- whether the category is compressible;
- whether the category may contain immutable evidence;
- whether the category should be loaded just in time;
- likely quality or safety risk from compression;
- proposed token budget.

Do not assign arbitrary production token limits without evidence.

Where evidence is unavailable, initially define the value as:

    Configurable; determine through baseline measurement.

REQUIRED OPTIMISATION CONTROLS

Evaluate the following controls.

CONTROL 1: Minimal always-on instructions

Keep only non-negotiable controls in the always-loaded agent profile.

Move detailed explanation, tutorials, examples, and reference material into
retrievable protocol or skill documents.

The following must remain explicit and always available:

- deterministic policy owns authorisation;
- the agent may never silently substitute an action;
- rejection means zero execution;
- unsupported evidence must not be invented;
- high-risk failures must fail closed;
- every decision requires traceable evidence.

CONTROL 2: Progressive tool disclosure

Create three levels of tool information:

Level 1:
- tool name;
- one-line purpose;
- risk class.

Level 2:
- relevant parameters;
- response shape;
- permission requirements.

Level 3:
- complete schema;
- examples;
- limitations;
- failure handling.

Load Level 2 or Level 3 only when the current task requires the tool.

CONTROL 3: Gate-specific tool loading

Load only the tools required by the current AgentShield phase:

- assurance audit;
- identity;
- impact analysis;
- policy;
- approval;
- execution;
- outcome validation;
- reporting.

Write-capable execution tools must not be exposed before authorisation and
approval.

CONTROL 4: Structured state

Use a compact structured state instead of replaying the entire conversation.

The state should preserve:

- trace ID;
- user objective;
- current phase;
- requester identity;
- requested action;
- target;
- immutable constraints;
- assurance posture;
- operational risk;
- policy version;
- runtime decision;
- approval status;
- evidence identifiers;
- completed steps;
- open questions;
- stop reason;
- expected and observed outcome.

CONTROL 5: Context compaction

When history exceeds a measured threshold:

- retain recent relevant turns;
- summarise older turns;
- retain exact immutable state separately;
- retain evidence pointers;
- validate the summary;
- log each compaction event;
- allow recovery from source evidence.

Never summarise away exact approvals, policy controls, resource identifiers,
security exceptions, or denial reasons.

CONTROL 6: Retrieval optimisation

Use:

- metadata filtering;
- semantic retrieval;
- reranking;
- deduplication;
- contextual compression;
- source identifiers;
- evidence coverage notes;
- bounded top-k retrieval.

Do not retrieve the complete protocol, registry, or audit history for every
request.

CONTROL 7: Dynamic few-shot selection

Store examples outside the always-on prompt.

Retrieve only one or two examples relevant to the current task.

Prefer examples targeting known failures.

Do not inject examples when evaluation shows the model performs adequately
without them.

CONTROL 8: Subagent context isolation

Use specialised subagents only for bounded work.

Each specialist should receive:

- one objective;
- a small evidence set;
- an allowed-tool list;
- an output schema;
- a token budget;
- a tool-call budget;
- a stop condition.

Return only a structured summary to the main orchestrator.

CONTROL 9: Model routing

Design deterministic or evaluated routing for:

Small model:
- classification;
- extraction;
- schema validation;
- deduplication;
- simple summarisation;
- output formatting.

Mid-tier model:
- bounded evidence synthesis;
- moderate planning;
- retrieval query rewriting;
- remediation drafting.

Frontier reasoning model:
- novel high-risk actions;
- conflicting policy evidence;
- ambiguous cross-system dependencies;
- complex security analysis.

Model routing may optimise analysis cost but must not replace deterministic
policy.

CONTROL 10: Agent-loop budgets

Define configurable budgets for:

- maximum turns;
- maximum tool calls;
- retries per tool;
- repeated identical calls;
- repeated actions;
- subagent count;
- retrieved-context size;
- output length;
- wall-clock timeout.

Stop immediately when:

- policy returns DENY;
- approval is rejected;
- the required decision is complete;
- validation fails;
- the same action repeats unexpectedly;
- the tool-call budget is exhausted;
- the evidence is insufficient for a safe write operation.

CONTROL 11: Caching

Evaluate:

- stable-prefix prompt caching;
- exact-response caching;
- semantic caching;
- retrieval caching;
- read-only tool-result caching.

Cache keys must consider:

- tenant;
- requester;
- identity;
- policy version;
- target;
- environment;
- permissions;
- data sensitivity;
- expiry.

Do not cache human approvals, rapidly changing infrastructure state, security
decisions, or sensitive outputs without explicit identity-bound controls.

CONTROL 12: Compact answer contract

Default output should contain:

- decision;
- risk;
- critical reason codes;
- required next action;
- trace ID.

Detailed evidence should be available through explicit modes such as:

- explain;
- audit;
- report.

Do not repeatedly print the full audit record in every response.

AGENTSHIELD TOKEN GOVERNANCE LAYER

Design an optional Token Governance capability that evaluates an agent run before
and during execution.

It should record:

- estimated input-token budget;
- actual input tokens;
- cached tokens;
- output tokens;
- tool-definition tokens;
- retrieved-context tokens;
- history tokens;
- tool-output tokens;
- turn count;
- tool-call count;
- repeated-call count;
- subagent token usage;
- compression events;
- routing decisions;
- cost, when available;
- latency, when available;
- final success or failure;
- safety and quality evaluation result.

The Token Governance capability may:

- warn;
- reduce retrieval breadth;
- load fewer tool descriptions;
- compact history;
- route bounded work to a smaller model;
- stop repeated exploration;
- require a fresh session;
- recommend an updated budget.

It must not:

- remove immutable safety controls;
- weaken policy;
- omit critical findings;
- bypass approval;
- suppress audit evidence;
- automatically change production policy;
- change the requested operation.

EVALUATION DESIGN

Create a baseline evaluation suite before changing behaviour.

Include representative tasks:

1. Read-only agent assessment.
2. High-risk runtime action.
3. Long multi-turn investigation.
4. Tool-heavy workflow.
5. Retrieval-heavy policy question.
6. Multi-agent delegation.
7. Human-approval workflow.
8. HTML report request.
9. Missing-evidence scenario.
10. Prompt-injection attempt.
11. Repeated-tool-call scenario.
12. Context-compaction scenario.

Measure:

- input tokens;
- output tokens;
- cached tokens;
- total tokens;
- tokens per successful task;
- turns per task;
- tool calls per task;
- repeated calls;
- latency;
- task success;
- decision agreement with baseline;
- critical-fact retention;
- evidence precision;
- policy-control retention;
- unsafe-action rate;
- approval-bypass rate;
- report completeness.

ACCEPTANCE CRITERIA

A candidate optimisation is acceptable only if:

- required security controls remain present;
- deterministic decisions match the approved baseline;
- critical evidence retention passes;
- approval behaviour is unchanged;
- unsafe-action rate does not increase;
- audit evidence remains complete;
- task success remains within the approved quality threshold;
- token usage or latency materially improves.

Do not invent threshold values.

Propose candidate thresholds based on baseline results and mark them for human
approval.

REQUIRED DELIVERABLES

For the initial phase, create no implementation changes.

Produce:

1. Research catalogue.
2. Evidence matrix covering every named paper.
3. Token-consumption model.
4. Current repository context map.
5. Proposed optimisation architecture.
6. Immutable-context definition.
7. Compressible-context definition.
8. Gate-specific tool-loading design.
9. Structured-state schema.
10. Compaction and validation design.
11. Retrieval-optimisation design.
12. Subagent-isolation design.
13. Model-routing design.
14. Caching design.
15. Agent-loop budget design.
16. Token Governance capability design.
17. Evaluation plan.
18. Risks and failure modes.
19. Recommended implementation phases.
20. Exact proposed files to create or modify.
21. Exact next action.

RESEARCH DOCUMENT

Create a proposed outline for:

    docs/research/agent-token-optimisation.md

The document should contain:

- executive summary;
- problem statement;
- research methodology;
- source-quality tiers;
- paper catalogue;
- technique taxonomy;
- evidence matrix;
- applicability to AgentShield;
- design recommendations;
- safety constraints;
- evaluation plan;
- open questions;
- bibliography.

Do not create the file during the research phase.

WORKING PROCESS

PHASE 0: RESEARCH AND BASELINE PLAN

- Inspect the current repository.
- Locate the new AgentShield agent definition, protocols, skills, tools, tests,
  and evaluation assets.
- Do not inspect or reference any previous AgentShield prototype.
- Research the named publications.
- Do not modify files.
- Do not install packages.
- Do not change prompts.
- Do not change tools.
- Do not optimise anything yet.

Return the 21 deliverables listed above.

Stop for human review.

PHASE 1: BASELINE MEASUREMENT

Only after approval:

- add instrumentation;
- establish current token usage;
- run the approved evaluation suite;
- record quality and security results;
- establish baseline artefacts.

Do not optimise yet.

PHASE 2: LOW-RISK OPTIMISATIONS

Only after baseline approval:

- remove duplicated instructions;
- add compact output contracts;
- add scoped retrieval;
- add gate-specific tool loading;
- add deterministic loop limits;
- preserve behaviour and safety.

PHASE 3: CONTEXT AND MEMORY

Only after Phase 2 evaluation:

- add structured state;
- add compaction;
- add summary validation;
- add evidence pointers;
- test critical-fact retention and execution stability.

PHASE 4: ROUTING, CACHING, AND SUBAGENTS

Only after Phase 3 evaluation:

- add model routing;
- add safe caching;
- add subagent isolation;
- evaluate quality, cost, latency, and safety.

PHASE 5: TOKEN GOVERNANCE

- integrate budgets and telemetry;
- add warnings and deterministic stop controls;
- generate efficiency evidence;
- document rollback;
- preserve human approval for policy changes.

IMPORTANT RULES

- Research before implementation.
- Measure before optimisation.
- Optimise successful-task cost, not tokens in isolation.
- Do not trust reported results outside their evaluation scope.
- Do not invent metrics or citations.
- Do not silently remove controls.
- Do not modify authorisation behaviour.
- Do not add a new dependency without explaining its security, licensing, and
  maintenance impact.
- Prefer transparent, auditable methods.
- Any learned compressor must have a deterministic fallback.
- Every change must be reversible.
- Every optimisation must be evaluated against the same baseline tasks.

START NOW

Perform Phase 0 only.

Research the publications, inspect the current repository, and return the 21
deliverables.

Do not create, edit, delete, install, optimise, or execute anything yet.

Wait for my approval before Phase 1.