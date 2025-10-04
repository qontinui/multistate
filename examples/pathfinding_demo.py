#!/usr/bin/env python3
"""Demonstration of multi-target pathfinding with visualization."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multistate.core.state import State
from multistate.transitions.transition import Transition
from multistate.pathfinding.multi_target import MultiTargetPathFinder, SearchStrategy
from multistate.pathfinding.visualizer import PathVisualizer


def create_complex_scenario():
    """Create a more complex scenario to demonstrate pathfinding."""
    states = {}

    # Create states for a complex application
    states["splash"] = State("splash", "Splash Screen")
    states["login"] = State("login", "Login")
    states["dashboard"] = State("dashboard", "Dashboard")

    # Main UI components
    states["menu"] = State("menu", "Menu Bar")
    states["toolbar"] = State("toolbar", "Toolbar")
    states["sidebar"] = State("sidebar", "Sidebar")

    # Work areas
    states["editor"] = State("editor", "Code Editor")
    states["console"] = State("console", "Console")
    states["debugger"] = State("debugger", "Debugger")
    states["terminal"] = State("terminal", "Terminal")

    # Settings and dialogs
    states["settings"] = State("settings", "Settings", blocking=True)
    states["preferences"] = State("preferences", "Preferences")

    # Create transitions
    transitions = []

    # Initial flow
    transitions.append(Transition(
        id="t1",
        name="Splash→Login",
        from_states={states["splash"]},
        activate_states={states["login"]},
        exit_states={states["splash"]},
        path_cost=1
    ))

    transitions.append(Transition(
        id="t2",
        name="Login→Dashboard",
        from_states={states["login"]},
        activate_states={states["dashboard"], states["menu"]},
        exit_states={states["login"]},
        path_cost=2
    ))

    # Open workspace (multi-state activation!)
    transitions.append(Transition(
        id="t3",
        name="Open Workspace",
        from_states={states["dashboard"]},
        activate_states={states["toolbar"], states["sidebar"], states["editor"]},
        path_cost=3
    ))

    # Open development tools
    transitions.append(Transition(
        id="t4",
        name="Open Dev Tools",
        from_states={states["editor"]},
        activate_states={states["console"], states["debugger"]},
        path_cost=2
    ))

    # Open terminal
    transitions.append(Transition(
        id="t5",
        name="Open Terminal",
        from_states={states["editor"]},
        activate_states={states["terminal"]},
        path_cost=1
    ))

    # Settings flow
    transitions.append(Transition(
        id="t6",
        name="Open Settings",
        from_states={states["menu"]},
        activate_states={states["settings"]},
        path_cost=1
    ))

    transitions.append(Transition(
        id="t7",
        name="Settings→Preferences",
        from_states={states["settings"]},
        activate_states={states["preferences"]},
        path_cost=1
    ))

    # Direct shortcut
    transitions.append(Transition(
        id="t8",
        name="Quick Editor",
        from_states={states["login"]},
        activate_states={states["editor"]},
        exit_states={states["login"]},
        path_cost=10  # Expensive shortcut
    ))

    return states, transitions


def demonstrate_single_vs_multi_target():
    """Show the difference between single and multi-target pathfinding."""
    print("="*80)
    print("DEMONSTRATION: Single vs Multi-Target Pathfinding")
    print("="*80)

    states, transitions = create_complex_scenario()
    visualizer = PathVisualizer()

    # Starting point
    current = {states["splash"]}

    # We want to reach: editor, console, and debugger
    targets = {states["editor"], states["console"], states["debugger"]}

    print("\n1. SINGLE-TARGET APPROACH (Sequential)")
    print("-"*40)

    single_paths = []
    single_labels = []
    total_single_cost = 0

    current_single = current.copy()
    for target in targets:
        finder = MultiTargetPathFinder(transitions, SearchStrategy.DIJKSTRA)
        path = finder.find_path_to_all(current_single, {target})

        if path:
            single_paths.append(path)
            single_labels.append(f"To {target.name}")
            total_single_cost += path.total_cost
            print(f"\nPath to {target.name}:")
            print(visualizer.visualize_path_ascii(path))
            # Update current position for next search
            current_single = path.states_sequence[-1]

    print(f"\n** Total Single-Target Cost: {total_single_cost} **")

    print("\n2. MULTI-TARGET APPROACH (All at once)")
    print("-"*40)

    finder = MultiTargetPathFinder(transitions, SearchStrategy.DIJKSTRA)
    multi_path = finder.find_path_to_all(current, targets)

    if multi_path:
        print("\nMulti-Target Path:")
        print(visualizer.visualize_path_ascii(multi_path))
        print(f"\n** Multi-Target Cost: {multi_path.total_cost} **")
        print(f"** Savings: {total_single_cost - multi_path.total_cost} cost units **")

    # Compare all paths
    print("\n3. COMPARISON")
    print("-"*40)
    all_paths = single_paths + [multi_path]
    all_labels = single_labels + ["Multi-Target"]
    print(visualizer.compare_paths(all_paths, all_labels))


def demonstrate_search_strategies():
    """Compare different search strategies."""
    print("\n" + "="*80)
    print("DEMONSTRATION: Search Strategy Comparison")
    print("="*80)

    states, transitions = create_complex_scenario()
    visualizer = PathVisualizer()

    current = {states["splash"]}
    targets = {states["editor"], states["terminal"]}

    strategies = [
        (SearchStrategy.BFS, "BFS (Breadth-First)"),
        (SearchStrategy.DIJKSTRA, "Dijkstra (Cost-Optimal)"),
        (SearchStrategy.A_STAR, "A* (Heuristic)")
    ]

    paths = []
    labels = []

    for strategy, name in strategies:
        print(f"\n{name}:")
        print("-"*40)

        finder = MultiTargetPathFinder(transitions, strategy)
        path = finder.find_path_to_all(current, targets)

        if path:
            print(visualizer.visualize_path_ascii(path))
            paths.append(path)
            labels.append(name)

    # Compare strategies
    print("\nSTRATEGY COMPARISON:")
    print(visualizer.compare_paths(paths, labels))


def generate_graphviz_output():
    """Generate Graphviz visualization."""
    print("\n" + "="*80)
    print("GRAPHVIZ OUTPUT (for visualization)")
    print("="*80)

    states, transitions = create_complex_scenario()

    # Find a path to highlight
    current = {states["splash"]}
    targets = {states["editor"], states["console"], states["debugger"]}

    finder = MultiTargetPathFinder(transitions, SearchStrategy.DIJKSTRA)
    path = finder.find_path_to_all(current, targets)

    visualizer = PathVisualizer()
    dot_output = visualizer.generate_graphviz(transitions, path, targets)

    print("\nSave this to 'graph.dot' and run:")
    print("  dot -Tpng graph.dot -o graph.png")
    print("\nDOT Output:")
    print("-"*40)
    print(dot_output)


def analyze_complexity_scaling():
    """Analyze how complexity scales with targets."""
    print("\n" + "="*80)
    print("COMPLEXITY SCALING ANALYSIS")
    print("="*80)

    states, transitions = create_complex_scenario()

    # Create a pathfinder
    finder = MultiTargetPathFinder(transitions, SearchStrategy.BFS)

    print("\nHow search space grows with number of targets:")
    print("-"*50)
    print(f"{'Targets':<10} {'Search Space':<20} {'Relative Growth'}")
    print("-"*50)

    prev_space = 0
    for k in range(1, 8):
        analysis = finder.analyze_complexity(num_states=12, num_targets=k)
        space = analysis['total_search_space']
        growth = f"{space/prev_space:.1f}x" if prev_space > 0 else "baseline"
        print(f"{k:<10} {space:<20,} {growth}")
        prev_space = space

    print("\n** Key Insight: Exponential growth O(V * 2^k) **")
    print("Each additional target DOUBLES the search space!")


def main():
    """Run all demonstrations."""
    print("\n" + "#"*80)
    print("# MULTI-TARGET PATHFINDING DEMONSTRATION")
    print("#"*80)

    demonstrate_single_vs_multi_target()
    demonstrate_search_strategies()
    analyze_complexity_scaling()

    print("\n" + "#"*80)
    print("# KEY TAKEAWAYS")
    print("#"*80)

    print("""
1. Multi-target pathfinding finds optimal paths to ALL targets
2. More efficient than sequential single-target searches
3. Leverages multi-state transitions effectively
4. Complexity is exponential in number of targets
5. Different strategies optimize for different criteria:
   - BFS: Fewest transitions
   - Dijkstra: Lowest cost
   - A*: Balance with heuristic guidance
    """)


if __name__ == "__main__":
    main()