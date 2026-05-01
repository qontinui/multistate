"""Tests for the PlanExecutor with replanning support."""

from __future__ import annotations

from unittest.mock import MagicMock

from multistate.planning.blackboard import Blackboard
from multistate.planning.executor import PlanExecutor, StepStatus
from multistate.planning.planner import HTNPlanner, PlanResult, WorldState
from multistate.planning.world_adapter import WorldStateAdapter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_executor(
    action_handlers: dict | None = None,
    max_replans: int = 5,
    planner: HTNPlanner | None = None,
    adapter: WorldStateAdapter | None = None,
) -> PlanExecutor:
    """Build a PlanExecutor with mocked planner and adapter."""
    if planner is None:
        planner = MagicMock(spec=HTNPlanner)
    # Executor accesses planner.operators for post-action state simulation
    if not hasattr(planner, "operators") or isinstance(planner.operators, MagicMock):
        planner.operators = {}
    if adapter is None:
        adapter = MagicMock(spec=WorldStateAdapter)
        adapter.snapshot.return_value = WorldState()
    if action_handlers is None:
        action_handlers = {}
    return PlanExecutor(
        planner=planner,
        adapter=adapter,
        action_handlers=action_handlers,
        max_replans=max_replans,
    )


def _noop_handler(blackboard: Blackboard, *args: object) -> None:
    """Handler that always succeeds."""


