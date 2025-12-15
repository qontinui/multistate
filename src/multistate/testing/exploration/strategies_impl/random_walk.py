"""Random walk exploration strategy.

Selects next state randomly from available transitions.
Useful for baseline comparison and discovering unexpected paths.
"""

import logging
import random

from multistate.testing.config import ExplorationConfig
from multistate.testing.exploration.strategies_impl.base import ExplorationStrategy
from multistate.testing.tracker import PathTracker

# Optional numpy support
try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore
    HAS_NUMPY = False

logger = logging.getLogger(__name__)


class RandomWalkExplorer(ExplorationStrategy):
    """Random walk exploration strategy.

    Selects next state randomly from available transitions.
    Useful for baseline comparison and discovering unexpected paths.
    """

    def __init__(self, config: ExplorationConfig, tracker: PathTracker):
        """Initialize random walk explorer.

        Args:
            config: Exploration configuration
            tracker: PathTracker instance
        """
        super().__init__(config, tracker)

        # Set random seed if provided
        if config.random_seed is not None:
            random.seed(config.random_seed)
            if HAS_NUMPY:
                np.random.seed(config.random_seed)

        self.temperature = config.random_walk_temperature

    def select_next_state(self, current_state: str) -> str | None:
        """Select next state randomly.

        Args:
            current_state: Current state name

        Returns:
            Random next state, or None if no transitions available
        """
        transitions = self.get_available_transitions(current_state)

        if not transitions:
            logger.debug(f"No transitions available from {current_state}")
            return None

        # Apply temperature for exploration control
        if self.temperature == 1.0 or not HAS_NUMPY:
            # Uniform random selection
            _, next_state = random.choice(transitions)
        else:
            # Temperature-weighted selection (requires numpy)
            # Higher temperature = more uniform
            # Lower temperature = more concentrated
            weights = np.ones(len(transitions))
            weights = np.exp(weights / self.temperature)  # type: ignore[assignment]
            weights /= weights.sum()

            idx = np.random.choice(len(transitions), p=weights)
            _, next_state = transitions[idx]

        logger.debug(f"Random walk: {current_state} -> {next_state}")
        return next_state
