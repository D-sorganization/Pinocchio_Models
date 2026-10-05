"""Cross-repo parity standard — canonical biomechanical parameters.

Every value here is computed from the vendored canonical bundle
(``_canonical/biomech_parity_standard.json``, loaded through
``conformance.load_standard``), which is the single source of truth shared by
all model packs. The names below are the legacy public dict/tuple forms kept
for existing importers.

``JOINT_LIMITS`` is the *standard's* limits, not the limits the URDF builder
emits (those live in ``shared/constants.py``); known differences are recorded
in ``parity_divergences.json``.
"""

from __future__ import annotations

import math
from typing import Any

from pinocchio_models.shared.parity._canonical.conformance import load_standard

_STD: dict[str, Any] = load_standard()
_ANTHRO: dict[str, Any] = _STD["anthropometrics"]
_SEGMENTS: dict[str, dict[str, Any]] = _ANTHRO["segments"]

STANDARD_BODY_MASS: float = float(_ANTHRO["body_mass_kg"])
STANDARD_HEIGHT: float = float(_ANTHRO["height_m"])

SEGMENT_MASS_FRACTIONS: dict[str, float] = {
    name: float(seg["mass_frac"]) for name, seg in _SEGMENTS.items()
}

SEGMENT_LENGTH_FRACTIONS: dict[str, float] = {
    name: float(seg["length_frac"]) for name, seg in _SEGMENTS.items()
}

# Coordinate names use a ``{side}`` placeholder for bilateral joints; the
# legacy key drops it (``hip_{side}_flex`` -> ``hip_flex``).
JOINT_LIMITS: dict[str, tuple[float, float]] = {
    coord["name"].replace("_{side}", ""): (
        math.radians(coord["limits_deg"][0]),
        math.radians(coord["limits_deg"][1]),
    )
    for coord in _STD["coordinates"]
}

_BARBELL: dict[str, float] = _STD["barbell"]["mens"]
MENS_BARBELL: dict[str, float] = {
    "total_length": _BARBELL["total_length_m"],
    "shaft_length": _BARBELL["shaft_length_m"],
    "shaft_diameter": _BARBELL["shaft_diameter_m"],
    "sleeve_diameter": _BARBELL["sleeve_diameter_m"],
    "bar_mass": _BARBELL["bar_mass_kg"],
}

FOOT_CONTACT_DIMS: dict[str, float] = dict(_STD["contact"]["foot_box_m"])

GROUND_FRICTION: dict[str, float] = {
    key: float(_STD["contact"]["ground_friction"][key]) for key in ("static", "dynamic")
}

# Keyed by the objective registry ids (``back_squat`` for the standard's
# ``squat``, via its ``legacy_key``).
EXERCISE_PHASE_COUNTS: dict[str, int] = {
    str(ex.get("legacy_key", name)): int(ex["phase_count"])
    for name, ex in _STD["exercises"].items()
}

GRAVITY: tuple[float, float, float] = (0.0, 0.0, -float(_STD["frame"]["gravity_mps2"]))
