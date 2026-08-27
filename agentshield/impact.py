"""Gate 3: operational impact.

Produces an explanatory operational-impact score that is kept separate from the
assurance score and never used to authorize an action. Unknown dimensions are
treated conservatively (worst-case 4) and recorded as limitations, so missing
evidence is never scored as zero risk.
"""

from __future__ import annotations

from .models import ImpactDimension, OperationalImpact


UNKNOWN_CONSERVATIVE_VALUE = 4


def compute_impact(
    dimensions: list[ImpactDimension],
    *,
    destructive: bool = False,
    irreversible: bool = False,
    fleet_wide: bool = False,
    tier_zero: bool = False,
    identity_impacting: bool = False,
    security_sensitive: bool = False,
    high_data_sensitivity: bool = False,
) -> OperationalImpact:
    if not dimensions:
        raise ValueError("operational impact requires at least one dimension")

    limitations: list[str] = []
    total = 0
    for dim in dimensions:
        if dim.is_unknown():
            limitations.append(
                f"Dimension '{dim.name}' is UNKNOWN; scored conservatively as "
                f"{UNKNOWN_CONSERVATIVE_VALUE}."
            )
            total += UNKNOWN_CONSERVATIVE_VALUE
        else:
            if not 0 <= dim.rating <= 4:
                raise ValueError(f"dimension '{dim.name}' rating must be 0..4")
            total += dim.rating

    score = round(100 * total / (4 * len(dimensions)))

    return OperationalImpact(
        dimensions=dimensions,
        score=score,
        limitations=limitations,
        destructive=destructive,
        irreversible=irreversible,
        fleet_wide=fleet_wide,
        tier_zero=tier_zero,
        identity_impacting=identity_impacting,
        security_sensitive=security_sensitive,
        high_data_sensitivity=high_data_sensitivity,
    )
