from __future__ import annotations

from safe_mcp_bridge_v2.config import PolicyConfig
from safe_mcp_bridge_v2.policy import Policy


def call(tool: str) -> dict[str, object]:
    return {"method": "tools/call", "params": {"name": tool}}


def test_allowlist_only_allows_named_tools() -> None:
    policy = Policy(PolicyConfig(mode="allowlist", allow_tools=["memory.search"]))
    assert policy.evaluate(call("memory.search")).allowed
    assert not policy.evaluate(call("memory.delete")).allowed


def test_explicit_deny_wins() -> None:
    policy = Policy(
        PolicyConfig(
            mode="allowlist",
            allow_tools=["memory.search"],
            deny_tools=["memory.search"],
        )
    )
    assert policy.evaluate(call("memory.search")).reason == "explicit_deny"


def test_read_only_blocks_write_shaped_tool_names() -> None:
    policy = Policy(PolicyConfig(mode="read_only"))
    assert policy.evaluate(call("memory.search")).allowed
    assert not policy.evaluate(call("memory.project_write")).allowed
    assert not policy.evaluate(call("control.task.create")).allowed


def test_unknown_method_is_blocked() -> None:
    decision = Policy(PolicyConfig()).evaluate({"method": "dangerous/custom"})
    assert not decision.allowed
    assert decision.reason == "method_not_allowed"
