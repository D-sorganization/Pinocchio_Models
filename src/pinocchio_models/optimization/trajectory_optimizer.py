"""Trajectory optimization configuration and results."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pinocchio_models.optimization.exercise_objectives import ExerciseObjective
from pinocchio_models.exceptions import GeometryError


def _validate_non_negative_weight(name: str, value: float) -> None:
    """Validate that a weight is non-negative."""
    if value < 0.0:
        msg = f"{name} must be non-negative, got {value}"
        raise GeometryError(msg)


@dataclass(frozen=True)
class TrajectoryConfig:
    """Parameters controlling the trajectory optimisation loop.

    Attributes:
        n_timesteps: Number of discrete time steps in trajectory.
        dt: Time step duration in seconds.
        max_iterations: Maximum optimiser iterations before stopping.
        convergence_tol: Cost change threshold for convergence.
        control_weight: Penalty weight on joint torque magnitudes.
        state_weight: Weight for tracking target trajectory.
        terminal_weight: Weight for reaching the final target pose.
        balance_weight: Weight for keeping CoM over base of support.
    """

    n_timesteps: int = 100
    dt: float = 0.01
    max_iterations: int = 200
    convergence_tol: float = 1e-4
    control_weight: float = 1e-3
    state_weight: float = 1.0
    terminal_weight: float = 10.0
    balance_weight: float = 5.0

    def __post_init__(self) -> None:
        """Validate configuration values are physically plausible."""
        if self.n_timesteps < 1:
            msg = f"n_timesteps must be >= 1, got {self.n_timesteps}"
            raise GeometryError(msg)
        if self.dt <= 0.0:
            msg = f"dt must be positive, got {self.dt}"
            raise GeometryError(msg)
        if self.max_iterations < 1:
            msg = f"max_iterations must be >= 1, got {self.max_iterations}"
            raise GeometryError(msg)
        if self.convergence_tol <= 0.0:
            msg = f"convergence_tol must be positive, got {self.convergence_tol}"
            raise GeometryError(msg)
        _validate_non_negative_weight("control_weight", self.control_weight)
        _validate_non_negative_weight("state_weight", self.state_weight)
        _validate_non_negative_weight("terminal_weight", self.terminal_weight)
        _validate_non_negative_weight("balance_weight", self.balance_weight)


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


def _build_phase_arrays(
    objective: ExerciseObjective,
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Return ``(joint_names, phase_fracs, phase_angles)`` for *objective*.

    ``joint_names`` is the sorted union of joints across all phases.
    ``phase_fracs`` has shape ``(n_phases,)`` and ``phase_angles`` has shape
    ``(n_phases, n_joints)``.
    """
    all_joints: set[str] = set()
    for phase in objective.phases:
        all_joints.update(phase.target_joints.keys())
    joint_names = sorted(all_joints)
    n_joints = len(joint_names)

    phase_fracs = np.array([p.fraction for p in objective.phases])
    phase_angles = np.zeros((len(objective.phases), n_joints))
    for p_idx, phase in enumerate(objective.phases):
        for k, jname in enumerate(joint_names):
            phase_angles[p_idx, k] = phase.target_joints.get(jname, 0.0)
    return joint_names, phase_fracs, phase_angles


def _interpolate_keyframes(
    phase_fracs: np.ndarray, phase_angles: np.ndarray, n_frames: int
) -> np.ndarray:
    """Linearly interpolate keyframes from phase boundaries using numpy ops."""
    fractions = np.linspace(0.0, 1.0, n_frames)

    # np.searchsorted finds the insertion point; clamp to valid phase indices
    indices = np.searchsorted(phase_fracs, fractions, side="right") - 1
    indices = np.clip(indices, 0, len(phase_fracs) - 2)
    next_indices = indices + 1

    # Vectorised alpha computation
    denom = phase_fracs[next_indices] - phase_fracs[indices]
    safe_denom = np.where(denom == 0.0, 1.0, denom)
    alpha = np.where(denom == 0.0, 0.0, (fractions - phase_fracs[indices]) / safe_denom)

    # Vectorised interpolation: v0 + alpha * (v1 - v0)
    v0 = phase_angles[indices]  # (n_frames, n_joints)
    v1 = phase_angles[next_indices]  # (n_frames, n_joints)
    return v0 + alpha[:, np.newaxis] * (v1 - v0)


def _validate_interpolation_inputs(objective: ExerciseObjective, n_frames: int) -> None:
    """Reject interpolation requests that cannot produce a valid timeline."""
    if n_frames < 2:
        raise GeometryError(f"n_frames must be >= 2, got {n_frames}")
    if not objective.phases:
        raise GeometryError("objective must have at least one phase")


def interpolate_phases(objective: ExerciseObjective, n_frames: int = 50) -> np.ndarray:
    """Return a linearly interpolated joint-angle timeline for *objective*."""
    _validate_interpolation_inputs(objective, n_frames)

    _joint_names, phase_fracs, phase_angles = _build_phase_arrays(objective)
    return _interpolate_keyframes(phase_fracs, phase_angles, n_frames)