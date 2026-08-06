# Contributing

Contributions are welcome when they preserve the bridge's narrow, fail-closed security boundary.

```bash
uv sync --extra dev
uv run ruff check .
uv run mypy
uv run pytest
```

Pull requests that add protocol behavior should include an official MCP specification reference and both positive and negative tests. Security-sensitive changes must prove that denied traffic never reaches the upstream fixture and that credentials do not appear in output or audit records.

Do not include real endpoints, customer data, credentials, private logs, or copied proprietary tool schemas in tests or documentation.

