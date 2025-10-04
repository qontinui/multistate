#!/usr/bin/env python3
"""GUI Workspace Example - Demonstrates MultiState in action.

This example shows a realistic GUI application with:
- Multiple simultaneous active states
- State groups that activate/deactivate atomically
- Blocking modal dialogs
- Incoming transitions for initialization
- Multi-state pathfinding (to be added)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dataclasses import dataclass
from typing import Set, Optional
from multistate.core.element import Element
from multistate.core.state import State
from multistate.core.state_group import StateGroup
from multistate.transitions.transition import (
    Transition,
    IncomingTransition,
    TransitionPhase,
)
from multistate.transitions.executor import TransitionExecutor, SuccessPolicy


class GUIWorkspaceDemo:
    """Demonstrates a complete GUI workspace with MultiState."""

    def __init__(self):
        """Initialize the GUI workspace demo."""
        self.executor = TransitionExecutor(
            success_policy=SuccessPolicy.STRICT,
            strict_mode=True
        )
        self.active_states: Set[State] = set()
        self.incoming_registry = {}

        # Create all states
        self._create_states()

        # Create state groups
        self._create_groups()

        # Create transitions
        self._create_transitions()

        # Register incoming transitions
        self._register_incoming_transitions()

        # Track execution for demonstration
        self.execution_log = []

    def _create_states(self):
        """Create all GUI states."""
        print("Creating GUI states...")

        # Login/Splash states
        self.splash = State("splash", "Splash Screen",
                           mock_starting_probability=3.0)
        self.login = State("login", "Login Screen",
                          mock_starting_probability=1.0)

        # Main window
        self.main_window = State("main_window", "Main Window Frame")

        # Menu bar
        self.menu_bar = State("menu_bar", "Application Menu Bar")
        self.menu_bar.add_element(Element("file_menu", "File Menu"))
        self.menu_bar.add_element(Element("edit_menu", "Edit Menu"))
        self.menu_bar.add_element(Element("view_menu", "View Menu"))

        # Workspace components (will be grouped)
        self.toolbar = State("toolbar", "Application Toolbar")
        self.toolbar.add_element(Element("new_button", "New"))
        self.toolbar.add_element(Element("open_button", "Open"))
        self.toolbar.add_element(Element("save_button", "Save"))

        self.sidebar = State("sidebar", "Navigation Sidebar")
        self.sidebar.add_element(Element("file_tree", "File Explorer"))
        self.sidebar.add_element(Element("search_panel", "Search"))

        self.editor = State("editor", "Code Editor")
        self.editor.add_element(Element("text_area", "Editor Area"))
        self.editor.add_element(Element("line_numbers", "Line Numbers"))

        self.console = State("console", "Console Panel")
        self.console.add_element(Element("output_area", "Console Output"))
        self.console.add_element(Element("input_field", "Console Input"))

        self.statusbar = State("statusbar", "Status Bar")
        self.statusbar.add_element(Element("status_text", "Status Message"))
        self.statusbar.add_element(Element("line_col", "Line:Column"))

        # Modal dialogs (blocking)
        self.save_dialog = State(
            "save_dialog",
            "Save File Dialog",
            blocking=True,
            blocks={"toolbar", "sidebar", "editor", "console"}
        )

        self.settings_dialog = State(
            "settings_dialog",
            "Settings Dialog",
            blocking=True,
            blocks={"toolbar", "sidebar", "editor", "console"}
        )

        self.error_dialog = State(
            "error_dialog",
            "Error Dialog",
            blocking=True,
            blocks={"toolbar", "sidebar", "editor", "console", "menu_bar"}
        )

        print(f"  Created {14} states")

    def _create_groups(self):
        """Create state groups for coordinated activation."""
        print("\nCreating state groups...")

        # Main workspace group - all activate together
        self.workspace_group = StateGroup(
            "workspace",
            "IDE Workspace",
            states={self.toolbar, self.sidebar, self.editor,
                   self.console, self.statusbar}
        )

        # Main UI group - includes menu and window
        self.main_ui_group = StateGroup(
            "main_ui",
            "Main UI Components",
            states={self.main_window, self.menu_bar}
        )

        print(f"  Workspace group: {len(self.workspace_group)} states")
        print(f"  Main UI group: {len(self.main_ui_group)} states")

    def _create_transitions(self):
        """Create all transitions between states."""
        print("\nCreating transitions...")

        # Splash to login
        self.splash_to_login = Transition(
            id="splash_to_login",
            name="Splash Complete",
            from_states={self.splash},
            activate_states={self.login},
            exit_states={self.splash},
            action=lambda: self._log_action("Splash screen timeout")
        )

        # Login to main application
        self.login_success = Transition(
            id="login_success",
            name="Login Successful",
            from_states={self.login},
            activate_groups={self.main_ui_group, self.workspace_group},
            exit_states={self.login},
            action=lambda: self._log_action("User authenticated")
        )

        # Show save dialog
        self.show_save_dialog = Transition(
            id="show_save_dialog",
            name="Show Save Dialog",
            from_states={self.editor},  # Can only save when editor is active
            activate_states={self.save_dialog},
            action=lambda: self._log_action("Opening save dialog")
        )

        # Close save dialog
        self.close_save_dialog = Transition(
            id="close_save_dialog",
            name="Close Save Dialog",
            from_states={self.save_dialog},
            exit_states={self.save_dialog},
            action=lambda: self._log_action("Save dialog closed")
        )

        # Show settings
        self.show_settings = Transition(
            id="show_settings",
            name="Show Settings",
            from_states={self.menu_bar},
            activate_states={self.settings_dialog},
            action=lambda: self._log_action("Opening settings")
        )

        # Close settings
        self.close_settings = Transition(
            id="close_settings",
            name="Close Settings",
            from_states={self.settings_dialog},
            exit_states={self.settings_dialog},
            action=lambda: self._log_action("Settings closed")
        )

        # Error occurred
        self.show_error = Transition(
            id="show_error",
            name="Show Error",
            from_states=set(),  # Can happen from any state
            activate_states={self.error_dialog},
            action=lambda: self._log_action("ERROR OCCURRED!")
        )

        # Logout
        self.logout = Transition(
            id="logout",
            name="Logout",
            from_states={self.menu_bar},
            activate_states={self.login},
            exit_groups={self.main_ui_group, self.workspace_group},
            action=lambda: self._log_action("User logged out")
        )

        print("  Created 8 transitions")

    def _register_incoming_transitions(self):
        """Register incoming transitions for state initialization."""
        print("\nRegistering incoming transitions...")

        # Incoming for workspace states
        def init_toolbar():
            self._log_action("  → Initializing toolbar buttons")

        def init_sidebar():
            self._log_action("  → Loading file tree")

        def init_editor():
            self._log_action("  → Setting up editor workspace")

        def init_console():
            self._log_action("  → Starting console process")

        def init_statusbar():
            self._log_action("  → Updating status information")

        def init_menu():
            self._log_action("  → Building menu structure")

        def init_main_window():
            self._log_action("  → Creating main window")

        # Register incoming transitions
        self.incoming_registry = {
            "toolbar": IncomingTransition("toolbar", init_toolbar),
            "sidebar": IncomingTransition("sidebar", init_sidebar),
            "editor": IncomingTransition("editor", init_editor),
            "console": IncomingTransition("console", init_console),
            "statusbar": IncomingTransition("statusbar", init_statusbar),
            "menu_bar": IncomingTransition("menu_bar", init_menu),
            "main_window": IncomingTransition("main_window", init_main_window),
        }

        print(f"  Registered {len(self.incoming_registry)} incoming transitions")

    def _log_action(self, message: str):
        """Log an action for demonstration."""
        self.execution_log.append(message)
        print(f"    {message}")
        return True  # For transition actions

    def execute_transition(self, transition: Transition) -> bool:
        """Execute a transition and update active states."""
        print(f"\n{'='*60}")
        print(f"Executing: {transition.name}")
        print(f"{'='*60}")

        print(f"Current active states: {self._format_states(self.active_states)}")
        print(f"States to activate: {self._format_states(transition.get_all_states_to_activate())}")
        print(f"States to exit: {self._format_states(transition.get_all_states_to_exit())}")

        result = self.executor.execute(
            transition,
            self.active_states,
            self.incoming_registry
        )

        if result.success:
            # Update our active states based on result
            self.active_states.update(result.activated_states)
            self.active_states.difference_update(result.deactivated_states)
            print(f"\n✓ Transition successful")
        else:
            failed_phase = result.get_failed_phase()
            print(f"\n✗ Transition failed at phase: {failed_phase}")
            for phase_result in result.phase_results:
                if not phase_result.success:
                    print(f"  Reason: {phase_result.message}")

        print(f"New active states: {self._format_states(self.active_states)}")

        return result.success

    def _format_states(self, states: Set[State]) -> str:
        """Format a set of states for display."""
        if not states:
            return "[]"
        return f"[{', '.join(s.name for s in states)}]"

    def verify_group_atomicity(self):
        """Verify that all groups maintain atomicity."""
        print("\n" + "="*60)
        print("Verifying Group Atomicity")
        print("="*60)

        groups = [self.workspace_group, self.main_ui_group]

        for group in groups:
            is_valid = group.validate_atomicity(self.active_states)
            if is_valid:
                if group.is_fully_active(self.active_states):
                    print(f"✓ {group.name}: Fully active (all {len(group)} states)")
                else:
                    print(f"✓ {group.name}: Fully inactive")
            else:
                active_in_group = [s for s in group.states if s in self.active_states]
                print(f"✗ {group.name}: ATOMICITY VIOLATED! "
                      f"{len(active_in_group)}/{len(group)} states active")

    def demonstrate_blocking(self):
        """Demonstrate blocking state behavior."""
        print("\n" + "="*60)
        print("Demonstrating Blocking States")
        print("="*60)

        # Try to show save dialog while editor is active
        if self.execute_transition(self.show_save_dialog):
            print("\nSave dialog is now blocking other states:")
            for state in self.active_states:
                if state.blocking:
                    print(f"  {state.name} blocks: {state.get_blocked_states()}")

            # Try to activate toolbar (should fail - it's blocked)
            test_transition = Transition(
                id="test",
                name="Try to activate toolbar",
                from_states=set(),
                activate_states={self.toolbar}
            )

            print("\nAttempting to activate blocked toolbar...")
            if not self.execute_transition(test_transition):
                print("  → Correctly prevented by blocking state!")

            # Close the dialog
            self.execute_transition(self.close_save_dialog)

    def run_demo(self):
        """Run the complete demonstration."""
        print("\n" + "#"*60)
        print("# MultiState GUI Workspace Demonstration")
        print("#"*60)

        # Start with splash
        self.active_states.add(self.splash)
        print(f"\nInitial state: {self._format_states(self.active_states)}")

        # Splash → Login
        self.execute_transition(self.splash_to_login)

        # Login → Main Application (activates 7 states!)
        self.execute_transition(self.login_success)

        # Verify groups are atomic
        self.verify_group_atomicity()

        # Demonstrate blocking dialog
        self.demonstrate_blocking()

        # Show settings
        self.execute_transition(self.show_settings)

        # Close settings
        self.execute_transition(self.close_settings)

        # Simulate error
        self.execute_transition(self.show_error)

        # Can't do much while error is showing (most things blocked)
        print("\nError dialog is blocking most operations...")

        # Would need to close error to continue (not implemented)

        print("\n" + "#"*60)
        print("# Demo Complete")
        print("#"*60)

        print(f"\nFinal active states: {self._format_states(self.active_states)}")
        print(f"\nExecution log ({len(self.execution_log)} entries):")
        for entry in self.execution_log:
            print(f"  - {entry}")


if __name__ == "__main__":
    demo = GUIWorkspaceDemo()
    demo.run_demo()