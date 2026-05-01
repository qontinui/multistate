from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from multistate.planning.methods.loader import MethodLoader


@dataclass
class FakeWorldState:
    """Stand-in for WorldState while Phase 1 is not yet available."""

    active_states: set[str] = field(default_factory=set)
    available_transitions: set[str] = field(default_factory=set)
    element_visible: dict[str, bool] = field(default_factory=dict)
    element_values: dict[str, str] = field(default_factory=dict)
    blackboard: dict[str, Any] = field(default_factory=dict)


class TestMethodLoader:
    def _write_config(
        self, dir_path: Path, filename: str, data: dict[str, Any]
    ) -> Path:
        filepath = dir_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return filepath

    def test_load_from_file(self, tmp_path: Path) -> None:
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
                }
            ]
        }
        filepath = self._write_config(tmp_path, "nav.json", config)
        methods = MethodLoader.load_from_file(filepath)
        assert "navigate_to" in methods
        assert len(methods["navigate_to"]) == 1

        # Test that the method works
        state = FakeWorldState(active_states={"sidebar", "home"})
        result = methods["navigate_to"][0](state, "settings")
        assert result == [
            ("click_element", "sidebar_settings"),
            ("wait_for_state", "settings"),
        ]

    def test_load_from_directory(self, tmp_path: Path) -> None:
        config1 = {
            "methods": [
                {
                    "task_name": "navigate_to",
                    "name": "nav_method_1",
                    "actions": [["goto", "{target_state}"]],
                }
            ]
        }
        config2 = {
            "methods": [
                {
                    "task_name": "fill_form",
                    "name": "fill_method_1",
                    "actions": [["type_text", "{target_state}"]],
                }
            ]
        }
        self._write_config(tmp_path, "nav.json", config1)
        self._write_config(tmp_path, "form.json", config2)

        methods = MethodLoader.load_from_directory(tmp_path)
        assert "navigate_to" in methods
        assert "fill_form" in methods

    def test_method_preconditions(self, tmp_path: Path) -> None:
        config = {
            "methods": [
                {
                    "task_name": "navigate_to",
                    "name": "nav_with_precond",
                    "preconditions": {"active_states_include": ["sidebar"]},
                    "actions": [["click_element", "sidebar_{target_state}"]],
                }
            ]
        }
        filepath = self._write_config(tmp_path, "nav.json", config)
        methods = MethodLoader.load_from_file(filepath)

        # Precondition not met — no sidebar
        state = FakeWorldState(active_states={"home"})
        result = methods["navigate_to"][0](state, "settings")
        assert result is None

    def test_method_string_interpolation(self, tmp_path: Path) -> None:
        config = {
            "methods": [
                {
                    "task_name": "navigate_to",
                    "name": "nav_interpolated",
                    "actions": [
                        ["navigate", "to_{target_state}"],
                        ["verify", "{target_state}_loaded"],
                    ],
                }
            ]
        }
        filepath = self._write_config(tmp_path, "nav.json", config)
        methods = MethodLoader.load_from_file(filepath)

        state = FakeWorldState()
        result = methods["navigate_to"][0](state, "dashboard")
        assert result == [
            ("navigate", "to_dashboard"),
            ("verify", "dashboard_loaded"),
        ]
