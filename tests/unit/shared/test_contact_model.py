"""Tests for contact point and contact specification models."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.shared.body.body_model import create_full_body
from pinocchio_models.shared.contact.contact_model import (
    ContactPoint,
    ContactSpec,
    get_exercise_contacts,
)


class TestContactPoint:
    def test_creation_defaults(self) -> None:
        cp = ContactPoint(frame_name="foot_l", local_position=(0.0, 0.0, -0.01))
        assert cp.frame_name == "foot_l"
        assert cp.local_position == (0.0, 0.0, -0.01)
        assert cp.normal == (0.0, 0.0, 1.0)
        assert cp.mu == 0.8

    def test_creation_custom(self) -> None:
        cp = ContactPoint(
            frame_name="hand_r",
            local_position=(0.1, 0.0, 0.0),
            normal=(1.0, 0.0, 0.0),
            mu=0.5,
        )
        assert cp.normal == (1.0, 0.0, 0.0)
        assert cp.mu == 0.5

    def test_frozen(self) -> None:
        cp = ContactPoint(frame_name="foot_l", local_position=(0.0, 0.0, 0.0))
        with pytest.raises(AttributeError):
            cp.mu = 1.0  # type: ignore


class TestContactSpec:
    def test_empty_spec(self) -> None:
        spec = ContactSpec()
        assert spec.foot_contacts == []
        assert spec.bench_contact is None
        assert spec.barbell_contacts is None

    def test_with_foot_contacts(self) -> None:
        contacts = [
            ContactPoint(frame_name="foot_l", local_position=(0.0, 0.0, -0.01)),
            ContactPoint(frame_name="foot_r", local_position=(0.0, 0.0, -0.01)),
        ]
        spec = ContactSpec(foot_contacts=contacts)
        assert len(spec.foot_contacts) == 2

    def test_frozen(self) -> None:
        spec = ContactSpec()
        with pytest.raises(AttributeError):
            spec.bench_contact = ContactPoint(  # type: ignore
                frame_name="torso", local_position=(0.0, 0.0, 0.0)
            )


class TestGetExerciseContacts:
    def test_rejects_unknown_exercise(self) -> None:
        with pytest.raises(ValueError, match="Unknown exercise"):
            get_exercise_contacts("jumping_jacks")

    @pytest.mark.parametrize(
        "exercise",
        ["back_squat", "bench_press", "deadlift", "snatch", "clean_and_jerk"],
    )
    def test_returns_eight_foot_contacts(self, exercise: str) -> None:
        """4 corners per foot x 2 feet = 8 foot contacts."""
        spec = get_exercise_contacts(exercise)
        assert len(spec.foot_contacts) == 8

    def test_foot_contacts_use_correct_frames(self) -> None:
        spec = get_exercise_contacts("back_squat")
        frames = {cp.frame_name for cp in spec.foot_contacts}
        assert frames == {"foot_l", "foot_r"}

    def test_foot_contact_z_offset_negative(self) -> None:
        """All foot contacts should be at or below foot frame origin."""
        spec = get_exercise_contacts("back_squat")
        for cp in spec.foot_contacts:
            assert cp.local_position[2] < 0

    def test_bench_press_has_bench_contact(self) -> None:
        spec = get_exercise_contacts("bench_press")
        assert spec.bench_contact is not None
        assert spec.bench_contact.frame_name == "torso"

    def test_squat_no_bench_contact(self) -> None:
        spec = get_exercise_contacts("back_squat")
        assert spec.bench_contact is None

    def test_deadlift_has_barbell_contacts(self) -> None:
        spec = get_exercise_contacts("deadlift")
        assert spec.barbell_contacts is not None
        assert len(spec.barbell_contacts) == 2
        frames = {cp.frame_name for cp in spec.barbell_contacts}
        assert frames == {"hand_l", "hand_r"}

    def test_snatch_has_barbell_contacts(self) -> None:
        spec = get_exercise_contacts("snatch")
        assert spec.barbell_contacts is not None

    def test_clean_and_jerk_has_barbell_contacts(self) -> None:
        spec = get_exercise_contacts("clean_and_jerk")
        assert spec.barbell_contacts is not None

    def test_squat_no_barbell_contacts(self) -> None:
        spec = get_exercise_contacts("back_squat")
        assert spec.barbell_contacts is None

    def test_default_friction_coefficient(self) -> None:
        spec = get_exercise_contacts("back_squat")
        for cp in spec.foot_contacts:
            assert cp.mu == 0.8

    def test_model_param_accepted(self) -> None:
        """Passing model=None (or any object) should not crash."""
        spec = get_exercise_contacts("back_squat", model=None)
        assert len(spec.foot_contacts) == 8


class TestURDFCollisionGeometry:
    def test_foot_links_have_collision(self) -> None:
        """URDF foot links should have <collision> elements with box geometry."""
        robot = ET.Element("robot", name="test")
        create_full_body(robot)

        for side in ("l", "r"):
            foot = robot.find(f".//link[@name='foot_{side}']")
            assert foot is not None, f"foot_{side} link not found"
            collision = foot.find("collision")
            assert collision is not None, f"foot_{side} missing collision element"

            origin = collision.find("origin")
            assert origin is not None
            assert origin.get("xyz") == "0 0 -0.01"

            box = collision.find("geometry/box")
            assert box is not None, f"foot_{side} collision missing box geometry"
            size = box.get("size", "")
            parts = size.split()
            assert len(parts) == 3
            assert float(parts[0]) == pytest.approx(0.26, abs=1e-4)
            assert float(parts[1]) == pytest.approx(0.10, abs=1e-4)
            assert float(parts[2]) == pytest.approx(0.02, abs=1e-4)

    def test_non_foot_links_no_collision(self) -> None:
        """Non-foot links should not have collision geometry (yet)."""
        robot = ET.Element("robot", name="test")
        create_full_body(robot)

        for link in robot.findall("link"):
            name = link.get("name", "")
            if name.startswith("foot_"):
                continue
            collision = link.find("collision")
            assert collision is None, f"Unexpected collision on {name}"


class TestOCPContactFormulation:
    """Test contact-aware OCP creation (mocked -- no real crocoddyl)."""

    def test_use_contacts_kwarg_accepted(self) -> None:
        """create_exercise_ocp should accept use_contacts keyword."""
        from unittest.mock import patch

        with patch.dict("sys.modules", {"crocoddyl": None, "pinocchio": None}):
            import importlib

            import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

            importlib.reload(oc_mod)

            # Without crocoddyl, it raises ImportError regardless
            with pytest.raises(ImportError, match="Crocoddyl is not installed"):
                oc_mod.create_exercise_ocp("<robot/>", "back_squat", use_contacts=True)

    def test_build_contact_models_signature_exists(self) -> None:
        """_build_contact_models should be importable."""
        import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

        assert hasattr(oc_mod, "_build_contact_models")


class TestIKGroundFeet:
    """Test ground_feet kwarg on IK solver (mocked -- no real pink)."""

    def test_ground_feet_kwarg_accepted(self) -> None:
        """solve_pose should accept ground_feet keyword."""
        from unittest.mock import patch

        with patch.dict("sys.modules", {"pinocchio": None, "pink": None}):
            import importlib

            import pinocchio_models.addons.pink.ik_solver as ik_mod

            importlib.reload(ik_mod)

            with pytest.raises(ImportError, match="Pink is not installed"):
                ik_mod.solve_pose(None, {}, ground_feet=True)  # type: ignore
