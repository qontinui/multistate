#!/usr/bin/env python3
"""Example demonstrating reliability-weighted pathfinding.

This example shows how transition reliability tracking affects path selection.
When using a ReliabilityTracker, the pathfinding algorithm will prefer
transitions with higher success rates.
"""

import sys

sys.path.insert(0, "src")

from multistate.core.state import State
from multistate.pathfinding.multi_target import MultiTargetPathFinder, SearchStrategy
from multistate.transitions.executor import TransitionExecutor
from multistate.transitions.reliability import ReliabilityTracker
from multistate.transitions.transition import Transition


def main():
    """Demonstrate reliability-weighted pathfinding."""
    print("=" * 60)
    print("Reliability-Weighted Pathfinding Example")
    print("=" * 60)

    # Create states
    start = State("start", "Start")
    middle = State("middle", "Middle")
    goal = State("goal", "Goal")

    # Create two alternative transitions from start to middle
    # Both have the same base cost, but one will be more reliable
    reliable_path = Transition(
        id="reliable_transition",
        name="Reliable Path",
        from_states={start},
        activate_states={middle},
        exit_states={start},
        path_cost=5.0,
        action=lambda: True,  # Always succeeds
    )

    unreliable_path = Transition(
        id="unreliable_transition",
        name="Unreliable Path",
        from_states={start},
        activate_states={middle},
        exit_states={start},
        path_cost=5.0,  # Same base cost
        action=lambda: False,  # Often fails
    )

    # Transition from middle to goal
    finish = Transition(
        id="finish",
        name="Finish",
        from_states={middle},
        activate_states={goal},
        exit_states={middle},
        path_cost=1.0,
    )

    # Set up reliability tracker
    tracker = ReliabilityTracker()

    # Simulate execution history
    print("\n1. Building reliability history...")
    executor = TransitionExecutor(reliability_tracker=tracker)

    # Execute reliable path 10 times (all succeed)
    for i in range(10):
        result = executor.execute(reliable_path, {start})
        print(
            f"   Reliable path attempt {i + 1}: "
            f"{'SUCCESS' if result.success else 'FAILED'}"
        )

    # Execute unreliable path 10 times (half fail)
    active = {start}
    for i in range(10):
        result = executor.execute(unreliable_path, active)
        # Only update active state if transition succeeded
        if result.success:
            active = {middle}
        else:
            active = {start}
        print(
            f"   Unreliable path attempt {i + 1}: "
            f"{'SUCCESS' if result.success else 'FAILED'}"
        )

    # Show reliability stats
    print("\n2. Reliability Statistics:")
    reliable_stats = tracker.get_stats("reliable_transition")
    unreliable_stats = tracker.get_stats("unreliable_transition")

    print(
        f"   Reliable path: {reliable_stats.success_count}/{reliable_stats.total_attempts} "
        f"({reliable_stats.success_rate:.1%} success rate)"
    )
    print(
        f"   Unreliable path: {unreliable_stats.success_count}/{unreliable_stats.total_attempts} "
        f"({unreliable_stats.success_rate:.1%} success rate)"
    )

    # Show dynamic costs
    print("\n3. Dynamic Path Costs:")
    print(f"   Reliable path base cost: {reliable_path.path_cost}")
    reliable_dynamic = tracker.get_dynamic_cost(
        "reliable_transition", base_cost=reliable_path.path_cost
    )
    print(f"   Reliable path dynamic cost: {reliable_dynamic:.2f}")

    print(f"   Unreliable path base cost: {unreliable_path.path_cost}")
    unreliable_dynamic = tracker.get_dynamic_cost(
        "unreliable_transition", base_cost=unreliable_path.path_cost
    )
    print(f"   Unreliable path dynamic cost: {unreliable_dynamic:.2f}")

    # Find path WITHOUT reliability tracking
    print("\n4. Pathfinding WITHOUT reliability tracking:")
    finder_no_reliability = MultiTargetPathFinder(
        transitions=[reliable_path, unreliable_path, finish],
        strategy=SearchStrategy.DIJKSTRA,
    )

    path_no_reliability = finder_no_reliability.find_path_to_all({start}, {goal})
    if path_no_reliability:
        print(f"   Path found: {path_no_reliability}")
        print(f"   Total cost: {path_no_reliability.total_cost:.2f}")
        print("   Transitions:")
        for t in path_no_reliability.transitions_sequence:
            print(f"     - {t.name} (cost: {t.path_cost})")

    # Find path WITH reliability tracking
    print("\n5. Pathfinding WITH reliability tracking:")
    finder_with_reliability = MultiTargetPathFinder(
        transitions=[reliable_path, unreliable_path, finish],
        strategy=SearchStrategy.DIJKSTRA,
        reliability_tracker=tracker,
    )

    path_with_reliability = finder_with_reliability.find_path_to_all({start}, {goal})
    if path_with_reliability:
        print(f"   Path found: {path_with_reliability}")
        print(f"   Total cost: {path_with_reliability.total_cost:.2f}")
        print("   Transitions:")
        for t in path_with_reliability.transitions_sequence:
            dynamic_cost = tracker.get_dynamic_cost(t.id, base_cost=t.path_cost)
            print(f"     - {t.name} (base: {t.path_cost}, dynamic: {dynamic_cost:.2f})")

    print("\n" + "=" * 60)
    print("Key Takeaway:")
    print("With reliability tracking, the pathfinding algorithm automatically")
    print("prefers more reliable transitions by adjusting their costs based on")
    print("historical success/failure rates.")
    print("=" * 60)


if __name__ == "__main__":
    main()
