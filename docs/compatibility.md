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
| Legacy `initialize` forwarding | Optional isolated mode |
| HTTP+SSE 2024 transport | Not supported |
| OAuth browser flow / CIMD registration | Not implemented |
| Automatic `x-mcp-header` schema discovery | Not implemented |

## Deliberate boundaries

The first release uses runtime environment credentials for a local stdio process. This follows the MCP authorization specification's guidance for stdio deployments. It is not a generic OAuth client and does not claim to replace an SDK.

Custom header mappings are explicit so the operator can audit which tool arguments leave the JSON body as routing headers. A future release may discover validated `x-mcp-header` annotations from `tools/list`, cache them by upstream identity, and refresh on `HeaderMismatch`.

## Legacy mode

Set `protocol.legacy_mode` to a non-`off` value only for a known legacy upstream. Legacy traffic is forwarded without pretending it conforms to the stateless revision. The modern path remains the default.

