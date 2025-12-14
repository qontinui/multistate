#!/usr/bin/env python3
"""Example: Using State References and History

Demonstrates how to use symbolic state references (PREVIOUS, CURRENT, EXPECTED)
and state history tracking in multistate.
"""

import sys

sys.path.insert(0, "src")

from multistate.manager import StateManager, StateManagerConfig
from multistate.state_references import StateReference


def main():
    """Run the state references example."""
    print("=" * 60)
    print("State References Example")
    print("=" * 60)

    # Create manager with history enabled
    config = StateManagerConfig(
        enable_state_history=True,
        max_history_snapshots=50,
        log_transitions=True,
    )
    manager = StateManager(config)

    # Define application states
    print("\nSetting up application states...")
    manager.add_state("login", "Login Screen")
    manager.add_state("main_menu", "Main Menu")
    manager.add_state("toolbar", "Toolbar")
    manager.add_state("sidebar", "Sidebar")
    manager.add_state("editor", "Code Editor")
    manager.add_state("console", "Debug Console")

    # Define transitions
    print("Defining transitions...")
    manager.add_transition(
        "login_success",
        name="Successful Login",
        from_states=["login"],
        activate_states=["main_menu"],
        exit_states=["login"],
    )

    manager.add_transition(
        "open_workspace",
        name="Open Workspace",
        from_states=["main_menu"],
        activate_states=["toolbar", "sidebar", "editor"],
    )

    manager.add_transition(
        "toggle_console",
        name="Toggle Debug Console",
        from_states=["editor"],
        activate_states=["console"],
    )

    # Start at login
    print("\n--- Initial State ---")
    manager.activate_states({"login"})
    print(f"Active states: {manager.get_active_states()}")

    # Use CURRENT reference
    print("\n--- Using StateReference.CURRENT ---")
    current = manager.resolve_state_reference(StateReference.CURRENT)
    print(f"Current states: {[s.name for s in current]}")

    # Execute login transition
    print("\n--- Executing Login Transition ---")
    manager.execute_transition("login_success")
    print(f"Active states: {manager.get_active_states()}")

    # Use PREVIOUS reference to see where we came from
    print("\n--- Using StateReference.PREVIOUS ---")
    previous = manager.resolve_state_reference(StateReference.PREVIOUS)
    print(f"Previous states: {[s.name for s in previous]}")

    # Check state changes
    print("\n--- Analyzing State Changes ---")
    added, removed = manager.get_state_changes()
    print(f"States added: {added}")
    print(f"States removed: {removed}")

    # Open workspace
    print("\n--- Opening Workspace ---")
    manager.execute_transition("open_workspace")
    print(f"Active states: {manager.get_active_states()}")

    # Check multi-state transition
    current = manager.resolve_state_reference(StateReference.CURRENT)
    print(f"Current states: {[s.name for s in current]}")

    # Toggle console
    print("\n--- Toggling Console ---")
    manager.execute_transition("toggle_console")
    print(f"Active states: {manager.get_active_states()}")

    # Look back through history
    print("\n--- Examining History ---")
    print(f"Total history snapshots: {manager.get_history_length()}")

    # Get states from 2 transitions ago
    two_back = manager.get_previous_states(offset=2)
    print(f"States 2 transitions ago: {[s.name for s in two_back]}")

    # Check which transitions led to certain states
    print("\n--- Transition Tracking ---")
    main_menu_transitions = manager.state_history.get_transitions_to_state("main_menu")
    print(f"Transitions that activated main_menu: {main_menu_transitions}")

    editor_transitions = manager.state_history.get_transitions_to_state("editor")
    print(f"Transitions that activated editor: {editor_transitions}")

    # Summary
    print("\n" + "=" * 60)
    print("Example Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. StateReference.CURRENT - Get currently active states")
    print("2. StateReference.PREVIOUS - Get previously active states")
    print("3. StateReference.EXPECTED - Get states expected to activate next")
    print("4. State history tracks all state changes automatically")
    print("5. You can look back through history with offset parameter")
    print("6. Track which transitions led to state activations")


if __name__ == "__main__":
    main()
