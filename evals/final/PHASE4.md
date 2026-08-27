# AgentShield AI — Token Optimisation Phase 4 (Routing, Caching, Subagents)

Deterministic, reversible, safety-preserving. Evaluated against the SAME 12
baseline tasks. The governed `agentshield/` engine is byte-identical; every
decision is produced by the unmodified engine and asserted equal to baseline.
No new dependency.

## What Phase 4 optimises

Token redundancy was already removed in Phases 2–3. Phase 4 targets **cost,
latency, and safety**, not primarily tokens — so the token total is unchanged
from Phase 3 (162,833; −33.4% vs baseline), while relative compute cost drops.

| Metric                          | Value                     |
| ------------------------------- | ------------------------- |
| Relative cost reduction         | **−53.6%** (196 → 91 units)|
| Economy-tier tasks              | 5 / 12 (all read-only ALLOW)|
| Cache hits (repeated-call demo) | 4 (hit rate 0.8)          |
| Cache-hit consistency           | true (hit == fresh compute)|
| Subagent isolation, no bleed    | true                      |
| Routing never downgrades risk   | true                      |

Cost units are a **labelled relative model** (premium = 4× economy), not real
prices.

## Techniques

1. **Model routing** (`ModelRouter`) — input-signal tiering computed BEFORE the
   engine runs. Economy is permitted only for read-only, non-production,
   non-security, impact ≤ 40 (on the 0–100 scale; high-impact tasks score 88).
   Everything else — and anything uncertain — routes premium (fail-safe). The
   router selects a REASONING model; the authorization decision still comes from
   the deterministic engine, so routing cannot weaken safety. Tasks 01, 03, 06,
   11, 12 route economy; all are read-only ALLOW.

2. **Safe caching** (`SafeCache` + `canonical_key`) — a hit is returned only when
   the FULL canonical input matches, and the key **includes `policy_version`** so
   any policy change misses. The engine is deterministic, so a matching key
   guarantees an identical decision; the harness verifies every hit equals a
   fresh computation. Demonstrated on the repeated-call task (4 hits, all
   consistent).

3. **Subagent isolation** (`IsolatedContext` / `isolate`) — each delegate gets a
   bounded, independent context with its own private store; `no_context_bleed`
   confirms no two delegates share mutable state. This is the full form of the
   task_06 shared-context win and additionally prevents cross-delegate context
   bleed (a prompt-injection containment property).

## Safety

- **Routing invariant** (`is_safe_route`): economy is valid only on a low-risk
  read-only ALLOW path; asserted for all 12 tasks (`routing_never_downgrades_risk
  = true`). Unit test proves economy is rejected on a non-ALLOW decision.
- **Cache invariant**: policy-version-scoped keys; every hit reproduces a fresh
  computation (`cache_hit_consistent = true`).
- **Isolation invariant**: `subagent_isolation_ok = true`.
- **Decisions unchanged**: 12/12 equal baseline.

## Tests

`tests/test_evals_phase45.py` covers routing tiers + safe-route rejection, cache
hit/consistency + policy-version miss, isolation no-bleed, and (with Phase 5) the
composed harness safety gate.
