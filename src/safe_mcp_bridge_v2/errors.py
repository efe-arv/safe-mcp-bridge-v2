from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class BridgeError(Exception):
    code: int
    message: str
    data: dict[str, Any] | None = None

    def as_jsonrpc(self, request_id: Any = None) -> dict[str, Any]:
        error: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data:
            error["data"] = self.data
        return {"jsonrpc": "2.0", "id": request_id, "error": error}


class ConfigurationError(ValueError):
    pass

