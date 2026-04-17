"""Tests for form-handling HTN methods."""

from __future__ import annotations

from multistate.planning.methods.forms import (
    clear_and_fill_field,
    fill_form_tab_order,
    fill_form_with_validation,
    select_dropdown,
)
from multistate.planning.planner import WorldState


def test_fill_form_tab_order() -> None:
    """Tab-order fill produces click on first field, then tab between fields."""
    state = WorldState()
    fields = {"name": "Alice", "email": "alice@example.com"}
    result = fill_form_tab_order(state, fields)
    assert result is not None
    # First field: click + type
    assert result[0] == ("click_element", "name")
    assert result[1] == ("type_text", "name", "Alice")
    # Second field: tab + type
    assert result[2] == ("type_text", "_keyboard", "\t")
    assert result[3] == ("type_text", "email", "alice@example.com")


def test_fill_form_tab_order_single_field() -> None:
    """Tab-order with single field produces click + type, no tab."""
    state = WorldState()
    result = fill_form_tab_order(state, {"username": "bob"})
    assert result is not None
    assert len(result) == 2
    assert result[0] == ("click_element", "username")
    assert result[1] == ("type_text", "username", "bob")


def test_fill_form_with_validation() -> None:
    """Validation fill produces click + type + click-away for each field."""
    state = WorldState()
    fields = {"field_a": "value_a"}
    result = fill_form_with_validation(state, fields)
    assert result is not None
    assert len(result) == 3
    assert result[0] == ("click_element", "field_a")
    assert result[1] == ("type_text", "field_a", "value_a")
    assert result[2] == ("click_element", "_body")


def test_clear_and_fill_field() -> None:
    """Clear-and-fill produces click + select-all + type when element visible."""
    state = WorldState(element_visible={"input_name": True})
    result = clear_and_fill_field(state, "input_name", "new_value")
    assert result is not None
    assert len(result) == 3
    assert result[0] == ("click_element", "input_name")
    assert result[1] == ("type_text", "_keyboard", "\x01")
    assert result[2] == ("type_text", "input_name", "new_value")


def test_clear_and_fill_field_not_visible() -> None:
    """Clear-and-fill returns None when element not visible."""
    state = WorldState()
    result = clear_and_fill_field(state, "input_name", "value")
    assert result is None


def test_select_dropdown() -> None:
    """Dropdown select produces click + wait-for-options + click-option."""
    state = WorldState(element_visible={"country_select": True})
    result = select_dropdown(state, "country_select", "Canada")
    assert result is not None
    assert len(result) == 3
    assert result[0] == ("click_element", "country_select")
    assert result[1] == ("wait_for_element", "country_select_options")
    assert result[2] == ("click_element", "country_select_option_Canada")


def test_select_dropdown_not_visible() -> None:
    """Dropdown select returns None when dropdown not visible."""
    state = WorldState()
    result = select_dropdown(state, "country_select", "Canada")
    assert result is None
