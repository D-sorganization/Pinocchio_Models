//! Rust accelerator for Pinocchio Models.
//!
//! Provides parallel batch computations via PyO3 + Rayon:
//! - `inverse_dynamics_batch()` — parallel batch inverse dynamics (τ = M·q̈ + C·q̇ + g)
//! - `com_batch()` — parallel batch center-of-mass computation
//! - `interpolate_phases_rs()` — parallel phase interpolation for keyframe generation

use ndarray::{Array1, Array2, Axis};
use numpy::{PyArray1, PyArray2, PyReadonlyArray1, PyReadonlyArray2};
use pyo3::prelude::*;
use rayon::prelude::*;

/// Compute inverse dynamics in batch: τ = M(q)·q̈ + C(q, q̇)·q̇ + g(q).
///
/// This is a simplified rigid-body inverse dynamics using diagonal inertia
/// approximation for demonstration. For production use, integrate with the
/// full Pinocchio RNEA algorithm via pin.rnea() on each sample.
///
/// # Arguments
/// * `q_batch`    — joint positions,    shape (batch, nq)
/// * `qd_batch`   — joint velocities,   shape (batch, nq)
/// * `qdd_batch`  — joint accelerations, shape (batch, nq)
/// * `masses`     — per-joint effective masses, shape (nq,)
/// * `gravity`    — gravitational acceleration magnitude (e.g. 9.81)
///
/// # Returns
/// Torques array of shape (batch, nq).
#[pyfunction]
fn inverse_dynamics_batch<'py>(
    py: Python<'py>,
    q_batch: PyReadonlyArray2<'py, f64>,
    qd_batch: PyReadonlyArray2<'py, f64>,
    qdd_batch: PyReadonlyArray2<'py, f64>,
    masses: PyReadonlyArray1<'py, f64>,
    gravity: f64,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let q = q_batch.as_array();
    let qd = qd_batch.as_array();
    let qdd = qdd_batch.as_array();
    let m = masses.as_array();

    let batch_size = q.nrows();
    let nq = q.ncols();

    // Pre-allocate output
    let mut torques = Array2::<f64>::zeros((batch_size, nq));

    // Parallel computation over batch dimension
    let rows: Vec<Array1<f64>> = (0..batch_size)
        .into_par_iter()
        .map(|i| {
            let mut tau = Array1::<f64>::zeros(nq);
            for j in 0..nq {
                // τ_j = m_j * q̈_j + damping * q̇_j + m_j * g
                let inertia_term = m[j] * qdd[[i, j]];
                let damping_term = 0.1 * m[j] * qd[[i, j]];
                let gravity_term = m[j] * gravity * q[[i, j]].cos();
                tau[j] = inertia_term + damping_term + gravity_term;
            }
            tau
        })
        .collect();

    for (i, row) in rows.into_iter().enumerate() {
        torques.row_mut(i).assign(&row);
    }

    Ok(PyArray2::from_owned_array(py, torques))
}

/// Compute center of mass for a batch of configurations.
///
/// Uses a weighted average of joint positions as a proxy for COM.
/// Each joint position is weighted by its segment mass.
///
/// # Arguments
/// * `q_batch` — joint positions, shape (batch, nq)
/// * `masses`  — per-joint segment masses, shape (nq,)
///
/// # Returns
/// COM positions, shape (batch, 3) — [x, y, z] for each sample.
#[pyfunction]
fn com_batch<'py>(
    py: Python<'py>,
    q_batch: PyReadonlyArray2<'py, f64>,
    masses: PyReadonlyArray1<'py, f64>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let q = q_batch.as_array();
    let m = masses.as_array();

    let batch_size = q.nrows();
    let nq = q.ncols();
    let total_mass: f64 = m.sum();

    let rows: Vec<[f64; 3]> = (0..batch_size)
        .into_par_iter()
        .map(|i| {
            let mut com = [0.0_f64; 3];
            // Simplified COM: project joint angles to Cartesian via sin/cos
            for j in 0..nq {
                let angle = q[[i, j]];
                com[0] += m[j] * angle.sin();
                com[1] += m[j] * angle.cos();
                // Z component accumulates height contribution
                com[2] += m[j] * (j as f64 / nq as f64);
            }
            if total_mass > 0.0 {
                com[0] /= total_mass;
                com[1] /= total_mass;
                com[2] /= total_mass;
            }
            com
        })
        .collect();

    let mut result = Array2::<f64>::zeros((batch_size, 3));
    for (i, row) in rows.iter().enumerate() {
        result[[i, 0]] = row[0];
        result[[i, 1]] = row[1];
        result[[i, 2]] = row[2];
    }

    Ok(PyArray2::from_owned_array(py, result))
}

/// Parallel phase interpolation for keyframe generation.
///
/// Given phase boundary angles and frame fractions, interpolate joint
/// angles for every frame in parallel.
///
/// # Arguments
/// * `phase_fractions` — sorted phase boundary fractions, shape (n_phases,)
/// * `phase_angles`    — joint angles at each phase boundary, shape (n_phases, n_joints)
/// * `n_frames`        — number of output frames
///
/// # Returns
/// Interpolated keyframes, shape (n_frames, n_joints).
#[pyfunction]
fn interpolate_phases_rs<'py>(
    py: Python<'py>,
    phase_fractions: PyReadonlyArray1<'py, f64>,
    phase_angles: PyReadonlyArray2<'py, f64>,
    n_frames: usize,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let fracs = phase_fractions.as_array();
    let angles = phase_angles.as_array();
    let n_joints = angles.ncols();
    let n_phases = fracs.len();

    let rows: Vec<Array1<f64>> = (0..n_frames)
        .into_par_iter()
        .map(|i| {
            let f = if n_frames > 1 {
                i as f64 / (n_frames - 1) as f64
            } else {
                0.0
            };

            // Find surrounding phase boundaries
            let mut prev_idx = 0;
            let mut next_idx = n_phases - 1;
            for k in 0..n_phases - 1 {
                if fracs[k] <= f && f <= fracs[k + 1] {
                    prev_idx = k;
                    next_idx = k + 1;
                    break;
                }
            }

            let denom = fracs[next_idx] - fracs[prev_idx];
            let alpha = if denom.abs() < 1e-15 {
                0.0
            } else {
                (f - fracs[prev_idx]) / denom
            };

            let mut row = Array1::<f64>::zeros(n_joints);
            for j in 0..n_joints {
                let v0 = angles[[prev_idx, j]];
                let v1 = angles[[next_idx, j]];
                row[j] = v0 + alpha * (v1 - v0);
            }
            row
        })
        .collect();

    let mut result = Array2::<f64>::zeros((n_frames, n_joints));
    for (i, row) in rows.into_iter().enumerate() {
        result.index_axis_mut(Axis(0), i).assign(&row);
    }

    Ok(PyArray2::from_owned_array(py, result))
}

/// Python module definition.
#[pymodule]
fn pinocchio_models_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(inverse_dynamics_batch, m)?)?;
    m.add_function(wrap_pyfunction!(com_batch, m)?)?;
    m.add_function(wrap_pyfunction!(interpolate_phases_rs, m)?)?;
    Ok(())
}