def _failing_handler(blackboard: Blackboard, *args: object) -> None:
    """Handler that always raises."""
    raise RuntimeError("action failed")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPlanExecutor:
    """Plan executor tests."""

    def test_execute_simple_plan(self) -> None:
        """3-action plan, all handlers succeed -> success, 3 steps recorded."""
        calls: list[str] = []

        def handler_a(bb: Blackboard) -> None:
            calls.append("a")

        def handler_b(bb: Blackboard) -> None:
            calls.append("b")

        def handler_c(bb: Blackboard) -> None:
            calls.append("c")

        adapter = MagicMock(spec=WorldStateAdapter)
        state = WorldState(active_states={"s1"})
        adapter.snapshot.return_value = state

        executor = _make_executor(
            action_handlers={
                "action_a": handler_a,
                "action_b": handler_b,
                "action_c": handler_c,
            },
            adapter=adapter,
        )

        plan = [("action_a",), ("action_b",), ("action_c",)]
        result = executor.execute(plan, state, original_tasks=[("do_stuff",)])

        assert result.success is True
        assert len(result.steps_executed) == 3
        assert all(s.status == StepStatus.SUCCESS for s in result.steps_executed)
        assert calls == ["a", "b", "c"]
        assert result.replans == 0

    def test_execute_handler_failure_triggers_replan(self) -> None:
        """Handler raises exception, planner finds alternative -> replanned."""
        call_count = 0

        def flaky_handler(bb: Blackboard) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("first try fails")

        planner = MagicMock(spec=HTNPlanner)
        planner.find_plan.return_value = PlanResult(
            success=True,
            actions=[("flaky_action",)],
            planning_time_ms=1.0,
            nodes_explored=1,
        )

        adapter = MagicMock(spec=WorldStateAdapter)
        adapter.snapshot.return_value = WorldState()

        executor = _make_executor(
            action_handlers={"flaky_action": flaky_handler},
            planner=planner,
            adapter=adapter,
        )

        plan = [("flaky_action",)]
        result = executor.execute(plan, WorldState(), original_tasks=[("task",)])

        assert result.success is True
        assert result.replans == 1
        # First step failed, then replanned step succeeded
        failed_steps = [
            s for s in result.steps_executed if s.status == StepStatus.FAILED
        ]
        assert len(failed_steps) == 1
        success_steps = [
            s for s in result.steps_executed if s.status == StepStatus.SUCCESS
        ]
        assert len(success_steps) == 1

    def test_execute_max_replans_exceeded(self) -> None:
        """Handler always fails, verify max_replans limit -> failure."""
        planner = MagicMock(spec=HTNPlanner)
        planner.find_plan.return_value = PlanResult(
            success=True,
            actions=[("bad_action",)],
            planning_time_ms=1.0,
            nodes_explored=1,
        )

        adapter = MagicMock(spec=WorldStateAdapter)
        adapter.snapshot.return_value = WorldState()

        executor = _make_executor(
            action_handlers={"bad_action": _failing_handler},
            planner=planner,
            adapter=adapter,
            max_replans=2,
        )

        plan = [("bad_action",)]
        result = executor.execute(plan, WorldState(), original_tasks=[("task",)])

        assert result.success is False
        assert result.error == "Max replans exceeded"
        # Should have attempted action 3 times (initial + 2 replans)
        failed_steps = [
            s for s in result.steps_executed if s.status == StepStatus.FAILED
        ]
        assert len(failed_steps) == 3

    def test_execute_plan_exhausted(self) -> None:
        """Handler fails, replanning returns no plan -> PlanExhausted error."""
        planner = MagicMock(spec=HTNPlanner)
        planner.find_plan.return_value = PlanResult(
            success=False,
            actions=[],
            planning_time_ms=1.0,
            nodes_explored=1,
            error="No plan found",
        )

        adapter = MagicMock(spec=WorldStateAdapter)
        adapter.snapshot.return_value = WorldState()

        executor = _make_executor(
            action_handlers={"bad_action": _failing_handler},
            planner=planner,
            adapter=adapter,
        )

        plan = [("bad_action",)]
        result = executor.execute(plan, WorldState(), original_tasks=[("task",)])

        assert result.success is False
        assert result.error == "PlanExhausted"
        assert result.replans == 0

    def test_execute_state_divergence_triggers_replan(self) -> None:
        """Mock _refresh_state to return changed state -> replanning triggered."""
        initial_state = WorldState(active_states={"state_a"})
        diverged_state = WorldState(active_states={"state_b"})

        call_count = 0

        def changing_snapshot(
            ui_elements: object = None, ui_values: object = None
        ) -> WorldState:
            nonlocal call_count
            call_count += 1
            # First refresh after action_a succeeds returns diverged state
            if call_count == 1:
                return diverged_state
            return diverged_state

        adapter = MagicMock(spec=WorldStateAdapter)
        adapter.snapshot.side_effect = changing_snapshot

        planner = MagicMock(spec=HTNPlanner)
        # Replanning returns a new single-action plan
        planner.find_plan.return_value = PlanResult(
            success=True,
            actions=[("action_b",)],
            planning_time_ms=1.0,
            nodes_explored=1,
        )

        executor = _make_executor(
            action_handlers={
                "action_a": _noop_handler,
                "action_b": _noop_handler,
            },
            planner=planner,
            adapter=adapter,
        )

        plan = [("action_a",), ("action_b",)]
        result = executor.execute(plan, initial_state, original_tasks=[("task",)])

        assert result.success is True
        assert result.replans == 1
        planner.find_plan.assert_called_once()

    def test_execute_not_interruptable_skips_divergence_check(self) -> None:
        """type_text action doesn't trigger state divergence check."""
        initial_state = WorldState(active_states={"state_a"})
        diverged_state = WorldState(active_states={"state_b"})

        adapter = MagicMock(spec=WorldStateAdapter)
        # If divergence check ran, it would see different states
        adapter.snapshot.return_value = diverged_state

        planner = MagicMock(spec=HTNPlanner)

        executor = _make_executor(
            action_handlers={
                "type_text": _noop_handler,
                "action_b": _noop_handler,
            },
            planner=planner,
            adapter=adapter,
        )

        # type_text followed by another action
        plan = [("type_text", "field1", "hello"), ("action_b",)]
        result = executor.execute(plan, initial_state, original_tasks=[("task",)])

        assert result.success is True
        # No replanning should have occurred for type_text
        # The divergence check after action_b won't happen since it's the last
        assert result.replans == 0

    def test_execute_empty_plan(self) -> None:
        """Empty plan -> success with 0 steps."""
        executor = _make_executor()
        result = executor.execute([], WorldState(), original_tasks=[("task",)])

        assert result.success is True
        assert len(result.steps_executed) == 0
        assert result.replans == 0

    def test_execute_unknown_handler(self) -> None:
        """Action with no handler -> failure."""
        executor = _make_executor(action_handlers={})

        plan = [("unknown_action",)]
        result = executor.execute(plan, WorldState(), original_tasks=[("task",)])

        assert result.success is False
        assert "No handler for action" in (result.error or "")
        assert len(result.steps_executed) == 1
        assert result.steps_executed[0].status == StepStatus.FAILED
