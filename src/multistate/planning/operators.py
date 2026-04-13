"""Standard operator library for the HTN planner.

Each operator takes a :class:`WorldState` plus arguments and returns a new
WorldState on success or ``None`` when its preconditions are not met.
"""

from __future__ import annotations

from multistate.planning.planner import Operator, WorldState


def navigate_transition(state: WorldState, transition_id: str) -> WorldState | None:
    """Fire *transition_id* if it is currently available.

    Sets ``blackboard["_last_transition"]`` to *transition_id*.
    """
    if transition_id not in state.available_transitions:
        return None
    new = state.copy()
    new.blackboard["_last_transition"] = transition_id
    return new


def click_element(state: WorldState, element_id: str) -> WorldState | None:
    """Click *element_id* if it is visible.

    Sets ``blackboard["_last_clicked"]`` to *element_id*.
    """
    if not state.element_visible.get(element_id, False):
        return None
    new = state.copy()
    new.blackboard["_last_clicked"] = element_id
    return new


def type_text(state: WorldState, element_id: str, text: str) -> WorldState | None:
    """Type *text* into *element_id* if visible.

    Updates ``element_values[element_id]`` to *text*.
    """
    if not state.element_visible.get(element_id, False):
        return None
    new = state.copy()
    new.element_values[element_id] = text
    return new


def wait_for_state(state: WorldState, target_state: str) -> WorldState | None:
    """Optimistically assume *target_state* will become active.

    Returns a copy with *target_state* added to ``active_states``.
    """
    new = state.copy()
    new.active_states.add(target_state)
    return new


def wait_for_element(state: WorldState, element_id: str) -> WorldState | None:
    """Optimistically assume *element_id* will become visible.

    Returns a copy with ``element_visible[element_id]`` set to ``True``.
    """
    new = state.copy()
    new.element_visible[element_id] = True
    return new


def dismiss_dialog(state: WorldState, dialog_state: str) -> WorldState | None:
    """Dismiss a dialog represented by *dialog_state*.

    Requires *dialog_state* to be in ``active_states``; removes it.
    """
    if dialog_state not in state.active_states:
        return None
    new = state.copy()
    new.active_states.discard(dialog_state)
    return new


def navigate_path(state: WorldState, target_state: str) -> WorldState | None:
    """Navigate to target via multistate pathfinding (optimistic during planning).

    At execution time the handler uses StateManager.navigate_to(). During
    planning this operator optimistically assumes the target will be reached.
    """
    new = state.copy()
    new.active_states.add(target_state)
    new.blackboard["_last_navigation_target"] = target_state
    return new


STANDARD_OPERATORS: dict[str, Operator] = {
    "navigate_transition": navigate_transition,
    "navigate_path": navigate_path,
    "click_element": click_element,
    "type_text": type_text,
    "wait_for_state": wait_for_state,
    "wait_for_element": wait_for_element,
    "dismiss_dialog": dismiss_dialog,
}
