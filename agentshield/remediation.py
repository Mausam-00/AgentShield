"""Prototype: auto-remediation for assessed agent definitions.

Findings become *action*, not just a report. Given a static assessment, this
module produces a corrected copy of the agent definition and a unified diff:

- SA-03 (over-privilege): remove write-capable tools from front matter.
- SA-02 (bad working dir): comment the invalid working-directory line and add a
  configurable placeholder.
- SA-01 (dangling deps): append a graceful-degradation note.
- SA-05 (no version): insert a ``version`` field into the front matter.

The remediation is deterministic and text-only. It never executes the agent and
only rewrites the definition text it was given.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Optional

from .models import Finding
from .static_assess import StaticAssessment, WRITE_TOOLS

_GRACEFUL_NOTE = (
    "\n\n## Dependency resilience (added by AgentShield)\n\n"
    "If a referenced protocol, template, or knowledge asset is not present, do "
    "not fail silently: announce the missing asset, lower confidence, record a "
    "coverage limitation, and continue with reduced scope. Never invent the "
    "content of a missing asset.\n"
)


@dataclass
class RemediationResult:
    changed: bool
    patched_text: str
    diff: str
    applied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _finding_ids(findings: list[Finding]) -> set[str]:
    return {f.id for f in findings}


def _strip_write_tools(text: str) -> tuple[str, bool]:
    """Remove write-capable entries from the front-matter ``tools:`` list."""

    if not text.startswith("---"):
        return text, False
    end = text.find("\n---", 3)
    if end == -1:
        return text, False
    fm = text[3:end]
    rest = text[end:]
    out_lines: list[str] = []
    changed = False
    in_tools = False
    for line in fm.splitlines():
        stripped = line.strip()
        if re.match(r"^tools\s*:", stripped):
            in_tools = True
            out_lines.append(line)
            continue
        if in_tools:
            m = re.match(r"^-\s*(.+)$", stripped)
            if m:
                tool = m.group(1).strip().strip("'\"")
                if tool.lower() in WRITE_TOOLS:
                    changed = True
                    continue  # drop this tool
                out_lines.append(line)
                continue
            elif stripped and not stripped.startswith("#"):
                in_tools = False
        out_lines.append(line)
    return "---" + "\n".join(out_lines) + rest, changed


def _fix_working_dir(text: str) -> tuple[str, bool]:
    pattern = re.compile(r"(?im)^(\s*[-*]?\s*)(\*\*)?working directory(\*\*)?\s*:\s*`?[A-Za-z]:\\[^\n`]*`?")

    def repl(m: re.Match) -> str:
        prefix = m.group(1)
        return (
            f"{prefix}**Working directory**: `${{AGENT_HOME}}` "
            "(configure to an existing path; was an invalid absolute path)"
        )

    new_text, n = pattern.subn(repl, text)
    return new_text, n > 0


def _insert_version(text: str, version: str = "1.0.0") -> tuple[str, bool]:
    if re.search(r"(?im)^\s*version\s*:", text):
        return text, False
    if not text.startswith("---"):
        return text, False
    end = text.find("\n", 3)
    if end == -1:
        return text, False
    # Insert version right after the opening front-matter fence.
    return text[: end + 1] + f"version: {version}\n" + text[end + 1 :], True


def remediate(assessment: StaticAssessment, *, version: str = "1.0.0") -> RemediationResult:
    """Produce a patched definition and unified diff from an assessment."""

    ids = _finding_ids(assessment.findings)
    text = assessment.definition_text
    original = text
    applied: list[str] = []
    skipped: list[str] = []

    if "SA-03" in ids:
        text, changed = _strip_write_tools(text)
        (applied if changed else skipped).append("SA-03: removed write-capable tools")

    if "SA-02" in ids:
        text, changed = _fix_working_dir(text)
        (applied if changed else skipped).append(
            "SA-02: replaced invalid working directory with configurable placeholder"
        )

    if "SA-01" in ids:
        text = text + _GRACEFUL_NOTE
        applied.append("SA-01: appended dependency-resilience note")

    if "SA-05" in ids:
        text, changed = _insert_version(text, version)
        (applied if changed else skipped).append("SA-05: inserted version field")

    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            text.splitlines(keepends=True),
            fromfile=f"a/{assessment.source_path}",
            tofile=f"b/{assessment.source_path}",
        )
    )
    return RemediationResult(
        changed=bool(applied),
        patched_text=text,
        diff=diff,
        applied=applied,
        skipped=skipped,
    )
