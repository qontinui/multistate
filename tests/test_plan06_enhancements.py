#!/usr/bin/env python3
"""Tests for Plan 06: Mermaid output, round-trip serialization, and state timeouts."""

import sys
import time

sys.path.insert(0, "src")

from multistate.core.element import Element
from multistate.core.state import State, StateTimeout
from multistate.core.state_group import StateGroup
from multistate.manager import StateManager
from multistate.pathfinding.visualizer import PathVisualizer
from multistate.transitions.transition import Transition
from multistate.transitions.visibility import StaysVisible

# ==================== Mermaid Tests ====================


def test_mermaid_basic_diagram() -> None:
    """Generate Mermaid from a simple 3-state machine, verify valid syntax."""
    s1 = State(id="idle", name="Idle")
    s2 = State(id="loading", name="Loading")
    s3 = State(id="ready", name="Ready")

    t1 = Transition(
        id="start",
        name="click_start",
        from_states={s1},
        activate_states={s2},
        exit_states={s1},
    )
    t2 = Transition(
        id="done",
        name="load_complete",
        from_states={s2},
        activate_states={s3},
        exit_states={s2},
    )

    mermaid = PathVisualizer.generate_mermaid([t1, t2])

    assert mermaid.startswith("stateDiagram-v2"), "Must start with stateDiagram-v2"
    assert "Idle --> Loading : click_start" in mermaid
    assert "Loading --> Ready : load_complete" in mermaid
    print("OK: Basic Mermaid diagram generation works")


def test_mermaid_active_state_highlighting() -> None:
    """Generate with active state highlighting."""
    s1 = State(id="idle", name="Idle")
    s2 = State(id="loading", name="Loading")
    s3 = State(id="ready", name="Ready")

    t1 = Transition(
        id="start",
        name="click_start",
        from_states={s1},
        activate_states={s2},
        exit_states={s1},
    )
    t2 = Transition(
        id="done",
        name="load_complete",
        from_states={s2},
        activate_states={s3},
        exit_states={s2},
    )

    mermaid = PathVisualizer.generate_mermaid([t1, t2], active_states={s2})

    assert "classDef active" in mermaid
    assert "class Loading active" in mermaid
    # Inactive states should NOT have the active class
    assert "class Idle active" not in mermaid
    print("OK: Mermaid active state highlighting works")


def test_mermaid_with_groups() -> None:
    """Generate with groups rendered as nested states."""
    s1 = State(id="idle", name="Idle")
    s2 = State(id="toolbar", name="Toolbar")
    s3 = State(id="sidebar", name="Sidebar")
    s4 = State(id="editor", name="Editor")

    group = StateGroup(id="workspace", name="Workspace", states={s2, s3, s4})

    t1 = Transition(
        id="open",
        name="open_workspace",
        from_states={s1},
        activate_states={s2, s3, s4},
        exit_states={s1},
    )

    mermaid = PathVisualizer.generate_mermaid([t1], groups=[group])

    assert "state Workspace {" in mermaid
    assert "}" in mermaid
    # All group members should be inside the block
    assert "Toolbar" in mermaid
    assert "Sidebar" in mermaid
    assert "Editor" in mermaid
    print("OK: Mermaid group rendering works")


def test_mermaid_no_from_states() -> None:
    """Transitions with no from_states render as initial transitions."""
    s1 = State(id="idle", name="Idle")
    t1 = Transition(
        id="init",
        name="initialize",
        from_states=set(),
        activate_states={s1},
    )

    mermaid = PathVisualizer.generate_mermaid([t1])
    assert "[*] --> Idle : initialize" in mermaid
    print("OK: Mermaid initial transitions work")


