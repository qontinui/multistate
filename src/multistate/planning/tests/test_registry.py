"""Tests for the PlannerRegistry and create_default_registry."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from multistate.planning.planner import HTNPlanner, WorldState
from multistate.planning.registry import PlannerRegistry, create_default_registry


def test_create_default_registry() -> None:
    """Default registry includes standard operators and methods from all packs."""
    registry = create_default_registry()
    # 6 standard operators
    assert registry.operator_count == 6
    # Methods from generic (7), navigation (4), forms (4), dialogs (4) = 19
    assert registry.method_count >= 19
    # Task names should include keys from all packs
    names = registry.task_names
    assert "navigate_to" in names
    assert "fill_form" in names
    assert "handle_dialog" in names
    assert "confirm_dialog" in names
    assert "cancel_dialog" in names
    assert "clear_and_fill" in names
    assert "select_dropdown" in names
    assert "login" in names
    assert "scroll_to" in names
    assert "submit_form" in names


def test_build_planner() -> None:
    """build_planner returns a working HTNPlanner with registered ops and methods."""
    registry = create_default_registry()
    planner = registry.build_planner()
    assert isinstance(planner, HTNPlanner)
    assert len(planner.operators) == 6
    assert "navigate_to" in planner.methods
    assert "fill_form" in planner.methods


def test_planner_with_all_methods_navigates() -> None:
    """Built planner can plan navigate_to with various state configurations."""
    registry = create_default_registry()
    planner = registry.build_planner()

    # Navigate when already at target
    state = WorldState(active_states={"settings"})
    result = planner.find_plan(state, [("navigate_to", "settings")])
    assert result.success

    # Navigate via breadcrumb
    state = WorldState(
        element_visible={"breadcrumb_bar": True, "breadcrumb_dashboard": True}
    )
    result = planner.find_plan(state, [("navigate_to", "dashboard")])
    assert result.success

    # Navigate via search
    state = WorldState(
        element_visible={
            "search_bar": True,
            "search_result_profile": True,
        }
    )
    result = planner.find_plan(state, [("navigate_to", "profile")])
    assert result.success


def test_register_method_pack() -> None:
    """Registering a custom pack adds its methods to the registry."""
    registry = PlannerRegistry()

    def my_method(state: WorldState) -> list[tuple[str, ...]] | None:
        return [("click_element", "custom")]

    pack = {"custom_task": [my_method]}
    registry.register_method_pack(pack)

    assert "custom_task" in registry.task_names
    assert registry.method_count == 1


def test_load_methods_from_directory() -> None:
    """Loading JSON configs from a temp directory adds methods."""
    config = {
        "methods": [
            {
                "task_name": "navigate_to",
                "name": "navigate_via_sidebar",
                "preconditions": {"active_states_include": ["sidebar"]},
                "actions": [
                    ["click_element", "sidebar_{target_state}"],
                    ["wait_for_state", "{target_state}"],
                ],
            },
            {
                "task_name": "open_settings",
                "name": "open_settings_menu",
                "preconditions": {},
                "actions": [["click_element", "settings_icon"]],
            },
        ]
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "nav_methods.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        registry = PlannerRegistry()
        count = registry.load_methods_from_directory(tmp_dir)

        assert count == 2
        assert "navigate_to" in registry.task_names
        assert "open_settings" in registry.task_names


def test_build_planner_custom_limits() -> None:
    """build_planner respects custom max_depth and max_nodes."""
    registry = PlannerRegistry()
    planner = registry.build_planner(max_depth=5, max_nodes=100)
    assert planner.max_depth == 5
    assert planner.max_nodes == 100


def test_register_operator() -> None:
    """Registering individual operators works."""
    registry = PlannerRegistry()

    def my_op(state: WorldState) -> WorldState | None:
        return state.copy()

    registry.register_operator("my_op", my_op)
    assert registry.operator_count == 1

    planner = registry.build_planner()
    assert "my_op" in planner.operators
