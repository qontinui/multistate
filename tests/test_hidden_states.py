#!/usr/bin/env python3
"""Test hidden states and dynamic transitions."""

import sys
sys.path.insert(0, 'src')

from multistate.core.state import State
from multistate.dynamics.hidden_states import (
    HiddenStateManager,
    OcclusionType,
    OcclusionRelation,
    DynamicTransition
)


def test_modal_occlusion():
    """Test modal dialog occlusion."""
    print("\n" + "="*60)
    print("Test 1: Modal Occlusion")
    print("="*60)
    
    manager = HiddenStateManager()
    
    # Create states
    main_window = State("main", "Main Window")
    sidebar = State("sidebar", "Sidebar")
    modal_dialog = State("modal", "Modal Dialog", blocking=True)
    
    # Check occlusion with modal active
    active = {main_window, sidebar, modal_dialog}
    occlusions = manager.detect_occlusion(active)
    
    # Modal should occlude non-blocking states
    assert len(occlusions) == 2  # Modal occludes main and sidebar
    
    occluded_states = {o.hidden_state.id for o in occlusions}
    assert "main" in occluded_states
    assert "sidebar" in occluded_states
    
    print("✓ Modal dialog correctly occludes other states")
    return True


def test_spatial_occlusion():
    """Test spatial overlap occlusion."""
    print("\n" + "="*60)
    print("Test 2: Spatial Occlusion")
    print("="*60)
    
    manager = HiddenStateManager()
    
    # Create overlapping states
    dropdown = State("dropdown", "Dropdown Menu")
    button = State("button", "Button")
    
    # Spatial info with overlap
    spatial_info = {
        "dropdown": {
            "z_order": 10,
            "bounds": {"left": 100, "top": 100, "right": 300, "bottom": 400}
        },
        "button": {
            "z_order": 5,
            "bounds": {"left": 150, "top": 150, "right": 250, "bottom": 200}
        }
    }
    
    active = {dropdown, button}
    occlusions = manager.detect_occlusion(active, spatial_info)
    
    # Dropdown (higher z-order) should occlude button
    assert len(occlusions) == 1
    occlusion = list(occlusions)[0]
    assert occlusion.covering_state.id == "dropdown"
    assert occlusion.hidden_state.id == "button"
    assert occlusion.occlusion_type == OcclusionType.SPATIAL
    
    print("✓ Spatial occlusion detected correctly")
    return True


def test_reveal_transition():
    """Test dynamic reveal transition generation."""
    print("\n" + "="*60)
    print("Test 3: Reveal Transition Generation")
    print("="*60)
    
    manager = HiddenStateManager()
    
    # Setup occlusion scenario
    main = State("main", "Main")
    popup = State("popup", "Popup", blocking=True)
    hidden1 = State("hidden1", "Hidden 1")
    hidden2 = State("hidden2", "Hidden 2")
    
    # Popup covers hidden states
    active = {main, popup, hidden1, hidden2}
    manager.update_occlusions(active)
    
    # Generate reveal transition
    reveal_trans = manager.generate_reveal_transition(
        covering_state=popup,
        hidden_states={hidden1, hidden2},
        current_time=1.0
    )
    
    assert reveal_trans.id.startswith("reveal_")
    assert popup in reveal_trans.from_states
    assert hidden1 in reveal_trans.activate_states
    assert hidden2 in reveal_trans.activate_states
    assert popup in reveal_trans.exit_states
    assert reveal_trans.path_cost == 0.1  # Reveal is cheap
    
    print(f"✓ Generated reveal transition: {reveal_trans.name}")
    return True


def test_self_transition():
    """Test self-transition generation."""
    print("\n" + "="*60)
    print("Test 4: Self-Transition")
    print("="*60)
    
    manager = HiddenStateManager()
    
    # Create state that needs refresh
    form = State("form", "Input Form")
    
    # Generate self-transition for refresh
    self_trans = manager.generate_self_transition(
        state=form,
        action="refresh",
        current_time=2.0
    )
    
    assert self_trans.is_self_transition
    assert form in self_trans.from_states
    assert form in self_trans.activate_states
    assert len(self_trans.exit_states) == 0  # Don't exit
    assert self_trans.trigger_condition == "Self-transition for refresh"
    
    print(f"✓ Generated self-transition: {self_trans.name}")
    return True


def test_occlusion_updates():
    """Test tracking occlusion changes over time."""
    print("\n" + "="*60)
    print("Test 5: Occlusion Updates")
    print("="*60)
    
    manager = HiddenStateManager()
    
    # Initial state
    main = State("main", "Main")
    sidebar = State("sidebar", "Sidebar")
    active = {main, sidebar}
    
    newly_occluded, newly_revealed = manager.update_occlusions(active)
    assert len(newly_occluded) == 0
    assert len(newly_revealed) == 0
    
    # Add modal dialog
    modal = State("modal", "Modal", blocking=True)
    active.add(modal)
    
    newly_occluded, newly_revealed = manager.update_occlusions(active)
    assert len(newly_occluded) == 2  # Modal occludes main and sidebar
    assert len(newly_revealed) == 0
    
    # Remove modal
    active.remove(modal)
    
    newly_occluded, newly_revealed = manager.update_occlusions(active)
    assert len(newly_occluded) == 0
    assert len(newly_revealed) == 2  # Main and sidebar revealed
    
    print("✓ Occlusion tracking updates correctly")
    return True


