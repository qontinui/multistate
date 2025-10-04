"""Multi-target pathfinding algorithm for MultiState.

This implements the core algorithmic innovation: finding paths that reach
ALL target states, not just one.

Following the formal model:
- ρ_MT = (S_ρ, T_ρ, S_targets) where S_targets ⊆ S
- valid(ρ_MT) ⟺ S_targets ⊆ ⋃_{i=0}^n {s_i}

The path must visit ALL target states to be valid.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from collections import deque
import heapq

from multistate.core.state import State
from multistate.transitions.transition import Transition


class SearchStrategy(Enum):
    """Strategy for multi-target pathfinding."""

    BFS = "bfs"  # Breadth-first search (optimal for unweighted)
    DIJKSTRA = "dijkstra"  # Consider path costs
    A_STAR = "astar"  # Use heuristic for remaining targets


@dataclass
class PathNode:
    """Node in the search tree for multi-target pathfinding.

    Key insight: We need to track not just current states, but
    which targets we've already reached.
    """

    active_states: Set[State]
    targets_reached: Set[State]
    transition_taken: Optional[Transition] = None
    parent: Optional['PathNode'] = None
    cost: float = 0.0
    depth: int = 0

    def __hash__(self) -> int:
        """Hash based on active states and targets reached."""
        # Create a hashable representation
        active_ids = tuple(sorted(s.id for s in self.active_states))
        target_ids = tuple(sorted(s.id for s in self.targets_reached))
        return hash((active_ids, target_ids))

    def __eq__(self, other) -> bool:
        """Nodes are equal if same active states and same targets reached."""
        if not isinstance(other, PathNode):
            return False
        return (self.active_states == other.active_states and
                self.targets_reached == other.targets_reached)

    def __lt__(self, other) -> bool:
        """For priority queue ordering."""
        return self.cost < other.cost


@dataclass
class Path:
    """Represents a path through the state space reaching all targets.

    In the formal model: ρ_MT = (S_ρ, T_ρ, S_targets)
    """

    states_sequence: List[Set[State]] = field(default_factory=list)
    transitions_sequence: List[Transition] = field(default_factory=list)
    targets: Set[State] = field(default_factory=set)
    total_cost: float = 0.0

    def is_complete(self) -> bool:
        """Check if path reaches all targets."""
        states_visited = set()
        for state_set in self.states_sequence:
            states_visited.update(state_set)
        return self.targets.issubset(states_visited)

    def __repr__(self) -> str:
        """String representation."""
        path_str = " -> ".join(
            f"[{', '.join(s.name for s in states)}]"
            for states in self.states_sequence
        )
        return f"Path({len(self.transitions_sequence)} steps): {path_str}"


class MultiTargetPathFinder:
    """Finds paths that reach ALL target states.

    This is the key algorithmic innovation of MultiState:
    instead of finding a path to ONE target, we find paths
    that reach ALL targets.

    The challenge: With k targets, we have 2^k possible
    "progress states" (which targets have been reached).
    """

    def __init__(
        self,
        transitions: List[Transition],
        strategy: SearchStrategy = SearchStrategy.BFS
    ):
        """Initialize pathfinder with available transitions.

        Args:
            transitions: All transitions in the system
            strategy: Search strategy to use
        """
        self.transitions = transitions
        self.strategy = strategy

        # Build transition graph for efficient lookup
        self.transitions_from_state: Dict[str, List[Transition]] = {}
        self._build_transition_graph()

    def _build_transition_graph(self):
        """Build lookup structure for transitions."""
        for transition in self.transitions:
            # Transitions can execute from any of their from_states
            for state in transition.from_states:
                if state.id not in self.transitions_from_state:
                    self.transitions_from_state[state.id] = []
                self.transitions_from_state[state.id].append(transition)

            # Transitions with no from_states can execute from anywhere
            if not transition.from_states:
                if "*" not in self.transitions_from_state:
                    self.transitions_from_state["*"] = []
                self.transitions_from_state["*"].append(transition)

    def find_path_to_all(
        self,
        current_states: Set[State],
        target_states: Set[State]
    ) -> Optional[Path]:
        """Find shortest path that reaches ALL target states.

        This implements the formal pathfinding function:
        f_pathfind_MT: (Ω_MS, S_Ξ, S_targets) → P(ρ_MT)

        Args:
            current_states: Starting active states (S_Ξ)
            target_states: ALL states that must be reached (S_targets)

        Returns:
            Path that visits all targets, or None if impossible
        """
        if not target_states:
            # No targets = already done
            return Path(states_sequence=[current_states], targets=target_states)

        # Check if we already have all targets
        if target_states.issubset(current_states):
            return Path(
                states_sequence=[current_states],
                targets=target_states,
                total_cost=0
            )

        if self.strategy == SearchStrategy.BFS:
            return self._bfs_search(current_states, target_states)
        elif self.strategy == SearchStrategy.DIJKSTRA:
            return self._dijkstra_search(current_states, target_states)
        elif self.strategy == SearchStrategy.A_STAR:
            return self._astar_search(current_states, target_states)

        return None

    def _bfs_search(
        self,
        current_states: Set[State],
        target_states: Set[State]
    ) -> Optional[Path]:
        """BFS implementation for multi-target pathfinding.

        Key insight: We need to track (active_states, targets_reached)
        as our search state, not just active_states.
        """
        # Initial node
        targets_in_current = target_states.intersection(current_states)
        start_node = PathNode(
            active_states=current_states,
            targets_reached=targets_in_current
        )

        # BFS queue
        queue = deque([start_node])
        visited = {start_node}

        while queue:
            node = queue.popleft()

            # Check if we've reached all targets
            if node.targets_reached == target_states:
                return self._reconstruct_path(node, target_states)

            # Get available transitions
            for transition in self._get_available_transitions(node.active_states):
                # Simulate transition execution
                new_states = self._apply_transition(
                    node.active_states,
                    transition
                )

                # Calculate newly reached targets
                new_targets_reached = node.targets_reached.union(
                    target_states.intersection(new_states)
                )

                # Create new node
                new_node = PathNode(
                    active_states=new_states,
                    targets_reached=new_targets_reached,
                    transition_taken=transition,
                    parent=node,
                    cost=node.cost + transition.path_cost,
                    depth=node.depth + 1
                )

                # Only explore if not visited
                if new_node not in visited:
                    visited.add(new_node)
                    queue.append(new_node)

        # No path found
        return None

    def _dijkstra_search(
        self,
        current_states: Set[State],
        target_states: Set[State]
    ) -> Optional[Path]:
        """Dijkstra's algorithm for multi-target pathfinding.

        Considers transition costs to find optimal path.
        """
        # Initial node
        targets_in_current = target_states.intersection(current_states)
        start_node = PathNode(
            active_states=current_states,
            targets_reached=targets_in_current,
            cost=0
        )

        # Priority queue (cost, node)
        heap = [(0, start_node)]
        visited = set()
        best_costs = {start_node: 0}

        while heap:
            current_cost, node = heapq.heappop(heap)

            # Skip if we've seen this state with lower cost
            if node in visited:
                continue
            visited.add(node)

            # Check if we've reached all targets
            if node.targets_reached == target_states:
                return self._reconstruct_path(node, target_states)

            # Explore transitions
            for transition in self._get_available_transitions(node.active_states):
                new_states = self._apply_transition(
                    node.active_states,
                    transition
                )

                new_targets_reached = node.targets_reached.union(
                    target_states.intersection(new_states)
                )

                new_cost = node.cost + transition.path_cost

                new_node = PathNode(
                    active_states=new_states,
                    targets_reached=new_targets_reached,
                    transition_taken=transition,
                    parent=node,
                    cost=new_cost,
                    depth=node.depth + 1
                )

                # Only explore if better cost
                if new_node not in visited:
                    if new_node not in best_costs or new_cost < best_costs[new_node]:
                        best_costs[new_node] = new_cost
                        heapq.heappush(heap, (new_cost, new_node))

        return None

    def _astar_search(
        self,
        current_states: Set[State],
        target_states: Set[State]
    ) -> Optional[Path]:
        """A* search with heuristic for remaining targets.

        Heuristic: Minimum cost to reach remaining targets
        (admissible but not very tight).
        """
        # Initial node
        targets_in_current = target_states.intersection(current_states)
        start_node = PathNode(
            active_states=current_states,
            targets_reached=targets_in_current,
            cost=0
        )

        # Priority queue (f_score, node)
        # f = g + h where g is cost so far, h is heuristic
        h_score = self._heuristic(start_node, target_states)
        heap = [(h_score, start_node)]
        visited = set()
        g_scores = {start_node: 0}

        while heap:
            _, node = heapq.heappop(heap)

            if node in visited:
                continue
            visited.add(node)

            # Check if we've reached all targets
            if node.targets_reached == target_states:
                return self._reconstruct_path(node, target_states)

            # Explore transitions
            for transition in self._get_available_transitions(node.active_states):
                new_states = self._apply_transition(
                    node.active_states,
                    transition
                )

                new_targets_reached = node.targets_reached.union(
                    target_states.intersection(new_states)
                )

                g_score = node.cost + transition.path_cost

                new_node = PathNode(
                    active_states=new_states,
                    targets_reached=new_targets_reached,
                    transition_taken=transition,
                    parent=node,
                    cost=g_score,
                    depth=node.depth + 1
                )

                if new_node not in visited:
                    if new_node not in g_scores or g_score < g_scores[new_node]:
                        g_scores[new_node] = g_score
                        h_score = self._heuristic(new_node, target_states)
                        f_score = g_score + h_score
                        heapq.heappush(heap, (f_score, new_node))

        return None

    def _heuristic(self, node: PathNode, target_states: Set[State]) -> float:
        """Heuristic for A* search.

        Estimates minimum cost to reach remaining targets.
        This is a simple admissible heuristic.
        """
        remaining_targets = target_states - node.targets_reached
        if not remaining_targets:
            return 0

        # Simple heuristic: number of remaining targets
        # (assumes minimum cost of 1 per target)
        return len(remaining_targets)

    def _get_available_transitions(
        self,
        active_states: Set[State]
    ) -> List[Transition]:
        """Get all transitions that can execute from current states."""
        available = []

        # Check transitions from each active state
        for state in active_states:
            if state.id in self.transitions_from_state:
                for transition in self.transitions_from_state[state.id]:
                    if transition not in available:
                        available.append(transition)

        # Add transitions with no from_states (can execute from anywhere)
        if "*" in self.transitions_from_state:
            for transition in self.transitions_from_state["*"]:
                if transition not in available:
                    available.append(transition)

        return available

    def _apply_transition(
        self,
        current_states: Set[State],
        transition: Transition
    ) -> Set[State]:
        """Simulate applying a transition to get new active states."""
        new_states = current_states.copy()

        # Remove exiting states
        new_states.difference_update(transition.get_all_states_to_exit())

        # Add activating states
        new_states.update(transition.get_all_states_to_activate())

        return new_states

    def _reconstruct_path(
        self,
        end_node: PathNode,
        target_states: Set[State]
    ) -> Path:
        """Reconstruct path from search tree."""
        path = Path(targets=target_states)

        # Walk backwards from end to start
        nodes = []
        current = end_node
        while current is not None:
            nodes.append(current)
            current = current.parent

        # Reverse to get forward path
        nodes.reverse()

        # Build path
        for node in nodes:
            path.states_sequence.append(node.active_states)
            if node.transition_taken:
                path.transitions_sequence.append(node.transition_taken)

        path.total_cost = end_node.cost

        return path

    def analyze_complexity(
        self,
        num_states: int,
        num_targets: int
    ) -> Dict[str, any]:
        """Analyze algorithmic complexity for given parameters.

        Returns complexity metrics for paper.
        """
        # State space size
        total_state_configs = 2 ** num_states  # Each state active or not

        # Progress tracking adds another dimension
        target_progress_configs = 2 ** num_targets  # Each target reached or not

        # Total search space
        search_space = total_state_configs * target_progress_configs

        return {
            "state_configurations": total_state_configs,
            "target_progress_configurations": target_progress_configs,
            "total_search_space": search_space,
            "complexity_class": f"O(V * 2^k) where V={num_states}, k={num_targets}",
            "comparison_to_single": f"Single target: O(V), Multi: O(V * 2^{num_targets})",
            "exponential_in_targets": True
        }