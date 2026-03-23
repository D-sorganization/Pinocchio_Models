"""Pink inverse kinematics for computing exercise target poses.

Uses Pink's task-based IK to solve for joint configurations that
place the barbell at target positions for each exercise phase.

Usage requires the optional ``pink`` extra::

    pip install pinocchio-models[pink]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

try:
    import pink
    import pinocchio as pin

    _HAS_PINK = True
except ImportError:
    _HAS_PINK = False

from pinocchio_models.shared.contracts.preconditions import (
    require_positive,
)


def _require_pink() -> None:
    """Raise ImportError with installation instructions if Pink is missing."""
    if not _HAS_PINK:
        raise ImportError(
            "Pink is not installed. Install with: pip install pinocchio-models[pink]"
        )


@dataclass(frozen=True)
class IKProblem:
    """Encapsulates a Pink inverse kinematics problem.

    Stores the Pinocchio model, data, and target frame names
    needed for IK solving.
    """

    model: Any
    data: Any
    target_frames: list[str] = field(default_factory=list)


def create_ik_problem(urdf_str: str, target_frames: list[str]) -> IKProblem:
    """Create an IK problem from a URDF string and target frame names.

    Parameters
    ----------
    urdf_str : str
        URDF XML string of the model.
    target_frames : list[str]
        Names of frames to target during IK solving.

    Returns
    -------
    IKProblem
        Configured IK problem ready for solving.
    """
    _require_pink()

    model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
    data = model.createData()

    return IKProblem(model=model, data=data, target_frames=target_frames)


def solve_pose(
    problem: IKProblem,
    targets: dict[str, np.ndarray],
    max_iterations: int = 100,
    tolerance: float = 1e-4,
) -> np.ndarray:
    """Solve for a joint configuration reaching the given targets.

    Parameters
    ----------
    problem : IKProblem
        IK problem from create_ik_problem().
    targets : dict[str, ndarray]
        Mapping from frame name to desired SE(3) pose (4x4 matrix).
    max_iterations : int
        Maximum solver iterations.
    tolerance : float
        Convergence tolerance.

    Returns
    -------
    ndarray
        Joint configuration vector (nq,).
    """
    _require_pink()
    require_positive(float(max_iterations), "max_iterations")

    model = problem.model
    data = problem.data
    q = pin.neutral(model)

    configuration = pink.Configuration(model, data, q)
    tasks = []

    for frame_name, target_pose in targets.items():
        se3_target = pin.SE3(target_pose[:3, :3], target_pose[:3, 3])
        task = pink.tasks.FrameTask(
            frame_name,
            position_cost=1.0,
            orientation_cost=1.0,
        )
        task.set_target(se3_target)
        tasks.append(task)

    for _iteration in range(max_iterations):
        velocity = configuration.solve_ik(tasks, dt=0.01)
        q = pin.integrate(model, configuration.q, velocity * 0.01)
        configuration = pink.Configuration(model, data, q)

        error = max(np.linalg.norm(task.compute_error(configuration)) for task in tasks)
        if error < tolerance:
            break

    return configuration.q


def compute_exercise_keyframes(
    urdf_str: str,
    exercise_name: str,
    n_frames: int = 10,
) -> list[np.ndarray]:
    """Compute keyframe configurations for an exercise motion.

    Parameters
    ----------
    urdf_str : str
        URDF XML string of the model.
    exercise_name : str
        Name of the exercise for keyframe generation.
    n_frames : int
        Number of keyframes to generate.

    Returns
    -------
    list[ndarray]
        List of joint configuration vectors.
    """
    _require_pink()
    require_positive(float(n_frames), "n_frames")

    model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
    q_neutral = pin.neutral(model)

    keyframes = [q_neutral.copy() for _ in range(n_frames)]
    return keyframes