def test_dynamic_transition_expiration():
    """Test that dynamic transitions can expire."""
    print("\n" + "="*60)
    print("Test 6: Dynamic Transition Expiration")
    print("="*60)
    
    manager = HiddenStateManager()
    
    # Create temporary transition
    state_a = State("a", "State A")
    state_b = State("b", "State B")
    
    temp_trans = DynamicTransition(
        id="temp_trans",
        name="Temporary",
        from_states={state_a},
        activate_states={state_b},
        created_at=1.0,
        expires_at=5.0  # Expires at time 5
    )
    
    manager.add_dynamic_transition(temp_trans)
    
    # Before expiration
    valid = manager.get_dynamic_transitions({state_a}, current_time=3.0)
    assert len(valid) == 1
    
    # After expiration
    valid = manager.get_dynamic_transitions({state_a}, current_time=6.0)
    assert len(valid) == 0
    
    # Cleanup expired
    removed = manager.cleanup_expired(current_time=6.0)
    assert removed == 1
    
    print("✓ Dynamic transitions expire correctly")
    return True


def test_complex_gui_scenario():
    """Test a complex GUI automation scenario."""
    print("\n" + "="*60)
    print("Test 7: Complex GUI Scenario")
    print("="*60)
    
    manager = HiddenStateManager()
    
    # Create GUI states
    main_window = State("main_window", "Main Window")
    menu_bar = State("menu_bar", "Menu Bar")
    file_menu = State("file_menu", "File Menu")
    edit_menu = State("edit_menu", "Edit Menu") 
    dropdown = State("dropdown", "Dropdown", blocking=True, blocks={"menu_bar"})
    tooltip = State("tooltip", "Tooltip")
    modal = State("save_dialog", "Save Dialog", blocking=True)
    
    # Register self-transitions for menus (can click to refresh)
    manager.register_self_transition(file_menu, "click")
    manager.register_self_transition(edit_menu, "click")
    
    # Scenario 1: Dropdown covers menu bar
    print("\nScenario 1: Dropdown menu open")
    active = {main_window, menu_bar, dropdown}
    newly_occluded, _ = manager.update_occlusions(active)
    
    assert len(manager.covering_to_hidden) == 1
    assert "menu_bar" in manager.covering_to_hidden["dropdown"]
    print("  ✓ Dropdown occludes menu bar")
    
    # Get dynamic transitions
    transitions = manager.get_dynamic_transitions(active)
    reveal_transitions = [t for t in transitions if t.id.startswith("reveal_")]
    assert len(reveal_transitions) == 1
    print(f"  ✓ Reveal transition available: {reveal_transitions[0].name}")
    
    # Scenario 2: Modal dialog blocks everything
    print("\nScenario 2: Modal dialog open")
    active = {main_window, menu_bar, file_menu, modal}
    newly_occluded, _ = manager.update_occlusions(active)
    
    occluded = {o.hidden_state.id for o in manager.occlusions}
    assert "main_window" in occluded
    assert "menu_bar" in occluded
    assert "file_menu" in occluded
    print("  ✓ Modal blocks all non-modal states")
    
    # Scenario 3: Self-transitions available
    print("\nScenario 3: Self-transitions")
    active = {main_window, file_menu}
    transitions = manager.get_dynamic_transitions(active)
    self_transitions = [t for t in transitions if t.is_self_transition]
    
    assert len(self_transitions) >= 1
    assert any("file_menu" in t.id for t in self_transitions)
    print("  ✓ Self-transitions available for menus")
    
    print("\n✓ Complex GUI scenario handled correctly")
    return True


def demonstrate_theoretical_extensions():
    """Demonstrate how this extends the formal model."""
    print("\n" + "="*60)
    print("Theoretical Model Extensions")
    print("="*60)
    
    print("""
The hidden states and dynamic transitions extend the formal model:

1. OCCLUSION RELATION: ω: S × S → {0,1}
   - Captures which states hide others at runtime
   - Types: Modal, Spatial, Logical
   - Example: ω(modal_dialog, main_window) = 1

2. DYNAMIC TRANSITION GENERATION: f_dyn: Ξ → P(T)
   - Creates transitions based on runtime state
   - Reveal transitions when covering state closes
   - Example: close(modal) → reveal(hidden_states)

3. SELF-TRANSITIONS: t_self where from_states = activate_states
   - Useful for refresh, retry, validation
   - Maintains state while executing action
   - Example: refresh(form) → form

4. TEMPORAL TRANSITIONS: t.expires_at
   - Transitions can have limited lifetime
   - Enables temporary UI behaviors
   - Example: tooltip_dismiss expires after 5s

These are GENERAL concepts applicable to:
- GUI automation (Brobot's use case)
- Game state management (fog of war, UI layers)
- Workflow systems (temporary states, rollback)
- Microservices (circuit breaker patterns)
    """)


def main():
    """Run all hidden state tests."""
    print("#"*60)
    print("# Hidden States and Dynamic Transitions Tests")
    print("#"*60)
    
    tests = [
        test_modal_occlusion,
        test_spatial_occlusion,
        test_reveal_transition,
        test_self_transition,
        test_occlusion_updates,
        test_dynamic_transition_expiration,
        test_complex_gui_scenario,
    ]
    
    results = []
    for test in tests:
        try:
            success = test()
            results.append((test.__name__, success))
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
    
    # Show theoretical extensions
    demonstrate_theoretical_extensions()
    
    # Summary
    print("\n" + "#"*60)
    print("# Summary")
    print("#"*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All hidden state tests passed!")
        print("\nKey achievements:")
        print("- Occlusion detection (modal and spatial)")
        print("- Dynamic reveal transition generation")
        print("- Self-transitions for state refresh")
        print("- Temporal transitions with expiration")
        print("- Complex GUI scenario handling")
        print("\nThis extends MultiState with runtime dynamics!")


if __name__ == "__main__":
    main()