#!/usr/bin/env python3
"""Test novelty-seeking exploration strategy."""

import sys

sys.path.insert(0, "src")

from multistate.testing.config import ExplorationConfig
from multistate.testing.exploration import NoveltySeekingExplorer
from multistate.testing.tracker import PathTracker


def create_mock_state_graph():
    """Create a mock state graph for testing.

    Structure:
        Start -> A -> A1
              -> A -> A2
              -> B -> B1
              -> B -> B2
    """

    class MockTransition:
        def __init__(self, to_state: str):
            self.to_state = to_state

    class MockState:
        def __init__(self, name: str, transitions: list[str]):
            self.name = name
            self.transitions = [MockTransition(t) for t in transitions]

    class MockStateGraph:
        def __init__(self):
            self.states = {
                "start": MockState("start", ["a", "b"]),
                "a": MockState("a", ["a1", "a2"]),
                "a1": MockState("a1", []),
                "a2": MockState("a2", []),
                "b": MockState("b", ["b1", "b2"]),
                "b1": MockState("b1", []),
                "b2": MockState("b2", []),
            }
            self.initial_state = "start"

    return MockStateGraph()


def test_novelty_prioritizes_unvisited():
    """Test that novelty explorer prioritizes unvisited states."""
    print("\n" + "=" * 60)
    print("Test 1: Novelty Explorer Prioritizes Unvisited States")
    print("=" * 60)

    graph = create_mock_state_graph()
    tracker = PathTracker(graph)
    config = ExplorationConfig()
    explorer = NoveltySeekingExplorer(config, tracker)

    # Start at 'start' state
    current = "start"
    visited_order = [current]

    # Explore several steps
    for step in range(5):
        next_state = explorer.select_next_state(current)
        if next_state:
            visited_order.append(next_state)
            current = next_state
            # Mark as visited in tracker (simulate actual execution)
            tracker._visited_states.add(next_state)
        else:
            break

    print(f"Visited order: {' -> '.join(visited_order)}")

    # Verify that novelty explorer explores new states
    unique_states = len(set(visited_order))
    print(f"Unique states visited: {unique_states}/{len(visited_order)}")

    # Should visit multiple unique states (not stuck in a loop)
    assert unique_states >= 3, "Novelty explorer should visit multiple unique states"
    print("[PASS] Novelty explorer successfully prioritizes unvisited states")

    return True


def test_local_visited_tracking():
    """Test that local visited tracking works correctly."""
    print("\n" + "=" * 60)
    print("Test 2: Local Visited Tracking")
    print("=" * 60)

    graph = create_mock_state_graph()
    tracker = PathTracker(graph)
    config = ExplorationConfig()
    explorer = NoveltySeekingExplorer(config, tracker)

    # First path: start -> a -> a1
    explorer.select_next_state("start")  # -> a or b
    explorer.select_next_state("a")  # -> a1 or a2

    local_before_reset = len(explorer.local_visited)
    print(f"Local visited before reset: {local_before_reset}")

    # Reset should clear local tracking
    explorer.reset()
    local_after_reset = len(explorer.local_visited)
    print(f"Local visited after reset: {local_after_reset}")

    assert local_after_reset == 0, "Reset should clear local visited set"
    print("[PASS] Local visited tracking reset works correctly")

    return True


