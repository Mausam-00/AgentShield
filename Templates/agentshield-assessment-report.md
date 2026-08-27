# AgentShield AI Assessment

> **Mode:** {{MODE}}  
> **Assessment timestamp (UTC):** {{TIMESTAMP_UTC}}  
> **Trace ID:** {{TRACE_ID}}  
> **Simulation:** {{SIMULATION_STATUS}}

## Executive decision

| Field | Result |
|---|---|
| Assurance posture | {{ASSURANCE_POSTURE}} |
| Assurance score | {{ASSURANCE_SCORE}} |
| Evidence coverage | {{EVIDENCE_COVERAGE}} |
| Confidence | {{CONFIDENCE}} |
| Runtime decision | {{RUNTIME_DECISION_OR_NOT_APPLICABLE}} |
| Policy version | {{POLICY_VERSION_OR_NOT_APPLICABLE}} |

Assurance posture and runtime decision are separate. A `PASS` is not
certification and does not authorize an action.

## Scope and subject

- **Subject:** {{SUBJECT}}
- **Owner:** {{OWNER_OR_UNKNOWN}}
- **Sponsor:** {{SPONSOR_OR_UNKNOWN}}
- **Environment:** {{ENVIRONMENT_OR_UNKNOWN}}
- **Definition hash:** {{DEFINITION_HASH_OR_NO_EVIDENCE}}
- **Tool-manifest hash:** {{TOOL_MANIFEST_HASH_OR_NO_EVIDENCE}}

### Included evidence

{{INCLUDED_EVIDENCE}}

### Missing evidence and coverage limitations

{{MISSING_EVIDENCE_OR_NONE}}

## Observations

Only directly observed, declared, or tested facts belong here.

{{OBSERVATIONS}}

## Hypotheses

Hypotheses are not evidence and require verification.

{{HYPOTHESES_OR_NONE}}

## Assurance findings

| Finding ID | Severity | Control family | Evidence state | Finding | Remediation |
|---|---|---|---|---|---|
| {{ID}} | {{SEVERITY}} | {{FAMILY}} | {{EVIDENCE_STATE}} | {{FINDING}} | {{REMEDIATION}} |

## Proposed action

- **Requester:** {{REQUESTER_OR_NOT_APPLICABLE}}
- **Requester type:** {{REQUESTER_TYPE_OR_NOT_APPLICABLE}}
- **Action:** {{ACTION_OR_NOT_APPLICABLE}}
- **Target:** {{TARGET_OR_NOT_APPLICABLE}}
- **Purpose:** {{PURPOSE_OR_NOT_APPLICABLE}}
- **Nothing reached the target:** {{INTERCEPTION_STATUS}}

## Operational impact

| Dimension | Evidence | Rating |
|---|---|---|
| Target criticality | {{TARGET_CRITICALITY_EVIDENCE}} | {{TARGET_CRITICALITY}} |
| Dependency reach | {{DEPENDENCY_EVIDENCE}} | {{DEPENDENCY_REACH}} |
| Fleet scope | {{FLEET_EVIDENCE}} | {{FLEET_SCOPE}} |
| Data sensitivity | {{DATA_EVIDENCE}} | {{DATA_SENSITIVITY}} |
| Identity reach | {{IDENTITY_EVIDENCE}} | {{IDENTITY_REACH}} |
| Reversibility | {{REVERSIBILITY_EVIDENCE}} | {{REVERSIBILITY}} |

**Operational-impact score:** {{OPERATIONAL_IMPACT_SCORE}}

This score is explanatory and does not grant authorization.

## Deterministic policy

| Control ID | Policy version | Reason code | Decision |
|---|---|---|---|
| {{CONTROL_ID}} | {{POLICY_VERSION}} | {{REASON_CODE}} | {{DECISION}} |

## Approval

- **Result:** {{APPROVAL_RESULT_OR_NOT_REQUIRED}}
- **Approver:** {{APPROVER_OR_NO_EVIDENCE}}
- **Bound requester:** {{BOUND_REQUESTER}}
- **Bound action:** {{BOUND_ACTION}}
- **Bound target:** {{BOUND_TARGET}}
- **Bound plan hash:** {{BOUND_PLAN_HASH}}
- **Bound policy version:** {{BOUND_POLICY_VERSION}}
- **Expiry:** {{APPROVAL_EXPIRY}}

Timeout is not approval. Rejection or invalid binding permits zero executed
steps.

## Constrained safe plan

| Step | Action and scope | Reason | Validation | Rollback | Stop condition |
|---|---|---|---|---|---|
| {{STEP_ID}} | {{STEP_ACTION}} | {{STEP_REASON}} | {{STEP_VALIDATION}} | {{STEP_ROLLBACK}} | {{STEP_STOP}} |

**Plan hash:** {{PLAN_HASH_OR_NOT_APPLICABLE}}

## Outcome validation

| Comparison | Expected | Observed | Result |
|---|---|---|---|
| Action | {{EXPECTED_ACTION}} | {{OBSERVED_ACTION}} | {{ACTION_MATCH}} |
| Target | {{EXPECTED_TARGET}} | {{OBSERVED_TARGET}} | {{TARGET_MATCH}} |
| Plan | {{EXPECTED_PLAN}} | {{OBSERVED_PLAN}} | {{PLAN_MATCH}} |
| Outcome | {{EXPECTED_OUTCOME}} | {{OBSERVED_OUTCOME}} | {{OUTCOME_MATCH}} |

- **Stopped step:** {{STOPPED_STEP_OR_NONE}}
- **Deviations:** {{DEVIATIONS_OR_NONE}}

## Evidence record

{{EVIDENCE_RECORD_SUMMARY}}

## Limitations

{{LIMITATIONS}}

## Accountability

{{ACCOUNTABILITY_STATEMENT}}

AgentShield AI provides security assurance and governance support, not
certification, legal advice, compliance approval, or a guarantee of safety.
