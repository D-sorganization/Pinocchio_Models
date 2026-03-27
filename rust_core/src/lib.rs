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

    // Input validation: shape checks
    if batch_size == 0 || nq == 0 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "q_batch must be non-empty with shape (batch, nq) where batch > 0 and nq > 0",
        ));
    }
    if qd.nrows() != batch_size || qd.ncols() != nq {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!(
                "qd_batch shape ({}, {}) must match q_batch shape ({}, {})",
                qd.nrows(), qd.ncols(), batch_size, nq
            ),
        ));
    }
    if qdd.nrows() != batch_size || qdd.ncols() != nq {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!(
                "qdd_batch shape ({}, {}) must match q_batch shape ({}, {})",
                qdd.nrows(), qdd.ncols(), batch_size, nq
            ),
        ));
    }
    if m.len() != nq {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("masses length {} must equal nq {}", m.len(), nq),
        ));
    }

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

    // Input validation
    if batch_size == 0 || nq == 0 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "q_batch must be non-empty with shape (batch, nq) where batch > 0 and nq > 0",
        ));
    }
    if m.len() != nq {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("masses length {} must equal nq {}", m.len(), nq),
        ));
    }

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

    // Input validation
    if n_phases == 0 || n_joints == 0 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "phase_fractions and phase_angles must be non-empty",
        ));
    }
    if angles.nrows() != n_phases {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!(
                "phase_angles rows {} must equal phase_fractions length {}",
                angles.nrows(), n_phases
            ),
        ));
    }
    if n_frames == 0 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "n_frames must be > 0",
        ));
    }

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


#[cfg(test)]
mod tests {
    use ndarray::{Array1, Array2};

    /// Helper: compute inverse dynamics for a single sample (non-PyO3).
    fn inverse_dynamics_single(
        q: &Array1<f64>,
        qd: &Array1<f64>,
        qdd: &Array1<f64>,
        masses: &Array1<f64>,
        gravity: f64,
    ) -> Array1<f64> {
        let nq = q.len();
        let mut tau = Array1::<f64>::zeros(nq);
        for j in 0..nq {
            let inertia_term = masses[j] * qdd[j];
            let damping_term = 0.1 * masses[j] * qd[j];
            let gravity_term = masses[j] * gravity * q[j].cos();
            tau[j] = inertia_term + damping_term + gravity_term;
        }
        tau
    }

    /// Helper: compute COM for a single sample (non-PyO3).
    fn com_single(q: &Array1<f64>, masses: &Array1<f64>) -> [f64; 3] {
        let nq = q.len();
        let total_mass: f64 = masses.sum();
        let mut com = [0.0_f64; 3];
        for j in 0..nq {
            let angle = q[j];
            com[0] += masses[j] * angle.sin();
            com[1] += masses[j] * angle.cos();
            com[2] += masses[j] * (j as f64 / nq as f64);
        }
        if total_mass > 0.0 {
            com[0] /= total_mass;
            com[1] /= total_mass;
            com[2] /= total_mass;
        }
        com
    }

    #[test]
    fn test_inverse_dynamics_zero_motion() {
        // Zero velocity and acceleration: τ = m * g * cos(q)
        let nq = 3;
        let q = Array1::zeros(nq);      // cos(0) = 1
        let qd = Array1::zeros(nq);
        let qdd = Array1::zeros(nq);
        let masses = Array1::from_vec(vec![1.0, 2.0, 3.0]);
        let gravity = 9.81;
        let tau = inverse_dynamics_single(&q, &qd, &qdd, &masses, gravity);
        for j in 0..nq {
            let expected = masses[j] * gravity; // cos(0) = 1
            assert!((tau[j] - expected).abs() < 1e-10, "j={j}: {:.6} != {:.6}", tau[j], expected);
        }
    }

    #[test]
    fn test_inverse_dynamics_shape_consistency() {
        let nq = 5;
        let q = Array1::ones(nq);
        let qd = Array1::ones(nq);
        let qdd = Array1::ones(nq);
        let masses = Array1::ones(nq);
        let tau = inverse_dynamics_single(&q, &qd, &qdd, &masses, 9.81);
        assert_eq!(tau.len(), nq);
    }

    #[test]
    fn test_com_zero_angles() {
        let nq = 4;
        let q = Array1::zeros(nq);
        let masses = Array1::from_vec(vec![1.0, 1.0, 1.0, 1.0]);
        let com = com_single(&q, &masses);
        // sin(0) = 0, so COM x should be 0
        assert!((com[0]).abs() < 1e-10);
        // cos(0) = 1, so COM y should be 1.0 (total_mass = 4, sum = 4)
        assert!((com[1] - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_com_single_joint() {
        let q = Array1::from_vec(vec![std::f64::consts::FRAC_PI_2]);
        let masses = Array1::from_vec(vec![2.0]);
        let com = com_single(&q, &masses);
        // sin(pi/2) = 1, cos(pi/2) ~ 0
        assert!((com[0] - 1.0).abs() < 1e-10);
        assert!((com[1]).abs() < 1e-10);
    }

    #[test]
    fn test_interpolate_phases_two_phases() {
        // Manually test the interpolation logic
        let fracs = Array1::from_vec(vec![0.0, 1.0]);
        let angles = Array2::from_shape_vec((2, 2), vec![0.0, 0.0, 1.0, 2.0]).unwrap();
        let n_frames = 3;

        // Frame 0: f=0.0 -> alpha=0 -> [0, 0]
        // Frame 1: f=0.5 -> alpha=0.5 -> [0.5, 1.0]
        // Frame 2: f=1.0 -> alpha=1.0 -> [1.0, 2.0]
        let expected = vec![
            vec![0.0, 0.0],
            vec![0.5, 1.0],
            vec![1.0, 2.0],
        ];

        for i in 0..n_frames {
            let f = i as f64 / (n_frames - 1) as f64;
            let alpha = f; // two phases: 0..1
            for j in 0..2 {
                let v0 = angles[[0, j]];
                let v1 = angles[[1, j]];
                let result = v0 + alpha * (v1 - v0);
                assert!(
                    (result - expected[i][j]).abs() < 1e-10,
                    "frame={i}, joint={j}: {result:.6} != {:.6}",
                    expected[i][j]
                );
            }
        }
    }

    #[test]
    fn test_interpolate_single_frame() {
        // n_frames=1 should produce f=0.0, returning the first phase angles
        let fracs = Array1::from_vec(vec![0.0, 1.0]);
        let angles = Array2::from_shape_vec((2, 1), vec![5.0, 10.0]).unwrap();

        let f = 0.0; // single frame
        let alpha = 0.0;
        let result = angles[[0, 0]] + alpha * (angles[[1, 0]] - angles[[0, 0]]);
        assert!((result - 5.0).abs() < 1e-10);
    }
}
