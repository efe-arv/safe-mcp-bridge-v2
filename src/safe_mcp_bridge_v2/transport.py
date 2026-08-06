from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx

from .config import TargetConfig
from .errors import BridgeError


class StreamableHttpTransport:
    def __init__(self, target: TargetConfig):
        self.target = target

    def send(
        self, request: dict[str, Any], headers: dict[str, str]
    ) -> Iterator[dict[str, Any]]:
        try:
            with httpx.Client(
                timeout=self.target.timeout_seconds,
                verify=self.target.verify_tls,
                follow_redirects=False,
            ) as client:
                with client.stream(
                    "POST", self.target.url, json=request, headers=headers
                ) as response:
                    if response.status_code == 202:
                        return
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
                    if response.is_error:
                        body = response.read()
                        yield _http_error(response.status_code, body)
                        return
                    if content_type == "application/json":
                        payload = json.loads(response.read())
                        if not isinstance(payload, dict):
                            raise BridgeError(-32603, "Upstream JSON response must be an object")
                        yield payload
                        return
                    if content_type == "text/event-stream":
                        yield from _parse_sse(response.iter_lines())
                        return
                    raise BridgeError(-32603, f"Unsupported upstream content type: {content_type}")
        except httpx.HTTPError as exc:
            raise BridgeError(
                -32098,
                "Upstream transport failure",
                {"type": type(exc).__name__},
            ) from exc
        except json.JSONDecodeError as exc:
            raise BridgeError(-32700, "Upstream returned malformed JSON") from exc


def _parse_sse(lines: Iterator[str]) -> Iterator[dict[str, Any]]:
    data: list[str] = []
    for line in lines:
        if line.startswith(":"):
            continue
        if line == "":
            if data:
                yield _decode_sse_data("\n".join(data))
                data = []
            continue
        if line.startswith("data:"):
            data.append(line[5:].lstrip(" "))
    if data:
        yield _decode_sse_data("\n".join(data))


def _decode_sse_data(data: str) -> dict[str, Any]:
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise BridgeError(-32700, "Malformed JSON in upstream SSE event") from exc
    if not isinstance(payload, dict):
        raise BridgeError(-32603, "Upstream SSE data must contain a JSON object")
    return payload


def _http_error(status: int, body: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict) and "error" in parsed:
            return parsed
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32000 - min(status, 999), "message": f"Upstream HTTP {status}"},
    }
