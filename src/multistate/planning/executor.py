"""Plan executor with replanning support.

Executes a sequence of planned actions, handling failures by requesting
fresh plans from the HTN planner when actions fail or the world state
diverges from expectations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from multistate.planning.blackboard import Blackboard
from multistate.planning.planner import HTNPlanner, WorldState
from multistate.planning.world_adapter import WorldStateAdapter


class StepStatus(Enum):
    """Outcome of a single execution step."""

    SUCCESS = "success"
    FAILED = "failed"
    REPLANNED = "replanned"


@dataclass
class ExecutionStep:
    """Record of one executed action."""

    action: tuple
    status: StepStatus
    error: str | None = None


@dataclass
class ExecutionResult:
    """Aggregate result of plan execution."""

    success: bool
    steps_executed: list[ExecutionStep] = field(default_factory=list)
    replans: int = 0
    final_state: WorldState | None = None
    error: str | None = None


class PlanExecutor:
    """Execute a plan with automatic replanning on failure or state divergence.

    Args:
        planner: The HTN planner used for replanning.
        adapter: World state adapter for refreshing state snapshots.
        action_handlers: Mapping of action name to callable handler.
        max_replans: Maximum number of replan attempts before giving up.
        not_interruptable: Action names that suppress divergence checks
            (e.g., multi-keystroke actions that shouldn't be interrupted).
    """

    _DEFAULT_NOT_INTERRUPTABLE: frozenset[str] = frozenset({"type_text"})

    def __init__(
        self,
        planner: HTNPlanner,
        adapter: WorldStateAdapter,
        action_handlers: dict[str, Callable],
        max_replans: int = 5,
        not_interruptable: frozenset[str] | None = None,
    ) -> None:
        self.planner = planner
        self.adapter = adapter
        self.action_handlers = action_handlers
        self.max_replans = max_replans
        self.not_interruptable = (
            not_interruptable
            if not_interruptable is not None
            else self._DEFAULT_NOT_INTERRUPTABLE
        )

    def execute(
        self,
        plan: list[tuple],
        initial_state: WorldState,
        original_tasks: list[tuple],
        blackboard: Blackboard | None = None,
    ) -> ExecutionResult:
        """Execute a plan, replanning on failure or state divergence.

        Args:
            plan: Ordered list of ``(action_name, *args)`` tuples.
            initial_state: The world state at the start of execution.
            original_tasks: The original task list, used for replanning.
            blackboard: Optional blackboard for handler context.

        Returns:
            An :class:`ExecutionResult` summarising the execution.
        """
        if blackboard is None:
            blackboard = Blackboard()

        steps: list[ExecutionStep] = []
        replans = 0
        current_state = initial_state
        remaining = list(plan)

        while remaining:
            action = remaining[0]
            action_name = action[0]
            action_args = action[1:]

            # Look up handler
            handler = self.action_handlers.get(action_name)
            if handler is None:
                steps.append(
                    ExecutionStep(
                        action=action,
                        status=StepStatus.FAILED,
                        error=f"No handler for action: {action_name}",
                    )
                )
                return ExecutionResult(
                    success=False,
                    steps_executed=steps,
                    replans=replans,
                    final_state=current_state,
                    error=f"No handler for action: {action_name}",
                )

            # Attempt to execute the action
            try:
                handler(blackboard, *action_args)
            except Exception as exc:
                steps.append(
                    ExecutionStep(
                        action=action,
                        status=StepStatus.FAILED,
                        error=str(exc),
                    )
                )

                # Attempt replanning
                if replans >= self.max_replans:
                    return ExecutionResult(
                        success=False,
                        steps_executed=steps,
                        replans=replans,
                        final_state=current_state,
                        error="Max replans exceeded",
                    )

                current_state = self._refresh_state(blackboard)
                replan_result = self.planner.find_plan(current_state, original_tasks)

                if not replan_result.success:
                    return ExecutionResult(
                        success=False,
                        steps_executed=steps,
                        replans=replans,
                        final_state=current_state,
                        error="PlanExhausted",
                    )

                remaining = list(replan_result.actions)
                replans += 1
                continue

            # Success
            steps.append(ExecutionStep(action=action, status=StepStatus.SUCCESS))
            remaining.pop(0)

            # Compute expected state by simulating the operator's effect.
            # This prevents false-positive divergence when an action
            # legitimately changes active_states (e.g. navigate_path).
            expected_state = current_state
            operator = self.planner.operators.get(action_name)
            if operator is not None:
                try:
                    simulated = operator(current_state, *action_args)
                    if simulated is not None:
                        expected_state = simulated
                except (TypeError, Exception):
                    pass  # Can't simulate — use pre-action state as baseline

            # State divergence check (skip for non-interruptable actions)
            if remaining and action_name not in self.not_interruptable:
                actual_state = self._refresh_state(blackboard)
                if self._state_diverged(expected_state, actual_state):
                    # Attempt replanning due to divergence
                    if replans >= self.max_replans:
                        return ExecutionResult(
                            success=False,
                            steps_executed=steps,
                            replans=replans,
                            final_state=actual_state,
                            error="Max replans exceeded",
                        )

                    current_state = actual_state
                    replan_result = self.planner.find_plan(
                        current_state, original_tasks
                    )

                    if not replan_result.success:
                        return ExecutionResult(
                            success=False,
                            steps_executed=steps,
                            replans=replans,
                            final_state=current_state,
                            error="PlanExhausted",
                        )

                    remaining = list(replan_result.actions)
                    replans += 1
                else:
                    current_state = actual_state

        return ExecutionResult(
            success=True,
            steps_executed=steps,
            replans=replans,
            final_state=current_state,
        )

    def _refresh_state(self, blackboard: Blackboard) -> WorldState:
        """Refresh the world state from the adapter.

        Passes UI element data from the blackboard if available.
        """
        ui_elements = blackboard.get("_ui_elements")
        ui_values = blackboard.get("_ui_values")
        return self.adapter.snapshot(
            ui_elements=ui_elements,
            ui_values=ui_values,
        )

    def _state_diverged(self, expected: WorldState, actual: WorldState) -> bool:
        """Check whether the actual state has diverged from expected.

        Currently checks only ``active_states``.
        """
        return expected.active_states != actual.active_states
