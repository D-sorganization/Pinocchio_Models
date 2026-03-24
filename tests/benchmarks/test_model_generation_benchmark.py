"""Benchmark tests for model generation performance.

Run with: python3 -m pytest tests/benchmarks/ -v --benchmark-only
"""

from __future__ import annotations

from typing import Any

import pytest

from pinocchio_models.exercises.bench_press.bench_press_model import (
    build_bench_press_model,
)
from pinocchio_models.exercises.clean_and_jerk.clean_and_jerk_model import (
    build_clean_and_jerk_model,
)
from pinocchio_models.exercises.deadlift.deadlift_model import build_deadlift_model
from pinocchio_models.exercises.snatch.snatch_model import build_snatch_model
from pinocchio_models.exercises.squat.squat_model import build_squat_model


@pytest.mark.benchmark(group="model-generation")
class TestModelGenerationBenchmark:
    @pytest.mark.slow()
    def test_squat_generation(self, benchmark: Any) -> None:
        benchmark(build_squat_model)

    @pytest.mark.slow()
    def test_bench_press_generation(self, benchmark: Any) -> None:
        benchmark(build_bench_press_model)

    @pytest.mark.slow()
    def test_deadlift_generation(self, benchmark: Any) -> None:
        benchmark(build_deadlift_model)

    @pytest.mark.slow()
    def test_snatch_generation(self, benchmark: Any) -> None:
        benchmark(build_snatch_model)

    @pytest.mark.slow()
    def test_clean_and_jerk_generation(self, benchmark: Any) -> None:
        benchmark(build_clean_and_jerk_model)
