"""Pinocchio engine fingerprint (schema ``model-fingerprint/v1``).

Builds an exercise URDF, loads it in the REAL Pinocchio engine with a
free-flyer root and reports what the engine sees, for comparison against the
canonical parity standard (see ``_canonical/conformance.py``).

Engine notes:

* Gravity is not part of URDF. Pinocchio's default ``model.gravity`` is
  ``(0, 0, -9.81)``; :func:`load_model` sets it from the standard
  (9.80665 m/s^2) explicitly, as the repo convention requires.
* Pinocchio has no contact model, so ``ground_friction`` is omitted.
* Barbell and fixture bodies are fixed-joint children that Pinocchio merges
  into their parent joint's inertia; human segment masses are therefore read
  from a second engine model built from the URDF with every fixed-joint
  subtree removed.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from pinocchio_models.model_pack import list_exercises, manifest
from pinocchio_models.shared.parity._canonical import conformance

logger = logging.getLogger(__name__)

ENGINE = "pinocchio"

# Pinocchio joint name -> canonical coordinate name (only names that differ).
COORDINATE_ALIASES: dict[str, str] = {
    **{f"elbow_{s}": f"elbow_{s}_flex" for s in ("l", "r")},
    **{f"knee_{s}": f"knee_{s}_flex" for s in ("l", "r")},
    "neck": "neck_flex",
}

# Pinocchio body (link) name -> canonical segment name; names already match.
SEGMENT_ALIASES: dict[str, str] = {}

# Registry ids of the optimisation objectives that differ from manifest ids.
_OBJECTIVE_IDS: dict[str, str] = {"squat": "back_squat"}


def _canon_segment_names(std: dict[str, Any]) -> set[str]:
    return set(conformance.expected_segments(std))


def _link_of(joint: ET.Element, tag: str) -> str:
    """Return the ``link`` attribute of a joint's ``<parent>``/``<child>``."""
    node = joint.find(tag)
    return "" if node is None else node.get("link", "")


def _strip_fixed_subtrees(urdf: str) -> str:
    """Return *urdf* without fixed joints and the links hanging below them."""
    root = ET.fromstring(urdf)
    joints = root.findall("joint")
    doomed: set[str] = set()
    frontier = [_link_of(j, "child") for j in joints if j.get("type") == "fixed"]
    while frontier:
        link = frontier.pop()
        doomed.add(link)
        frontier += [
            _link_of(j, "child") for j in joints if _link_of(j, "parent") == link
        ]
    for j in joints:
        if j.get("type") == "fixed" or _link_of(j, "child") in doomed:
            root.remove(j)
    for link_el in root.findall("link"):
        if link_el.get("name") in doomed:
            root.remove(link_el)
    return ET.tostring(root, encoding="unicode")


def build_urdf(exercise: str) -> str:
    """Return the URDF string for a manifest exercise id."""
    from pinocchio_models.__main__ import _BUILDERS, _MANIFEST_ID_ALIASES

    if exercise not in list_exercises():
        raise ValueError(f"unknown exercise {exercise!r}")
    return _BUILDERS[_MANIFEST_ID_ALIASES.get(exercise, exercise)]()


def load_model(urdf: str, std: dict[str, Any] | None = None) -> Any:
    """Load *urdf* in Pinocchio with a free-flyer root and standard gravity."""
    import numpy as np
    import pinocchio as pin

    std = std or conformance.load_standard()
    model = pin.buildModelFromXML(urdf, pin.JointModelFreeFlyer())
    model.gravity.linear = np.array([0.0, 0.0, -std["frame"]["gravity_mps2"]])
    return model


