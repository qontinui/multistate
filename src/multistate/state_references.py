"""State references and history tracking.

Provides symbolic references to states (PREVIOUS, CURRENT, EXPECTED) and
history tracking to resolve these references to actual State objects.

This enables workflows to reference states relative to the current position
in the state machine without hardcoding specific state IDs.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, Set

from multistate.core.state import State


class StateReference(Enum):
    """Symbolic state references.

    These provide relative references to states based on state history
    and transitions, enabling dynamic state lookups without hardcoding IDs.

    Attributes:
        PREVIOUS: States that were previously active but are now inactive.
                 Useful for "back" navigation and undo operations.
        CURRENT: The set of currently active states in the system.
        EXPECTED: States anticipated to become active after transitions.
                 Used for predictive UI and validation.
    """

    PREVIOUS = "PREVIOUS"
    CURRENT = "CURRENT"
    EXPECTED = "EXPECTED"

    def __str__(self) -> str:
        """String representation."""
        return self.value


@dataclass
class StateSnapshot:
    """Snapshot of active states at a point in time.

    Captures the complete state configuration for history tracking.

    Attributes:
        states: Set of active state IDs at this point
        timestamp: When this snapshot was taken
        transition_id: ID of transition that led to this state (if any)
        metadata: Additional context information
    """

    states: Set[str]
    timestamp: datetime = field(default_factory=datetime.now)
    transition_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        """String representation."""
        states_str = ", ".join(sorted(self.states))
        trans_str = f" (via {self.transition_id})" if self.transition_id else ""
        return f"StateSnapshot({states_str}){trans_str}"


class StateHistory:
    """Tracks state configuration changes over time.

    Maintains a rolling history of state snapshots, enabling resolution
    of symbolic references like PREVIOUS and supporting undo/replay.

    The history is bounded to prevent unbounded memory growth.

    Attributes:
        max_history: Maximum number of snapshots to retain
        snapshots: Deque of historical snapshots (oldest first)
        expected_states: Set of state IDs expected to activate next
    """

    def __init__(self, max_history: int = 100):
        """Initialize state history.

        Args:
            max_history: Maximum snapshots to retain (default: 100)
        """
        self.max_history = max_history
        self.snapshots: Deque[StateSnapshot] = deque(maxlen=max_history)
        self.expected_states: Set[str] = set()

    def record_snapshot(
        self,
        active_states: Set[str],
        transition_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a new state snapshot.

        Args:
            active_states: Currently active state IDs
            transition_id: Transition that led to this state
            metadata: Additional context
        """
        snapshot = StateSnapshot(
            states=active_states.copy(),
            transition_id=transition_id,
            metadata=metadata or {},
        )
        self.snapshots.append(snapshot)

    def get_current_snapshot(self) -> Optional[StateSnapshot]:
        """Get the most recent snapshot.

        Returns:
            Latest snapshot, or None if history is empty
        """
        return self.snapshots[-1] if self.snapshots else None

    def get_previous_snapshot(self, offset: int = 1) -> Optional[StateSnapshot]:
        """Get a snapshot from history.

        Args:
            offset: How many snapshots back (1 = immediately previous)

        Returns:
            Historical snapshot, or None if not enough history
        """
        if len(self.snapshots) <= offset:
            return None
        return self.snapshots[-(offset + 1)]

    def get_previous_states(self, offset: int = 1) -> Set[str]:
        """Get previously active state IDs.

        Args:
            offset: How many snapshots back (1 = immediately previous)

        Returns:
            Set of state IDs that were active, empty if no history
        """
        snapshot = self.get_previous_snapshot(offset)
        return snapshot.states.copy() if snapshot else set()

    def get_current_states(self) -> Set[str]:
        """Get currently active state IDs.

        Returns:
            Set of currently active state IDs, empty if no history
        """
        snapshot = self.get_current_snapshot()
        return snapshot.states.copy() if snapshot else set()

    def get_expected_states(self) -> Set[str]:
        """Get expected next state IDs.

        Returns:
            Set of state IDs expected to activate next
        """
        return self.expected_states.copy()

    def set_expected_states(self, state_ids: Set[str]) -> None:
        """Set the expected next states.

        This is typically called before executing a transition to
        capture what states are anticipated to become active.

        Args:
            state_ids: State IDs expected to activate
        """
        self.expected_states = state_ids.copy()

    def clear_expected_states(self) -> None:
        """Clear expected states."""
        self.expected_states.clear()

    def get_state_changes(self) -> tuple[Set[str], Set[str]]:
        """Get states added/removed since previous snapshot.

        Returns:
            Tuple of (added_states, removed_states)
        """
        current = self.get_current_states()
        previous = self.get_previous_states()

        added = current - previous
        removed = previous - current

        return added, removed

    def get_history_length(self) -> int:
        """Get number of snapshots in history.

        Returns:
            Count of historical snapshots
        """
        return len(self.snapshots)

    def clear_history(self) -> None:
        """Clear all history.

        Removes all snapshots and expected states.
        """
        self.snapshots.clear()
        self.expected_states.clear()

    def get_snapshots_since(self, timestamp: datetime) -> List[StateSnapshot]:
        """Get all snapshots since a given time.

        Args:
            timestamp: Starting point for snapshot retrieval

        Returns:
            List of snapshots after the given timestamp
        """
        return [s for s in self.snapshots if s.timestamp >= timestamp]

    def get_transitions_to_state(self, state_id: str) -> List[str]:
        """Get all transitions that led to a state being activated.

        Args:
            state_id: State to find transitions for

        Returns:
            List of transition IDs that activated this state
        """
        transitions = []
        for i, snapshot in enumerate(self.snapshots):
            if state_id in snapshot.states and snapshot.transition_id:
                # Check if this transition added the state
                if i > 0:
                    prev = self.snapshots[i - 1]
                    if state_id not in prev.states:
                        transitions.append(snapshot.transition_id)
                else:
                    transitions.append(snapshot.transition_id)
        return transitions

    def __repr__(self) -> str:
        """String representation."""
        return f"StateHistory(snapshots={len(self.snapshots)}, max={self.max_history})"


