"""Azure AI Content Safety - Prompt Shields adapter (offline heuristic).

Feeds Gate R (red-team) with a detection signal shaped like Azure AI Content
Safety's Prompt Shields response (``attackDetected`` for user-prompt and
document/tool content). The real service is a network call; this adapter is a
deterministic offline heuristic so the pipeline runs without credentials or
egress. Swap in the real client behind the same :class:`ShieldVerdict` shape.

The heuristic never *obeys* analysed content - it only scans it as inert data
for well-known injection and jailbreak markers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Markers associated with direct prompt-injection / jailbreak attempts.
_USER_PROMPT_MARKERS = [
    r"ignore (all|any|previous|prior) (instructions|rules)",
    r"disregard (the|your|all) (system|previous) (prompt|instructions)",
    r"you are now (in )?(dan|developer mode|jailbroken)",
    r"pretend (you are|to be) (an?|the) .*(unrestricted|no rules)",
    r"reveal (your )?(system prompt|hidden instructions)",
    r"do anything now",
]
# Markers associated with indirect / document / tool-embedded injection.
_DOCUMENT_MARKERS = [
    r"</?system>",
    r"assistant:\s*",
    r"tool_call\s*:",
    r"exfiltrate|send (the )?(secret|token|credential)",
    r"when you read this,? (do|execute|run)",
]


@dataclass
class ShieldVerdict:
    """Mirrors the Prompt Shields decision surface."""

    user_prompt_attack: bool
    document_attack: bool
    matched: list[str] = field(default_factory=list)

    @property
    def attack_detected(self) -> bool:
        return self.user_prompt_attack or self.document_attack

    def as_dict(self) -> dict:
        return {
            "userPromptAnalysis": {"attackDetected": self.user_prompt_attack},
            "documentsAnalysis": [{"attackDetected": self.document_attack}],
            "matched": self.matched,
        }


class ContentSafetyPromptShield:
    """Offline Prompt Shields analog. No network, no credentials."""

    def __init__(self) -> None:
        self._user_re = [re.compile(p, re.IGNORECASE) for p in _USER_PROMPT_MARKERS]
        self._doc_re = [re.compile(p, re.IGNORECASE) for p in _DOCUMENT_MARKERS]

    def analyze(self, user_prompt: str = "", documents: list[str] | None = None) -> ShieldVerdict:
        matched: list[str] = []
        up = user_prompt or ""
        user_hit = False
        for rx in self._user_re:
            m = rx.search(up)
            if m:
                user_hit = True
                matched.append(f"user:{m.group(0)[:40]}")

        doc_hit = False
        for doc in documents or []:
            for rx in self._doc_re:
                m = rx.search(doc or "")
                if m:
                    doc_hit = True
                    matched.append(f"doc:{m.group(0)[:40]}")

        return ShieldVerdict(user_hit, doc_hit, matched)

    def injection_resistance_signal(self, definition_text: str) -> float:
        """Return a 0..1 resistance signal for a target definition.

        A definition that itself contains many injection markers as *examples of
        what to refuse* is treated as more defended; one that contains active
        injection phrasing with no refusal context scores lower. This is a coarse
        heuristic used only to enrich Gate R, never to authorize anything.
        """

        verdict = self.analyze(user_prompt=definition_text, documents=[definition_text])
        text_l = (definition_text or "").lower()
        has_refusal = any(
            kw in text_l for kw in ("refuse", "decline", "must not", "never obey", "inert data")
        )
        if not verdict.attack_detected:
            return 1.0
        return 0.7 if has_refusal else 0.3
