"""Graph exploration utilities for state graphs.

This module provides utility functions for exploring and analyzing state graphs,
independent of specific exploration strategies.
"""

import sys
from collections import deque
from typing import Any, Dict, Set

from multistate.testing.tracker import PathTracker


def explore_graph(
    tracker: PathTracker, start_state: str, max_depth: int = 10
) -> Set[str]:
    """Explore the graph from a starting state using BFS.

    This is a simple utility for discovering states within a depth limit.
    Unlike full pathfinding, this just discovers what's reachable.

    Args:
        tracker: PathTracker with state graph
        start_state: Starting state name
        max_depth: Maximum exploration depth

    Returns:
        Set of discovered state names
    """
    discovered: Set[str] = set()
    queue = deque([(start_state, 0)])

    while queue:
        current, depth = queue.popleft()

        if current in discovered or depth >= max_depth:
            continue

        discovered.add(current)

        # Get transitions from tracker
        if hasattr(tracker.state_graph, "states"):
            state = tracker.state_graph.states.get(current)
            if state and hasattr(state, "transitions"):
                for transition in state.transitions:
                    to_state = getattr(transition, "to_state", None)
                    if to_state and to_state not in discovered:
                        queue.append((to_state, depth + 1))

    return discovered


def get_reachable_states(tracker: PathTracker, start_state: str) -> Set[str]:
    """Get all states reachable from a starting state.

    This explores the entire reachable graph without depth limit.

    Args:
        tracker: PathTracker with state graph
        start_state: Starting state name

    Returns:
        Set of reachable state names
    """
    return explore_graph(tracker, start_state, max_depth=sys.maxsize)


def analyze_graph_structure(tracker: PathTracker) -> Dict[str, Any]:
    """Analyze structural properties of the state graph.

    Args:
        tracker: PathTracker with state graph

    Returns:
        Dictionary with graph metrics
    """
    if not hasattr(tracker.state_graph, "states"):
        return {
            "num_states": 0,
            "num_transitions": 0,
            "avg_out_degree": 0,
            "max_out_degree": 0,
            "min_out_degree": 0,
        }

    states = tracker.state_graph.states
    num_states = len(states)
    num_transitions = 0
    out_degrees = []

    for state in states.values():
        if hasattr(state, "transitions"):
            degree = len(state.transitions)
            out_degrees.append(degree)
            num_transitions += degree

    return {
        "num_states": num_states,
        "num_transitions": num_transitions,
        "avg_out_degree": (sum(out_degrees) / len(out_degrees) if out_degrees else 0),
        "max_out_degree": max(out_degrees) if out_degrees else 0,
        "min_out_degree": min(out_degrees) if out_degrees else 0,
        "graph_density": (
            num_transitions / (num_states * (num_states - 1)) if num_states > 1 else 0
        ),
    }


def find_unreachable_states(tracker: PathTracker, start_state: str) -> Set[str]:
    """Find states that cannot be reached from the starting state.

    Args:
        tracker: PathTracker with state graph
        start_state: Starting state name

    Returns:
        Set of unreachable state names
    """
    if not hasattr(tracker.state_graph, "states"):
        return set()

    all_states = set(tracker.state_graph.states.keys())
    reachable = get_reachable_states(tracker, start_state)
    return all_states - reachable


def find_terminal_states(tracker: PathTracker) -> Set[str]:
    """Find states with no outgoing transitions (terminal/dead-end states).

    Args:
        tracker: PathTracker with state graph

    Returns:
        Set of terminal state names
    """
    if not hasattr(tracker.state_graph, "states"):
        return set()

    terminal = set()
    for state_name, state in tracker.state_graph.states.items():
        if not hasattr(state, "transitions") or not state.transitions:
            terminal.add(state_name)

    return terminal


def compute_shortest_distances(
    tracker: PathTracker, start_state: str
) -> Dict[str, int]:
    """Compute shortest distance (in transitions) from start to all reachable states.

    Uses BFS to find shortest paths.

    Args:
        tracker: PathTracker with state graph
        start_state: Starting state name

    Returns:
        Dictionary mapping state names to distances
    """
    distances: Dict[str, int] = {start_state: 0}
    queue = deque([(start_state, 0)])
    visited = {start_state}

    while queue:
        current, dist = queue.popleft()

        if hasattr(tracker.state_graph, "states"):
            state = tracker.state_graph.states.get(current)
            if state and hasattr(state, "transitions"):
                for transition in state.transitions:
                    to_state = getattr(transition, "to_state", None)
                    if to_state and to_state not in visited:
                        visited.add(to_state)
                        distances[to_state] = dist + 1
                        queue.append((to_state, dist + 1))

    return distances
