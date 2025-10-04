# MultiState

A Python library for managing multiple simultaneous active states with intelligent pathfinding and coordinated transitions.

## Overview

Unlike traditional FSM libraries that assume a single active state, MultiState handles:
- Multiple states active simultaneously
- State groups that activate/deactivate together
- Pathfinding to multiple target states
- Coordinated transition execution with phases
- Incoming transitions for newly activated states

## Installation

```bash
pip install multistate
```

## Quick Start

```python
from multistate import StateManager, State, StateGroup, Transition

# Create states
login = State("login")
dashboard = State("dashboard")
toolbar = State("toolbar")
sidebar = State("sidebar")

# Group related states
workspace = StateGroup("workspace", [dashboard, toolbar, sidebar])

# Setup manager
manager = StateManager()
manager.add_state(login)
manager.add_group(workspace)

# Define transition that activates multiple states
login_transition = Transition(
    from_states={login},
    activate_group=workspace  # Activates all states in group
)

# Execute transition
manager.execute_transition(login_transition)
assert manager.get_active_states() == {dashboard, toolbar, sidebar}
```

## Documentation

Full documentation available at [https://multistate.readthedocs.io](https://multistate.readthedocs.io)

## Research

This library is based on research extending Model-based GUI Automation theory. See the `paper/` directory for:
- Formal mathematical model
- Related work analysis
- Implementation details

## Contributing

We welcome contributions! Please see CONTRIBUTING.md for guidelines.

## License

MIT License - See LICENSE file for details.