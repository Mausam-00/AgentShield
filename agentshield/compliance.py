"""Deterministic mapping from AgentShield control families to external frameworks.

This module is *advisory reporting only*. It expresses how each assurance
control family (``ASF-01`` .. ``ASF-10``) relates to widely published control
frameworks, and derives an honest, evidence-based coverage status for each
framework control from an existing :class:`AssuranceResult`.

Hard boundaries (see repository instructions):

* The mapping is a static, versioned table. It never authorizes anything and is
  kept separate from runtime policy.
* Coverage status is derived only from evidence already present in the assurance
  result. Absent evidence is reported as ``Unevidenced`` - never inferred away.
* No status ever asserts certification, attestation, or regulatory compliance.
  The strongest status is ``Evidenced`` (tested control family), which still is
  not a compliance claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .assurance import FAMILY_NAMES
from .models import (
    AssuranceResult,
    EvidenceState,
    FamilyEvaluation,
    Finding,
    SEVERITY_ORDER,
    Severity,
)

# Bump when the mapping table or status derivation changes.
COMPLIANCE_MAP_VERSION = "agentshield-compliance-map-1.0.0"

COMPLIANCE_DISCLAIMER = (
    "Framework mapping is advisory and derived from static assurance evidence. "
    "It is not a certification, attestation, audit opinion, or claim of "
    "regulatory compliance. 'Evidenced' means a mapped control family was tested,"
    " not that any framework requirement is satisfied."
)


@dataclass(frozen=True)
class FrameworkMeta:
    key: str
    name: str
    version: str


# Published control frameworks referenced by the mapping.
FRAMEWORKS: dict[str, FrameworkMeta] = {
    "owasp_llm": FrameworkMeta(
        "owasp_llm", "OWASP Top 10 for LLM Applications", "2025"
    ),
    "nist_ai_rmf": FrameworkMeta(
        "nist_ai_rmf", "NIST AI Risk Management Framework", "1.0"
    ),
    "eu_ai_act": FrameworkMeta(
        "eu_ai_act", "EU AI Act (high-risk obligations)", "Regulation (EU) 2024/1689"
    ),
}


@dataclass(frozen=True)
class ControlRef:
    """A single framework control that an ASF family maps to."""

    framework: str
    control_id: str
    control_title: str


# ASF family -> list of framework control references. Every family is mapped so
# no family silently drops out of the matrix.
FAMILY_TO_CONTROLS: dict[str, list[ControlRef]] = {
    "ASF-01": [
        ControlRef("owasp_llm", "LLM01", "Prompt Injection"),
        ControlRef("eu_ai_act", "Art. 15", "Accuracy, robustness and cybersecurity"),
        ControlRef("nist_ai_rmf", "MANAGE", "Manage AI risks"),
    ],
    "ASF-02": [
        ControlRef("owasp_llm", "LLM06", "Excessive Agency"),
        ControlRef("eu_ai_act", "Art. 26", "Obligations of deployers"),
        ControlRef("nist_ai_rmf", "GOVERN", "Govern accountability and roles"),
    ],
    "ASF-03": [
        ControlRef("owasp_llm", "LLM06", "Excessive Agency"),
        ControlRef("eu_ai_act", "Art. 15", "Accuracy, robustness and cybersecurity"),
        ControlRef("nist_ai_rmf", "MANAGE", "Manage AI risks"),
    ],
    "ASF-04": [
        ControlRef("owasp_llm", "LLM02", "Sensitive Information Disclosure"),
        ControlRef("owasp_llm", "LLM08", "Vector and Embedding Weaknesses"),
        ControlRef("eu_ai_act", "Art. 10", "Data and data governance"),
        ControlRef("nist_ai_rmf", "MAP", "Map context and data"),
    ],
    "ASF-05": [
        ControlRef("owasp_llm", "LLM02", "Sensitive Information Disclosure"),
        ControlRef("eu_ai_act", "Art. 15", "Accuracy, robustness and cybersecurity"),
        ControlRef("nist_ai_rmf", "MEASURE", "Measure risks and effectiveness"),
    ],
    "ASF-06": [
        ControlRef("owasp_llm", "LLM06", "Excessive Agency"),
        ControlRef("eu_ai_act", "Art. 14", "Human oversight"),
        ControlRef("nist_ai_rmf", "GOVERN", "Govern accountability and roles"),
    ],
    "ASF-07": [
        ControlRef("owasp_llm", "LLM03", "Supply Chain"),
        ControlRef("eu_ai_act", "Art. 15", "Accuracy, robustness and cybersecurity"),
        ControlRef("nist_ai_rmf", "MAP", "Map context and data"),
    ],
    "ASF-08": [
        ControlRef("owasp_llm", "LLM10", "Unbounded Consumption"),
        ControlRef("eu_ai_act", "Art. 12", "Record-keeping"),
        ControlRef("nist_ai_rmf", "MEASURE", "Measure risks and effectiveness"),
    ],
    "ASF-09": [
        ControlRef("owasp_llm", "LLM10", "Unbounded Consumption"),
        ControlRef("eu_ai_act", "Art. 15", "Accuracy, robustness and cybersecurity"),
        ControlRef("nist_ai_rmf", "MANAGE", "Manage AI risks"),
    ],
    "ASF-10": [
        ControlRef("owasp_llm", "LLM03", "Supply Chain"),
        ControlRef("eu_ai_act", "Art. 11", "Technical documentation"),
        ControlRef("nist_ai_rmf", "GOVERN", "Govern accountability and roles"),
    ],
}

# Honest coverage states, ordered weakest -> strongest for rollups.
STATUS_UNEVIDENCED = "Unevidenced"
STATUS_GAP = "Gap"
STATUS_DECLARED = "Declared (not tested)"
STATUS_PARTIAL = "Partial"
STATUS_EVIDENCED = "Evidenced"

_STATUS_RANK = {
    STATUS_UNEVIDENCED: 0,
    STATUS_GAP: 1,
    STATUS_DECLARED: 2,
    STATUS_PARTIAL: 3,
    STATUS_EVIDENCED: 4,
}


@dataclass
class FamilyStatus:
    family_id: str
    family_name: str
    status: str
    note: str


def _open_finding_severity(family_id: str, findings: list[Finding]) -> Optional[Severity]:
    """Most severe *effective* severity of an open finding on this family."""

    worst: Optional[Severity] = None
    for f in findings:
        if not f.is_open():
            continue
        if f.control_family.split()[0] != family_id:
            continue
        sev = f.effective_severity()
        if worst is None or SEVERITY_ORDER[sev] > SEVERITY_ORDER[worst]:
            worst = sev
    return worst


def _family_status(
    family: Optional[FamilyEvaluation],
    findings: list[Finding],
    family_id: str,
) -> FamilyStatus:
    """Derive an honest per-family coverage status from existing evidence."""

    name = FAMILY_NAMES.get(family_id, family_id)
    if family is None or not family.has_evidence():
        return FamilyStatus(
            family_id, name, STATUS_UNEVIDENCED, "No evidence for this family."
        )

    worst = _open_finding_severity(family_id, findings)
    if worst is not None and SEVERITY_ORDER[worst] >= SEVERITY_ORDER[Severity.MEDIUM]:
        return FamilyStatus(
            family_id,
            name,
            STATUS_GAP,
            f"Open {worst.value} finding weakens this family.",
        )

    state = family.evidence_state
    maturity = family.maturity or 0
    if state == EvidenceState.TESTED and maturity >= 3:
        return FamilyStatus(family_id, name, STATUS_EVIDENCED, "Tested with adequate maturity.")
    if state == EvidenceState.TESTED:
        return FamilyStatus(family_id, name, STATUS_PARTIAL, "Tested but low maturity.")
    if state == EvidenceState.DECLARED:
        return FamilyStatus(
            family_id, name, STATUS_DECLARED, "Declared in definition; not tested."
        )
    if worst is not None:
        return FamilyStatus(
            family_id, name, STATUS_PARTIAL, f"Observed with a {worst.value} finding."
        )
    return FamilyStatus(family_id, name, STATUS_PARTIAL, f"Observed ({state.value}).")


@dataclass
class ControlCoverage:
    control_id: str
    control_title: str
    families: list[str]
    status: str
    note: str


@dataclass
class FrameworkCoverage:
    key: str
    name: str
    version: str
    controls: list[ControlCoverage]
    summary: dict[str, int]


def build_compliance_coverage(assurance: AssuranceResult) -> list[FrameworkCoverage]:
    """Compute per-framework control coverage from an assurance result."""

    families_by_id = {f.family_id: f for f in assurance.families}
    findings = assurance.findings

    # Pre-compute one status per ASF family.
    family_status: dict[str, FamilyStatus] = {
        fid: _family_status(families_by_id.get(fid), findings, fid)
        for fid in FAMILY_TO_CONTROLS
    }

    # Group (framework, control_id) -> {title, families:set}.
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for fid, refs in FAMILY_TO_CONTROLS.items():
        for ref in refs:
            key = (ref.framework, ref.control_id)
            entry = grouped.setdefault(
                key, {"title": ref.control_title, "families": []}
            )
            if fid not in entry["families"]:
                entry["families"].append(fid)

    result: list[FrameworkCoverage] = []
    for fkey, meta in FRAMEWORKS.items():
        controls: list[ControlCoverage] = []
        for (framework, control_id), entry in grouped.items():
            if framework != fkey:
                continue
            fams = sorted(entry["families"])
            # A control is only as strong as its weakest mapped family.
            weakest = min(fams, key=lambda x: _STATUS_RANK[family_status[x].status])
            status = family_status[weakest].status
            note = family_status[weakest].note
            controls.append(
                ControlCoverage(
                    control_id=control_id,
                    control_title=entry["title"],
                    families=fams,
                    status=status,
                    note=note,
                )
            )
        controls.sort(key=lambda c: c.control_id)
        summary = {
            STATUS_EVIDENCED: 0,
            STATUS_PARTIAL: 0,
            STATUS_DECLARED: 0,
            STATUS_GAP: 0,
            STATUS_UNEVIDENCED: 0,
        }
        for c in controls:
            summary[c.status] = summary.get(c.status, 0) + 1
        result.append(
            FrameworkCoverage(
                key=meta.key,
                name=meta.name,
                version=meta.version,
                controls=controls,
                summary=summary,
            )
        )
    return result


def compliance_to_report(assurance: AssuranceResult) -> dict[str, Any]:
    """Serialize compliance coverage into the report schema (advisory block)."""

    frameworks = build_compliance_coverage(assurance)
    return {
        "map_version": COMPLIANCE_MAP_VERSION,
        "disclaimer": COMPLIANCE_DISCLAIMER,
        "frameworks": [
            {
                "key": fw.key,
                "name": fw.name,
                "version": fw.version,
                "summary": fw.summary,
                "controls": [
                    {
                        "control_id": c.control_id,
                        "control_title": c.control_title,
                        "families": c.families,
                        "status": c.status,
                        "note": c.note,
                    }
                    for c in fw.controls
                ],
            }
            for fw in frameworks
        ],
    }
