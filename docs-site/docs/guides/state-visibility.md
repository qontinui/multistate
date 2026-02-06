---
sidebar_position: 3
---

# State Visibility Control

The `StaysVisible` enum provides fine-grained control over state visibility during transitions. This feature is essential for managing GUI applications where some UI elements should remain visible while navigating to new states.

## Overview

When a transition executes, you often need to control whether the source states remain visible or become hidden. The `StaysVisible` enum offers three options:

- `StaysVisible.NONE` - Inherit visibility behavior from parent container (default)
- `StaysVisible.TRUE` - Source states remain visible after transition
- `StaysVisible.FALSE` - Source states become hidden after transition

## Use Cases

### Modal Dialogs (StaysVisible.TRUE)

When opening a modal dialog, you typically want the underlying state to remain visible:

```python
from multistate import State, Transition, StaysVisible, TransitionExecutor

# Create states
main_menu = State("main_menu", "Main Menu")
modal = State("modal", "Modal Dialog")

# Transition that keeps parent visible
open_modal = Transition(
    id="open_modal",
    name="Open Modal",
    from_states={main_menu},
    activate_states={modal},
    stays_visible=StaysVisible.TRUE  # main_menu stays visible behind modal
)

# Execute
executor = TransitionExecutor()
result = executor.execute(open_modal, {main_menu})

# Both states are now active:
# - modal is activated
# - main_menu remains visible in the background
```

### Full Screen Navigation (StaysVisible.FALSE)

For full-screen transitions where the previous state should be completely hidden:

```python
# Create states
main_menu = State("main_menu", "Main Menu")
settings = State("settings", "Settings Panel")

# Transition that hides previous state
open_settings = Transition(
    id="open_settings",
    name="Open Settings",
    from_states={main_menu},
    activate_states={settings},
    stays_visible=StaysVisible.FALSE  # main_menu gets hidden
)

# Execute
executor = TransitionExecutor()
result = executor.execute(open_settings, {main_menu})

# main_menu is hidden, only settings is visible
```

### Default Behavior (StaysVisible.NONE)

When you want to let the parent state manager or container decide:

```python
default_transition = Transition(
    id="default",
    name="Default Transition",
    from_states={settings},
    activate_states={main_menu},
    stays_visible=StaysVisible.NONE  # Inherit from parent
)
```

## How It Works

During transition execution, the `TransitionExecutor` processes visibility in a dedicated phase:

1. **VALIDATE** - Check preconditions
2. **OUTGOING** - Execute outgoing transition action
3. **ACTIVATE** - Activate target states
4. **INCOMING** - Execute incoming transitions for activated states
5. **EXIT** - Deactivate exit states
6. **VISIBILITY** - Apply visibility rules ← This is where stays_visible is applied
7. **CLEANUP** - Finalize and clean up

The visibility phase examines the transition's `stays_visible` setting and determines:

- Which states should remain visible (`states_to_show`)
- Which states should be hidden (`states_to_hide`)

## Inspecting Visibility Results

You can inspect the visibility changes in the transition result:

```python
result = executor.execute(transition, active_states)

# Find the visibility phase
for phase_result in result.phase_results:
    if phase_result.phase == TransitionPhase.VISIBILITY:
        print(f"Visibility setting: {phase_result.data['stays_visible']}")
        print(f"States to show: {phase_result.data['states_to_show']}")
        print(f"States to hide: {phase_result.data['states_to_hide']}")
```

## Serialization

The `stays_visible` property is included when serializing transitions to dictionaries:

```python
transition = Transition(
    id="example",
    name="Example",
    from_states={state1},
    activate_states={state2},
    stays_visible=StaysVisible.TRUE
)

data = transition.to_dict()
# data['stays_visible'] == 'TRUE'
```

This allows you to persist and restore transitions with their visibility settings intact.

## Best Practices

1. **Use TRUE for overlays**: Modal dialogs, tooltips, dropdowns
2. **Use FALSE for full-screen transitions**: Page navigation, workspace switching
3. **Use NONE when unsure**: Let the state management framework decide
4. **Consider state hierarchy**: Parent-child relationships may affect visibility

## Multiple Source States

When a transition has multiple source states, the visibility setting applies to all of them:

```python
# Transition from multiple states
multi_source = Transition(
    id="close_panels",
    name="Close All Panels",
    from_states={panel1, panel2, panel3},
    activate_states={main_view},
    stays_visible=StaysVisible.FALSE  # All panels get hidden
)
```

## Example Application

See the complete working example at `examples/visibility_example.py` in the multistate repository.

## Migration from Qontinui

This feature was migrated from the Qontinui visual automation framework, where it's used to manage GUI element visibility during automated workflows. The semantics are identical, making it easy to port Qontinui automation scripts to multistate.
