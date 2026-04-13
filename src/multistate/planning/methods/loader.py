from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from multistate.planning.planner import WorldState


class MethodLoader:
    """Load HTN methods from JSON configuration files."""

    @staticmethod
    def load_from_file(path: str | Path) -> dict[str, list[Callable[..., Any]]]:
        """Load methods from a JSON config file.

        Format:
        {
            "methods": [
                {
                    "task_name": "navigate_to",
                    "name": "navigate_via_sidebar",
                    "preconditions": {"active_states_include": ["sidebar"]},
                    "actions": [
                        ["click_element", "sidebar_{target_state}"],
                        ["wait_for_state", "{target_state}"]
                    ]
                }
            ]
        }
        """
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        result: dict[str, list[Callable[..., Any]]] = {}
        for method_config in data.get("methods", []):
            task_name = method_config["task_name"]
            method_fn = MethodLoader._build_method_from_config(method_config)
            if task_name not in result:
                result[task_name] = []
            result[task_name].append(method_fn)
        return result

    @staticmethod
    def load_from_directory(
        dir_path: str | Path,
    ) -> dict[str, list[Callable[..., Any]]]:
        """Load all .json files in a directory, merge results."""
        dir_path = Path(dir_path)
        merged: dict[str, list[Callable[..., Any]]] = {}
        for json_file in sorted(dir_path.glob("*.json")):
            file_methods = MethodLoader.load_from_file(json_file)
            for task_name, methods in file_methods.items():
                if task_name not in merged:
                    merged[task_name] = []
                merged[task_name].extend(methods)
        return merged

    @staticmethod
    def _build_method_from_config(
        config: dict[str, Any],
    ) -> Callable[..., list[tuple[str, ...]] | None]:
        """Build a method closure from a config dict."""
        preconditions: dict[str, Any] = config.get("preconditions", {})
        actions_template: list[list[str]] = config.get("actions", [])
        method_name: str = config.get("name", "unnamed_method")

        def method(
            state: WorldState, *args: Any, **kwargs: Any
        ) -> list[tuple[str, ...]] | None:
            # Check preconditions
            if not _check_preconditions(state, preconditions):
                return None

            # Build substitution context from kwargs and positional args
            subs: dict[str, str] = dict(kwargs)
            # Common positional arg names by convention
            arg_names = ["target_state", "element_id", "value"]
            for i, arg in enumerate(args):
                if i < len(arg_names):
                    subs[arg_names[i]] = str(arg)

            # Interpolate actions
            result: list[tuple[str, ...]] = []
            for action_parts in actions_template:
                interpolated = tuple(
                    part.format(**subs) if "{" in part else part
                    for part in action_parts
                )
                result.append(interpolated)
            return result

        method.__name__ = method_name  # type: ignore[attr-defined]
        method.__qualname__ = method_name  # type: ignore[attr-defined]
        return method


def _check_preconditions(state: WorldState, preconditions: dict[str, Any]) -> bool:
    """Check if a WorldState satisfies the given preconditions."""
    if "active_states_include" in preconditions:
        required = set(preconditions["active_states_include"])
        if not required.issubset(state.active_states):
            return False

    if "active_states_exclude" in preconditions:
        excluded = set(preconditions["active_states_exclude"])
        if excluded & state.active_states:
            return False

    if "element_visible" in preconditions:
        for elem_id, expected in preconditions["element_visible"].items():
            if state.element_visible.get(elem_id, False) != expected:
                return False

    return True
