#!/usr/bin/env python3
"""Test transition reliability tracking."""

import sys

sys.path.insert(0, "src")

# Import directly to avoid state_references.py type hint issue
from multistate.core.state import State
from multistate.transitions.executor import TransitionExecutor
from multistate.transitions.reliability import ReliabilityTracker
from multistate.transitions.transition import Transition


def test_basic_reliability_tracking():
    """Test basic success/failure tracking."""
    print("\n1. Testing basic reliability tracking...")

    tracker = ReliabilityTracker()

    # Record some successes
    tracker.record_success("t1", execution_time=0.1)
    tracker.record_success("t1", execution_time=0.15)
    tracker.record_success("t1", execution_time=0.12)

    stats = tracker.get_stats("t1")
    assert stats.success_count == 3
    assert stats.failure_count == 0
    assert stats.success_rate == 1.0
    assert abs(stats.average_time - 0.123) < 0.01  # ~0.123 seconds
    print("   [OK] Success tracking works correctly")

    # Record some failures
    tracker.record_failure("t1", execution_time=0.05)

    stats = tracker.get_stats("t1")
    assert stats.success_count == 3
    assert stats.failure_count == 1
    assert stats.total_attempts == 4
    assert stats.success_rate == 0.75  # 3/4
    assert stats.failure_rate == 0.25  # 1/4
    print("   [OK] Failure tracking works correctly")

    return True


def test_dynamic_cost_calculation():
    """Test dynamic cost calculation based on reliability."""
    print("\n2. Testing dynamic cost calculation...")

    tracker = ReliabilityTracker(cost_multiplier_on_failure=2.0)

    # No history yet - should return base cost
    cost = tracker.get_dynamic_cost("t1", base_cost=1.0)
    assert cost == 1.0
    print("   [OK] Base cost used when no history")

    # 100% success rate - should return base cost
    for _ in range(10):
        tracker.record_success("t1")

    cost = tracker.get_dynamic_cost("t1", base_cost=1.0)
    assert cost == 1.0
    print("   [OK] Base cost used for perfect success rate")

    # 50% success rate - should double the cost
    for _ in range(10):
        tracker.record_failure("t1")

    cost = tracker.get_dynamic_cost("t1", base_cost=1.0)
    assert abs(cost - 1.5) < 0.01  # 50% failure → 1.5x multiplier
    print(f"   [OK] Cost adjusted for 50% success rate: {cost:.2f}x")

    # 0% success rate - should reach max multiplier
    tracker.reset_stats("t2")
    for _ in range(10):
        tracker.record_failure("t2")

    cost = tracker.get_dynamic_cost("t2", base_cost=1.0)
    assert cost == 2.0  # Full multiplier applied
    print(f"   [OK] Cost adjusted for 0% success rate: {cost:.2f}x")

    return True


def test_executor_integration():
    """Test reliability tracking integrated with TransitionExecutor."""
    print("\n3. Testing executor integration...")

    # Create states
    s1 = State("s1", "State 1")
    s2 = State("s2", "State 2")
    s3 = State("s3", "State 3")

    # Create reliability tracker
    tracker = ReliabilityTracker()

    # Create executor with tracker
    executor = TransitionExecutor(reliability_tracker=tracker)

    # Create a successful transition
    t1 = Transition(
        id="t1",
        name="Transition 1",
        from_states={s1},
        activate_states={s2},
        exit_states={s1},
        action=lambda: True,  # Always succeeds
    )

    # Execute successfully
    active_states = {s1}
    result = executor.execute(t1, active_states)

    assert result.success
    stats = tracker.get_stats("t1")
    assert stats.success_count == 1
    assert stats.failure_count == 0
    print("   [OK] Successful transition recorded")

    # Create a failing transition
    def failing_action():
        raise RuntimeError("Transition failed")

    t2 = Transition(
        id="t2",
        name="Transition 2",
        from_states={s2},
        activate_states={s3},
        exit_states={s2},
        action=failing_action,
    )

    # Execute and fail
    active_states = {s2}
    result = executor.execute(t2, active_states)

    assert not result.success
    stats = tracker.get_stats("t2")
    assert stats.success_count == 0
    assert stats.failure_count == 1
    print("   [OK] Failed transition recorded")

    return True


