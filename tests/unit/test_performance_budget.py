"""Validation for the documented model-generation performance budget."""

from __future__ import annotations

import pathlib

import yaml

from scripts.profile_model_generation import _BUILDERS
from tests.benchmarks.test_model_generation_benchmark import (
    TestModelGenerationBenchmark as _ModelGenerationBenchmark,
)

_REPO_ROOT = pathlib.Path(__file__).parents[2]
_BUDGET_FILE = _REPO_ROOT / "docs" / "performance_budget.yml"
_BUDGET_DOC = _REPO_ROOT / "docs" / "performance_budget.md"

_REQUIRED_MODEL_GENERATION_FIELDS = {
    "description",
    "percentile",
    "threshold_ms",
    "warn_at_ms",
    "sample_size_min",
    "targets",
    "response",
}


def _load_budget() -> dict[str, object]:
    loaded = yaml.safe_load(_BUDGET_FILE.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict), "performance budget must parse as a mapping"
    return loaded


def test_performance_budget_artifact_is_documented() -> None:
    """The machine-readable SLO must have a human-readable companion document."""
    text = _BUDGET_DOC.read_text(encoding="utf-8")

    assert "## SLO" in text
    assert "## Breach Response" in text
    assert "performance_budget.yml" in text


def test_model_generation_budget_has_required_contract_fields() -> None:
    """Model generation SLO must define an actionable threshold and response."""
    budget = _load_budget()
    budgets = budget.get("budgets")
    assert isinstance(budgets, dict), "budget artifact must define budgets"
    model_generation = budgets.get("model_generation")
    assert isinstance(model_generation, dict), (
        "budget artifact must define model_generation"
    )

    assert set(model_generation) >= _REQUIRED_MODEL_GENERATION_FIELDS
    assert model_generation["percentile"] == "p95"
    assert isinstance(model_generation["threshold_ms"], int)
    assert isinstance(model_generation["warn_at_ms"], int)
    assert model_generation["threshold_ms"] > model_generation["warn_at_ms"] > 0
    assert model_generation["sample_size_min"] >= 20

    response = model_generation["response"]
    assert isinstance(response, dict)
    assert {"warn", "breach"} <= set(response)


def test_budget_targets_match_profiling_and_benchmark_targets() -> None:
    """Every profiled model target must have a budget and benchmark coverage."""
    budget = _load_budget()
    model_generation = budget["budgets"]["model_generation"]
    budget_targets = set(model_generation["targets"])
    profiled_targets = {name for name, _build_model in _BUILDERS}
    benchmark_methods = {
        name.removeprefix("test_").removesuffix("_generation")
        for name in dir(_ModelGenerationBenchmark)
        if name.startswith("test_") and name.endswith("_generation")
    }

    assert budget_targets == profiled_targets
    assert budget_targets == benchmark_methods
