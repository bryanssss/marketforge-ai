# Security Policy

## Supported Release

Security fixes are applied to the latest tagged MarketForge AI release. Older research
snapshots and superseded benchmark protocols are retained for reproducibility, but they
are not active support branches.

## Reporting a Vulnerability

Use GitHub's **Report a vulnerability** or private Security Advisory feature. Do not open
a public issue for an unpatched vulnerability. Include:

- the affected MarketForge version or commit;
- clear reproduction steps using synthetic data;
- the expected security impact;
- any safe mitigation already identified.

Never attach API keys, passwords, exchange secrets, personal account exports, private
datasets, unredacted databases or server logs.

## Public Connector Safety

MarketForge public connectors are read-only and are designed for unauthenticated market
data. They must not be modified to collect trading credentials through the browser.
Provider responses are untrusted and remain subject to request timeouts, size limits and
market-data validation.

Using a public connector still reveals the requested market, timestamp and network
address to the external provider.

## Local Storage

Saved projects, experiments and model records are stored in
`storage/marketforge.db`. This file is excluded from Git but is not encrypted by
MarketForge. Protect the user account and filesystem, and do not store secrets in notes.

## Deployment Boundary

The default configuration binds to the local machine. Anyone exposing the app to a
network should place it behind an authenticated, rate-limited reverse proxy, set
`MARKETFORGE_ALLOWED_HOSTS`, consider disabling interactive API documentation and apply
normal operating-system and container updates.

A hosted instance receives uploaded datasets. Do not describe hosted processing as local
or private unless the deployment architecture genuinely provides those guarantees.

MarketForge is a research application, not an exchange execution service.

## Model and Registry Boundary

The model registry stores descriptive metadata. It must not automatically import or
execute arbitrary third-party code. Optional Kronos source and weights remain third-party
components and must be pinned and verified before benchmark use.

## Benchmark Integrity

A change to benchmark-bound code after preregistration is not treated as a patch to the
same protocol. Create a new benchmark identifier, preserve the old protocol and document
why it was superseded.
