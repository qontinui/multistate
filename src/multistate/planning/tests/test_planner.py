"""Tests for the HTN planner core, standard operators, and world adapter snapshot."""

from __future__ import annotations

from typing import Optional

from multistate.manager import StateManager
from multistate.planning.operators import STANDARD_OPERATORS
from multistate.planning.planner import HTNPlanner, WorldState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _op_step_a(state: WorldState) -> WorldState | None:
    new = state.copy()
    new.blackboard["a_done"] = True
    return new


def _op_step_b(state: WorldState) -> WorldState | None:
    new = state.copy()
    new.blackboard["b_done"] = True
    return new


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHTNPlanner:
    """Core planner tests."""

    def test_find_plan_with_operators_only(self) -> None:
        planner = HTNPlanner()
        planner.register_operator("step_a", _op_step_a)
        planner.register_operator("step_b", _op_step_b)

        state = WorldState()
        result = planner.find_plan(state, [("step_a",), ("step_b",)])

        assert result.success
        assert len(result.actions) == 2
        assert result.actions[0] == ("step_a",)
        assert result.actions[1] == ("step_b",)
        assert result.planning_time_ms >= 0
        assert result.nodes_explored >= 2

    def test_find_plan_with_methods(self) -> None:
        planner = HTNPlanner()
        planner.register_operator("step_a", _op_step_a)
        planner.register_operator("step_b", _op_step_b)

        def decompose_ab(state: WorldState) -> Optional[list[tuple]]:
            return [("step_a",), ("step_b",)]

        planner.register_method("do_ab", decompose_ab)

        result = planner.find_plan(WorldState(), [("do_ab",)])
        assert result.success
        assert result.actions == [("step_a",), ("step_b",)]

    def test_backtracking(self) -> None:
        planner = HTNPlanner()
        planner.register_operator("step_a", _op_step_a)

        def bad_method(state: WorldState) -> Optional[list[tuple]]:
            # Decomposes into unknown operator -> forces backtrack
            return [("nonexistent_op",)]

        def good_method(state: WorldState) -> Optional[list[tuple]]:
            return [("step_a",)]

        planner.register_method("goal", bad_method)
        planner.register_method("goal", good_method)

        result = planner.find_plan(WorldState(), [("goal",)])
        assert result.success
        assert result.actions == [("step_a",)]

    def test_max_depth_limit(self) -> None:
        planner = HTNPlanner(max_depth=3)

        def recursive_method(state: WorldState) -> Optional[list[tuple]]:
            return [("recurse",)]

        planner.register_method("recurse", recursive_method)

        result = planner.find_plan(WorldState(), [("recurse",)])
        assert not result.success
        assert result.error is not None

    def test_max_nodes_limit(self) -> None:
        planner = HTNPlanner(max_nodes=5)

        call_count = [0]

        def counting_method(state: WorldState) -> Optional[list[tuple]]:
            call_count[0] += 1
            return [("expand",)]

        planner.register_method("expand", counting_method)

        result = planner.find_plan(WorldState(), [("expand",)])
        assert not result.success
        assert result.nodes_explored <= 6  # may slightly overshoot by 1

    def test_empty_task_list(self) -> None:
        planner = HTNPlanner()
        result = planner.find_plan(WorldState(), [])
        assert result.success
        assert result.actions == []

    def test_unknown_task(self) -> None:
        planner = HTNPlanner()
        result = planner.find_plan(WorldState(), [("no_such_task",)])
        assert not result.success
        assert result.error is not None

    def test_world_state_copy(self) -> None:
        original = WorldState(
            active_states={"s1"},
            available_transitions={"t1"},
            element_visible={"btn": True},
            element_values={"input": "hello"},
            blackboard={"key": "val"},
        )
        copied = original.copy()

        # Mutate copy
        copied.active_states.add("s2")
        copied.available_transitions.add("t2")
        copied.element_visible["btn2"] = False
        copied.element_values["input2"] = "world"
        copied.blackboard["key2"] = "val2"

        # Original unchanged
        assert "s2" not in original.active_states
        assert "t2" not in original.available_transitions
        assert "btn2" not in original.element_visible
        assert "input2" not in original.element_values
        assert "key2" not in original.blackboard


