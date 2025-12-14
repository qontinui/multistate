#!/usr/bin/env python3
"""Standalone test for visibility functionality.

This test doesn't rely on the full multistate import to avoid
the state_references.py type annotation issue.
"""

import sys
sys.path.insert(0, "src")

from multistate.core.state import State
from multistate.transitions.transition import Transition, TransitionPhase
from multistate.transitions.visibility import StaysVisible
from multistate.transitions.executor import TransitionExecutor


def test_stays_visible_enum():
    """Test StaysVisible enum values."""
    print("1. Testing StaysVisible enum...")

    assert StaysVisible.NONE.value == "NONE"
    assert StaysVisible.TRUE.value == "TRUE"
    assert StaysVisible.FALSE.value == "FALSE"

    assert str(StaysVisible.TRUE) == "TRUE"
    assert repr(StaysVisible.FALSE) == "StaysVisible.FALSE"

    print("   [OK] StaysVisible enum works correctly")
    return True


def test_transition_default():
    """Test that Transition defaults to StaysVisible.NONE."""
    print("2. Testing Transition default stays_visible...")

    s1 = State("s1", "State 1")
    s2 = State("s2", "State 2")

    t = Transition(
        id="test",
        name="Test",
        from_states={s1},
        activate_states={s2}
    )

    assert t.stays_visible == StaysVisible.NONE
    print("   [OK] Default is StaysVisible.NONE")
    return True


def test_transition_with_stays_visible():
    """Test setting stays_visible on Transition."""
    print("3. Testing Transition with stays_visible...")

    s1 = State("s1", "State 1")
    s2 = State("s2", "State 2")

    # Test TRUE
    t_true = Transition(
        id="test_true",
        name="Test True",
        from_states={s1},
        activate_states={s2},
        stays_visible=StaysVisible.TRUE
    )
    assert t_true.stays_visible == StaysVisible.TRUE

    # Test FALSE
    t_false = Transition(
        id="test_false",
        name="Test False",
        from_states={s1},
        activate_states={s2},
        stays_visible=StaysVisible.FALSE
    )
    assert t_false.stays_visible == StaysVisible.FALSE

    print("   [OK] stays_visible can be set to TRUE and FALSE")
    return True


def test_to_dict_includes_stays_visible():
    """Test that to_dict includes stays_visible."""
    print("4. Testing to_dict serialization...")

    s1 = State("s1", "State 1")
    s2 = State("s2", "State 2")

    t = Transition(
        id="test",
        name="Test",
        from_states={s1},
        activate_states={s2},
        stays_visible=StaysVisible.TRUE
    )

    data = t.to_dict()
    assert "stays_visible" in data
    assert data["stays_visible"] == "TRUE"

    print("   [OK] to_dict includes stays_visible")
    return True


def test_executor_visibility_phase_none():
    """Test executor visibility phase with StaysVisible.NONE."""
    print("5. Testing executor visibility phase (NONE)...")

    s1 = State("s1", "State 1")
    s2 = State("s2", "State 2")

    t = Transition(
        id="test",
        name="Test",
        from_states={s1},
        activate_states={s2},
        stays_visible=StaysVisible.NONE
    )

    executor = TransitionExecutor()
    result = executor.execute(t, {s1})

    assert result.success

    # Find visibility phase
    visibility_phase = None
    for phase_result in result.phase_results:
        if phase_result.phase == TransitionPhase.VISIBILITY:
            visibility_phase = phase_result
            break

    assert visibility_phase is not None
    assert visibility_phase.success
    assert visibility_phase.data["stays_visible"] == "NONE"
    assert len(visibility_phase.data["states_to_hide"]) == 0
    assert len(visibility_phase.data["states_to_show"]) == 0

    print("   [OK] NONE: No visibility changes")
    return True


