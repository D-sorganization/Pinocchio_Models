# ADR 001: Use Pinocchio for Rigid-Body Dynamics

## Status
Accepted

## Context
The project needs a rigid-body dynamics library for multibody simulation of barbell exercises. Candidates included Pinocchio, RBDL, and custom implementations.

## Decision
We chose [Pinocchio](https://github.com/stack-of-tasks/pinocchio) because:
- It provides analytical derivatives (Jacobian, Hessian) needed for optimal control.
- It has mature Python bindings and active maintenance.
- It integrates well with Crocoddyl for optimal control and Pink for IK.

## Consequences
- **Positive:** Fast dynamics computation, rich ecosystem, good documentation.
- **Negative:** Adds a heavy C++ dependency; users must install Pinocchio (often from conda-forge or robotpkg).

## Date
2026-01-15
