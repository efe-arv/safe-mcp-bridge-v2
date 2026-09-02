from __future__ import annotations

from safe_mcp_bridge_v2.bridge import Bridge
from safe_mcp_bridge_v2.config import BridgeConfig, TargetConfig


def test_legacy_initialize_negotiates_the_client_protocol_without_upstream_transport() -> None:
    bridge = Bridge(BridgeConfig(target=TargetConfig(url="http://127.0.0.1:1/mcp")))
    response = list(
        bridge.handle(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-11-25"},
            }
        )
    )
    assert response[0]["id"] == 1
    assert response[0]["result"]["protocolVersion"] == "2025-11-25"
    assert response[0]["result"]["capabilities"]["tools"] == {"listChanged": False}


def test_legacy_initialized_notification_is_ignored() -> None:
    bridge = Bridge(BridgeConfig(target=TargetConfig(url="http://127.0.0.1:1/mcp")))
    assert list(bridge.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})) == []


def test_legacy_initialize_rejects_protocol_downgrade() -> None:
    bridge = Bridge(BridgeConfig(target=TargetConfig(url="http://127.0.0.1:1/mcp")))
    response = list(
        bridge.handle(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05"},
            }
        )
    )
    assert response[0]["error"]["code"] == -32602


def test_initialized_notification_with_id_is_rejected() -> None:
    bridge = Bridge(BridgeConfig(target=TargetConfig(url="http://127.0.0.1:1/mcp")))
    response = list(
        bridge.handle(
            {
                "jsonrpc": "2.0",
                "id": "not-a-notification",
                "method": "notifications/initialized",
            }
        )
    )
    assert response[0]["error"]["code"] == -32600
