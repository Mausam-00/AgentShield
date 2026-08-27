"""Deterministic token approximation for AgentShield baseline measurement.

Phase 1 instrumentation. This module is intentionally kept OUTSIDE the
``agentshield`` runtime package so that measurement never alters governed
behaviour, and imports only the Python standard library (no new dependency).

IMPORTANT HONESTY NOTE
----------------------
This is an APPROXIMATION, not a model tokenizer. It reports three exact,
deterministic quantities - characters, words, and bytes - and derives an
approximate token count using a disclosed heuristic (``chars / 4``), which is a
commonly used rule of thumb for English-plus-code text. A real byte-pair
encoder (for example ``tiktoken``) can be substituted in a later, approved phase
if a provider-exact count is required; that would be a new dependency and is not
introduced here.

No figure produced here should be presented as a provider-exact token count.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


# Disclosed heuristic: average English/code characters per token.
CHARS_PER_TOKEN = 4.0

_WORD_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


@dataclass
class TokenEstimate:
    chars: int
    words: int
    bytes_utf8: int
    approx_tokens: int  # ceil(chars / CHARS_PER_TOKEN); heuristic, not exact

    def add(self, other: "TokenEstimate") -> "TokenEstimate":
        return TokenEstimate(
            chars=self.chars + other.chars,
            words=self.words + other.words,
            bytes_utf8=self.bytes_utf8 + other.bytes_utf8,
            approx_tokens=self.approx_tokens + other.approx_tokens,
        )

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def estimate_text(text: str) -> TokenEstimate:
    """Deterministic estimate for a string. Exact chars/words/bytes; heuristic tokens."""

    if text is None:
        text = ""
    chars = len(text)
    words = len(_WORD_RE.findall(text))
    bytes_utf8 = len(text.encode("utf-8"))
    approx_tokens = int(math.ceil(chars / CHARS_PER_TOKEN)) if chars else 0
    return TokenEstimate(chars, words, bytes_utf8, approx_tokens)


def estimate_file(path: Path) -> TokenEstimate:
    """Estimate a file's content. Missing file -> zero estimate (recorded, not invented)."""

    try:
        return estimate_text(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, IsADirectoryError):
        return TokenEstimate(0, 0, 0, 0)


def estimate_json(payload: Any) -> TokenEstimate:
    """Estimate a JSON-serialisable payload using a canonical, stable serialisation."""

    import json

    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return estimate_text(text)


def empty() -> TokenEstimate:
    return TokenEstimate(0, 0, 0, 0)
