"""Transition system for MultiState framework."""

from multistate.transitions.transition import (
    Transition,
    TransitionResult,
    TransitionPhase,
    PhaseResult,
)
from multistate.transitions.executor import TransitionExecutor

__all__ = [
    "Transition",
    "TransitionResult",
    "TransitionPhase",
    "PhaseResult",
    "TransitionExecutor",
]