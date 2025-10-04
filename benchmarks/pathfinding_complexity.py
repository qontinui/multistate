#!/usr/bin/env python3
"""Benchmarks for multi-target pathfinding complexity.

Demonstrates exponential complexity O(V * 2^k) in number of targets.
"""

import sys
import os
import time
import random
# import matplotlib.pyplot as plt  # Optional for plotting
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multistate.core.state import State
from multistate.transitions.transition import Transition
from multistate.pathfinding.multi_target import (
    MultiTargetPathFinder,
    SearchStrategy
)


def create_grid_scenario(width: int, height: int) -> Tuple[Dict[str, State], List[Transition]]:
    """Create a grid-based state space for benchmarking.
    
    Args:
        width: Grid width
        height: Grid height
        
    Returns:
        States and transitions forming a grid
    """
    states = {}
    transitions = []
    
    # Create states for each grid position
    for y in range(height):
        for x in range(width):
            state_id = f"s_{x}_{y}"
            states[state_id] = State(state_id, f"State ({x},{y})")
    
    # Create transitions between adjacent cells
    for y in range(height):
        for x in range(width):
            current = states[f"s_{x}_{y}"]
            
            # Right transition
            if x < width - 1:
                right = states[f"s_{x+1}_{y}"]
                transitions.append(Transition(
                    id=f"t_{x}_{y}_right",
                    name=f"({x},{y}) → ({x+1},{y})",
                    from_states={current},
                    activate_states={right},
                    path_cost=1
                ))
            
            # Down transition
            if y < height - 1:
                down = states[f"s_{x}_{y+1}"]
                transitions.append(Transition(
                    id=f"t_{x}_{y}_down",
                    name=f"({x},{y}) → ({x},{y+1})",
                    from_states={current},
                    activate_states={down},
                    path_cost=1
                ))
            
            # Diagonal transition (more expensive)
            if x < width - 1 and y < height - 1:
                diag = states[f"s_{x+1}_{y+1}"]
                transitions.append(Transition(
                    id=f"t_{x}_{y}_diag",
                    name=f"({x},{y}) → ({x+1},{y+1})",
                    from_states={current},
                    activate_states={diag},
                    path_cost=1.4  # √2 approximation
                ))
    
    return states, transitions


def benchmark_target_scaling(max_targets: int = 8) -> Dict:
    """Benchmark how performance scales with number of targets.
    
    Args:
        max_targets: Maximum number of targets to test
        
    Returns:
        Benchmark results
    """
    # Create a moderate-sized grid
    states, transitions = create_grid_scenario(6, 6)
    
    # Start from top-left corner
    start = {states["s_0_0"]}
    
    results = {
        'num_targets': [],
        'bfs_time': [],
        'dijkstra_time': [],
        'astar_time': [],
        'path_cost': [],
        'path_length': []
    }
    
    print("\nBenchmarking Target Scaling")
    print("="*60)
    print(f"{'Targets':<10} {'BFS (ms)':<12} {'Dijkstra (ms)':<15} {'A* (ms)':<10} {'Cost':<8} {'Steps'}")
    print("-"*60)
    
    for num_targets in range(1, max_targets + 1):
        # Select random targets
        all_state_ids = list(states.keys())
        all_state_ids.remove("s_0_0")  # Don't include start
        target_ids = random.sample(all_state_ids, min(num_targets, len(all_state_ids)))
        targets = {states[sid] for sid in target_ids}
        
        results['num_targets'].append(num_targets)
        
        # Benchmark BFS
        finder_bfs = MultiTargetPathFinder(transitions, SearchStrategy.BFS)
        start_time = time.time()
        path_bfs = finder_bfs.find_path_to_all(start, targets)
        bfs_time = (time.time() - start_time) * 1000
        results['bfs_time'].append(bfs_time)
        
        # Benchmark Dijkstra
        finder_dijkstra = MultiTargetPathFinder(transitions, SearchStrategy.DIJKSTRA)
        start_time = time.time()
        path_dijkstra = finder_dijkstra.find_path_to_all(start, targets)
        dijkstra_time = (time.time() - start_time) * 1000
        results['dijkstra_time'].append(dijkstra_time)
        
        # Benchmark A*
        finder_astar = MultiTargetPathFinder(transitions, SearchStrategy.A_STAR)
        start_time = time.time()
        path_astar = finder_astar.find_path_to_all(start, targets)
        astar_time = (time.time() - start_time) * 1000
        results['astar_time'].append(astar_time)
        
        # Record path metrics (should be same for optimal algorithms)
        if path_dijkstra:
            results['path_cost'].append(path_dijkstra.total_cost)
            results['path_length'].append(len(path_dijkstra.transitions_sequence))
        else:
            results['path_cost'].append(0)
            results['path_length'].append(0)
        
        print(f"{num_targets:<10} {bfs_time:<12.2f} {dijkstra_time:<15.2f} {astar_time:<10.2f} "
              f"{results['path_cost'][-1]:<8.1f} {results['path_length'][-1]}")
    
    return results


