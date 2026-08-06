# Architecture

```text
local MCP client
  │ newline-delimited JSON-RPC over stdio
  ▼
request parser
  ├─ policy gate (before network access)
  ├─ modern metadata normalizer
  ├─ header mirror + safe value encoder
  ├─ runtime credential injection
  └─ redacted audit receipt
  ▼
MCP 2026-07-28 Streamable HTTP endpoint
  │ application/json or request-scoped SSE
  ▼
response parser
  ├─ secret-shape detector
  ├─ fail-closed output policy
  └─ JSON-RPC messages back to stdio
```

## Invariants

1. A denied request is never passed to the HTTP transport.
2. Credentials are read from the environment at the final outbound boundary.
3. Audit records contain header names, never header values.
4. Modern requests carry matching body and HTTP protocol metadata.
5. Unsafe header values use the MCP Base64 sentinel encoding.
6. Unexpected content types, malformed SSE, and secret-shaped outputs fail closed.

## Components

- `config.py`: strict configuration and inline-secret rejection.
- `policy.py`: method gate, explicit deny, allowlist, and conservative read-only mode.
- `protocol.py`: MCP metadata, standard headers, custom argument headers, encoding.
- `transport.py`: POST-only modern Streamable HTTP with JSON/SSE response parsing.
- `redaction.py`: structured and text redaction of common credential shapes.
- `audit.py`: append-only redacted JSONL receipts.
- `bridge.py`: orchestration and fail-closed error conversion.
- `cli.py`: stdio runner and operator checks.

