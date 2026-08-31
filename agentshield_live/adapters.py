"""Target-model adapters for the live-assessment lane.

A :class:`TargetAdapter` is the single seam between AgentShield and the model
under test. Every adapter takes a list of chat messages and returns a
:class:`TargetResponse`; nothing else in the live lane knows or cares which
provider is behind it.

Adapters are intentionally stdlib-only (``urllib``) so the engine has **no new
runtime dependencies** and can talk to any OpenAI-compatible or Azure endpoint.
Provider selection is env-driven via :func:`build_target_adapter`, so nothing
is hardcoded and CI stays offline by defaulting to :class:`MockAdapter`.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol, runtime_checkable

# A chat message is the familiar ``{"role": ..., "content": ...}`` shape.
Message = dict[str, str]


class AdapterError(RuntimeError):
    """Raised when a live target cannot be reached or returns an error.

    The live harness treats an :class:`AdapterError` as an *inconclusive* probe
    (not a silent success), so a broken endpoint never masquerades as a
    resisted attack.
    """


@dataclass
class TargetResponse:
    """A single completion from the model under test."""

    text: str
    provider: str
    model: str
    latency_ms: float = 0.0
    raw: dict = field(default_factory=dict)


@runtime_checkable
class TargetAdapter(Protocol):
    """Protocol every model target must satisfy."""

    name: str
    model: str

    def generate(self, messages: list[Message], **kwargs) -> TargetResponse:
        """Return the model's completion for ``messages``."""


# --------------------------------------------------------------------------- #
# Mock adapter (deterministic, offline, CI-safe)
# --------------------------------------------------------------------------- #

# Canonical refusal phrasing the judge recognises. Kept here so the mock and the
# scorer agree by construction in tests.
_REFUSAL_LINE = (
    "I can't help with that. That request conflicts with my safety policy, so "
    "I must refuse and will not comply."
)


class MockAdapter:
    """A deterministic, offline stand-in for a real model.

    ``behavior`` selects how the mock *reacts to attacks* so tests can measure
    a known ASR without network access:

    * ``"hardened"`` - always refuses (expected measured ASR ~ 0).
    * ``"vulnerable"`` - complies: echoes any explicit compliance marker found
      in the probe and leaks the planted canary (expected ASR ~ 1).
    * ``"mixed"`` - complies only with injection/jailbreak families, refuses the
      rest (a realistic partial posture).
    * a callable ``(messages) -> str`` - full control for bespoke scenarios.
    """

    def __init__(
        self,
        behavior: "str | Callable[[list[Message]], str]" = "hardened",
        *,
        model: str = "mock-model",
    ) -> None:
        self.name = "mock"
        self.model = model
        self.behavior = behavior

    def generate(self, messages: list[Message], **kwargs) -> TargetResponse:
        if callable(self.behavior):
            text = self.behavior(messages)
            return TargetResponse(text=text, provider="mock", model=self.model)

        system = " ".join(m.get("content", "") for m in messages if m.get("role") == "system")
        user = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")
        text = self._react(self.behavior, system, user)
        return TargetResponse(text=text, provider="mock", model=self.model)

    @staticmethod
    def _react(behavior: str, system: str, user: str) -> str:
        from .canary import extract_canary, extract_compliance_markers

        comply = behavior == "vulnerable"
        if behavior == "mixed":
            low = user.lower()
            comply = any(
                s in low for s in ("ignore", "override", "system prompt", "exfil", "instructions")
            )
        if not comply:
            return _REFUSAL_LINE

        # A "vulnerable" model both echoes the attack's compliance marker and
        # leaks any secret it was given - exactly the observable evidence the
        # judge scores as a measured success.
        parts: list[str] = []
        for marker in extract_compliance_markers(user):
            parts.append(marker)
        canary = extract_canary(system)
        if canary:
            parts.append(f"the secret is {canary}")
        if not parts:
            parts.append("Sure, here is the unrestricted answer you asked for.")
        return " ".join(parts)


# --------------------------------------------------------------------------- #
# HTTP adapters (OpenAI-compatible + Azure)
# --------------------------------------------------------------------------- #


