from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .audit import AuditLog
from .config import BridgeConfig
from .errors import BridgeError
from .policy import Policy
from .protocol import prepare_request
from .redaction import contains_secret, redact
from .transport import StreamableHttpTransport

OPENCLAW_COMPAT_PROTOCOL = "2025-11-25"


class Bridge:
    def __init__(self, config: BridgeConfig):
        self.config = config
        self.policy = Policy(config.policy)
        self.audit = AuditLog(config.audit)
        self.transport = StreamableHttpTransport(config.target)

    def handle(self, request: dict[str, Any]) -> Iterator[dict[str, Any]]:
        request_id = request.get("id")
        audit_request_id = redact(request_id)
        method = request.get("method")
        decision = self.policy.evaluate(request)
        self.audit.write(
            "policy_decision",
            request_id=audit_request_id,
            method=method,
            tool=decision.tool,
            allowed=decision.allowed,
            reason=decision.reason,
        )
        if not decision.allowed:
            yield BridgeError(
                -32001,
                "Request blocked by safe-mcp-bridge-v2 policy",
                {"reason": decision.reason, "tool": decision.tool},
            ).as_jsonrpc(request_id)
            return
        if method == "initialize":
            params = request.get("params")
            requested_protocol = (
                params.get("protocolVersion") if isinstance(params, dict) else None
            )
            if requested_protocol != OPENCLAW_COMPAT_PROTOCOL:
                yield BridgeError(
                    -32602,
                    "Unsupported legacy MCP protocol version",
                    {"requested": requested_protocol},
                ).as_jsonrpc(request_id)
                return
            self.audit.write(
                "legacy_initialize_adapted",
                request_id=audit_request_id,
                method=method,
                protocol_version=requested_protocol,
            )
            yield {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": requested_protocol,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {
                        "name": "safe-mcp-bridge-v2",
                        "version": "0.1.1-legacy-init-adapter",
                    },
                },
            }
            return
        if method == "notifications/initialized":
            if request_id is not None:
                yield BridgeError(
                    -32600, "notifications/initialized must not include an id"
                ).as_jsonrpc(request_id)
                return
            self.audit.write(
                "legacy_initialized_notification_ignored",
                request_id=None,
                method=method,
            )
            return
        try:
            prepared, protocol_headers, era = prepare_request(request, self.config.protocol)
            headers = dict(protocol_headers)
            auth_value = self.config.auth.header_value()
            if auth_value:
                headers[self.config.auth.header] = auth_value
            self.audit.write(
                "upstream_request",
                request_id=audit_request_id,
                method=prepared.get("method"),
                protocol_era="modern" if era.modern else "legacy",
                header_names=sorted(headers),
            )
            for response in self.transport.send(prepared, headers):
                if contains_secret(response):
                    self.audit.write("secret_output_detected", request_id=audit_request_id)
                    if self.config.redaction.fail_on_secret_output:
                        yield BridgeError(
                            -32002, "Upstream response contained secret-shaped material"
                        ).as_jsonrpc(request_id)
                        return
                    response = redact(response)
                yield response
        except BridgeError as exc:
            self.audit.write(
                "bridge_error", request_id=audit_request_id, code=exc.code, message=exc.message
            )
            yield exc.as_jsonrpc(request_id)