class StateReferenceResolver:
    """Resolves symbolic state references to actual State objects.

    Bridges StateHistory with the actual State objects from StateManager,
    enabling lookups like "give me all PREVIOUS states as State objects".

    Attributes:
        history: State history tracker
        state_lookup: Function to get State by ID
    """

    def __init__(
        self, history: StateHistory, state_lookup: Callable[[str], Optional[State]]
    ):
        """Initialize resolver.

        Args:
            history: State history tracker
            state_lookup: Function that returns State by ID
        """
        self.history = history
        self.state_lookup = state_lookup

    def resolve_reference(self, reference: StateReference) -> Set[State]:
        """Resolve a symbolic reference to State objects.

        Args:
            reference: Symbolic reference to resolve

        Returns:
            Set of State objects matching the reference
        """
        if reference == StateReference.CURRENT:
            state_ids = self.history.get_current_states()
        elif reference == StateReference.PREVIOUS:
            state_ids = self.history.get_previous_states()
        elif reference == StateReference.EXPECTED:
            state_ids = self.history.get_expected_states()
        else:
            raise ValueError(f"Unknown state reference: {reference}")

        # Convert IDs to State objects
        states = set()
        for state_id in state_ids:
            state = self.state_lookup(state_id)
            if state is not None:
                states.add(state)

        return states

    def get_previous_state_objects(self, offset: int = 1) -> Set[State]:
        """Get previous states as State objects.

        Args:
            offset: How many snapshots back

        Returns:
            Set of State objects that were previously active
        """
        state_ids = self.history.get_previous_states(offset)
        states = set()
        for state_id in state_ids:
            state = self.state_lookup(state_id)
            if state is not None:
                states.add(state)
        return states

    def get_current_state_objects(self) -> Set[State]:
        """Get current states as State objects.

        Returns:
            Set of currently active State objects
        """
        return self.resolve_reference(StateReference.CURRENT)

    def get_expected_state_objects(self) -> Set[State]:
        """Get expected states as State objects.

        Returns:
            Set of State objects expected to activate next
        """
        return self.resolve_reference(StateReference.EXPECTED)

    def resolve_by_name(self, reference: StateReference) -> List[str]:
        """Resolve reference to state names.

        Args:
            reference: Symbolic reference

        Returns:
            List of state names matching the reference
        """
        states = self.resolve_reference(reference)
        return sorted([s.name for s in states])

    def __repr__(self) -> str:
        """String representation."""
        return f"StateReferenceResolver(history={self.history})"