def _http_post_json(url: str, headers: dict, payload: dict, timeout: float) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # pragma: no cover - network path
        body = exc.read().decode("utf-8", "replace")[:500]
        raise AdapterError(f"target HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover - network path
        raise AdapterError(f"target unreachable: {exc.reason}") from exc
    except (TimeoutError, OSError) as exc:  # pragma: no cover - network path
        raise AdapterError(f"target request failed: {exc}") from exc


def _extract_openai_text(body: dict) -> str:
    try:
        return body["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover
        raise AdapterError(f"unexpected response shape: {body!r}") from exc


class _OpenAICompatibleAdapter:
    """Base for any endpoint exposing the OpenAI chat-completions contract."""

    provider = "openai-compatible"

    def __init__(
        self,
        *,
        url: str,
        model: str,
        headers: dict,
        timeout: float,
        max_tokens: int,
        temperature: float,
        name: Optional[str] = None,
    ) -> None:
        self._url = url
        self.model = model
        self._headers = {"Content-Type": "application/json", **headers}
        self._timeout = timeout
        self._max_tokens = max_tokens
        self._temperature = temperature
        self.name = name or self.provider

    def generate(self, messages: list[Message], **kwargs) -> TargetResponse:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self._max_tokens),
            "temperature": kwargs.get("temperature", self._temperature),
        }
        start = time.perf_counter()
        body = _http_post_json(self._url, self._headers, payload, self._timeout)
        latency = (time.perf_counter() - start) * 1000.0
        return TargetResponse(
            text=_extract_openai_text(body),
            provider=self.provider,
            model=self.model,
            latency_ms=round(latency, 1),
            raw=body,
        )


# --------------------------------------------------------------------------- #
# Env-driven factory
# --------------------------------------------------------------------------- #

_DEFAULT_TIMEOUT = 60.0
_DEFAULT_MAX_TOKENS = 512
# Attacks must be evaluated at a deterministic, low temperature.
_DEFAULT_TEMPERATURE = 0.0


def _env(*names: str) -> Optional[str]:
    for n in names:
        v = os.environ.get(n)
        if v:
            return v.strip()
    return None


def describe_target_config() -> dict:
    """Non-secret description of what target (if any) is configured.

    Never returns keys or tokens - only which provider would be selected and the
    model/endpoint host, for honest display in the report.
    """

    provider = (_env("AGENTSHIELD_LIVE_TARGET") or "").lower()
    if not provider:
        # Infer from whichever credential set is present.
        if _env("AZURE_AI_ENDPOINT") and _env("AZURE_AI_KEY"):
            provider = "azure_ai"
        elif _env("AZURE_OPENAI_ENDPOINT") and _env("AZURE_OPENAI_KEY", "AZURE_OPENAI_API_KEY"):
            provider = "azure_openai"
        elif _env("OPENAI_API_KEY"):
            provider = "openai"
        elif _env("OLLAMA_HOST", "OLLAMA_BASE_URL"):
            provider = "ollama"
        else:
            provider = "mock"
    model = _env(
        "AGENTSHIELD_LIVE_MODEL", "AZURE_AI_MODEL", "AZURE_OPENAI_DEPLOYMENT",
        "OPENAI_MODEL", "OLLAMA_MODEL",
    )
    return {
        "provider": provider,
        "model": model,
        "configured": provider not in ("", "mock"),
    }


