# MultiState

[![PyPI version](https://badge.fury.io/py/multistate.svg)](https://badge.fury.io/py/multistate)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-github%20pages-blue)](https://qontinui.github.io/multistate/)

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

**📚 Full documentation with interactive playground: [qontinui.github.io/multistate](https://qontinui.github.io/multistate/)**

Features:
- Complete API reference
- Mathematical formulas and proofs
- Interactive playground to try MultiState in your browser
- Usage examples and tutorials

## Research

This library is based on research extending Model-based GUI Automation theory:

- **Paper**: [Model-based GUI Automation](https://link.springer.com/article/10.1007/s10270-025-01319-9) - Springer SoSyM (October 2025)
- **Mathematical model**: Formal proofs of complexity reduction
- **Related work**: Analysis of state machine approaches
- **Implementation details**: See `paper/` directory

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## License

MIT License - See [LICENSE](LICENSE) file for details.