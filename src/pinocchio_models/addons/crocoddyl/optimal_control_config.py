"""Named constants for the Crocoddyl optimal-control problem.

Split out of :mod:`optimal_control` to keep the public module focused
on orchestration. These weights and physics constants are re-exported
from the facade for backward compatibility.
"""

from __future__ import annotations

# --- Cost weights used in the running and terminal cost models. ---
EFFORT_COST_WEIGHT: float = 1e-3
STATE_REG_RUNNING_WEIGHT: float = 1e-1
STATE_REG_TERMINAL_WEIGHT: float = 1.0
FRICTION_COST_WEIGHT: float = 1e-2

# Baumgarte stabilisation gains for bilateral foot-ground contacts.
CONTACT_BAUMGARTE_GAINS: tuple[float, float] = (0.0, 50.0)

# Ground friction coefficient (Coulomb) and friction cone facets.
GROUND_FRICTION_MU: float = 0.8
FRICTION_CONE_FACETS: int = 4
