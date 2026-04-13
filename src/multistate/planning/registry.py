"""Central registry for HTN operators and methods.

Provides a one-call setup that registers standard operators, generic methods,
domain-specific method packs, and file-loaded methods into an HTNPlanner.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from multistate.planning.planner import HTNPlanner, WorldState  # noqa: F401

logger = logging.getLogger(__name__)


class PlannerRegistry:
    """Aggregates operators and methods from multiple sources into a planner."""

    def __init__(self) -> None:
        self._operators: dict[str, Callable] = {}
        self._methods: dict[str, list[Callable]] = {}

    def register_operator(self, name: str, fn: Callable) -> None:
        """Register a primitive operator under *name*."""
        self._operators[name] = fn

    def register_methods(self, task_name: str, methods: list[Callable]) -> None:
        """Register a list of methods for *task_name*."""
        self._methods.setdefault(task_name, []).extend(methods)

    def register_method_pack(self, pack: dict[str, list[Callable]]) -> None:
        """Register a dict of task_name -> method lists (like GENERIC_METHODS)."""
        for task_name, methods in pack.items():
            self.register_methods(task_name, methods)

    def load_methods_from_directory(self, dir_path: str | Path) -> int:
        """Load methods from JSON config files in a directory. Returns count loaded."""
        from multistate.planning.methods.loader import MethodLoader

        loaded = MethodLoader.load_from_directory(dir_path)
        count = 0
        for task_name, methods in loaded.items():
            self.register_methods(task_name, methods)
            count += len(methods)
        return count

    def build_planner(
        self, max_depth: int = 16, max_nodes: int = 10_000
    ) -> HTNPlanner:
        """Create a fully-configured HTNPlanner with all registered content."""
        planner = HTNPlanner(max_depth=max_depth, max_nodes=max_nodes)
        for name, fn in self._operators.items():
            planner.register_operator(name, fn)
        for task_name, methods in self._methods.items():
            for m in methods:
                planner.register_method(task_name, m)
        logger.info(
            "Built planner with %d operators and %d method groups",
            len(self._operators),
            len(self._methods),
        )
        return planner

    @property
    def operator_count(self) -> int:
        """Number of registered operators."""
        return len(self._operators)

    @property
    def method_count(self) -> int:
        """Total number of registered methods across all tasks."""
        return sum(len(ms) for ms in self._methods.values())

    @property
    def task_names(self) -> list[str]:
        """Sorted list of task names with registered methods."""
        return sorted(self._methods.keys())


def create_default_registry() -> PlannerRegistry:
    """Create a registry with all built-in operators and methods."""
    from multistate.planning.methods.dialogs import DIALOG_METHODS
    from multistate.planning.methods.forms import FORM_METHODS
    from multistate.planning.methods.generic import GENERIC_METHODS
    from multistate.planning.methods.navigation import NAVIGATION_METHODS
    from multistate.planning.operators import STANDARD_OPERATORS

    registry = PlannerRegistry()

    for name, fn in STANDARD_OPERATORS.items():
        registry.register_operator(name, fn)

    for pack in [GENERIC_METHODS, NAVIGATION_METHODS, FORM_METHODS, DIALOG_METHODS]:
        registry.register_method_pack(pack)

    return registry