def test_executor_visibility_phase_true():
    """Test executor visibility phase with StaysVisible.TRUE."""
    print("6. Testing executor visibility phase (TRUE)...")

    s1 = State("s1", "State 1")
    s2 = State("s2", "State 2")

    t = Transition(
        id="test",
        name="Test",
        from_states={s1},
        activate_states={s2},
        stays_visible=StaysVisible.TRUE
    )

    executor = TransitionExecutor()
    result = executor.execute(t, {s1})

    assert result.success

    # Find visibility phase
    visibility_phase = None
    for phase_result in result.phase_results:
        if phase_result.phase == TransitionPhase.VISIBILITY:
            visibility_phase = phase_result
            break

    assert visibility_phase is not None
    assert visibility_phase.success
    assert visibility_phase.data["stays_visible"] == "TRUE"
    assert "s1" in visibility_phase.data["states_to_show"]
    assert len(visibility_phase.data["states_to_hide"]) == 0

    print("   [OK] TRUE: Source state marked to stay visible")
    return True


def test_executor_visibility_phase_false():
    """Test executor visibility phase with StaysVisible.FALSE."""
    print("7. Testing executor visibility phase (FALSE)...")

    s1 = State("s1", "State 1")
    s2 = State("s2", "State 2")

    t = Transition(
        id="test",
        name="Test",
        from_states={s1},
        activate_states={s2},
        stays_visible=StaysVisible.FALSE
    )

    executor = TransitionExecutor()
    result = executor.execute(t, {s1})

    assert result.success

    # Find visibility phase
    visibility_phase = None
    for phase_result in result.phase_results:
        if phase_result.phase == TransitionPhase.VISIBILITY:
            visibility_phase = phase_result
            break

    assert visibility_phase is not None
    assert visibility_phase.success
    assert visibility_phase.data["stays_visible"] == "FALSE"
    assert "s1" in visibility_phase.data["states_to_hide"]
    assert len(visibility_phase.data["states_to_show"]) == 0

    print("   [OK] FALSE: Source state marked to hide")
    return True


def test_multiple_from_states():
    """Test visibility with multiple from_states."""
    print("8. Testing visibility with multiple from_states...")

    s1 = State("s1", "State 1")
    s2 = State("s2", "State 2")
    s3 = State("s3", "State 3")

    t = Transition(
        id="test",
        name="Test",
        from_states={s1, s2},
        activate_states={s3},
        stays_visible=StaysVisible.TRUE
    )

    executor = TransitionExecutor()
    result = executor.execute(t, {s1, s2})

    assert result.success

    # Find visibility phase
    visibility_phase = None
    for phase_result in result.phase_results:
        if phase_result.phase == TransitionPhase.VISIBILITY:
            visibility_phase = phase_result
            break

    assert visibility_phase is not None
    assert "s1" in visibility_phase.data["states_to_show"]
    assert "s2" in visibility_phase.data["states_to_show"]

    print("   [OK] All source states marked to stay visible")
    return True


def main():
    """Run all visibility tests."""
    print("=" * 60)
    print("Visibility Migration Tests")
    print("Testing StaysVisible enum and integration...")
    print("=" * 60)

    tests = [
        test_stays_visible_enum,
        test_transition_default,
        test_transition_with_stays_visible,
        test_to_dict_includes_stays_visible,
        test_executor_visibility_phase_none,
        test_executor_visibility_phase_true,
        test_executor_visibility_phase_false,
        test_multiple_from_states,
    ]

    results = []
    for test in tests:
        try:
            success = test()
            results.append((test.__name__, success))
        except Exception as e:
            print(f"   ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))

    print("\n" + "=" * 60)
    print("Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total} tests")

    if passed == total:
        print("\n✓ All visibility tests passed!")
        print("\nMigration successful:")
        print("- StaysVisible enum migrated from qontinui")
        print("- stays_visible property added to Transition")
        print("- TransitionExecutor respects visibility settings")
        print("- Visibility data included in TransitionResult")
        return 0
    else:
        print("\n✗ Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
