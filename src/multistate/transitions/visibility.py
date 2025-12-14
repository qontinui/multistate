"""Visibility control for state transitions.

Migrated from qontinui's StaysVisible enum.
Controls whether source states remain visible after a transition.
"""

from enum import Enum


class StaysVisible(Enum):
    """Visibility behavior after transition.

    Controls whether source states remain visible in the UI after
    a transition executes.

    Values:
        NONE: Inherit visibility behavior from parent container or use default
        TRUE: Source state remains visible after transition
        FALSE: Source state becomes hidden after transition

    Example:
        >>> transition = Transition(
        ...     id="open_modal",
        ...     from_states={main_screen},
        ...     activate_states={modal},
        ...     stays_visible=StaysVisible.TRUE  # main_screen stays visible
        ... )
    """

    NONE = "NONE"
    TRUE = "TRUE"
    FALSE = "FALSE"

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Debug representation."""
        return f"StaysVisible.{self.name}"
