"""Real-Crocoddyl optimal control solve on a short squat horizon (issue #430).

Crocoddyl is an optional extra, not a ``dev`` dependency: the module skips
cleanly when it is not installed (``pip install pinocchio-models[crocoddyl]``
runs it).
"""

from __future__ import annotations

import numpy as np
import pytest

crocoddyl = pytest.importorskip("crocoddyl")
pin = pytest.importorskip("pinocchio")

from pinocchio_models import ground_configuration  # noqa: E402
from pinocchio_models.addons.crocoddyl.optimal_control import (  # noqa: E402
    create_exercise_ocp,
    solve_ocp,
    solve_trajectory,
)
from pinocchio_models.shared.parity.fingerprint import build_urdf  # noqa: E402

DT_S = 0.01
N_STEPS = 20  # 0.2 s horizon
MAX_ITERATIONS = 100
FEET = ("foot_l", "foot_r")


def _version(module: object) -> tuple[int, ...]:
    text = str(getattr(module, "__version__", "0"))
    return tuple(int(part) for part in text.split(".")[:3] if part.isdigit())


# Observed 2026-10-13: the crocoddyl 3.2.1 wheel links libpinocchio without a
# version pin; with libpinocchio 4.1.0 ContactModel3D.calc segfaults on these
# models, while crocoddyl 3.2.0 on pinocchio 3.9.0 solves cleanly. A segfault
# would kill the test process, so skip only that binary combination.
_CONTACT_ABI_BROKEN = _version(pin) >= (4,) and _version(crocoddyl) <= (3, 2, 1)


def _standing_state(model: object) -> np.ndarray:
    q0 = ground_configuration(model, pin.neutral(model))
    return np.concatenate([q0, np.zeros(model.nv)])


def _solve(use_contacts: bool) -> tuple[object, object, np.ndarray]:
    ocp = create_exercise_ocp(
        build_urdf("squat"),
        "back_squat",
        dt=DT_S,
        n_steps=N_STEPS,
        use_contacts=use_contacts,
    )
    x0 = _standing_state(ocp.model)
    return ocp, solve_ocp(ocp, x0, max_iterations=MAX_ITERATIONS), x0


def _assert_well_formed(ocp: object, solution: object, x0: np.ndarray) -> None:
    assert solution.converged, f"DDP did not converge in {solution.iterations} its"
    assert solution.iterations < MAX_ITERATIONS
    assert np.isfinite(solution.cost)
    assert len(solution.states) == N_STEPS + 1
    assert len(solution.controls) == N_STEPS
    np.testing.assert_array_equal(solution.states[0], x0)
    nu = ocp.model.nv - 6  # floating base: the root is unactuated
    for u in solution.controls:
        assert u.shape == (nu,)
        assert np.all(np.isfinite(u))


@pytest.mark.skipif(
    _CONTACT_ABI_BROKEN,
    reason="crocoddyl<=3.2.1 wheels segfault in ContactModel3D on pinocchio 4",
)
def test_squat_contact_ocp_converges_with_feet_held() -> None:
    ocp, solution, x0 = _solve(use_contacts=True)

    _assert_well_formed(ocp, solution, x0)
    # The bilateral foot contacts hold the feet while the body moves. The
    # constraint is enforced at velocity level (Baumgarte) and integrated with
    # first-order Euler, so the feet drift by O(dt / T) of the body motion:
    # bound the drift by (dt / T) times the centre-of-mass excursion.
    model = ocp.model
    data = model.createData()

    def feet(x: np.ndarray) -> np.ndarray:
        pin.framesForwardKinematics(model, data, x[: model.nq])
        return np.array([data.oMf[model.getFrameId(f)].translation for f in FEET])

    def com(x: np.ndarray) -> np.ndarray:
        return np.array(pin.centerOfMass(model, data, x[: model.nq]))

    drift = max(np.abs(feet(x) - feet(x0)).max() for x in solution.states)
    excursion = max(np.linalg.norm(com(x) - com(x0)) for x in solution.states)
    assert excursion > 0.0
    assert drift <= (DT_S / (N_STEPS * DT_S)) * excursion


def test_squat_free_dynamics_ocp_converges() -> None:
    ocp, solution, x0 = _solve(use_contacts=False)

    _assert_well_formed(ocp, solution, x0)


def test_solve_trajectory_returns_the_solved_trajectory() -> None:
    ocp, solution, x0 = _solve(use_contacts=False)

    states, controls = solve_trajectory(ocp, x0, max_iterations=MAX_ITERATIONS)

    np.testing.assert_allclose(states[-1], solution.states[-1], atol=1e-8)
    np.testing.assert_allclose(controls[0], solution.controls[0], atol=1e-6)
