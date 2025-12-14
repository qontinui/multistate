#!/usr/bin/env python3
"""Test state references and history tracking."""

import sys
from datetime import datetime

sys.path.insert(0, "src")

from multistate.manager import StateManager, StateManagerConfig
from multistate.state_references import (
    StateHistory,
    StateReference,
    StateReferenceResolver,
    StateSnapshot,
)


def test_state_snapshot():
    """Test StateSnapshot creation and representation."""
    print("\n" + "=" * 60)
    print("Test 1: StateSnapshot")
    print("=" * 60)

    snapshot = StateSnapshot(
        states={"login", "welcome"},
        transition_id="initialize",
        metadata={"user": "test_user"},
    )

    assert snapshot.states == {"login", "welcome"}
    assert snapshot.transition_id == "initialize"
    assert snapshot.metadata["user"] == "test_user"
    assert isinstance(snapshot.timestamp, datetime)

    print(f"Snapshot: {snapshot}")
    print("[PASS] StateSnapshot works correctly")
    return True


def test_state_history_basic():
    """Test basic StateHistory operations."""
    print("\n" + "=" * 60)
    print("Test 2: StateHistory Basic Operations")
    print("=" * 60)

    history = StateHistory(max_history=5)

    # Record some snapshots
    history.record_snapshot({"login"}, transition_id="start")
    history.record_snapshot(
        {"main_menu"}, transition_id="login_success", metadata={"step": 1}
    )
    history.record_snapshot({"main_menu", "toolbar"}, transition_id="open_toolbar")

    # Check current state
    current = history.get_current_states()
    assert current == {"main_menu", "toolbar"}
    print(f"Current states: {current}")

    # Check previous state
    previous = history.get_previous_states(offset=1)
    assert previous == {"main_menu"}
    print(f"Previous states (offset=1): {previous}")

    # Check older state
    older = history.get_previous_states(offset=2)
    assert older == {"login"}
    print(f"Previous states (offset=2): {older}")

    # Check history length
    assert history.get_history_length() == 3
    print(f"History length: {history.get_history_length()}")

    print("[PASS] StateHistory basic operations work")
    return True


def test_state_history_expected():
    """Test expected states tracking."""
    print("\n" + "=" * 60)
    print("Test 3: Expected States Tracking")
    print("=" * 60)

    history = StateHistory()

    # Set expected states
    history.set_expected_states({"editor", "console", "sidebar"})

    expected = history.get_expected_states()
    assert expected == {"editor", "console", "sidebar"}
    print(f"Expected states: {expected}")

    # Clear expected states
    history.clear_expected_states()
    assert history.get_expected_states() == set()
    print("[PASS] Expected states cleared")

    return True


def test_state_history_changes():
    """Test state change detection."""
    print("\n" + "=" * 60)
    print("Test 4: State Change Detection")
    print("=" * 60)

    history = StateHistory()

    # Initial state
    history.record_snapshot({"login", "welcome"})

    # Change state
    history.record_snapshot({"main_menu", "toolbar", "welcome"})

    # Get changes
    added, removed = history.get_state_changes()
    assert added == {"main_menu", "toolbar"}
    assert removed == {"login"}

    print(f"Added states: {added}")
    print(f"Removed states: {removed}")
    print("[PASS] State change detection works")

    return True


def test_state_history_max_size():
    """Test history size limit."""
    print("\n" + "=" * 60)
    print("Test 5: History Size Limit")
    print("=" * 60)

    history = StateHistory(max_history=3)

    # Add 5 snapshots
    for i in range(5):
        history.record_snapshot({f"state_{i}"})

    # Should only keep last 3
    assert history.get_history_length() == 3
    print(f"History length after 5 snapshots: {history.get_history_length()}")

    # Current should be state_4
    current = history.get_current_states()
    assert current == {"state_4"}
    print(f"Current state: {current}")

    # Previous should be state_3
    previous = history.get_previous_states(offset=1)
    assert previous == {"state_3"}
    print(f"Previous state: {previous}")

    print("[PASS] History size limit works")
    return True


def test_reference_resolver():
    """Test StateReferenceResolver."""
    print("\n" + "=" * 60)
    print("Test 6: StateReferenceResolver")
    print("=" * 60)

    # Create a manager with state history enabled
    config = StateManagerConfig(enable_state_history=True)
    manager = StateManager(config)

    # Add states
    manager.add_state("login", "Login Screen")
    manager.add_state("main_menu", "Main Menu")
    manager.add_state("editor", "Code Editor")

    # Activate login
    manager.activate_states({"login"})

    # Resolve CURRENT reference
    current_states = manager.resolve_state_reference(StateReference.CURRENT)
    assert len(current_states) == 1
    assert list(current_states)[0].id == "login"
    print(f"CURRENT: {[s.id for s in current_states]}")

    # Deactivate login and activate main menu (simulating a state change)
    manager.deactivate_states({"login"})
    manager.activate_states({"main_menu"})

    # Resolve PREVIOUS reference
    # After deactivate + activate, we have 3 snapshots:
    # 0: {login}
    # 1: {} (after deactivate)
    # 2: {main_menu} (after activate)
    # So offset=1 gives us the empty set, offset=2 gives us login
    previous_states = manager.get_previous_states(offset=2)
    assert len(previous_states) == 1
    assert list(previous_states)[0].id == "login"
    print(f"PREVIOUS (offset=2): {[s.id for s in previous_states]}")

    # Resolve CURRENT reference again
    current_states = manager.resolve_state_reference(StateReference.CURRENT)
    assert len(current_states) == 1
    assert list(current_states)[0].id == "main_menu"
    print(f"CURRENT: {[s.id for s in current_states]}")

    print("[PASS] StateReferenceResolver works")
    return True


