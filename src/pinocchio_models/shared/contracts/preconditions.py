"""Design-by-Contract precondition checks — Pinocchio_Models wrapper.

Re-exports the generic :mod:`robotics_contracts.preconditions` guards,
wrapping them with domain-specific :class:`URDFError` exceptions for
backward compatibility.

Migration note:
    Direct callers can switch to ``from robotics_contracts.preconditions import ...``
    and use ``ValueError`` directly, dropping the URDFError wrapper.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import ArrayLike

from pinocchio_models.exceptions import URDFError

if TYPE_CHECKING:
    from robotics_contracts.preconditions import (  # noqa: F401
        require_finite,
        require_in_range,
        require_non_negative,
        require_positive,
        require_shape,
        require_unit_vector,
    )


def require_positive(value: float, name: str) -> None:
    """Require *value* to be strictly positive."""
    try:
        import robotics_contracts.preconditions as _rc

        _rc.require_positive(value, name)
    except ValueError as exc:
        raise URDFError(str(exc), error_code="PM101") from exc


def require_non_negative(value: float, name: str) -> None:
    """Require *value* >= 0."""
    try:
        import robotics_contracts.preconditions as _rc

        _rc.require_non_negative(value, name)
    except ValueError as exc:
        raise URDFError(str(exc), error_code="PM102") from exc


def require_unit_vector(vec: ArrayLike, name: str, tol: float = 1e-6) -> None:
    """Require *vec* to have unit norm within *tol*."""
    arr = np.asarray(vec, dtype=float)
    if arr.shape != (3,):
        raise URDFError(
            f"{name} must be a 3-vector, got shape {arr.shape}",
            error_code="PM103",
        )
    norm = float(np.linalg.norm(arr))
    if abs(norm - 1.0) > tol:
        raise URDFError(
            f"{name} must be unit-length (norm={norm:.6f})",
            error_code="PM104",
        )


def require_finite(arr: ArrayLike, name: str) -> None:
    """Require all elements of *arr* to be finite (no NaN/Inf)."""
    try:
        import robotics_contracts.preconditions as _rc

        _rc.require_finite(arr, name)
    except ValueError as exc:
        raise URDFError(str(exc), error_code="PM105") from exc


def require_in_range(value: float, low: float, high: float, name: str) -> None:
    """Require *low* <= *value* <= *high*."""
    try:
        import robotics_contracts.preconditions as _rc

        _rc.require_in_range(value, low, high, name)
    except ValueError as exc:
        raise URDFError(str(exc), error_code="PM106") from exc


def require_shape(arr: ArrayLike, expected: tuple[int, ...], name: str) -> None:
    """Require *arr* to have the given shape."""
    try:
        import robotics_contracts.preconditions as _rc

        _rc.require_shape(arr, expected, name)
    except ValueError as exc:
        raise URDFError(str(exc), error_code="PM107") from exc


def require_valid_urdf_string(urdf_str: str) -> None:
    """Validate that *urdf_str* is a well-formed URDF XML string.

    Performs lightweight checks before dispatching to Pinocchio's
    ``buildModelFromXML``, which gives opaque C++ errors on bad input.

    Checks:
    1. Non-empty string
    2. Parseable XML
    3. Root element is ``<robot>``

    Raises :class:`ValueError` with a descriptive message on failure.
    """
    if not urdf_str or not urdf_str.strip():
        raise URDFError(
            "URDF string must not be empty",
            error_code="PM108",
        )

    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(urdf_str)  # nosec B314 -- validating input
    except ET.ParseError as exc:
        raise URDFError(
            f"URDF string is not valid XML: {exc}",
            error_code="PM109",
        ) from exc

    if root.tag != "robot":
        raise URDFError(
            f"URDF root element must be <robot>, got <{root.tag}>",
            error_code="PM110",
        )


def require_valid_exercise_name(exercise_name: str) -> None:
    """Require *exercise_name* to be one of the recognised exercises.

    Raises :class:`ValueError` with a descriptive message listing the
    valid options when the name is not recognised.
    """
    from pinocchio_models.shared.constants import VALID_EXERCISE_NAMES

    if exercise_name not in VALID_EXERCISE_NAMES:
        raise URDFError(
            f"Unknown exercise '{exercise_name}'. "
            f"Valid names: {sorted(VALID_EXERCISE_NAMES)}",
            error_code="PM111",
        )
