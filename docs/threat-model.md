# Threat model

## Assets

- upstream bearer credentials;
- authority to invoke remote MCP tools;
- sensitive tool results;
- audit integrity;
- consistency between routed HTTP headers and executed JSON-RPC bodies.

## Defended failure modes

- credentials committed inside bridge YAML;
- credentials exposed through audit header values;
- accidental invocation of tools outside a local policy;
- write-shaped calls crossing a read-only boundary;
- non-ASCII or control characters injected into routing headers;
- protocol metadata disagreement;
- secrets echoed by an upstream into bridge-managed output;
- malformed JSON/SSE confusing downstream clients;
- blocked calls reaching the upstream despite a local refusal.

## Out of scope

- a compromised host or Python runtime;
- malicious code executing as the same operating-system user;
- upstream data authorization mistakes;
- semantic proof that a tool is read-only;
- prompt injection inside otherwise authorized tool results;
- safe storage before the credential reaches the environment;
- full OAuth authorization-code handling in `0.1.0`.

## Trust assumptions

The operator controls the bridge configuration and process environment. TLS verification remains enabled. The upstream endpoint is expected to implement its own authentication, authorization, origin validation where applicable, and data minimization.