class TestStandardOperators:
    """Test each operator's preconditions and effects."""

    def test_navigate_transition_success(self) -> None:
        state = WorldState(available_transitions={"go_login"})
        op = STANDARD_OPERATORS["navigate_transition"]
        result = op(state, "go_login")
        assert result is not None
        assert result.blackboard["_last_transition"] == "go_login"

    def test_navigate_transition_unavailable(self) -> None:
        state = WorldState(available_transitions=set())
        op = STANDARD_OPERATORS["navigate_transition"]
        assert op(state, "go_login") is None

    def test_click_element_visible(self) -> None:
        state = WorldState(element_visible={"btn_ok": True})
        op = STANDARD_OPERATORS["click_element"]
        result = op(state, "btn_ok")
        assert result is not None
        assert result.blackboard["_last_clicked"] == "btn_ok"

    def test_click_element_not_visible(self) -> None:
        state = WorldState(element_visible={"btn_ok": False})
        op = STANDARD_OPERATORS["click_element"]
        assert op(state, "btn_ok") is None

    def test_click_element_unknown(self) -> None:
        state = WorldState()
        op = STANDARD_OPERATORS["click_element"]
        assert op(state, "btn_ok") is None

    def test_type_text_success(self) -> None:
        state = WorldState(element_visible={"input_name": True})
        op = STANDARD_OPERATORS["type_text"]
        result = op(state, "input_name", "Alice")
        assert result is not None
        assert result.element_values["input_name"] == "Alice"

    def test_type_text_not_visible(self) -> None:
        state = WorldState(element_visible={"input_name": False})
        op = STANDARD_OPERATORS["type_text"]
        assert op(state, "input_name", "Alice") is None

    def test_wait_for_state(self) -> None:
        state = WorldState(active_states={"s1"})
        op = STANDARD_OPERATORS["wait_for_state"]
        result = op(state, "s2")
        assert result is not None
        assert "s2" in result.active_states
        assert "s1" in result.active_states

    def test_wait_for_element(self) -> None:
        state = WorldState()
        op = STANDARD_OPERATORS["wait_for_element"]
        result = op(state, "spinner")
        assert result is not None
        assert result.element_visible["spinner"] is True

    def test_dismiss_dialog_present(self) -> None:
        state = WorldState(active_states={"dialog_confirm"})
        op = STANDARD_OPERATORS["dismiss_dialog"]
        result = op(state, "dialog_confirm")
        assert result is not None
        assert "dialog_confirm" not in result.active_states

    def test_dismiss_dialog_absent(self) -> None:
        state = WorldState(active_states=set())
        op = STANDARD_OPERATORS["dismiss_dialog"]
        assert op(state, "dialog_confirm") is None


class TestWorldAdapterSnapshot:
    """Test WorldStateAdapter.snapshot via a real StateManager."""

    def test_world_adapter_snapshot(self) -> None:
        manager = StateManager()
        manager.add_state("login", "Login Screen")
        manager.add_state("dashboard", "Dashboard")
        manager.add_transition(
            "do_login",
            from_states=["login"],
            activate_states=["dashboard"],
            exit_states=["login"],
        )
        manager.activate_states({"login"})

        from multistate.planning.world_adapter import WorldStateAdapter

        adapter = WorldStateAdapter(manager)
        ws = adapter.snapshot(
            ui_elements={"btn_submit": True},
            ui_values={"input_user": "admin"},
        )

        assert "login" in ws.active_states
        assert "dashboard" not in ws.active_states
        assert "do_login" in ws.available_transitions
        assert ws.element_visible["btn_submit"] is True
        assert ws.element_values["input_user"] == "admin"
