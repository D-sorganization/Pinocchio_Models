# SPDX-License-Identifier: MIT
"""Unit tests for the custom exception hierarchy."""

import pytest

from pinocchio_models.exceptions import (
    GeometryError,
    PinocchioModelsError,
    URDFError,
)


def test_exception_inheritance() -> None:
    """All domain exceptions inherit from PinocchioModelsError."""
    assert issubclass(GeometryError, PinocchioModelsError)
    assert issubclass(URDFError, PinocchioModelsError)
    assert issubclass(PinocchioModelsError, Exception)


def test_geometry_error_is_value_error() -> None:
    """GeometryError inherits from ValueError for backward compatibility."""
    assert issubclass(GeometryError, ValueError)


def test_urdf_error_is_value_error() -> None:
    """URDFError inherits from ValueError for backward compatibility."""
    assert issubclass(URDFError, ValueError)


def test_can_catch_with_base_class() -> None:
    """Catching PinocchioModelsError catches all domain exceptions."""
    with pytest.raises(PinocchioModelsError):
        raise GeometryError("test")

    with pytest.raises(PinocchioModelsError):
        raise URDFError("test")


def test_can_catch_with_value_error() -> None:
    """Catching ValueError catches domain exceptions for backward compatibility."""
    with pytest.raises(ValueError):
        raise GeometryError("test")

    with pytest.raises(ValueError):
        raise URDFError("test")
