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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

try:
    import crocoddyl
    import pinocchio as pin

    _HAS_CROCODDYL = True
except ImportError:
    _HAS_CROCODDYL = False

from pinocchio_models.shared.constants import VALID_EXERCISE_NAMES
from pinocchio_models.shared.contracts.preconditions import (
    require_positive,
)


def _require_crocoddyl() -> None:
    """Raise ImportError with instructions if Crocoddyl is missing."""
    if not _HAS_CROCODDYL:
        raise ImportError(
            "Crocoddyl is not installed. " "Install with: pip install pinocchio-models[crocoddyl]"
        )


def _validate_exercise_name(exercise_name: str) -> None:
    """Validate that exercise_name is a recognized exercise."""
    if exercise_name not in VALID_EXERCISE_NAMES:
        raise ValueError(
            f"Unknown exercise '{exercise_name}'. " f"Valid names: {sorted(VALID_EXERCISE_NAMES)}"
        )


@dataclass
class ExerciseOCP:
    """Encapsulates a Crocoddyl optimal control problem for an exercise.

    Stores the Pinocchio model, the Crocoddyl shooting problem,
    and solver configuration.
    """

    model: Any
    state: Any
    actuation: Any
    problem: Any
    dt: float
    n_steps: int
    running_models: list[Any] = field(default_factory=list)
    terminal_model: Any = None


def _build_contact_models(
    model: Any,
    state: Any,
    foot_frame_names: list[str],
) -> Any:
    """Build a ContactModelMultiple with 3D foot contacts.

    Each foot frame gets a :class:`crocoddyl.ContactModel3D` enforcing
    the frame position (bilateral, zero-velocity contact on the ground
    plane).

    Parameters
    ----------
    model : pinocchio.Model
        Pinocchio model.
    state : crocoddyl.StateMultibody
        State object wrapping *model*.
    foot_frame_names : list[str]
        Frame names to constrain (e.g. ``["foot_l", "foot_r"]``).

    Returns
    -------
    crocoddyl.ContactModelMultiple
        Contact model ready for use in a DAM.
    """
    contacts = crocoddyl.ContactModelMultiple(state, model.nv)
    for name in foot_frame_names:
        frame_id = model.getFrameId(name)
        contact = crocoddyl.ContactModel3D(
            state,
            frame_id,
            np.zeros(3),  # reference position (ground)
            model.nv,
            np.array([0.0, 50.0]),  # gains (baumgarte stabilisation)
        )
        contacts.addContact(f"{name}_contact", contact)
    return contacts


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
    _validate_exercise_name(exercise_name)
    require_positive(dt, "dt")
    require_positive(float(n_steps), "n_steps")

    model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
    state = crocoddyl.StateMultibody(model)
    actuation = crocoddyl.ActuationModelFloatingBase(state)

    # Running cost: effort regularization
    running_cost_model = crocoddyl.CostModelSum(state)
    u_residual = crocoddyl.ResidualModelControl(state)
    u_cost = crocoddyl.CostModelResidual(state, u_residual)
    running_cost_model.addCost("effort", u_cost, 1e-3)

    # State regularization
    x_residual = crocoddyl.ResidualModelState(state)
    x_cost = crocoddyl.CostModelResidual(state, x_residual)
    running_cost_model.addCost("state_reg", x_cost, 1e-1)

    # Terminal cost: state regularization
    terminal_cost_model = crocoddyl.CostModelSum(state)
    terminal_cost_model.addCost("state_reg", x_cost, 1.0)

    # Optionally add contact constraints
    contacts = None
    if use_contacts:
        foot_frames = ["foot_l", "foot_r"]
        contacts = _build_contact_models(model, state, foot_frames)

        # Add friction cone cost on contact forces
        for fname in foot_frames:
            frame_id = model.getFrameId(fname)
            cone = crocoddyl.FrictionCone(
                np.eye(3),  # rotation (world frame)
                0.8,  # mu
                4,  # number of facets
                False,  # inner / outer approximation
            )
            friction_residual = crocoddyl.ResidualModelContactFrictionCone(
                state, frame_id, cone, model.nv
            )
            friction_cost = crocoddyl.CostModelResidual(state, friction_residual)
            running_cost_model.addCost(f"{fname}_friction", friction_cost, 1e-2)

    # Differential action models
    if contacts is not None:
        running_dam = crocoddyl.DifferentialActionModelContactFwdDynamics(
            state, actuation, contacts, running_cost_model
        )
        terminal_dam = crocoddyl.DifferentialActionModelContactFwdDynamics(
            state, actuation, contacts, terminal_cost_model
        )
    else:
        running_dam = crocoddyl.DifferentialActionModelFreeFwdDynamics(
            state, actuation, running_cost_model
        )
        terminal_dam = crocoddyl.DifferentialActionModelFreeFwdDynamics(
            state, actuation, terminal_cost_model
        )

    # Integrated action models
    running_models = [crocoddyl.IntegratedActionModelEuler(running_dam, dt) for _ in range(n_steps)]
    terminal_model = crocoddyl.IntegratedActionModelEuler(terminal_dam, 0.0)

    # Shooting problem
    x0 = np.concatenate([pin.neutral(model), np.zeros(model.nv)])
    problem = crocoddyl.ShootingProblem(x0, running_models, terminal_model)

    return ExerciseOCP(
        model=model,
        state=state,
        actuation=actuation,
        problem=problem,
        dt=dt,
        n_steps=n_steps,
        running_models=running_models,
        terminal_model=terminal_model,
    )


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
