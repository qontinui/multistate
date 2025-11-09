---
sidebar_position: 1
---

# Quick Start Guide

Get started with MultiState in just a few minutes. This guide walks you through building your first multi-state application.

## Installation

Install MultiState using pip:

```bash
pip install multistate
```

## Step 1: Import the Library

```python
from multistate import StateManager, State, StateGroup, Transition
```

## Step 2: Define Your States

Create states representing different parts of your application:

```python
# Create individual states
login = State("login", description="Login Screen")
dashboard = State("dashboard", description="Main Dashboard")
toolbar = State("toolbar", description="Top Toolbar")
sidebar = State("sidebar", description="Side Navigation")
modal = State("settings_modal", description="Settings Dialog", is_blocking=True)
```

The `is_blocking` parameter marks states that should occlude others (like modal dialogs).

## Step 3: Organize States into Groups

Group related states that should activate together:

```python
# Create a group for workspace components
workspace = StateGroup(
    name="workspace",
    states=[dashboard, toolbar, sidebar],
    description="Main workspace layout"
)
```

## Step 4: Setup the State Manager

Initialize the manager and register your states and groups:

```python
manager = StateManager()

# Add individual states
manager.add_state(login)
manager.add_state(modal)

# Add the group (automatically adds all states in the group)
manager.add_group(workspace)

# Set initial state
manager.activate_state(login)
```

## Step 5: Define Transitions

Create transitions between states:

```python
# Transition from login to workspace (activates multiple states)
login_to_workspace = Transition(
    name="login_success",
    from_states={login},
    activate_group=workspace,  # Activates all workspace states
    exit_states={login},
    path_cost=1.0
)

# Transition to open modal
open_settings = Transition(
    name="open_settings",
    from_states={dashboard},
    activate_states={modal},
    path_cost=1.0
)

# Add transitions to manager
manager.add_transition(login_to_workspace)
manager.add_transition(open_settings)
```

## Step 6: Execute Transitions and Find Paths

Now you can navigate your state space:

```python
# Execute a single transition
manager.execute_transition(login_to_workspace)
print(manager.get_active_states())  # {dashboard, toolbar, sidebar}

# Find path to multiple targets
path = manager.find_path_to(['dashboard', 'settings_modal'])
if path:
    print(f"Found path with {len(path.transitions)} steps")
    success = manager.execute_path(path)
```

## Complete Example

Here's a complete working example combining all the steps:

```python
from multistate import StateManager, State, StateGroup, Transition

# Define states
login = State("login", "Login Screen")
dashboard = State("dashboard", "Dashboard")
toolbar = State("toolbar", "Toolbar")
sidebar = State("sidebar", "Sidebar")
settings = State("settings", "Settings Panel")

# Create workspace group
workspace = StateGroup("workspace", [dashboard, toolbar, sidebar])

# Setup manager
manager = StateManager()
manager.add_state(login)
manager.add_state(settings)
manager.add_group(workspace)

# Define transitions
manager.add_transition(
    Transition(
        name="login",
        from_states={login},
        activate_group=workspace,
        exit_states={login}
    )
)

manager.add_transition(
    Transition(
        name="open_settings",
        from_states={dashboard},
        activate_states={settings}
    )
)

# Start from login
manager.activate_state(login)

# Execute login transition
print("Active states:", manager.get_active_states())  # {login}

login_transition = manager.get_transition("login")
manager.execute_transition(login_transition)

print("Active states:", manager.get_active_states())  # {dashboard, toolbar, sidebar}

# Find path to settings
path = manager.find_path_to(['settings'])
if path:
    manager.execute_path(path)
    print("Active states:", manager.get_active_states())  # {dashboard, toolbar, sidebar, settings}
```

## Key Concepts

- **States**: Represent distinct configurations of your system
- **State Groups**: Collections of states that activate/deactivate together
- **Transitions**: Define how to move between states with multi-state activation
- **Pathfinding**: Automatically find optimal paths to reach target states
- **Blocking States**: Modal/occluding states that hide others when active

## Next Steps

- Understand the [Formal Model](/docs/theory/formal-model) - Mathematical foundations
- Read the [Introduction](/docs/introduction) - Core concepts and use cases
- Try the [Interactive Playground](/playground) - Hands-on experimentation

## Need Help?

- Join our [Discussion Forum](https://github.com/qontinui/multistate/discussions)
- Report issues on [GitHub](https://github.com/qontinui/multistate/issues)
- Browse the [GitHub Repository](https://github.com/qontinui/multistate) - Source code and examples
