"""Base exploration strategy abstract class.

This module defines the ExplorationStrategy ABC that all concrete
exploration strategies must implement.
"""

import logging
from abc import ABC, abstractmethod

from multistate.testing.config import ExplorationConfig
from multistate.testing.tracker import PathTracker

logger = logging.getLogger(__name__)


class ExplorationStrategy(ABC):
    """Base class for exploration strategies.

    All exploration strategies must implement the select_next_state method
    to determine which state to transition to next.
    """

    def __init__(self, config: ExplorationConfig, tracker: PathTracker):
        """Initialize exploration strategy.

        Args:
            config: Exploration configuration
            tracker: PathTracker instance for metrics and history
        """
        self.config = config
        self.tracker = tracker
        self.state_graph = tracker.state_graph

    @abstractmethod
    def select_next_state(self, current_state: str) -> str | None:
        """Select the next state to transition to.

        Args:
            current_state: Current state name

        Returns:
            Next state name, or None if no valid transition available
        """
        pass

    def get_available_transitions(self, state_name: str) -> list[tuple[str, str]]:
        """Get available transitions from a state.

        Args:
            state_name: State to get transitions from

        Returns:
            List of (from_state, to_state) tuples
        """
        transitions: list[tuple[str, str]] = []

        if not hasattr(self.state_graph, "states"):
            return transitions

        state = self.state_graph.states.get(state_name)
        if not state or not hasattr(state, "transitions"):
            return transitions

        for transition in state.transitions:
            to_state = getattr(transition, "to_state", None)
            if to_state:
                transitions.append((state_name, to_state))

        return transitions

    def reset(self) -> None:  # noqa: B027
        """Reset strategy state for stateful strategies.

        This is a no-op by default. Stateful strategies should override
        this method to clear any accumulated state between exploration runs.
        """
        pass  # Intentional no-op for stateless strategies
