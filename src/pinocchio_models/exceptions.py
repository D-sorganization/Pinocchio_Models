# SPDX-License-Identifier: MIT
"""Domain-specific exceptions for Pinocchio model operations.

All errors raised by this package should use (or inherit from)
:class:`PinocchioModelsError` so that consumers can catch domain-specific
problems separately from generic Python built-in exceptions.
"""

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 D-sorganization


class PinocchioModelsError(Exception):
    """Base exception for all Pinocchio model domain errors."""

    pass


class GeometryError(PinocchioModelsError, ValueError):
    """Raised when geometric constraints or computations are violated."""

    pass


class URDFError(PinocchioModelsError, ValueError):
    """Raised when URDF parsing or validation fails."""

    pass