"""Testing module for state machine coverage and exploration.

This module provides comprehensive tools for testing state machines,
including path tracking, coverage metrics, deficiency detection,
and exploration strategies.

Modules:
    enums: Status and category enumerations
    config: Exploration configuration
    models: Data models for tracking
    deficiency_detector: Deficiency detection
    tracker: PathTracker for execution tracking
    exploration: Path exploration strategies (submodule)

Example:
    >>> from multistate.testing import PathTracker, ExplorationConfig
    >>> from multistate.testing.exploration import PathExplorer
    >>>
    >>> tracker = PathTracker(state_graph)
    >>> config = ExplorationConfig(strategy="adaptive", coverage_target=0.95)
"""

from multistate.testing.config import ExplorationConfig
from multistate.testing.deficiency_detector import DeficiencyDetector
from multistate.testing.enums import (
    DeficiencyCategory,
    DeficiencySeverity,
    ExecutionStatus,
)
from multistate.testing.models import (
    CoverageMetrics,
    Deficiency,
    PathHistory,
    TransitionExecution,
    TransitionStatistics,
)
from multistate.testing.tracker import PathTracker

__all__ = [
    # Enums
    "ExecutionStatus",
    "DeficiencySeverity",
    "DeficiencyCategory",
    # Config
    "ExplorationConfig",
    # Models
    "TransitionExecution",
    "CoverageMetrics",
    "Deficiency",
    "PathHistory",
    "TransitionStatistics",
    # Classes
    "DeficiencyDetector",
    "PathTracker",
]
