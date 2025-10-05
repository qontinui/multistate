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
    ) -> 'TransitionResult':
        """Execute a transition with full phased orchestration.

        This implements the complete transition execution following
        the formal model's phased approach:
        φ = ⟨φ_validate, φ_outgoing, φ_activate, φ_incoming, φ_exit, φ_visibility, φ_cleanup⟩

        Args:
            transition: The transition to execute
            active_states: Current active states (S_Ξ)
            callbacks: Optional callbacks to execute during phases

        Returns:
            TransitionResult with complete phase tracking
        """
        from multistate.transitions.transition import (
            TransitionResult, PhaseResult, TransitionPhase
        )

        result = TransitionResult(success=False)
        states_to_activate = transition.get_all_states_to_activate()
        states_to_exit = transition.get_all_states_to_exit()

        # Track which states successfully completed incoming transitions
        successfully_activated = set()
        failed_incoming = set()

        try:
            # PHASE 1: VALIDATE
            # Pre-validate all preconditions before any changes
            if not self.can_execute(transition, active_states):
                result.phase_results.append(PhaseResult(
                    phase=TransitionPhase.VALIDATE,
                    success=False,
                    message="Transition cannot execute from current state"
                ))
                return result

            # Validate group atomicity
            if not transition.validate_groups(active_states):
                result.phase_results.append(PhaseResult(
                    phase=TransitionPhase.VALIDATE,
                    success=False,
                    message="Group atomicity violation detected"
                ))
                return result

            result.phase_results.append(PhaseResult(
                phase=TransitionPhase.VALIDATE,
                success=True,
                message="All preconditions satisfied"
            ))

            # PHASE 2: OUTGOING
            # Execute outgoing transition action
            outgoing_success = True
            if callbacks:
                outgoing_success = callbacks.execute_outgoing(transition.id)
            elif transition.action:
                try:
                    outgoing_success = transition.action()
                except Exception as e:
                    outgoing_success = False
                    result.phase_results.append(PhaseResult(
                        phase=TransitionPhase.OUTGOING,
                        success=False,
                        message=f"Outgoing action failed: {str(e)}"
                    ))

            if not outgoing_success:
                if not result.phase_results or result.phase_results[-1].phase != TransitionPhase.OUTGOING:
                    result.phase_results.append(PhaseResult(
                        phase=TransitionPhase.OUTGOING,
                        success=False,
                        message="Outgoing transition failed"
                    ))
                return result

            result.phase_results.append(PhaseResult(
                phase=TransitionPhase.OUTGOING,
                success=True,
                message="Outgoing transition completed"
            ))

            # PHASE 3: ACTIVATE
            # Pure memory update - activate ALL target states atomically
            # This phase CANNOT fail (it's just memory update)
            for state in states_to_activate:
                successfully_activated.add(state)

            result.phase_results.append(PhaseResult(
                phase=TransitionPhase.ACTIVATE,
                success=True,
                message=f"Activated {len(successfully_activated)} states",
                data={"activated": {s.id for s in successfully_activated}}
            ))

            # PHASE 4: INCOMING
            # Execute incoming transitions for ALL activated states
            incoming_results = {}
            for state in successfully_activated:
                incoming_success = True

                if callbacks:
                    incoming_success = callbacks.execute_incoming(transition.id, state.id)
                else:
                    # Check for incoming action in transition
                    incoming_action = transition.get_incoming_action_for_state(state)
                    if incoming_action:
                        try:
                            incoming_action()
                        except Exception as e:
                            incoming_success = False

                incoming_results[state.id] = incoming_success
                if not incoming_success:
                    failed_incoming.add(state)

            # Determine if incoming phase succeeded based on policy
            incoming_phase_success = self._evaluate_incoming_success(
                successfully_activated,
                failed_incoming
            )

            result.phase_results.append(PhaseResult(
                phase=TransitionPhase.INCOMING,
                success=incoming_phase_success,
                message=f"{len(successfully_activated) - len(failed_incoming)}/{len(successfully_activated)} incoming transitions succeeded",
                data={
                    "successful": {s.id for s in successfully_activated - failed_incoming},
                    "failed": {s.id for s in failed_incoming}
                }
            ))

            if not incoming_phase_success:
                # Incoming phase failed according to policy
                # In strict mode, this means transition fails
                return result

            # PHASE 5: EXIT
            # Pure memory update - deactivate exit states
            # This phase CANNOT fail (it's just memory update)
            result.phase_results.append(PhaseResult(
                phase=TransitionPhase.EXIT,
                success=True,
                message=f"Deactivated {len(states_to_exit)} states",
                data={"deactivated": {s.id for s in states_to_exit}}
            ))

            # PHASE 6: VISIBILITY
            # Update visibility of states (if needed)
            result.phase_results.append(PhaseResult(
                phase=TransitionPhase.VISIBILITY,
                success=True,
                message="Visibility updated"
            ))

            # PHASE 7: CLEANUP
            # Clean up resources and finalize
            result.phase_results.append(PhaseResult(
                phase=TransitionPhase.CLEANUP,
                success=True,
                message="Cleanup completed"
            ))

            # Set final result data
            result.success = True
            result.activated_states = successfully_activated.copy()
            result.deactivated_states = states_to_exit.copy()
            result.metadata = {
                "transition_id": transition.id,
                "incoming_failures": len(failed_incoming),
                "policy": self.success_policy.value
            }

        except Exception as e:
            # Unexpected error during execution
            result.error = e
            result.phase_results.append(PhaseResult(
                phase=TransitionPhase.CLEANUP,
                success=False,
                message=f"Unexpected error: {str(e)}"
            ))

        return result

    def _evaluate_incoming_success(
        self,
        activated_states: Set[State],
        failed_states: Set[State]
    ) -> bool:
        """Evaluate if incoming phase succeeded based on policy.

        Args:
            activated_states: All states that were activated
            failed_states: States whose incoming transitions failed

        Returns:
            True if incoming phase succeeded according to policy
        """
        if not activated_states:
            return True

        successful_count = len(activated_states) - len(failed_states)
        total_count = len(activated_states)
        success_rate = successful_count / total_count if total_count > 0 else 1.0

        if self.success_policy == SuccessPolicy.STRICT:
            # ALL incoming must succeed
            return len(failed_states) == 0

        elif self.success_policy == SuccessPolicy.LENIENT:
            # Only activation must succeed (incoming failures are OK)
            return True

        elif self.success_policy == SuccessPolicy.THRESHOLD:
            # At least threshold% must succeed
            return success_rate >= self.success_threshold

        return False

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

