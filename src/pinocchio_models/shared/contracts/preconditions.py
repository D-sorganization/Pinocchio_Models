# NOTE: The six core require_* functions in this module (require_positive,
# require_non_negative, require_unit_vector, require_finite, require_in_range,
# require_shape) are duplicated verbatim across Pinocchio_Models, MuJoCo_Models,
# and OpenSim_Models.  The duplication is intentional: each repo is an
# independent deployable and a cross-repo shared package adds coordination
# overhead that is not yet warranted.  If that changes, see
# D-sorganization/Pinocchio_Models#104 for context and migration options.

"""Design-by-Contract precondition checks.

All public functions in this project validate inputs via these guards.
Violations raise ValueError with descriptive messages — never silently
accept invalid geometry or physics parameters.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def require_positive(value: float, name: str) -> None:
    """Require *value* to be strictly positive."""
    require_finite(value, name)
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def require_non_negative(value: float, name: str) -> None:
    """Require *value* >= 0."""
    require_finite(value, name)
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")


def require_unit_vector(vec: ArrayLike, name: str, tol: float = 1e-6) -> None:
    """Require *vec* to have unit norm within *tol*."""
    arr = np.asarray(vec, dtype=float)
    if arr.shape != (3,):
        raise ValueError(f"{name} must be a 3-vector, got shape {arr.shape}")
    norm = float(np.linalg.norm(arr))
    if abs(norm - 1.0) > tol:
        raise ValueError(f"{name} must be unit-length (norm={norm:.6f})")


def require_finite(arr: ArrayLike, name: str) -> None:
    """Require all elements of *arr* to be finite (no NaN/Inf)."""
    a = np.asarray(arr, dtype=float)
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{name} contains non-finite values")


def require_in_range(value: float, low: float, high: float, name: str) -> None:
    """Require *low* <= *value* <= *high*."""
    if not (low <= value <= high):
        raise ValueError(f"{name} must be in [{low}, {high}], got {value}")


def require_shape(arr: ArrayLike, expected: tuple[int, ...], name: str) -> None:
    """Require *arr* to have the given shape."""
    a = np.asarray(arr)
    if a.shape != expected:
        raise ValueError(f"{name} must have shape {expected}, got {a.shape}")


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
        raise ValueError("URDF string must not be empty")

    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(urdf_str)  # nosec B314 -- validating input
    except ET.ParseError as exc:
        raise ValueError(f"URDF string is not valid XML: {exc}") from exc

    if root.tag != "robot":
        raise ValueError(f"URDF root element must be <robot>, got <{root.tag}>")


def require_valid_exercise_name(exercise_name: str) -> None:
    """Require *exercise_name* to be one of the recognised exercises.

    Raises :class:`ValueError` with a descriptive message listing the
    valid options when the name is not recognised.
    """
    from pinocchio_models.shared.constants import VALID_EXERCISE_NAMES

    if exercise_name not in VALID_EXERCISE_NAMES:
        raise ValueError(
            f"Unknown exercise '{exercise_name}'. "
            f"Valid names: {sorted(VALID_EXERCISE_NAMES)}"
        )
