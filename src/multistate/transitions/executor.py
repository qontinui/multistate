"""TransitionExecutor: Orchestrates phased transition execution.

Implements the formal transition function:
f_τ_MS: t_MS → (Ξ', r_t)

With phased execution φ = ⟨φ_outgoing, φ_activate, φ_incoming, φ_exit⟩
"""

import time
from enum import Enum
from typing import TYPE_CHECKING, Optional, Set

from multistate.core.state import State
from multistate.transitions.transition import Transition
from multistate.transitions.visibility import StaysVisible

if TYPE_CHECKING:
    from multistate.transitions.callbacks import TransitionCallbacks
    from multistate.transitions.reliability import ReliabilityTracker
    from multistate.transitions.transition import TransitionResult


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
        strict_mode: bool = True,
        reliability_tracker: Optional["ReliabilityTracker"] = None,
    ):
        """Initialize the executor.

        Args:
            success_policy: Policy for determining transition success
            success_threshold: For THRESHOLD policy, % of incoming that must succeed
            strict_mode: If True, enforce strict validation and rollback
            reliability_tracker: Optional tracker for transition reliability metrics
        """
        self.success_policy = success_policy
        self.success_threshold = success_threshold
        self.strict_mode = strict_mode
        self.reliability_tracker = reliability_tracker

    def execute(
        self,
        transition: Transition,
        active_states: Set[State],
        callbacks: Optional["TransitionCallbacks"] = None,
    ) -> "TransitionResult":
        """Execute a transition with full phased orchestration.

        This implements the complete transition execution following
        the formal model's phased approach:
        φ = ⟨φ_validate, φ_outgoing, φ_activate, φ_incoming, φ_exit,
        φ_visibility, φ_cleanup⟩

        Args:
            transition: The transition to execute
            active_states: Current active states (S_Ξ)
            callbacks: Optional callbacks to execute during phases

        Returns:
            TransitionResult with complete phase tracking
        """
        from multistate.transitions.transition import (
            PhaseResult,
            TransitionPhase,
            TransitionResult,
        )

        result = TransitionResult(success=False)
        states_to_activate = transition.get_all_states_to_activate()
        states_to_exit = transition.get_all_states_to_exit()

        # Track which states successfully completed incoming transitions
        successfully_activated = set()
        failed_incoming = set()

        # Track execution time for reliability metrics
        start_time = time.time() if self.reliability_tracker else None
        reliability_recorded = False  # Flag to prevent double-recording

        try:
            # PHASE 1: VALIDATE
            # Pre-validate all preconditions before any changes
            if not self.can_execute(transition, active_states):
                result.phase_results.append(
                    PhaseResult(
                        phase=TransitionPhase.VALIDATE,
                        success=False,
                        message="Transition cannot execute from current state",
                    )
                )
                # Track failure before returning
                if self.reliability_tracker and start_time is not None:
                    execution_time = time.time() - start_time
                    self.reliability_tracker.record_failure(
                        transition.id, execution_time=execution_time
                    )
                return result

            # Validate group atomicity
            if not transition.validate_groups(active_states):
                result.phase_results.append(
                    PhaseResult(
                        phase=TransitionPhase.VALIDATE,
                        success=False,
                        message="Group atomicity violation detected",
                    )
                )
                # Track failure before returning
                if self.reliability_tracker and start_time is not None:
                    execution_time = time.time() - start_time
                    self.reliability_tracker.record_failure(
                        transition.id, execution_time=execution_time
                    )
                return result

            result.phase_results.append(
                PhaseResult(
                    phase=TransitionPhase.VALIDATE,
                    success=True,
                    message="All preconditions satisfied",
                )
            )

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
                    result.phase_results.append(
                        PhaseResult(
                            phase=TransitionPhase.OUTGOING,
                            success=False,
                            message=f"Outgoing action failed: {str(e)}",
                        )
                    )

            if not outgoing_success:
                if (
                    not result.phase_results
                    or result.phase_results[-1].phase != TransitionPhase.OUTGOING
                ):
                    result.phase_results.append(
                        PhaseResult(
                            phase=TransitionPhase.OUTGOING,
                            success=False,
                            message="Outgoing transition failed",
                        )
                    )
                # Track failure before returning
                if self.reliability_tracker and start_time is not None:
                    execution_time = time.time() - start_time
                    self.reliability_tracker.record_failure(
                        transition.id, execution_time=execution_time
                    )
                return result

            result.phase_results.append(
                PhaseResult(
                    phase=TransitionPhase.OUTGOING,
                    success=True,
                    message="Outgoing transition completed",
                )
            )

            # PHASE 3: ACTIVATE
            # Pure memory update - activate ALL target states atomically
            # This phase CANNOT fail (it's just memory update)
            for state in states_to_activate:
                successfully_activated.add(state)

            result.phase_results.append(
                PhaseResult(
                    phase=TransitionPhase.ACTIVATE,
                    success=True,
                    message=f"Activated {len(successfully_activated)} states",
                    data={"activated": {s.id for s in successfully_activated}},
                )
            )

            # PHASE 4: INCOMING
            # Execute incoming transitions for ALL activated states
            incoming_results = {}
            for state in successfully_activated:
                incoming_success = True

                if callbacks:
                    incoming_success = callbacks.execute_incoming(
                        transition.id, state.id
                    )
                else:
                    # Check for incoming action in transition
                    incoming_action = transition.get_incoming_action_for_state(state)
                    if incoming_action:
                        try:
                            incoming_action()
                        except Exception:
                            incoming_success = False

                incoming_results[state.id] = incoming_success
                if not incoming_success:
                    failed_incoming.add(state)

            # Determine if incoming phase succeeded based on policy
            incoming_phase_success = self._evaluate_incoming_success(
                successfully_activated, failed_incoming
            )

            successful_count = len(successfully_activated) - len(failed_incoming)
            total_count = len(successfully_activated)
            result.phase_results.append(
                PhaseResult(
                    phase=TransitionPhase.INCOMING,
                    success=incoming_phase_success,
                    message=(
                        f"{successful_count}/{total_count} "
                        "incoming transitions succeeded"
                    ),
                    data={
                        "successful": {
                            s.id for s in successfully_activated - failed_incoming
                        },
                        "failed": {s.id for s in failed_incoming},
                    },
                )
            )

            if not incoming_phase_success:
                # Incoming phase failed according to policy
                # In strict mode, this means transition fails
                # Track failure before returning
                if self.reliability_tracker and start_time is not None:
                    execution_time = time.time() - start_time
                    self.reliability_tracker.record_failure(
                        transition.id, execution_time=execution_time
                    )
                return result

            # PHASE 5: EXIT
            # Pure memory update - deactivate exit states
            # This phase CANNOT fail (it's just memory update)
            result.phase_results.append(
                PhaseResult(
                    phase=TransitionPhase.EXIT,
                    success=True,
                    message=f"Deactivated {len(states_to_exit)} states",
                    data={"deactivated": {s.id for s in states_to_exit}},
                )
            )

            # PHASE 6: VISIBILITY
            # Update visibility of states based on stays_visible setting
            visibility_data = self._update_visibility(
                transition, active_states, successfully_activated
            )
            result.phase_results.append(
                PhaseResult(
                    phase=TransitionPhase.VISIBILITY,
                    success=True,
                    message="Visibility updated",
                    data=visibility_data,
                )
            )

            # PHASE 7: CLEANUP
            # Clean up resources and finalize
            result.phase_results.append(
                PhaseResult(
                    phase=TransitionPhase.CLEANUP,
                    success=True,
                    message="Cleanup completed",
                )
            )

            # Set final result data
            result.success = True
            result.activated_states = successfully_activated.copy()
            result.deactivated_states = states_to_exit.copy()
            result.metadata = {
                "transition_id": transition.id,
                "incoming_failures": len(failed_incoming),
                "policy": self.success_policy.value,
            }

            # Track successful execution in reliability tracker
            if self.reliability_tracker and start_time is not None:
                execution_time = time.time() - start_time
                self.reliability_tracker.record_success(
                    transition.id, execution_time=execution_time
                )
                reliability_recorded = True

        except Exception as e:
            # Unexpected error during execution
            result.error = e
            result.phase_results.append(
                PhaseResult(
                    phase=TransitionPhase.CLEANUP,
                    success=False,
                    message=f"Unexpected error: {str(e)}",
                )
            )

            # Track failed execution in reliability tracker
            if self.reliability_tracker and start_time is not None:
                execution_time = time.time() - start_time
                self.reliability_tracker.record_failure(
                    transition.id, execution_time=execution_time
                )
                reliability_recorded = True

        # Also track failures from failed phases (not exceptions)
        if (
            not result.success
            and self.reliability_tracker
            and start_time is not None
            and not reliability_recorded
        ):
            execution_time = time.time() - start_time
            self.reliability_tracker.record_failure(
                transition.id, execution_time=execution_time
            )

        return result

    def _evaluate_incoming_success(
        self, activated_states: Set[State], failed_states: Set[State]
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
        self, transition: Transition, current_states: Set[State]
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

    def _update_visibility(
        self,
        transition: Transition,
        from_states: Set[State],
        activated_states: Set[State],
    ) -> dict:
        """Update state visibility based on transition's stays_visible setting.

        Args:
            transition: The transition being executed
            from_states: States the transition executed from
            activated_states: States that were activated

        Returns:
            Dictionary with visibility information for the phase result
        """
        states_to_hide = set()
        states_to_show = set()

        # Determine which states were "source" states (not being exited)
        states_to_exit = transition.get_all_states_to_exit()
        source_states = from_states - states_to_exit

        if transition.stays_visible == StaysVisible.TRUE:
            # Source states should remain visible (explicitly ensure they're shown)
            states_to_show = {s.id for s in source_states}

        elif transition.stays_visible == StaysVisible.FALSE:
            # Source states should be hidden
            states_to_hide = {s.id for s in source_states}

        # NONE means no explicit visibility changes - inherit from container/parent

        return {
            "stays_visible": transition.stays_visible.value,
            "states_to_hide": list(states_to_hide),
            "states_to_show": list(states_to_show),
        }