def test_mermaid_path_visualization() -> None:
    """Generate path visualization with highlighted edges and targets."""
    s1 = State(id="idle", name="Idle")
    s2 = State(id="loading", name="Loading")
    s3 = State(id="ready", name="Ready")

    t1 = Transition(
        id="start",
        name="click_start",
        from_states={s1},
        activate_states={s2},
        exit_states={s1},
    )
    t2 = Transition(
        id="done",
        name="load_complete",
        from_states={s2},
        activate_states={s3},
        exit_states={s2},
    )

    # Build a fake Path
    from multistate.pathfinding.multi_target import Path

    path = Path(
        states_sequence=[{s1}, {s2}, {s3}],
        transitions_sequence=[t1, t2],
        targets={s3},
        total_cost=2.0,
    )

    # Path-only diagram
    mermaid = PathVisualizer.generate_mermaid_path(path)
    assert "stateDiagram-v2" in mermaid
    assert "Idle --> Loading : click_start" in mermaid
    assert "Loading --> Ready : load_complete" in mermaid
    assert "classDef pathNode" in mermaid
    assert "classDef target" in mermaid
    assert "class Ready target" in mermaid

    # Path with full graph context
    mermaid_full = PathVisualizer.generate_mermaid_path(path, all_transitions=[t1, t2])
    assert "Idle --> Loading" in mermaid_full
    assert "classDef target" in mermaid_full

    print("OK: Mermaid path visualization works")


def test_mermaid_diff() -> None:
    """Show before/after state differences."""
    s1 = State(id="login", name="Login")
    s2 = State(id="menu", name="Menu")
    s3 = State(id="toolbar", name="Toolbar")

    t1 = Transition(
        id="go",
        name="go",
        from_states={s1},
        activate_states={s2, s3},
        exit_states={s1},
    )

    before = {s1}
    after = {s2, s3}

    mermaid = PathVisualizer.generate_mermaid_diff([t1], before, after)

    assert "classDef removed" in mermaid
    assert "classDef added" in mermaid
    assert "class Login removed" in mermaid
    # Menu and Toolbar should be in "added"
    assert "class Menu added" in mermaid
    assert "class Toolbar added" in mermaid
    print("OK: Mermaid diff works")


# ==================== Serialization Tests ====================


def test_element_round_trip() -> None:
    """Element from_dict(to_dict()) round-trip."""
    elem = Element(id="btn1", name="Submit Button", type="button", metadata={"x": 10})
    data = elem.to_dict()
    restored = Element.from_dict(data)

    assert restored.id == elem.id
    assert restored.name == elem.name
    assert restored.type == elem.type
    assert restored.metadata == elem.metadata
    print("OK: Element round-trip serialization works")


def test_state_round_trip() -> None:
    """State from_dict(to_dict()) round-trip."""
    elem = Element(id="e1", name="E1")
    state = State(
        id="s1",
        name="Login",
        elements={elem},
        group="auth",
        mock_starting_probability=0.8,
        path_cost=2.0,
        blocking=True,
        blocks={"s2", "s3"},
        metadata={"priority": "high"},
    )
    data = state.to_dict()
    restored = State.from_dict(data)

    assert restored.id == state.id
    assert restored.name == state.name
    assert restored.group == state.group
    assert restored.mock_starting_probability == state.mock_starting_probability
    assert restored.path_cost == state.path_cost
    assert restored.blocking == state.blocking
    assert restored.blocks == state.blocks
    assert restored.metadata == state.metadata
    assert len(restored.elements) == 1
    print("OK: State round-trip serialization works")


def test_state_round_trip_with_timeout() -> None:
    """State with timeout serializes and deserializes correctly."""
    timeout = StateTimeout(
        duration_seconds=30.0, on_timeout="t_timeout", auto_transition=False
    )
    state = State(id="loading", name="Loading", timeout=timeout)
    data = state.to_dict()

    assert "timeout" in data
    assert data["timeout"]["duration_seconds"] == 30.0
    assert data["timeout"]["on_timeout"] == "t_timeout"
    assert data["timeout"]["auto_transition"] is False

    restored = State.from_dict(data)
    assert restored.timeout is not None
    assert restored.timeout.duration_seconds == 30.0
    assert restored.timeout.on_timeout == "t_timeout"
    assert restored.timeout.auto_transition is False
    print("OK: State with timeout round-trip works")


