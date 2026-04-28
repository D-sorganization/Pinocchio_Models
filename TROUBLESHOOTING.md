# TROUBLESHOOTING

## Installation Issues

### `ModuleNotFoundError: No module named 'pinocchio'`

Pinocchio is an optional dependency. Install it with:

```bash
pip install -e ".[pinocchio]"
```

Or install all optional add-ons:

```bash
pip install -e ".[all-addons]"
```

### `pip install -e .` fails with "No module named hatchling"

Make sure you have a recent `pip` and `setuptools`:

```bash
pip install --upgrade pip setuptools wheel
```

Then retry the editable install.

## Runtime Issues

### Viewer does not open (Gepetto)

Gepetto Viewer requires a running `gepetto-gui` instance and the
`gepetto-viewer-corba` package:

```bash
pip install -e ".[gepetto]"
gepetto-gui &
python -m pinocchio_models squat --viewer
```

If the viewer still does not appear, check that port 12321 is not
blocked by a firewall.

### `URDF file not found` error

The package looks for URDF files relative to the installed package
location. If you are running from the repository root without an
editable install, the data files may not be resolved correctly.

**Fix:** always install in editable mode during development:

```bash
pip install -e .
```

### Slow IK convergence with Pink

The default tolerance (`1e-4`) may be too tight for complex poses.
Increase it in the configuration or reduce the number of iterations
if real-time performance is required.

## Reporting New Issues

If you encounter a problem not listed here, please open a GitHub
issue with:

1. The exact command you ran
2. The full traceback or error message
3. Your Python version (`python --version`)
4. Your OS and architecture