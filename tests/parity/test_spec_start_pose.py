"""Every barbell lift starts at its spec ``start`` via-pose (UpstreamDrift#11743).

LIFT-3: the generated models no longer carry pack-local start-pose literals.
Joint coordinates, the pelvis root placement and the bar position at the start
come from the vendored exercise spec (``biomech_parity_standard.json`` v2.1),
and the real Pinocchio engine must reproduce them: the bar where the spec puts
it (pulls on the floor at plate radius), feet flat on the floor at the spec
stance, both palm centres on the bar, the spec masses, and the combined
lifter-plus-bar centre of mass over mid-foot.

Every model here is built at the spec load (``load.plates_per_side_kg``) and
the spec lifter (``anthropometrics``), so it is the configuration the spec's
own reference forward kinematics describes. Tolerances come from the
standard's ``tolerances`` block, except the 5 mm hand-bar closure bound of the
LIFT-3 acceptance (UpstreamDrift#11743) and an exact-construction bound for
quantities the generator places directly.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET

import numpy as np
import pinocchio as pin
import pytest

from pinocchio_models.exercises.base import ExerciseConfig
from pinocchio_models.exercises.bench_press.bench_press_model import (
    BenchPressModelBuilder,
)
from pinocchio_models.exercises.clean_and_jerk.clean_and_jerk_model import (
    CleanAndJerkModelBuilder,
)
from pinocchio_models.exercises.deadlift.deadlift_model import DeadliftModelBuilder
from pinocchio_models.exercises.snatch.snatch_model import SnatchModelBuilder
from pinocchio_models.exercises.spec_lift import SpecLiftBuilder
from pinocchio_models.exercises.squat.squat_model import SquatModelBuilder
from pinocchio_models.shared.barbell import BarbellSpec
from pinocchio_models.shared.barbell.barbell_model import PLATE_OUTER_RADIUS_M
from pinocchio_models.shared.body import BodyModelSpec
from pinocchio_models.shared.contact.contact_model import get_exercise_contacts
from pinocchio_models.shared.parity._canonical import conformance, spec, topology
from pinocchio_models.shared.parity.fingerprint import COORDINATE_ALIASES, load_model
from pinocchio_models.shared.utils.urdf_helpers import get_initial_configuration

STD = conformance.load_standard()
TOL = STD["tolerances"]
ANTHRO = STD["anthropometrics"]

# The generator places the root, the bar and the joint angles directly, so the
# engine must reproduce them to the URDF's 6-decimal serialisation (``float_str``),
# not merely to the 2 cm cross-engine tolerance.
_EXACT_M = 1e-5
# LIFT-3 acceptance (UpstreamDrift#11743): palm centre to bar grip point.
_HAND_BAR_CLOSURE_M = 0.005

BUILDERS: dict[str, type[SpecLiftBuilder]] = {
    "squat": SquatModelBuilder,
    "deadlift": DeadliftModelBuilder,
    "bench_press": BenchPressModelBuilder,
    "snatch": SnatchModelBuilder,
    "clean_and_jerk": CleanAndJerkModelBuilder,
}
LIFTS = tuple(BUILDERS)
# Pulls start with the loaded bar resting on the floor (UpstreamDrift#11743).
PULLS = ("deadlift", "snatch", "clean_and_jerk")
# Supine on the bench: the bench, not the feet, carries the lifter.
STANDING = tuple(ex for ex in LIFTS if ex != "bench_press")


def _start(exercise: str) -> dict:
    return spec.exercise_spec(STD, exercise)["via_poses"]["start"]


def _plates(exercise: str) -> float:
    return float(spec.exercise_spec(STD, exercise)["load"]["plates_per_side_kg"])


def _builder(exercise: str) -> SpecLiftBuilder:
    """The lift at the spec lifter and the spec load."""
    config = ExerciseConfig(
        body_spec=BodyModelSpec(
            total_mass=float(ANTHRO["body_mass_kg"]), height=float(ANTHRO["height_m"])
        ),
        barbell_spec=BarbellSpec.mens_olympic(plate_mass_per_side=_plates(exercise)),
    )
    return BUILDERS[exercise](config)


class _Posed:
    """Generated model of one lift, loaded in Pinocchio at its initial q."""

    def __init__(self, exercise: str) -> None:
        self.urdf = _builder(exercise).build()
        self.model = load_model(self.urdf, STD)
        self.data = self.model.createData()
        self.q0 = get_initial_configuration(self.model, self.urdf)
        pin.forwardKinematics(self.model, self.data, self.q0)
        pin.updateFramePlacements(self.model, self.data)

    def frame(self, name: str) -> pin.SE3:
        return self.data.oMf[self.model.getFrameId(name)]

    def coordinate(self, canonical: str) -> float:
        engine = {v: k for k, v in COORDINATE_ALIASES.items()}.get(canonical, canonical)
        joint = self.model.joints[self.model.getJointId(engine)]
        return float(self.q0[joint.idx_q])

    def centre_of_mass(self) -> np.ndarray:
        return np.asarray(pin.centerOfMass(self.model, self.data, self.q0))


_CACHE: dict[str, _Posed] = {}


def _posed(exercise: str) -> _Posed:
    if exercise not in _CACHE:
        _CACHE[exercise] = _Posed(exercise)
    return _CACHE[exercise]


@pytest.mark.parametrize("exercise", LIFTS)
def test_start_coordinates_equal_the_spec_start(exercise: str) -> None:
    """Every coordinate equals the spec start; unlisted coordinates are 0."""
    want = dict.fromkeys(conformance.expected_coordinates(STD), 0.0)
    want.update(spec.pose_coordinates(STD, exercise, "start"))
    posed = _posed(exercise)
    off = {
        name: (posed.coordinate(name), value)
        for name, value in want.items()
        if abs(posed.coordinate(name) - value) > TOL["limit_abs_rad"]
    }
    assert not off, f"{exercise}: (generated, spec) rad {off}"


@pytest.mark.parametrize("exercise", LIFTS)
def test_pelvis_root_is_the_spec_start_root(exercise: str) -> None:
    root = _start(exercise)["root"]
    pelvis = _posed(exercise).frame("pelvis")
    gap = np.linalg.norm(pelvis.translation - np.array(root["position_m"]))
    turn = np.abs(
        pelvis.rotation - np.array(topology.rpy_matrix(root["orientation_rpy_rad"]))
    ).max()
    assert gap <= _EXACT_M, f"{exercise}: pelvis {gap:.2e} m off the spec root"
    assert turn <= _EXACT_M, f"{exercise}: pelvis rotation off by {turn:.2e}"


@pytest.mark.parametrize("exercise", LIFTS)
def test_bar_starts_level_at_the_spec_bar_position(exercise: str) -> None:
    shaft = _posed(exercise).frame("barbell_shaft")
    gap = np.linalg.norm(
        shaft.translation - np.array(_start(exercise)["bar_position_m"])
    )
    assert gap <= _EXACT_M, f"{exercise}: bar centre {gap:.2e} m off the spec"
    assert np.abs(shaft.rotation - np.eye(3)).max() <= _EXACT_M, "bar not level"


@pytest.mark.parametrize("exercise", PULLS)
def test_pull_bar_rests_on_the_floor_at_plate_radius(exercise: str) -> None:
    radius = spec.exercise_spec(STD, exercise)["load"]["plate_diameter_m"] / 2.0
    assert radius == pytest.approx(PLATE_OUTER_RADIUS_M)
    z = float(_posed(exercise).frame("barbell_shaft").translation[2])
    assert abs(z - radius) <= _EXACT_M, f"{exercise}: bar centre z={z:.6f} m"


@pytest.mark.parametrize("exercise", LIFTS)
@pytest.mark.parametrize("side,sign", [("l", 1.0), ("r", -1.0)])
def test_feet_are_flat_on_the_floor_at_the_spec_stance(
    exercise: str, side: str, sign: float
) -> None:
    """Ankle at its stance point, sole (foot.length below it) on z = 0, flat."""
    stance = spec.exercise_spec(STD, exercise)["stance"]
    ankle_height = topology.dimension(STD, "foot.length")
    foot = _posed(exercise).frame(f"foot_{side}")
    want = np.array(
        [
            STD["pose_frame"]["ankle_x_m"],
            sign * stance["foot_width_m"] / 2,
            ankle_height,
        ]
    )
    gap = np.linalg.norm(foot.translation - want)
    assert gap <= TOL["cross_engine_position_abs_m"], f"ankle {gap:.4f} m off"
    sole_z = float(foot.translation[2]) - ankle_height
    assert abs(sole_z) <= TOL["cross_engine_position_abs_m"], f"sole z={sole_z:.4f}"
    flat = np.array(
        topology.rpy_matrix((0.0, 0.0, sign * math.radians(stance["toe_out_deg"])))
    )
    tilt = np.abs(foot.rotation - flat).max()
    assert tilt <= TOL["axis_angle_abs_rad"], f"foot not flat ({tilt:.4f})"


@pytest.mark.parametrize("exercise", LIFTS)
@pytest.mark.parametrize("side,sign", [("l", 1.0), ("r", -1.0)])
def test_palm_centres_close_on_the_bar(exercise: str, side: str, sign: float) -> None:
    """Both hands hold the bar at the spec grip width (palm centre, #2060)."""
    posed = _posed(exercise)
    factor, term = STD["grip_point"]["origin"]["z"]
    hand = posed.frame(f"hand_{side}")
    palm = hand.translation + hand.rotation @ np.array(
        [0.0, 0.0, factor * topology.dimension(STD, term)]
    )
    shaft = posed.frame("barbell_shaft")
    half = spec.exercise_spec(STD, exercise)["grip"]["width_m"] / 2.0
    grip = shaft.translation + shaft.rotation @ np.array([0.0, sign * half, 0.0])
    gap = float(np.linalg.norm(palm - grip))
    assert gap <= _HAND_BAR_CLOSURE_M, f"{exercise}/{side}: palm {gap * 1e3:.2f} mm"


def _urdf_masses(urdf: str) -> dict[str, float]:
    root = ET.fromstring(urdf)  # nosec B314 -- generated by this package
    return {
        link.get("name", ""): float(link.find("inertial/mass").get("value", "0"))  # type: ignore[union-attr]
        for link in root.findall("link")
        if link.find("inertial/mass") is not None
    }


@pytest.mark.parametrize("exercise", LIFTS)
def test_lifter_and_barbell_masses_are_the_spec_masses(exercise: str) -> None:
    masses = _urdf_masses(_posed(exercise).urdf)
    body = float(ANTHRO["body_mass_kg"])
    human = 0.0
    for name, segment in ANTHRO["segments"].items():
        for link in (f"{name}_l", f"{name}_r") if segment["bilateral"] else (name,):
            assert masses[link] == pytest.approx(
                segment["mass_frac"] * body, rel=TOL["mass_rel"]
            ), link
            human += masses[link]
    assert human == pytest.approx(body, rel=TOL["mass_rel"])
    bar = sum(m for name, m in masses.items() if name.startswith("barbell_"))
    want_bar = STD["barbell"]["mens"]["bar_mass_kg"] + 2.0 * _plates(exercise)
    assert bar == pytest.approx(want_bar, rel=TOL["mass_rel"])
    total = pin.computeTotalMass(_posed(exercise).model)
    assert total == pytest.approx(body + want_bar, rel=TOL["mass_rel"])


@pytest.mark.parametrize("exercise", STANDING)
def test_combined_centre_of_mass_is_over_mid_foot(exercise: str) -> None:
    """Lifter plus loaded bar balance over mid-foot (the pose_frame origin)."""
    com = _posed(exercise).centre_of_mass()
    offset = float(np.hypot(com[0], com[1]))
    assert offset <= TOL["cross_engine_position_abs_m"], (
        f"{exercise}: combined CoM {com.round(4).tolist()} is {offset:.4f} m "
        "from mid-foot"
    )


@pytest.mark.parametrize("exercise", LIFTS)
def test_foot_contacts_and_collision_sole_on_floor_at_start_pose(
    exercise: str,
) -> None:
    """Foot contact points and sole collision bottom rest on z = 0 at start pose."""
    posed = _posed(exercise)
    contacts = get_exercise_contacts(exercise)
    assert contacts.foot_contacts, f"{exercise}: no foot contacts defined"

    for cp in contacts.foot_contacts:
        p_world = posed.frame(cp.frame_name).act(np.array(cp.local_position))
        assert abs(p_world[2]) <= TOL["cross_engine_position_abs_m"], (
            f"{exercise} {cp.frame_name} contact z={p_world[2]:.4f} m (want 0)"
        )

    root = ET.fromstring(posed.urdf)
    for side in ("l", "r"):
        collision = root.find(f".//link[@name='foot_{side}']/collision")
        assert collision is not None, f"foot_{side} collision missing"
        origin = collision.find("origin")
        assert origin is not None, f"foot_{side} collision origin missing"
        box = collision.find("geometry/box")
        assert box is not None, f"foot_{side} collision box missing"

        origin_xyz = [float(v) for v in origin.get("xyz", "0 0 0").split()]
        size_xyz = [float(v) for v in box.get("size", "0 0 0").split()]
        bottom_local = np.array(
            [origin_xyz[0], origin_xyz[1], origin_xyz[2] - size_xyz[2] / 2.0]
        )
        bottom_world = posed.frame(f"foot_{side}").act(bottom_local)
        assert abs(bottom_world[2]) <= TOL["cross_engine_position_abs_m"], (
            f"{exercise} foot_{side} collision bottom z={bottom_world[2]:.4f} m (want 0)"
        )
