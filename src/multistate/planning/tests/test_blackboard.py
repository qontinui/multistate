from __future__ import annotations

import threading

import pytest

from multistate.planning.blackboard import Blackboard, BlackboardPlan


class TestBlackboard:
    def test_get_set_basic(self) -> None:
        bb = Blackboard()
        bb.set("x", 42)
        assert bb.get("x") == 42
        assert bb.get("missing", "default") == "default"

    def test_parent_chain_lookup(self) -> None:
        parent = Blackboard()
        parent.set("inherited", "from_parent")
        child = Blackboard(parent=parent)
        assert child.get("inherited") == "from_parent"

    def test_local_override(self) -> None:
        parent = Blackboard()
        parent.set("key", "parent_value")
        child = Blackboard(parent=parent)
        child.set("key", "child_value")
        assert child.get("key") == "child_value"
        assert parent.get("key") == "parent_value"

    def test_depth_limit(self) -> None:
        bb = Blackboard()
        for _ in range(Blackboard.MAX_DEPTH):
            bb = Blackboard(parent=bb)
        # bb is now at depth 16, which is exactly MAX_DEPTH — allowed
        with pytest.raises(ValueError, match="exceeds MAX_DEPTH"):
            Blackboard(parent=bb)

    def test_thread_safety(self) -> None:
        bb = Blackboard()
        errors: list[Exception] = []

        def writer(thread_id: int) -> None:
            try:
                for i in range(100):
                    bb.set(f"t{thread_id}_{i}", i)
            except Exception as e:
                errors.append(e)

        def reader(thread_id: int) -> None:
            try:
                for i in range(100):
                    bb.get(f"t{thread_id}_{i}")
                    bb.has(f"t{thread_id}_{i}")
                    bb.all_keys()
            except Exception as e:
                errors.append(e)

        threads: list[threading.Thread] = []
        for tid in range(4):
            threads.append(threading.Thread(target=writer, args=(tid,)))
            threads.append(threading.Thread(target=reader, args=(tid,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []

    def test_create_child(self) -> None:
        parent = Blackboard()
        child = parent.create_child()
        assert child._parent is parent
        assert child._depth == 1

    def test_blackboard_plan_create(self) -> None:
        plan = BlackboardPlan({"count": int, "name": str, "values": list})
        bb = plan.create_blackboard()
        assert bb.get("count") == 0
        assert bb.get("name") == ""
        assert bb.get("values") == []

    def test_blackboard_plan_validate(self) -> None:
        plan = BlackboardPlan({"count": int, "name": str})
        bb = Blackboard()
        bb.set("count", 5)
        bb.set("name", "test")
        assert plan.validate(bb) == []

        bb2 = Blackboard()
        bb2.set("count", "not_an_int")
        errors = plan.validate(bb2)
        assert len(errors) == 2  # wrong type for count + missing name
        assert any("count" in e for e in errors)
        assert any("name" in e for e in errors)

    def test_to_dict(self) -> None:
        parent = Blackboard()
        parent.set("parent_key", "parent_val")
        child = Blackboard(parent=parent)
        child.set("child_key", "child_val")
        snapshot = child.to_dict()
        assert snapshot == {"child_key": "child_val"}
        assert "parent_key" not in snapshot

    def test_all_keys(self) -> None:
        parent = Blackboard()
        parent.set("a", 1)
        parent.set("b", 2)
        child = Blackboard(parent=parent)
        child.set("b", 20)
        child.set("c", 3)
        keys = child.all_keys()
        assert keys == {"a", "b", "c"}
