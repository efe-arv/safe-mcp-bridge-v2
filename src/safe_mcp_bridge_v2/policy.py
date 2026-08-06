from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import PolicyConfig

WRITE_WORDS = {
    "append",
    "apply",
    "approve",
    "create",
    "delete",
    "execute",
    "merge",
    "post",
    "publish",
    "remove",
    "run",
    "send",
    "set",
    "update",
    "write",
}


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    reason: str
    tool: str | None = None


class Policy:
    def __init__(self, config: PolicyConfig):
        self.config = config

    def evaluate(self, request: dict[str, Any]) -> Decision:
        method = request.get("method")
        if not isinstance(method, str):
            return Decision(False, "missing_or_invalid_method")
        if method not in self.config.allow_methods:
            return Decision(False, "method_not_allowed")
        if method != "tools/call":
            return Decision(True, "method_allowed")
        params = request.get("params")
        tool = params.get("name") if isinstance(params, dict) else None
        if not isinstance(tool, str) or not tool:
            return Decision(False, "missing_tool_name")
        if tool in self.config.deny_tools:
            return Decision(False, "explicit_deny", tool)
        if self.config.mode == "allowlist":
            return Decision(tool in self.config.allow_tools, "allowlist", tool)
        normalized = tool.replace("-", ".").replace("_", ".")
        segments = {segment.lower() for segment in normalized.split(".")}
        if segments & WRITE_WORDS:
            return Decision(False, "read_only_policy_blocks_write_shaped_tool", tool)
        return Decision(True, "read_only_policy", tool)
