"""MultiState: Multi-State Pathfinding & Traversal Library

A Python library for managing multiple simultaneous active states with
intelligent pathfinding and coordinated transitions.
"""

__version__ = "0.1.0"

from multistate.core.element import Element
from multistate.core.state import State
from multistate.core.state_group import StateGroup

__all__ = [
    "Element",
    "State",
    "StateGroup",
]

# These will be imported when implemented
# from multistate.transitions.transition import Transition, TransitionResult
# from multistate.transitions.executor import TransitionExecutor
# from multistate.pathfinding.multi_target import MultiTargetPathFinder, Path
# from multistate.api.state_manager import StateManager