def test_manager_with_history():
    """Test StateManager with history enabled."""
    print("\n" + "=" * 60)
    print("Test 7: StateManager with History")
    print("=" * 60)

    # Create manager with history
    config = StateManagerConfig(enable_state_history=True, log_transitions=True)
    manager = StateManager(config)

    # Setup states
    manager.add_state("login")
    manager.add_state("main_menu")
    manager.add_state("editor")

    # Setup transition
    manager.add_transition(
        "login_success",
        from_states=["login"],
        activate_states=["main_menu"],
        exit_states=["login"],
    )

    # Start at login
    manager.activate_states({"login"})
    assert manager.get_history_length() == 1
    print(f"History after activation: {manager.get_history_length()} snapshots")

    # Execute transition
    success = manager.execute_transition("login_success")
    assert success
    assert manager.get_history_length() == 2
    print(f"History after transition: {manager.get_history_length()} snapshots")

    # Check state changes
    added, removed = manager.get_state_changes()
    assert added == {"main_menu"}
    assert removed == {"login"}
    print(f"State changes: +{added}, -{removed}")

    # Verify previous states
    previous = manager.get_previous_states()
    assert len(previous) == 1
    assert list(previous)[0].id == "login"
    print(f"Previous states: {[s.id for s in previous]}")

    print("[PASS] StateManager with history works")
    return True


def test_expected_states_in_transition():
    """Test expected states are set during transitions."""
    print("\n" + "=" * 60)
    print("Test 8: Expected States in Transitions")
    print("=" * 60)

    config = StateManagerConfig(enable_state_history=True)
    manager = StateManager(config)

    # Setup states
    manager.add_state("login")
    manager.add_state("main_menu")
    manager.add_state("toolbar")
    manager.add_state("sidebar")

    # Setup transition that activates multiple states
    manager.add_transition(
        "open_workspace",
        from_states=["main_menu"],
        activate_states=["toolbar", "sidebar"],
    )

    # Start at main menu
    manager.activate_states({"main_menu"})

    # Before transition, expected should be empty
    expected_before = manager.get_expected_states()
    assert len(expected_before) == 0
    print(f"Expected before transition: {expected_before}")

    # Execute transition
    manager.execute_transition("open_workspace")

    # After transition, expected should be cleared
    expected_after = manager.get_expected_states()
    assert len(expected_after) == 0
    print(f"Expected after transition: {expected_after}")

    # Verify the states are actually active
    active = manager.get_active_states()
    assert "toolbar" in active
    assert "sidebar" in active
    print(f"Active states: {active}")

    print("[PASS] Expected states tracking in transitions works")
    return True


def test_history_transitions_to_state():
    """Test finding transitions that led to a state."""
    print("\n" + "=" * 60)
    print("Test 9: Transitions to State Tracking")
    print("=" * 60)

    config = StateManagerConfig(enable_state_history=True)
    manager = StateManager(config)

    # Setup states
    manager.add_state("login")
    manager.add_state("main_menu")
    manager.add_state("editor")

    # Setup transitions
    manager.add_transition(
        "login_success",
        from_states=["login"],
        activate_states=["main_menu"],
        exit_states=["login"],
    )

    manager.add_transition(
        "open_editor", from_states=["main_menu"], activate_states=["editor"]
    )

    # Execute sequence
    manager.activate_states({"login"})
    manager.execute_transition("login_success")
    manager.execute_transition("open_editor")

    # Check transitions that activated main_menu
    transitions = manager.state_history.get_transitions_to_state("main_menu")
    assert "login_success" in transitions
    print(f"Transitions to main_menu: {transitions}")

    # Check transitions that activated editor
    transitions = manager.state_history.get_transitions_to_state("editor")
    assert "open_editor" in transitions
    print(f"Transitions to editor: {transitions}")

    print("[PASS] Transitions to state tracking works")
    return True


def test_manager_without_history():
    """Test that StateManager works without history enabled."""
    print("\n" + "=" * 60)
    print("Test 10: StateManager without History")
    print("=" * 60)

    # Create manager WITHOUT history (default)
    config = StateManagerConfig(enable_state_history=False)
    manager = StateManager(config)

    # Setup states
    manager.add_state("login")
    manager.add_state("main_menu")

    # Basic operations should work
    manager.activate_states({"login"})
    assert manager.is_active("login")
    print("[PASS] State activation works without history")

    # History operations should raise errors
    try:
        manager.get_previous_states()
        assert False, "Should have raised error"
    except Exception as e:
        print(f"[PASS] Expected error raised: {type(e).__name__}")

    try:
        manager.resolve_state_reference(StateReference.CURRENT)
        assert False, "Should have raised error"
    except Exception as e:
        print(f"[PASS] Expected error raised: {type(e).__name__}")

    print("[PASS] StateManager works correctly without history")
    return True


def run_all_tests():
    """Run all tests."""
    tests = [
        test_state_snapshot,
        test_state_history_basic,
        test_state_history_expected,
        test_state_history_changes,
        test_state_history_max_size,
        test_reference_resolver,
        test_manager_with_history,
        test_expected_states_in_transition,
        test_history_transitions_to_state,
        test_manager_without_history,
    ]

    print("\n" + "=" * 60)
    print("RUNNING STATE REFERENCES TESTS")
    print("=" * 60)

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n[FAIL] {test.__name__} FAILED: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n[PASS] All tests passed!")
        return True
    else:
        print(f"\n[FAIL] {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
