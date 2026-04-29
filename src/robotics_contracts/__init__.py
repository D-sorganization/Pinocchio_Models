"""Shared design-by-contract guards for robotics packages.

Provides generic precondition and postcondition validators that raise
standard :class:`ValueError` on violations.  Consumers typically wrap
these with domain-specific exceptions.
"""

from robotics_contracts.postconditions import (
    ensure_positive_definite_inertia,
    ensure_positive_mass,
)
from robotics_contracts.preconditions import (
    require_finite,
    require_in_range,
    require_non_negative,
    require_positive,
    require_shape,
    require_unit_vector,
)

__all__ = [
    "ensure_positive_definite_inertia",
    "ensure_positive_mass",
    "require_finite",
    "require_in_range",
    "require_non_negative",
    "require_positive",
    "require_shape",
    "require_unit_vector",
]
