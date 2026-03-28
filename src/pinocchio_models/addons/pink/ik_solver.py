"""Pink inverse kinematics for computing exercise target poses.

Uses Pink's task-based IK to solve for joint configurations that
place the barbell at target positions for each exercise phase.

Usage requires the optional ``pink`` extra::

    pip install pinocchio-models[pink]
"""

from __future__ import annotations

import logging
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
)
from pinocchio_models.shared.contracts.preconditions import (
    require_valid_exercise_name as _validate_exercise_name,
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

    model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
    data = model.createData()

    return IKProblem(model=model, data=data, target_frames=target_frames)


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

    # Foot-on-ground constraints: pin feet at Z=0
    if ground_feet:
        for foot_name in ("foot_l", "foot_r"):
            ground_pose = pin.SE3.Identity()
            # Keep X/Y from neutral, set Z=0
            foot_task = pink.tasks.FrameTask(
                foot_name,
                position_cost=10.0,  # High weight to enforce contact
                orientation_cost=0.1,
            )
            foot_task.set_target(ground_pose)
            tasks.append(foot_task)

    for _iteration in range(max_iterations):
        velocity = configuration.solve_ik(tasks, dt=0.01)
        q = pin.integrate(model, configuration.q, velocity * 0.01)
        configuration = pink.Configuration(model, data, q)

        error = max(np.linalg.norm(task.compute_error(configuration)) for task in tasks)
        if error < tolerance:
            break

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
    _validate_exercise_name(exercise_name)
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
