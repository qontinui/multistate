"""Path Analysis - Provides graph analysis and path suggestion algorithms.

This module provides pathfinding and analysis functionality separated from
the main PathTracker to improve modularity and maintainability.
"""

import logging
from typing import Any

from multistate.testing.models import PathHistory, TransitionStatistics

logger = logging.getLogger(__name__)


class PathAnalyzer:
    """Analyzes state graphs and suggests optimal paths for exploration.

    This class handles:
    - State reachability analysis using graph algorithms
    - Transition priority calculation
    - Critical path identification

    Thread Safety:
        This class is stateless and thread-safe.
    """

    def analyze_reachability(self, state_graph: Any) -> dict[str, list[str]]:
        """Analyze state reachability from initial state.

        Args:
            state_graph: State graph to analyze

        Returns:
            Dictionary mapping state names to list of reachable states
        """
        try:
            import networkx as nx
        except ImportError:
            logger.warning("networkx not available, skipping reachability analysis")
            return {}

        # Build graph
        G: Any = nx.DiGraph()

        if hasattr(state_graph, "states"):
            for state_name, state in state_graph.states.items():
                G.add_node(state_name)
                if hasattr(state, "transitions"):
                    for transition in state.transitions:
                        to_s = getattr(transition, "to_state", None)
                        if to_s:
                            G.add_edge(state_name, to_s)

        # Calculate reachability from initial state
        reachability = {}
        initial = getattr(state_graph, "initial_state", None)

        if initial and hasattr(state_graph, "states"):
            for state_name in state_graph.states:
                if nx.has_path(G, initial, state_name):
                    reachability[state_name] = [state_name]
                else:
                    reachability[state_name] = []

        return reachability

    def suggest_next_transitions(
        self,
        state_graph: Any,
        current_state: str,
        visited_states: set[str],
        executed_transitions: set[tuple[str, str]],
        transition_stats: dict[tuple[str, str], TransitionStatistics],
        prioritize_unexplored: bool = True,
    ) -> list[tuple[str, float]]:
        """Suggest next transitions to maximize coverage.

        Args:
            state_graph: State graph
            current_state: Current state
            visited_states: Set of visited states
            executed_transitions: Set of executed transitions
            transition_stats: Dictionary of transition statistics
            prioritize_unexplored: Prioritize unexplored transitions

        Returns:
            List of (to_state, priority_score) tuples, sorted by priority
        """
        suggestions = []

        # Get current state transitions
        if not hasattr(state_graph, "states"):
            return []

        state = state_graph.states.get(current_state)
        if not state or not hasattr(state, "transitions"):
            return []

        # Score each possible transition
        for transition in state.transitions:
            to_state = getattr(transition, "to_state", None)
            if not to_state:
                continue

            transition_key = (current_state, to_state)

            # Base priority
            priority = 1.0

            # Boost unexplored
            if prioritize_unexplored and transition_key not in executed_transitions:
                priority *= 2.0

            # Boost if leads to unvisited state
            if to_state not in visited_states:
                priority *= 1.5

            # Reduce if unstable
            if transition_key in transition_stats:
                stats = transition_stats[transition_key]
                if stats.is_unreliable:
                    priority *= 0.5

            suggestions.append((to_state, priority))

        # Sort by priority
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions

    def get_critical_path(
        self,
        paths: list[PathHistory],
        start_state: str,
        end_state: str,
    ) -> PathHistory | None:
        """Get the critical path between two states.

        Args:
            paths: List of path histories
            start_state: Starting state
            end_state: Target state

        Returns:
            PathHistory for critical path (shortest successful), or None if no path found
        """
        # Find all paths that match
        matching_paths = [
            p
            for p in paths
            if p.start_state == start_state and p.end_state == end_state and p.success
        ]

        if not matching_paths:
            return None

        # Return shortest successful path
        return min(matching_paths, key=lambda p: p.length)
