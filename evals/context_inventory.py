"""Static context inventory for the AgentShield token-consumption baseline.

Maps the token-consumption model categories (Deliverable 3) to the real files
in this repository and approximates the always-on tool-definition surface by
introspecting the package's public exports. Standard library only.

The BASELINE assumes the CURRENT design: no gate-specific tool loading and no
progressive disclosure, so every category below is treated as always-on context
for every task. That is the honest pre-optimisation starting point.
"""

from __future__ import annotations

import inspect
from pathlib import Path

from token_estimate import TokenEstimate, estimate_file, estimate_text, empty

ROOT = Path(__file__).resolve().parents[1]

# Token-model category -> repository files that supply that context today.
CONTEXT_FILES: dict[str, list[Path]] = {
    "system_instructions": [
        ROOT / "AGENTS.md",
        ROOT / ".github" / "copilot-instructions.md",
    ],
    "agent_profile": [
        ROOT / ".github" / "agents" / "agentshield.agent.md",
    ],
    "protocol_controls": [
        ROOT / "Protocols" / "AGENTSHIELD-PROTOCOL.md",
        ROOT / "Protocols" / "RESPONSIBLE-AI-PROTOCOL.md",
    ],
    "skills": [
        ROOT / ".github" / "skills" / "agentshield-html-report" / "SKILL.md",
        ROOT / ".github" / "skills" / "agentshield-html-report" / "references"
        / "report-schema.md",
    ],
    "templates": [
        ROOT / "Templates" / "agentshield-assessment-report.md",
        ROOT / "Templates" / "responsible-ai-assessment-report.md",
    ],
}


def _tool_definition_text() -> str:
    """Approximate the always-on tool surface from the package public exports.

    Uses each public callable's name, signature, and full docstring - a proxy for
    a Level-3 (full) tool description, which is what an always-on design would
    expose today. Deterministic and offline.
    """

    import agentshield

    parts: list[str] = []
    for name in sorted(getattr(agentshield, "__all__", [])):
        obj = getattr(agentshield, name, None)
        if obj is None:
            continue
        try:
            sig = str(inspect.signature(obj))
        except (TypeError, ValueError):
            sig = "(...)"
        doc = inspect.getdoc(obj) or ""
        parts.append(f"{name}{sig}\n{doc}")
    return "\n\n".join(parts)


def static_context() -> dict[str, TokenEstimate]:
    """Return the always-on context estimate per token-model category."""

    result: dict[str, TokenEstimate] = {}
    for category, files in CONTEXT_FILES.items():
        acc = empty()
        for path in files:
            acc = acc.add(estimate_file(path))
        result[category] = acc
    result["tool_definitions"] = estimate_text(_tool_definition_text())
    return result


def static_context_total(inv: dict[str, TokenEstimate]) -> TokenEstimate:
    acc = empty()
    for est in inv.values():
        acc = acc.add(est)
    return acc
