"""Tests for dialog-handling HTN methods."""

from __future__ import annotations

from multistate.planning.methods.dialogs import (
    cancel_dialog,
    confirm_dialog,
    dismiss_via_close_button,
    dismiss_via_escape,
)
from multistate.planning.planner import WorldState


def test_dismiss_via_escape() -> None:
    """Escape dismissal produces type-escape + dismiss_dialog when dialog present."""
    state = WorldState(active_states={"dialog_confirm", "main_page"})
    result = dismiss_via_escape(state)
    assert result is not None
    assert result[0] == ("type_text", "_keyboard", "\x1b")
    # Should have dismiss_dialog for the dialog
    dismiss_actions = [a for a in result if a[0] == "dismiss_dialog"]
    assert len(dismiss_actions) == 1
    assert dismiss_actions[0] == ("dismiss_dialog", "dialog_confirm")


def test_dismiss_via_escape_modal() -> None:
    """Escape dismissal handles modal_ prefix too."""
    state = WorldState(active_states={"modal_settings"})
    result = dismiss_via_escape(state)
    assert result is not None
    assert ("dismiss_dialog", "modal_settings") in result


def test_dismiss_via_close_button() -> None:
    """Close button dismissal clicks close and dismisses when button visible."""
    state = WorldState(
        active_states={"dialog_error"},
        element_visible={"dialog_error_close": True},
    )
    result = dismiss_via_close_button(state)
    assert result is not None
    assert ("click_element", "dialog_error_close") in result
    assert ("dismiss_dialog", "dialog_error") in result


def test_dismiss_via_close_button_not_visible() -> None:
    """Close button dismissal returns None when close button not visible."""
    state = WorldState(active_states={"dialog_error"}, element_visible={})
    result = dismiss_via_close_button(state)
    assert result is None


def test_confirm_dialog() -> None:
    """Confirm dialog clicks confirm button and dismisses dialog."""
    state = WorldState(active_states={"dialog_delete"})
    result = confirm_dialog(state, "dialog_delete", "btn_ok")
    assert result is not None
    assert len(result) == 2
    assert result[0] == ("click_element", "btn_ok")
    assert result[1] == ("dismiss_dialog", "dialog_delete")


def test_confirm_dialog_not_active() -> None:
    """Confirm dialog returns None when dialog not in active states."""
    state = WorldState(active_states=set())
    result = confirm_dialog(state, "dialog_delete", "btn_ok")
    assert result is None


def test_cancel_dialog() -> None:
    """Cancel dialog clicks auto-named cancel button and dismisses."""
    state = WorldState(active_states={"dialog_save"})
    result = cancel_dialog(state, "dialog_save")
    assert result is not None
    assert len(result) == 2
    assert result[0] == ("click_element", "dialog_save_cancel")
    assert result[1] == ("dismiss_dialog", "dialog_save")


def test_no_dialog_returns_none() -> None:
    """All dialog methods return None when no dialog/modal is active."""
    state = WorldState(active_states={"home", "sidebar"})
    assert dismiss_via_escape(state) is None
    assert dismiss_via_close_button(state) is None
    assert confirm_dialog(state, "dialog_nonexistent", "btn_ok") is None
    assert cancel_dialog(state, "dialog_nonexistent") is None
