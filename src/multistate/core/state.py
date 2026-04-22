"""State: A collection of GUI elements.

Following the paper's formal model where:
- S is the set of all GUI states
- Each state s ∈ S is a subset of E (collection of elements)
- Multiple states can be active simultaneously: S_Ξ ⊆ S
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

from multistate.core.element import Element


@dataclass
class StateTimeout:
    """Timeout configuration for a state.

    When a state has been active longer than `duration_seconds`, it is
    considered timed out.  The caller's automation loop should call
    `StateManager.check_timeouts()` periodically to detect and optionally
    auto-execute the named timeout transition.

    Attributes:
        duration_seconds: How long (in seconds) before the state times out.
        on_timeout: Name/ID of the transition to trigger on timeout.
        auto_transition: If True, `check_timeouts()` will automatically
            execute the timeout transition.
    """

    duration_seconds: float
    on_timeout: str
    auto_transition: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration_seconds": self.duration_seconds,
            "on_timeout": self.on_timeout,
            "auto_transition": self.auto_transition,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateTimeout":
        return cls(
            duration_seconds=data["duration_seconds"],
            on_timeout=data["on_timeout"],
            auto_transition=data.get("auto_transition", True),
        )


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
    timeout: Optional[StateTimeout] = None
    htn_config: Optional[Any] = field(default=None, repr=False)
    """Optional :class:`~multistate.planning.htn_state.HTNStateConfig`.

    Typed as ``Any`` to avoid a circular import from the planning sub-package
    back into core.  At runtime the value should be an ``HTNStateConfig``
    instance (or ``None``).
    """
    _activated_at: Optional[float] = field(default=None, repr=False)

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

    def on_activate(self) -> None:
        """Record activation time for timeout tracking."""
        if self.timeout:
            self._activated_at = time.monotonic()

    def on_deactivate(self) -> None:
        """Clear activation time when state is deactivated."""
        self._activated_at = None

    def check_timeout(self) -> bool:
        """Check whether this state has exceeded its timeout duration.

        Returns:
            True if the state has timed out, False otherwise.
        """
        if self.timeout and self._activated_at is not None:
            elapsed = time.monotonic() - self._activated_at
            return elapsed >= self.timeout.duration_seconds
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary representation.

        Returns:
            Dictionary containing state properties
        """
        d: Dict[str, Any] = {
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
        if self.timeout:
            d["timeout"] = self.timeout.to_dict()
        if self.htn_config is not None:
            from dataclasses import asdict, is_dataclass

            if is_dataclass(self.htn_config) and not isinstance(self.htn_config, type):
                d["htn_config"] = asdict(self.htn_config)
            elif hasattr(self.htn_config, "to_dict"):
                d["htn_config"] = self.htn_config.to_dict()
            else:
                d["htn_config"] = self.htn_config  # assume it's already a dict
        return d

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        element_lookup: Optional[Dict[str, Element]] = None,
    ) -> "State":
        """Reconstruct a State from its serialized representation.

        Callbacks cannot be serialized and must be re-registered after
        deserialization.

        Args:
            data: Dictionary produced by ``to_dict()``.
            element_lookup: Optional mapping of element ID -> Element.
                If provided, elements are resolved from this dict;
                otherwise lightweight Element stubs are created.

        Returns:
            Reconstructed State object.
        """
        elements: Set[Element] = set()
        for eid in data.get("elements", []):
            if element_lookup and eid in element_lookup:
                elements.add(element_lookup[eid])
            else:
                elements.add(Element(id=eid, name=eid))

        timeout = None
        if "timeout" in data:
            timeout = StateTimeout.from_dict(data["timeout"])

        # htn_config stays as a dict; caller can convert to HTNStateConfig if needed
        htn_config = data.get("htn_config")

        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            elements=elements,
            group=data.get("group"),
            mock_starting_probability=data.get("mock_starting_probability", 1.0),
            path_cost=data.get("path_cost", 1.0),
            blocking=data.get("blocking", False),
            blocks=set(data.get("blocks", [])),
            metadata=dict(data.get("metadata", {})),
            timeout=timeout,
            htn_config=htn_config,
        )
