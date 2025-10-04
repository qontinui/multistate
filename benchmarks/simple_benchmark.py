#!/usr/bin/env python3
"""Simple benchmark demonstrating multi-target pathfinding complexity."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multistate.core.state import State
from multistate.transitions.transition import Transition
from multistate.pathfinding.multi_target import MultiTargetPathFinder, SearchStrategy


def create_simple_graph():
    """Create a simple graph for benchmarking."""
    states = {}
    for i in range(10):
        states[f"s{i}"] = State(f"s{i}", f"State {i}")
    
    transitions = []
    # Create a connected graph
    for i in range(9):
        transitions.append(Transition(
            id=f"t{i}",
            name=f"s{i} to s{i+1}",
            from_states={states[f"s{i}"]},
            activate_states={states[f"s{i+1}"]},
            path_cost=1
        ))
    
    # Add some cross-connections
    for i in range(0, 8, 2):
        if i + 2 < 10:
            transitions.append(Transition(
                id=f"tc{i}",
                name=f"s{i} to s{i+2}",
                from_states={states[f"s{i}"]},
                activate_states={states[f"s{i+2}"]},
                path_cost=1.5
            ))
    
    return states, transitions


def benchmark_scaling():
    """Simple benchmark showing exponential scaling."""
    print("\nMulti-Target Pathfinding Complexity Benchmark")
    print("="*60)
    
    states, transitions = create_simple_graph()
    start = {states["s0"]}
    
    print(f"{'Targets':<10} {'Time (ms)':<15} {'Path Cost':<12} {'Steps'}")
    print("-"*50)
    
    for num_targets in [1, 2, 3, 4]:
        # Select targets
        target_indices = list(range(3, 3 + num_targets))
        targets = {states[f"s{i}"] for i in target_indices}
        
        # Benchmark
        finder = MultiTargetPathFinder(transitions, SearchStrategy.DIJKSTRA)
        
        start_time = time.time()
        path = finder.find_path_to_all(start, targets)
        elapsed = (time.time() - start_time) * 1000
        
        if path:
            print(f"{num_targets:<10} {elapsed:<15.2f} {path.total_cost:<12.1f} {len(path.transitions_sequence)}")
        else:
            print(f"{num_targets:<10} No path found")
    
    # Show complexity analysis
    analysis = finder.analyze_complexity(num_states=10, num_targets=4)
    print(f"\nComplexity with 4 targets: {analysis['total_search_space']:,} configurations")
    print(f"Formula: {analysis['complexity_class']}")


def compare_approaches():
    """Compare sequential vs multi-target."""
    print("\nSequential vs Multi-Target Comparison")
    print("="*60)
    
    states, transitions = create_simple_graph()
    start = {states["s0"]}
    targets = [states["s3"], states["s5"], states["s7"]]
    
    # Sequential approach
    print("\nSequential (one target at a time):")
    total_cost = 0
    total_time = 0
    current = start
    
    for i, target in enumerate(targets):
        finder = MultiTargetPathFinder(transitions, SearchStrategy.DIJKSTRA)
        start_time = time.time()
        path = finder.find_path_to_all(current, {target})
        elapsed = (time.time() - start_time) * 1000
        
        if path:
            print(f"  Target {i+1}: cost={path.total_cost:.1f}, time={elapsed:.2f}ms")
            total_cost += path.total_cost
            total_time += elapsed
            current = path.states_sequence[-1] if path.states_sequence else current
    
    print(f"  TOTAL: cost={total_cost:.1f}, time={total_time:.2f}ms")
    
    # Multi-target approach
    print("\nMulti-Target (all at once):")
    finder = MultiTargetPathFinder(transitions, SearchStrategy.DIJKSTRA)
    start_time = time.time()
    path = finder.find_path_to_all(start, set(targets))
    elapsed = (time.time() - start_time) * 1000
    
    if path:
        print(f"  All targets: cost={path.total_cost:.1f}, time={elapsed:.2f}ms")
        print(f"\n  EFFICIENCY GAIN: {((total_cost/path.total_cost - 1) * 100):.0f}% better")


def main():
    """Run simple benchmarks."""
    print("#"*60)
    print("# MULTI-TARGET PATHFINDING BENCHMARKS")
    print("#"*60)
    
    benchmark_scaling()
    compare_approaches()
    
    print("\n" + "#"*60)
    print("# KEY INSIGHTS")
    print("#"*60)
    print("""
1. Search space grows as O(V * 2^k) where:
   - V = number of states
   - k = number of targets

2. Multi-target pathfinding finds globally optimal paths
   that visit ALL targets more efficiently than sequential.

3. The exponential growth makes it suitable for k < 10 targets.

4. Real-world applications:
   - Game AI navigating to multiple objectives
   - Robot path planning with multiple goals
   - UI automation reaching multiple states
    """)


if __name__ == "__main__":
    main()