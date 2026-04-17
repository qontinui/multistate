"""Novelty-seeking exploration strategy."""

import logging

from multistate.testing.config import ExplorationConfig
from multistate.testing.exploration.strategies_impl.base import ExplorationStrategy
from multistate.testing.tracker import PathTracker

logger = logging.getLogger(__name__)


class NoveltySeekingExplorer(ExplorationStrategy):
    """Novelty-seeking exploration that prioritizes unvisited states.

    This strategy maintains per-path visited tracking to maximize
    exploration of new states, inspired by best-first search with
    novelty heuristic. Similar to greedy coverage but tracks local
    path history to avoid revisiting states within a search branch.

    Useful for discovering new states and transitions quickly.
    """

    def __init__(self, config: ExplorationConfig, tracker: PathTracker):
        """Initialize novelty-seeking explorer.

        Args:
            config: Exploration configuration
            tracker: PathTracker instance
        """
        super().__init__(config, tracker)
        self.local_visited: set[str] = set()
        self.exploration_bonus = config.greedy_unexplored_bonus

    def select_next_state(self, current_state: str) -> str | None:
        """Select next state prioritizing novelty.

        Args:
            current_state: Current state name

        Returns:
            Most novel next state, or None if no transitions available
        """
        self.local_visited.add(current_state)

        transitions = self.get_available_transitions(current_state)

        if not transitions:
            return None

        executed_transitions = self.tracker._executed_transitions
        visited_states = self.tracker._visited_states

        # Sort transitions by novelty (prefer unvisited states)
        # Tuple sorting: (local_visited, global_visited, transition_executed)
        sorted_transitions = sorted(
            transitions,
            key=lambda t: (
                t[1] in self.local_visited,  # Local path tracking (best: False)
                t[1] in visited_states,  # Global visited (better: False)
                t in executed_transitions,  # Transition executed (ok: False)
            ),
        )

        # Select most novel transition
        _, next_state = sorted_transitions[0]

        logger.debug(
            f"Novelty: {current_state} -> {next_state} "
            f"(local_visited: {len(self.local_visited)})"
        )

        return next_state

    def reset(self) -> None:
        """Reset local visited tracking."""
        self.local_visited.clear()
