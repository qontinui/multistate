"""Hybrid exploration strategy combining multiple approaches."""

import logging

from multistate.testing.config import ExplorationConfig
from multistate.testing.exploration.strategies_impl.adaptive import AdaptiveExplorer
from multistate.testing.exploration.strategies_impl.bfs import BreadthFirstExplorer
from multistate.testing.exploration.strategies_impl.novelty import NoveltySeekingExplorer
from multistate.testing.exploration.strategies_impl.base import ExplorationStrategy
from multistate.testing.exploration.strategies_impl.dfs import DepthFirstExplorer
from multistate.testing.exploration.strategies_impl.greedy import GreedyCoverageExplorer
from multistate.testing.exploration.strategies_impl.random_walk import (
    RandomWalkExplorer,
)
from multistate.testing.tracker import PathTracker

logger = logging.getLogger(__name__)


class HybridExplorer(ExplorationStrategy):
    """Hybrid exploration strategy combining multiple approaches.

    Uses different strategies in phases or dynamically switches based
    on coverage progress. Combines strengths of multiple strategies.
    """

    def __init__(self, config: ExplorationConfig, tracker: PathTracker):
        """Initialize hybrid explorer.

        Args:
            config: Exploration configuration
            tracker: PathTracker instance
        """
        super().__init__(config, tracker)

        # Phase configuration
        self.phase_iterations = config.hybrid_phase_iterations
        self.phase_strategies = config.hybrid_phase_strategies
        self.dynamic_switching = config.hybrid_dynamic_switching
        self.switch_threshold = config.hybrid_switch_threshold

        # Current state
        self.iteration = 0
        self.current_phase = 0
        self.last_coverage = 0.0
        self.stagnation_count = 0

        # Initialize sub-strategies
        self.strategies: dict[str, ExplorationStrategy] = {
            "random_walk": RandomWalkExplorer(config, tracker),
            "greedy": GreedyCoverageExplorer(config, tracker),
            "dfs": DepthFirstExplorer(config, tracker),
            "bfs": BreadthFirstExplorer(config, tracker),
            "adaptive": AdaptiveExplorer(config, tracker),
            "novelty": NoveltySeekingExplorer(config, tracker),
        }

        # Set initial strategy
        self.current_strategy_name = self.phase_strategies[0]
        self.current_strategy = self.strategies[self.current_strategy_name]

        logger.info(f"Hybrid explorer initialized with phases: {self.phase_strategies}")

    def select_next_state(self, current_state: str) -> str | None:
        """Select next state using current strategy.

        Args:
            current_state: Current state name

        Returns:
            Next state from current strategy
        """
        # Update phase if needed
        self._update_phase()

        # Select using current strategy
        next_state = self.current_strategy.select_next_state(current_state)

        self.iteration += 1

        return next_state

    def _update_phase(self) -> None:
        """Update current phase/strategy based on iteration or coverage."""
        # Check if phase transition needed
        if self.current_phase < len(self.phase_iterations):
            if self.iteration >= self.phase_iterations[self.current_phase]:
                self._transition_to_next_phase()
                return

        # Dynamic switching based on coverage
        if self.dynamic_switching:
            metrics = self.tracker.get_coverage_metrics()
            current_coverage = metrics.transition_coverage_percent

            # Check if coverage is stagnating
            improvement = current_coverage - self.last_coverage

            if improvement < self.switch_threshold:
                self.stagnation_count += 1

                # Switch strategy if stagnating
                if self.stagnation_count >= 10:
                    self._switch_strategy_dynamically()
                    self.stagnation_count = 0
            else:
                self.stagnation_count = 0

            self.last_coverage = current_coverage

    def _transition_to_next_phase(self) -> None:
        """Transition to next phase."""
        self.current_phase += 1

        if self.current_phase < len(self.phase_strategies):
            new_strategy_name = self.phase_strategies[self.current_phase]
            self._switch_strategy(new_strategy_name)

            logger.info(
                f"Phase transition: {self.current_strategy_name} -> {new_strategy_name} "
                f"(iteration: {self.iteration})"
            )

    def _switch_strategy(self, strategy_name: str) -> None:
        """Switch to a different strategy.

        Args:
            strategy_name: Name of strategy to switch to
        """
        if strategy_name in self.strategies:
            self.current_strategy_name = strategy_name
            self.current_strategy = self.strategies[strategy_name]

    def _switch_strategy_dynamically(self) -> None:
        """Dynamically switch to a different strategy."""
        # Try strategies in order, skip current one
        available = [
            s for s in self.strategies.keys() if s != self.current_strategy_name
        ]

        if available:
            new_strategy = available[0]
            self._switch_strategy(new_strategy)

            logger.info(
                f"Dynamic switch: {self.current_strategy_name} -> {new_strategy} "
                f"(coverage stagnation detected)"
            )

    def reset(self) -> None:
        """Reset hybrid explorer state."""
        self.iteration = 0
        self.current_phase = 0
        self.last_coverage = 0.0
        self.stagnation_count = 0

        # Reset all sub-strategies
        for strategy in self.strategies.values():
            strategy.reset()

        # Reset to initial strategy
        self.current_strategy_name = self.phase_strategies[0]
        self.current_strategy = self.strategies[self.current_strategy_name]