def test_state_without_timeout_no_key() -> None:
    """State without timeout should not have timeout key in dict."""
    state = State(id="s1", name="S1")
    data = state.to_dict()
    assert "timeout" not in data
    print("OK: State without timeout omits timeout key")


def test_state_group_round_trip() -> None:
    """StateGroup from_dict(to_dict()) round-trip."""
    s1 = State(id="s1", name="S1")
    s2 = State(id="s2", name="S2")
    group = StateGroup(
        id="g1", name="Group1", states={s1, s2}, metadata={"zone": "left"}
    )

    data = group.to_dict()
    state_lookup = {"s1": s1, "s2": s2}
    restored = StateGroup.from_dict(data, state_lookup)

    assert restored.id == group.id
    assert restored.name == group.name
    assert restored.metadata == group.metadata
    # States should be the SAME objects, not copies
    assert s1 in restored.states
    assert s2 in restored.states
    print("OK: StateGroup round-trip serialization works")


def test_transition_round_trip() -> None:
    """Transition from_dict(to_dict()) round-trip."""
    s1 = State(id="s1", name="S1")
    s2 = State(id="s2", name="S2")
    s3 = State(id="s3", name="S3")

    trans = Transition(
        id="t1",
        name="Go",
        from_states={s1},
        activate_states={s2, s3},
        exit_states={s1},
        path_cost=3.0,
        stays_visible=StaysVisible.TRUE,
        metadata={"category": "nav"},
    )

    data = trans.to_dict()
    state_lookup = {"s1": s1, "s2": s2, "s3": s3}
    restored = Transition.from_dict(data, state_lookup)

    assert restored.id == trans.id
    assert restored.name == trans.name
    assert restored.from_states == trans.from_states
    assert restored.activate_states == trans.activate_states
    assert restored.exit_states == trans.exit_states
    assert restored.path_cost == trans.path_cost
    assert restored.stays_visible == trans.stays_visible
    assert restored.metadata == trans.metadata
    # Callbacks should NOT be restored
    assert restored.action is None
    assert restored.incoming_actions == {}
    print("OK: Transition round-trip serialization works")


def test_transition_resolves_same_state_objects() -> None:
    """Verify transitions resolve to correct state objects, not copies."""
    s1 = State(id="s1", name="S1")
    s2 = State(id="s2", name="S2")

    trans = Transition(
        id="t1",
        name="Go",
        from_states={s1},
        activate_states={s2},
        exit_states={s1},
    )

    data = trans.to_dict()
    state_lookup = {"s1": s1, "s2": s2}
    restored = Transition.from_dict(data, state_lookup)

    # The from_states should contain the EXACT same State objects
    for fs in restored.from_states:
        assert fs is s1
    for ats in restored.activate_states:
        assert ats is s2
    print("OK: Transition resolves to same state objects")


def test_state_manager_round_trip() -> None:
    """StateManager from_dict(to_dict()) produces equivalent state machine."""
    manager = StateManager()

    manager.add_state("login", "Login Screen")
    manager.add_state("menu", "Main Menu")
    manager.add_state("editor", "Editor")
    manager.add_state("toolbar", "Toolbar")

    manager.add_transition(
        "login_success",
        name="Login Success",
        from_states=["login"],
        activate_states=["menu"],
        exit_states=["login"],
    )
    manager.add_transition(
        "open_workspace",
        name="Open Workspace",
        from_states=["menu"],
        activate_states=["editor", "toolbar"],
        exit_states=["menu"],
        path_cost=2.0,
    )

    manager.activate_states({"login"})

    # Serialize and restore
    data = manager.to_dict()
    restored = StateManager.from_dict(data)

    # Verify structure
    assert set(restored.states.keys()) == set(manager.states.keys())
    assert set(restored.transitions.keys()) == set(manager.transitions.keys())
    assert restored.get_active_states() == manager.get_active_states()

    # Verify re-serialization produces same data
    re_data = restored.to_dict()
    assert re_data["active_states"] == data["active_states"]
    assert len(re_data["states"]) == len(data["states"])
    assert len(re_data["transitions"]) == len(data["transitions"])

    print("OK: StateManager round-trip serialization works")


