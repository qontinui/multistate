#!/usr/bin/env python3
"""Example demonstrating StaysVisible functionality.

This example shows how to control state visibility during transitions,
which is useful for managing GUI states where some UI elements should
remain visible while navigating to new states.
"""

import sys
from pathlib import Path

# Add src to path for running directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from multistate.core.state import State
from multistate.transitions import StaysVisible, Transition, TransitionExecutor


def main() -> None:
    """Demonstrate visibility control in state transitions."""

    print("=" * 60)
    print("StaysVisible Example - State Visibility Control")
    print("=" * 60)

    # Create states representing a GUI application
    main_menu = State("main_menu", "Main Menu")
    settings = State("settings", "Settings Panel")
    modal = State("modal", "Modal Dialog")

    # Example 1: Modal that keeps parent visible (StaysVisible.TRUE)
    print("\n1. Opening modal - parent stays visible")
    print("   Use case: Modal dialog over main menu")

    open_modal = Transition(
        id="open_modal",
        name="Open Modal",
        from_states={main_menu},
        activate_states={modal},
        stays_visible=StaysVisible.TRUE,  # main_menu stays visible behind modal
    )

    executor = TransitionExecutor()
    result = executor.execute(open_modal, {main_menu})

    print(f"   Transition success: {result.success}")
    print(f"   Activated states: {[s.name for s in result.activated_states]}")

    # Find visibility phase result
    for phase_result in result.phase_results:
        if phase_result.phase.value == "visibility":
            print(f"   Visibility setting: {phase_result.data['stays_visible']}")
            states_to_show = phase_result.data["states_to_show"]
            show_ids = [main_menu.id if main_menu.id in states_to_show else None]
            print(f"   States to show: {show_ids}")

    # Example 2: Navigation that hides previous state (StaysVisible.FALSE)
    print("\n2. Opening settings - main menu hides")
    print("   Use case: Full screen transition")

    open_settings = Transition(
        id="open_settings",
        name="Open Settings",
        from_states={main_menu},
        activate_states={settings},
        stays_visible=StaysVisible.FALSE,  # main_menu gets hidden
    )

    result = executor.execute(open_settings, {main_menu})

    print(f"   Transition success: {result.success}")
    print(f"   Activated states: {[s.name for s in result.activated_states]}")

    for phase_result in result.phase_results:
        if phase_result.phase.value == "visibility":
            print(f"   Visibility setting: {phase_result.data['stays_visible']}")
            states_to_hide = phase_result.data["states_to_hide"]
            hide_ids = [main_menu.id if main_menu.id in states_to_hide else None]
            print(f"   States to hide: {hide_ids}")

    # Example 3: Default behavior (StaysVisible.NONE)
    print("\n3. Default behavior - inherits from container")
    print("   Use case: Let parent state manager decide")

    default_transition = Transition(
        id="default",
        name="Default Transition",
        from_states={settings},
        activate_states={main_menu},
        stays_visible=StaysVisible.NONE,  # Default - inherit behavior
    )

    result = executor.execute(default_transition, {settings})

    print(f"   Transition success: {result.success}")
    for phase_result in result.phase_results:
        if phase_result.phase.value == "visibility":
            print(f"   Visibility setting: {phase_result.data['stays_visible']}")
            print("   No explicit visibility changes")

    # Example 4: Serialization
    print("\n4. Serialization to JSON")

    transition_dict = open_modal.to_dict()
    print(f"   Transition ID: {transition_dict['id']}")
    print(f"   Stays Visible: {transition_dict['stays_visible']}")
    print(f"   From States: {transition_dict['from_states']}")
    print(f"   Activate States: {transition_dict['activate_states']}")

    print("\n" + "=" * 60)
    print("Summary:")
    print("- StaysVisible.TRUE: Source states remain visible")
    print("- StaysVisible.FALSE: Source states become hidden")
    print("- StaysVisible.NONE: Inherit from parent container")
    print("=" * 60)


if __name__ == "__main__":
    main()
