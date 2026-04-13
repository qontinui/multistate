"""Dialog-handling HTN methods.

Provides decompositions for dismissing, confirming, and cancelling dialogs
and modals using different interaction strategies.
"""

from __future__ import annotations

from typing import Callable

from multistate.planning.planner import WorldState

# Type alias for methods
Method = Callable[..., list[tuple[str, ...]] | None]


def dismiss_via_escape(state: WorldState) -> list[tuple[str, ...]] | None:
    """Dismiss dialog by pressing Escape key."""
    dialog_states = [
        s
        for s in state.active_states
        if s.startswith("dialog_") or s.startswith("modal_")
    ]
    if not dialog_states:
        return None
    actions: list[tuple[str, ...]] = [("type_text", "_keyboard", "\x1b")]  # Escape key
    for ds in dialog_states:
        actions.append(
            ("wait_for_state", ds.replace("dialog_", "").replace("modal_", ""))
        )
    return actions


def dismiss_via_close_button(state: WorldState) -> list[tuple[str, ...]] | None:
    """Dismiss dialog by clicking its close button."""
    dialog_states = [
        s
        for s in state.active_states
        if s.startswith("dialog_") or s.startswith("modal_")
    ]
    if not dialog_states:
        return None
    actions: list[tuple[str, ...]] = []
    for ds in dialog_states:
        close_btn = f"{ds}_close"
        if state.element_visible.get(close_btn, False):
            actions.append(("click_element", close_btn))
            actions.append(("dismiss_dialog", ds))
    return actions if actions else None


def confirm_dialog(
    state: WorldState, dialog_state: str, confirm_button: str
) -> list[tuple[str, ...]] | None:
    """Confirm a dialog (click OK/Yes/Confirm)."""
    if dialog_state not in state.active_states:
        return None
    return [
        ("click_element", confirm_button),
        ("dismiss_dialog", dialog_state),
    ]


def cancel_dialog(
    state: WorldState, dialog_state: str
) -> list[tuple[str, ...]] | None:
    """Cancel a dialog."""
    if dialog_state not in state.active_states:
        return None
    cancel_btn = f"{dialog_state}_cancel"
    return [
        ("click_element", cancel_btn),
        ("dismiss_dialog", dialog_state),
    ]


DIALOG_METHODS: dict[str, list[Method]] = {
    "handle_dialog": [dismiss_via_escape, dismiss_via_close_button],
    "confirm_dialog": [confirm_dialog],
    "cancel_dialog": [cancel_dialog],
}
