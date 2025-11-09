---
sidebar_position: 0
slug: /
---

# Welcome to MultiState

MultiState is a Python library for managing multiple simultaneous active states with intelligent pathfinding and coordinated transitions.

:::tip Quick Start
Jump right in with our [Introduction](/docs/introduction) or try the [Interactive Playground](/playground)!
:::

## Installation

```bash
pip install multistate
```

## Key Features

- **Multi-State Activation** - Multiple states can be active simultaneously
- **Multi-Target Pathfinding** - Find optimal paths to reach all specified targets
- **State Groups** - Organize related states that activate/deactivate together
- **Coordinated Transitions** - Execute complex transitions with multiple phases
- **Dynamic Transitions** - Automatically generate transitions based on current state

## Quick Example

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
    activate_group=workspace
)

# Execute transition
manager.execute_transition(login_transition)
assert manager.get_active_states() == {dashboard, toolbar, sidebar}
```

## Learn More

- [Introduction](/docs/introduction) - Core concepts and use cases
- [Formal Model](/docs/theory/formal-model) - Mathematical foundations
- [GitHub Repository](https://github.com/qontinui/multistate) - Source code and examples
- [Research Paper](https://link.springer.com/article/10.1007/s10270-025-01319-9) - Academic publication

## Resources

- **PyPI:** [pypi.org/project/multistate](https://pypi.org/project/multistate/)
- **Documentation:** [qontinui.github.io/multistate](https://qontinui.github.io/multistate/)
- **Discussions:** [GitHub Discussions](https://github.com/qontinui/multistate/discussions)
- **Issues:** [GitHub Issues](https://github.com/qontinui/multistate/issues)
