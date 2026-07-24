# Security Policy

## Supported release

Security fixes are applied to the latest tagged MarketForge AI release. Older
research snapshots and superseded benchmark protocols are retained for
reproducibility, but they are not active support branches.

## Reporting a vulnerability

Use GitHub's **Report a vulnerability** / private Security Advisory feature.
Do not open a public issue for an unpatched vulnerability. Include:

- the affected MarketForge version or commit;
- clear reproduction steps using synthetic data;
- the expected security impact;
- any safe mitigation you have already identified.

Never attach API keys, passwords, exchange secrets, personal account exports,
private datasets or unredacted server logs. MarketForge only requires ordinary
candle data and does not require exchange trading credentials.

## Deployment boundary

The default configuration binds to the local machine. Anyone exposing the app
to a network should place it behind an authenticated, rate-limited reverse
proxy, set `MARKETFORGE_ALLOWED_HOSTS`, keep API documentation disabled, and
apply normal operating-system and container updates. MarketForge is a research
application, not an exchange execution service.

## Benchmark integrity

A change to benchmark-bound code after preregistration is not treated as a
security patch to the same protocol. Create a new benchmark identifier and
record why the old protocol was superseded.
