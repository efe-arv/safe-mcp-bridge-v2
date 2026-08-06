from __future__ import annotations

import json
import re
from typing import Any

REDACTED = "<REDACTED>"
PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\b(?:sk-|ghp_|github_pat_|xox[baprs]-)[_A-Za-z0-9-]{10,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,}\b"),
    re.compile(r"(?i)(authorization|api[_-]?key|token|secret|password)(\s*[:=]\s*)([^\s,;]+)"),
)
SENSITIVE_KEYS = re.compile(
    r"(?i)(?:^|[_-])(authorization|api[_-]?key|token|secret|password|credential)(?:$|[_-])"
)


def redact_text(text: str) -> str:
    output = text
    for pattern in PATTERNS:
        if pattern.groups >= 3:
            output = pattern.sub(
                lambda match: f"{match.group(1)}{match.group(2)}{REDACTED}", output
            )
        else:
            output = pattern.sub(REDACTED, output)
    return output


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): REDACTED if SENSITIVE_KEYS.search(str(key)) else redact(item)
            for key, item in value.items()
        }
    return value


def contains_secret(value: Any) -> bool:
    if isinstance(value, dict):
        if any(SENSITIVE_KEYS.search(str(key)) for key in value):
            return True
        return any(contains_secret(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_secret(item) for item in value)
    serialized = json.dumps(value, ensure_ascii=False, default=str)
    return redact_text(serialized) != serialized
