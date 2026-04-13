"""Tests for the HTNState wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

from multistate.planning.blackboard import Blackboard, BlackboardPlan
from multistate.planning.htn_state import HTNState, HTNStateConfig
from multistate.planning.planner import HTNPlanner, PlanResult, WorldState

# ---------------------------------------------------------------------------
# Minimal State stub (avoids importing full core.state with its dependencies)
# ---------------------------------------------------------------------------


@dataclass
class _FakeState:
    """Minimal stand-in for multistate.core.state.State."""

    id: str = "fake_state"
    name: str = "Fake State"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHTNState:
    """HTNState lifecycle and plan advancement tests."""

    def test_activate_creates_blackboard(self) -> None:
        """on_activate with parent -> child blackboard created."""
        parent_bb = Blackboard()
        parent_bb.set("shared_key", "shared_value")

        config = HTNStateConfig(
            blackboard_plan=BlackboardPlan({"counter": int}),
        )
        planner = MagicMock(spec=HTNPlanner)
        htn = HTNState(state=_FakeState(), config=config, planner=planner)  # type: ignore[arg-type]

        htn.on_activate(parent_blackboard=parent_bb)

        assert htn._active is True
        assert htn._blackboard is not None
        # BlackboardPlan initialises counter to int() == 0
        assert htn._blackboard.get("counter") == 0
        # Parent chain lookup works
        assert htn._blackboard.get("shared_key") == "shared_value"

    def test_activate_without_plan_creates_plain_blackboard(self) -> None:
        """on_activate without blackboard_plan creates a plain Blackboard."""
        config = HTNStateConfig()
        planner = MagicMock(spec=HTNPlanner)
        htn = HTNState(state=_FakeState(), config=config, planner=planner)  # type: ignore[arg-type]

        htn.on_activate()

        assert htn._active is True
        assert htn._blackboard is not None

    def test_deactivate_clears_state(self) -> None:
        """on_deactivate clears plan and blackboard."""
        config = HTNStateConfig()
        planner = MagicMock(spec=HTNPlanner)
        htn = HTNState(state=_FakeState(), config=config, planner=planner)  # type: ignore[arg-type]

        htn.on_activate()
        htn._current_plan = [("action_a",), ("action_b",)]
        htn._plan_index = 1

        htn.on_deactivate()

        assert htn._active is False
        assert htn._blackboard is None
        assert htn._current_plan is None
        assert htn._plan_index == 0

    def test_plan_calls_planner(self) -> None:
        """plan() delegates to planner.find_plan."""
        config = HTNStateConfig(task=("navigate_to", "dashboard"))
        planner = MagicMock(spec=HTNPlanner)
        planner.find_plan.return_value = PlanResult(
            success=True,
            actions=[("click_element", "btn")],
            planning_time_ms=2.0,
            nodes_explored=5,
        )

        htn = HTNState(state=_FakeState(), config=config, planner=planner)  # type: ignore[arg-type]
        ws = WorldState(active_states={"login_screen"})

        result = htn.plan(ws)

        assert result.success is True
        planner.find_plan.assert_called_once_with(ws, [("navigate_to", "dashboard")])
        assert htn.current_plan == [("click_element", "btn")]
        assert htn._plan_index == 0

    def test_plan_with_no_task(self) -> None:
        """plan() with no configured task passes empty task list."""
        config = HTNStateConfig()
        planner = MagicMock(spec=HTNPlanner)
        planner.find_plan.return_value = PlanResult(
            success=True,
            actions=[],
            planning_time_ms=0.5,
            nodes_explored=1,
        )

        htn = HTNState(state=_FakeState(), config=config, planner=planner)  # type: ignore[arg-type]
        htn.plan(WorldState())

        planner.find_plan.assert_called_once_with(WorldState(), [])

    def test_advance_returns_actions_in_order(self) -> None:
        """Set current_plan, advance() returns each action sequentially."""
        config = HTNStateConfig()
        planner = MagicMock(spec=HTNPlanner)
        htn = HTNState(state=_FakeState(), config=config, planner=planner)  # type: ignore[arg-type]

        htn.current_plan = [
            ("action_a",),
            ("action_b", "arg1"),
            ("action_c", "arg1", "arg2"),
        ]

        assert htn.advance() == ("action_a",)
        assert htn.advance() == ("action_b", "arg1")
        assert htn.advance() == ("action_c", "arg1", "arg2")

    def test_advance_returns_none_when_complete(self) -> None:
        """advance past end -> None."""
        config = HTNStateConfig()
        planner = MagicMock(spec=HTNPlanner)
        htn = HTNState(state=_FakeState(), config=config, planner=planner)  # type: ignore[arg-type]

        htn.current_plan = [("action_a",)]
        assert htn.advance() == ("action_a",)
        assert htn.advance() is None
        assert htn.advance() is None  # stays None

    def test_advance_returns_none_when_no_plan(self) -> None:
        """advance with no plan -> None."""
        config = HTNStateConfig()
        planner = MagicMock(spec=HTNPlanner)
        htn = HTNState(state=_FakeState(), config=config, planner=planner)  # type: ignore[arg-type]

        assert htn.advance() is None

    def test_is_plan_complete(self) -> None:
        """True when no plan or index past end."""
        config = HTNStateConfig()
        planner = MagicMock(spec=HTNPlanner)
        htn = HTNState(state=_FakeState(), config=config, planner=planner)  # type: ignore[arg-type]

        # No plan -> complete
        assert htn.is_plan_complete is True

        # Set plan -> not complete
        htn.current_plan = [("action_a",), ("action_b",)]
        assert htn.is_plan_complete is False

        # Advance past all -> complete
        htn.advance()
        htn.advance()
        assert htn.is_plan_complete is True

    def test_has_plan(self) -> None:
        """has_plan reflects whether a plan has been set."""
        config = HTNStateConfig()
        planner = MagicMock(spec=HTNPlanner)
        htn = HTNState(state=_FakeState(), config=config, planner=planner)  # type: ignore[arg-type]

        assert htn.has_plan is False
        htn.current_plan = [("action_a",)]
        assert htn.has_plan is True
