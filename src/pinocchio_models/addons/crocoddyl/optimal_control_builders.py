"""Internal builders for the Crocoddyl optimal-control problem.

Contains the helpers that assemble contact models, cost models,
intermediate component bundles, and shooting problems. These are
implementation details of :mod:`optimal_control` and are re-exported
from the facade only where tests require attribute access
(e.g. ``_build_contact_models``).

Callers from :mod:`optimal_control` are expected to gate entry with
``_require_crocoddyl()`` so that the functions here are only reached
when the optional Crocoddyl and Pinocchio packages are importable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

try:
    import crocoddyl
    import pinocchio as pin
except ImportError:  # pragma: no cover - exercised via import guard tests
    crocoddyl = None  # type: ignore[assignment]
    pin = None  # type: ignore[assignment]

from pinocchio_models.shared.contracts.preconditions import (
    require_positive,
    require_valid_exercise_name,
    require_valid_urdf_string,
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
