"""Tests for navigation-specific HTN methods."""

from __future__ import annotations

from multistate.planning.methods.navigation import (
    navigate_via_back_button, navigate_via_breadcrumb,
    navigate_via_keyboard_shortcut, navigate_via_search)
from multistate.planning.planner import WorldState


def test_navigate_via_breadcrumb() -> None:
    """Breadcrumb navigation produces click + wait when breadcrumb bar visible."""
    state = WorldState(element_visible={"breadcrumb_bar": True})
    result = navigate_via_breadcrumb(state, "settings")
    assert result is not None
    assert len(result) == 2
    assert result[0] == ("click_element", "breadcrumb_settings")
    assert result[1] == ("wait_for_state", "settings")


def test_navigate_via_breadcrumb_not_visible() -> None:
    """Breadcrumb navigation returns None when breadcrumb bar not visible."""
    state = WorldState(element_visible={})
    result = navigate_via_breadcrumb(state, "settings")
    assert result is None


def test_navigate_via_back_button() -> None:
    """Back button navigation produces click + wait when button visible."""
    state = WorldState(element_visible={"btn_back": True})
    result = navigate_via_back_button(state, "home")
    assert result is not None
    assert len(result) == 2
    assert result[0] == ("click_element", "btn_back")
    assert result[1] == ("wait_for_state", "home")


def test_navigate_via_back_button_not_visible() -> None:
    """Back button navigation returns None when button not visible."""
    state = WorldState()
    result = navigate_via_back_button(state, "home")
    assert result is None


def test_navigate_via_keyboard_shortcut() -> None:
    """Keyboard shortcut navigation works when shortcut in blackboard."""
    state = WorldState(blackboard={"shortcut_settings": "Ctrl+,"})
    result = navigate_via_keyboard_shortcut(state, "settings")
    assert result is not None
    assert len(result) == 2
    assert result[0] == ("type_text", "_keyboard", "Ctrl+,")
    assert result[1] == ("wait_for_state", "settings")


def test_navigate_via_keyboard_shortcut_missing() -> None:
    """Keyboard shortcut returns None when no shortcut in blackboard."""
    state = WorldState()
    result = navigate_via_keyboard_shortcut(state, "settings")
    assert result is None


def test_navigate_via_search() -> None:
    """Search navigation: click + type + click + wait when search bar visible."""
    state = WorldState(element_visible={"search_bar": True})
    result = navigate_via_search(state, "dashboard")
    assert result is not None
    assert len(result) == 4
    assert result[0] == ("click_element", "search_bar")
    assert result[1] == ("type_text", "search_bar", "dashboard")
    assert result[2] == ("click_element", "search_result_dashboard")
    assert result[3] == ("wait_for_state", "dashboard")


def test_navigate_via_search_not_visible() -> None:
    """Search navigation returns None when search bar not visible."""
    state = WorldState()
    result = navigate_via_search(state, "dashboard")
    assert result is None
