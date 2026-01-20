"""Test metrics tracking functionality."""

import time

import pytest

from multistate.manager import StateManager, StateManagerConfig
from multistate.metrics import MetricsManager, StateMetrics, TransitionMetrics


class TestStateMetrics:
    """Test StateMetrics dataclass."""

    def test_initial_state(self) -> None:
        """Test initial metrics state."""
        metrics = StateMetrics(state_id="test_state")

        assert metrics.state_id == "test_state"
        assert metrics.visit_count == 0
        assert metrics.last_visited is None
        assert metrics.total_time_active == 0.0
        assert metrics.activation_count == 0
        assert metrics.deactivation_count == 0
        assert metrics.is_currently_active is False

    def test_record_activation(self) -> None:
        """Test recording state activation."""
        metrics = StateMetrics(state_id="test_state")

        metrics.record_activation()

        assert metrics.activation_count == 1
        assert metrics.visit_count == 1
        assert metrics.last_visited is not None
        assert metrics.is_currently_active is True

    def test_record_deactivation(self) -> None:
        """Test recording state deactivation."""
        metrics = StateMetrics(state_id="test_state")

        metrics.record_activation()
        time.sleep(0.01)  # Small delay to measure time
        metrics.record_deactivation()

        assert metrics.deactivation_count == 1
        assert metrics.is_currently_active is False
        assert metrics.total_time_active > 0.0

    def test_multiple_activations(self) -> None:
        """Test multiple activation/deactivation cycles."""
        metrics = StateMetrics(state_id="test_state")

        for _ in range(3):
            metrics.record_activation()
            time.sleep(0.01)
            metrics.record_deactivation()

        assert metrics.activation_count == 3
        assert metrics.deactivation_count == 3
        assert metrics.visit_count == 3
        assert metrics.total_time_active > 0.0

    def test_average_time_active(self) -> None:
        """Test average time calculation."""
        metrics = StateMetrics(state_id="test_state")

        # No activations yet
        assert metrics.get_average_time_active() == 0.0

        # After activations
        for _ in range(2):
            metrics.record_activation()
            time.sleep(0.01)
            metrics.record_deactivation()

        avg = metrics.get_average_time_active()
        assert avg > 0.0
        assert avg == metrics.total_time_active / metrics.activation_count

    def test_reset(self) -> None:
        """Test resetting metrics."""
        metrics = StateMetrics(state_id="test_state")

        metrics.record_activation()
        metrics.record_deactivation()

        metrics.reset()

        assert metrics.visit_count == 0
        assert metrics.last_visited is None
        assert metrics.total_time_active == 0.0
        assert metrics.activation_count == 0
        assert metrics.deactivation_count == 0
        assert metrics.is_currently_active is False


class TestTransitionMetrics:
    """Test TransitionMetrics dataclass."""

    def test_initial_state(self) -> None:
        """Test initial metrics state."""
        metrics = TransitionMetrics(transition_id="test_transition")

        assert metrics.transition_id == "test_transition"
        assert metrics.execution_count == 0
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert metrics.last_executed is None
        assert metrics.total_execution_time == 0.0

    def test_record_success(self) -> None:
        """Test recording successful execution."""
        metrics = TransitionMetrics(transition_id="test_transition")

        metrics.record_execution(success=True, execution_time=0.5)

        assert metrics.execution_count == 1
        assert metrics.success_count == 1
        assert metrics.failure_count == 0
        assert metrics.last_executed is not None
        assert metrics.total_execution_time == 0.5

    def test_record_failure(self) -> None:
        """Test recording failed execution."""
        metrics = TransitionMetrics(transition_id="test_transition")

        metrics.record_execution(success=False, execution_time=0.3)

        assert metrics.execution_count == 1
        assert metrics.success_count == 0
        assert metrics.failure_count == 1
        assert metrics.total_execution_time == 0.3

    def test_success_rate(self) -> None:
        """Test success rate calculation."""
        metrics = TransitionMetrics(transition_id="test_transition")

        # No executions
        assert metrics.get_success_rate() == 0.0

        # After mixed results
        metrics.record_execution(success=True)
        metrics.record_execution(success=True)
        metrics.record_execution(success=False)

        assert metrics.get_success_rate() == 2 / 3

    def test_average_execution_time(self) -> None:
        """Test average execution time calculation."""
        metrics = TransitionMetrics(transition_id="test_transition")

        # No executions
        assert metrics.get_average_execution_time() == 0.0

        # After executions
        metrics.record_execution(success=True, execution_time=0.5)
        metrics.record_execution(success=True, execution_time=0.3)

        assert metrics.get_average_execution_time() == 0.4

    def test_reset(self) -> None:
        """Test resetting metrics."""
        metrics = TransitionMetrics(transition_id="test_transition")

        metrics.record_execution(success=True, execution_time=0.5)

        metrics.reset()

        assert metrics.execution_count == 0
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert metrics.last_executed is None
        assert metrics.total_execution_time == 0.0


