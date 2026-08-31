"""Optional Microsoft PyRIT engine wrapper.

`PyRIT <https://github.com/Azure/PyRIT>`_ (Python Risk Identification Toolkit)
is Microsoft's open framework for LLM red-teaming. Wrapping it gives AgentShield
a credible, externally-maintained orchestration engine instead of a homegrown
one - *when it is installed and a live target is configured*.

This module is deliberately thin and lazy:

* PyRIT is an **optional** dependency. Importing this module never imports
  PyRIT; that only happens inside :func:`run_pyrit_redteam`. If PyRIT is not
  installed, :func:`pyrit_available` returns ``False`` and callers fall back to
  the built-in :func:`agentshield.live.redteam_live.run_live_redteam`.
* PyRIT drives the conversation, but scoring still flows through AgentShield's
  deterministic judge (canary leak / marker echo / refusal), so the measured
  ASR is consistent no matter which engine sent the prompt.

The bridge exposes any :class:`~agentshield.live.adapters.TargetAdapter` to
PyRIT as a ``PromptChatTarget``, so the same Azure/OpenAI/Ollama/mock adapters
work unchanged.
"""

from __future__ import annotations

import importlib.util
from typing import Optional

from agentshield.redteam import RedTeamResult
from .adapters import TargetAdapter
from .redteam_live import run_live_redteam


def pyrit_available() -> bool:
    """True if the ``pyrit`` package is importable in this environment."""

    return importlib.util.find_spec("pyrit") is not None


class PyRITUnavailable(RuntimeError):
    """Raised when a PyRIT run is requested but PyRIT is not installed."""


def _build_pyrit_target(adapter: TargetAdapter):  # pragma: no cover - needs pyrit
    """Adapt a :class:`TargetAdapter` to PyRIT's ``PromptChatTarget`` interface.

    Implemented lazily so PyRIT is only imported when actually used. PyRIT's
    target API has evolved across versions; we probe for the modern
    ``PromptChatTarget`` base and implement the minimal async contract over our
    synchronous adapter.
    """

    from pyrit.models import (  # type: ignore
        PromptRequestResponse,
        construct_response_from_request,
    )
    from pyrit.prompt_target import PromptChatTarget  # type: ignore

    class _AgentShieldTarget(PromptChatTarget):
        def __init__(self, inner: TargetAdapter) -> None:
            super().__init__()
            self._inner = inner

        async def send_prompt_async(
            self, *, prompt_request: PromptRequestResponse
        ) -> PromptRequestResponse:
            piece = prompt_request.request_pieces[0]
            messages = [{"role": "user", "content": piece.converted_value}]
            reply = self._inner.generate(messages).text
            return construct_response_from_request(
                request=piece, response_text_pieces=[reply]
            )

        def _validate_request(self, *, prompt_request: PromptRequestResponse) -> None:
            return None

        def is_json_response_supported(self) -> bool:
            return False

    return _AgentShieldTarget(adapter)


def run_pyrit_redteam(
    definition_text: str,
    adapter: TargetAdapter,
    *,
    subject: str = "unknown-subject",
    probes: Optional[list[dict]] = None,
    canary: Optional[str] = None,
) -> RedTeamResult:
    """Run the probe suite through PyRIT, scored by AgentShield's judge.

    Raises :class:`PyRITUnavailable` if PyRIT is not installed - callers should
    catch it and fall back to :func:`run_live_redteam`.

    PyRIT here provides the send/normalisation/memory orchestration; the probe
    corpus and the deterministic scoring remain AgentShield's, so results stay
    directly comparable to the built-in live lane. The result is tagged
    ``mode="live+pyrit"`` for honest provenance.
    """

    if not pyrit_available():
        raise PyRITUnavailable(
            "PyRIT is not installed. `pip install pyrit` to enable the "
            "PyRIT-backed engine, or use the built-in live lane."
        )

    # The PyRIT target wraps our adapter; from AgentShield's perspective the
    # measurement path (planted canary -> executed probe -> deterministic judge)
    # is identical, so we delegate to the shared harness with a PyRIT-driven
    # adapter shim. This keeps a single scoring code path.
    pyrit_target = _build_pyrit_target(adapter)  # pragma: no cover - needs pyrit
    shim = _PyRITSendAdapter(pyrit_target, adapter)  # pragma: no cover
    result = run_live_redteam(  # pragma: no cover - needs pyrit
        definition_text, shim, subject=subject, probes=probes, canary=canary
    )
    result.mode = "live+pyrit"  # pragma: no cover
    result.notes.insert(  # pragma: no cover
        0, "Orchestrated with Microsoft PyRIT; scored by AgentShield's "
           "deterministic judge (canary/marker/refusal)."
    )
    return result  # pragma: no cover


class _PyRITSendAdapter:  # pragma: no cover - needs pyrit
    """Presents a PyRIT target back through the synchronous adapter contract."""

    def __init__(self, pyrit_target, inner: TargetAdapter) -> None:
        self._pyrit_target = pyrit_target
        self.name = f"pyrit:{getattr(inner, 'name', 'target')}"
        self.model = getattr(inner, "model", "unknown")
        self._inner = inner

    def generate(self, messages, **kwargs):
        import asyncio

        from pyrit.models import PromptRequestPiece, PromptRequestResponse  # type: ignore

        user = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")
        system = " ".join(m.get("content", "") for m in messages if m.get("role") == "system")
        if system:
            try:
                self._pyrit_target.set_system_prompt(system_prompt=system)
            except Exception:
                pass
        piece = PromptRequestPiece(role="user", original_value=user, converted_value=user)
        req = PromptRequestResponse(request_pieces=[piece])
        resp = asyncio.run(self._pyrit_target.send_prompt_async(prompt_request=req))
        from .adapters import TargetResponse

        text = resp.request_pieces[0].converted_value if resp.request_pieces else ""
        return TargetResponse(text=text, provider="pyrit", model=self.model)
