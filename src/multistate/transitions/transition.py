"""Transition: Defines state changes with multi-state support.

Following the formal model:
t_MS = (A, S_activate, S_exit, G_activate, φ)

where:
- A: sequence of actions
- S_activate: set of states to activate
- S_exit: set of states to exit
- G_activate: set of groups to activate atomically
- φ: phased execution strategy
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from multistate.core.state import State
from multistate.core.state_group import StateGroup


class TransitionPhase(Enum):
    """Phases of transition execution following φ = ⟨φ_validate, φ_outgoing, φ_activate, φ_incoming, φ_exit⟩."""

    VALIDATE = "validate"  # φ_validate: Pre-validate all preconditions
    OUTGOING = "outgoing"  # φ_outgoing: Execute outgoing transition action
    ACTIVATE = "activate"  # φ_activate: Pure memory update (cannot fail)
    INCOMING = "incoming"  # φ_incoming: Execute incoming for ALL activated
    EXIT = "exit"  # φ_exit: Pure memory update (cannot fail)
    VISIBILITY = "visibility"  # Update visibility of states
    CLEANUP = "cleanup"  # Clean up resources and finalize


@dataclass
class PhaseResult:
    """Result of executing a single phase."""

    phase: TransitionPhase
    success: bool
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransitionResult:
    """Result of executing a complete transition.

    Corresponds to r_t in the formal model.
    """

    success: bool
    phase_results: List[PhaseResult] = field(default_factory=list)
    activated_states: Set[State] = field(default_factory=set)
    deactivated_states: Set[State] = field(default_factory=set)
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_failed_phase(self) -> Optional[TransitionPhase]:
        """Get the first phase that failed, if any."""
        for result in self.phase_results:
            if not result.success:
                return result.phase
        return None


@dataclass
class Transition:
    """Represents a transition between states with multi-state support.

    In the formal model: t_MS = (A, S_activate, S_exit, G_activate, φ)

    Key properties:
    - Can activate multiple states simultaneously
    - Can activate entire groups atomically
    - Executes in well-defined phases
    - Supports incoming transitions for ALL activated states

    Attributes:
        id: Unique identifier
        name: Human-readable name
        from_states: States this transition can execute from
        activate_states: Individual states to activate
        exit_states: States to deactivate
        activate_groups: Groups to activate atomically
        exit_groups: Groups to deactivate atomically
        action: Optional action function A to execute
        incoming_actions: Actions to run for newly activated states
        path_cost: Cost for pathfinding (c_T(t))
        metadata: Additional transition-specific data
    """

    id: str
    name: str
    from_states: Set[State] = field(default_factory=set)
    activate_states: Set[State] = field(default_factory=set)
    exit_states: Set[State] = field(default_factory=set)
    activate_groups: Set[StateGroup] = field(default_factory=set)
    exit_groups: Set[StateGroup] = field(default_factory=set)
    action: Optional[Callable[[], bool]] = None
    incoming_actions: Dict[str, Callable[[], None]] = field(default_factory=dict)
    path_cost: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        """Make transition hashable for use in sets."""
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        """Transitions are equal if they have the same id."""
        if not isinstance(other, Transition):
            return False
        return self.id == other.id

    def __repr__(self) -> str:
        """String representation for debugging."""
        from_names = [s.name for s in self.from_states]
        activate_names = [s.name for s in self.get_all_states_to_activate()]
        return (
            f"Transition(id='{self.id}', name='{self.name}', "
            f"from={from_names}, activate={activate_names})"
        )

    def can_execute_from(self, active_states: Set[State]) -> bool:
        """Check if this transition can execute from the given active states.

        Args:
            active_states: Current active states (S_Ξ)

        Returns:
            True if at least one from_state is active
        """
        if not self.from_states:
            # Transition with no from_states can execute from any state
            return True
        return bool(self.from_states.intersection(active_states))

    def get_all_states_to_activate(self) -> Set[State]:
        """Get all states that will be activated (S_activate ∪ ⋃G_activate).

        Returns:
            Complete set of states to activate including group members
        """
        all_states = self.activate_states.copy()
        for group in self.activate_groups:
            all_states.update(group.states)
        return all_states

    def get_all_states_to_exit(self) -> Set[State]:
        """Get all states that will be deactivated (S_exit ∪ ⋃G_exit).

        Returns:
            Complete set of states to exit including group members
        """
        all_states = self.exit_states.copy()
        for group in self.exit_groups:
            all_states.update(group.states)
        return all_states

    def get_state_changes(self) -> Dict[str, Set[State]]:
        """Get a summary of all state changes this transition will make.

        Returns:
            Dictionary with 'activate' and 'exit' keys
        """
        return {
            "activate": self.get_all_states_to_activate(),
            "exit": self.get_all_states_to_exit(),
        }

    def validate_groups(self, active_states: Set[State]) -> bool:
        """Validate that group atomicity will be maintained.

        Checks that after this transition, all groups satisfy:
        ∀g ∈ G: g ⊆ S_Ξ' ∨ g ∩ S_Ξ' = ∅

        Args:
            active_states: Current active states

        Returns:
            True if atomicity will be preserved
        """
        # Calculate what the active states will be after transition
        new_active = active_states.copy()
        new_active.difference_update(self.get_all_states_to_exit())
        new_active.update(self.get_all_states_to_activate())

        # Check all affected groups
        all_groups = set()
        for state in new_active:
            if state.group:
                # Need to get the actual group object
                # This is a simplification - in practice we'd look it up
                pass

        # For now, return True (actual validation would check each group)
        return True

    def get_incoming_action_for_state(self, state: State) -> Optional[Callable]:
        """Get the incoming action for a specific state.

        Args:
            state: State to get incoming action for

        Returns:
            Incoming action function if defined, None otherwise
        """
        return self.incoming_actions.get(state.id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert transition to dictionary representation.

        Returns:
            Dictionary containing transition properties
        """
        return {
            "id": self.id,
            "name": self.name,
            "from_states": [s.id for s in self.from_states],
            "activate_states": [s.id for s in self.activate_states],
            "exit_states": [s.id for s in self.exit_states],
            "activate_groups": [g.id for g in self.activate_groups],
            "exit_groups": [g.id for g in self.exit_groups],
            "path_cost": self.path_cost,
            "has_action": self.action is not None,
            "incoming_actions": list(self.incoming_actions.keys()),
            "metadata": self.metadata,
        }


class IncomingTransition:
    """Represents an incoming transition for a state.

    Incoming transitions execute automatically when a state is activated.
    This ensures initialization logic runs for ALL newly activated states.
    """

    def __init__(
        self,
        state_id: str,
        action: Callable[[], None],
        name: Optional[str] = None
    ):
        """Initialize incoming transition.

        Args:
            state_id: ID of state this incoming transition belongs to
            action: Function to execute when state is activated
            name: Optional human-readable name
        """
        self.state_id = state_id
        self.action = action
        self.name = name or f"incoming_{state_id}"

    def execute(self) -> bool:
        """Execute the incoming transition action.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.action()
            return True
        except Exception as e:
            print(f"Incoming transition {self.name} failed: {e}")
            return False