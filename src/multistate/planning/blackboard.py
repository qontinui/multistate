from __future__ import annotations

import threading
from typing import Any


class Blackboard:
    """Scoped variable storage with parent chain lookup and thread safety."""

    MAX_DEPTH: int = 16

    def __init__(self, parent: Blackboard | None = None) -> None:
        self._data: dict[str, Any] = {}
        self._parent: Blackboard | None = parent
        self._lock: threading.Lock = threading.Lock()

        # Compute depth from parent chain
        depth = 0
        current = parent
        while current is not None:
            depth += 1
            current = current._parent
        self._depth: int = depth

        if self._depth > self.MAX_DEPTH:
            raise ValueError(
                f"Blackboard depth {self._depth} exceeds MAX_DEPTH {self.MAX_DEPTH}"
            )

    def get(self, name: str, default: Any = None) -> Any:
        """Check local _data first (under lock), then parent chain."""
        with self._lock:
            if name in self._data:
                return self._data[name]
        if self._parent is not None:
            return self._parent.get(name, default)
        return default

    def set(self, name: str, value: Any) -> None:
        """Set in local scope only (under lock)."""
        with self._lock:
            self._data[name] = value

    def has(self, name: str) -> bool:
        """Check local then parent chain."""
        with self._lock:
            if name in self._data:
                return True
        if self._parent is not None:
            return self._parent.has(name)
        return False

    def delete(self, name: str) -> None:
        """Remove from local scope."""
        with self._lock:
            self._data.pop(name, None)

    def local_keys(self) -> set[str]:
        """Return keys in this scope only."""
        with self._lock:
            return set(self._data.keys())

    def all_keys(self) -> set[str]:
        """Return keys from this scope + all parents (no duplicates)."""
        keys = self.local_keys()
        if self._parent is not None:
            keys |= self._parent.all_keys()
        return keys

    def create_child(self) -> Blackboard:
        """Return new Blackboard with self as parent."""
        return Blackboard(parent=self)

    def to_dict(self) -> dict[str, Any]:
        """Snapshot of local scope only."""
        with self._lock:
            return dict(self._data)

    def __repr__(self) -> str:
        with self._lock:
            key_count = len(self._data)
        return f"Blackboard(depth={self._depth}, local_keys={key_count})"


class BlackboardPlan:
    """Declares expected variables and types for a Blackboard."""

    def __init__(self, variables: dict[str, type]) -> None:
        self._variables: dict[str, type] = dict(variables)

    def create_blackboard(self, parent: Blackboard | None = None) -> Blackboard:
        """Create Blackboard, initialize each variable to typ() default."""
        bb = Blackboard(parent=parent)
        for name, typ in self._variables.items():
            bb.set(name, typ())
        return bb

    def validate(self, blackboard: Blackboard) -> list[str]:
        """Return list of error strings (empty = valid).

        Check each variable exists and has correct type.
        """
        errors: list[str] = []
        for name, typ in self._variables.items():
            if not blackboard.has(name):
                errors.append(f"Missing variable: {name}")
            else:
                value = blackboard.get(name)
                if not isinstance(value, typ):
                    errors.append(
                        f"Variable '{name}' has type {type(value).__name__}, "
                        f"expected {typ.__name__}"
                    )
        return errors
