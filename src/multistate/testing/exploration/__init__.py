"""Exploration strategies for intelligent path traversal.

This package provides various exploration strategies for systematically
discovering and testing state transitions in state machines.
"""

from multistate.testing.exploration.backtracking import BacktrackingNavigator
from multistate.testing.exploration.diversity import PathDiversityEngine
from multistate.testing.exploration.failure_handler import FailureAwareExplorer
from multistate.testing.exploration.graph_utils import (
    analyze_graph_structure,
    compute_shortest_distances,
    explore_graph,
    find_terminal_states,
    find_unreachable_states,
    get_reachable_states,
)
from multistate.testing.exploration.path_explorer import PathExplorer
from multistate.testing.exploration.strategies import (
    AdaptiveExplorer,
    BreadthFirstExplorer,
    DepthFirstExplorer,
    ExplorationStrategy,
    GreedyCoverageExplorer,
    HybridExplorer,
    NoveltySeekingExplorer,
    RandomWalkExplorer,
)

__all__ = [
    "PathExplorer",
    "ExplorationStrategy",
    "RandomWalkExplorer",
    "GreedyCoverageExplorer",
    "DepthFirstExplorer",
    "BreadthFirstExplorer",
    "AdaptiveExplorer",
    "HybridExplorer",
    "NoveltySeekingExplorer",
    "BacktrackingNavigator",
    "PathDiversityEngine",
    "FailureAwareExplorer",
    "explore_graph",
    "get_reachable_states",
    "analyze_graph_structure",
    "find_unreachable_states",
    "find_terminal_states",
    "compute_shortest_distances",
]
