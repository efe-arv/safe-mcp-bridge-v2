from __future__ import annotations

import json
from typing import Any

import pytest

from safe_mcp_bridge_v2.config import TargetConfig
from safe_mcp_bridge_v2.errors import BridgeError
from safe_mcp_bridge_v2.transport import StreamableHttpTransport, _parse_sse


def test_sse_parser_ignores_comments_and_yields_messages() -> None:
    lines = iter(
        [
            ": keepalive",
            "",
            'data: {"jsonrpc":"2.0","method":"notifications/progress"}',
            "",
            'data: {"jsonrpc":"2.0","id":1,"result":{"ok":true}}',
            "",
        ]
    )
    messages = list(_parse_sse(lines))
    assert len(messages) == 2
    assert messages[-1]["result"]["ok"]


def test_malformed_sse_fails() -> None:
    with pytest.raises(BridgeError, match="Malformed JSON"):
        list(_parse_sse(iter(["data: nope", ""])))


def test_json_transport(httpx_mock: Any) -> None:
    httpx_mock.add_response(json={"jsonrpc": "2.0", "id": 1, "result": {"ok": True}})
    transport = StreamableHttpTransport(TargetConfig("https://example.com/mcp"))
    messages = list(transport.send({"jsonrpc": "2.0", "id": 1}, {"Accept": "application/json"}))
    assert messages[0]["result"]["ok"]


def test_sse_transport(httpx_mock: Any) -> None:
    body = 'data: {"jsonrpc":"2.0","id":1,"result":{"ok":true}}\n\n'
    httpx_mock.add_response(headers={"content-type": "text/event-stream"}, content=body)
    transport = StreamableHttpTransport(TargetConfig("https://example.com/mcp"))
    messages = list(transport.send({"jsonrpc": "2.0", "id": 1}, {}))
    assert messages[0]["result"]["ok"]


def test_http_error_does_not_echo_body(httpx_mock: Any) -> None:
    httpx_mock.add_response(status_code=500, content=b"Bearer abcdefghijklmnop")
    transport = StreamableHttpTransport(TargetConfig("https://example.com/mcp"))
    message = list(transport.send({"jsonrpc": "2.0", "id": 1}, {}))[0]
    assert message["error"]["message"] == "Upstream HTTP 500"
    assert "Bearer" not in json.dumps(message)
