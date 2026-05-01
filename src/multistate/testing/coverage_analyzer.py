"""Coverage Analyzer - Calculates coverage metrics for state machine testing.

This module provides coverage analysis functionality separated from
the main PathTracker to improve modularity and maintainability.
"""

import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from multistate.testing.enums import ExecutionStatus
from multistate.testing.models import CoverageMetrics, PathHistory, TransitionExecution

logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """Analyzes and calculates coverage metrics for state machine testing.

    This class handles all coverage-related calculations including:
    - State coverage (visited/unvisited states)
    - Transition coverage (executed/unexecuted transitions)
    - Execution statistics
    - Path metrics
    - Time metrics

    Thread Safety:
        This class is stateless and thread-safe.
    """

    def calculate_metrics(
        self,
        state_graph: Any,
        visited_states: set[str],
        executed_transitions: set[tuple[str, str]],
        executions: Sequence[TransitionExecution],
        paths: Sequence[PathHistory],
    ) -> CoverageMetrics:
        """Calculate comprehensive coverage metrics.

        Args:
            state_graph: State graph to analyze coverage against
            visited_states: Set of visited state names
            executed_transitions: Set of executed transitions (from_state, to_state)
            executions: Sequence of transition executions
            paths: Sequence of path histories

        Returns:
            CoverageMetrics with complete coverage analysis
        """
        # State coverage
        total_states = len(state_graph.states) if hasattr(state_graph, "states") else 0
        visited_count = len(visited_states)
        unvisited_states = []
        if hasattr(state_graph, "states"):
            unvisited_states = [
                name for name in state_graph.states if name not in visited_states
            ]

        # Transition coverage
        all_transitions = self._extract_all_transitions(state_graph)
        total_transitions = len(all_transitions)
        executed_count = len(executed_transitions)
        unexecuted_transitions = list(all_transitions - executed_transitions)

        # Execution metrics
        total_executions = len(executions)
        successful = sum(1 for e in executions if e.status == ExecutionStatus.SUCCESS)
        failed = sum(1 for e in executions if e.status == ExecutionStatus.FAILURE)
        errors = sum(1 for e in executions if e.status == ExecutionStatus.ERROR)

        # Path metrics
        unique_paths = len(paths)
        longest_path = max((p.length for p in paths), default=0)
        avg_path_length = sum(p.length for p in paths) / len(paths) if paths else 0.0

        # Time metrics
        total_time = sum(e.duration_ms for e in executions)
        avg_time = total_time / total_executions if total_executions > 0 else 0.0

        return CoverageMetrics(
            total_states=total_states,
            visited_states=visited_count,
            unvisited_states=unvisited_states,
            total_transitions=total_transitions,
            executed_transitions=executed_count,
            unexecuted_transitions=unexecuted_transitions,
            total_executions=total_executions,
            successful_executions=successful,
            failed_executions=failed,
            error_executions=errors,
            unique_paths=unique_paths,
            longest_path_length=longest_path,
            average_path_length=avg_path_length,
            total_execution_time_ms=total_time,
            average_transition_time_ms=avg_time,
            calculated_at=datetime.now(),
        )

    def get_unexplored_transitions(
        self,
        state_graph: Any,
        executed_transitions: set[tuple[str, str]],
    ) -> list[tuple[str, str]]:
        """Get list of transitions that have never been executed.

        Args:
            state_graph: State graph to analyze
            executed_transitions: Set of executed transitions

        Returns:
            List of (from_state, to_state) tuples for unexplored transitions
        """
        all_transitions = self._extract_all_transitions(state_graph)
        return list(all_transitions - executed_transitions)

    def _extract_all_transitions(self, state_graph: Any) -> set[tuple[str, str]]:
        """Extract all possible transitions from state graph.

        Args:
            state_graph: State graph to extract transitions from

        Returns:
            Set of (from_state, to_state) tuples
        """
        all_transitions = set()

        if hasattr(state_graph, "states"):
            for state in state_graph.states.values():
                if hasattr(state, "transitions"):
                    for transition in state.transitions:
                        from_s = getattr(transition, "from_state", state.name)
                        to_s = getattr(transition, "to_state", None)
                        if to_s:
                            all_transitions.add((from_s, to_s))

        return all_transitions
