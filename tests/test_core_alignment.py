"""Test that implementation aligns with formal model from paper.

These tests verify that our implementation correctly follows the
mathematical definitions from the Model-based GUI Automation paper.
"""

import pytest
from typing import Set

from multistate.core.element import Element
from multistate.core.state import State
from multistate.core.state_group import StateGroup


class TestFormalModelAlignment:
    """Verify implementation matches formal mathematical model."""

    def test_state_is_subset_of_elements(self):
        """Test: s ∈ S where s ⊆ E (state is collection of elements)"""
        # Create elements (E)
        e1 = Element("e1", "Button")
        e2 = Element("e2", "Input Field")
        e3 = Element("e3", "Label")

        # Create state as subset of E
        s = State("s1", "Login Form")
        s.add_element(e1)
        s.add_element(e2)

        # Verify s ⊆ E
        assert s.has_element(e1)
        assert s.has_element(e2)
        assert not s.has_element(e3)
        assert len(s.elements) == 2

    def test_multiple_active_states(self):
        """Test: S_Ξ ⊆ S (multiple states can be active simultaneously)"""
        # Create states (S)
        s1 = State("s1", "Toolbar")
        s2 = State("s2", "Sidebar")
        s3 = State("s3", "Content")
        s4 = State("s4", "Footer")

        # Active states S_Ξ ⊆ S
        S_Xi: Set[State] = {s1, s2, s3}  # Multiple active states

        # Verify multiple states active
        assert len(S_Xi) == 3
        assert s1 in S_Xi
        assert s2 in S_Xi
        assert s3 in S_Xi
        assert s4 not in S_Xi  # Not all states must be active

    def test_group_membership_function(self):
        """Test: γ: G → P(S) (group membership function)"""
        # Create states
        s1 = State("s1", "Toolbar")
        s2 = State("s2", "Sidebar")
        s3 = State("s3", "Content")

        # Create group g ∈ G
        g = StateGroup("g1", "Workspace", states={s1, s2, s3})

        # Verify γ(g) = {s1, s2, s3}
        assert len(g.states) == 3
        assert s1 in g.states
        assert s2 in g.states
        assert s3 in g.states

        # Verify each state knows its group
        assert s1.group == "g1"
        assert s2.group == "g1"
        assert s3.group == "g1"

    def test_group_atomicity_property(self):
        """Test: ∀g ∈ G: g ⊆ S_Ξ ∨ g ∩ S_Ξ = ∅ (atomicity)"""
        # Create states and group
        s1 = State("s1", "Toolbar")
        s2 = State("s2", "Sidebar")
        s3 = State("s3", "Content")
        s4 = State("s4", "Footer")
        g = StateGroup("g1", "Workspace", states={s1, s2, s3})

        # Case 1: Group fully active (g ⊆ S_Ξ)
        active_states_1 = {s1, s2, s3, s4}
        assert g.is_fully_active(active_states_1)
        assert g.validate_atomicity(active_states_1)

        # Case 2: Group fully inactive (g ∩ S_Ξ = ∅)
        active_states_2 = {s4}
        assert g.is_fully_inactive(active_states_2)
        assert g.validate_atomicity(active_states_2)

        # Case 3: Partial activation violates atomicity
        active_states_3 = {s1, s2, s4}  # Only 2 of 3 group states
        assert not g.is_fully_active(active_states_3)
        assert not g.is_fully_inactive(active_states_3)
        assert not g.validate_atomicity(active_states_3)

    def test_mock_starting_probability(self):
        """Test: P_initial(s) = w_s / Σw_s' (initial state selection)"""
        # Create initial states with weights
        s1 = State("s1", "Login", mock_starting_probability=2.0)
        s2 = State("s2", "Dashboard", mock_starting_probability=1.0)
        s3 = State("s3", "Settings", mock_starting_probability=1.0)

        # Calculate probabilities
        total_weight = s1.mock_starting_probability + s2.mock_starting_probability + s3.mock_starting_probability
        p1 = s1.mock_starting_probability / total_weight
        p2 = s2.mock_starting_probability / total_weight
        p3 = s3.mock_starting_probability / total_weight

        # Verify probability distribution
        assert p1 == 0.5  # 2.0 / 4.0
        assert p2 == 0.25  # 1.0 / 4.0
        assert p3 == 0.25  # 1.0 / 4.0
        assert p1 + p2 + p3 == 1.0  # Probabilities sum to 1

    def test_blocking_states(self):
        """Test: s_b ∈ S_Ξ ⟹ target(t) ∩ B(s_b) = ∅ (blocking)"""
        # Create states
        modal = State("modal", "Modal Dialog", blocking=True, blocks={"toolbar", "sidebar"})
        toolbar = State("toolbar", "Toolbar")
        sidebar = State("sidebar", "Sidebar")
        footer = State("footer", "Footer")

        # When modal is active, it blocks certain states
        assert modal.is_blocking()
        assert "toolbar" in modal.get_blocked_states()
        assert "sidebar" in modal.get_blocked_states()
        assert "footer" not in modal.get_blocked_states()

    def test_path_cost_function(self):
        """Test: c_S: S → ℝ (state cost function)"""
        # Create states with different costs
        s1 = State("s1", "Easy State", path_cost=1.0)
        s2 = State("s2", "Normal State", path_cost=2.0)
        s3 = State("s3", "Expensive State", path_cost=10.0)

        # Verify costs
        assert s1.path_cost == 1.0
        assert s2.path_cost == 2.0
        assert s3.path_cost == 10.0

        # Cost should influence pathfinding (lower is better)
        states_by_cost = sorted([s1, s2, s3], key=lambda s: s.path_cost)
        assert states_by_cost == [s1, s2, s3]


