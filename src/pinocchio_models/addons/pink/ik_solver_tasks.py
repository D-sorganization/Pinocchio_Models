"""Task/step helpers for the Pink IK solver.

Low-level building blocks used by :func:`ik_solver.solve_pose`:

- :func:`_build_target_tasks` converts a user-supplied targets dict
  into Pink ``FrameTask`` instances.
- :func:`_build_ground_tasks` emits foot-contact tasks that put each
  sole on the ground (Z=0) where the foot starts.
- :func:`_select_qp_solver` picks the QP backend Pink solves with.
- :func:`_ik_step` advances the configuration by one integration step.
- :func:`_check_convergence` evaluates the maximum task error.

These helpers are re-exported from the facade :mod:`ik_solver` module
so that tests can ``patch.object`` them on the facade while
:func:`ik_solver.solve_pose` still calls them by bare name.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from pinocchio_models.shared.body.foot_sole import sole_depth_m

try:
    import pink
    import pinocchio as pin
    import qpsolvers
except ImportError:  # pragma: no cover - exercised via import guard tests
    pink = None  # type: ignore[assignment]
    pin = None  # type: ignore[assignment]
    qpsolvers = None  # type: ignore[assignment]

#: Frames constrained to the ground by :func:`_build_ground_tasks`.
FOOT_FRAMES: tuple[str, ...] = ("foot_l", "foot_r")

#: QP backends in order of preference; ``daqp`` ships with the ``pink`` extra.
_PREFERRED_QP_SOLVERS: tuple[str, ...] = ("daqp", "quadprog", "proxqp", "osqp")

#: Integration time step (s) for one IK iteration.
_IK_DT = 0.01


def _build_target_tasks(targets: dict[str, np.ndarray]) -> list[Any]:
    """Convert a targets dict into a list of Pink FrameTask objects.

    Parameters
    ----------
    targets : dict[str, ndarray]
        Mapping from frame name to desired SE(3) pose (4x4 matrix).

    Returns
    -------
    list
        Pink FrameTask instances with targets set.
    """
    tasks: list[Any] = []
    for frame_name, target_pose in targets.items():
        se3_target = pin.SE3(target_pose[:3, :3], target_pose[:3, 3])
        task = pink.tasks.FrameTask(
            frame_name,
            position_cost=1.0,
            orientation_cost=1.0,
        )
        task.set_target(se3_target)
        tasks.append(task)
    return tasks


def _build_ground_tasks(configuration: Any) -> list[Any]:
    """Build foot-contact tasks that put each sole flat on the ground.

    Each foot frame (the ankle origin) is targeted at its starting X/Y
    position, ``sole_depth_m()`` above Z=0 so the sole touches the ground,
    with a level (identity) orientation.

    Parameters
    ----------
    configuration : pink.Configuration
        Starting configuration; it fixes where each foot is planted.

    Returns
    -------
    list
        Two Pink FrameTask instances (foot_l, foot_r) with high position
        weight to enforce ground contact.
    """
    sole_height = sole_depth_m()
    tasks: list[Any] = []
    for foot_name in FOOT_FRAMES:
        start = configuration.get_transform_frame_to_world(foot_name).translation
        foot_task = pink.tasks.FrameTask(
            foot_name,
            position_cost=10.0,  # High weight to enforce contact
            orientation_cost=0.1,
        )
        foot_task.set_target(
            pin.SE3(np.eye(3), np.array([start[0], start[1], sole_height]))
        )
        tasks.append(foot_task)
    return tasks


def _select_qp_solver() -> str:
    """Return the QP backend Pink should use.

    Returns
    -------
    str
        A preferred solver when installed, else the first available one.

    Raises
    ------
    ImportError
        If ``qpsolvers`` has no backend installed.
    """
    available = list(qpsolvers.available_solvers)
    for name in _PREFERRED_QP_SOLVERS:
        if name in available:
            return name
    if available:
        return str(available[0])
    raise ImportError(
        "Pink found no QP solver backend. Install with: "
        "pip install pinocchio-models[pink]"
    )


def _ik_step(
    configuration: Any,
    model: Any,
    data: Any,
    tasks: list[Any],
) -> Any:
    """Advance the IK solver by one integration step.

    Parameters
    ----------
    configuration : pink.Configuration
        Current robot configuration.
    model : pinocchio.Model
        Pinocchio model.
    data : pinocchio.Data
        Pinocchio data.
    tasks : list
        Active Pink tasks for this step.

    Returns
    -------
    pink.Configuration
        Updated configuration after the integration step.
    """
    velocity = pink.solve_ik(configuration, tasks, _IK_DT, solver=_select_qp_solver())
    q = pin.integrate(model, configuration.q, velocity * _IK_DT)
    return pink.Configuration(model, data, q)


def _check_convergence(configuration: Any, tasks: list[Any], tolerance: float) -> bool:
    """Return True if the maximum task error is below *tolerance*.

    Parameters
    ----------
    configuration : pink.Configuration
        Current robot configuration.
    tasks : list
        Active Pink tasks to evaluate.
    tolerance : float
        Convergence threshold.

    Returns
    -------
    bool
        True when all tasks are within tolerance.
    """
    error = float(
        max(float(np.linalg.norm(task.compute_error(configuration))) for task in tasks)
    )
    return error < tolerance
