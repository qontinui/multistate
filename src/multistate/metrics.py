"""Metrics tracking for states and transitions.

This module provides optional metrics tracking for monitoring state machine behavior,
including visit counts, success rates, and execution statistics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class StateMetrics:
    """Metrics for a single state.

    Tracks usage statistics and execution data for individual states
    in the state machine.

    Attributes:
        state_id: ID of the state being tracked
        visit_count: Number of times this state has been activated
        last_visited: Timestamp of last activation
        total_time_active: Total time spent in this state (seconds)
        activation_count: Count of individual activations (may differ from visit_count)
        deactivation_count: Count of deactivations
        is_currently_active: Whether the state is currently active
    """

    state_id: str
    visit_count: int = 0
    last_visited: Optional[datetime] = None
    total_time_active: float = 0.0
    activation_count: int = 0
    deactivation_count: int = 0
    is_currently_active: bool = False

    # Internal tracking
    _last_activation_time: Optional[datetime] = field(default=None, repr=False)

    def record_activation(self) -> None:
        """Record a state activation."""
        self.activation_count += 1
        self.visit_count += 1
        self.last_visited = datetime.now()
        self.is_currently_active = True
        self._last_activation_time = datetime.now()

    def record_deactivation(self) -> None:
        """Record a state deactivation."""
        self.deactivation_count += 1
        self.is_currently_active = False

        # Track time if we have activation timestamp
        if self._last_activation_time is not None:
            duration = (datetime.now() - self._last_activation_time).total_seconds()
            self.total_time_active += duration
            self._last_activation_time = None

    def get_average_time_active(self) -> float:
        """Calculate average time spent active.

        Returns:
            Average seconds per activation, or 0 if never activated
        """
        if self.activation_count == 0:
            return 0.0
        return self.total_time_active / self.activation_count

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        self.visit_count = 0
        self.last_visited = None
        self.total_time_active = 0.0
        self.activation_count = 0
        self.deactivation_count = 0
        self.is_currently_active = False
        self._last_activation_time = None


@dataclass
class TransitionMetrics:
    """Metrics for a single transition.

    Tracks execution statistics and success rates for transitions.

    Attributes:
        transition_id: ID of the transition being tracked
        execution_count: Total number of execution attempts
        success_count: Number of successful executions
        failure_count: Number of failed executions
        last_executed: Timestamp of last execution attempt
        total_execution_time: Total time spent executing (seconds)
        average_execution_time: Running average of execution time
    """

    transition_id: str
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_executed: Optional[datetime] = None
    total_execution_time: float = 0.0

    def record_execution(self, success: bool, execution_time: float = 0.0) -> None:
        """Record a transition execution.

        Args:
            success: Whether the execution succeeded
            execution_time: Time taken to execute in seconds
        """
        self.execution_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.last_executed = datetime.now()
        self.total_execution_time += execution_time

    def get_success_rate(self) -> float:
        """Calculate success rate as a percentage.

        Returns:
            Success rate from 0.0 to 1.0, or 0.0 if never executed
        """
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count

    def get_average_execution_time(self) -> float:
        """Calculate average execution time.

        Returns:
            Average seconds per execution, or 0.0 if never executed
        """
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_time / self.execution_count

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_executed = None
        self.total_execution_time = 0.0


class MetricsManager:
    """Manager for tracking state and transition metrics.

    Provides centralized metrics collection and querying for state machines.
    Can be enabled/disabled for production vs. development use.

    Example:
        >>> manager = MetricsManager()
        >>> manager.record_state_activation("login")
        >>> manager.record_transition_execution("login_success", True, 0.5)
        >>> metrics = manager.get_state_metrics("login")
        >>> print(f"Visited {metrics.visit_count} times")
    """

    def __init__(self, enabled: bool = True):
        """Initialize metrics manager.

        Args:
            enabled: Whether metrics tracking is active
        """
        self.enabled = enabled
        self.state_metrics: Dict[str, StateMetrics] = {}
        self.transition_metrics: Dict[str, TransitionMetrics] = {}

    def _ensure_state_metrics(self, state_id: str) -> StateMetrics:
        """Get or create state metrics.

        Args:
            state_id: State to track

        Returns:
            StateMetrics instance for the state
        """
        if state_id not in self.state_metrics:
            self.state_metrics[state_id] = StateMetrics(state_id=state_id)
        return self.state_metrics[state_id]

    def _ensure_transition_metrics(self, transition_id: str) -> TransitionMetrics:
        """Get or create transition metrics.

        Args:
            transition_id: Transition to track

        Returns:
            TransitionMetrics instance for the transition
        """
        if transition_id not in self.transition_metrics:
            self.transition_metrics[transition_id] = TransitionMetrics(
                transition_id=transition_id
            )
        return self.transition_metrics[transition_id]

    def record_state_activation(self, state_id: str) -> None:
        """Record a state activation.

        Args:
            state_id: ID of state being activated
        """
        if not self.enabled:
            return
        metrics = self._ensure_state_metrics(state_id)
        metrics.record_activation()

    def record_state_deactivation(self, state_id: str) -> None:
        """Record a state deactivation.

        Args:
            state_id: ID of state being deactivated
        """
        if not self.enabled:
            return
        metrics = self._ensure_state_metrics(state_id)
        metrics.record_deactivation()

    def record_transition_execution(
        self, transition_id: str, success: bool, execution_time: float = 0.0
    ) -> None:
        """Record a transition execution.

        Args:
            transition_id: ID of transition executed
            success: Whether execution succeeded
            execution_time: Time taken in seconds
        """
        if not self.enabled:
            return
        metrics = self._ensure_transition_metrics(transition_id)
        metrics.record_execution(success, execution_time)

    def get_state_metrics(self, state_id: str) -> Optional[StateMetrics]:
        """Get metrics for a state.

        Args:
            state_id: State to query

        Returns:
            StateMetrics if tracked, None otherwise
        """
        return self.state_metrics.get(state_id)

    def get_transition_metrics(self, transition_id: str) -> Optional[TransitionMetrics]:
        """Get metrics for a transition.

        Args:
            transition_id: Transition to query

        Returns:
            TransitionMetrics if tracked, None otherwise
        """
        return self.transition_metrics.get(transition_id)

    def get_all_state_metrics(self) -> Dict[str, StateMetrics]:
        """Get all state metrics.

        Returns:
            Dictionary mapping state IDs to their metrics
        """
        return self.state_metrics.copy()

    def get_all_transition_metrics(self) -> Dict[str, TransitionMetrics]:
        """Get all transition metrics.

        Returns:
            Dictionary mapping transition IDs to their metrics
        """
        return self.transition_metrics.copy()

    def get_most_visited_states(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get the most frequently visited states.

        Args:
            limit: Maximum number of states to return

        Returns:
            List of (state_id, visit_count) tuples, sorted descending
        """
        items = [(sid, m.visit_count) for sid, m in self.state_metrics.items()]
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:limit]

    def get_most_executed_transitions(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get the most frequently executed transitions.

        Args:
            limit: Maximum number of transitions to return

        Returns:
            List of (transition_id, execution_count) tuples, sorted descending
        """
        items = [(tid, m.execution_count) for tid, m in self.transition_metrics.items()]
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:limit]

    def get_transition_success_rates(self) -> Dict[str, float]:
        """Get success rates for all transitions.

        Returns:
            Dictionary mapping transition IDs to success rates (0.0-1.0)
        """
        return {
            tid: metrics.get_success_rate()
            for tid, metrics in self.transition_metrics.items()
        }

    def get_currently_active_states(self) -> list[str]:
        """Get list of currently active states.

        Returns:
            List of state IDs that are currently active
        """
        return [
            sid
            for sid, metrics in self.state_metrics.items()
            if metrics.is_currently_active
        ]

    def reset_all(self) -> None:
        """Reset all metrics to initial state."""
        for metrics in self.state_metrics.values():
            metrics.reset()
        for metrics in self.transition_metrics.values():
            metrics.reset()

    def reset_state_metrics(self, state_id: str) -> None:
        """Reset metrics for a specific state.

        Args:
            state_id: State to reset
        """
        if state_id in self.state_metrics:
            self.state_metrics[state_id].reset()

    def reset_transition_metrics(self, transition_id: str) -> None:
        """Reset metrics for a specific transition.

        Args:
            transition_id: Transition to reset
        """
        if transition_id in self.transition_metrics:
            self.transition_metrics[transition_id].reset()

    def enable(self) -> None:
        """Enable metrics tracking."""
        self.enabled = True

    def disable(self) -> None:
        """Disable metrics tracking."""
        self.enabled = False

    def get_summary(self) -> Dict[str, any]:
        """Get a summary of all metrics.

        Returns:
            Dictionary with overview statistics
        """
        total_state_visits = sum(m.visit_count for m in self.state_metrics.values())
        total_transitions = sum(
            m.execution_count for m in self.transition_metrics.values()
        )
        total_successful = sum(
            m.success_count for m in self.transition_metrics.values()
        )

        return {
            "enabled": self.enabled,
            "states_tracked": len(self.state_metrics),
            "transitions_tracked": len(self.transition_metrics),
            "total_state_visits": total_state_visits,
            "total_transition_executions": total_transitions,
            "total_successful_transitions": total_successful,
            "overall_success_rate": (
                total_successful / total_transitions if total_transitions > 0 else 0.0
            ),
            "currently_active_states": self.get_currently_active_states(),
        }

    def __repr__(self) -> str:
        """String representation."""
        summary = self.get_summary()
        return (
            f"MetricsManager(enabled={summary['enabled']}, "
            f"states={summary['states_tracked']}, "
            f"transitions={summary['transitions_tracked']}, "
            f"visits={summary['total_state_visits']}, "
            f"executions={summary['total_transition_executions']})"
        )