class TestPracticalScenarios:
    """Test practical use cases that demonstrate the model."""

    def test_gui_workspace_scenario(self):
        """Test a typical GUI workspace with multiple components."""
        # Create elements for each component
        toolbar_button = Element("tb_btn", "Toolbar Button")
        toolbar_menu = Element("tb_menu", "Toolbar Menu")
        sidebar_panel = Element("sb_panel", "Sidebar Panel")
        content_area = Element("cnt_area", "Content Area")

        # Create states representing UI components
        toolbar = State("toolbar", "Toolbar")
        toolbar.add_element(toolbar_button)
        toolbar.add_element(toolbar_menu)

        sidebar = State("sidebar", "Sidebar")
        sidebar.add_element(sidebar_panel)

        content = State("content", "Content")
        content.add_element(content_area)

        # Group them as workspace
        workspace = StateGroup(
            "workspace",
            "Main Workspace",
            states={toolbar, sidebar, content}
        )

        # Verify workspace structure
        assert len(workspace) == 3
        assert toolbar.group == "workspace"
        assert sidebar.group == "workspace"
        assert content.group == "workspace"

        # Simulate activation - all must activate together
        active_states = set()

        # Attempting partial activation violates atomicity
        active_states.add(toolbar)
        assert not workspace.validate_atomicity(active_states)

        # Full activation satisfies atomicity
        active_states.update({sidebar, content})
        assert workspace.validate_atomicity(active_states)

    def test_modal_dialog_scenario(self):
        """Test blocking modal dialog scenario."""
        # Create main UI states
        main_menu = State("main_menu", "Main Menu")
        toolbar = State("toolbar", "Toolbar")
        content = State("content", "Content")

        # Create blocking modal
        modal = State(
            "modal",
            "Save Dialog",
            blocking=True,
            blocks={"toolbar", "content"}
        )

        # Before modal: normal states active
        active_states = {main_menu, toolbar, content}
        assert len(active_states) == 3

        # Modal appears
        active_states.add(modal)

        # Check what should be blocked
        blocked_ids = modal.get_blocked_states()
        states_to_hide = [s for s in active_states if s.id in blocked_ids]

        assert toolbar in states_to_hide
        assert content in states_to_hide
        assert main_menu not in states_to_hide  # Menu stays visible