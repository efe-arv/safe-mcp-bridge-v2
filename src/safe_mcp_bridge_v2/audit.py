from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import AuditConfig
from .redaction import redact


class AuditLog:
    def __init__(self, config: AuditConfig):
        self.config = config

    def write(self, event: str, **fields: Any) -> None:
        if not self.config.enabled:
            return
        path = Path(self.config.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = redact({"timestamp": datetime.now(UTC).isoformat(), "event": event, **fields})
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

