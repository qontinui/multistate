"""MultiState: Multi-State Pathfinding & Traversal Library

A Python library for managing multiple simultaneous active states with
intelligent pathfinding and coordinated transitions.
"""

__version__ = "0.1.0"

from multistate.core.element import Element
from multistate.core.state import State
from multistate.core.state_group import StateGroup
from multistate.manager import StateManager, StateManagerConfig
from multistate.metrics import MetricsManager, StateMetrics, TransitionMetrics
from multistate.state_references import (
    StateHistory,
    StateReference,
    StateReferenceResolver,
    StateSnapshot,
)

__all__ = [
    "Element",
    "State",
    "StateGroup",
    "StateManager",
    "StateManagerConfig",
    "MetricsManager",
    "StateMetrics",
    "TransitionMetrics",
    "StateHistory",
    "StateReference",
    "StateReferenceResolver",
    "StateSnapshot",
]

# Testing module (always available, but some features require optional dependencies)
# Use: pip install multistate[testing] for full screenshot support
# Use: pip install multistate[yaml] for YAML config support
# Use: pip install multistate[all] for everything
try:
    from multistate import testing  # noqa: F401

    __all__.append("testing")
except ImportError:
    pass  # Testing module not available

# Transition system (available now)
try:
    from multistate.transitions import (  # noqa: F401
        PhaseResult,
        StaysVisible,
        Transition,
        TransitionExecutor,
        TransitionPhase,
        TransitionResult,
    )

    __all__.extend(
        [
            "Transition",
            "TransitionResult",
            "TransitionPhase",
            "PhaseResult",
            "TransitionExecutor",
            "StaysVisible",
        ]
    )
except ImportError:
    pass  # Transition module may have missing dependencies

# These will be imported when implemented
# from multistate.pathfinding.multi_target import MultiTargetPathFinder, Path
# from multistate.api.state_manager import StateManager
