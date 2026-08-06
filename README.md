# safe-mcp-bridge-v2

**A fail-closed policy boundary between local stdio MCP clients and authenticated Streamable HTTP servers.**

[![CI](https://github.com/efe-arv/safe-mcp-bridge-v2/actions/workflows/ci.yml/badge.svg)](https://github.com/efe-arv/safe-mcp-bridge-v2/actions/workflows/ci.yml)
[![MCP](https://img.shields.io/badge/MCP-2026--07--28-5A67D8)](https://modelcontextprotocol.io/specification/2026-07-28)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

MCP's authorization standard answers **who may connect**. This bridge adds a local enforcement layer for **what an agent may call** and **what must never leak through the bridge's logs or output**.

It translates newline-delimited stdio JSON-RPC into MCP `2026-07-28` Streamable HTTP, injects credentials only at the outbound boundary, mirrors required routing metadata into HTTP headers, applies a local tool policy before network access, and fails closed on secret-shaped upstream output.

## Why this still exists after MCP OAuth

OAuth, CIMD, scopes, and protected-resource metadata are essential remote authorization primitives. They do not replace:

- per-agent local allowlists;
- a conservative read-only mode;
- proof that blocked calls never reach the upstream server;
- redacted audit trails;
- leak fixtures for wrapper and gateway behavior;
- env-to-header credential isolation for local stdio clients.

`safe-mcp-bridge-v2` is deliberately a narrow safety boundary, not another general MCP platform.

## MCP 2026-07-28 support

- stateless, self-describing requests with `_meta` protocol/client fields;
- required `MCP-Protocol-Version`, `Mcp-Method`, and `Mcp-Name` headers;
- spec Base64 sentinel encoding for non-ASCII or unsafe header values;
- configured `Mcp-Param-*` mirroring for `x-mcp-header` deployments;
- `application/json` and request-scoped `text/event-stream` responses;
- transparent MRTR `InputRequiredResult` pass-through;
- `202 Accepted` notification handling;
- optional isolated legacy-initialize adapter;
- fail-closed header/body and protocol-version checks.

See [Compatibility](docs/compatibility.md) for the exact support boundary.

## Quick start

```bash
git clone https://github.com/efe-arv/safe-mcp-bridge-v2.git
cd safe-mcp-bridge-v2
uv sync --extra dev
cp examples/modern-read-only.yaml bridge.yaml
```

Set the credential named by `auth.env` without placing it in YAML:

```bash
export EXAMPLE_MCP_TOKEN='use-your-secret-manager-here'
uv run safe-mcp-bridge-v2 doctor bridge.yaml
uv run safe-mcp-bridge-v2 run bridge.yaml
```

Example stdio input:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"memory.search","arguments":{"query":"status"}}}
```

The bridge adds modern MCP metadata and sends headers equivalent to:

```http
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tools/call
Mcp-Name: memory.search
Authorization: Bearer <injected at runtime>
```

Credentials are never included in audit records.

## Policy modes

### Allowlist

Only explicitly named tools may cross the network boundary:

```yaml
policy:
  mode: allowlist
  allow_tools:
    - memory.search
    - memory.read
```

### Read-only

Blocks tool names containing write-shaped segments such as `create`, `delete`, `send`, `update`, or `write`:

```yaml
policy:
  mode: read_only
```

Read-only name matching is a conservative local guard, not semantic proof. Prefer an allowlist for consequential environments.

## `x-mcp-header` deployments

The 2026-07-28 HTTP binding can mirror selected primitive tool arguments into `Mcp-Param-*` headers. Configure mappings learned from your server's tool schema:

```yaml
protocol:
  custom_tool_headers:
    execute_sql:
      region: Region
      tenant.id: Tenant
```

The bridge performs spec-compliant primitive conversion and Base64 sentinel encoding. Automatic schema discovery is intentionally not in `0.1.0`; mappings are explicit and auditable.

## Commands

```text
safe-mcp-bridge-v2 doctor CONFIG
safe-mcp-bridge-v2 run CONFIG
safe-mcp-bridge-v2 policy-check CONFIG METHOD [--tool TOOL]
safe-mcp-bridge-v2 leak-scan PATH
```

## Verification

```bash
uv run ruff check .
uv run mypy
uv run pytest
```

CI runs the same checks on Python 3.11 and 3.12, plus dependency and secret scanning.

## Security model

Read [SECURITY.md](SECURITY.md) and [Threat model](docs/threat-model.md) before deployment. Important boundaries:

- redaction is defense in depth, not encryption;
- upstream authorization and data minimization remain mandatory;
- an allowlist cannot make a malicious upstream safe;
- this bridge does not terminate an OAuth browser flow in `0.1.0`;
- local process compromise remains outside the bridge's protection boundary.

## Origin

This is a clean second-generation implementation of the original private `safe-mcp-bridge`, rebuilt for the MCP `2026-07-28` stateless protocol. Created by Efe Büken / Arven Digital.

## License

Apache-2.0. See [LICENSE](LICENSE).

