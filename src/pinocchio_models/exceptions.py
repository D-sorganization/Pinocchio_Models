# SPDX-License-Identifier: MIT
"""Domain-specific exceptions for Pinocchio model operations.

All errors raised by this package should use (or inherit from)
:class:`PinocchioModelsError` so that consumers can catch domain-specific
problems separately from generic Python built-in exceptions.
"""

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 D-sorganization


class PinocchioModelsError(Exception):
    """Base exception for all Pinocchio model domain errors.

    Attributes:
        error_code: Machine-readable error identifier (e.g., ``PM001``).
    """

    def __init__(self, message: str, *, error_code: str | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code or self._default_error_code()
        self.message = message

    def _default_error_code(self) -> str:
        """Return the default error code for this exception class."""
        return "PM000"

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class GeometryError(PinocchioModelsError, ValueError):
    """Raised when geometric constraints or computations are violated."""

    def _default_error_code(self) -> str:
        return "PM001"


class URDFError(PinocchioModelsError, ValueError):
    """Raised when URDF parsing or validation fails."""

    def _default_error_code(self) -> str:
        return "PM002"


class ConfigurationError(PinocchioModelsError, ValueError):
    """Raised when model configuration is invalid."""

    def _default_error_code(self) -> str:
        return "PM003"


class OptimizationError(PinocchioModelsError, RuntimeError):
    """Raised when trajectory optimization fails to converge."""

    def _default_error_code(self) -> str:
        return "PM004"


class AddonError(PinocchioModelsError, ImportError):
    """Raised when an optional addon dependency is missing or incompatible."""

    def _default_error_code(self) -> str:
        return "PM005"
