from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from safe_mcp_bridge_v2.bridge import Bridge
from safe_mcp_bridge_v2.config import (
    AuditConfig,
    AuthConfig,
    BridgeConfig,
    PolicyConfig,
    TargetConfig,
)


class FakeTransport:
    def __init__(self, responses: list[dict[str, Any]]):
        self.responses = responses
        self.calls: list[tuple[dict[str, Any], dict[str, str]]] = []

    def send(
        self, request: dict[str, Any], headers: dict[str, str]
    ) -> Iterator[dict[str, Any]]:
        self.calls.append((request, headers))
        yield from self.responses


def bridge(monkeypatch: Any, responses: list[dict[str, Any]]) -> tuple[Bridge, FakeTransport]:
    monkeypatch.setenv("TEST_TOKEN", "bridge-test-token-value")
    config = BridgeConfig(
        target=TargetConfig("https://example.com/mcp"),
        auth=AuthConfig(env="TEST_TOKEN"),
        policy=PolicyConfig(allow_tools=["memory.search"]),
        audit=AuditConfig(enabled=False),
    )
    instance = Bridge(config)
    fake = FakeTransport(responses)
    instance.transport = fake  # type: ignore[assignment]
    return instance, fake


def test_bridge_injects_auth_and_modern_headers(monkeypatch: Any) -> None:
    instance, fake = bridge(monkeypatch, [{"jsonrpc": "2.0", "id": 1, "result": {}}])
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "memory.search", "arguments": {}},
    }
    assert list(instance.handle(request))[0]["result"] == {}
    headers = fake.calls[0][1]
    assert headers["Authorization"] == "Bearer bridge-test-token-value"
    assert headers["Mcp-Method"] == "tools/call"
    assert headers["Mcp-Name"] == "memory.search"


def test_blocked_tool_never_reaches_transport(monkeypatch: Any) -> None:
    instance, fake = bridge(monkeypatch, [])
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "x"}}
    response = list(instance.handle(request))[0]
    assert response["error"]["code"] == -32001
    assert not fake.calls


def test_secret_shaped_upstream_output_fails_closed(monkeypatch: Any) -> None:
    instance, _ = bridge(
        monkeypatch,
        [{"jsonrpc": "2.0", "id": 1, "result": {"token": "abcdefghijklmnop"}}],
    )
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "memory.search"},
    }
    response = list(instance.handle(request))[0]
    assert response["error"]["code"] == -32002

