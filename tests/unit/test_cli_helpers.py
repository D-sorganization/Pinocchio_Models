"""Unit tests for the argument-parser helpers introduced by A-N Refresh 2026-04-14.

Issue #133 called out ``__main__.main`` as oversized; the subsequent
``_create_parser`` has also grown.  This module covers the decomposition
into ``_add_exercise_argument`` / ``_add_anthropometry_arguments`` /
``_add_output_arguments`` so each argument group is independently testable.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from pinocchio_models import __main__ as cli
from pinocchio_models.shared.constants import VALID_EXERCISE_NAMES


def test_add_exercise_argument_accepts_known_and_all() -> None:
    """Known exercise names and the ``all`` keyword parse successfully."""
    p = argparse.ArgumentParser()
    cli._add_exercise_argument(p)
    known = sorted(VALID_EXERCISE_NAMES)[0]
    assert p.parse_args([known]).exercise == known
    assert p.parse_args(["all"]).exercise == "all"


def test_add_exercise_argument_rejects_unknown() -> None:
    """An unknown exercise name fails at argparse level (SystemExit)."""
    p = argparse.ArgumentParser()
    cli._add_exercise_argument(p)
    with pytest.raises(SystemExit):
        p.parse_args(["not_an_exercise"])


def test_add_anthropometry_arguments_defaults() -> None:
    """Defaults come through as documented: 80 kg / 1.75 m / 0 kg plates."""
    p = argparse.ArgumentParser()
    cli._add_anthropometry_arguments(p)
    ns = p.parse_args([])
    assert ns.mass == pytest.approx(80.0)
    assert ns.height == pytest.approx(1.75)
    assert ns.plates == pytest.approx(0.0)


def test_add_output_arguments_defaults_and_flags() -> None:
    """``--output-dir`` yields a Path; ``-v`` sets ``verbose=True``."""
    p = argparse.ArgumentParser()
    cli._add_output_arguments(p)
    ns = p.parse_args([])
    assert ns.output_dir is None
    assert ns.verbose is False
    ns2 = p.parse_args(["--output-dir", "/tmp/out", "-v"])
    assert ns2.output_dir == Path("/tmp/out")
    assert ns2.verbose is True


def test_create_parser_composes_all_groups() -> None:
    """End-to-end: the composed parser accepts one command from each group."""
    p = cli._create_parser()
    known = sorted(VALID_EXERCISE_NAMES)[0]
    ns = p.parse_args(
        [known, "--mass", "70", "--height", "1.7", "--plates", "10", "-v"]
    )
    assert ns.exercise == known
    assert ns.mass == pytest.approx(70.0)
    assert ns.height == pytest.approx(1.7)
    assert ns.plates == pytest.approx(10.0)
    assert ns.verbose is True


def test_resolve_exercise_list_single() -> None:
    """A specific exercise name returns a single-element list."""
    known = sorted(VALID_EXERCISE_NAMES)[0]
    assert cli._resolve_exercise_list(known) == [known]


def test_resolve_exercise_list_all_is_sorted_full_set() -> None:
    """The ``all`` keyword expands to every exercise name, sorted."""
    result = cli._resolve_exercise_list("all")
    assert result == sorted(VALID_EXERCISE_NAMES)
    assert set(result) == set(VALID_EXERCISE_NAMES)


def test_configure_logging_verbose_flag() -> None:
    """``_configure_logging(True)`` sets the root logger to DEBUG."""
    import logging

    cli._configure_logging(verbose=True)
    assert logging.getLogger().level == logging.DEBUG
    cli._configure_logging(verbose=False)
    assert logging.getLogger().level == logging.WARNING
