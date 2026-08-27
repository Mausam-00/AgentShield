"""Microsoft-ecosystem integration adapters (offline mocks).

These adapters show *where* AgentShield plugs into the Microsoft security stack.
They implement the package's provider interfaces with the shape of the real
services, but contact no network and require no credentials - consistent with
AgentShield's mock-only, ``CONTROLLED LIVE``-disabled design. A production
deployment would swap these for authenticated implementations behind the same
interfaces.
"""

from .entra import EntraIdentityProvider, entra_claims_to_identity  # noqa: F401
from .content_safety import (  # noqa: F401
    ContentSafetyPromptShield,
    ShieldVerdict,
)

__all__ = [
    "EntraIdentityProvider",
    "entra_claims_to_identity",
    "ContentSafetyPromptShield",
    "ShieldVerdict",
]
