"""Bridge from AgentShield evidence to the HTML report schema.

Builds a report input document strictly from existing evidence and assurance
results. It never invents missing values; absent optional data is left as
``None`` so the generator renders ``No evidence available``.
"""

from __future__ import annotations

from typing import Any, Optional

from .models import (
    AssuranceResult,
    EvidenceState,
    Mode,
    WorkflowResult,
)


def workflow_to_report(
    result: WorkflowResult,
    *,
    simulation: bool = True,
    observations: Optional[list[str]] = None,
    hypotheses: Optional[list[str]] = None,
    redteam: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Assemble a report-schema document from a completed workflow result."""

    assurance = result.assurance
    evidence = result.evidence

    runtime = None
    if result.policy is not None:
        runtime = {
            "decision": result.policy.decision.value,
            "policy_version": result.policy.policy_version,
            "action": evidence.action if evidence else None,
            "target": evidence.target if evidence else None,
            "purpose": evidence.purpose if evidence else None,
            "environment": evidence.environment if evidence else None,
            "operational_impact_score": (
                result.impact.score if result.impact else None
            ),
            "nothing_reached_target": result.nothing_reached_target,
        }

    return {
        "trace_id": result.trace_id,
        "timestamp_utc": evidence.timestamp_utc if evidence else None,
        "mode": result.mode.value,
        "simulation": simulation,
        "subject": {
            "name": assurance.subject if assurance else (
                evidence.requester_id if evidence else None
            ),
            "owner": evidence.owner if evidence else None,
            "sponsor": evidence.sponsor if evidence else None,
        },
        "assurance": _assurance_block(assurance),
        "runtime": runtime,
        "findings": _findings_block(assurance),
        "coverage_limitations": (
            evidence.coverage_limitations if evidence else []
        ),
        "observations": observations or [],
        "hypotheses": hypotheses or [],
        "redteam": redteam,
        "policy_matches": _policy_block(result),
        "approval": _approval_block(result),
        "plan": _plan_block(result),
        "validation": _validation_block(result),
        "evidence_summary": {
            "outcome": evidence.outcome if evidence else "unknown",
            "reason_codes": evidence.reason_codes if evidence else [],
        },
        "limitations": list(result.limitations),
        "accountability_statement": (
            evidence.accountability_statement if evidence else ""
        ),
    }


def _assurance_block(assurance: Optional[AssuranceResult]) -> dict[str, Any]:
    if assurance is None:
        return {
            "posture": "BLOCK",
            "score": None,
            "coverage": 0.0,
            "confidence": "LOW",
            "audit_version": None,
            "definition_hash": None,
            "tool_manifest_hash": None,
        }
    return {
        "posture": assurance.posture.value,
        "score": assurance.score,
        "coverage": assurance.coverage,
        "confidence": assurance.confidence.value,
        "audit_version": assurance.audit_version,
        "definition_hash": assurance.definition_hash,
        "tool_manifest_hash": assurance.tool_manifest_hash,
    }


def _findings_block(assurance: Optional[AssuranceResult]) -> list[dict[str, Any]]:
    if assurance is None:
        return []
    blocks = []
    for f in assurance.findings:
        blocks.append(
            {
                "id": f.id,
                "severity": f.severity.value,
                "control_family": f.control_family,
                "evidence_state": f.evidence_state.value,
                "title": f.title,
                "observation": f.observation,
                "remediation": f.remediation,
                "hypothesis": f.hypothesis,
            }
        )
    return blocks


def _policy_block(result: WorkflowResult) -> list[dict[str, Any]]:
    if result.policy is None:
        return []
    return [
        {
            "control_id": m.control_id,
            "reason_code": m.reason_code,
            "decision": m.decision.value,
            "explanation": m.explanation,
        }
        for m in result.policy.matches
    ]


def _approval_block(result: WorkflowResult) -> Optional[dict[str, Any]]:
    approval = result.approval
    if approval is None:
        return None
    binding = approval.binding
    return {
        "result": approval.result.value,
        "approver": approval.approver,
        "requester": binding.requester_id if binding else None,
        "action": binding.action if binding else None,
        "target": binding.target if binding else None,
        "plan_hash": binding.plan_hash if binding else None,
        "policy_version": binding.policy_version if binding else None,
        "expiry": binding.expiry_utc if binding else None,
    }


def _plan_block(result: WorkflowResult) -> Optional[dict[str, Any]]:
    plan = result.plan
    if plan is None:
        return None
    return {
        "plan_hash": plan.plan_hash,
        "steps": [
            {
                "id": s.id,
                "action": s.action,
                "target_scope": s.target_scope,
                "reason": s.reason,
                "validation": s.validation,
                "rollback": s.rollback,
                "stop_condition": s.stop_condition,
            }
            for s in plan.steps
        ],
    }


def _validation_block(result: WorkflowResult) -> Optional[dict[str, Any]]:
    v = result.validation
    if v is None:
        return None
    return {
        "action_match": v.action_match,
        "target_match": v.target_match,
        "outcome_match": v.outcome_match,
        "stopped_step": v.stopped_step,
        "deviations": v.deviations,
    }