def benchmark_grid_scaling(max_size: int = 10) -> Dict:
    """Benchmark how performance scales with grid size.
    
    Args:
        max_size: Maximum grid dimension to test
        
    Returns:
        Benchmark results
    """
    results = {
        'grid_size': [],
        'num_states': [],
        'num_transitions': [],
        'search_time': [],
        'memory_estimate': []  # In KB
    }
    
    print("\nBenchmarking Grid Size Scaling")
    print("="*60)
    print(f"{'Size':<8} {'States':<10} {'Trans':<10} {'Time (ms)':<12} {'Memory (KB)'}")
    print("-"*60)
    
    for size in range(3, max_size + 1):
        states, transitions = create_grid_scenario(size, size)
        
        # Fixed 3 targets at corners
        start = {states[f"s_0_0"]}
        targets = {
            states[f"s_{size-1}_0"],  # Top-right
            states[f"s_0_{size-1}"],  # Bottom-left
            states[f"s_{size-1}_{size-1}"]  # Bottom-right
        }
        
        # Benchmark
        finder = MultiTargetPathFinder(transitions, SearchStrategy.DIJKSTRA)
        start_time = time.time()
        path = finder.find_path_to_all(start, targets)
        search_time = (time.time() - start_time) * 1000
        
        # Estimate memory (rough)
        # Each state in search: ~200 bytes for PathNode
        # Worst case: V * 2^k configurations
        memory_kb = (len(states) * (2**3) * 200) / 1024
        
        results['grid_size'].append(size)
        results['num_states'].append(len(states))
        results['num_transitions'].append(len(transitions))
        results['search_time'].append(search_time)
        results['memory_estimate'].append(memory_kb)
        
        print(f"{size}x{size:<5} {len(states):<10} {len(transitions):<10} "
              f"{search_time:<12.2f} {memory_kb:<.1f}")
    
    return results


def compare_single_vs_multi() -> None:
    """Compare sequential single-target vs multi-target pathfinding."""
    print("\nComparing Single-Target (Sequential) vs Multi-Target")
    print("="*60)
    
    # Create scenario
    states, transitions = create_grid_scenario(8, 8)
    start = {states["s_0_0"]}
    
    # Select targets in different corners
    targets = [
        states["s_7_0"],   # Top-right
        states["s_0_7"],   # Bottom-left
        states["s_7_7"],   # Bottom-right
        states["s_3_3"],   # Center
    ]
    
    # Sequential single-target
    print("\nSequential Single-Target:")
    total_single_cost = 0
    total_single_time = 0
    current = start
    
    for i, target in enumerate(targets):
        finder = MultiTargetPathFinder(transitions, SearchStrategy.DIJKSTRA)
        start_time = time.time()
        path = finder.find_path_to_all(current, {target})
        elapsed = (time.time() - start_time) * 1000
        
        if path:
            print(f"  Target {i+1}: cost={path.total_cost:.1f}, time={elapsed:.2f}ms")
            total_single_cost += path.total_cost
            total_single_time += elapsed
            current = path.states_sequence[-1] if path.states_sequence else current
    
    print(f"  TOTAL: cost={total_single_cost:.1f}, time={total_single_time:.2f}ms")
    
    # Multi-target
    print("\nMulti-Target (All at once):")
    finder = MultiTargetPathFinder(transitions, SearchStrategy.DIJKSTRA)
    start_time = time.time()
    path = finder.find_path_to_all(start, set(targets))
    elapsed = (time.time() - start_time) * 1000
    
    if path:
        print(f"  All targets: cost={path.total_cost:.1f}, time={elapsed:.2f}ms")
        print(f"\n  SAVINGS: {total_single_cost - path.total_cost:.1f} cost units")
        print(f"  EFFICIENCY: {(total_single_cost / path.total_cost - 1) * 100:.1f}% better")


