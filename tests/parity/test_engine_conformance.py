"""Real-engine load and parity conformance for every manifest exercise.

Not marked ``slow``/``live_simulation``: Pinocchio is a ``dev`` dependency so
this runs in default CI. Closes the engine-parity gap tracked in #423.
"""

from __future__ import annotations

import hashlib
import json
from importlib import resources
from pathlib import Path

import pinocchio as pin
import pytest

import pinocchio_models
from pinocchio_models.__main__ import _BUILDERS, _MANIFEST_ID_ALIASES
from pinocchio_models.model_pack import list_exercises, manifest
from pinocchio_models.shared.parity import fingerprint as fingerprint_module
from pinocchio_models.shared.parity._canonical import conformance
from pinocchio_models.shared.parity.fingerprint import (
    COORDINATE_ALIASES,
    fingerprint,
)

fingerprint_main = fingerprint_module.main

EXERCISES = list_exercises()


def _build_urdf(exercise: str) -> str:
    return _BUILDERS[_MANIFEST_ID_ALIASES.get(exercise, exercise)]()


@pytest.mark.parametrize("exercise", EXERCISES)
def test_exercise_loads_in_real_engine(exercise: str) -> None:
    """Every exercise URDF parses in Pinocchio with a free-flyer root."""
    model = pin.buildModelFromXML(_build_urdf(exercise), pin.JointModelFreeFlyer())
    assert model.nq == 35, "7 (free-flyer) + 28 human coordinates"
    assert model.nv == 34
    assert model.njoints > 29


STD = conformance.load_standard()
LEDGER = (
    Path(pinocchio_models.__file__).parent
    / "shared"
    / "parity"
    / "parity_divergences.json"
)


def _divergences(exercise: str) -> list[conformance.Divergence]:
    fp = fingerprint(exercise)
    assert fp["loaded_in_engine"], fp["load_error"]
    return conformance.check_fingerprint(fp, STD)


@pytest.mark.parametrize("exercise", EXERCISES)
def test_fingerprint_conforms_to_standard(exercise: str) -> None:
    """Every divergence of an exercise must be in the issue-tracked ledger."""
    ledger = conformance.load_ledger(LEDGER)
    unexpected, _ = conformance.reconcile(
        _divergences(exercise), ledger, exercise=exercise
    )
    assert not unexpected, [(d.key, d.message) for d in unexpected]


def test_ledger_has_no_stale_entries() -> None:
    """An entry (or a scoped exercise of one) no exercise still diverges on
    is stale and must go."""
    by_exercise = {ex: _divergences(ex) for ex in EXERCISES}
    _, stale = conformance.reconcile_all(by_exercise, conformance.load_ledger(LEDGER))
    assert not stale, f"stale ledger entries (delete them): {stale}"


def test_fingerprint_reports_engine_sums() -> None:
    fp = fingerprint("squat")
    assert fp["engine"] == "pinocchio"
    assert fp["root_joint"] == "free"
    assert len(fp["segments"]) == 15
    assert len(fp["coordinates"]) == 28
    assert fp["segment_origins_neutral_m"]["pelvis"] == [0.0, 0.0, 0.0]
    assert "ground_friction" not in fp, "Pinocchio has no contact model"


def test_fingerprint_unknown_exercise_reports_load_failure() -> None:
    fp = fingerprint("nope")
    assert fp["loaded_in_engine"] is False
    assert "nope" in fp["load_error"]


def test_cli_writes_fingerprint(tmp_path: Path) -> None:
    assert fingerprint_main(["--exercise", "gait", "--out", str(tmp_path)]) == 0
    data = json.loads((tmp_path / "pinocchio_gait.json").read_text())
    assert data["schema"] == conformance.FINGERPRINT_SCHEMA


def test_aliases_only_map_to_canonical_names() -> None:
    canon = set(conformance.expected_coordinates(STD))
    assert set(COORDINATE_ALIASES.values()) <= canon


def test_capabilities_block_matches_standard() -> None:
    block = manifest()["capabilities"]
    spec = STD["capabilities"]
    assert sorted(block) == sorted(spec["keys"])
    root = Path(pinocchio_models.__file__).parents[2]
    for key, entry in block.items():
        assert entry["level"] in spec["levels"], key
        if entry["evidence"] is not None:
            assert (root / entry["evidence"]).exists(), key


def test_vendored_bundle_matches_manifest_hashes() -> None:
    canon = resources.files("pinocchio_models.shared.parity._canonical")
    sums = json.loads((canon / "MANIFEST.json").read_text(encoding="utf-8"))
    files = sums["files"]
    assert {"assemble.py", "conformance.py"} <= set(files)
    for name, expected in files.items():
        digest = hashlib.sha256((canon / name).read_bytes()).hexdigest()
        assert digest == (
            expected["sha256"] if isinstance(expected, dict) else expected
        )


def test_standard_json_ships_as_package_data() -> None:
    canon = resources.files("pinocchio_models.shared.parity._canonical")
    assert (canon / "biomech_parity_standard.json").is_file()