class TestMetricsManager:
    """Test MetricsManager class."""

    def test_initialization(self) -> None:
        """Test metrics manager initialization."""
        manager = MetricsManager(enabled=True)

        assert manager.enabled is True
        assert len(manager.state_metrics) == 0
        assert len(manager.transition_metrics) == 0

    def test_disabled_manager(self) -> None:
        """Test that disabled manager doesn't record metrics."""
        manager = MetricsManager(enabled=False)

        manager.record_state_activation("test")
        manager.record_transition_execution("test_t", True)

        assert len(manager.state_metrics) == 0
        assert len(manager.transition_metrics) == 0

    def test_record_state_activation(self) -> None:
        """Test recording state activation."""
        manager = MetricsManager()

        manager.record_state_activation("state1")

        metrics = manager.get_state_metrics("state1")
        assert metrics is not None
        assert metrics.visit_count == 1

    def test_record_state_deactivation(self) -> None:
        """Test recording state deactivation."""
        manager = MetricsManager()

        manager.record_state_activation("state1")
        manager.record_state_deactivation("state1")

        metrics = manager.get_state_metrics("state1")
        assert metrics is not None
        assert metrics.deactivation_count == 1

    def test_record_transition_execution(self) -> None:
        """Test recording transition execution."""
        manager = MetricsManager()

        manager.record_transition_execution("trans1", success=True, execution_time=0.5)

        metrics = manager.get_transition_metrics("trans1")
        assert metrics is not None
        assert metrics.success_count == 1
        assert metrics.total_execution_time == 0.5

    def test_get_most_visited_states(self) -> None:
        """Test getting most visited states."""
        manager = MetricsManager()

        manager.record_state_activation("state1")
        manager.record_state_activation("state2")
        manager.record_state_activation("state2")
        manager.record_state_activation("state3")
        manager.record_state_activation("state3")
        manager.record_state_activation("state3")

        most_visited = manager.get_most_visited_states(limit=2)

        assert len(most_visited) == 2
        assert most_visited[0] == ("state3", 3)
        assert most_visited[1] == ("state2", 2)

    def test_get_most_executed_transitions(self) -> None:
        """Test getting most executed transitions."""
        manager = MetricsManager()

        manager.record_transition_execution("t1", True)
        manager.record_transition_execution("t2", True)
        manager.record_transition_execution("t2", False)

        most_executed = manager.get_most_executed_transitions(limit=5)

        assert len(most_executed) == 2
        assert most_executed[0] == ("t2", 2)
        assert most_executed[1] == ("t1", 1)

    def test_get_transition_success_rates(self) -> None:
        """Test getting transition success rates."""
        manager = MetricsManager()

        manager.record_transition_execution("t1", True)
        manager.record_transition_execution("t1", True)
        manager.record_transition_execution("t2", True)
        manager.record_transition_execution("t2", False)

        rates = manager.get_transition_success_rates()

        assert rates["t1"] == 1.0
        assert rates["t2"] == 0.5

    def test_get_currently_active_states(self) -> None:
        """Test getting currently active states."""
        manager = MetricsManager()

        manager.record_state_activation("state1")
        manager.record_state_activation("state2")
        manager.record_state_deactivation("state1")

        active = manager.get_currently_active_states()

        assert "state2" in active
        assert "state1" not in active

    def test_reset_all(self) -> None:
        """Test resetting all metrics."""
        manager = MetricsManager()

        manager.record_state_activation("state1")
        manager.record_transition_execution("trans1", True)

        manager.reset_all()

        s_metrics = manager.get_state_metrics("state1")
        t_metrics = manager.get_transition_metrics("trans1")

        assert s_metrics is not None
        assert t_metrics is not None
        assert s_metrics.visit_count == 0
        assert t_metrics.execution_count == 0

    def test_enable_disable(self) -> None:
        """Test enabling and disabling metrics."""
        manager = MetricsManager(enabled=False)

        manager.record_state_activation("state1")
        assert manager.get_state_metrics("state1") is None

        manager.enable()
        manager.record_state_activation("state2")
        assert manager.get_state_metrics("state2") is not None

        manager.disable()
        manager.record_state_activation("state3")
        assert manager.get_state_metrics("state3") is None

    def test_get_summary(self) -> None:
        """Test getting metrics summary."""
        manager = MetricsManager()

        manager.record_state_activation("state1")
        manager.record_state_activation("state2")
        manager.record_transition_execution("trans1", True)
        manager.record_transition_execution("trans2", False)

        summary = manager.get_summary()

        assert summary["enabled"] is True
        assert summary["states_tracked"] == 2
        assert summary["transitions_tracked"] == 2
        assert summary["total_state_visits"] == 2
        assert summary["total_transition_executions"] == 2
        assert summary["total_successful_transitions"] == 1
        assert summary["overall_success_rate"] == 0.5


