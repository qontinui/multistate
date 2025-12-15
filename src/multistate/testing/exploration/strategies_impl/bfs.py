"""Breadth-first search exploration strategy."""

import logging
from collections import deque

from multistate.testing.config import ExplorationConfig
from multistate.testing.exploration.strategies_impl.base import ExplorationStrategy
from multistate.testing.tracker import PathTracker

logger = logging.getLogger(__name__)


class BreadthFirstExplorer(ExplorationStrategy):
    """Breadth-first search exploration strategy.

    Explores states level by level, useful for finding shortest paths
    and ensuring broad coverage before going deep.
    """

    def __init__(self, config: ExplorationConfig, tracker: PathTracker):
        """Initialize BFS explorer.

        Args:
            config: Exploration configuration
            tracker: PathTracker instance
        """
        super().__init__(config, tracker)
        self.queue: deque[str] = deque()
        self.visited_this_run: set[str] = set()
        self.max_breadth = config.bfs_max_breadth

    def select_next_state(self, current_state: str) -> str | None:
        """Select next state using BFS.

        Args:
            current_state: Current state name

        Returns:
            Next state via BFS, or None if no more states
        """
        # Add current state to visited
        self.visited_this_run.add(current_state)

        # Get all transitions from current state
        transitions = self.get_available_transitions(current_state)

        # Add unvisited states to queue
        for _, to_state in transitions:
            if to_state not in self.visited_this_run and to_state not in self.queue:
                if len(self.queue) < self.max_breadth:
                    self.queue.append(to_state)

        # Get next state from queue
        if self.queue:
            next_state = self.queue.popleft()
            logger.debug(
                f"BFS: {current_state} -> {next_state} (queue: {len(self.queue)})"
            )
            return next_state

        logger.debug("BFS queue exhausted")
        return None

    def reset(self) -> None:
        """Reset BFS state."""
        self.queue.clear()
        self.visited_this_run.clear()
