"""HTN (Hierarchical Task Network) Planner for MultiState.

Provides a depth-first HTN planner that decomposes compound tasks into
primitive operators, producing executable plans over a WorldState.
"""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class WorldState:
    """Snapshot of the world that the planner reasons over.

    Fields:
        active_states: Currently active state IDs.
        available_transitions: Transition IDs that can fire right now.
        element_visible: Mapping of element ID to visibility.
        element_values: Mapping of element ID to current text value.
        blackboard: Arbitrary planner scratch-space.
    """

    active_states: set[str] = field(default_factory=set)
    available_transitions: set[str] = field(default_factory=set)
    element_visible: dict[str, bool] = field(default_factory=dict)
    element_values: dict[str, str] = field(default_factory=dict)
    blackboard: dict[str, Any] = field(default_factory=dict)

    def copy(self) -> WorldState:
        """Return a deep-enough copy suitable for planning branches."""
        return WorldState(
            active_states=set(self.active_states),
            available_transitions=set(self.available_transitions),
            element_visible=dict(self.element_visible),
            element_values=dict(self.element_values),
            blackboard=copy.deepcopy(self.blackboard),
        )


# Type aliases
Operator = Callable[..., Optional[WorldState]]
Method = Callable[..., Optional[list[tuple]]]


@dataclass
class PlanResult:
    """Result returned by :meth:`HTNPlanner.find_plan`.

    Fields:
        success: Whether a valid plan was found.
        actions: Ordered list of ``(operator_name, *args)`` tuples.
        planning_time_ms: Wall-clock time spent planning, in milliseconds.
        nodes_explored: Number of search nodes expanded.
        error: Human-readable error string on failure, else ``None``.
    """

    success: bool
    actions: list[tuple]
    planning_time_ms: float
    nodes_explored: int
    error: str | None = None


class HTNPlanner:
    """Depth-first HTN planner with backtracking.

    Register *operators* (primitive actions that transform a WorldState)
    and *methods* (decompositions of compound tasks into sub-tasks), then
    call :meth:`find_plan` to search for a sequence of operators that
    accomplishes the given task list.

    Args:
        max_depth: Maximum recursion depth before giving up.
        max_nodes: Maximum search nodes before giving up.
    """

    def __init__(self, max_depth: int = 16, max_nodes: int = 10_000) -> None:
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.operators: dict[str, Operator] = {}
        self.methods: dict[str, list[Method]] = {}

    # -- Registration ---------------------------------------------------------

    def register_operator(self, name: str, fn: Operator) -> None:
        """Register a primitive operator under *name*."""
        self.operators[name] = fn

    def register_method(self, task_name: str, fn: Method) -> None:
        """Register a decomposition method for *task_name*."""
        self.methods.setdefault(task_name, []).append(fn)

    # -- Planning -------------------------------------------------------------

    def find_plan(self, state: WorldState, tasks: list[tuple]) -> PlanResult:
        """Find a plan that accomplishes *tasks* starting from *state*.

        Each element of *tasks* is a tuple ``(task_name, *args)``.

        Returns:
            A :class:`PlanResult` with the outcome.
        """
        t0 = time.perf_counter()
        nodes = [0]  # mutable counter shared across recursion
        result = self._seek_plan(state, list(tasks), depth=0, nodes=nodes)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        if result is not None:
            return PlanResult(
                success=True,
                actions=result,
                planning_time_ms=elapsed_ms,
                nodes_explored=nodes[0],
            )
        return PlanResult(
            success=False,
            actions=[],
            planning_time_ms=elapsed_ms,
            nodes_explored=nodes[0],
            error="No plan found within search limits",
        )

    def _seek_plan(
        self,
        state: WorldState,
        tasks: list[tuple],
        depth: int,
        nodes: list[int],
    ) -> list[tuple] | None:
        """Recursive depth-first search with backtracking.

        Returns a list of operator tuples on success, or ``None`` to backtrack.
        """
        # Base case: all tasks accomplished
        if not tasks:
            return []

        # Budget guards
        if depth >= self.max_depth or nodes[0] >= self.max_nodes:
            return None

        nodes[0] += 1

        task = tasks[0]
        task_name = task[0]
        task_args = task[1:]
        remaining = tasks[1:]

        # 1. Try as primitive operator
        if task_name in self.operators:
            operator = self.operators[task_name]
            new_state = operator(state, *task_args)
            if new_state is not None:
                rest = self._seek_plan(new_state, remaining, depth + 1, nodes)
                if rest is not None:
                    return [task] + rest

        # 2. Try as compound task via methods
        if task_name in self.methods:
            for method in self.methods[task_name]:
                subtasks = method(state, *task_args)
                if subtasks is not None:
                    merged = subtasks + remaining
                    result = self._seek_plan(state, merged, depth + 1, nodes)
                    if result is not None:
                        return result

        # Backtrack
        return None
