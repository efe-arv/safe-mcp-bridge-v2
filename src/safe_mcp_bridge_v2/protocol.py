from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from .config import MODERN_VERSION, ProtocolConfig
from .errors import BridgeError

PROTOCOL_META = "io.modelcontextprotocol/protocolVersion"
CLIENT_INFO_META = "io.modelcontextprotocol/clientInfo"
CLIENT_CAPS_META = "io.modelcontextprotocol/clientCapabilities"
NAMED_METHODS = {"tools/call": "name", "prompts/get": "name", "resources/read": "uri"}


def encode_header_value(value: str) -> str:
    safe = all(character == "\t" or 0x20 <= ord(character) <= 0x7E for character in value)
    sentinel = value.startswith("=?base64?") and value.endswith("?=")
    if safe and value == value.strip() and not sentinel:
        return value
    encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
    return f"=?base64?{encoded}?="


def decode_header_value(value: str) -> str:
    if value.startswith("=?base64?") and value.endswith("?="):
        payload = value[len("=?base64?") : -2]
        try:
            return base64.b64decode(payload, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise BridgeError(-32020, "Malformed base64 header sentinel") from exc
    return value


def ensure_modern_metadata(request: dict[str, Any], config: ProtocolConfig) -> None:
    params = request.setdefault("params", {})
    if not isinstance(params, dict):
        raise BridgeError(-32602, "params must be an object")
    meta = params.setdefault("_meta", {})
    if not isinstance(meta, dict):
        raise BridgeError(-32602, "params._meta must be an object")
    existing = meta.get(PROTOCOL_META)
    if existing is not None and existing != config.version:
        raise BridgeError(
            -32020,
            "Protocol metadata does not match configured version",
            {"configured": config.version, "body": existing},
        )
    meta.setdefault(PROTOCOL_META, config.version)
    meta.setdefault(
        CLIENT_INFO_META,
        {"name": config.client_name, "version": config.client_version},
    )
    meta.setdefault(CLIENT_CAPS_META, {})


def _primitive_header(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and -(2**53) + 1 <= value <= (2**53) - 1:
        return str(value)
    if isinstance(value, str):
        return encode_header_value(value)
    raise BridgeError(-32602, "Configured MCP header parameter must be string, integer, or boolean")


def _nested(arguments: dict[str, Any], path: str) -> Any:
    current: Any = arguments
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return current


def build_modern_headers(request: dict[str, Any], config: ProtocolConfig) -> dict[str, str]:
    method = request.get("method")
    if not isinstance(method, str) or not method:
        raise BridgeError(-32600, "MCP request requires a method")
    params = request.get("params")
    if not isinstance(params, dict):
        params = {}
    meta = params.get("_meta")
    if not isinstance(meta, dict) or meta.get(PROTOCOL_META) != config.version:
        raise BridgeError(-32020, "Missing or mismatched protocol metadata")
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": config.version,
        "Mcp-Method": method,
    }
    name_key = NAMED_METHODS.get(method)
    if name_key:
        value = params.get(name_key)
        if not isinstance(value, str) or not value:
            raise BridgeError(-32602, f"{method} requires params.{name_key}")
        headers["Mcp-Name"] = encode_header_value(value)
    if method == "tools/call":
        tool = params.get("name")
        arguments = params.get("arguments", {})
        if isinstance(tool, str) and isinstance(arguments, dict):
            mappings = config.custom_tool_headers.get(tool, {})
            for path, header_name in mappings.items():
                value = _nested(arguments, path)
                if value is not None:
                    headers[f"Mcp-Param-{header_name}"] = _primitive_header(value)
    return headers


@dataclass(frozen=True, slots=True)
class ProtocolEra:
    modern: bool
    version: str


def prepare_request(
    request: dict[str, Any], config: ProtocolConfig
) -> tuple[dict[str, Any], dict[str, str], ProtocolEra]:
    cloned = _clone(request)
    if cloned.get("method") in {"initialize", "notifications/initialized"}:
        raise BridgeError(-32601, "Legacy initialize is not supported by the V2 bridge")
    ensure_modern_metadata(cloned, config)
    return cloned, build_modern_headers(cloned, config), ProtocolEra(True, MODERN_VERSION)


def _clone(value: dict[str, Any]) -> dict[str, Any]:
    import copy

    return copy.deepcopy(value)
