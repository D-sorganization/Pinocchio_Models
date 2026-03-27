"""Tests for top-level convenience imports."""

from __future__ import annotations


class TestConvenienceImports:
    def test_import_builders(self) -> None:
        from pinocchio_models import (
            BenchPressModelBuilder,
            CleanAndJerkModelBuilder,
            DeadliftModelBuilder,
            GaitModelBuilder,
            SitToStandModelBuilder,
            SnatchModelBuilder,
            SquatModelBuilder,
        )

        assert BenchPressModelBuilder is not None
        assert CleanAndJerkModelBuilder is not None
        assert DeadliftModelBuilder is not None
        assert GaitModelBuilder is not None
        assert SitToStandModelBuilder is not None
        assert SnatchModelBuilder is not None
        assert SquatModelBuilder is not None

    def test_import_convenience_functions(self) -> None:
        from pinocchio_models import (
            build_bench_press_model,
            build_clean_and_jerk_model,
            build_deadlift_model,
            build_gait_model,
            build_sit_to_stand_model,
            build_snatch_model,
            build_squat_model,
        )

        assert callable(build_bench_press_model)
        assert callable(build_clean_and_jerk_model)
        assert callable(build_deadlift_model)
        assert callable(build_gait_model)
        assert callable(build_sit_to_stand_model)
        assert callable(build_snatch_model)
        assert callable(build_squat_model)

    def test_import_specs(self) -> None:
        from pinocchio_models import BarbellSpec, BodyModelSpec, ExerciseConfig

        assert BarbellSpec is not None
        assert BodyModelSpec is not None
        assert ExerciseConfig is not None

    def test_build_via_top_level_import(self) -> None:
        from pinocchio_models import build_squat_model

        urdf = build_squat_model()
        assert "<robot" in urdf
