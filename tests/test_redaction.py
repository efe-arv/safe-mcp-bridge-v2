from __future__ import annotations

from safe_mcp_bridge_v2.redaction import REDACTED, contains_secret, redact, redact_text


def test_redacts_common_secret_shapes() -> None:
    samples = [
        "Authorization: Bearer abcdefghijklmnop",
        "token=very-secret-value",
        "github_pat_abcdefghijklmnopqrstuvwxyz",
        "eyJhbGciOiJIUzI1NiJ9.abcdef.signature",
    ]
    for sample in samples:
        output = redact_text(sample)
        assert REDACTED in output
        assert sample != output


def test_recursive_redaction_preserves_structure() -> None:
    value = {"result": ["ok", "api_key=abcdefghijklmnop"]}
    cleaned = redact(value)
    assert cleaned["result"][0] == "ok"
    assert REDACTED in cleaned["result"][1]


def test_secret_detection() -> None:
    assert contains_secret({"message": "Bearer abcdefghijklmnop"})
    assert not contains_secret({"message": "ordinary result"})

