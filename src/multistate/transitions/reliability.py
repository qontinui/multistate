"""Transition reliability tracking for pathfinding and monitoring.

This module provides reliability metrics for transitions, tracking success/failure
counts and calculating dynamic costs for pathfinding algorithms. The reliability
system enables:

1. Success rate calculation based on execution history
2. Dynamic pathfinding cost adjustment (penalize unreliable transitions)
3. Execution statistics for monitoring and debugging
4. Optional persistence for long-running applications

The reliability tracking is inspired by qontinui's transition scoring system but
adapted for generic state machine usage (no GUI-specific code).
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class TransitionStats:
    """Statistics for a single transition.

    Attributes:
        transition_id: Unique identifier for the transition
        success_count: Number of successful executions
        failure_count: Number of failed executions
        total_time: Total execution time in seconds
        last_success_time: Timestamp of last successful execution
        last_failure_time: Timestamp of last failed execution
        base_cost: Base pathfinding cost (before reliability adjustment)
    """

    transition_id: str
    success_count: int = 0
    failure_count: int = 0
    total_time: float = 0.0
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None
    base_cost: float = 1.0

    @property
    def total_attempts(self) -> int:
        """Total number of execution attempts."""
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        """Success rate as a float between 0.0 and 1.0.

        Returns:
            Success rate, or 1.0 if no attempts yet
        """
        if self.total_attempts == 0:
            return 1.0
        return self.success_count / self.total_attempts

    @property
    def failure_rate(self) -> float:
        """Failure rate as a float between 0.0 and 1.0."""
        return 1.0 - self.success_rate

    @property
    def average_time(self) -> float:
        """Average execution time in seconds.

        Returns:
            Average time, or 0.0 if no attempts yet
        """
        if self.total_attempts == 0:
            return 0.0
        return self.total_time / self.total_attempts

    def record_success(self, execution_time: float = 0.0) -> None:
        """Record a successful execution.

        Args:
            execution_time: Time taken to execute (seconds)
        """
        self.success_count += 1
        self.total_time += execution_time
        self.last_success_time = time.time()

    def record_failure(self, execution_time: float = 0.0) -> None:
        """Record a failed execution.

        Args:
            execution_time: Time taken before failure (seconds)
        """
        self.failure_count += 1
        self.total_time += execution_time
        self.last_failure_time = time.time()

    def to_dict(self) -> Dict[str, any]:
        """Convert stats to dictionary format.

        Returns:
            Dictionary representation of stats
        """
        return {
            "transition_id": self.transition_id,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_attempts": self.total_attempts,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "total_time": self.total_time,
            "average_time": self.average_time,
            "last_success_time": self.last_success_time,
            "last_failure_time": self.last_failure_time,
            "base_cost": self.base_cost,
        }


class ReliabilityTracker:
    """Tracks reliability metrics for all transitions in a state machine.

    The tracker maintains execution statistics for each transition and can
    calculate dynamic pathfinding costs based on reliability. This enables
    the pathfinding algorithm to prefer more reliable transitions.

    Usage:
        tracker = ReliabilityTracker()

        # Record results after executing a transition
        tracker.record_success("login_transition")
        tracker.record_failure("flaky_transition")

        # Get adjusted cost for pathfinding
        cost = tracker.get_dynamic_cost("login_transition", base_cost=1.0)

        # Get statistics
        stats = tracker.get_stats("login_transition")
        print(f"Success rate: {stats.success_rate:.2%}")

    Attributes:
        cost_multiplier_on_failure: How much to increase cost per failure
        min_cost_multiplier: Minimum cost multiplier (floor)
        max_cost_multiplier: Maximum cost multiplier (ceiling)
    """

    def __init__(
        self,
        cost_multiplier_on_failure: float = 2.0,
        min_cost_multiplier: float = 1.0,
        max_cost_multiplier: float = 10.0,
    ):
        """Initialize the reliability tracker.

        Args:
            cost_multiplier_on_failure: Multiplier applied for each failure
                (e.g., 2.0 means cost doubles for a transition with 50% failure rate)
            min_cost_multiplier: Minimum cost multiplier (default 1.0 = base cost)
            max_cost_multiplier: Maximum cost multiplier to prevent infinite costs
        """
        self._stats: Dict[str, TransitionStats] = {}
        self.cost_multiplier_on_failure = cost_multiplier_on_failure
        self.min_cost_multiplier = min_cost_multiplier
        self.max_cost_multiplier = max_cost_multiplier

    def get_stats(self, transition_id: str) -> TransitionStats:
        """Get statistics for a transition, creating if needed.

        Args:
            transition_id: Unique transition identifier

        Returns:
            TransitionStats object
        """
        if transition_id not in self._stats:
            self._stats[transition_id] = TransitionStats(transition_id=transition_id)
        return self._stats[transition_id]

    def record_success(self, transition_id: str, execution_time: float = 0.0) -> None:
        """Record a successful transition execution.

        Args:
            transition_id: Unique transition identifier
            execution_time: Time taken to execute (seconds)
        """
        stats = self.get_stats(transition_id)
        stats.record_success(execution_time)
        logger.debug(
            "Transition %s succeeded (success_rate=%.2f%%)",
            transition_id,
            stats.success_rate * 100,
        )

    def record_failure(self, transition_id: str, execution_time: float = 0.0) -> None:
        """Record a failed transition execution.

        Args:
            transition_id: Unique transition identifier
            execution_time: Time taken before failure (seconds)
        """
        stats = self.get_stats(transition_id)
        stats.record_failure(execution_time)
        logger.warning(
            "Transition %s failed (success_rate=%.2f%%)",
            transition_id,
            stats.success_rate * 100,
        )

    def get_dynamic_cost(
        self,
        transition_id: str,
        base_cost: float = 1.0,
    ) -> float:
        """Calculate dynamic pathfinding cost based on reliability.

        The cost is adjusted based on the failure rate:
        - High success rate → cost ≈ base_cost
        - High failure rate → cost = base_cost * multiplier

        Formula:
            multiplier = 1.0 + (failure_rate * (cost_multiplier_on_failure - 1.0))
            dynamic_cost = base_cost * clamp(multiplier, min, max)

        Args:
            transition_id: Unique transition identifier
            base_cost: Base pathfinding cost before reliability adjustment

        Returns:
            Adjusted cost for pathfinding
        """
        stats = self.get_stats(transition_id)

        # Store base cost for reference
        if stats.base_cost != base_cost:
            stats.base_cost = base_cost

        # No history yet - use base cost
        if stats.total_attempts == 0:
            return base_cost

        # Calculate multiplier based on failure rate
        # failure_rate=0.0 → multiplier=1.0 (no penalty)
        # failure_rate=1.0 → multiplier=cost_multiplier_on_failure (full penalty)
        multiplier = 1.0 + (
            stats.failure_rate * (self.cost_multiplier_on_failure - 1.0)
        )

        # Clamp to reasonable range
        multiplier = max(self.min_cost_multiplier, multiplier)
        multiplier = min(self.max_cost_multiplier, multiplier)

        return base_cost * multiplier

    def get_all_stats(self) -> Dict[str, TransitionStats]:
        """Get statistics for all tracked transitions.

        Returns:
            Dictionary mapping transition IDs to their stats
        """
        return self._stats.copy()

    def reset_stats(self, transition_id: Optional[str] = None) -> None:
        """Reset statistics for one or all transitions.

        Args:
            transition_id: Transition to reset, or None to reset all
        """
        if transition_id is None:
            self._stats.clear()
            logger.info("Reset all transition statistics")
        elif transition_id in self._stats:
            del self._stats[transition_id]
            logger.info("Reset statistics for transition %s", transition_id)

    def get_summary(self) -> Dict[str, any]:
        """Get summary statistics across all transitions.

        Returns:
            Dictionary with aggregate statistics
        """
        if not self._stats:
            return {
                "total_transitions": 0,
                "total_attempts": 0,
                "total_successes": 0,
                "total_failures": 0,
                "overall_success_rate": 0.0,
            }

        total_attempts = sum(s.total_attempts for s in self._stats.values())
        total_successes = sum(s.success_count for s in self._stats.values())
        total_failures = sum(s.failure_count for s in self._stats.values())

        return {
            "total_transitions": len(self._stats),
            "total_attempts": total_attempts,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "overall_success_rate": (
                total_successes / total_attempts if total_attempts > 0 else 0.0
            ),
            "transitions": {tid: stats.to_dict() for tid, stats in self._stats.items()},
        }

    def get_least_reliable(self, limit: int = 5) -> list[TransitionStats]:
        """Get the least reliable transitions.

        Args:
            limit: Maximum number of transitions to return

        Returns:
            List of TransitionStats sorted by success rate (ascending)
        """
        # Filter to transitions with at least some attempts
        transitions_with_data = [
            stats for stats in self._stats.values() if stats.total_attempts > 0
        ]

        # Sort by success rate (lowest first)
        sorted_transitions = sorted(transitions_with_data, key=lambda s: s.success_rate)

        return sorted_transitions[:limit]

    def get_most_reliable(self, limit: int = 5) -> list[TransitionStats]:
        """Get the most reliable transitions.

        Args:
            limit: Maximum number of transitions to return

        Returns:
            List of TransitionStats sorted by success rate (descending)
        """
        # Filter to transitions with at least some attempts
        transitions_with_data = [
            stats for stats in self._stats.values() if stats.total_attempts > 0
        ]

        # Sort by success rate (highest first)
        sorted_transitions = sorted(
            transitions_with_data, key=lambda s: s.success_rate, reverse=True
        )

        return sorted_transitions[:limit]