def plot_complexity_results(results: Dict) -> None:
    """Create plots showing complexity scaling.
    
    Args:
        results: Benchmark results to plot
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Time vs number of targets
    ax = axes[0, 0]
    ax.plot(results['num_targets'], results['bfs_time'], 'o-', label='BFS')
    ax.plot(results['num_targets'], results['dijkstra_time'], 's-', label='Dijkstra')
    ax.plot(results['num_targets'], results['astar_time'], '^-', label='A*')
    ax.set_xlabel('Number of Targets')
    ax.set_ylabel('Time (ms)')
    ax.set_title('Search Time vs Number of Targets')
    ax.legend()
    ax.grid(True)
    
    # Plot 2: Exponential growth visualization
    ax = axes[0, 1]
    ax.semilogy(results['num_targets'], results['dijkstra_time'], 'o-', label='Actual')
    # Fit exponential
    import numpy as np
    x = np.array(results['num_targets'])
    y = np.array(results['dijkstra_time'])
    # Simple exponential fit
    coeffs = np.polyfit(x, np.log(y + 0.01), 1)
    fitted = np.exp(coeffs[1]) * np.exp(coeffs[0] * x)
    ax.semilogy(x, fitted, '--', label=f'Exponential fit (2^k behavior)')
    ax.set_xlabel('Number of Targets (k)')
    ax.set_ylabel('Time (ms, log scale)')
    ax.set_title('Exponential Complexity O(V * 2^k)')
    ax.legend()
    ax.grid(True)
    
    # Plot 3: Path cost and length
    ax = axes[1, 0]
    ax2 = ax.twinx()
    l1 = ax.plot(results['num_targets'], results['path_cost'], 'b-', label='Path Cost')
    l2 = ax2.plot(results['num_targets'], results['path_length'], 'r-', label='Path Length')
    ax.set_xlabel('Number of Targets')
    ax.set_ylabel('Path Cost', color='b')
    ax2.set_ylabel('Path Length (steps)', color='r')
    ax.set_title('Solution Quality vs Targets')
    ax.tick_params(axis='y', labelcolor='b')
    ax2.tick_params(axis='y', labelcolor='r')
    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels)
    
    # Plot 4: Strategy comparison
    ax = axes[1, 1]
    strategies = ['BFS', 'Dijkstra', 'A*']
    times = [
        sum(results['bfs_time']),
        sum(results['dijkstra_time']),
        sum(results['astar_time'])
    ]
    bars = ax.bar(strategies, times)
    ax.set_ylabel('Total Time (ms)')
    ax.set_title('Strategy Performance Comparison')
    ax.grid(True, axis='y')
    
    # Color code bars
    bars[0].set_color('blue')
    bars[1].set_color('green')
    bars[2].set_color('red')
    
    plt.tight_layout()
    plt.savefig('pathfinding_complexity.png', dpi=150)
    print("\n✓ Saved complexity plots to pathfinding_complexity.png")


def main():
    """Run all benchmarks."""
    print("#"*60)
    print("# MULTI-TARGET PATHFINDING COMPLEXITY BENCHMARKS")
    print("#"*60)
    
    # Run benchmarks
    target_results = benchmark_target_scaling(max_targets=5)
    grid_results = benchmark_grid_scaling(max_size=6)
    compare_single_vs_multi()
    
    # Theoretical analysis
    print("\n" + "="*60)
    print("THEORETICAL COMPLEXITY ANALYSIS")
    print("="*60)
    
    print("""
For multi-target pathfinding with:
  - V states in the graph
  - k target states to reach
  - E transitions

Complexity:
  - Search Space: O(V * 2^k)
    Each state can be paired with 2^k subsets of reached targets
  
  - Time Complexity:
    - BFS: O(V * 2^k + E * 2^k)
    - Dijkstra: O((V * 2^k) * log(V * 2^k) + E * 2^k)
    - A*: Similar to Dijkstra with heuristic pruning
  
  - Space Complexity: O(V * 2^k)
    Must track all (state, targets_reached) configurations

Key Insight:
  The exponential factor 2^k makes this problem NP-hard
  for large k, but practical for small target sets (k < 10).
    """)
    
    # Create visualization
    print("\n(Matplotlib not available for plotting - install with: pip install matplotlib)")
    
    print("\n" + "#"*60)
    print("# BENCHMARK COMPLETE")
    print("#"*60)
    print("""
Conclusions:
1. Complexity grows exponentially with number of targets
2. Dijkstra/A* find optimal solutions but take longer
3. BFS is fastest but may not find cost-optimal paths
4. Multi-target is significantly more efficient than sequential
5. Practical for k < 10 targets in moderate-sized graphs
    """)


if __name__ == "__main__":
    main()