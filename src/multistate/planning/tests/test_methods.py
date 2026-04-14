from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from multistate.planning.methods.generic import (fill_form_sequential,
                                                 handle_unexpected_dialog,
                                                 login_generic,
                                                 navigate_to_via_menu,
                                                 navigate_to_via_pathfinding)


@dataclass
class FakeWorldState:
    """Stand-in for WorldState while Phase 1 is not yet available."""

    active_states: set[str] = field(default_factory=set)
    available_transitions: set[str] = field(default_factory=set)
    element_visible: dict[str, bool] = field(default_factory=dict)
    element_values: dict[str, str] = field(default_factory=dict)
    blackboard: dict[str, Any] = field(default_factory=dict)


class TestNavigateTo:
    def test_navigate_to_already_there(self) -> None:
        state = FakeWorldState(active_states={"dashboard"})
        result = navigate_to_via_pathfinding(state, "dashboard")  # type: ignore[arg-type]
        assert result == []

    def test_navigate_to_pathfinding(self) -> None:
        state = FakeWorldState(active_states={"home"})
        result = navigate_to_via_pathfinding(state, "settings")  # type: ignore[arg-type]
        assert result == [("navigate_path", "settings")]

    def test_navigate_to_via_menu(self) -> None:
        state = FakeWorldState(active_states={"main_menu", "home"})
        result = navigate_to_via_menu(state, "settings")  # type: ignore[arg-type]
        assert result == [
            ("click_element", "menu_settings"),
            ("wait_for_state", "settings"),
        ]

    def test_navigate_to_via_menu_not_applicable(self) -> None:
        state = FakeWorldState(active_states={"home"})
        result = navigate_to_via_menu(state, "settings")  # type: ignore[arg-type]
        assert result is None


class TestFormMethods:
    def test_fill_form(self) -> None:
        state = FakeWorldState()
        fields = {"email_input": "test@example.com", "name_input": "John"}
        result = fill_form_sequential(state, fields)  # type: ignore[arg-type]
        assert result is not None
        # Each field should produce click + type pair
        assert len(result) == 4
        assert result[0] == ("click_element", "email_input")
        assert result[1] == ("type_text", "email_input", "test@example.com")
        assert result[2] == ("click_element", "name_input")
        assert result[3] == ("type_text", "name_input", "John")


class TestDialogHandling:
    def test_handle_dialog_present(self) -> None:
        state = FakeWorldState(active_states={"dialog_confirm", "modal_alert", "home"})
        result = handle_unexpected_dialog(state)  # type: ignore[arg-type]
        assert result is not None
        assert len(result) == 2
        dismissed = {action[1] for action in result}
        assert dismissed == {"dialog_confirm", "modal_alert"}

    def test_handle_dialog_absent(self) -> None:
        state = FakeWorldState(active_states={"home", "sidebar"})
        result = handle_unexpected_dialog(state)  # type: ignore[arg-type]
        assert result is None


class TestLogin:
    def test_login_from_other_screen(self) -> None:
        state = FakeWorldState(active_states={"home"})
        result = login_generic(state, "user1", "pass1")  # type: ignore[arg-type]
        assert result is not None
        # Should include navigate_to as first action
        assert result[0] == ("navigate_to", "login_screen")

    def test_login_from_login_screen(self) -> None:
        state = FakeWorldState(active_states={"login_screen"})
        result = login_generic(state, "user1", "pass1")  # type: ignore[arg-type]
        assert result is not None
        # Should NOT include navigate_to
        assert ("navigate_to", "login_screen") not in result
        # Should have fill_form subtask + click btn_login + wait
        assert ("click_element", "btn_login") in result
        assert ("wait_for_state", "dashboard") in result
