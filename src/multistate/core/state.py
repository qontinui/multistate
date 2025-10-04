"""State: A collection of GUI elements.

Following the paper's formal model where:
- S is the set of all GUI states
- Each state s ∈ S is a subset of E (collection of elements)
- Multiple states can be active simultaneously: S_Ξ ⊆ S
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

from multistate.core.element import Element


@dataclass
class State:
    """Represents a GUI state as a collection of elements.

    In the formal model: s ∈ S where s ⊆ E

    States represent meaningful collections of GUI elements that often:
    - Appear together spatially
    - Activate/deactivate together
    - Are used together in processes

    Attributes:
        id: Unique identifier for the state
        name: Human-readable name
        elements: Set of elements that define this state (s ⊆ E)
        group: Optional group membership (for G ⊆ P(S))
        mock_starting_probability: Weight for initial state selection in mock mode (w_s)
        path_cost: Cost for pathfinding algorithms (c_S(s))
        blocking: If True, prevents other state activations when active
        blocks: Set of state IDs that this state blocks when active
        metadata: Additional state-specific properties
    """

    id: str
    name: str
    elements: Set[Element] = field(default_factory=set)
    group: Optional[str] = None
    mock_starting_probability: float = 1.0
    path_cost: float = 1.0
    blocking: bool = False
    blocks: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        """Make state hashable for use in sets."""
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        """States are equal if they have the same id."""
        if not isinstance(other, State):
            return False
        return self.id == other.id

    def __repr__(self) -> str:
        """String representation for debugging."""
        elem_count = len(self.elements)
        group_str = f", group='{self.group}'" if self.group else ""
        return f"State(id='{self.id}', name='{self.name}', elements={elem_count}{group_str})"

    def add_element(self, element: Element) -> None:
        """Add an element to this state.

        Args:
            element: Element to add to the state's collection
        """
        self.elements.add(element)

    def remove_element(self, element: Element) -> None:
        """Remove an element from this state.

        Args:
            element: Element to remove from the state's collection
        """
        self.elements.discard(element)

    def has_element(self, element: Element) -> bool:
        """Check if this state contains the given element.

        Args:
            element: Element to check for

        Returns:
            True if the element is in this state's collection
        """
        return element in self.elements

    def is_blocking(self) -> bool:
        """Check if this is a blocking state.

        Returns:
            True if this state blocks other activations when active
        """
        return self.blocking

    def get_blocked_states(self) -> Set[str]:
        """Get the set of state IDs blocked by this state.

        Returns:
            Set of state IDs that cannot activate when this state is active
        """
        return self.blocks.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary representation.

        Returns:
            Dictionary containing state properties
        """
        return {
            "id": self.id,
            "name": self.name,
            "elements": [e.id for e in self.elements],
            "group": self.group,
            "mock_starting_probability": self.mock_starting_probability,
            "path_cost": self.path_cost,
            "blocking": self.blocking,
            "blocks": list(self.blocks),
            "metadata": self.metadata,
        }