"""Entra ID identity provider adapter (offline mock).

Maps Microsoft Entra ID-shaped token claims onto AgentShield's
:class:`IdentityContext`, so Gate 2 (identity and assurance context) can be
driven by a real enterprise identity rather than a hand-built mock.

This adapter validates *no* tokens and calls *no* Microsoft Graph endpoint. It
accepts an already-decoded claims dictionary (as an app would receive after
Entra performed authentication) and translates it. Swapping in a real
implementation means validating the JWT and calling Graph behind the same
:class:`IdentityProvider` interface.
"""

from __future__ import annotations

from typing import Optional

from ..models import IdentityContext, Lifecycle

# Entra ``accountEnabled`` / risk state -> AgentShield lifecycle.
_ACCOUNT_STATE_TO_LIFECYCLE = {
    "enabled": Lifecycle.ACTIVE,
    "atRisk": Lifecycle.REVIEW,
    "confirmedCompromised": Lifecycle.QUARANTINED,
    "disabled": Lifecycle.QUARANTINED,
}


def entra_claims_to_identity(
    claims: dict,
    *,
    capability_claim: str = "roles",
) -> IdentityContext:
    """Translate decoded Entra claims into an :class:`IdentityContext`.

    Recognized claims (all optional, mapped defensively):
      - ``oid`` / ``sub``      -> requester_id
      - ``idtyp``              -> requester_type (``app`` => service principal)
      - ``roles`` / ``scp``    -> permitted_capabilities
      - ``account_state``      -> lifecycle (custom claim in this mock)
      - ``owner`` / ``sponsor``-> accountability
      - ``assurance_age_days`` -> assurance freshness (custom claim in this mock)
    """

    requester_id = claims.get("oid") or claims.get("sub") or ""
    known = bool(requester_id)
    idtyp = (claims.get("idtyp") or "").lower()
    requester_type = "service-principal" if idtyp == "app" else "user"

    caps = claims.get(capability_claim)
    if isinstance(caps, str):
        capabilities = [c for c in caps.replace(",", " ").split() if c]
    elif isinstance(caps, (list, tuple)):
        capabilities = list(caps)
    else:
        capabilities = []

    state = (claims.get("account_state") or "enabled")
    lifecycle = _ACCOUNT_STATE_TO_LIFECYCLE.get(state, Lifecycle.UNKNOWN)

    age = claims.get("assurance_age_days")
    try:
        assurance_age = float(age) if age is not None else None
    except (TypeError, ValueError):
        assurance_age = None

    return IdentityContext(
        requester_id=requester_id or "unknown",
        known=known,
        requester_type=requester_type,
        lifecycle=lifecycle,
        owner=claims.get("owner"),
        sponsor=claims.get("sponsor"),
        platform="Entra ID",
        permitted_capabilities=capabilities,
        assurance_age_days=assurance_age,
        tool_manifest_changed=bool(claims.get("tool_manifest_changed", False)),
    )


class EntraIdentityProvider:
    """Offline ``IdentityProvider`` backed by a supplied claims table.

    In production this class would validate the presented Entra token and query
    Microsoft Graph. Here it resolves against an in-memory claims directory so
    the workflow can be exercised without any network or credential.
    """

    def __init__(self, directory: Optional[dict[str, dict]] = None) -> None:
        self._directory = directory or {}

    def add(self, requester_id: str, claims: dict) -> None:
        self._directory[requester_id] = claims

    def resolve(self, requester_id: str) -> IdentityContext:
        claims = self._directory.get(requester_id)
        if claims is None:
            # Fail closed: unknown identity is not silently trusted.
            return IdentityContext(
                requester_id=requester_id,
                known=False,
                requester_type="unknown",
                lifecycle=Lifecycle.UNKNOWN,
                owner=None,
                sponsor=None,
                platform="Entra ID",
                permitted_capabilities=[],
            )
        # Ensure the id is present for translation.
        claims = {**claims, "oid": claims.get("oid", requester_id)}
        return entra_claims_to_identity(claims)
