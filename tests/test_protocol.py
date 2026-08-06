from __future__ import annotations

import base64

import pytest

from safe_mcp_bridge_v2.config import ProtocolConfig
from safe_mcp_bridge_v2.errors import BridgeError
from safe_mcp_bridge_v2.protocol import (
    CLIENT_CAPS_META,
    CLIENT_INFO_META,
    PROTOCOL_META,
    build_modern_headers,
    decode_header_value,
    encode_header_value,
    prepare_request,
)


def test_modern_request_gets_self_describing_metadata_and_headers() -> None:
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "memory.search", "arguments": {"query": "status"}},
    }
    prepared, headers, era = prepare_request(request, ProtocolConfig())
    meta = prepared["params"]["_meta"]
    assert era.modern
    assert meta[PROTOCOL_META] == "2026-07-28"
    assert meta[CLIENT_INFO_META]["name"] == "safe-mcp-bridge-v2"
    assert meta[CLIENT_CAPS_META] == {}
    assert headers["MCP-Protocol-Version"] == "2026-07-28"
    assert headers["Mcp-Method"] == "tools/call"
    assert headers["Mcp-Name"] == "memory.search"
    assert "_meta" not in request["params"]


def test_non_ascii_name_uses_spec_base64_sentinel() -> None:
    raw = "araç/bul"
    encoded = encode_header_value(raw)
    assert encoded == f"=?base64?{base64.b64encode(raw.encode()).decode()}?="
    assert decode_header_value(encoded) == raw


def test_existing_sentinel_is_encoded_to_avoid_ambiguity() -> None:
    raw = "=?base64?literal?="
    assert decode_header_value(encode_header_value(raw)) == raw


def test_protocol_metadata_mismatch_fails_closed() -> None:
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {"_meta": {PROTOCOL_META: "2025-11-25"}},
    }
    with pytest.raises(BridgeError, match="Protocol metadata"):
        prepare_request(request, ProtocolConfig())


def test_required_named_method_value_is_enforced() -> None:
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "resources/read",
        "params": {
            "_meta": {
                PROTOCOL_META: "2026-07-28",
                CLIENT_INFO_META: {"name": "test", "version": "1"},
                CLIENT_CAPS_META: {},
            }
        },
    }
    with pytest.raises(BridgeError, match="params.uri"):
        build_modern_headers(request, ProtocolConfig())


def test_configured_tool_parameter_headers_are_mirrored() -> None:
    config = ProtocolConfig(custom_tool_headers={"execute": {"region": "Region", "safe.ok": "Ok"}})
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "execute",
            "arguments": {"region": "us-west1", "safe": {"ok": True}},
            "_meta": {
                PROTOCOL_META: "2026-07-28",
                CLIENT_INFO_META: {"name": "test", "version": "1"},
                CLIENT_CAPS_META: {},
            },
        },
    }
    headers = build_modern_headers(request, config)
    assert headers["Mcp-Param-Region"] == "us-west1"
    assert headers["Mcp-Param-Ok"] == "true"


def test_initialize_is_rejected_when_legacy_is_off() -> None:
    with pytest.raises(BridgeError, match="Legacy initialize"):
        prepare_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"}, ProtocolConfig())

