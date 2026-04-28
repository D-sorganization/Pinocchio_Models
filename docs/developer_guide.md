# Developer Guide

## Getting Started

### Prerequisites

- Python 3.10+
- [Pinocchio](https://stack-of-tasks.github.io/pinocchio/) 3.0+
- NumPy 1.24+

### Installation

```bash
git clone https://github.com/D-sorganization/Pinocchio_Models.git
cd Pinocchio_Models
pip install -e ".[dev]"
```

### Generate Models

```bash
python examples/generate_all_models.py --output-dir ./models
```

## Project Structure

```
pinocchio_models/
├── addons/          # Optional integrations (gepetto, pink, crocoddyl)
├── exercises/       # Exercise-specific URDF builders
├── shared/          # Body model, barbell, and joint builders
├── exceptions.py    # Structured error types
└── py.typed         # PEP 561 typing marker
```

## Adding a New Exercise

1. Create `exercises/<name>/<name>_model.py`
2. Implement `build_<name>_model() -> str` returning URDF XML
3. Add entry to `examples/generate_all_models.py`
4. Add tests in `tests/exercises/test_<name>.py`

## Testing

```bash
pytest tests/ -v
```

## Code Style

- Format with `black src/ tests/`
- Import sort with `isort src/ tests/`
- Type check with `mypy src/`