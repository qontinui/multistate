---
sidebar_position: 1
---

# Introduction to MultiState

MultiState is an advanced state management framework that extends traditional finite state machines with powerful multi-state capabilities. Born from the practical needs of GUI automation and formalized through rigorous mathematical foundations, MultiState solves complex state management challenges that existing frameworks cannot handle.

## The Problem

Traditional state management approaches (FSMs, Statecharts, Petri nets) share a fundamental limitation: they assume only one state can be active at a time, or they handle multiple states without considering the complex relationships between them.

In real-world applications, especially GUI automation, we face scenarios like:

- Multiple UI components active simultaneously (toolbar + sidebar + content area)
- Modal dialogs occluding underlying states without destroying them
- Complex navigation requiring multiple targets to be reached
- Dynamic transitions discovered at runtime based on current state

## The Solution

MultiState introduces groundbreaking capabilities:

### Multi-Target Pathfinding

```python
# Traditional: Find path to ONE state
path = find_path_to('search_panel')

# MultiState: Find path to reach ALL targets
path = manager.find_path_to(['search', 'properties', 'debug'])
# Returns optimal sequence reaching ALL three panels
```

### Multi-State Activation

```python
# Transitions activate multiple states atomically
transition = Transition(
    name="Open Workspace",
    activate=['toolbar', 'sidebar', 'content'],  # ALL activated together
    exit=['splash_screen']
)
```

### Occlusion & Reveal

```python
# Modal dialog occluding others
manager.activate('settings_modal')  # Automatically detects occlusion
manager.deactivate('settings_modal')  # Generates reveal transition
# Previously hidden states are restored
```

### Phased Execution

Safe, rollback-capable execution model:

```
VALIDATE → OUTGOING → ACTIVATE → INCOMING → EXIT
             ↓ on failure
          ROLLBACK (preserves state)
```

## Mathematical Foundation

MultiState is built on formal mathematical foundations:

$$
\Omega = (S, T, G, \omega, T_d)
$$

Where:

- $S$ is the set of states
- $T \subseteq S \times \mathcal{P}(S) \times \mathcal{P}(S)$ defines transitions
- $G \subseteq \mathcal{P}(S)$ groups related states
- $\omega: S \times S \times \mathbb{R} \to [0,1]$ models occlusion
- $T_d: \mathbb{R} \times \mathcal{P}(S) \to \mathcal{P}(T)$ generates dynamic transitions

## Key Innovations

### 1. Multi-State Activation Semantics

Unlike traditional frameworks, activation is a pure memory operation that cannot fail, following Brobot's proven model.

### 2. Global Optimality in Pathfinding

Our algorithm finds globally optimal paths to reach ALL specified targets, not just local solutions.

### 3. Runtime Adaptability

Dynamic transitions are discovered and generated at runtime based on current state configuration.

### 4. Formal Verification

All properties are formally proven with property-based testing achieving 100% theorem coverage.

## Use Cases

MultiState excels in domains requiring complex state orchestration:

- **GUI Automation:** Managing complex UI states with modals, panels, and workspaces
- **Game Development:** Handling multiple active game states, abilities, and effects
- **Microservices:** Orchestrating service states with circuit breakers and fallbacks
- **Workflow Engines:** Managing parallel workflow branches and synchronization
- **Robotics:** Coordinating multiple subsystem states simultaneously

## Quick Example

```python
from multistate import StateManager, SearchStrategy

# Initialize manager
manager = StateManager(search_strategy=SearchStrategy.DIJKSTRA)

# Define states
manager.add_state('main', 'Main Window')
manager.add_state('toolbar', 'Toolbar')
manager.add_state('search', 'Search Panel')
manager.add_state('properties', 'Properties Panel')

# Define multi-state transition
manager.add_transition(
    'open_workspace',
    from_states=['main'],
    activate=['toolbar', 'search', 'properties'],  # Activate ALL
    path_cost=1.0
)

# Find path to multiple targets
path = manager.find_path_to(['search', 'properties'])
print(f"Path found: {path.total_cost} cost, {len(path.transitions)} steps")

# Execute with automatic rollback on failure
success = manager.execute_path(path)
```

## Why MultiState?

| Feature | MultiState | FSM | Statecharts | Petri Nets |
|---------|-----------|-----|-------------|------------|
| Multi-state activation | ✅ | ❌ | Partial | ✅ |
| Multi-target pathfinding | ✅ | ❌ | ❌ | ❌ |
| Dynamic transitions | ✅ | ❌ | ❌ | Partial |
| Occlusion handling | ✅ | ❌ | ❌ | ❌ |
| Formal verification | ✅ | ✅ | Partial | ✅ |
| Phased execution | ✅ | ❌ | ❌ | ❌ |

## Next Steps

- 📐 [Formal Model](/docs/theory/formal-model) - Understand the mathematical foundations

## 🎓 Academic Contribution

MultiState represents a significant theoretical contribution to state management, with:

- ✨ Novel multi-target pathfinding algorithm with proven optimality
- 📝 Formal semantics for multi-state activation
- ⚡ Dynamic transition generation framework
- ✅ Complete property-based verification

## 🌟 Community

MultiState is open-source and welcomes contributions:

- 💻 [GitHub Repository](https://github.com/qontinui/multistate)
- 💬 [Discussion Forum](https://github.com/qontinui/multistate/discussions)
- 🐛 [Issue Tracker](https://github.com/qontinui/multistate/issues)

Join us in advancing the state of the art in state management!
