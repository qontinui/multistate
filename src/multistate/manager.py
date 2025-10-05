"""StateManager: High-level API for MultiState framework.

This provides the main user interface for working with multi-state systems.
It integrates states, transitions, execution, and pathfinding into a cohesive API.

Following the formal model from the paper:
- Manages state space Ω_MS = (E, S, G, T) 
- Maintains current configuration S_Ξ ⊆ S
- Provides pathfinding and execution capabilities
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable, Any
import logging
from enum import Enum

from multistate.core.state import State
from multistate.core.state_group import StateGroup
from multistate.core.element import Element
from multistate.transitions.transition import Transition
from multistate.transitions.executor import TransitionExecutor, SuccessPolicy
from multistate.transitions.callbacks import TransitionCallbacks
from multistate.pathfinding.multi_target import (
    MultiTargetPathFinder,
    SearchStrategy,
    Path
)


class StateManagerError(Exception):
    """Base exception for StateManager errors."""
    pass


class InvalidStateError(StateManagerError):
    """Raised when referencing non-existent states."""
    pass


class InvalidTransitionError(StateManagerError):
    """Raised when transition cannot be executed."""
    pass


@dataclass
class StateManagerConfig:
    """Configuration for StateManager."""
    
    # Execution settings
    allow_invalid_transitions: bool = False
    auto_rollback_on_failure: bool = True
    success_policy: SuccessPolicy = SuccessPolicy.STRICT
    
    # Pathfinding settings  
    default_search_strategy: SearchStrategy = SearchStrategy.DIJKSTRA
    max_path_depth: int = 100
    
    # Logging
    log_transitions: bool = True
    log_level: str = "INFO"


class StateManager:
    """High-level manager for multi-state systems.
    
    This is the main API users interact with. It provides:
    - State and transition registration
    - Current state management
    - Transition execution
    - Multi-target pathfinding
    - State queries and analysis
    
    Example:
        manager = StateManager()
        
        # Define states
        login = manager.add_state("login", "Login Screen")
        main_menu = manager.add_state("main_menu", "Main Menu")
        
        # Define transitions
        manager.add_transition(
            "login_success",
            from_states=["login"],
            activate_states=["main_menu"],
            exit_states=["login"]
        )
        
        # Execute transitions
        manager.execute_transition("login_success")
        
        # Find paths
        path = manager.find_path_to(["editor", "console"])
    """
    
    def __init__(self, config: Optional[StateManagerConfig] = None):
        """Initialize StateManager.
        
        Args:
            config: Configuration settings
        """
        self.config = config or StateManagerConfig()
        
        # Core data structures
        self.states: Dict[str, State] = {}
        self.groups: Dict[str, StateGroup] = {}
        self.transitions: Dict[str, Transition] = {}
        self.elements: Dict[str, Element] = {}
        
        # Current state (S_Ξ in formal model)
        self.active_states: Set[State] = set()
        
        # Components
        self.executor = TransitionExecutor()
        self.pathfinder: Optional[MultiTargetPathFinder] = None
        
        # Callbacks
        self.callbacks = TransitionCallbacks()
        
        # History
        self.transition_history: List[Tuple[str, bool, Dict[str, Any]]] = []  # (transition_id, success, metadata)
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, self.config.log_level))
    
    # ==================== State Management ====================
    
    def add_state(
        self,
        id: str,
        name: Optional[str] = None,
        elements: Optional[Set[str]] = None,
        group: Optional[str] = None,
        blocking: bool = False,
        blocks: Optional[Set[str]] = None
    ) -> State:
        """Add a state to the system.
        
        Args:
            id: Unique identifier
            name: Human-readable name
            elements: Element IDs in this state
            group: Group this state belongs to
            blocking: Whether this blocks other states
            blocks: Specific states this blocks
            
        Returns:
            Created State object
            
        Raises:
            StateManagerError: If state ID already exists
        """
        if id in self.states:
            raise StateManagerError(f"State '{id}' already exists")
        
        # Create element objects if needed
        element_objs = set()
        if elements:
            for elem_id in elements:
                if elem_id not in self.elements:
                    self.elements[elem_id] = Element(elem_id, elem_id)
                element_objs.add(self.elements[elem_id])
        
        # Create state
        state = State(
            id=id,
            name=name or id,
            elements=element_objs,
            group=group,
            blocking=blocking,
            blocks=blocks or set()
        )
        
        self.states[id] = state
        
        # Add to group if specified
        if group:
            if group not in self.groups:
                self.groups[group] = StateGroup(group, group)
            self.groups[group].states.add(state)
        
        self.logger.info(f"Added state: {id}")
        return state
    
    def get_state(self, id: str) -> State:
        """Get state by ID.
        
        Raises:
            InvalidStateError: If state doesn't exist
        """
        if id not in self.states:
            raise InvalidStateError(f"State '{id}' not found")
        return self.states[id]
    
    def activate_states(self, state_ids: Set[str]):
        """Directly activate states (bypassing transitions).
        
        This is like Brobot's state memory population.
        
        Args:
            state_ids: States to activate
            
        Raises:
            InvalidStateError: If any state doesn't exist
        """
        states = {self.get_state(sid) for sid in state_ids}
        
        # Check blocking
        for state in states:
            if state.blocking:
                # Clear other states except those in same group
                to_clear = self.active_states.copy()
                if state.group:
                    group_states = self.groups[state.group].states
                    to_clear -= group_states
                self.active_states = self.active_states.intersection(group_states) if state.group else set()
        
        self.active_states.update(states)
        self.logger.info(f"Activated states: {state_ids}")
    
    def deactivate_states(self, state_ids: Set[str]):
        """Directly deactivate states.
        
        Args:
            state_ids: States to deactivate
        """
        states = {self.get_state(sid) for sid in state_ids}
        self.active_states.difference_update(states)
        self.logger.info(f"Deactivated states: {state_ids}")
    
    def get_active_states(self) -> Set[str]:
        """Get currently active state IDs."""
        return {s.id for s in self.active_states}
    
    def is_active(self, state_id: str) -> bool:
        """Check if state is active."""
        state = self.get_state(state_id)
        return state in self.active_states
    
    # ==================== Transition Management ====================
    
    def add_transition(
        self,
        id: str,
        name: Optional[str] = None,
        from_states: Optional[List[str]] = None,
        activate_states: Optional[List[str]] = None,
        exit_states: Optional[List[str]] = None,
        activate_groups: Optional[List[str]] = None,
        exit_groups: Optional[List[str]] = None,
        path_cost: float = 1.0,
        success_policy: Optional[SuccessPolicy] = None,
        outgoing_callback: Optional[Callable] = None,
        incoming_callbacks: Optional[Dict[str, Callable]] = None
    ) -> Transition:
        """Add a transition to the system.
        
        Args:
            id: Unique identifier
            name: Human-readable name
            from_states: Required active state IDs
            activate_states: States to activate
            exit_states: States to exit
            activate_groups: Groups to activate
            exit_groups: Groups to exit
            path_cost: Cost for pathfinding
            success_policy: How to handle multi-state success
            outgoing_callback: Function to call during transition
            incoming_callbacks: Per-state initialization callbacks
            
        Returns:
            Created Transition object
            
        Raises:
            StateManagerError: If transition ID exists or states invalid
        """
        if id in self.transitions:
            raise StateManagerError(f"Transition '{id}' already exists")
        
        # Convert IDs to objects
        from_objs = {self.get_state(s) for s in (from_states or [])}
        activate_objs = {self.get_state(s) for s in (activate_states or [])}
        exit_objs = {self.get_state(s) for s in (exit_states or [])}
        
        activate_group_objs = {self.groups[g] for g in (activate_groups or []) if g in self.groups}
        exit_group_objs = {self.groups[g] for g in (exit_groups or []) if g in self.groups}
        
        # Create transition
        transition = Transition(
            id=id,
            name=name or id,
            from_states=from_objs,
            activate_states=activate_objs,
            exit_states=exit_objs,
            activate_groups=activate_group_objs,
            exit_groups=exit_group_objs,
            path_cost=path_cost
        )
        
        # Register callbacks
        if outgoing_callback:
            self.callbacks.register_outgoing(id, outgoing_callback)
        
        if incoming_callbacks:
            for state_id, callback in incoming_callbacks.items():
                self.callbacks.register_incoming(id, state_id, callback)
        
        self.transitions[id] = transition
        
        # Rebuild pathfinder with new transition
        self._rebuild_pathfinder()
        
        self.logger.info(f"Added transition: {id}")
        return transition
    
    def get_transition(self, id: str) -> Transition:
        """Get transition by ID.
        
        Raises:
            InvalidTransitionError: If transition doesn't exist
        """
        if id not in self.transitions:
            raise InvalidTransitionError(f"Transition '{id}' not found")
        return self.transitions[id]
    
    # ==================== Execution ====================
    
    def can_execute(self, transition_id: str) -> bool:
        """Check if transition can execute from current state.
        
        Args:
            transition_id: Transition to check
            
        Returns:
            True if transition can execute
        """
        transition = self.get_transition(transition_id)
        return self.executor.can_execute(transition, self.active_states)
    
    def execute_transition(self, transition_id: str) -> bool:
        """Execute a transition.

        Args:
            transition_id: Transition to execute

        Returns:
            True if successful

        Raises:
            InvalidTransitionError: If transition cannot execute
        """
        transition = self.get_transition(transition_id)

        # Check if can execute
        if not self.config.allow_invalid_transitions:
            if not self.can_execute(transition_id):
                raise InvalidTransitionError(
                    f"Cannot execute '{transition_id}' from current state"
                )

        # Execute with callbacks
        initial_states = self.active_states.copy()

        result = self.executor.execute(
            transition,
            self.active_states,
            self.callbacks
        )

        # Update active states if successful
        if result.success:
            self.active_states = self.executor.get_result_states(
                transition,
                initial_states
            )

            # Log detailed phase information
            if self.config.log_transitions:
                self.logger.info(f"Transition '{transition_id}' succeeded")
                for phase_result in result.phase_results:
                    self.logger.debug(
                        f"  {phase_result.phase.value}: "
                        f"{'✓' if phase_result.success else '✗'} {phase_result.message}"
                    )
        else:
            # Log failure information
            failed_phase = result.get_failed_phase()
            if self.config.log_transitions:
                self.logger.warning(
                    f"Transition '{transition_id}' failed at phase: "
                    f"{failed_phase.value if failed_phase else 'unknown'}"
                )

            if self.config.auto_rollback_on_failure:
                # Rollback to initial state
                self.active_states = initial_states
                self.logger.debug(f"Rolled back to initial state")

        # Log history with additional metadata
        self.transition_history.append((
            transition_id,
            result.success,
            {
                'failed_phase': result.get_failed_phase().value if result.get_failed_phase() else None,
                'activated': len(result.activated_states),
                'deactivated': len(result.deactivated_states),
                'error': str(result.error) if result.error else None
            }
        ))

        return result.success
    
    def execute_sequence(self, transition_ids: List[str]) -> bool:
        """Execute a sequence of transitions.
        
        Stops on first failure.
        
        Args:
            transition_ids: Transitions to execute in order
            
        Returns:
            True if all succeeded
        """
        for tid in transition_ids:
            if not self.execute_transition(tid):
                return False
        return True
    
    # ==================== Pathfinding ====================
    
    def _rebuild_pathfinder(self):
        """Rebuild pathfinder with current transitions."""
        if self.transitions:
            self.pathfinder = MultiTargetPathFinder(
                list(self.transitions.values()),
                self.config.default_search_strategy
            )
    
    def find_path_to(
        self,
        target_state_ids: List[str],
        from_states: Optional[Set[str]] = None,
        strategy: Optional[SearchStrategy] = None
    ) -> Optional[Path]:
        """Find path to reach ALL target states.
        
        Args:
            target_state_ids: States that must ALL be reached
            from_states: Starting states (default: current)
            strategy: Search strategy (default: config)
            
        Returns:
            Path to reach all targets, or None if impossible
        """
        if not self.pathfinder:
            self._rebuild_pathfinder()
        
        if not self.pathfinder:
            return None
        
        # Convert IDs to states
        targets = {self.get_state(sid) for sid in target_state_ids}
        
        if from_states is None:
            current = self.active_states
        else:
            current = {self.get_state(sid) for sid in from_states}
        
        # Use different strategy if specified
        if strategy and strategy != self.config.default_search_strategy:
            pathfinder = MultiTargetPathFinder(
                list(self.transitions.values()),
                strategy
            )
        else:
            pathfinder = self.pathfinder
        
        path = pathfinder.find_path_to_all(current, targets)
        
        if path and self.config.log_transitions:
            self.logger.info(
                f"Found path to {target_state_ids}: "
                f"{len(path.transitions_sequence)} steps, cost={path.total_cost}"
            )
        
        return path
    
    def execute_path(self, path: Path) -> bool:
        """Execute a path found by pathfinding.
        
        Args:
            path: Path to execute
            
        Returns:
            True if all transitions succeeded
        """
        for transition in path.transitions_sequence:
            if not self.execute_transition(transition.id):
                return False
        return True
    
    def navigate_to(
        self,
        target_state_ids: List[str],
        strategy: Optional[SearchStrategy] = None
    ) -> bool:
        """Find and execute path to targets.
        
        Convenience method combining pathfinding and execution.
        
        Args:
            target_state_ids: States to reach
            strategy: Search strategy
            
        Returns:
            True if successfully navigated to all targets
        """
        path = self.find_path_to(target_state_ids, strategy=strategy)
        if not path:
            self.logger.warning(f"No path found to {target_state_ids}")
            return False
        
        return self.execute_path(path)
    
    # ==================== Analysis ====================
    
    def get_available_transitions(self) -> List[str]:
        """Get transitions that can execute from current state.
        
        Returns:
            List of transition IDs
        """
        available = []
        for tid, transition in self.transitions.items():
            if self.can_execute(tid):
                available.append(tid)
        return available
    
    def get_reachable_states(self, max_depth: Optional[int] = None) -> Set[str]:
        """Get all states reachable from current configuration.
        
        Args:
            max_depth: Maximum transitions to explore
            
        Returns:
            Set of reachable state IDs
        """
        if not self.pathfinder:
            self._rebuild_pathfinder()
        
        if not self.pathfinder:
            return set()
        
        max_depth = max_depth or self.config.max_path_depth
        
        # Use BFS to explore reachable states
        reachable = set()
        visited = set()
        queue = [(self.active_states, 0)]
        
        while queue:
            states, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            state_tuple = tuple(sorted(s.id for s in states))
            if state_tuple in visited:
                continue
            visited.add(state_tuple)
            
            reachable.update(s.id for s in states)
            
            # Get available transitions
            for transition in self.transitions.values():
                if self.executor.can_execute(transition, states):
                    new_states = self.executor.get_result_states(transition, states)
                    queue.append((new_states, depth + 1))
        
        return reachable
    
    def analyze_complexity(self) -> Dict[str, Any]:
        """Analyze complexity of current state space.
        
        Returns:
            Complexity metrics
        """
        return {
            "num_states": len(self.states),
            "num_transitions": len(self.transitions),
            "num_groups": len(self.groups),
            "active_states": len(self.active_states),
            "available_transitions": len(self.get_available_transitions()),
            "reachable_states": len(self.get_reachable_states()),
            "max_group_size": max(
                (len(g.states) for g in self.groups.values()),
                default=0
            ),
            "transition_density": (
                len(self.transitions) / (len(self.states) ** 2)
                if self.states else 0
            )
        }
    
    def get_state_info(self) -> str:
        """Get human-readable state information.
        
        Returns:
            Formatted string with state info
        """
        lines = []
        lines.append("=" * 60)
        lines.append("STATE MANAGER STATUS")
        lines.append("=" * 60)
        
        # Active states
        lines.append("\nActive States:")
        if self.active_states:
            for state in sorted(self.active_states, key=lambda s: s.id):
                marker = "[B]" if state.blocking else ""
                lines.append(f"  - {state.name} ({state.id}) {marker}")
        else:
            lines.append("  (none)")
        
        # Available transitions
        lines.append("\nAvailable Transitions:")
        available = self.get_available_transitions()
        if available:
            for tid in sorted(available):
                trans = self.transitions[tid]
                lines.append(f"  - {trans.name} ({tid})")
        else:
            lines.append("  (none)")
        
        # Groups
        if self.groups:
            lines.append("\nState Groups:")
            for gid, group in sorted(self.groups.items()):
                active_count = sum(1 for s in group.states if s in self.active_states)
                lines.append(f"  - {group.name}: {active_count}/{len(group.states)} active")
        
        # Statistics
        lines.append("\nStatistics:")
        stats = self.analyze_complexity()
        lines.append(f"  Total States: {stats['num_states']}")
        lines.append(f"  Total Transitions: {stats['num_transitions']}")
        lines.append(f"  Reachable States: {stats['reachable_states']}")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"StateManager("
            f"states={len(self.states)}, "
            f"transitions={len(self.transitions)}, "
            f"active={len(self.active_states)}"
            f")"
        )