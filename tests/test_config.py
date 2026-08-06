from __future__ import annotations

from pathlib import Path

import pytest

from safe_mcp_bridge_v2.config import load_config
from safe_mcp_bridge_v2.errors import ConfigurationError


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_inline_credentials_are_forbidden(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
target:
  url: https://example.com/mcp
auth:
  value: do-not-allow
""",
    )
    with pytest.raises(ConfigurationError, match="Inline auth.value"):
        load_config(path)


def test_minimal_config_loads(tmp_path: Path) -> None:
    config = load_config(write(tmp_path, "target:\n  url: https://example.com/mcp\n"))
    assert config.protocol.version == "2026-07-28"
    assert config.target.verify_tls


def test_remote_plain_http_is_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, "target:\n  url: http://example.com/mcp\n")
    with pytest.raises(ConfigurationError, match="must use HTTPS"):
        load_config(path)


def test_local_plain_http_is_allowed(tmp_path: Path) -> None:
    config = load_config(write(tmp_path, "target:\n  url: http://127.0.0.1:8000/mcp\n"))
    assert config.target.url.startswith("http://127.0.0.1")


def test_header_injection_is_rejected(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
target:
  url: https://example.com/mcp
auth:
  header: "Authorization\\nInjected"
""",
    )
    with pytest.raises(ConfigurationError, match="valid HTTP field"):
        load_config(path)


def test_remote_tls_verification_cannot_be_disabled(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
target:
  url: https://example.com/mcp
  verify_tls: false
""",
    )
    with pytest.raises(ConfigurationError, match="localhost"):
        load_config(path)
