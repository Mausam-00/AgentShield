"""Static file assessor: turn an agent definition file into an assurance result.

This is the deterministic engine behind the CLI ``ASSESS`` mode. It reads an
agent ``.md`` definition, checks a fixed set of publicly-safe structural rules
(dangling asset references, non-existent working directory, over-privileged
tool grants, hardcoded external URLs, missing version marker, absent
instruction-hierarchy defense), and returns a set of :class:`Finding` objects
plus a coarse :class:`AssuranceResult`.

Every rule is a pure, deterministic text/filesystem check. Nothing here executes
the agent, follows its instructions, or contacts a network. Missing evidence is
recorded as a coverage limitation and never scored favorably.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .assurance import CONTROL_FAMILIES, evaluate_assurance
from .models import (
    AssuranceResult,
    EvidenceState,
    FamilyEvaluation,
    Finding,
    Provenance,
    Severity,
)

# Front-matter tools that grant write/modify capability to an agent.
WRITE_TOOLS = {"edit", "create", "write", "apply_patch", "delete"}

# Referenced-asset patterns of the form ``Protocols/NAME.md`` etc.
_ASSET_RE = re.compile(
    r"(?P<path>(?:Protocols|Templates|MyKnowledge)[\\/][\w\-./\\]+\.\w+)"
)
# Windows working-directory declaration, e.g. ``Working directory: E:\CLI``.
_WORKDIR_RE = re.compile(r"(?i)working directory[^\n:]*:\s*`?([A-Za-z]:\\[^\s`\n]+)")
# External URLs (used to flag hardcoded endpoints; localhost/example excluded).
_URL_RE = re.compile(r"https?://[^\s)>\]\"']+", re.IGNORECASE)
_URL_ALLOW = ("localhost", "127.0.0.1", "example.com", "example.org")
# Markdown headings that scope an illustrative example/sample region.
_EXAMPLE_HEADING_RE = re.compile(
    r"(?i)^\s*#{1,6}\s.*\b(example|sample|for instance|illustrat|demo)\b"
)

# Operator control-attestation block: a heading, then bullet lines of the form
#   - ASF-01: <claim> [evidence: <reference>]
# Only attestations that cite a non-empty evidence reference are honoured.
_ATTEST_HEADING_RE = re.compile(r"(?im)^\s*#{1,6}\s*control attestations\b")
_ATTEST_LINE_RE = re.compile(
    r"(?im)^\s*[-*]\s*(?P<fam>ASF-\d{2})\s*:\s*(?P<claim>.+?)"
    r"\s*\[evidence:\s*(?P<ev>[^\]]+?)\s*\]\s*$"
)
_FAMILY_IDS = {fid for fid, _name, _weight in CONTROL_FAMILIES}


def _fenced_spans(text: str) -> list[tuple[int, int]]:
    """Character spans covered by triple-backtick fenced code blocks."""

    return [(m.start(), m.end()) for m in re.finditer(r"```.*?```", text, re.DOTALL)]


def _example_spans(text: str) -> list[tuple[int, int]]:
    """Character spans of sections introduced by an example/sample heading.

    A region runs from an example heading to the next heading of any level.
    """

    spans: list[tuple[int, int]] = []
    pos = 0
    in_example = False
    start = 0
    for line in text.splitlines(keepends=True):
        if re.match(r"\s*#{1,6}\s", line):
            is_example = bool(_EXAMPLE_HEADING_RE.match(line))
            if in_example and not is_example:
                spans.append((start, pos))
                in_example = False
            if is_example and not in_example:
                in_example = True
                start = pos
        pos += len(line)
    if in_example:
        spans.append((start, pos))
    return spans


def _in_spans(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(a <= pos < b for a, b in spans)


def _parse_attestations(text: str) -> dict[str, str]:
    """Parse an operator ``## Control attestations`` block.

    Returns ``{family_id: evidence_ref}`` for each control family the operator
    formally attests to, provided the line cites a non-empty evidence reference.
    Only lines within the attestation section (its heading up to the next
    heading of any level) are considered.

    An attestation is a *self-declared* claim backed by a cited artifact. The
    engine credits it above a bare declaration but never treats it as an
    independent test: attested families cannot reach HIGH confidence, so a
    static assessment still cannot certify (PASS). This keeps operators honest
    while giving structured, evidence-referenced hardening real, bounded credit.
    """

    m = _ATTEST_HEADING_RE.search(text)
    if not m:
        return {}
    start = m.end()
    nxt = re.search(r"(?m)^\s*#{1,6}\s", text[start:])
    section = text[start : start + nxt.start()] if nxt else text[start:]
    out: dict[str, str] = {}
    for line in _ATTEST_LINE_RE.finditer(section):
        fam = line.group("fam").upper()
        ev = line.group("ev").strip()
        if fam in _FAMILY_IDS and ev:
            out.setdefault(fam, ev)
    return out


def _classify_provenance(
    positions: list[int],
    fenced: list[tuple[int, int]],
    example: list[tuple[int, int]],
) -> Provenance:
    """Classify a finding by the provenance of every matched position.

    Conservative: if any match sits in the active definition body, the whole
    finding is treated as active (full weight). Only when *all* matches are
    illustrative is the finding down-weighted.
    """

    if not positions:
        return Provenance.DEFINITION_BODY
    if all(_in_spans(p, fenced) for p in positions):
        return Provenance.FENCED_EXAMPLE
    if all(_in_spans(p, fenced) or _in_spans(p, example) for p in positions):
        return Provenance.DOCS_EXAMPLE
    return Provenance.DEFINITION_BODY


@dataclass
class StaticAssessment:
    subject: str
    source_path: str
    findings: list[Finding]
    assurance: AssuranceResult
    write_tools: list[str]
    definition_text: str


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _front_matter_tools(text: str) -> list[str]:
    """Extract the ``tools:`` list from YAML front matter, if present."""

    if not text.startswith("---"):
        return []
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else text[3:]
    tools: list[str] = []
    in_tools = False
    for line in block.splitlines():
        stripped = line.strip()
        if re.match(r"^tools\s*:", stripped):
            in_tools = True
            # inline list form: tools: [a, b]
            inline = stripped.split(":", 1)[1].strip()
            if inline.startswith("["):
                return [t.strip().strip("'\"") for t in inline.strip("[]").split(",") if t.strip()]
            continue
        if in_tools:
            m = re.match(r"^-\s*(.+)$", stripped)
            if m:
                tools.append(m.group(1).strip().strip("'\""))
            elif stripped and not stripped.startswith("#"):
                break
    return tools


def _agent_name(text: str, fallback: str) -> str:
    m = re.search(r"(?im)^name\s*:\s*(.+)$", text)
    return m.group(1).strip() if m else fallback


def assess_agent_file(
    path: str,
    *,
    resolve_roots: Optional[list[str]] = None,
) -> StaticAssessment:
    """Assess a single agent definition file.

    ``resolve_roots`` are additional base directories against which referenced
    assets are checked for existence (in addition to the file's own directory
    and any absolute drive path found in the definition).
    """

    p = Path(path)
    text = _read(p)
    name = _agent_name(text, p.stem)
    tools = _front_matter_tools(text)
    write_tools = [t for t in tools if t.lower() in WRITE_TOOLS]

    findings: list[Finding] = []
    roots = [p.parent] + [Path(r) for r in (resolve_roots or [])]
    fenced = _fenced_spans(text)
    example = _example_spans(text)

    # --- Rule 1: dangling asset references --------------------------------
    ref_positions: dict[str, list[int]] = {}
    for m in _ASSET_RE.finditer(text):
        ref_positions.setdefault(m.group("path"), []).append(m.start())
    referenced = sorted(ref_positions)
    dangling: list[str] = []
    dangling_positions: list[int] = []
    for ref in referenced:
        rel = ref.replace("\\", "/")
        if not any((root / rel).exists() for root in roots):
            dangling.append(ref)
            dangling_positions.extend(ref_positions[ref])
    if dangling:
        findings.append(
            Finding(
                id="SA-01",
                control_family="ASF-08 Monitoring, auditability, and evidence retention",
                severity=Severity.HIGH,
                title="Dangling dependency references",
                condition="Referenced protocol/template/knowledge assets do not exist",
                evidence_state=EvidenceState.OBSERVED,
                observation="Missing referenced assets: " + ", ".join(dangling),
                remediation=(
                    "Ship the referenced assets alongside the agent, or make the "
                    "agent degrade gracefully and announce when they are absent."
                ),
                evidence_refs=[str(p)],
                impact=(
                    "'Always reference' instructions silently no-op or error, "
                    "degrading output quality without the operator knowing."
                ),
                provenance=_classify_provenance(dangling_positions, fenced, example),
            )
        )

    # --- Rule 2: non-existent working directory ---------------------------
    for wm in _WORKDIR_RE.finditer(text):
        wd = wm.group(1)
        if not Path(wd).exists():
            findings.append(
                Finding(
                    id="SA-02",
                    control_family="ASF-09 Fail-closed behavior, resilience, and recovery",
                    severity=Severity.HIGH,
                    title="Declared working directory does not exist",
                    condition="Declared working directory is not present on this host",
                    evidence_state=EvidenceState.OBSERVED,
                    observation=f"Working directory '{wd}' was not found.",
                    remediation=(
                        "Point the working directory to a path that exists, or make "
                        "it configurable / relative to the install location."
                    ),
                    evidence_refs=[str(p)],
                    impact="Relative asset paths resolve against a non-existent root.",
                    provenance=_classify_provenance([wm.start()], fenced, example),
                )
            )
            break

    # --- Rule 3: over-privileged tool grant vs role -----------------------
    role_is_readonly = bool(
        re.search(r"(?i)\b(analy|diagnos|assess|review|read-only|inspect)", text)
    )
    if write_tools and role_is_readonly:
        findings.append(
            Finding(
                id="SA-03",
                control_family="ASF-03 Tool inventory, permissions, and least privilege",
                severity=Severity.MEDIUM,
                title="Over-privileged tool grant versus role",
                condition="Write-capable tools granted to an analysis/diagnostic role",
                evidence_state=EvidenceState.OBSERVED,
                observation="Write-capable tools granted: " + ", ".join(write_tools),
                remediation=(
                    "Remove write tools unless a concrete write use-case exists; if "
                    "retained, restrict writes to a declared output directory."
                ),
                evidence_refs=[str(p)],
                impact="Write capability exceeds least privilege and widens the trust boundary.",
            )
        )

    # --- Rule 4: hardcoded external URLs ----------------------------------
    url_positions: dict[str, list[int]] = {}
    for m in _URL_RE.finditer(text):
        u = m.group(0)
        if not any(a in u.lower() for a in _URL_ALLOW):
            url_positions.setdefault(u, []).append(m.start())
    urls = sorted(url_positions)
    if urls:
        flat_positions = [pos for u in urls for pos in url_positions[u]]
        findings.append(
            Finding(
                id="SA-04",
                control_family="ASF-05 Secret handling and output protection",
                severity=Severity.LOW,
                title="Hardcoded external endpoint(s)",
                condition="Definition embeds external URL(s)",
                evidence_state=EvidenceState.OBSERVED,
                observation="External URL(s): " + ", ".join(urls[:5]),
                remediation="Make external endpoints configurable and allowlisted.",
                evidence_refs=[str(p)],
                impact="Hardcoded endpoints reduce portability and can leak intent.",
                provenance=_classify_provenance(flat_positions, fenced, example),
            )
        )

    # --- Rule 5: missing version / integrity marker -----------------------
    if not re.search(r"(?im)^\s*(version|revision)\s*:", text):
        findings.append(
            Finding(
                id="SA-05",
                control_family="ASF-10 Definition, manifest, and policy version integrity",
                severity=Severity.LOW,
                title="Unversioned definition with no integrity marker",
                condition="No version/revision field present",
                evidence_state=EvidenceState.OBSERVED,
                observation="No 'version:' field found in the definition.",
                remediation="Add a version field and an integrity/hash marker.",
                evidence_refs=[str(p)],
                impact="Assurance freshness and definition-hash binding cannot be established.",
                provenance=Provenance.ABSENCE,
            )
        )

    # --- Rule 6: instruction-hierarchy / untrusted-content defense --------
    text_l = text.lower()
    has_hierarchy = any(
        s in text_l
        for s in (
            "instruction hierarchy",
            "take precedence",
            "as data, not",
            "data, not instructions",
            "untrusted",
            "never obey",
            "do not follow instructions",
            "inert data",
        )
    )
    if not has_hierarchy:
        findings.append(
            Finding(
                id="SA-06",
                control_family="ASF-01 Instruction hierarchy and untrusted-content isolation",
                severity=Severity.MEDIUM,
                title="No explicit instruction-hierarchy / untrusted-content defense",
                condition="Definition lacks language treating external content as data",
                evidence_state=EvidenceState.OBSERVED,
                observation="No instruction-hierarchy or untrusted-content isolation language found.",
                remediation=(
                    "State that system instructions take precedence and that external/"
                    "tool content is untrusted data, never instructions."
                ),
                evidence_refs=[str(p)],
                impact="Raises exposure to direct and indirect prompt injection.",
                provenance=Provenance.ABSENCE,
            )
        )

    assurance = _assurance_from_findings(
        subject=name,
        findings=findings,
        definition_text=text,
        write_capable=bool(write_tools),
        attestations=_parse_attestations(text),
    )

    return StaticAssessment(
        subject=name,
        source_path=str(p),
        findings=findings,
        assurance=assurance,
        write_tools=write_tools,
        definition_text=text,
    )


def _assurance_from_findings(
    *,
    subject: str,
    findings: list[Finding],
    definition_text: str,
    write_capable: bool,
    attestations: Optional[dict[str, str]] = None,
) -> AssuranceResult:
    """Derive a coarse assurance result from the affected control families.

    Each family's maturity is reduced by the most severe open finding that
    touches it. A family with no open finding is either DECLARED at maturity 3
    (documented but not tested) or, when the operator supplies an evidence-cited
    attestation for it, ATTESTED at maturity 4. Attested families are credited
    above a bare declaration but are never counted as TESTED, so confidence
    stays below HIGH and the posture cannot reach PASS from static text alone.
    """

    attestations = attestations or {}
    sev_penalty = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 2,
        Severity.LOW: 3,
        Severity.INFO: 3,
    }
    worst: dict[str, Severity] = {}
    for f in findings:
        fam_id = f.control_family.split()[0]
        sev = f.effective_severity()
        cur = worst.get(fam_id)
        if cur is None or sev_penalty[sev] < sev_penalty[cur]:
            worst[fam_id] = sev

    families: list[FamilyEvaluation] = []
    for fid, name, weight in CONTROL_FAMILIES:
        if fid in worst:
            # An open finding always wins over any attestation for that family.
            maturity = sev_penalty[worst[fid]]
            state = EvidenceState.OBSERVED
            note = f"reduced by {worst[fid].value} finding"
        elif fid in attestations:
            maturity = 4
            state = EvidenceState.ATTESTED
            note = (
                f"operator-attested (evidence: {attestations[fid]}); "
                "attested, not independently tested"
            )
        else:
            maturity = 3
            state = EvidenceState.DECLARED
            note = "declared in definition; not tested"
        families.append(
            FamilyEvaluation(fid, name, weight, maturity, state, note)
        )

    return evaluate_assurance(
        subject=subject,
        families=families,
        findings=findings,
        definition_text=definition_text,
        write_capable=write_capable,
    )
