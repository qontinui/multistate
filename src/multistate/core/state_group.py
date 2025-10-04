"""StateGroup: Collection of states that activate/deactivate together.

Following the paper's formal model where:
- G ⊆ P(S) is the set of state groups
- γ: G → P(S) is the group membership function
- Group atomicity ensures all states in a group activate together
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from multistate.core.state import State


@dataclass
class StateGroup:
    """Represents a group of states that must activate/deactivate atomically.

    In the formal model: g ∈ G where g = {s₁, s₂, ..., sₖ}

    Key property (Group Atomicity):
    ∀g ∈ G, ∀t ∈ T: activate(g, t) ⟹ ∀s ∈ g: s ∈ S_Ξ'

    This ensures all states in a group activate together or none do.

    Attributes:
        id: Unique identifier for the group
        name: Human-readable name
        states: Set of states in this group
        metadata: Additional group-specific properties
    """

    id: str
    name: str
    states: Set[State] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Post-initialization to update state group memberships."""
        # Update each state's group membership
        for state in self.states:
            if state.group and state.group != self.id:
                raise ValueError(
                    f"State '{state.name}' already belongs to group '{state.group}'"
                )
            state.group = self.id

    def __hash__(self) -> int:
        """Make group hashable for use in sets."""
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        """Groups are equal if they have the same id."""
        if not isinstance(other, StateGroup):
            return False
        return self.id == other.id

    def __repr__(self) -> str:
        """String representation for debugging."""
        state_names = [s.name for s in self.states]
        return f"StateGroup(id='{self.id}', name='{self.name}', states={state_names})"

    def __len__(self) -> int:
        """Return the number of states in the group."""
        return len(self.states)

    def __iter__(self):
        """Iterate over states in the group."""
        return iter(self.states)

    def add_state(self, state: State) -> None:
        """Add a state to this group.

        Args:
            state: State to add to the group

        Raises:
            ValueError: If state already belongs to another group
        """
        if state.group and state.group != self.id:
            raise ValueError(
                f"State '{state.name}' already belongs to group '{state.group}'"
            )
        state.group = self.id
        self.states.add(state)

    def remove_state(self, state: State) -> None:
        """Remove a state from this group.

        Args:
            state: State to remove from the group
        """
        if state in self.states:
            state.group = None
            self.states.discard(state)

    def has_state(self, state: State) -> bool:
        """Check if this group contains the given state.

        Args:
            state: State to check for

        Returns:
            True if the state is in this group
        """
        return state in self.states

    def get_state_ids(self) -> Set[str]:
        """Get the IDs of all states in this group.

        Returns:
            Set of state IDs
        """
        return {s.id for s in self.states}

    def is_fully_active(self, active_states: Set[State]) -> bool:
        """Check if all states in the group are active.

        This verifies the group atomicity property:
        g ⊆ S_Ξ (all group states are in active states)

        Args:
            active_states: Current set of active states

        Returns:
            True if all states in group are active
        """
        return self.states.issubset(active_states)

    def is_fully_inactive(self, active_states: Set[State]) -> bool:
        """Check if no states in the group are active.

        This verifies: g ∩ S_Ξ = ∅ (no group states are active)

        Args:
            active_states: Current set of active states

        Returns:
            True if no states in group are active
        """
        return self.states.isdisjoint(active_states)

    def validate_atomicity(self, active_states: Set[State]) -> bool:
        """Validate the group atomicity property.

        Ensures: g ⊆ S_Ξ ∨ g ∩ S_Ξ = ∅
        (group is either fully active or fully inactive)

        Args:
            active_states: Current set of active states

        Returns:
            True if atomicity property holds
        """
        return self.is_fully_active(active_states) or self.is_fully_inactive(
            active_states
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert group to dictionary representation.

        Returns:
            Dictionary containing group properties
        """
        return {
            "id": self.id,
            "name": self.name,
            "states": [s.id for s in self.states],
            "metadata": self.metadata,
        }