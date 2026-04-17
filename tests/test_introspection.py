"""Tests for StateManager trigger introspection (Phase 1).

Covers:
    * PermittedTrigger / BlockedTrigger dataclasses (hashing, to_dict).
    * ``permitted_triggers`` lists transitions whose from_states are active.
    * ``blocked_triggers`` annotates the reason for each blocked transition.
    * Blocking by inactive required state, failed guard, and guard exception.
    * Backwards compatibility of ``get_available_transitions``.
    * Single-pass consistency of ``_evaluate_all_triggers``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Match sibling-test convention (src/ layout, no editable install required).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from multistate.core.trigger_introspection import BlockedTrigger, PermittedTrigger
from multistate.manager import StateManager


def _build_manager() -> StateManager:
    """Create a small 3-state manager used by most tests."""
    manager = StateManager()
    manager.add_state("login")
    manager.add_state("main_menu")
    manager.add_state("editor")

    manager.add_transition(
        "login_success",
        from_states=["login"],
        activate_states=["main_menu"],
        exit_states=["login"],
    )
    manager.add_transition(
        "open_editor",
        from_states=["main_menu"],
        activate_states=["editor"],
    )
    manager.add_transition(
        "logout",
        from_states=["main_menu"],
        activate_states=["login"],
        exit_states=["main_menu"],
    )
    return manager


# ---------- Dataclass sanity ----------


def test_permitted_trigger_to_dict_roundtrip() -> None:
    t = PermittedTrigger(
        transition_id="t1",
        from_states=["a"],
        to_states=["b"],
        guards=["g"],
        path_cost=1.5,
    )
    d = t.to_dict()
    assert d == {
        "transition_id": "t1",
        "from_states": ["a"],
        "to_states": ["b"],
        "is_available": True,
        "guards": ["g"],
        "path_cost": 1.5,
    }


def test_blocked_trigger_to_dict_roundtrip() -> None:
    t = BlockedTrigger(
        transition_id="t2",
        from_states=["a"],
        to_states=["b"],
        reason="required_state_inactive:a",
    )
    d = t.to_dict()
    assert d["is_available"] is False
    assert d["reason"] == "required_state_inactive:a"
    assert d["transition_id"] == "t2"


def test_triggers_are_hashable() -> None:
    """Both types override __hash__ so they can live in sets."""
    p = PermittedTrigger(transition_id="t1")
    b = BlockedTrigger(transition_id="t1", reason="executor_refused")
    assert {p, p} == {p}
    assert {b, b} == {b}


# ---------- permitted_triggers ----------


def test_permitted_triggers_from_active_state() -> None:
    manager = _build_manager()
    manager.activate_states({"login"})

    permitted = manager.permitted_triggers()
    permitted_ids = {t.transition_id for t in permitted}

    assert permitted_ids == {"login_success"}
    (trigger,) = permitted
    assert trigger.from_states == ["login"]
    assert trigger.to_states == ["main_menu"]
    assert trigger.is_available is True
    assert trigger.path_cost == 1.0
    assert trigger.guards == []


def test_permitted_triggers_after_transition() -> None:
    manager = _build_manager()
    manager.activate_states({"main_menu"})

    permitted_ids = {t.transition_id for t in manager.permitted_triggers()}
    assert permitted_ids == {"open_editor", "logout"}


# ---------- blocked_triggers ----------


def test_blocked_by_inactive_required_state() -> None:
    manager = _build_manager()
    manager.activate_states({"login"})

    blocked = manager.blocked_triggers()
    by_id = {b.transition_id: b for b in blocked}

    # Two transitions require main_menu and should both be blocked.
    assert set(by_id) == {"open_editor", "logout"}
    assert by_id["open_editor"].reason == "required_state_inactive:main_menu"
    assert by_id["logout"].reason == "required_state_inactive:main_menu"
    assert all(b.is_available is False for b in blocked)


def test_blocked_by_guard_failure() -> None:
    manager = StateManager()
    manager.add_state("a")
    manager.add_state("b")

    def never_ok(_mgr: StateManager) -> bool:
        return False

    manager.add_transition(
        "t_gated",
        from_states=["a"],
        activate_states=["b"],
    )
    # Attach a callable guard via metadata (Phase 1 surface).
    manager.transitions["t_gated"].metadata["guards"] = [never_ok]

    manager.activate_states({"a"})

    permitted_ids = {t.transition_id for t in manager.permitted_triggers()}
    blocked = manager.blocked_triggers()

    assert permitted_ids == set()
    assert len(blocked) == 1
    (b,) = blocked
    assert b.transition_id == "t_gated"
    assert b.reason == "guard_failed:never_ok"
    assert b.guards == ["never_ok"]


def test_blocked_by_guard_exception() -> None:
    manager = StateManager()
    manager.add_state("a")
    manager.add_state("b")

    def boom(_mgr: StateManager) -> bool:
        raise RuntimeError("nope")

    manager.add_transition(
        "t_broken",
        from_states=["a"],
        activate_states=["b"],
    )
    manager.transitions["t_broken"].metadata["guards"] = [boom]
    manager.activate_states({"a"})

    blocked = manager.blocked_triggers()
    assert len(blocked) == 1
    assert blocked[0].reason == "guard_error:boom:RuntimeError"


def test_guard_names_include_string_entries() -> None:
    """String entries are documented but not executed — they still surface."""
    manager = StateManager()
    manager.add_state("a")
    manager.add_state("b")

    def passes(_mgr: StateManager) -> bool:
        return True

    manager.add_transition("t1", from_states=["a"], activate_states=["b"])
    manager.transitions["t1"].metadata["guards"] = ["declarative_name", passes]
    manager.activate_states({"a"})

    permitted = manager.permitted_triggers()
    assert len(permitted) == 1
    assert permitted[0].guards == ["declarative_name", "passes"]


# ---------- backward compatibility / consistency ----------


def test_get_available_transitions_matches_permitted() -> None:
    manager = _build_manager()
    manager.activate_states({"main_menu"})

    available = manager.get_available_transitions()
    permitted_ids = [t.transition_id for t in manager.permitted_triggers()]

    assert isinstance(available, list)
    assert all(isinstance(tid, str) for tid in available)
    assert sorted(available) == sorted(permitted_ids)


def test_evaluate_all_partitions_transitions() -> None:
    """Every transition appears in exactly one of the two lists."""
    manager = _build_manager()
    manager.activate_states({"main_menu"})

    permitted, blocked = manager._evaluate_all_triggers()
    permitted_ids = {t.transition_id for t in permitted}
    blocked_ids = {t.transition_id for t in blocked}

    all_ids = set(manager.transitions.keys())
    assert permitted_ids.isdisjoint(blocked_ids)
    assert permitted_ids | blocked_ids == all_ids


def test_evaluate_all_covers_all_transitions_when_no_state_active() -> None:
    """With no active states, every with-from transition is blocked."""
    manager = _build_manager()
    # Don't activate anything.

    permitted, blocked = manager._evaluate_all_triggers()
    assert permitted == []
    assert {b.transition_id for b in blocked} == set(manager.transitions.keys())
    # All blocks should cite the inactive required state.
    assert all(b.reason.startswith("required_state_inactive:") for b in blocked)


def test_no_from_states_transition_is_always_permitted() -> None:
    """Transitions without from_states are permitted regardless of active set."""
    manager = StateManager()
    manager.add_state("bootstrap")
    manager.add_transition("boot", activate_states=["bootstrap"])

    permitted_ids = {t.transition_id for t in manager.permitted_triggers()}
    assert permitted_ids == {"boot"}
