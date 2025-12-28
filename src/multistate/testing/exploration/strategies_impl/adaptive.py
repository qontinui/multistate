"""Adaptive exploration strategy with Q-learning."""

import logging
import random
from collections import defaultdict

# Optional numpy support
try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore
    HAS_NUMPY = False

from multistate.testing.config import ExplorationConfig
from multistate.testing.exploration.strategies_impl.base import ExplorationStrategy
from multistate.testing.tracker import PathTracker

logger = logging.getLogger(__name__)


class AdaptiveExplorer(ExplorationStrategy):
    """Adaptive exploration using Q-learning.

    Learns optimal transition policies through reinforcement learning,
    balancing exploration and exploitation using epsilon-greedy strategy.
    """

    def __init__(self, config: ExplorationConfig, tracker: PathTracker):
        """Initialize adaptive explorer.

        Args:
            config: Exploration configuration
            tracker: PathTracker instance
        """
        super().__init__(config, tracker)

        # Q-learning parameters
        self.learning_rate = config.adaptive_learning_rate
        self.discount_factor = config.adaptive_discount_factor
        self.epsilon = config.adaptive_epsilon_start
        self.epsilon_min = config.adaptive_epsilon_min
        self.epsilon_decay = config.adaptive_epsilon_decay

        # Rewards
        self.reward_success = config.adaptive_reward_success
        self.reward_failure = config.adaptive_reward_failure
        self.reward_new_state = config.adaptive_reward_new_state
        self.reward_new_transition = config.adaptive_reward_new_transition

        # Q-table: (state, action) -> Q-value
        self.q_table: dict[tuple[str, str], float] = defaultdict(float)

        # History for learning
        self.last_state: str | None = None
        self.last_action: str | None = None

    def select_next_state(self, current_state: str) -> str | None:
        """Select next state using Q-learning with epsilon-greedy.

        Args:
            current_state: Current state name

        Returns:
            Next state based on Q-values, or None if no transitions
        """
        transitions = self.get_available_transitions(current_state)

        if not transitions:
            return None

        # Epsilon-greedy selection
        if random.random() < self.epsilon:
            # Explore: random action
            _, next_state = random.choice(transitions)
            logger.debug(
                f"Q-learning explore: {current_state} -> {next_state} "
                f"(eps={self.epsilon:.3f})"
            )
        else:
            # Exploit: best Q-value
            q_values = [
                (to_state, self.q_table[(current_state, to_state)])
                for _, to_state in transitions
            ]
            q_values.sort(key=lambda x: x[1], reverse=True)
            next_state, q_val = q_values[0]
            logger.debug(
                f"Q-learning exploit: {current_state} -> {next_state} (Q={q_val:.2f})"
            )

        # Store for learning update
        self.last_state = current_state
        self.last_action = next_state

        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        return next_state

    def update_q_value(
        self,
        success: bool,
        new_state_discovered: bool = False,
        new_transition_discovered: bool = False,
    ) -> None:
        """Update Q-value based on outcome.

        Args:
            success: Whether transition succeeded
            new_state_discovered: Whether a new state was discovered
            new_transition_discovered: Whether a new transition was executed
        """
        if self.last_state is None or self.last_action is None:
            return

        # Calculate reward
        reward = self.reward_success if success else self.reward_failure

        if new_state_discovered:
            reward += self.reward_new_state

        if new_transition_discovered:
            reward += self.reward_new_transition

        # Get current Q-value
        state_action = (self.last_state, self.last_action)
        current_q = self.q_table[state_action]

        # Get max Q-value for next state
        next_transitions = self.get_available_transitions(self.last_action)
        if next_transitions:
            max_next_q = max(
                self.q_table[(self.last_action, to_state)]
                for _, to_state in next_transitions
            )
        else:
            max_next_q = 0.0

        # Q-learning update: Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        self.q_table[state_action] = new_q

        logger.debug(
            f"Q-update: ({self.last_state}, {self.last_action}) "
            f"Q: {current_q:.2f} -> {new_q:.2f} (r={reward:.1f})"
        )

    def reset(self) -> None:
        """Reset learning state (keep Q-table for transfer learning)."""
        self.last_state = None
        self.last_action = None
