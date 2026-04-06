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

from pinocchio_models.shared.contracts.preconditions import (
    require_positive,
    require_valid_exercise_name,
    require_valid_urdf_string,
)

# --- Named constants for Crocoddyl OCP weights and physics ---
# Cost weights used in the running and terminal cost models.
EFFORT_COST_WEIGHT: float = 1e-3
STATE_REG_RUNNING_WEIGHT: float = 1e-1
STATE_REG_TERMINAL_WEIGHT: float = 1.0
FRICTION_COST_WEIGHT: float = 1e-2

# Baumgarte stabilisation gains for bilateral foot-ground contacts.
CONTACT_BAUMGARTE_GAINS: tuple[float, float] = (0.0, 50.0)

# Ground friction coefficient (Coulomb) and friction cone facets.
GROUND_FRICTION_MU: float = 0.8
FRICTION_CONE_FACETS: int = 4


def _require_crocoddyl() -> None:
    """Raise ImportError with instructions if Crocoddyl is missing."""
    if not _HAS_CROCODDYL:
        raise ImportError(
            "Crocoddyl is not installed. "
            "Install with: pip install pinocchio-models[crocoddyl]"
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
            np.array(CONTACT_BAUMGARTE_GAINS),
        )
        contacts.addContact(f"{name}_contact", contact)
    return contacts


@dataclass
class _OCPComponents:
    """Intermediate components produced by _build_ocp_common.

    Bundles the Pinocchio model, Crocoddyl state/actuation, cost
    models, optional contacts, and the initial state vector so that
    both ``create_exercise_ocp`` and ``create_cyclic_ocp`` can
    customise the terminal cost before assembling the shooting problem.
    """

    model: Any
    state: Any
    actuation: Any
    running_cost_model: Any
    terminal_cost_model: Any
    contacts: Any  # None when use_contacts is False
    x0: Any  # ndarray


def _build_ocp_common(
    urdf_str: str,
    exercise_name: str,
    dt: float,
    n_steps: int,
    use_contacts: bool,
) -> _OCPComponents:
    """Build the shared OCP components used by both exercise and cyclic OCPs.

    Validates inputs, constructs the Pinocchio model, state, actuation,
    running cost (effort + state regularisation), terminal cost (state
    regularisation), and optional foot-ground contacts with friction
    cone costs.

    Returns an ``_OCPComponents`` bundle that callers extend before
    assembling the final shooting problem.
    """
    _require_crocoddyl()
    require_valid_urdf_string(urdf_str)
    require_valid_exercise_name(exercise_name)
    require_positive(dt, "dt")
    require_positive(float(n_steps), "n_steps")

    model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
    state = crocoddyl.StateMultibody(model)
    actuation = crocoddyl.ActuationModelFloatingBase(state)

    # Running cost: effort regularization + state regularization
    running_cost_model = crocoddyl.CostModelSum(state)
    u_residual = crocoddyl.ResidualModelControl(state)
    u_cost = crocoddyl.CostModelResidual(state, u_residual)
    running_cost_model.addCost("effort", u_cost, EFFORT_COST_WEIGHT)

    x_residual = crocoddyl.ResidualModelState(state)
    x_cost = crocoddyl.CostModelResidual(state, x_residual)
    running_cost_model.addCost("state_reg", x_cost, STATE_REG_RUNNING_WEIGHT)

    # Terminal cost: state regularization
    terminal_cost_model = crocoddyl.CostModelSum(state)
    terminal_cost_model.addCost("state_reg", x_cost, STATE_REG_TERMINAL_WEIGHT)

    # Optionally add contact constraints
    contacts = None
    if use_contacts:
        foot_frames = ["foot_l", "foot_r"]
        contacts = _build_contact_models(model, state, foot_frames)

        for fname in foot_frames:
            frame_id = model.getFrameId(fname)
            cone = crocoddyl.FrictionCone(
                np.eye(3),
                GROUND_FRICTION_MU,
                FRICTION_CONE_FACETS,
                False,
            )
            friction_residual = crocoddyl.ResidualModelContactFrictionCone(
                state, frame_id, cone, model.nv
            )
            friction_cost = crocoddyl.CostModelResidual(state, friction_residual)
            running_cost_model.addCost(
                f"{fname}_friction", friction_cost, FRICTION_COST_WEIGHT
            )

    x0 = np.concatenate([pin.neutral(model), np.zeros(model.nv)])

    return _OCPComponents(
        model=model,
        state=state,
        actuation=actuation,
        running_cost_model=running_cost_model,
        terminal_cost_model=terminal_cost_model,
        contacts=contacts,
        x0=x0,
    )


def _assemble_shooting_problem(
    c: _OCPComponents, dt: float, n_steps: int
) -> ExerciseOCP:
    """Build integrated action models and shooting problem from components."""
    if c.contacts is not None:
        running_dam = crocoddyl.DifferentialActionModelContactFwdDynamics(
            c.state, c.actuation, c.contacts, c.running_cost_model
        )
        terminal_dam = crocoddyl.DifferentialActionModelContactFwdDynamics(
            c.state, c.actuation, c.contacts, c.terminal_cost_model
        )
    else:
        running_dam = crocoddyl.DifferentialActionModelFreeFwdDynamics(
            c.state, c.actuation, c.running_cost_model
        )
        terminal_dam = crocoddyl.DifferentialActionModelFreeFwdDynamics(
            c.state, c.actuation, c.terminal_cost_model
        )

    running_models = [
        crocoddyl.IntegratedActionModelEuler(running_dam, dt) for _ in range(n_steps)
    ]
    terminal_model = crocoddyl.IntegratedActionModelEuler(terminal_dam, 0.0)
    problem = crocoddyl.ShootingProblem(c.x0, running_models, terminal_model)

    return ExerciseOCP(
        model=c.model,
        state=c.state,
        actuation=c.actuation,
        problem=problem,
        dt=dt,
        n_steps=n_steps,
        running_models=running_models,
        terminal_model=terminal_model,
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
