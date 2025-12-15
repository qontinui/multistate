"""State Manager Information - Provides analysis and reporting for StateManager.

This module provides analysis and information retrieval functionality
separated from the main StateManager to improve modularity.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from multistate.core.state import State
from multistate.metrics import MetricsManager, StateMetrics, TransitionMetrics

logger = logging.getLogger(__name__)


class StateManagerInfo:
    """Provides analysis and information retrieval for StateManager.

    This class handles:
    - Complexity analysis
    - State reachability analysis
    - State information formatting
    - Metrics retrieval and summaries

    Thread Safety:
        Read-only operations are thread-safe.
    """

    def __init__(self, metrics_manager: MetricsManager) -> None:
        """Initialize StateManagerInfo.

        Args:
            metrics_manager: MetricsManager instance to query
        """
        self.metrics = metrics_manager

    def analyze_complexity(
        self,
        states: Dict[str, State],
        transitions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze state machine complexity metrics.

        Args:
            states: Dictionary of states
            transitions: Dictionary of transitions

        Returns:
            Dictionary with complexity analysis
        """
        total_states = len(states)
        total_transitions = len(transitions)

        # Count transitions per state
        transitions_per_state: dict[str, int] = {}
        for trans in transitions.values():
            from_state = getattr(trans, "from_state", None)
            if from_state:
                transitions_per_state[from_state] = (
                    transitions_per_state.get(from_state, 0) + 1
                )

        avg_transitions = (
            sum(transitions_per_state.values()) / len(transitions_per_state)
            if transitions_per_state
            else 0
        )

        # Cyclomatic complexity estimate
        cyclomatic_complexity = total_transitions - total_states + 2

        return {
            "total_states": total_states,
            "total_transitions": total_transitions,
            "avg_transitions_per_state": avg_transitions,
            "max_transitions_from_state": max(transitions_per_state.values(), default=0),
            "cyclomatic_complexity": cyclomatic_complexity,
        }

    def get_reachable_states(
        self,
        states: Dict[str, State],
        transitions: Dict[str, Any],
        from_states: Set[str],
        max_depth: Optional[int] = None,
    ) -> Set[str]:
        """Get all states reachable from given states.

        Args:
            states: Dictionary of all states
            transitions: Dictionary of all transitions
            from_states: Starting states
            max_depth: Maximum search depth (None = unlimited)

        Returns:
            Set of reachable state IDs
        """
        reachable = from_states.copy()
        frontier = from_states.copy()
        depth = 0

        while frontier and (max_depth is None or depth < max_depth):
            next_frontier = set()

            for trans in transitions.values():
                from_state = getattr(trans, "from_state", None)
                to_state = getattr(trans, "to_state", None)

                if from_state in frontier and to_state:
                    if to_state not in reachable:
                        reachable.add(to_state)
                        next_frontier.add(to_state)

            frontier = next_frontier
            depth += 1

        return reachable

    def get_state_info(
        self,
        states: Dict[str, State],
        active_states: Set[State],
        show_groups: bool = True,
    ) -> str:
        """Get formatted state information string.

        Args:
            states: Dictionary of all states
            active_states: Set of currently active states
            show_groups: Whether to show group information

        Returns:
            Formatted multi-line string with state information
        """
        lines = []
        lines.append(f"States: {len(states)}")
        lines.append(f"Active: {len(active_states)}")

        if active_states:
            active_names = [s.name for s in active_states]
            lines.append(f"  {', '.join(sorted(active_names))}")

        if show_groups:
            # Group states by group
            grouped: Dict[str, List[str]] = {}
            for state in states.values():
                group = state.group or "ungrouped"
                if group not in grouped:
                    grouped[group] = []
                grouped[group].append(state.name)

            lines.append("\nGroups:")
            for group, state_names in sorted(grouped.items()):
                lines.append(f"  {group}: {', '.join(sorted(state_names))}")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Metrics Delegation
    # -------------------------------------------------------------------------

    def get_state_metrics(self, state_id: str) -> Optional[StateMetrics]:
        """Get metrics for a specific state.

        Args:
            state_id: State ID

        Returns:
            StateMetrics or None if not tracked
        """
        return self.metrics.get_state_metrics(state_id)

    def get_transition_metrics(self, transition_id: str) -> Optional[TransitionMetrics]:
        """Get metrics for a specific transition.

        Args:
            transition_id: Transition ID

        Returns:
            TransitionMetrics or None if not tracked
        """
        return self.metrics.get_transition_metrics(transition_id)

    def get_most_visited_states(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently visited states.

        Args:
            limit: Maximum number of results

        Returns:
            List of (state_id, visit_count) tuples
        """
        return self.metrics.get_most_visited_states(limit)

    def get_most_executed_transitions(
        self, limit: int = 10
    ) -> List[Tuple[str, int]]:
        """Get most frequently executed transitions.

        Args:
            limit: Maximum number of results

        Returns:
            List of (transition_id, execution_count) tuples
        """
        return self.metrics.get_most_executed_transitions(limit)

    def get_transition_success_rates(self) -> Dict[str, float]:
        """Get success rates for all transitions.

        Returns:
            Dictionary mapping transition_id to success rate (0.0-1.0)
        """
        return self.metrics.get_transition_success_rates()

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics.

        Returns:
            Dictionary with metrics summary
        """
        return self.metrics.get_summary()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics.reset_all()

    def enable_metrics(self) -> None:
        """Enable metrics collection."""
        self.metrics.enable()

    def disable_metrics(self) -> None:
        """Disable metrics collection."""
        self.metrics.disable()
