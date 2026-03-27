"""Trajectory optimization configuration and results."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pinocchio_models.optimization.exercise_objectives import ExerciseObjective


@dataclass(frozen=True)
class TrajectoryConfig:
    """Parameters controlling the trajectory optimisation loop."""

    n_timesteps: int = 100
    dt: float = 0.01
    max_iterations: int = 200
    convergence_tol: float = 1e-4
    control_weight: float = 1e-3
    state_weight: float = 1.0
    terminal_weight: float = 10.0
    balance_weight: float = 5.0


@dataclass
class TrajectoryResult:
    """Container for the output of a trajectory optimisation run."""

    joint_positions: np.ndarray
    joint_velocities: np.ndarray
    joint_torques: np.ndarray
    time: np.ndarray
    cost: float
    converged: bool
    iterations: int


def interpolate_phases(
    objective: ExerciseObjective, n_frames: int = 50
) -> np.ndarray:
    """Linearly interpolate between exercise phases to generate keyframes.

    Returns an array of shape ``(n_frames, n_joints)`` where joints are sorted
    alphabetically by name.
    """
    all_joints: set[str] = set()
    for phase in objective.phases:
        all_joints.update(phase.target_joints.keys())
    joint_names = sorted(all_joints)

    fractions = np.linspace(0.0, 1.0, n_frames)
    keyframes = np.zeros((n_frames, len(joint_names)))

    for i, f in enumerate(fractions):
        # Find surrounding phases
        prev_phase = objective.phases[0]
        next_phase = objective.phases[-1]
        for j in range(len(objective.phases) - 1):
            if objective.phases[j].fraction <= f <= objective.phases[j + 1].fraction:
                prev_phase = objective.phases[j]
                next_phase = objective.phases[j + 1]
                break

        # Interpolate
        if next_phase.fraction == prev_phase.fraction:
            alpha = 0.0
        else:
            alpha = (f - prev_phase.fraction) / (
                next_phase.fraction - prev_phase.fraction
            )

        for k, jname in enumerate(joint_names):
            v0 = prev_phase.target_joints.get(jname, 0.0)
            v1 = next_phase.target_joints.get(jname, 0.0)
            keyframes[i, k] = v0 + alpha * (v1 - v0)

    return keyframes