def test_summary_statistics():
    """Test summary statistics across multiple transitions."""
    print("\n4. Testing summary statistics...")

    tracker = ReliabilityTracker()

    # Create diverse reliability history
    for _ in range(10):
        tracker.record_success("reliable_t")

    for _ in range(5):
        tracker.record_success("medium_t")
    for _ in range(5):
        tracker.record_failure("medium_t")

    for _ in range(10):
        tracker.record_failure("unreliable_t")

    summary = tracker.get_summary()
    assert summary["total_transitions"] == 3
    assert summary["total_attempts"] == 30
    assert summary["total_successes"] == 15
    assert summary["total_failures"] == 15
    assert summary["overall_success_rate"] == 0.5
    print("   [OK] Summary statistics correct")

    # Test least reliable
    least_reliable = tracker.get_least_reliable(limit=2)
    assert len(least_reliable) == 2
    assert least_reliable[0].transition_id == "unreliable_t"
    assert least_reliable[1].transition_id == "medium_t"
    print("   [OK] Least reliable transitions identified")

    # Test most reliable
    most_reliable = tracker.get_most_reliable(limit=2)
    assert len(most_reliable) == 2
    assert most_reliable[0].transition_id == "reliable_t"
    assert most_reliable[1].transition_id == "medium_t"
    print("   [OK] Most reliable transitions identified")

    return True


def test_cost_multiplier_bounds():
    """Test that cost multipliers respect min/max bounds."""
    print("\n5. Testing cost multiplier bounds...")

    tracker = ReliabilityTracker(
        cost_multiplier_on_failure=5.0,
        min_cost_multiplier=0.5,
        max_cost_multiplier=3.0,
    )

    # Create 100% failure transition
    for _ in range(10):
        tracker.record_failure("bad_t")

    # Cost should be capped at max_cost_multiplier
    cost = tracker.get_dynamic_cost("bad_t", base_cost=1.0)
    assert cost == 3.0  # Capped at max
    print(f"   [OK] Cost capped at max multiplier: {cost:.2f}x")

    # Test with different base cost
    cost = tracker.get_dynamic_cost("bad_t", base_cost=2.0)
    assert cost == 6.0  # 2.0 * 3.0
    print(f"   [OK] Base cost respected: {cost:.2f}")

    return True


def test_reset_functionality():
    """Test resetting statistics."""
    print("\n6. Testing reset functionality...")

    tracker = ReliabilityTracker()

    # Build up some history
    tracker.record_success("t1")
    tracker.record_success("t2")
    tracker.record_success("t3")

    assert len(tracker.get_all_stats()) == 3

    # Reset specific transition
    tracker.reset_stats("t1")
    assert len(tracker.get_all_stats()) == 2
    print("   [OK] Individual transition reset")

    # Reset all
    tracker.reset_stats()
    assert len(tracker.get_all_stats()) == 0
    print("   [OK] All transitions reset")

    return True


def test_execution_time_tracking():
    """Test execution time tracking."""
    print("\n7. Testing execution time tracking...")

    tracker = ReliabilityTracker()

    # Simulate different execution times
    tracker.record_success("t1", execution_time=0.1)
    tracker.record_success("t1", execution_time=0.2)
    tracker.record_success("t1", execution_time=0.3)

    stats = tracker.get_stats("t1")
    assert abs(stats.total_time - 0.6) < 0.001  # Floating point tolerance
    assert abs(stats.average_time - 0.2) < 0.001  # Floating point tolerance
    print(f"   [OK] Average execution time: {stats.average_time:.2f}s")

    # Check timestamp tracking
    assert stats.last_success_time is not None
    assert stats.last_failure_time is None
    print("   [OK] Timestamps tracked correctly")

    tracker.record_failure("t1")
    stats = tracker.get_stats("t1")
    assert stats.last_failure_time is not None
    print("   [OK] Failure timestamp recorded")

    return True


def test_stats_to_dict():
    """Test conversion to dictionary format."""
    print("\n8. Testing stats serialization...")

    tracker = ReliabilityTracker()

    tracker.record_success("t1", execution_time=0.5)
    tracker.record_failure("t1", execution_time=0.3)

    stats = tracker.get_stats("t1")
    data = stats.to_dict()

    assert data["transition_id"] == "t1"
    assert data["success_count"] == 1
    assert data["failure_count"] == 1
    assert data["total_attempts"] == 2
    assert data["success_rate"] == 0.5
    assert data["failure_rate"] == 0.5
    assert data["total_time"] == 0.8
    assert data["average_time"] == 0.4
    assert "last_success_time" in data
    assert "last_failure_time" in data
    print("   [OK] Stats serialization works correctly")

    return True


def run_all_tests():
    """Run all reliability tests."""
    tests = [
        test_basic_reliability_tracking,
        test_dynamic_cost_calculation,
        test_executor_integration,
        test_summary_statistics,
        test_cost_multiplier_bounds,
        test_reset_functionality,
        test_execution_time_tracking,
        test_stats_to_dict,
    ]

    print("=" * 60)
    print("RELIABILITY TRACKING TESTS")
    print("=" * 60)

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"   [FAIL] {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"   [FAIL] {test.__name__} raised exception: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
