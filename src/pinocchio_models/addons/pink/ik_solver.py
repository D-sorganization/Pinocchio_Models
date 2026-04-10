"""Pink inverse kinematics for computing exercise target poses.

Uses Pink's task-based IK to solve for joint configurations that
place the barbell at target positions for each exercise phase.

Usage requires the optional ``pink`` extra::

    pip install pinocchio-models[pink]
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from typing import Any

import numpy as np

try:
    import pink
    import pinocchio as pin

    _HAS_PINK = True
except ImportError:
    _HAS_PINK = False

from pinocchio_models.shared.constants import HIP_FLEXION_MAX
from pinocchio_models.shared.contracts.preconditions import (
    require_positive,
    require_valid_exercise_name,
    require_valid_urdf_string,
)

logger = logging.getLogger(__name__)


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
    require_valid_urdf_string(urdf_str)

    model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
    data = model.createData()

    return IKProblem(model=model, data=data, target_frames=target_frames)


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


def _build_ground_tasks() -> list[Any]:
    """Build foot-contact tasks that pin feet at Z=0.

    Returns
    -------
    list
        Two Pink FrameTask instances (foot_l, foot_r) with high position
        weight to enforce ground contact.
    """
    tasks: list[Any] = []
    for foot_name in ("foot_l", "foot_r"):
        foot_task = pink.tasks.FrameTask(
            foot_name,
            position_cost=10.0,  # High weight to enforce contact
            orientation_cost=0.1,
        )
        foot_task.set_target(pin.SE3.Identity())
        tasks.append(foot_task)
    return tasks


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
    velocity = configuration.solve_ik(tasks, dt=0.01)
    q = pin.integrate(model, configuration.q, velocity * 0.01)
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


def solve_pose(
    problem: IKProblem,
    targets: dict[str, np.ndarray],
    max_iterations: int = 100,
    tolerance: float = 1e-4,
    *,
    ground_feet: bool = False,
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
    ground_feet : bool
        If True, constrain ``foot_l`` and ``foot_r`` frames to
        maintain Z=0 (ground contact). This prevents the model from
        floating during IK.

    Returns
    -------
    ndarray
        Joint configuration vector (nq,).
    """
    _require_pink()
    require_positive(float(max_iterations), "max_iterations")

    for frame_name, pose in targets.items():
        pose_arr = np.asarray(pose)
        if pose_arr.shape != (4, 4):
            raise ValueError(
                f"SE(3) pose for frame '{frame_name}' must be a (4, 4) matrix, "
                f"got shape {pose_arr.shape}"
            )
        if not np.all(np.isfinite(pose_arr)):
            raise ValueError(
                f"SE(3) pose for frame '{frame_name}' contains non-finite values"
            )

    model = problem.model
    data = problem.data

    # --- Setup phase ---
    tasks = _build_target_tasks(targets)
    if ground_feet:
        tasks.extend(_build_ground_tasks())

    configuration = pink.Configuration(model, data, pin.neutral(model))

    # --- Solve phase ---
    converged = False
    for _iteration in range(max_iterations):
        configuration = _ik_step(configuration, model, data, tasks)
        if _check_convergence(configuration, tasks, tolerance):
            converged = True
            break

    if not converged:
        warnings.warn(
            f"IK did not converge within {max_iterations} iterations "
            f"(tolerance={tolerance}). The returned configuration may not satisfy "
            "all target constraints.",
            UserWarning,
            stacklevel=2,
        )

    return configuration.q


# Exercise phase definitions for keyframe generation.
# Maps exercise_name -> list of (phase_name, hip_angle_fraction) pairs
# where fraction 0.0 = start position, 1.0 = end position.
_EXERCISE_PHASES: dict[str, list[tuple[str, float]]] = {
    "back_squat": [
        ("standing", 0.0),
        ("descent_start", 0.2),
        ("quarter_squat", 0.4),
        ("half_squat", 0.6),
        ("parallel", 0.8),
        ("bottom", 1.0),
        ("ascent_start", 0.8),
        ("half_up", 0.5),
        ("quarter_up", 0.25),
        ("lockout", 0.0),
    ],
    "bench_press": [
        ("lockout", 0.0),
        ("descent_start", 0.15),
        ("mid_descent", 0.4),
        ("chest_touch", 1.0),
        ("press_start", 0.9),
        ("mid_press", 0.5),
        ("near_lockout", 0.15),
        ("lockout_end", 0.0),
    ],
    "deadlift": [
        ("floor", 1.0),
        ("break_floor", 0.85),
        ("below_knee", 0.6),
        ("above_knee", 0.4),
        ("hip_drive", 0.2),
        ("lockout", 0.0),
    ],
    "snatch": [
        ("floor", 1.0),
        ("first_pull", 0.7),
        ("power_position", 0.3),
        ("triple_ext", 0.0),
        ("turnover", 0.5),
        ("overhead_squat", 0.9),
        ("recovery", 0.0),
    ],
    "clean_and_jerk": [
        ("floor", 1.0),
        ("first_pull", 0.7),
        ("power_position", 0.3),
        ("rack", 0.1),
        ("dip", 0.3),
        ("drive", 0.0),
        ("split", 0.2),
        ("recovery", 0.0),
    ],
}


def compute_exercise_keyframes(
    urdf_str: str,
    exercise_name: str,
    n_frames: int = 10,
) -> list[np.ndarray]:
    """Compute keyframe configurations for an exercise motion.

    Generates keyframes by interpolating joint angles between exercise
    phase positions. Each keyframe represents a biomechanically
    plausible configuration along the exercise trajectory.

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
    require_valid_urdf_string(urdf_str)
    require_valid_exercise_name(exercise_name)
    require_positive(float(n_frames), "n_frames")

    model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
    q_neutral = pin.neutral(model)

    phases = _EXERCISE_PHASES.get(exercise_name, [])
    if not phases:
        return [q_neutral.copy() for _ in range(n_frames)]

    # Interpolate between phase key positions
    keyframes: list[np.ndarray] = []
    max_hip_angle = HIP_FLEXION_MAX

    for i in range(n_frames):
        t = i / max(n_frames - 1, 1)
        phase_idx = t * (len(phases) - 1)
        lower_idx = int(phase_idx)
        upper_idx = min(lower_idx + 1, len(phases) - 1)
        blend = phase_idx - lower_idx

        lower_frac = phases[lower_idx][1]
        upper_frac = phases[upper_idx][1]
        angle_frac = lower_frac + blend * (upper_frac - lower_frac)

        q = q_neutral.copy()
        # Determine the number of FreeFlyer DOFs dynamically so the code
        # works correctly even if the root joint ever changes.
        try:
            root_joint_id = model.getJointId("root_joint")
            freeflyer_nq = model.joints[root_joint_id].nq
        except (RuntimeError, KeyError) as _e:
            logger.warning("root_joint not found in model, using fallback nq=7: %s", _e)
            freeflyer_nq = 7  # Fallback for standard FreeFlyer
        nq_actuated = model.nq - freeflyer_nq
        if nq_actuated <= 0:
            raise ValueError(
                f"Model has no actuated joints (nq={model.nq}, freeflyer_nq={freeflyer_nq})"
            )
        # Scale hip-like joints by the angle fraction
        perturbation = np.zeros(nq_actuated)
        perturbation[0] = angle_frac * max_hip_angle * 0.3
        q[freeflyer_nq : freeflyer_nq + nq_actuated] = (
            q[freeflyer_nq : freeflyer_nq + nq_actuated] + perturbation
        )

        keyframes.append(q)

    return keyframes
