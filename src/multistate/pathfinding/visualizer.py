"""Visualization tools for multi-target pathfinding.

Generates ASCII, Graphviz, and Mermaid visualizations of pathfinding.
"""

from typing import Dict, List, Optional, Set

from multistate.core.state import State
from multistate.core.state_group import StateGroup
from multistate.pathfinding.multi_target import Path
from multistate.transitions.transition import Transition


class PathVisualizer:
    """Visualizes paths and state transitions."""

    @staticmethod
    def visualize_path_ascii(path: Path) -> str:
        """Create ASCII visualization of a path.

        Shows the progression through states with targets marked.
        """
        if not path or not path.states_sequence:
            return "Empty path"

        lines = []
        lines.append("Path Visualization")
        lines.append("=" * 60)

        # Track which targets have been reached
        targets_reached = set()

        for i, state_set in enumerate(path.states_sequence):
            # Format current states
            state_names = sorted(s.name for s in state_set)
            states_str = f"[{', '.join(state_names)}]"

            # Check for newly reached targets
            new_targets = []
            for state in state_set:
                if state in path.targets and state not in targets_reached:
                    new_targets.append(state.name)
                    targets_reached.add(state)

            # Build step description
            step_line = f"Step {i}: {states_str}"

            if new_targets:
                step_line += f"  ← TARGETS REACHED: {', '.join(new_targets)}"

            lines.append(step_line)

            # Show transition taken
            if i < len(path.transitions_sequence):
                trans = path.transitions_sequence[i]
                arrow = "  ↓"
                trans_desc = f"  {trans.name} (cost={trans.path_cost})"
                lines.append(arrow)
                lines.append(trans_desc)

        # Summary
        lines.append("")
        lines.append("Summary:")
        lines.append(f"  Total steps: {len(path.transitions_sequence)}")
        lines.append(f"  Total cost: {path.total_cost}")
        lines.append(f"  Targets reached: {len(targets_reached)}/{len(path.targets)}")

        return "\n".join(lines)

    @staticmethod
    def generate_graphviz(
        transitions: List[Transition],
        highlight_path: Optional[Path] = None,
        target_states: Optional[Set[State]] = None,
    ) -> str:
        """Generate Graphviz DOT format for visualization.

        Can be rendered with: dot -Tpng output.dot -o graph.png
        """
        lines = []
        lines.append("digraph StateGraph {")
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=ellipse];")

        # Collect all states
        all_states = set()
        for trans in transitions:
            all_states.update(trans.from_states)
            all_states.update(trans.get_all_states_to_activate())
            all_states.update(trans.get_all_states_to_exit())

        # Highlight states in path
        highlighted_states = set()
        if highlight_path:
            for state_set in highlight_path.states_sequence:
                highlighted_states.update(state_set)

        # Draw states
        for state in all_states:
            attributes = []

            # Color coding
            if target_states and state in target_states:
                attributes.append('fillcolor="lightblue"')
                attributes.append('style="filled"')

            if state in highlighted_states:
                attributes.append('penwidth="2"')
                attributes.append('color="red"')

            if state.blocking:
                attributes.append('shape="box"')

            attr_str = f" [{', '.join(attributes)}]" if attributes else ""
            lines.append(f'  "{state.name}"{attr_str};')

        # Highlight transitions in path
        highlighted_transitions = set()
        if highlight_path:
            highlighted_transitions = set(highlight_path.transitions_sequence)

        # Draw transitions
        for trans in transitions:
            # For each from state to each activated state
            from_states = trans.from_states if trans.from_states else [State("*", "Any")]

            for from_state in from_states:
                for to_state in trans.get_all_states_to_activate():
                    attributes = []

                    if trans in highlighted_transitions:
                        attributes.append('color="red"')
                        attributes.append('penwidth="2"')

                    label = f"{trans.name}\\ncost={trans.path_cost}"
                    attributes.append(f'label="{label}"')

                    attr_str = f" [{', '.join(attributes)}]"
                    lines.append(f'  "{from_state.name}" -> "{to_state.name}"{attr_str};')

        # Legend
        lines.append("")
        lines.append("  // Legend")
        lines.append("  subgraph cluster_legend {")
        lines.append('    label="Legend";')
        lines.append('    style="dashed";')
        lines.append('    "Target State" [fillcolor="lightblue", style="filled"];')
        lines.append('    "Path State" [color="red", penwidth="2"];')
        lines.append('    "Blocking State" [shape="box"];')
        lines.append("  }")

        lines.append("}")

        return "\n".join(lines)

    @staticmethod
    def compare_paths(paths: List[Path], labels: List[str]) -> str:
        """Compare multiple paths side by side."""
        if not paths or len(paths) != len(labels):
            return "Invalid input for comparison"

        lines = []
        lines.append("Path Comparison")
        lines.append("=" * 80)

        # Header
        header = "| " + " | ".join(f"{label:^20}" for label in labels) + " |"
        lines.append(header)
        lines.append("-" * len(header))

        # Compare metrics
        metrics = [
            ("Steps", lambda p: len(p.transitions_sequence)),
            ("Total Cost", lambda p: p.total_cost),
            ("States Visited", lambda p: sum(len(s) for s in p.states_sequence)),
            (
                "Targets Reached",
                lambda p: len([s for s in p.targets if any(s in ss for ss in p.states_sequence)]),
            ),
        ]

        for metric_name, metric_func in metrics:
            values = [str(metric_func(p)) if p else "N/A" for p in paths]
            row = f"| {metric_name:<15} | " + " | ".join(f"{v:^20}" for v in values) + " |"
            lines.append(row)

        lines.append("-" * len(header))

        # Show path sequences
        lines.append("\nPath Details:")
        for path, label in zip(paths, labels, strict=False):
            if path:
                lines.append(f"\n{label}:")
                for j, trans in enumerate(path.transitions_sequence):
                    lines.append(f"  {j + 1}. {trans.name} (cost={trans.path_cost})")
            else:
                lines.append(f"\n{label}: No path found")

        return "\n".join(lines)

    # ==================== Mermaid ====================

    @staticmethod
    def generate_mermaid(
        transitions: List[Transition],
        active_states: Optional[Set[State]] = None,
        highlight_path: Optional[Path] = None,
        groups: Optional[List[StateGroup]] = None,
    ) -> str:
        """Generate a Mermaid ``stateDiagram-v2`` from transitions.

        Args:
            transitions: All transitions in the state machine.
            active_states: Currently active states to highlight.
            highlight_path: Optional path to highlight with a distinct style.
            groups: State groups to render as nested state blocks.

        Returns:
            A Mermaid diagram string.
        """
        lines: List[str] = ["stateDiagram-v2"]

        # Collect all states referenced by transitions
        all_states: Set[State] = set()
        for trans in transitions:
            all_states.update(trans.from_states)
            all_states.update(trans.get_all_states_to_activate())
            all_states.update(trans.get_all_states_to_exit())

        # Collect states that belong to groups (to avoid listing them at top level)
        grouped_state_ids: Set[str] = set()
        if groups:
            for group in groups:
                grouped_state_ids.update(s.id for s in group.states)

        # Render groups
        if groups:
            for group in groups:
                lines.append(f"    state {group.name} {{")
                for state in sorted(group.states, key=lambda s: s.id):
                    lines.append(f"        {state.name}")
                lines.append("    }")
            lines.append("")

        # Transitions
        highlighted_transitions: Set[Transition] = set()
        if highlight_path:
            highlighted_transitions = set(highlight_path.transitions_sequence)

        for trans in transitions:
            from_states = trans.from_states if trans.from_states else set()
            to_states = trans.get_all_states_to_activate()
            label = trans.name or trans.id

            for from_state in sorted(from_states, key=lambda s: s.id):
                for to_state in sorted(to_states, key=lambda s: s.id):
                    if trans in highlighted_transitions:
                        lines.append(f"    {from_state.name} ==> {to_state.name} : {label}")
                    else:
                        lines.append(f"    {from_state.name} --> {to_state.name} : {label}")

            # Transitions with no from_states: show as initial transitions
            if not from_states:
                for to_state in sorted(to_states, key=lambda s: s.id):
                    lines.append(f"    [*] --> {to_state.name} : {label}")

        # Highlight active states
        if active_states:
            active_in_machine = active_states & all_states
            if active_in_machine:
                lines.append("")
                lines.append("    classDef active fill:#90EE90,stroke:#333")
                for state in sorted(active_in_machine, key=lambda s: s.id):
                    lines.append(f"    class {state.name} active")

        # Highlight path states
        if highlight_path:
            path_states: Set[State] = set()
            for state_set in highlight_path.states_sequence:
                path_states.update(state_set)
            path_only = path_states - (active_states or set())
            if path_only:
                lines.append("")
                lines.append("    classDef pathHighlight fill:#FFD700,stroke:#333")
                for state in sorted(path_only, key=lambda s: s.id):
                    lines.append(f"    class {state.name} pathHighlight")

        return "\n".join(lines)

    @staticmethod
    def generate_mermaid_path(
        path: Path,
        all_transitions: Optional[List[Transition]] = None,
    ) -> str:
        """Generate a Mermaid diagram that highlights a specific path.

        Only the transitions along the path are drawn unless
        *all_transitions* is provided, in which case the full graph is
        drawn with the path highlighted.

        Args:
            path: The path to visualise.
            all_transitions: Optional full transition list for context.

        Returns:
            A Mermaid diagram string.
        """
        lines: List[str] = ["stateDiagram-v2"]

        if all_transitions:
            # Draw all transitions in grey, then overlay path in colour
            for trans in all_transitions:
                from_states = trans.from_states if trans.from_states else set()
                to_states = trans.get_all_states_to_activate()
                label = trans.name or trans.id
                for fs in sorted(from_states, key=lambda s: s.id):
                    for ts in sorted(to_states, key=lambda s: s.id):
                        lines.append(f"    {fs.name} --> {ts.name} : {label}")
                if not from_states:
                    for ts in sorted(to_states, key=lambda s: s.id):
                        lines.append(f"    [*] --> {ts.name} : {label}")
        else:
            # Draw only path transitions
            for trans in path.transitions_sequence:
                from_states = trans.from_states if trans.from_states else set()
                to_states = trans.get_all_states_to_activate()
                label = trans.name or trans.id
                for fs in sorted(from_states, key=lambda s: s.id):
                    for ts in sorted(to_states, key=lambda s: s.id):
                        lines.append(f"    {fs.name} --> {ts.name} : {label}")
                if not from_states:
                    for ts in sorted(to_states, key=lambda s: s.id):
                        lines.append(f"    [*] --> {ts.name} : {label}")

        # Highlight states along the path
        path_states: Set[State] = set()
        for state_set in path.states_sequence:
            path_states.update(state_set)

        if path_states:
            lines.append("")
            lines.append("    classDef pathNode fill:#FFD700,stroke:#333")
            for state in sorted(path_states, key=lambda s: s.id):
                lines.append(f"    class {state.name} pathNode")

        # Highlight targets
        if path.targets:
            lines.append("    classDef target fill:#90EE90,stroke:#333,stroke-width:2px")
            for state in sorted(path.targets, key=lambda s: s.id):
                lines.append(f"    class {state.name} target")

        return "\n".join(lines)

    @staticmethod
    def generate_mermaid_diff(
        transitions: List[Transition],
        before_states: Set[State],
        after_states: Set[State],
    ) -> str:
        """Generate a Mermaid diagram showing before/after state differences.

        States only active *before* are styled red, states only active
        *after* are styled green, and states active in both are styled blue.

        Args:
            transitions: All transitions in the state machine.
            before_states: Active states before the change.
            after_states: Active states after the change.

        Returns:
            A Mermaid diagram string.
        """
        lines: List[str] = ["stateDiagram-v2"]

        # Draw all transitions
        for trans in transitions:
            from_states = trans.from_states if trans.from_states else set()
            to_states = trans.get_all_states_to_activate()
            label = trans.name or trans.id
            for fs in sorted(from_states, key=lambda s: s.id):
                for ts in sorted(to_states, key=lambda s: s.id):
                    lines.append(f"    {fs.name} --> {ts.name} : {label}")
            if not from_states:
                for ts in sorted(to_states, key=lambda s: s.id):
                    lines.append(f"    [*] --> {ts.name} : {label}")

        # Compute diff sets
        removed = before_states - after_states
        added = after_states - before_states
        unchanged = before_states & after_states

        lines.append("")
        if removed:
            lines.append("    classDef removed fill:#FF6B6B,stroke:#333")
            for s in sorted(removed, key=lambda s: s.id):
                lines.append(f"    class {s.name} removed")
        if added:
            lines.append("    classDef added fill:#90EE90,stroke:#333")
            for s in sorted(added, key=lambda s: s.id):
                lines.append(f"    class {s.name} added")
        if unchanged:
            lines.append("    classDef unchanged fill:#87CEEB,stroke:#333")
            for s in sorted(unchanged, key=lambda s: s.id):
                lines.append(f"    class {s.name} unchanged")

        return "\n".join(lines)

    @staticmethod
    def visualize_search_tree(
        search_nodes: List,
        max_depth: int = 5,  # List of PathNode objects
    ) -> str:
        """Visualize the search tree exploration."""
        lines = []
        lines.append("Search Tree Exploration")
        lines.append("=" * 60)

        # Group nodes by depth
        by_depth: Dict[int, List] = {}
        for node in search_nodes[:100]:  # Limit to first 100 for readability
            if node.depth not in by_depth:
                by_depth[node.depth] = []
            by_depth[node.depth].append(node)

        # Show each depth level
        for depth in range(min(max_depth + 1, max(by_depth.keys(), default=0) + 1)):
            if depth in by_depth:
                lines.append(f"\nDepth {depth}: {len(by_depth[depth])} nodes")

                for node in by_depth[depth][:5]:  # Show first 5 at each depth
                    states = ", ".join(s.name for s in node.active_states)
                    targets = ", ".join(s.name for s in node.targets_reached)
                    lines.append(f"  [{states}] | Reached: {{{targets}}} | Cost: {node.cost}")

                if len(by_depth[depth]) > 5:
                    lines.append(f"  ... and {len(by_depth[depth]) - 5} more")

        # Statistics
        total_nodes = sum(len(nodes) for nodes in by_depth.values())
        lines.append(f"\nTotal nodes explored: {total_nodes}")
        lines.append(f"Max depth reached: {max(by_depth.keys(), default=0)}")

        return "\n".join(lines)
