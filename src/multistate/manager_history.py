"""State History Management - Handles historical state tracking for StateManager.

This module provides historical state tracking functionality separated from
the main StateManager to improve modularity.
"""

import logging
from typing import Any, Callable, Optional, Set

from multistate.core.state import State
from multistate.state_references import (
    StateHistory,
    StateReference,
    StateReferenceResolver,
    StateSnapshot,
)

logger = logging.getLogger(__name__)


class StateHistoryManager:
    """Manages state history tracking and resolution for StateManager.

    This class handles:
    - Recording state snapshots over time
    - Resolving state references (previous, current, expected)
    - State change detection
    - History size management

    Thread Safety:
        StateHistory and StateReferenceResolver are thread-safe.
    """

    def __init__(
        self,
        max_history_size: int = 100,
        state_lookup_fn: Optional[Callable[[str], Optional[State]]] = None,
    ) -> None:
        """Initialize StateHistoryManager.

        Args:
            max_history_size: Maximum number of historical snapshots to keep
            state_lookup_fn: Function to lookup state by ID
        """
        self.state_history = StateHistory(max_history=max_history_size)
        self.state_resolver: Optional[StateReferenceResolver] = None

        if state_lookup_fn:
            self.state_resolver = StateReferenceResolver(
                self.state_history, state_lookup_fn
            )

        logger.debug(f"StateHistoryManager initialized (max_size={max_history_size})")

    def record_snapshot(
        self,
        active_state_ids: Set[str],
        transition_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record a state snapshot.

        Args:
            active_state_ids: Set of currently active state IDs
            transition_id: ID of transition that led to this state
            metadata: Additional context information
        """
        self.state_history.record_snapshot(active_state_ids, transition_id, metadata)

    def resolve_reference(self, reference: StateReference) -> Set[State]:
        """Resolve a state reference to actual states.

        Args:
            reference: State reference to resolve

        Returns:
            Set of State objects matching the reference

        Raises:
            ValueError: If state resolver is not configured
        """
        if not self.state_resolver:
            raise ValueError("State resolver not configured")

        return self.state_resolver.resolve_reference(reference)

    def get_previous_states(self, offset: int = 1) -> Set[State]:
        """Get states from a previous snapshot.

        Args:
            offset: How many snapshots to look back (1 = previous)

        Returns:
            Set of State objects from that snapshot
        """
        if not self.state_resolver:
            return set()

        return self.state_resolver.get_previous_state_objects(offset)















    def get_current_states(self) -> Set[State]:
        """Get current states from history.

        Returns:
            Set of current State objects
        """
        if not self.state_resolver:
            return set()

        reference = StateReference.CURRENT
        return self.state_resolver.resolve_reference(reference)

    def get_expected_states(self) -> Set[State]:
        """Get expected states from history.

        Returns:
            Set of expected State objects
        """
        if not self.state_resolver:
            return set()

        reference = StateReference.EXPECTED
        return self.state_resolver.resolve_reference(reference)

    def get_state_changes(self) -> tuple[Set[State], Set[State]]:
        """Get states that were added/removed in last transition.

        Returns:
            Tuple of (added_states, removed_states)
        """
        if len(self.state_history.snapshots) < 2:
            return set(), set()

        # Get last two snapshots
        current = self.state_history.snapshots[-1]
        previous = self.state_history.snapshots[-2]

        # Calculate differences
        added_ids = current.states - previous.states
        removed_ids = previous.states - current.states

        # Resolve to state objects
        if self.state_resolver:
            added = set()
            for state_id in added_ids:
                state = self.state_resolver.state_lookup(state_id)
                if state is not None:
                    added.add(state)
            
            removed = set()
            for state_id in removed_ids:
                state = self.state_resolver.state_lookup(state_id)
                if state is not None:
                    removed.add(state)
            
            return added, removed

        return set(), set()

    def get_history_length(self) -> int:
        """Get number of snapshots in history.

        Returns:
            Number of recorded snapshots
        """
        return len(self.state_history.snapshots)

    def clear_history(self) -> None:
        """Clear all historical snapshots."""
        self.state_history.snapshots.clear()
        logger.debug("State history cleared")

    def get_latest_snapshot(self) -> Optional[StateSnapshot]:
        """Get the most recent snapshot.

        Returns:
            Latest StateSnapshot or None if history is empty
        """
        if not self.state_history.snapshots:
            return None
        return self.state_history.snapshots[-1]