def _human_segments(
    urdf: str, std: dict[str, Any]
) -> tuple[dict[str, dict[str, float]], dict[str, list[float]]]:
    """Masses and neutral origins of the human segments, read from the engine."""
    import pinocchio as pin

    model = load_model(_strip_fixed_subtrees(urdf), std)
    data = model.createData()
    pin.forwardKinematics(model, data, pin.neutral(model))
    pin.updateFramePlacements(model, data)
    wanted = _canon_segment_names(std)
    masses: dict[str, dict[str, float]] = {}
    origins: dict[str, list[float]] = {}
    for fid, frame in enumerate(model.frames):
        name = SEGMENT_ALIASES.get(frame.name, frame.name)
        if frame.type != pin.FrameType.BODY or name not in wanted:
            continue
        masses[name] = {"mass_kg": float(model.inertias[frame.parentJoint].mass)}
        origins[name] = [float(v) for v in data.oMf[fid].translation]
    pelvis = origins["pelvis"]
    rel = {
        seg: list(
            conformance.to_canonical(
                std, ENGINE, [p - q for p, q in zip(pos, pelvis, strict=True)]
            )
        )
        for seg, pos in origins.items()
    }
    return masses, rel


def _coordinates(model: Any) -> dict[str, dict[str, list[float]]]:
    out: dict[str, dict[str, list[float]]] = {}
    for jid in range(2, model.njoints):  # 0 = universe, 1 = free-flyer root
        joint = model.joints[jid]
        if joint.nq != 1:
            continue
        name = COORDINATE_ALIASES.get(model.names[jid], model.names[jid])
        q = joint.idx_q
        out[name] = {
            "limits_rad": [
                float(model.lowerPositionLimit[q]),
                float(model.upperPositionLimit[q]),
            ]
        }
    return out


def _capabilities() -> dict[str, str]:
    block = manifest().get("capabilities", {})
    return {key: str(entry["level"]) for key, entry in block.items()}


def _phase_count(exercise: str) -> int | None:
    from pinocchio_models.optimization.objectives.registry import EXERCISE_OBJECTIVES

    objective = EXERCISE_OBJECTIVES.get(_OBJECTIVE_IDS.get(exercise, exercise))
    return None if objective is None else len(objective.phases)


def fingerprint(exercise: str) -> dict[str, Any]:
    """Build *exercise*, load it in Pinocchio and return its fingerprint."""
    std = conformance.load_standard()
    fp: dict[str, Any] = {
        "schema": conformance.FINGERPRINT_SCHEMA,
        "engine": ENGINE,
        "engine_version": None,
        "exercise": exercise,
        "standard_sha256": conformance.standard_sha256(),
        "loaded_in_engine": False,
        "load_error": None,
        "capabilities": _capabilities(),
    }
    try:
        import pinocchio as pin

        fp["engine_version"] = str(pin.__version__)
        urdf = build_urdf(exercise)
        model = load_model(urdf, std)
        segments, origins = _human_segments(urdf, std)
    except Exception as exc:  # noqa: BLE001 - any load failure is reported
        logger.warning("%s failed to load in %s: %s", exercise, ENGINE, exc)
        fp["load_error"] = str(exc)
        return fp
    fp.update(
        loaded_in_engine=True,
        root_joint="free" if model.joints[1].nq == 7 else "fixed",
        gravity_canonical=list(
            conformance.to_canonical(
                std, ENGINE, [float(v) for v in model.gravity.linear]
            )
        ),
        body_mass_kg=sum(s["mass_kg"] for s in segments.values()),
        segments=segments,
        coordinates=_coordinates(model),
        segment_origins_neutral_m=origins,
    )
    phases = _phase_count(exercise)
    if phases is not None:
        fp["phase_count"] = phases
    if not all(math.isfinite(s["mass_kg"]) for s in segments.values()):
        raise ValueError("fingerprint contains non-finite segment mass")
    return fp


def main(argv: list[str] | None = None) -> int:
    """CLI: write fingerprint JSON for one exercise or all of them."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--exercise", choices=list_exercises())
    group.add_argument("--all", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for exercise in list_exercises() if args.all else [args.exercise]:
        path = args.out / f"{ENGINE}_{exercise}.json"
        path.write_text(json.dumps(fingerprint(exercise), indent=2) + "\n")
        logger.info("wrote %s", path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
