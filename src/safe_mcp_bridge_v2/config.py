from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml

from .errors import ConfigurationError

MODERN_VERSION = "2026-07-28"
HEADER_NAME = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


@dataclass(slots=True)
class TargetConfig:
    url: str
    timeout_seconds: float = 30.0
    verify_tls: bool = True


@dataclass(slots=True)
class AuthConfig:
    mode: str = "env_bearer"
    env: str = ""
    header: str = "Authorization"
    prefix: str = "Bearer"

    def header_value(self) -> str:
        if self.mode == "none":
            return ""
        if self.mode != "env_bearer":
            raise ConfigurationError(f"Unsupported auth mode: {self.mode}")
        if not self.env:
            raise ConfigurationError("auth.env is required for env_bearer")
        value = os.getenv(self.env)
        if not value:
            raise ConfigurationError(f"Credential environment variable is not set: {self.env}")
        return f"{self.prefix} {value}".strip()


@dataclass(slots=True)
class PolicyConfig:
    mode: str = "allowlist"
    allow_tools: list[str] = field(default_factory=list)
    deny_tools: list[str] = field(default_factory=list)
    allow_methods: list[str] = field(
        default_factory=lambda: [
            "initialize",
            "notifications/initialized",
            "server/discover",
            "tools/list",
            "tools/call",
            "resources/list",
            "resources/read",
            "prompts/list",
            "prompts/get",
            "subscriptions/listen",
        ]
    )


@dataclass(slots=True)
class AuditConfig:
    path: str = "./logs/safe-mcp-bridge-v2.jsonl"
    enabled: bool = True


@dataclass(slots=True)
class ProtocolConfig:
    version: str = MODERN_VERSION
    client_name: str = "safe-mcp-bridge-v2"
    client_version: str = "0.1.0"
    custom_tool_headers: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass(slots=True)
class RedactionConfig:
    fail_on_secret_output: bool = True


@dataclass(slots=True)
class BridgeConfig:
    target: TargetConfig
    auth: AuthConfig = field(default_factory=AuthConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    protocol: ProtocolConfig = field(default_factory=ProtocolConfig)
    redaction: RedactionConfig = field(default_factory=RedactionConfig)


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigurationError(f"{name} must be a mapping")
    return value


def load_config(path: str | Path) -> BridgeConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ConfigurationError("Config root must be a mapping")
    target = _mapping(raw.get("target"), "target")
    if not target.get("url"):
        raise ConfigurationError("target.url is required")
    auth = _mapping(raw.get("auth"), "auth")
    if "value" in auth:
        raise ConfigurationError("Inline auth.value is forbidden; use auth.env")
    config = BridgeConfig(
        target=TargetConfig(**target),
        auth=AuthConfig(**auth),
        policy=PolicyConfig(**_mapping(raw.get("policy"), "policy")),
        audit=AuditConfig(**_mapping(raw.get("audit"), "audit")),
        protocol=ProtocolConfig(**_mapping(raw.get("protocol"), "protocol")),
        redaction=RedactionConfig(**_mapping(raw.get("redaction"), "redaction")),
    )
    if config.protocol.version != MODERN_VERSION:
        raise ConfigurationError(f"Only MCP {MODERN_VERSION} is supported")
    if config.policy.mode not in {"allowlist", "read_only"}:
        raise ConfigurationError("policy.mode must be allowlist or read_only")
    _validate_security(config)
    return config


def _validate_security(config: BridgeConfig) -> None:
    target = urlsplit(config.target.url)
    if target.scheme not in {"http", "https"} or not target.hostname:
        raise ConfigurationError("target.url must be an absolute HTTP(S) URL")
    if target.username or target.password:
        raise ConfigurationError("Credentials in target.url are forbidden")
    if target.scheme != "https" and target.hostname not in LOCAL_HOSTS:
        raise ConfigurationError("Remote MCP targets must use HTTPS")
    if not config.target.verify_tls and target.hostname not in LOCAL_HOSTS:
        raise ConfigurationError("TLS verification may only be disabled for localhost")
    if not HEADER_NAME.fullmatch(config.auth.header):
        raise ConfigurationError("auth.header is not a valid HTTP field name")
    if any(character in config.auth.prefix for character in "\r\n"):
        raise ConfigurationError("auth.prefix contains forbidden control characters")
    for mappings in config.protocol.custom_tool_headers.values():
        for header_name in mappings.values():
            if not HEADER_NAME.fullmatch(header_name):
                raise ConfigurationError(
                    f"Invalid x-mcp-header mapping name: {header_name!r}"
                )
