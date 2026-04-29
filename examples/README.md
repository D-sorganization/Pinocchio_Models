# Examples

This directory contains runnable examples for the `pinocchio-models` package.

## Quick Start

```bash
# Generate all exercise models
python examples/generate_all_models.py

# Basic usage without optional dependencies
python examples/basic_usage.py
```

## Addon Examples

When optional dependencies are installed:

- `crocoddyl_optimal_control.py` — Crocoddyl trajectory optimization
- `gepetto_visualization.py` — Gepetto Viewer 3D visualization
- `pink_inverse_kinematics.py` — Pink IK solver integration

## Running with Dependencies

```bash
# Pinocchio only
pip install -e ".[pinocchio]"

# All addons
pip install -e ".[all-addons]"
```
