"""Element: Basic building block of states.

Following the paper's notation where E = {e₁, e₂, ..., eₙ} is the set of
all GUI elements, and each state s ∈ S is a subset of E.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Element:
    """Represents a GUI element in the state structure.

    In the formal model: e ∈ E
    Elements are the atomic units that compose states.

    Attributes:
        id: Unique identifier for the element
        name: Human-readable name
        type: Type of element (e.g., 'button', 'image', 'region')
        metadata: Additional properties specific to element type
    """

    id: str
    name: str
    type: str = "generic"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        """Make element hashable for use in sets."""
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        """Elements are equal if they have the same id."""
        if not isinstance(other, Element):
            return False
        return self.id == other.id

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Element(id='{self.id}', name='{self.name}', type='{self.type}')"

    def to_dict(self) -> Dict[str, Any]:
        """Convert element to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Element":
        """Reconstruct an Element from its serialized representation."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            type=data.get("type", "generic"),
            metadata=dict(data.get("metadata", {})),
        )
