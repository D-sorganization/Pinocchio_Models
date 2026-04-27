"""Crocoddyl optimal control for exercise motion optimization.

Formulates the exercise as an optimal control problem (OCP) with:
- State: joint positions + velocities
- Controls: joint torques
- Cost: tracking cost + effort regularization
- Constraints: joint limits, ground contact

Usage requires the optional ``crocoddyl`` extra::

    pip install pinocchio-models[crocoddyl]

Note on Pinocchio energy API: There is no ``computeTotalEnergy``.
Use ``computeKineticEnergy`` + ``computePotentialEnergy`` separately.

This module is a thin facade. The heavy building blocks live in
:mod:`optimal_control_builders` and the tunable constants in
:mod:`optimal_control_config`. Public API and attribute names are
preserved so existing imports and test mocks continue to work.
"""

from __future__ import annotations

import numpy as np

from pinocchio_models.exceptions import GeometryError

try:
    import crocoddyl
    import pinocchio as pin  # noqa: F401  (re-exported for test mocks)

    _HAS_CROCODDYL = True
except ImportError:
    _HAS_CROCODDYL = False

from .optimal_control_builders import (
    ExerciseOCP,
    _assemble_shooting_problem,
    _build_contact_models,
    _build_ocp_common,
    _OCPComponents,
)
from .optimal_control_config import (
    CONTACT_BAUMGARTE_GAINS,
    EFFORT_COST_WEIGHT,
    FRICTION_CONE_FACETS,
    FRICTION_COST_WEIGHT,
    GROUND_FRICTION_MU,
    STATE_REG_RUNNING_WEIGHT,
    STATE_REG_TERMINAL_WEIGHT,
)

__all__ = [
    "CONTACT_BAUMGARTE_GAINS",
    "EFFORT_COST_WEIGHT",
    "FRICTION_CONE_FACETS",
    "FRICTION_COST_WEIGHT",
    "GROUND_FRICTION_MU",
    "STATE_REG_RUNNING_WEIGHT",
    "STATE_REG_TERMINAL_WEIGHT",
    "ExerciseOCP",
    "create_cyclic_ocp",
    "create_exercise_ocp",
    "extract_joint_torques",
    "solve_trajectory",
]


def _require_crocoddyl() -> None:
    """Raise ImportError with instructions if Crocoddyl is missing."""
    if not _HAS_CROCODDYL:
        raise ImportError(
            "Crocoddyl is not installed. "
            "Install with: pip install pinocchio-models[crocoddyl]"
        )


def create_exercise_ocp(
    urdf_str: str,
    exercise_name: str,
    dt: float = 0.01,
    n_steps: int = 100,
    *,
    use_contacts: bool = False,
) -> ExerciseOCP:
    """Create an optimal control problem for an exercise.

    Parameters
    ----------
    urdf_str : str
        URDF XML string of the model.
    exercise_name : str
        Name of the exercise (must be one of the valid exercise names).
    dt : float
        Time step for discretization (seconds).
    n_steps : int
        Number of time steps in the horizon.
    use_contacts : bool
        If True, add bilateral foot-ground contact constraints and
        friction-cone regularisation to the running cost.

    Returns
    -------
    ExerciseOCP
        Configured OCP ready for solving.
    """
    _require_crocoddyl()
    c = _build_ocp_common(urdf_str, exercise_name, dt, n_steps, use_contacts)
    return _assemble_shooting_problem(c, dt, n_steps)


def create_cyclic_ocp(
    urdf_str: str,
    exercise_name: str,
    dt: float = 0.01,
    n_steps: int = 100,
    *,
    periodicity_weight: float = 100.0,
    use_contacts: bool = False,
) -> ExerciseOCP:
    """Create an OCP with periodicity constraints for cyclic motion (e.g. gait).

    Adds a terminal cost penalizing the difference between the final
    and initial configurations, encouraging the solver to find a
    steady-state cycle where q_start ~ q_end.

    Parameters
    ----------
    urdf_str : str
        URDF XML string of the model.
    exercise_name : str
        Name of the exercise (must be one of the valid exercise names).
    dt : float
        Time step for discretization (seconds).
    n_steps : int
        Number of time steps in the horizon.
    periodicity_weight : float
        Weight on the periodicity (q_start ~ q_end) terminal cost.
        Higher values enforce stricter cyclic behaviour.
    use_contacts : bool
        If True, add bilateral foot-ground contact constraints.

    Returns
    -------
    ExerciseOCP
        Configured cyclic OCP ready for solving.
    """
    _require_crocoddyl()
    from pinocchio_models.shared.contracts.preconditions import require_positive

    require_positive(periodicity_weight, "periodicity_weight")
    c = _build_ocp_common(urdf_str, exercise_name, dt, n_steps, use_contacts)

    # Periodicity constraint: penalize (x_terminal - x_initial)
    x_ref_residual = crocoddyl.ResidualModelState(c.state, c.x0)
    x_ref_cost = crocoddyl.CostModelResidual(c.state, x_ref_residual)
    c.terminal_cost_model.addCost("periodicity", x_ref_cost, periodicity_weight)

    return _assemble_shooting_problem(c, dt, n_steps)


def solve_trajectory(
    ocp: ExerciseOCP,
    initial_state: np.ndarray | None = None,
    max_iterations: int = 100,
) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """Solve the OCP and return the optimal state trajectory and controls.

    Parameters
    ----------
    ocp : ExerciseOCP
        Configured OCP from create_exercise_ocp().
    initial_state : ndarray or None
        Initial state (nq+nv,). Uses default if None.
    max_iterations : int
        Maximum DDP iterations.

    Returns
    -------
    tuple[list[ndarray], list[ndarray]]
        (states, controls) -- optimal state trajectory and control inputs.
    """
    _require_crocoddyl()

    if initial_state is not None:
        if not np.all(np.isfinite(initial_state)):
            raise GeometryError(
                "initial_state contains non-finite values (NaN or Inf). "
                "Provide a valid finite state vector."
            )
        ocp.problem.x0 = initial_state

    solver = crocoddyl.SolverDDP(ocp.problem)
    solver.solve(maxiter=max_iterations)

    return list(solver.xs), list(solver.us)


def extract_joint_torques(
    trajectory: tuple[list[np.ndarray], list[np.ndarray]],
    ocp: ExerciseOCP,
) -> np.ndarray:
    """Extract joint torques from a solved trajectory.

    Uses the controls from the already-solved trajectory rather than
    re-solving the OCP.

    Parameters
    ----------
    trajectory : tuple[list[ndarray], list[ndarray]]
        (states, controls) tuple from solve_trajectory().
    ocp : ExerciseOCP
        The OCP that produced the trajectory.

    Returns
    -------
    ndarray
        Joint torques array of shape (n_steps, nu).
    """
    _require_crocoddyl()

    _states, controls = trajectory
    return np.array(controls)


# Re-export private helpers kept as module attributes for backward compatibility
# (tests rely on ``hasattr(oc_mod, "_build_contact_models")`` and similar).
__all__ += ["_OCPComponents", "_build_contact_models"]
