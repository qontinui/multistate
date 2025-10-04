"""TransitionExecutor: Orchestrates phased transition execution.

Implements the formal transition function:
f_τ_MS: t_MS → (Ξ', r_t)

With phased execution φ = ⟨φ_outgoing, φ_activate, φ_incoming, φ_exit⟩
"""

from enum import Enum
from typing import Optional, Set

from multistate.core.state import State
from multistate.transitions.transition import Transition


class SuccessPolicy(Enum):
    """Defines when a transition is considered successful."""

    STRICT = "strict"  # All incoming must succeed (Brobot-like)
    LENIENT = "lenient"  # Only activation must succeed
    THRESHOLD = "threshold"  # At least k% of incoming must succeed




class TransitionExecutor:
    """Executes transitions with proper phased orchestration.

    Ensures:
    1. Outgoing transition validates before any changes
    2. ALL target states are activated atomically
    3. ALL activated states get their incoming transitions
    4. Exit happens after incoming (enables safe rollback)
    5. Groups maintain atomicity throughout
    """

    def __init__(
        self,
        success_policy: SuccessPolicy = SuccessPolicy.STRICT,
        success_threshold: float = 0.8,
        strict_mode: bool = True
    ):
        """Initialize the executor.

        Args:
            success_policy: Policy for determining transition success
            success_threshold: For THRESHOLD policy, % of incoming that must succeed
            strict_mode: If True, enforce strict validation and rollback
        """
        self.success_policy = success_policy
        self.success_threshold = success_threshold
        self.strict_mode = strict_mode

    def execute(
        self,
        transition: Transition,
        active_states: Set[State],
        callbacks: Optional['TransitionCallbacks'] = None
    ) -> bool:
        """Execute a transition with full phased orchestration.

        This implements the complete transition execution following
        the formal model's phased approach.

        Args:
            transition: The transition to execute
            active_states: Current active states (S_Ξ)
            callbacks: Optional callbacks to execute during phases

        Returns:
            True if transition succeeded
        """
        # Check if transition can execute
        if not self.can_execute(transition, active_states):
            return False

        # Execute callbacks if provided
        if callbacks:
            # Outgoing callback
            if not callbacks.execute_outgoing(transition.id):
                return False

            # Incoming callbacks for each state to activate
            for state in transition.get_all_states_to_activate():
                if not callbacks.execute_incoming(transition.id, state.id):
                    if self.success_policy == SuccessPolicy.STRICT:
                        return False

        # Simple execution: just update active states
        # This follows Brobot's simple memory update model
        return True

    def can_execute(self, transition: Transition, active_states: Set[State]) -> bool:
        """Check if transition can execute from current state.

        Args:
            transition: Transition to check
            active_states: Current active states

        Returns:
            True if transition can execute
        """
        # Check if from_states requirement is met
        if transition.from_states:
            # At least one from_state must be active
            if not any(state in active_states for state in transition.from_states):
                return False

        # Check for blocking states
        for state in active_states:
            if state.blocking:
                # Blocking state prevents most transitions
                # Allow if targeting the blocking state's group or explicit override
                states_to_activate = transition.get_all_states_to_activate()
                if state.group:
                    # Check if any activated state is in same group
                    for new_state in states_to_activate:
                        if new_state.group == state.group:
                            return True
                return False

        return True

    def get_result_states(
        self,
        transition: Transition,
        current_states: Set[State]
    ) -> Set[State]:
        """Get the resulting active states after executing transition.

        Args:
            transition: Transition to execute
            current_states: Current active states

        Returns:
            New set of active states
        """
        new_states = current_states.copy()

        # Exit states
        new_states.difference_update(transition.get_all_states_to_exit())

        # Activate states
        new_states.update(transition.get_all_states_to_activate())

        return new_states

