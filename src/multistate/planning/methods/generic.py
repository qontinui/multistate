from __future__ import annotations

from typing import Callable

from multistate.planning.planner import WorldState

# Type alias for methods
Method = Callable[..., list[tuple[str, ...]] | None]


def navigate_to_via_pathfinding(
    state: WorldState, target_state: str
) -> list[tuple[str, ...]] | None:
    """Navigate to target using multistate pathfinding.

    During planning this is optimistic (assumes success). The actual
    pathfinding is performed by the executor's action handler at runtime.
    """
    if target_state in state.active_states:
        return []
    return [("navigate_path", target_state)]


def navigate_to_via_menu(state: WorldState, target_state: str) -> list[tuple[str, ...]] | None:
    """Navigate via menu. Only applicable if main_menu is active."""
    if "main_menu" not in state.active_states:
        return None
    return [
        ("click_element", f"menu_{target_state}"),
        ("wait_for_state", target_state),
    ]


def fill_form_sequential(state: WorldState, fields: dict[str, str]) -> list[tuple[str, ...]] | None:
    """Fill form fields sequentially. fields maps element_id to value."""
    actions: list[tuple[str, ...]] = []
    for element_id, value in fields.items():
        actions.append(("click_element", element_id))
        actions.append(("type_text", element_id, value))
    return actions


def handle_unexpected_dialog(
    state: WorldState,
) -> list[tuple[str, ...]] | None:
    """Dismiss any active dialog/modal states."""
    dialog_states = [
        s for s in state.active_states if s.startswith("dialog_") or s.startswith("modal_")
    ]
    if not dialog_states:
        return None
    return [("dismiss_dialog", s) for s in dialog_states]


def login_generic(state: WorldState, username: str, password: str) -> list[tuple[str, ...]] | None:
    """Generic login: navigate to login screen, fill credentials, submit."""
    tasks: list[tuple[str, ...]] = []
    if "login_screen" not in state.active_states:
        tasks.append(("navigate_to", "login_screen"))
    tasks.extend(
        [
            ("fill_form", {"username_field": username, "password_field": password}),  # type: ignore[list-item]
            ("click_element", "btn_login"),
            ("wait_for_state", "dashboard"),
        ]
    )
    return tasks


def scroll_to_element(state: WorldState, element_id: str) -> list[tuple[str, ...]] | None:
    """Scroll to make an element visible."""
    if state.element_visible.get(element_id, False):
        return []
    return [("wait_for_element", element_id)]


def submit_form(state: WorldState, submit_button_id: str) -> list[tuple[str, ...]] | None:
    """Click submit button and wait for result."""
    return [("click_element", submit_button_id)]


GENERIC_METHODS: dict[str, list[Method]] = {
    "navigate_to": [navigate_to_via_pathfinding, navigate_to_via_menu],
    "fill_form": [fill_form_sequential],
    "handle_dialog": [handle_unexpected_dialog],
    "login": [login_generic],
    "scroll_to": [scroll_to_element],
    "submit_form": [submit_form],
}
