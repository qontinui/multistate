"""Bridge between StateManager and the HTN planner's WorldState."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from multistate.planning.planner import WorldState

if TYPE_CHECKING:
    from multistate.manager import StateManager


class WorldStateAdapter:
    """Converts live :class:`StateManager` state into a :class:`WorldState`.

    Args:
        manager: The StateManager instance to read from.
    """

    def __init__(self, manager: StateManager) -> None:
        self.manager = manager

    def snapshot(
        self,
        ui_elements: Optional[dict[str, bool]] = None,
        ui_values: Optional[dict[str, str]] = None,
    ) -> WorldState:
        """Create a :class:`WorldState` from the current manager state.

        Args:
            ui_elements: Optional element-visibility overrides.
            ui_values: Optional element-value overrides.

        Returns:
            A fresh WorldState reflecting the manager plus any UI data.
        """
        active = self.manager.get_active_states()
        available = set(self.manager.get_available_transitions())

        return WorldState(
            active_states=active,
            available_transitions=available,
            element_visible=dict(ui_elements) if ui_elements else {},
            element_values=dict(ui_values) if ui_values else {},
            blackboard={},
        )

    def apply_transition(self, state: WorldState, transition_id: str) -> WorldState | None:
        """Simulate a transition on a WorldState without executing it.

        Checks the transition exists and is currently available, then
        applies its ``exit_states`` / ``activate_states`` and recomputes
        which transitions are available in the resulting state.

        Args:
            state: The world state to apply the transition on.
            transition_id: The transition to simulate.

        Returns:
            A new WorldState after the transition, or ``None`` if the
            transition is invalid or unavailable.
        """
        if transition_id not in state.available_transitions:
            return None

        if transition_id not in self.manager.transitions:
            return None

        transition = self.manager.transitions[transition_id]

        # Compute new active states
        new_active = set(state.active_states)
        for s in transition.exit_states:
            new_active.discard(s.id)
        for s in transition.activate_states:
            new_active.add(s.id)

        # Recompute available transitions based on new active states
        new_available: set[str] = set()
        for tid, t in self.manager.transitions.items():
            # A transition is available if all its from_states are active
            from_ids = {s.id for s in t.from_states}
            if from_ids.issubset(new_active):
                new_available.add(tid)

        new_state = state.copy()
        new_state.active_states = new_active
        new_state.available_transitions = new_available
        new_state.blackboard["_last_transition"] = transition_id
        return new_state
