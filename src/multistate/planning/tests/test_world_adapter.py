"""Tests for WorldStateAdapter — snapshot and apply_transition."""

from __future__ import annotations

import pytest

from multistate.manager import StateManager
from multistate.planning.world_adapter import WorldStateAdapter


@pytest.fixture()
def setup_manager() -> tuple[StateManager, WorldStateAdapter]:
    """Create a small state graph and return (manager, adapter)."""
    manager = StateManager()
    manager.add_state("login", "Login Screen")
    manager.add_state("dashboard", "Dashboard")
    manager.add_state("settings", "Settings")

    manager.add_transition(
        "do_login",
        from_states=["login"],
        activate_states=["dashboard"],
        exit_states=["login"],
    )
    manager.add_transition(
        "open_settings",
        from_states=["dashboard"],
        activate_states=["settings"],
        exit_states=[],
    )

    manager.activate_states({"login"})
    return manager, WorldStateAdapter(manager)


class TestWorldAdapterSnapshot:
    def test_snapshot_captures_active_states(
        self, setup_manager: tuple[StateManager, WorldStateAdapter]
    ) -> None:
        manager, adapter = setup_manager
        ws = adapter.snapshot()
        assert "login" in ws.active_states
        assert "dashboard" not in ws.active_states

    def test_snapshot_captures_available_transitions(
        self, setup_manager: tuple[StateManager, WorldStateAdapter]
    ) -> None:
        manager, adapter = setup_manager
        ws = adapter.snapshot()
        assert "do_login" in ws.available_transitions
        # open_settings requires dashboard, which is not active
        assert "open_settings" not in ws.available_transitions


class TestWorldAdapterApplyTransition:
    def test_apply_transition_valid(
        self, setup_manager: tuple[StateManager, WorldStateAdapter]
    ) -> None:
        manager, adapter = setup_manager
        ws = adapter.snapshot()

        result = adapter.apply_transition(ws, "do_login")
        assert result is not None
        assert "login" not in result.active_states
        assert "dashboard" in result.active_states
        # After reaching dashboard, open_settings should be available
        assert "open_settings" in result.available_transitions
        assert result.blackboard["_last_transition"] == "do_login"

    def test_apply_transition_invalid(
        self, setup_manager: tuple[StateManager, WorldStateAdapter]
    ) -> None:
        manager, adapter = setup_manager
        ws = adapter.snapshot()

        # open_settings is not available from login state
        result = adapter.apply_transition(ws, "open_settings")
        assert result is None

        # Completely unknown transition
        result = adapter.apply_transition(ws, "nonexistent")
        assert result is None
