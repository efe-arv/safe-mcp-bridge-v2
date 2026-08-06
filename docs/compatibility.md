# Compatibility

## Supported in 0.1.0

| Surface | Status |
|---|---|
| MCP `2026-07-28` stateless request metadata | Supported |
| `MCP-Protocol-Version` / `Mcp-Method` / `Mcp-Name` | Supported |
| Base64 sentinel header encoding | Supported |
| `Mcp-Param-*` mirroring | Explicit configured mappings |
| JSON response | Supported |
| Request-scoped SSE response | Supported |
| MRTR result pass-through | Supported |
| `202 Accepted` notification response | Supported |
| `subscriptions/listen` | Allowed; caller controls process lifetime |
| Legacy `initialize` / stateful sessions | Not supported |
| HTTP+SSE 2024 transport | Not supported |
| OAuth browser flow / CIMD registration | Not implemented |
| Automatic `x-mcp-header` schema discovery | Not implemented |

## Deliberate boundaries

The first release uses runtime environment credentials for a local stdio process. This follows the MCP authorization specification's guidance for stdio deployments. It is not a generic OAuth client and does not claim to replace an SDK.

Custom header mappings are explicit so the operator can audit which tool arguments leave the JSON body as routing headers. A future release may discover validated `x-mcp-header` annotations from `tools/list`, cache them by upstream identity, and refresh on `HeaderMismatch`.

## Legacy deployments

This repository intentionally targets the stateless MCP `2026-07-28` era. Stateful `2025-*` sessions have different lifecycle, cancellation, and server-to-client request semantics; forwarding only their `initialize` message would create false compatibility. Use the original bridge for a known legacy deployment or contribute a separately tested compatibility adapter.