class TestStateManagerIntegration:
    """Test metrics integration with StateManager."""

    def test_metrics_disabled_by_default(self) -> None:
        """Test that metrics are disabled by default."""
        manager = StateManager()

        manager.add_state("state1")
        manager.activate_states({"state1"})

        # Metrics should exist but be disabled
        assert manager.metrics.enabled is False

    def test_metrics_enabled_in_config(self) -> None:
        """Test enabling metrics via config."""
        config = StateManagerConfig(enable_metrics=True)
        manager = StateManager(config)

        assert manager.metrics.enabled is True

    def test_state_activation_tracking(self) -> None:
        """Test state activation metrics tracking."""
        config = StateManagerConfig(enable_metrics=True)
        manager = StateManager(config)

        manager.add_state("state1")
        manager.activate_states({"state1"})

        metrics = manager.get_state_metrics("state1")
        assert metrics is not None
        assert metrics.visit_count == 1

    def test_state_deactivation_tracking(self) -> None:
        """Test state deactivation metrics tracking."""
        config = StateManagerConfig(enable_metrics=True)
        manager = StateManager(config)

        manager.add_state("state1")
        manager.activate_states({"state1"})
        manager.deactivate_states({"state1"})

        metrics = manager.get_state_metrics("state1")
        assert metrics is not None
        assert metrics.deactivation_count == 1

    def test_transition_execution_tracking(self) -> None:
        """Test transition execution metrics tracking."""
        config = StateManagerConfig(enable_metrics=True)
        manager = StateManager(config)

        manager.add_state("state1")
        manager.add_state("state2")
        manager.add_transition(
            "trans1", from_states=["state1"], activate_states=["state2"]
        )

        manager.activate_states({"state1"})
        success = manager.execute_transition("trans1")

        assert success
        metrics = manager.get_transition_metrics("trans1")
        assert metrics is not None
        assert metrics.execution_count == 1
        assert metrics.success_count == 1

    def test_transition_timing_tracking(self) -> None:
        """Test transition execution time tracking."""
        config = StateManagerConfig(enable_metrics=True)
        manager = StateManager(config)

        manager.add_state("state1")
        manager.add_state("state2")
        manager.add_transition(
            "trans1", from_states=["state1"], activate_states=["state2"]
        )

        manager.activate_states({"state1"})
        manager.execute_transition("trans1")

        metrics = manager.get_transition_metrics("trans1")
        assert metrics is not None
        assert metrics.total_execution_time > 0.0

    def test_most_visited_states_integration(self) -> None:
        """Test getting most visited states through StateManager."""
        config = StateManagerConfig(enable_metrics=True)
        manager = StateManager(config)

        manager.add_state("state1")
        manager.add_state("state2")
        manager.add_state("state3")

        manager.activate_states({"state1"})
        manager.activate_states({"state2"})
        manager.activate_states({"state2"})
        manager.activate_states({"state3"})

        most_visited = manager.get_most_visited_states(limit=2)

        assert len(most_visited) == 2
        assert most_visited[0][0] == "state2"
        assert most_visited[0][1] == 2

    def test_transition_success_rates_integration(self) -> None:
        """Test getting transition success rates through StateManager."""
        config = StateManagerConfig(enable_metrics=True, allow_invalid_transitions=True)
        manager = StateManager(config)

        manager.add_state("state1")
        manager.add_state("state2")
        manager.add_transition(
            "trans1", from_states=["state1"], activate_states=["state2"]
        )

        # Successful execution
        manager.activate_states({"state1"})
        manager.execute_transition("trans1")

        # Failed execution (wrong state)
        manager.activate_states({"state2"})
        manager.execute_transition("trans1")  # Will fail

        rates = manager.get_transition_success_rates()
        assert "trans1" in rates

    def test_metrics_summary_integration(self) -> None:
        """Test getting metrics summary through StateManager."""
        config = StateManagerConfig(enable_metrics=True)
        manager = StateManager(config)

        manager.add_state("state1")
        manager.add_state("state2")
        manager.add_transition(
            "trans1", from_states=["state1"], activate_states=["state2"]
        )

        manager.activate_states({"state1"})
        manager.execute_transition("trans1")

        summary = manager.get_metrics_summary()

        assert summary["enabled"] is True
        assert summary["states_tracked"] >= 1
        assert summary["transitions_tracked"] == 1

    def test_reset_metrics_integration(self) -> None:
        """Test resetting metrics through StateManager."""
        config = StateManagerConfig(enable_metrics=True)
        manager = StateManager(config)

        manager.add_state("state1")
        manager.activate_states({"state1"})

        manager.reset_metrics()

        metrics = manager.get_state_metrics("state1")
        assert metrics is not None
        assert metrics.visit_count == 0

    def test_enable_disable_metrics_integration(self) -> None:
        """Test dynamically enabling/disabling metrics."""
        manager = StateManager()

        manager.add_state("state1")

        # Start disabled
        manager.activate_states({"state1"})
        metrics1 = manager.get_state_metrics("state1")
        assert metrics1 is None  # No metrics recorded

        # Enable and activate again
        manager.enable_metrics()
        manager.deactivate_states({"state1"})
        manager.activate_states({"state1"})
        metrics2 = manager.get_state_metrics("state1")
        assert metrics2 is not None
        assert metrics2.visit_count == 1

        # Disable and activate again
        manager.disable_metrics()
        manager.deactivate_states({"state1"})
        manager.activate_states({"state1"})
        metrics3 = manager.get_state_metrics("state1")
        assert metrics3 is not None
        assert metrics3.visit_count == 1  # Unchanged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
