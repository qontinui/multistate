"""PathTracker - Main class for tracking state transitions during testing.

This module provides comprehensive tracking of state transitions during
state machine testing, including coverage metrics, deficiency detection,
and performance analysis.

This is a refactored version that delegates to specialized modules for
better maintainability and separation of concerns.
"""

import logging
import threading
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime
from typing import Any, Literal

from multistate.testing.coverage_analyzer import CoverageAnalyzer
from multistate.testing.deficiency_detector import DeficiencyDetector
from multistate.testing.enums import (
    DeficiencyCategory,
    DeficiencySeverity,
    ExecutionStatus,
)
from multistate.testing.export_handlers import ExportHandlers
from multistate.testing.models import (
    CoverageMetrics,
    Deficiency,
    PathHistory,
    TransitionExecution,
    TransitionStatistics,
)
from multistate.testing.path_analysis import PathAnalyzer
from multistate.testing.screenshot_manager import ScreenshotManager

logger = logging.getLogger(__name__)


class PathTracker:
    """Tracks state/transition execution for testing and coverage analysis.

    This class provides comprehensive tracking of state transitions during
    state machine testing, including coverage metrics, deficiency detection,
    and performance analysis.

    Thread Safety:
        All public methods are thread-safe and can be called concurrently.

    Example:
        >>> tracker = PathTracker(
        ...     state_graph=graph,
        ...     enable_screenshots=True
        ... )
        >>> tracker.record_transition("login", "dashboard", success=True)
        >>> metrics = tracker.get_coverage_metrics()
        >>> print(f"Coverage: {metrics.state_coverage_percent:.1f}%")
    """

    def __init__(
        self,
        state_graph: Any,
        enable_screenshots: bool = True,
        screenshot_dir: str = "./screenshots",
        max_history_size: int = 10000,
        performance_threshold_ms: float = 5000.0,
        stability_threshold: float = 0.95,
    ) -> None:
        """Initialize PathTracker.

        Args:
            state_graph: StateGraph to track (read-only reference)
            enable_screenshots: Whether to capture screenshots
            screenshot_dir: Directory for screenshot storage
            max_history_size: Maximum execution history entries
            performance_threshold_ms: Threshold for slow transition detection
            stability_threshold: Success rate threshold for stability (0.95 = 95%)
        """
        self.state_graph = state_graph
        self.max_history_size = max_history_size
        self.performance_threshold_ms = performance_threshold_ms
        self.stability_threshold = stability_threshold

        # Initialize specialized components
        self._screenshot_manager = ScreenshotManager(
            screenshot_dir=screenshot_dir,
            enabled=enable_screenshots,
        )
        self._coverage_analyzer = CoverageAnalyzer()
        self._export_handlers = ExportHandlers()
        self._path_analyzer = PathAnalyzer()
        self._deficiency_detector = DeficiencyDetector(
            performance_threshold_ms=performance_threshold_ms,
            stability_threshold=stability_threshold,
        )

        # Thread safety
        self._lock = threading.RLock()

        # Execution tracking
        self._executions: deque[TransitionExecution] = deque(maxlen=max_history_size)
        self._execution_lookup: dict[str, TransitionExecution] = {}

        # Coverage tracking
        self._visited_states: set[str] = set()
        self._executed_transitions: set[tuple[str, str]] = set()

        # Statistics (incremental)
        self._transition_stats: dict[tuple[str, str], TransitionStatistics] = {}

        # Deficiency tracking
        self._deficiencies: list[Deficiency] = []
        self._deficiency_lookup: dict[str, Deficiency] = {}

        # Path tracking
        self._paths: list[PathHistory] = []
        self._current_path: PathHistory | None = None

        # Metrics cache
        self._metrics_cache: CoverageMetrics | None = None
        self._cache_dirty = True

        # Callbacks
        self._deficiency_callbacks: list[Callable[[Deficiency], None]] = []
        self._coverage_milestone_callbacks: dict[
            float, list[Callable[[CoverageMetrics, float], None]]
        ] = defaultdict(list)
        self._milestone_reached: set[float] = set()

        # Log initialization
        total_states = len(state_graph.states) if hasattr(state_graph, "states") else 0
        total_transitions = 0
        if hasattr(state_graph, "states"):
            for state in state_graph.states.values():
                if hasattr(state, "transitions"):
                    total_transitions += len(state.transitions)

        logger.info(
            f"PathTracker initialized: {total_states} states, "
            f"{total_transitions} transitions"
        )

    # -------------------------------------------------------------------------
    # Public API - Recording
    # -------------------------------------------------------------------------

    def record_transition(
        self,
        from_state: str,
        to_state: str,
        success: bool = True,
        duration_ms: float | None = None,
        error_message: str | None = None,
        actual_end_state: str | None = None,
        screenshot: Any | None = None,
        variables: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TransitionExecution:
        """Record a transition execution attempt.

        This is the primary method for tracking state transitions during test execution.

        Args:
            from_state: Source state name
            to_state: Target state name (intended)
            success: Whether transition succeeded
            duration_ms: Execution duration in milliseconds
            error_message: Error message if failed
            actual_end_state: Actual state reached
            screenshot: Screenshot array (numpy ndarray if cv2 available)
            variables: Current execution variables snapshot
            metadata: Additional metadata

        Returns:
            TransitionExecution record

        Thread Safety:
            This method is thread-safe.
        """
        with self._lock:
            # Generate execution ID
            execution_id = str(uuid.uuid4())

            # Determine status
            if success:
                status = ExecutionStatus.SUCCESS
            elif error_message:
                status = ExecutionStatus.ERROR
            else:
                status = ExecutionStatus.FAILURE

            # Auto-calculate duration if not provided
            if duration_ms is None:
                duration_ms = 0.0

            # Save screenshot if provided
            screenshot_path = None
            if screenshot is not None:
                screenshot_path = self._screenshot_manager.save_screenshot(
                    execution_id, screenshot
                )

            # Determine attempt number
            transition_key = (from_state, to_state)
            if transition_key in self._transition_stats:
                attempt_number = (
                    self._transition_stats[transition_key].total_attempts + 1
                )
            else:
                attempt_number = 1

            # Create execution record
            execution = TransitionExecution(
                execution_id=execution_id,
                from_state=from_state,
                to_state=to_state,
                status=status,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                attempt_number=attempt_number,
                error_message=error_message,
                actual_end_state=actual_end_state
                or (to_state if success else from_state),
                screenshot_path=screenshot_path,
                variables_snapshot=variables.copy() if variables else None,
                metadata=metadata or {},
            )

            # Store execution
            self._executions.append(execution)
            self._execution_lookup[execution_id] = execution

            # Update tracking
            self._update_coverage(execution)
            self._update_statistics(execution)
            self._update_path_history(execution)
            self._detect_deficiencies(execution)

            # Invalidate cache
            self._cache_dirty = True

            # Check coverage milestones
            self._check_coverage_milestones()

            logger.debug(
                f"Recorded transition: {from_state} -> {to_state} "
                f"[{status.value}] {duration_ms:.0f}ms"
            )

            return execution

    def start_new_path(self, start_state: str) -> None:
        """Start tracking a new path.

        Args:
            start_state: Starting state for the new path
        """
        with self._lock:
            # Finalize current path if exists
            if self._current_path and not self._current_path.is_complete:
                self._current_path.end_time = datetime.now()
                self._paths.append(self._current_path)

            # Create new path
            self._current_path = PathHistory(
                path_id=str(uuid.uuid4()),
                start_state=start_state,
                end_state=start_state,
                states=[start_state],
                transitions=[],
                start_time=datetime.now(),
            )

    def end_current_path(self, success: bool = True) -> None:
        """End the current path tracking.

        Args:
            success: Whether the path completed successfully
        """
        with self._lock:
            if self._current_path:
                self._current_path.end_time = datetime.now()
                self._current_path.success = success
                self._paths.append(self._current_path)
                self._current_path = None

    # -------------------------------------------------------------------------
    # Public API - Retrieval
    # -------------------------------------------------------------------------

    def get_coverage_metrics(self) -> CoverageMetrics:
        """Calculate current coverage metrics.

        Returns:
            CoverageMetrics with complete coverage analysis

        Performance:
            Uses cached calculations when possible.
        """
        with self._lock:
            if not self._cache_dirty and self._metrics_cache:
                return self._metrics_cache

            # Delegate to coverage analyzer
            metrics = self._coverage_analyzer.calculate_metrics(
                state_graph=self.state_graph,
                visited_states=self._visited_states,
                executed_transitions=self._executed_transitions,
                executions=list(self._executions),
                paths=self._paths,
            )

            # Cache
            self._metrics_cache = metrics
            self._cache_dirty = False

            return metrics

    def get_unexplored_transitions(self) -> list[tuple[str, str]]:
        """Get list of transitions that have never been executed.

        Returns:
            List of (from_state, to_state) tuples
        """
        with self._lock:
            return self._coverage_analyzer.get_unexplored_transitions(
                state_graph=self.state_graph,
                executed_transitions=self._executed_transitions,
            )

    def get_unstable_transitions(
        self, min_threshold: float | None = None
    ) -> list[TransitionStatistics]:
        """Get transitions with unstable/unreliable success rates.

        Args:
            min_threshold: Minimum success rate threshold

        Returns:
            List of TransitionStatistics for unstable transitions
        """
        threshold = (
            min_threshold if min_threshold is not None else self.stability_threshold
        )

        with self._lock:
            unstable = []

            for stats in self._transition_stats.values():
                if stats.total_attempts >= 2 and stats.success_rate < (threshold * 100):
                    unstable.append(stats)

            return sorted(unstable, key=lambda s: s.success_rate)

    def get_deficiencies(
        self,
        severity: DeficiencySeverity | None = None,
        category: DeficiencyCategory | None = None,
    ) -> list[Deficiency]:
        """Get detected deficiencies/issues.

        Args:
            severity: Filter by severity
            category: Filter by category

        Returns:
            List of Deficiency objects
        """
        with self._lock:
            deficiencies = self._deficiencies.copy()

            # Apply filters
            if severity:
                deficiencies = [d for d in deficiencies if d.severity == severity]

            if category:
                deficiencies = [d for d in deficiencies if d.category == category]

            return deficiencies

    def get_path_history(
        self, limit: int | None = None, successful_only: bool = False
    ) -> list[PathHistory]:
        """Get path traversal history.

        Args:
            limit: Maximum number of paths to return
            successful_only: Only return successful paths

        Returns:
            List of PathHistory objects, newest first
        """
        with self._lock:
            paths = self._paths.copy()

            if successful_only:
                paths = [p for p in paths if p.success]

            # Sort by start time, newest first
            paths.sort(key=lambda p: p.start_time, reverse=True)

            if limit:
                paths = paths[:limit]

            return paths

    def get_transition_statistics(
        self, from_state: str | None = None, to_state: str | None = None
    ) -> list[TransitionStatistics]:
        """Get detailed statistics for transitions.

        Args:
            from_state: Filter by source state
            to_state: Filter by target state

        Returns:
            List of TransitionStatistics
        """
        with self._lock:
            stats = list(self._transition_stats.values())

            # Apply filters
            if from_state:
                stats = [s for s in stats if s.from_state == from_state]

            if to_state:
                stats = [s for s in stats if s.to_state == to_state]

            return stats

    # -------------------------------------------------------------------------
    # Public API - Analysis
    # -------------------------------------------------------------------------

    def analyze_reachability(self) -> dict[str, list[str]]:
        """Analyze state reachability from initial state.

        Returns:
            Dictionary mapping state names to list of reachable states
        """
        return self._path_analyzer.analyze_reachability(self.state_graph)

    def suggest_next_transitions(
        self, current_state: str, prioritize_unexplored: bool = True
    ) -> list[tuple[str, float]]:
        """Suggest next transitions to maximize coverage.

        Args:
            current_state: Current state
            prioritize_unexplored: Prioritize unexplored transitions

        Returns:
            List of (to_state, priority_score) tuples
        """
        with self._lock:
            return self._path_analyzer.suggest_next_transitions(
                state_graph=self.state_graph,
                current_state=current_state,
                visited_states=self._visited_states,
                executed_transitions=self._executed_transitions,
                transition_stats=self._transition_stats,
                prioritize_unexplored=prioritize_unexplored,
            )

    def get_critical_path(self, start_state: str, end_state: str) -> PathHistory | None:
        """Get the critical path between two states.

        Args:
            start_state: Starting state
            end_state: Target state

        Returns:
            PathHistory for critical path, or None if no path found
        """
        with self._lock:
            return self._path_analyzer.get_critical_path(
                paths=self._paths,
                start_state=start_state,
                end_state=end_state,
            )

    # -------------------------------------------------------------------------
    # Public API - Export
    # -------------------------------------------------------------------------

    def export_results(
        self,
        output_path: str,
        format: Literal["json", "html", "csv", "markdown"] = "json",
        include_screenshots: bool = True,
        include_variables: bool = False,
    ) -> None:
        """Export tracking results to file.

        Args:
            output_path: Path to output file
            format: Export format
            include_screenshots: Include screenshot references
            include_variables: Include variable snapshots
        """
        with self._lock:
            metrics = self.get_coverage_metrics()

            self._export_handlers.export_results(
                output_path=output_path,
                format=format,
                metrics=metrics,
                executions=list(self._executions),
                statistics=list(self._transition_stats.values()),
                deficiencies=self._deficiencies,
                paths=self._paths,
                include_screenshots=include_screenshots,
                include_variables=include_variables,
            )

    # -------------------------------------------------------------------------
    # Public API - Reset
    # -------------------------------------------------------------------------

    def reset(self) -> None:
        """Reset all tracking data.

        Thread Safety:
            This method is thread-safe but should not be called during active tracking.
        """
        with self._lock:
            self._executions.clear()
            self._execution_lookup.clear()
            self._visited_states.clear()
            self._executed_transitions.clear()
            self._transition_stats.clear()
            self._deficiencies.clear()
            self._deficiency_lookup.clear()
            self._paths.clear()
            self._current_path = None
            self._metrics_cache = None
            self._cache_dirty = True
            self._milestone_reached.clear()

            logger.info("PathTracker reset")

    # -------------------------------------------------------------------------
    # Public API - Callbacks
    # -------------------------------------------------------------------------

    def on_deficiency_detected(self, callback: Callable[[Deficiency], None]) -> None:
        """Register callback for deficiency detection.

        Args:
            callback: Function to call with Deficiency object
        """
        with self._lock:
            self._deficiency_callbacks.append(callback)

    def on_coverage_milestone(
        self,
        callback: Callable[[CoverageMetrics, float], None],
        milestone_percent: float,
    ) -> None:
        """Register callback for coverage milestones.

        Args:
            callback: Function to call with (metrics, milestone_percent)
            milestone_percent: Coverage percentage to trigger callback
        """
        with self._lock:
            self._coverage_milestone_callbacks[milestone_percent].append(callback)

    # -------------------------------------------------------------------------
    # Internal Methods
    # -------------------------------------------------------------------------

    def _update_coverage(self, execution: TransitionExecution) -> None:
        """Update coverage tracking.

        Args:
            execution: Execution to update from
        """
        self._visited_states.add(execution.from_state)
        if execution.is_successful:
            self._visited_states.add(execution.to_state)

        transition_key = (execution.from_state, execution.to_state)
        self._executed_transitions.add(transition_key)

    def _update_statistics(self, execution: TransitionExecution) -> None:
        """Update transition statistics.

        Args:
            execution: Execution to update from
        """
        transition_key = (execution.from_state, execution.to_state)

        if transition_key not in self._transition_stats:
            self._transition_stats[transition_key] = TransitionStatistics(
                from_state=execution.from_state, to_state=execution.to_state
            )

        stats = self._transition_stats[transition_key]
        stats.total_attempts += 1

        if execution.status == ExecutionStatus.SUCCESS:
            stats.successes += 1
        elif execution.status == ExecutionStatus.ERROR:
            stats.errors += 1
        else:
            stats.failures += 1

        # Update duration stats
        stats.min_duration_ms = min(stats.min_duration_ms, execution.duration_ms)
        stats.max_duration_ms = max(stats.max_duration_ms, execution.duration_ms)

        # Update average (incremental)
        n = stats.total_attempts
        stats.avg_duration_ms = (
            stats.avg_duration_ms * (n - 1) + execution.duration_ms
        ) / n

        # Update timestamps
        if stats.first_executed is None:
            stats.first_executed = execution.timestamp
        stats.last_executed = execution.timestamp

    def _update_path_history(self, execution: TransitionExecution) -> None:
        """Update path history tracking.

        Args:
            execution: Execution to add to path
        """
        # Start new path if needed
        if self._current_path is None:
            self._current_path = PathHistory(
                path_id=str(uuid.uuid4()),
                start_state=execution.from_state,
                end_state=execution.from_state,
                states=[execution.from_state],
                transitions=[],
                start_time=execution.timestamp,
            )

        # Add to current path
        self._current_path.transitions.append(execution.execution_id)
        self._current_path.states.append(execution.to_state)
        self._current_path.end_state = execution.to_state
        self._current_path.total_duration_ms += execution.duration_ms

        if not execution.is_successful:
            self._current_path.success = False

    def _detect_deficiencies(self, execution: TransitionExecution) -> None:
        """Detect deficiencies from execution.

        Args:
            execution: Execution to analyze
        """
        # Detect execution-level deficiencies
        deficiency_tuples = self._deficiency_detector.detect_execution_deficiencies(
            execution
        )

        for category, severity, title, description in deficiency_tuples:
            self._add_deficiency(
                category=category,
                severity=severity,
                title=title,
                description=description,
                affected_transitions=[(execution.from_state, execution.to_state)],
                execution_id=execution.execution_id,
                timestamp=execution.timestamp,
                screenshot_path=execution.screenshot_path,
            )

        # Check transition statistics
        transition_key = (execution.from_state, execution.to_state)
        if transition_key in self._transition_stats:
            stats = self._transition_stats[transition_key]
            stat_deficiencies = (
                self._deficiency_detector.detect_transition_deficiencies(stats)
            )

            for category, severity, title, description in stat_deficiencies:
                self._add_deficiency(
                    category=category,
                    severity=severity,
                    title=title,
                    description=description,
                    affected_transitions=[(execution.from_state, execution.to_state)],
                    execution_id=execution.execution_id,
                    timestamp=execution.timestamp,
                )

    def _add_deficiency(
        self,
        category: DeficiencyCategory,
        severity: DeficiencySeverity,
        title: str,
        description: str,
        affected_transitions: list[tuple[str, str]],
        execution_id: str,
        timestamp: datetime,
        screenshot_path: str | None = None,
    ) -> None:
        """Add or update deficiency.

        Args:
            category: Deficiency category
            severity: Severity level
            title: Title
            description: Description
            affected_transitions: Affected transitions
            execution_id: Execution ID
            timestamp: Timestamp
            screenshot_path: Optional screenshot
        """
        # Check if similar deficiency exists
        deficiency_key = self._deficiency_detector.get_deficiency_key(category, title)

        if deficiency_key in self._deficiency_lookup:
            # Update existing
            deficiency = self._deficiency_lookup[deficiency_key]
            deficiency.add_occurrence(execution_id, timestamp, screenshot_path)
        else:
            # Create new
            deficiency = self._deficiency_detector.create_deficiency(
                category=category,
                severity=severity,
                title=title,
                description=description,
                affected_transitions=affected_transitions,
                execution_id=execution_id,
                timestamp=timestamp,
                screenshot_path=screenshot_path,
            )

            self._deficiencies.append(deficiency)
            self._deficiency_lookup[deficiency_key] = deficiency

            # Fire callbacks
            for callback in self._deficiency_callbacks:
                try:
                    callback(deficiency)
                except Exception as e:
                    logger.error(f"Deficiency callback failed: {e}")

    def _check_coverage_milestones(self) -> None:
        """Check if coverage milestones have been reached."""
        metrics = self.get_coverage_metrics()

        for milestone_percent, callbacks in self._coverage_milestone_callbacks.items():
            if milestone_percent in self._milestone_reached:
                continue

            if metrics.state_coverage_percent >= milestone_percent:
                self._milestone_reached.add(milestone_percent)

                for callback in callbacks:
                    try:
                        callback(metrics, milestone_percent)
                    except Exception as e:
                        logger.error(f"Coverage milestone callback failed: {e}")