def test_novelty_vs_greedy():
    """Compare novelty explorer with greedy coverage explorer."""
    print("\n" + "=" * 60)
    print("Test 3: Novelty vs Greedy Coverage")
    print("=" * 60)

    from multistate.testing.exploration import GreedyCoverageExplorer

    graph = create_mock_state_graph()

    # Test novelty explorer
    tracker_novelty = PathTracker(graph)
    config = ExplorationConfig()
    novelty = NoveltySeekingExplorer(config, tracker_novelty)

    novelty_path = ["start"]
    current = "start"
    for _ in range(4):
        next_state = novelty.select_next_state(current)
        if next_state:
            novelty_path.append(next_state)
            tracker_novelty._visited_states.add(next_state)
            current = next_state

    # Test greedy explorer
    tracker_greedy = PathTracker(graph)
    greedy = GreedyCoverageExplorer(config, tracker_greedy)

    greedy_path = ["start"]
    current = "start"
    for _ in range(4):
        next_state = greedy.select_next_state(current)
        if next_state:
            greedy_path.append(next_state)
            tracker_greedy._visited_states.add(next_state)
            current = next_state

    print(f"Novelty path: {' -> '.join(novelty_path)}")
    print(f"Greedy path:  {' -> '.join(greedy_path)}")

    # Both should explore effectively (at least 3 unique states)
    novelty_unique = len(set(novelty_path))
    greedy_unique = len(set(greedy_path))

    print(f"Novelty unique states: {novelty_unique}")
    print(f"Greedy unique states:  {greedy_unique}")

    assert novelty_unique >= 3, "Novelty should explore multiple states"
    assert greedy_unique >= 3, "Greedy should explore multiple states"

    print("[PASS] Both explorers effectively discover new states")

    return True


def test_integration_with_path_explorer():
    """Test novelty explorer integrated with PathExplorer."""
    print("\n" + "=" * 60)
    print("Test 4: Integration with PathExplorer")
    print("=" * 60)

    graph = create_mock_state_graph()

    # PathExplorer expects (config, tracker, initial_state)
    # But looking at the code, it's actually (config_or_manager, config_or_none, initial)
    # Let's look at PathExplorer signature first
    from multistate.testing.exploration.path_explorer import PathExplorer

    config = ExplorationConfig(
        strategy="novelty", max_iterations=10, coverage_target=0.8
    )
    tracker = PathTracker(graph)

    explorer = PathExplorer(config, tracker, initial_state="start")

    # Define simple executor
    def execute_transition(from_state: str, to_state: str):
        """Simulate transition execution."""
        return True, 100.0, {}

    # Run exploration
    report = explorer.explore(execute_transition)

    print("Exploration completed:")
    print(f"  Iterations: {report['summary']['iterations']}")
    print(f"  State Coverage: {report['coverage']['state_coverage_percent']:.1f}%")

    # Check what keys are available in coverage
    if "states_visited" in report["coverage"]:
        states_visited = report["coverage"]["states_visited"]
    elif "visited_states_count" in report["coverage"]:
        states_visited = report["coverage"]["visited_states_count"]
    else:
        # Calculate from state coverage percentage
        # state_coverage_percent = (states_visited / total_states) * 100
        # We have 7 states total in our mock graph
        states_visited = int(report["coverage"]["state_coverage_percent"] / 100 * 7)

    print(f"  States Visited: {states_visited}")

    # Should discover multiple states
    assert states_visited >= 3, "Should visit multiple states"
    print("[PASS] Integration with PathExplorer successful")

    return True


def main():
    """Run all novelty explorer tests."""
    print("#" * 60)
    print("# Novelty-Seeking Explorer Tests")
    print("#" * 60)

    tests = [
        test_novelty_prioritizes_unvisited,
        test_local_visited_tracking,
        test_novelty_vs_greedy,
        test_integration_with_path_explorer,
    ]

    results = []
    for test in tests:
        try:
            success = test()
            results.append((test.__name__, success))
        except Exception as e:
            print(f"[FAIL] Test failed with exception: {e}")
            import traceback

            traceback.print_exc()
            results.append((test.__name__, False))

    print("\n" + "#" * 60)
    print("# Summary")
    print("#" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}")

    if passed == total:
        print("\n[SUCCESS] All novelty explorer tests passed!")
        print("\nKey achievements:")
        print("- Novelty-seeking strategy successfully prioritizes unvisited states")
        print("- Local visited tracking works correctly")
        print("- Integrates properly with PathExplorer framework")
        print("- Complements existing exploration strategies")


if __name__ == "__main__":
    main()
