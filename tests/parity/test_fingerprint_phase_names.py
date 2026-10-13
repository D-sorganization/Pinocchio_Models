"""The fingerprint reports the standard's ordered named phases (RM#2025, #425).

Standard v2.0 defines ordered named phases per exercise; since
Repository_Management#2089 ``phase_names`` is a core ``assemble_fingerprint``
field that ``spec.check_fingerprint`` compares in order. These tests prove the
Pinocchio fingerprint reports the names for every exercise, in the standard's
order, and that the objective is resolved through the standard's own
``legacy_key`` rather than a pack-local id table.
"""

from __future__ import annotations

import pytest

from pinocchio_models.shared.parity import fingerprint as fingerprint_mod
from pinocchio_models.shared.parity._canonical import conformance, spec

STD = conformance.load_standard()
EXERCISES = tuple(STD["exercises"])


def test_every_standard_exercise_names_its_phases() -> None:
    """Guard: the vendored standard is v2 for every exercise (non-vacuous)."""
    assert len(EXERCISES) == 7
    for exercise in EXERCISES:
        assert spec.phase_names(STD, exercise), exercise


@pytest.mark.parametrize("exercise", EXERCISES)
def test_objective_phase_names_follow_standard_order(exercise: str) -> None:
    names = fingerprint_mod.objective_phase_names(exercise, STD)
    assert names == spec.phase_names(STD, exercise)
    assert len(names) == STD["exercises"][exercise]["phase_count"]


def test_objective_phase_names_default_to_vendored_standard() -> None:
    assert fingerprint_mod.objective_phase_names("squat") == spec.phase_names(
        STD, "squat"
    )


def test_objective_phase_names_reject_unknown_exercise() -> None:
    with pytest.raises(ValueError, match="unknown exercise"):
        fingerprint_mod.objective_phase_names("curl", STD)


def test_objective_resolved_via_standard_legacy_key() -> None:
    """DRY: ``squat`` -> ``back_squat`` comes from the standard, not a local table."""
    assert STD["exercises"]["squat"]["legacy_key"] == "back_squat"
    assert not hasattr(fingerprint_mod, "_OBJECTIVE_IDS")


@pytest.mark.parametrize("exercise", EXERCISES)
def test_fingerprint_reports_standard_phase_names(exercise: str) -> None:
    pytest.importorskip("pinocchio")
    fp = fingerprint_mod.fingerprint(exercise)
    assert fp["loaded_in_engine"] is True
    assert fp["phase_names"] == spec.phase_names(STD, exercise)
    assert fp["phase_count"] == len(fp["phase_names"])
    assert [f for f in spec.check_fingerprint(fp, STD) if f[0] == "phase_names"] == []
