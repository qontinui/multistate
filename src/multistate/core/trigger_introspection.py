"""Trigger introspection dataclasses.

These types describe WHY a transition is (or isn't) currently available.  They
are returned by ``StateManager.permitted_triggers()`` and
``StateManager.blocked_triggers()`` and are designed to be safe to hand to
upstream facades/UI layers: frozen (immutable) and convertible to plain dicts
for JSON serialization.

The "trigger" terminology matches the UI vocabulary ("which triggers can I
fire right now?") even though the underlying model calls them transitions.

Hashing:
    Both dataclasses override ``__hash__`` to hash by ``transition_id`` only,
    mirroring the pattern used by :class:`multistate.transitions.transition.Transition`.
    This keeps instances usable in sets/dict keys even though the auto-generated
    hash from ``frozen=True`` would fail on the ``list`` fields.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PermittedTrigger:
    """A transition that is currently permitted from the active state set.

    Attributes:
        transition_id: Unique transition identifier.
        from_states: IDs of the states the transition requires to be active.
        to_states: IDs of the states the transition will activate
            (including group-expanded states).
        is_available: Always ``True`` for permitted triggers; reserved for
            future use where availability and permission might differ.
        guards: Names of guards that were evaluated (empty if no guards).
        path_cost: Transition's path-finding cost, or ``None`` when not
            applicable.
    """

    transition_id: str
    from_states: List[str] = field(default_factory=list)
    to_states: List[str] = field(default_factory=list)
    is_available: bool = True
    guards: List[str] = field(default_factory=list)
    path_cost: Optional[float] = None

    def __hash__(self) -> int:
        return hash(("permitted", self.transition_id))

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        return asdict(self)


@dataclass(frozen=True)
class BlockedTrigger:
    """A transition that is currently blocked, annotated with the reason.

    Attributes:
        transition_id: Unique transition identifier.
        from_states: IDs of the states the transition requires to be active.
        to_states: IDs of the states the transition would activate.
        is_available: Always ``False`` for blocked triggers.
        guards: Names of guards that were evaluated.
        path_cost: Transition's path-finding cost, or ``None``.
        reason: Why the transition is blocked.  Uses a structured prefix:
            ``required_state_inactive:{state_id}``,
            ``guard_failed:{guard_name}``,
            ``guard_error:{guard_name}:{exception_class}``, or
            ``executor_refused`` as a fallback.
    """

    transition_id: str
    from_states: List[str] = field(default_factory=list)
    to_states: List[str] = field(default_factory=list)
    is_available: bool = False
    guards: List[str] = field(default_factory=list)
    path_cost: Optional[float] = None
    reason: str = "executor_refused"

    def __hash__(self) -> int:
        return hash(("blocked", self.transition_id, self.reason))

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        return asdict(self)


__all__ = ["PermittedTrigger", "BlockedTrigger"]
