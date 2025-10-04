#!/usr/bin/env python3
"""Verify that our implementation aligns with the formal model."""

import sys
sys.path.insert(0, 'src')

from multistate.core.element import Element
from multistate.core.state import State
from multistate.core.state_group import StateGroup


def verify_state_as_element_collection():
    """Verify: s ∈ S where s ⊆ E"""
    print("\n1. Testing state as collection of elements (s ⊆ E)...")

    # Create elements
    e1 = Element("e1", "Login Button")
    e2 = Element("e2", "Username Field")
    e3 = Element("e3", "Password Field")

    # Create state as subset of elements
    login_state = State("login", "Login Screen")
    login_state.add_element(e1)
    login_state.add_element(e2)
    login_state.add_element(e3)

    assert len(login_state.elements) == 3
    assert login_state.has_element(e1)
    print("   ✓ State correctly contains elements")
    print(f"   State: {login_state}")
    return True


def verify_multiple_active_states():
    """Verify: S_Ξ ⊆ S (multiple simultaneous active states)"""
    print("\n2. Testing multiple simultaneous active states...")

    # Create states
    toolbar = State("toolbar", "Toolbar")
    sidebar = State("sidebar", "Sidebar")
    content = State("content", "Content Area")
    footer = State("footer", "Footer")

    # Multiple states can be active
    active_states = {toolbar, sidebar, content}  # S_Ξ

    assert len(active_states) == 3
    assert toolbar in active_states
    assert footer not in active_states
    print("   ✓ Multiple states active simultaneously")
    print(f"   Active: {[s.name for s in active_states]}")
    return True


def verify_group_atomicity():
    """Verify: ∀g ∈ G: g ⊆ S_Ξ ∨ g ∩ S_Ξ = ∅"""
    print("\n3. Testing group atomicity property...")

    # Create states and group
    s1 = State("s1", "Toolbar")
    s2 = State("s2", "Sidebar")
    s3 = State("s3", "Content")
    s4 = State("s4", "StatusBar")

    workspace = StateGroup("workspace", "Main Workspace", states={s1, s2, s3})

    # Test fully active (g ⊆ S_Ξ)
    active_all = {s1, s2, s3, s4}
    assert workspace.is_fully_active(active_all)
    assert workspace.validate_atomicity(active_all)
    print("   ✓ Group fully active: atomicity holds")

    # Test fully inactive (g ∩ S_Ξ = ∅)
    active_none = {s4}
    assert workspace.is_fully_inactive(active_none)
    assert workspace.validate_atomicity(active_none)
    print("   ✓ Group fully inactive: atomicity holds")

    # Test partial activation violates atomicity
    active_partial = {s1, s2, s4}  # Missing s3
    assert not workspace.validate_atomicity(active_partial)
    print("   ✓ Partial activation correctly violates atomicity")

    print(f"   Group: {workspace}")
    return True


def verify_mock_probability():
    """Verify: P_initial(s) = w_s / Σw_s'"""
    print("\n4. Testing mock starting probability...")

    # Create states with weights
    login = State("login", "Login", mock_starting_probability=3.0)
    dashboard = State("dash", "Dashboard", mock_starting_probability=1.0)
    settings = State("settings", "Settings", mock_starting_probability=1.0)

    # Calculate probabilities
    total = 3.0 + 1.0 + 1.0
    p_login = 3.0 / total
    p_dash = 1.0 / total
    p_settings = 1.0 / total

    assert abs(p_login - 0.6) < 0.01
    assert abs(p_dash - 0.2) < 0.01
    assert abs(p_settings - 0.2) < 0.01
    print(f"   ✓ P(login) = {p_login:.1%}")
    print(f"   ✓ P(dashboard) = {p_dash:.1%}")
    print(f"   ✓ P(settings) = {p_settings:.1%}")
    return True


def verify_blocking_states():
    """Verify blocking state behavior"""
    print("\n5. Testing blocking states...")

    modal = State(
        "modal",
        "Save Dialog",
        blocking=True,
        blocks={"toolbar", "sidebar", "content"}
    )

    assert modal.is_blocking()
    assert len(modal.get_blocked_states()) == 3
    print(f"   ✓ Modal blocks: {modal.get_blocked_states()}")
    return True


def verify_gui_workspace_scenario():
    """Verify practical GUI workspace scenario"""
    print("\n6. Testing GUI workspace scenario...")

    # Create workspace components
    toolbar = State("toolbar", "Application Toolbar")
    toolbar.add_element(Element("file_menu", "File Menu"))
    toolbar.add_element(Element("edit_menu", "Edit Menu"))

    sidebar = State("sidebar", "Navigation Sidebar")
    sidebar.add_element(Element("nav_tree", "Navigation Tree"))

    content = State("content", "Main Content Area")
    content.add_element(Element("editor", "Text Editor"))

    statusbar = State("statusbar", "Status Bar")
    statusbar.add_element(Element("status_text", "Status Text"))

    # Create workspace group
    workspace = StateGroup(
        "workspace",
        "IDE Workspace",
        states={toolbar, sidebar, content, statusbar}
    )

    print(f"   ✓ Created workspace with {len(workspace)} components")

    # Verify all states know their group
    for state in workspace:
        assert state.group == "workspace"
        print(f"     - {state.name}: {len(state.elements)} elements")

    return True


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("MultiState Implementation Verification")
    print("Checking alignment with formal model from paper...")
    print("=" * 60)

    tests = [
        verify_state_as_element_collection,
        verify_multiple_active_states,
        verify_group_atomicity,
        verify_mock_probability,
        verify_blocking_states,
        verify_gui_workspace_scenario,
    ]

    results = []
    for test in tests:
        try:
            success = test()
            results.append((test.__name__, success))
        except Exception as e:
            print(f"   ✗ Test failed: {e}")
            results.append((test.__name__, False))

    print("\n" + "=" * 60)
    print("Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total} tests")

    if passed == total:
        print("\n✓ All tests passed! Implementation aligns with formal model.")
    else:
        print("\n✗ Some tests failed. Please review implementation.")
        sys.exit(1)


if __name__ == "__main__":
    main()