def test_state_manager_round_trip_with_groups() -> None:
    """StateManager with groups serializes correctly."""
    manager = StateManager()

    manager.add_state("s1", "S1", group="g1")
    manager.add_state("s2", "S2", group="g1")
    manager.add_state("s3", "S3")

    manager.add_transition(
        "t1",
        from_states=["s3"],
        activate_states=["s1", "s2"],
        exit_states=["s3"],
    )

    data = manager.to_dict()
    assert len(data["groups"]) == 1

    restored = StateManager.from_dict(data)
    assert "g1" in restored.groups
    assert len(restored.groups["g1"].states) == 2
    print("OK: StateManager round-trip with groups works")


def test_state_manager_version_field() -> None:
    """Serialized data includes version field."""
    manager = StateManager()
    data = manager.to_dict()
    assert "version" in data
    assert data["version"] == 1
    print("OK: Serialization version field present")


def test_callbacks_not_serialized() -> None:
    """Verify callbacks are not included in serialized output."""
    s1 = State(id="s1", name="S1")
    trans = Transition(
        id="t1",
        name="Go",
        from_states={s1},
        activate_states={s1},
        action=lambda: True,
        incoming_actions={"s1": lambda: None},
    )

    data = trans.to_dict()
    assert "action" not in data
    assert data["has_action"] is True  # Flag only
    assert data["incoming_actions"] == ["s1"]  # Keys only

    restored = Transition.from_dict(data, {"s1": s1})
    assert restored.action is None
    assert restored.incoming_actions == {}
    print("OK: Callbacks are not serialized (documented behavior)")


# ==================== Timeout Tests ====================


def test_state_timeout_check_before_duration() -> None:
    """State with timeout: check_timeout() returns False before duration."""
    timeout = StateTimeout(duration_seconds=10.0, on_timeout="t_timeout")
    state = State(id="loading", name="Loading", timeout=timeout)

    # Not activated yet
    assert state.check_timeout() is False

    # Activate
    state.on_activate()
    assert state.check_timeout() is False  # Just activated, not timed out yet
    print("OK: check_timeout() returns False before duration")


def test_state_timeout_check_after_duration() -> None:
    """State with timeout: check_timeout() returns True after duration."""
    timeout = StateTimeout(duration_seconds=0.05, on_timeout="t_timeout")
    state = State(id="loading", name="Loading", timeout=timeout)

    state.on_activate()
    time.sleep(0.08)
    assert state.check_timeout() is True
    print("OK: check_timeout() returns True after duration")


def test_state_no_timeout() -> None:
    """State without timeout: check_timeout() always returns False."""
    state = State(id="idle", name="Idle")
    assert state.check_timeout() is False
    state.on_activate()  # No-op since no timeout
    assert state.check_timeout() is False
    print("OK: No timeout -> check_timeout() always False")


def test_timeout_reset_on_deactivate_reactivate() -> None:
    """Timeout resets on deactivate/reactivate."""
    timeout = StateTimeout(duration_seconds=0.05, on_timeout="t_timeout")
    state = State(id="loading", name="Loading", timeout=timeout)

    state.on_activate()
    time.sleep(0.08)
    assert state.check_timeout() is True

    # Deactivate clears the timer
    state.on_deactivate()
    assert state.check_timeout() is False

    # Reactivate restarts the timer
    state.on_activate()
    assert state.check_timeout() is False  # Fresh activation
    print("OK: Timeout resets on deactivate/reactivate")


