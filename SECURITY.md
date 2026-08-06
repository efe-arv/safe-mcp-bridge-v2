# Security Policy

## Supported versions

Security fixes are provided for the latest released minor version.

## Reporting a vulnerability

Please use GitHub private vulnerability reporting for this repository. Do not open a public issue containing credentials, exploit details, private endpoints, or sensitive logs.

Reports should include:

- affected version and commit;
- minimal reproduction using synthetic credentials;
- expected and observed policy behavior;
- whether a denied request reached an upstream fixture;
- whether any secret-shaped value entered stdout, stderr, or audit output.

Never send a real token. Synthetic fixtures are sufficient.

## Release gate

Before a release:

1. tests, lint, and type checking must pass;
2. dependency audit must report no known actionable vulnerability;
3. current tree and git history must pass secret scanning;
4. blocked-call and leak fixtures must pass;
5. compatibility claims must match the implemented MCP revision.

