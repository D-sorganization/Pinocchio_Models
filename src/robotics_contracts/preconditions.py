"""Generic precondition validators for robotics packages.

All public functions validate inputs and raise :class:`ValueError`
with descriptive messages on violation.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike


def require_positive(value: float, name: str) -> None:
    """Require *value* to be strictly positive."""
    if not math.isfinite(value):
        raise ValueError(f"{name} contains non-finite values")
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def require_non_negative(value: float, name: str) -> None:
    """Require *value* >= 0."""
    if not math.isfinite(value):
        raise ValueError(f"{name} contains non-finite values")
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
    # ⚡ Bolt Optimization: Use exact type checks over isinstance for primitives.
    # Profiling shows this tight loop validation is called millions of times
    # during tree generation, and type() is significantly faster than isinstance().
    # Note: Also checking numpy scalar types to avoid falling back to slow np.asarray.
    arr_type = type(arr)
    if (
        arr_type is float
        or arr_type is int
        or arr_type is np.float64
        or arr_type is np.int64
    ):
        if not math.isfinite(arr):  # type: ignore[arg-type]
            raise ValueError(f"{name} contains non-finite values")
        return
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
