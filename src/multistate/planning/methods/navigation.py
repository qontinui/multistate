"""Navigation-specific HTN methods.

Provides specialized navigation decompositions beyond the generic pathfinding
and menu-based methods: breadcrumb trails, back-button, keyboard shortcuts,
and search/command-palette navigation.
"""

from __future__ import annotations

from typing import Callable

from multistate.planning.planner import WorldState

# Type alias for methods
Method = Callable[..., list[tuple[str, ...]] | None]


def navigate_via_breadcrumb(state: WorldState, target_state: str) -> list[tuple[str, ...]] | None:
    """Navigate via breadcrumb trail (if breadcrumb bar is visible)."""
    if not state.element_visible.get("breadcrumb_bar", False):
        return None
    return [
        ("click_element", f"breadcrumb_{target_state}"),
        ("wait_for_state", target_state),
    ]


def navigate_via_back_button(state: WorldState, target_state: str) -> list[tuple[str, ...]] | None:
    """Navigate back (if back button is visible and target is in history)."""
    if not state.element_visible.get("btn_back", False):
        return None
    return [
        ("click_element", "btn_back"),
        ("wait_for_state", target_state),
    ]


def navigate_via_keyboard_shortcut(
    state: WorldState, target_state: str
) -> list[tuple[str, ...]] | None:
    """Navigate via keyboard shortcut (if shortcut mapping exists in blackboard)."""
    shortcut = state.blackboard.get(f"shortcut_{target_state}")
    if shortcut is None:
        return None
    return [
        ("type_text", "_keyboard", shortcut),
        ("wait_for_state", target_state),
    ]


def navigate_via_search(state: WorldState, target_state: str) -> list[tuple[str, ...]] | None:
    """Navigate via search/command palette."""
    if not state.element_visible.get("search_bar", False):
        return None
    return [
        ("click_element", "search_bar"),
        ("type_text", "search_bar", target_state),
        ("click_element", f"search_result_{target_state}"),
        ("wait_for_state", target_state),
    ]


NAVIGATION_METHODS: dict[str, list[Method]] = {
    "navigate_to": [
        navigate_via_breadcrumb,
        navigate_via_back_button,
        navigate_via_keyboard_shortcut,
        navigate_via_search,
    ],
}
