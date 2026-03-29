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


def interpolate_phases(objective: ExerciseObjective, n_frames: int = 50) -> np.ndarray:
    """Linearly interpolate between exercise phases to generate keyframes.

    Returns an array of shape ``(n_frames, n_joints)`` where joints are sorted
    alphabetically by name.

    Uses vectorised numpy operations instead of per-element scalar loops.
    """
    all_joints: set[str] = set()
    for phase in objective.phases:
        all_joints.update(phase.target_joints.keys())
    joint_names = sorted(all_joints)
    n_joints = len(joint_names)

    # Build phase boundary arrays for vectorised lookup
    phase_fracs = np.array([p.fraction for p in objective.phases])
    phase_angles = np.zeros((len(objective.phases), n_joints))
    for p_idx, phase in enumerate(objective.phases):
        for k, jname in enumerate(joint_names):
            phase_angles[p_idx, k] = phase.target_joints.get(jname, 0.0)

    fractions = np.linspace(0.0, 1.0, n_frames)
    keyframes = np.zeros((n_frames, n_joints))

    # np.searchsorted finds the insertion point; clamp to valid phase indices
    indices = np.searchsorted(phase_fracs, fractions, side="right") - 1
    indices = np.clip(indices, 0, len(objective.phases) - 2)
    next_indices = indices + 1

    # Vectorised alpha computation
    denom = phase_fracs[next_indices] - phase_fracs[indices]
    safe_denom = np.where(denom == 0.0, 1.0, denom)
    alpha = np.where(denom == 0.0, 0.0, (fractions - phase_fracs[indices]) / safe_denom)

    # Vectorised interpolation: v0 + alpha * (v1 - v0)
    v0 = phase_angles[indices]  # (n_frames, n_joints)
    v1 = phase_angles[next_indices]  # (n_frames, n_joints)
    keyframes = v0 + alpha[:, np.newaxis] * (v1 - v0)

    return keyframes
