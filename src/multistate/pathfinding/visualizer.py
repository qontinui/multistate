"""Visualization tools for multi-target pathfinding.

Generates ASCII and Graphviz visualizations of pathfinding.
"""

from typing import Set, List, Optional
from multistate.core.state import State
from multistate.transitions.transition import Transition
from multistate.pathfinding.multi_target import Path


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
        target_states: Optional[Set[State]] = None
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
        lines.append('  subgraph cluster_legend {')
        lines.append('    label="Legend";')
        lines.append('    style="dashed";')
        lines.append('    "Target State" [fillcolor="lightblue", style="filled"];')
        lines.append('    "Path State" [color="red", penwidth="2"];')
        lines.append('    "Blocking State" [shape="box"];')
        lines.append('  }')

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
            ("Targets Reached", lambda p: len([s for s in p.targets if any(s in ss for ss in p.states_sequence)])),
        ]

        for metric_name, metric_func in metrics:
            values = [str(metric_func(p)) if p else "N/A" for p in paths]
            row = f"| {metric_name:<15} | " + " | ".join(f"{v:^20}" for v in values) + " |"
            lines.append(row)

        lines.append("-" * len(header))

        # Show path sequences
        lines.append("\nPath Details:")
        for i, (path, label) in enumerate(zip(paths, labels)):
            if path:
                lines.append(f"\n{label}:")
                for j, trans in enumerate(path.transitions_sequence):
                    lines.append(f"  {j+1}. {trans.name} (cost={trans.path_cost})")
            else:
                lines.append(f"\n{label}: No path found")

        return "\n".join(lines)

    @staticmethod
    def visualize_search_tree(
        search_nodes: List,  # List of PathNode objects
        max_depth: int = 5
    ) -> str:
        """Visualize the search tree exploration."""
        lines = []
        lines.append("Search Tree Exploration")
        lines.append("=" * 60)

        # Group nodes by depth
        by_depth = {}
        for node in search_nodes[:100]:  # Limit to first 100 for readability
            if node.depth not in by_depth:
                by_depth[node.depth] = []
            by_depth[node.depth].append(node)

        # Show each depth level
        for depth in range(min(max_depth + 1, max(by_depth.keys()) + 1)):
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
        lines.append(f"Max depth reached: {max(by_depth.keys())}")

        return "\n".join(lines)