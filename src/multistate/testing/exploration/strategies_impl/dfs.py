"""Depth-first search exploration strategy."""

import logging
from collections import deque

from multistate.testing.config import ExplorationConfig
from multistate.testing.exploration.strategies_impl.base import ExplorationStrategy
from multistate.testing.tracker import PathTracker

logger = logging.getLogger(__name__)


class DepthFirstExplorer(ExplorationStrategy):
    """Depth-first search exploration strategy.

    Explores paths deeply before backtracking, useful for finding
    long execution sequences and deep states.
    """

    def __init__(self, config: ExplorationConfig, tracker: PathTracker):
        """Initialize DFS explorer.

        Args:
            config: Exploration configuration
            tracker: PathTracker instance
        """
        super().__init__(config, tracker)
        self.visited_stack: deque[str] = deque()
        self.depth = 0
        self.max_depth = config.dfs_max_depth

    def select_next_state(self, current_state: str) -> str | None:
        """Select next state using DFS.

        Args:
            current_state: Current state name

        Returns:
            Next state via DFS, or None if max depth reached
        """
        # Check depth limit
        if self.depth >= self.max_depth:
            logger.debug(f"DFS max depth {self.max_depth} reached, backtracking")
            return self._backtrack()

        transitions = self.get_available_transitions(current_state)

        if not transitions:
            return self._backtrack()

        # Prioritize unexplored transitions
        executed_transitions = self.tracker._executed_transitions
        unexplored = [
            (f, t) for f, t in transitions if (f, t) not in executed_transitions
        ]

        if unexplored:
            _, next_state = unexplored[0]
        else:
            # All explored, take first available
            _, next_state = transitions[0]

        # Update stack and depth
        self.visited_stack.append(current_state)
        self.depth += 1

        logger.debug(f"DFS: {current_state} -> {next_state} (depth: {self.depth})")
        return next_state

    def _backtrack(self) -> str | None:
        """Backtrack to previous state.

        Returns:
            Previous state, or None if stack is empty
        """
        if self.visited_stack:
            prev_state = self.visited_stack.pop()
            self.depth = len(self.visited_stack)
            logger.debug(f"DFS backtrack to {prev_state}")
            return prev_state

        return None

    def reset(self) -> None:
        """Reset DFS state."""
        self.visited_stack.clear()
        self.depth = 0
