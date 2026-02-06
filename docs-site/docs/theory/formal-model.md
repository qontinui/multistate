---
sidebar_position: 1
---

# Formal Model

The MultiState framework extends traditional state machine theory with capabilities for multiple simultaneous active states, dynamic transitions, and occlusion semantics.

## Core Definition

The system is formally defined as a tuple:

$$
\Omega = (S, T, G, \omega, T_d)
$$

Where:

- **S**: finite set of states
- **T ⊆ S × P(S) × P(S)**: transition relation
- **G ⊆ P(S)**: set of state groups
- **ω: S × S × ℝ → [0,1]**: occlusion function
- **T_d: ℝ × P(S) → P(T)**: dynamic transition generator

## States

### Definition & Properties

A state represents a distinguishable system configuration with:

- Unique identity
- Associated UI elements/components
- Boolean blocking indicator
- Optional group membership

### Active States

The system maintains active states $S_\Xi(t) \subseteq S$. Unlike traditional FSMs where $|S_\Xi| = 1$, MultiState allows $|S_\Xi| \geq 0$.

## Transitions

### Definition

A transition $\tau = (F, A, E)$ consists of:

- **F ⊆ S**: "from" states (preconditions)
- **A ⊆ S**: states to activate
- **E ⊆ S**: states to exit

### Multi-State Activation

**Innovation:** $|A| \geq 1$, enabling atomic activation of multiple states simultaneously.

### Execution Enablement

A transition is enabled when:

$$
F \subseteq S_\Xi \land (A \cap E = \emptyset)
$$

## State Groups

### Definition & Constraints

A group $g \subseteq S$ activates/deactivates atomically. Group constraint ensures: for any transition $\tau$ and group $g$, all states in $g$ transition together:

$$
s_1 \in A(\tau) \Leftrightarrow s_2 \in A(\tau) \quad \forall s_1, s_2 \in g
$$

## Occlusion Function

The function $\omega(s_c, s_h, t) = p$ models state visibility, where:

- $s_c$: covering state
- $s_h$: hidden state
- $p \in [0,1]$: occlusion probability

### Types

1. **Modal** ($p = 1.0$): Complete occlusion
2. **Spatial** ($p \in [0.5, 0.9]$): Partial overlap
3. **Logical** ($p \in [0.7, 1.0]$): Semantic exclusion

## Dynamic Transitions

Generated at runtime:

$$
T_d(t, S_\Xi) = \{\tau_1, \tau_2, ..., \tau_n\}
$$

### Types

- **Reveal Transitions**: Generated when occluding state closes
- **Self-Transitions**: Validate current state without change
- **Discovery Transitions**: Found through runtime exploration

### Reveal Generation

When state $s_c$ covering $H = \{s_{h1}, s_{h2}, ...\}$ is removed:

$$
\tau_{reveal} = (\{s_c\}, H, \{s_c\})
$$

## Phased Execution Model

### Execution Sequence

```
VALIDATE → OUTGOING → ACTIVATE → INCOMING → EXIT
```

### Phase Definitions

1. **VALIDATE**: Check preconditions
   $$valid(\tau) = F(\tau) \subseteq S_\Xi$$

2. **OUTGOING**: Execute exit actions
   $$outgoing(S_\Xi) = \bigwedge_{s \in S_\Xi} exit(s)$$

3. **ACTIVATE**: Add states (infallible)
   $$S'_\Xi = S_\Xi \cup A(\tau)$$

4. **INCOMING**: Execute entry actions
   $$incoming(A) = \bigwedge_{s \in A} entry(s)$$

5. **EXIT**: Remove exited states
   $$S''_\Xi = S'_\Xi \setminus E(\tau)$$

### Rollback Semantics

If INCOMING fails, rollback restores:

$$
S_{\Xi,rollback} = S_\Xi
$$

## Multi-Target Pathfinding

### Problem Definition

Given current states $S_c$ and target states $T$, find path $\pi$ such that:

$$
execute(\pi, S_c) \supseteq T
$$

### Optimality

Optimal path:

$$
\pi^* = \arg\min_\pi cost(\pi) \text{ s.t. } T \subseteq reachable(\pi, S_c)
$$

### Complexity

Search space: $O(|V| \cdot 2^{|T|})$, where $|V|$ is state count and $|T|$ is target count.

## Theorems

**Theorem 1 (Activation Atomicity)**: State activation is atomic and infallible; it's a pure set operation that cannot fail.

**Theorem 2 (Group Atomicity)**: States in a group are always activated/deactivated together per group constraints.

**Theorem 3 (Multi-Target Optimality)**: The algorithm explores all reachable state combinations using dynamic programming with memoization, guaranteeing optimal solutions.

**Theorem 4 (Occlusion Transitivity)**: If $s_1$ occludes $s_2$ and $s_2$ occludes $s_3$, then $s_1$ occludes $s_3$.

**Theorem 5 (Safe Rollback)**: Failed incoming transitions preserve system state; rollback restores original state and skips EXIT phase.

## Comparison with Existing Models

| Property    | MultiState   | FSM     | Statecharts | Petri Nets  |
| ----------- | ------------ | ------- | ----------- | ----------- |
| States      | P(S)         | S       | P(S)        | Markings    |
| Transitions | (F,A,E)      | (s₁,s₂) | Complex     | Token flow  |
| Concurrency | Native       | None    | Orthogonal  | Token-based |
| Hierarchy   | Groups       | None    | Nested      | Subnets     |
| Dynamics    | T_d function | Static  | Static      | Static      |

## Formal Verification

Verification completed through:

- **Mathematical proofs** for all core properties
- **Property-based testing** achieving 100% theorem coverage
- **Bounded model checking** for safety properties
