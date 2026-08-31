"""AgentShield live-assessment lane.

This package upgrades the red-team and Responsible-AI signals from *static
inference* (does the definition text declare a defense?) to *live measurement*
(execute a probe against a real model target and observe what actually
happens).

Design principles, consistent with the rest of AgentShield:

* **Target-agnostic.** A :class:`~agentshield.live.adapters.TargetAdapter`
  abstracts the model under test. Adapters exist for Azure AI Foundry, Azure
  OpenAI, OpenAI, and Ollama, plus a deterministic
  :class:`~agentshield.live.adapters.MockAdapter` so the whole lane runs
  offline and in CI with no credentials or egress.
* **Honest fallback.** When no live target is configured, callers fall back to
  the existing static inference. Live results are labelled ``mode="live"`` and
  carry HIGH confidence (measured); static results stay ``mode="static"`` and
  are capped at WARN.
* **Measured, deterministic scoring.** Attack success is decided by observable
  evidence - a planted canary leaking, an explicit compliance marker echoed,
  or the absence of a refusal - never by a keyword in the target's own text.
"""

from __future__ import annotations

from .adapters import (  # noqa: F401
    AdapterError,
    MockAdapter,
    TargetAdapter,
    TargetResponse,
    build_target_adapter,
    describe_target_config,
)

__all__ = [
    "AdapterError",
    "MockAdapter",
    "TargetAdapter",
    "TargetResponse",
    "build_target_adapter",
    "describe_target_config",
]
