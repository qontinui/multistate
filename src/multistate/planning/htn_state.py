"""HTN State wrapper — embeds planning behaviour inside a State.

Provides :class:`HTNState` which wraps a core :class:`State` with HTN
planning capabilities, managing a scoped blackboard and plan lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from multistate.planning.blackboard import Blackboard, BlackboardPlan
from multistate.planning.planner import HTNPlanner, PlanResult, WorldState

if TYPE_CHECKING:
    from multistate.core.state import State


@dataclass
class HTNStateConfig:
    """Configuration for an :class:`HTNState`.

    Attributes:
        task: Task tuple to plan on activation.
        blackboard_plan: Variable contract for the scoped blackboard.
        replan_timeout: Seconds before replanning is triggered.
        on_success: Transition ID to fire when the plan succeeds.
        on_failure: Transition ID to fire when the plan fails.
    """

    task: tuple | None = None
    blackboard_plan: BlackboardPlan | None = None
    replan_timeout: float | None = None
    on_success: str | None = None
    on_failure: str | None = None


class HTNState:
    """Wraps a :class:`State` with HTN planning behaviour.

    Manages a scoped blackboard, plan lifecycle, and step-by-step
    advancement through the planned action sequence.

    Args:
        state: The core State this wraps.
        config: HTN configuration for this state.
        planner: The HTN planner to use for planning.
    """

    def __init__(
        self,
        state: State,
        config: HTNStateConfig,
        planner: HTNPlanner,
    ) -> None:
        self.state = state
        self.config = config
        self.planner = planner

        self._active: bool = False
        self._blackboard: Blackboard | None = None
        self._current_plan: list[tuple] | None = None
        self._plan_index: int = 0

    def on_activate(self, parent_blackboard: Blackboard | None = None) -> None:
        """Activate this HTN state, creating a scoped blackboard.

        Args:
            parent_blackboard: Optional parent blackboard for scope chaining.
        """
        if self.config.blackboard_plan is not None:
            self._blackboard = self.config.blackboard_plan.create_blackboard(
                parent=parent_blackboard
            )
        else:
            self._blackboard = Blackboard(parent=parent_blackboard)
        self._active = True

    def on_deactivate(self) -> None:
        """Deactivate this HTN state, clearing plan and blackboard."""
        self._active = False
        self._blackboard = None
        self._current_plan = None
        self._plan_index = 0

    def plan(self, world_state: WorldState) -> PlanResult:
        """Create a plan for the configured task.

        Args:
            world_state: Current world state to plan from.

        Returns:
            A :class:`PlanResult` from the planner.
        """
        tasks: list[tuple] = []
        if self.config.task is not None:
            tasks = [self.config.task]

        result = self.planner.find_plan(world_state, tasks)
        if result.success:
            self._current_plan = list(result.actions)
            self._plan_index = 0
        return result

    @property
    def is_plan_complete(self) -> bool:
        """True when there is no plan or all actions have been advanced past."""
        if self._current_plan is None:
            return True
        return self._plan_index >= len(self._current_plan)

    @property
    def has_plan(self) -> bool:
        """True when a plan has been set."""
        return self._current_plan is not None

    @property
    def current_plan(self) -> list[tuple] | None:
        """The current plan, or ``None`` if no plan is set."""
        return self._current_plan

    @current_plan.setter
    def current_plan(self, value: list[tuple] | None) -> None:
        self._current_plan = value
        self._plan_index = 0

    def advance(self) -> tuple | None:
        """Return the next action in the plan and advance the index.

        Returns:
            The next action tuple, or ``None`` if the plan is complete.
        """
        if self._current_plan is None:
            return None
        if self._plan_index >= len(self._current_plan):
            return None
        action = self._current_plan[self._plan_index]
        self._plan_index += 1
        return action