def test_auto_transition_on_timeout() -> None:
    """Auto-transition on timeout executes the timeout transition."""
    manager = StateManager()

    manager.add_state("loading", "Loading")
    manager.add_state("error", "Error")

    # Manually set the timeout on the state object
    loading = manager.get_state("loading")
    loading.timeout = StateTimeout(
        duration_seconds=0.05,
        on_timeout="loading_timeout",
        auto_transition=True,
    )

    manager.add_transition(
        "loading_timeout",
        name="Loading Timeout",
        from_states=["loading"],
        activate_states=["error"],
        exit_states=["loading"],
    )

    manager.activate_states({"loading"})
    assert manager.is_active("loading")

    # Wait for timeout
    time.sleep(0.08)

    timed_out = manager.check_timeouts()
    assert len(timed_out) == 1
    assert timed_out[0][0].id == "loading"

    # Auto-transition should have executed
    assert manager.is_active("error")
    assert not manager.is_active("loading")
    print("OK: Auto-transition on timeout works")


def test_manual_timeout_no_auto_transition() -> None:
    """Manual timeout (auto_transition=False): state flagged but no auto-transition."""
    manager = StateManager()

    manager.add_state("loading", "Loading")
    manager.add_state("error", "Error")

    loading = manager.get_state("loading")
    loading.timeout = StateTimeout(
        duration_seconds=0.05,
        on_timeout="loading_timeout",
        auto_transition=False,
    )

    manager.add_transition(
        "loading_timeout",
        from_states=["loading"],
        activate_states=["error"],
        exit_states=["loading"],
    )

    manager.activate_states({"loading"})
    time.sleep(0.08)

    timed_out = manager.check_timeouts()
    assert len(timed_out) == 1

    # Should NOT auto-transition
    assert manager.is_active("loading")
    assert not manager.is_active("error")
    print("OK: Manual timeout (no auto-transition) works")


def test_timeout_serialization_round_trip() -> None:
    """StateTimeout survives StateManager serialization round-trip."""
    manager = StateManager()
    manager.add_state("loading", "Loading")
    manager.add_state("error", "Error")

    loading = manager.get_state("loading")
    loading.timeout = StateTimeout(
        duration_seconds=30.0,
        on_timeout="t_timeout",
        auto_transition=False,
    )

    data = manager.to_dict()
    restored = StateManager.from_dict(data)

    r_loading = restored.get_state("loading")
    assert r_loading.timeout is not None
    assert r_loading.timeout.duration_seconds == 30.0
    assert r_loading.timeout.on_timeout == "t_timeout"
    assert r_loading.timeout.auto_transition is False
    print("OK: Timeout survives StateManager round-trip")


# ==================== Runner ====================


def run_all_tests() -> bool:
    """Run all tests and report results."""
    tests = [
        # Mermaid
        test_mermaid_basic_diagram,
        test_mermaid_active_state_highlighting,
        test_mermaid_with_groups,
        test_mermaid_no_from_states,
        test_mermaid_path_visualization,
        test_mermaid_diff,
        # Serialization
        test_element_round_trip,
        test_state_round_trip,
        test_state_round_trip_with_timeout,
        test_state_without_timeout_no_key,
        test_state_group_round_trip,
        test_transition_round_trip,
        test_transition_resolves_same_state_objects,
        test_state_manager_round_trip,
        test_state_manager_round_trip_with_groups,
        test_state_manager_version_field,
        test_callbacks_not_serialized,
        # Timeout
        test_state_timeout_check_before_duration,
        test_state_timeout_check_after_duration,
        test_state_no_timeout,
        test_timeout_reset_on_deactivate_reactivate,
        test_auto_transition_on_timeout,
        test_manual_timeout_no_auto_transition,
        test_timeout_serialization_round_trip,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
                print(f"  FAIL: {test.__name__} returned False")
        except Exception as e:
            failed += 1
            print(f"  FAIL: {test.__name__} raised: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