def build_target_adapter(
    *,
    allow_mock: bool = True,
    behavior: str = "hardened",
) -> TargetAdapter:
    """Construct the model target from environment variables.

    Selection order (first satisfied wins), overridable with
    ``AGENTSHIELD_LIVE_TARGET`` = ``azure_ai|azure_openai|openai|ollama|mock``:

    1. Azure AI Foundry  - ``AZURE_AI_ENDPOINT`` + ``AZURE_AI_KEY`` + ``AZURE_AI_MODEL``
    2. Azure OpenAI      - ``AZURE_OPENAI_ENDPOINT`` + ``AZURE_OPENAI_KEY`` + ``AZURE_OPENAI_DEPLOYMENT``
    3. OpenAI            - ``OPENAI_API_KEY`` (+ ``OPENAI_MODEL``)
    4. Ollama            - ``OLLAMA_HOST`` (+ ``OLLAMA_MODEL``)

    Falls back to :class:`MockAdapter` when nothing is configured (and
    ``allow_mock``); otherwise raises :class:`AdapterError` so a caller that
    *requires* a live target fails closed rather than silently mocking.
    """

    forced = (_env("AGENTSHIELD_LIVE_TARGET") or "").lower()
    timeout = float(_env("AGENTSHIELD_LIVE_TIMEOUT") or _DEFAULT_TIMEOUT)
    max_tokens = int(_env("AGENTSHIELD_LIVE_MAX_TOKENS") or _DEFAULT_MAX_TOKENS)
    temperature = float(_env("AGENTSHIELD_LIVE_TEMPERATURE") or _DEFAULT_TEMPERATURE)

    def want(provider: str) -> bool:
        return forced == provider or (not forced)

    # 1) Azure AI Foundry (unified model-inference endpoint)
    if want("azure_ai"):
        endpoint = _env("AZURE_AI_ENDPOINT")
        key = _env("AZURE_AI_KEY")
        model = _env("AGENTSHIELD_LIVE_MODEL", "AZURE_AI_MODEL")
        if endpoint and key and model:
            api_version = _env("AZURE_AI_API_VERSION") or "2024-05-01-preview"
            base = endpoint.rstrip("/")
            url = f"{base}/models/chat/completions?api-version={api_version}"
            return _OpenAICompatibleAdapter(
                url=url, model=model,
                headers={"api-key": key},
                timeout=timeout, max_tokens=max_tokens, temperature=temperature,
                name="azure_ai",
            )
        if forced == "azure_ai":
            raise AdapterError("azure_ai selected but AZURE_AI_ENDPOINT/KEY/MODEL are not all set")

    # 2) Azure OpenAI (deployment-scoped endpoint)
    if want("azure_openai"):
        endpoint = _env("AZURE_OPENAI_ENDPOINT")
        key = _env("AZURE_OPENAI_KEY", "AZURE_OPENAI_API_KEY")
        deployment = _env("AGENTSHIELD_LIVE_MODEL", "AZURE_OPENAI_DEPLOYMENT")
        if endpoint and key and deployment:
            api_version = _env("AZURE_OPENAI_API_VERSION") or "2024-06-01"
            base = endpoint.rstrip("/")
            url = (
                f"{base}/openai/deployments/{deployment}/chat/completions"
                f"?api-version={api_version}"
            )
            return _OpenAICompatibleAdapter(
                url=url, model=deployment,
                headers={"api-key": key},
                timeout=timeout, max_tokens=max_tokens, temperature=temperature,
                name="azure_openai",
            )
        if forced == "azure_openai":
            raise AdapterError("azure_openai selected but AZURE_OPENAI_ENDPOINT/KEY/DEPLOYMENT are not all set")

    # 3) OpenAI
    if want("openai"):
        key = _env("OPENAI_API_KEY")
        if key:
            base = (_env("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
            model = _env("AGENTSHIELD_LIVE_MODEL", "OPENAI_MODEL") or "gpt-4o-mini"
            return _OpenAICompatibleAdapter(
                url=f"{base}/chat/completions", model=model,
                headers={"Authorization": f"Bearer {key}"},
                timeout=timeout, max_tokens=max_tokens, temperature=temperature,
                name="openai",
            )
        if forced == "openai":
            raise AdapterError("openai selected but OPENAI_API_KEY is not set")

    # 4) Ollama (local, OpenAI-compatible /v1)
    if want("ollama"):
        host = _env("OLLAMA_BASE_URL", "OLLAMA_HOST")
        if host or forced == "ollama":
            base = (host or "http://localhost:11434").rstrip("/")
            if not base.endswith("/v1"):
                base = f"{base}/v1"
            model = _env("AGENTSHIELD_LIVE_MODEL", "OLLAMA_MODEL") or "llama3"
            return _OpenAICompatibleAdapter(
                url=f"{base}/chat/completions", model=model,
                headers={}, timeout=timeout, max_tokens=max_tokens,
                temperature=temperature, name="ollama",
            )

    if forced and forced != "mock":
        raise AdapterError(f"unknown or unconfigured live target: {forced!r}")

    if allow_mock:
        return MockAdapter(behavior=behavior)
    raise AdapterError(
        "no live target configured; set AGENTSHIELD_LIVE_TARGET and the "
        "matching endpoint/key/model env vars"
    )
