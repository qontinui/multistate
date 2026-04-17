"""Greedy coverage-maximizing exploration strategy."""

import logging

from multistate.testing.exploration.strategies_impl.base import ExplorationStrategy

logger = logging.getLogger(__name__)


class GreedyCoverageExplorer(ExplorationStrategy):
    """Greedy coverage-maximizing exploration strategy.

    Prioritizes unexplored transitions and states to maximize coverage quickly.
    Uses heuristics to score transitions based on exploration value.
    """

    def select_next_state(self, current_state: str) -> str | None:
        """Select next state greedily to maximize coverage.

        Args:
            current_state: Current state name

        Returns:
            Best next state for coverage, or None if no transitions available
        """
        transitions = self.get_available_transitions(current_state)

        if not transitions:
            return None

        # Score each transition
        scored_transitions = []
        executed_transitions = self.tracker._executed_transitions
        visited_states = self.tracker._visited_states
        transition_stats = self.tracker._transition_stats

        for from_state, to_state in transitions:
            score = 1.0
            transition_key = (from_state, to_state)

            # Bonus for unexplored transitions
            if transition_key not in executed_transitions:
                score *= self.config.greedy_unexplored_bonus

            # Bonus for unvisited states
            if to_state not in visited_states:
                score *= self.config.greedy_unvisited_state_bonus

            # Penalty for unstable transitions
            if transition_key in transition_stats:
                stats = transition_stats[transition_key]
                if stats.is_unreliable:
                    score *= self.config.greedy_unstable_penalty

            scored_transitions.append((to_state, score))

        # Select highest scoring transition
        scored_transitions.sort(key=lambda x: x[1], reverse=True)
        next_state, score = scored_transitions[0]

        logger.debug(f"Greedy: {current_state} -> {next_state} (score: {score:.2f})")
        return next_state
