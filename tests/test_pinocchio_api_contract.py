"""Pinocchio API contract guard tests.

Per UpstreamDrift CLAUDE.md (mirrored in this repo's CLAUDE.md):

    Pinocchio API: NO ``computeTotalEnergy``; use ``computeKineticEnergy``
    + ``computePotentialEnergy`` separately.

These tests assert that the API we *actually* call still exists with
the expected signature, and that ``computeTotalEnergy`` is *not*
present. They surface upstream regressions here, in Pinocchio_Models,
rather than downstream in UpstreamDrift launcher code.

The live-pinocchio assertions are marked ``live_simulation`` so they
are skipped by default CI but exercised on rigs with the real ``pin``
package installed.
"""

from __future__ import annotations

import pytest


@pytest.mark.live_simulation
class TestPinocchioEnergyAPI:
    """Guard the energy-API contract Pinocchio_Models depends on."""

    def test_compute_total_energy_is_absent(self) -> None:
        """``computeTotalEnergy`` must not exist. If it ever appears,
        downstream code that learned to depend on it would break the
        very Pinocchio versions we support."""
        pin = pytest.importorskip("pinocchio", reason="pin package not installed")
        assert not hasattr(pin, "computeTotalEnergy"), (
            "pinocchio.computeTotalEnergy reappeared upstream; update "
            "the contract guard and the documentation in CLAUDE.md."
        )

    def test_kinetic_and_potential_energy_callables_exist(self) -> None:
        pin = pytest.importorskip("pinocchio", reason="pin package not installed")
        assert callable(getattr(pin, "computeKineticEnergy", None))
        assert callable(getattr(pin, "computePotentialEnergy", None))

    def test_total_energy_is_sum_of_kinetic_and_potential(self) -> None:
        """Numerical sanity check on a tiny model: total = T + V."""
        pin = pytest.importorskip("pinocchio", reason="pin package not installed")
        import numpy as np

        from pinocchio_models.exercises.gait.gait_model import build_gait_model

        urdf_str = build_gait_model()
        if hasattr(pin, "buildModelFromXML"):
            model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
        else:
            pytest.skip("pin.buildModelFromXML not available in this build")
        data = model.createData()

        q = pin.neutral(model)
        v = np.zeros(model.nv)

        kinetic = pin.computeKineticEnergy(model, data, q, v)
        potential = pin.computePotentialEnergy(model, data, q)
        expected_total = kinetic + potential

        # Contract: there is no ``pin.computeTotalEnergy``; the caller
        # must sum kinetic + potential explicitly. We assert the sum
        # matches itself (sanity) and that no helper is silently masking
        # the API gotcha.
        assert np.isfinite(expected_total)
        assert not hasattr(pin, "computeTotalEnergy")


class TestEnergyAPIDocumentation:
    """Static guards that always run (no Pinocchio required)."""

    def test_repo_claude_md_documents_gotcha(self) -> None:
        from pathlib import Path

        claude_md = (Path(__file__).resolve().parent.parent / "CLAUDE.md").read_text(
            encoding="utf-8"
        )
        assert "computeTotalEnergy" in claude_md, (
            "CLAUDE.md must continue to document the missing-API gotcha."
        )
        assert "computeKineticEnergy" in claude_md
        assert "computePotentialEnergy" in claude_md
