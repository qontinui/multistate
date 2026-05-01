"""Form-handling HTN methods.

Provides decompositions for filling forms, clearing fields, and selecting
dropdown options with different interaction strategies.
"""

from __future__ import annotations

from typing import Callable

from multistate.planning.planner import WorldState

# Type alias for methods
Method = Callable[..., list[tuple[str, ...]] | None]


def fill_form_tab_order(
    state: WorldState, fields: dict[str, str]
) -> list[tuple[str, ...]] | None:
    """Fill form using Tab to move between fields (more reliable than clicking)."""
    actions: list[tuple[str, ...]] = []
    first = True
    for element_id, value in fields.items():
        if first:
            actions.append(("click_element", element_id))
            first = False
        else:
            actions.append(("type_text", "_keyboard", "\t"))
        actions.append(("type_text", element_id, value))
    return actions


def fill_form_with_validation(
    state: WorldState, fields: dict[str, str]
) -> list[tuple[str, ...]] | None:
    """Fill form and click away after each field to trigger validation."""
    actions: list[tuple[str, ...]] = []
    for element_id, value in fields.items():
        actions.append(("click_element", element_id))
        actions.append(("type_text", element_id, value))
        # Click away to trigger validation
        actions.append(("click_element", "_body"))
    return actions


def clear_and_fill_field(
    state: WorldState, element_id: str, value: str
) -> list[tuple[str, ...]] | None:
    """Clear an existing field value before typing new value."""
    if not state.element_visible.get(element_id, False):
        return None
    return [
        ("click_element", element_id),
        ("type_text", "_keyboard", "\x01"),  # Ctrl+A select all
        ("type_text", element_id, value),  # Type overwrites selection
    ]


def select_dropdown(
    state: WorldState, dropdown_id: str, option_text: str
) -> list[tuple[str, ...]] | None:
    """Select an option from a dropdown/select element."""
    if not state.element_visible.get(dropdown_id, False):
        return None
    return [
        ("click_element", dropdown_id),
        ("wait_for_element", f"{dropdown_id}_options"),
        ("click_element", f"{dropdown_id}_option_{option_text}"),
    ]


FORM_METHODS: dict[str, list[Method]] = {
    "fill_form": [fill_form_tab_order, fill_form_with_validation],
    "clear_and_fill": [clear_and_fill_field],
    "select_dropdown": [select_dropdown],
}
