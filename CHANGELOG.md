# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] — 2026-05-19

Minor bump: shipping support mirroring `opensalestax-js` and
`ejosterberg/opensalestax` v0.3.0. Engine v0.59.0+ accepts a
top-level `shipping` field on `POST /v1/calculate` and applies
per-state taxability rules. Backward compatible.

### Added

- `Shipping` pydantic model (request-side).
- `CalculatedShipping` pydantic model (response-side).
- Optional `shipping` kwarg on `OpenSalesTaxClient.calculate()`.
- `CalculationResult.shipping` (`CalculatedShipping | None`).
- `CalculationResult.coverage_warning` (`str | None`).
- `Shipping` and `CalculatedShipping` exported from package root.

## [0.2.0] — 2026-05-18

Minor bump: adopts the engine's new `GET /v1/capabilities` endpoint
shipped in engine v0.59.0. Connectors that depend on this SDK can now
query engine capabilities at setup time + gate feature-flagged code
paths on a single fetch. Backward compatible — existing
`health()` / `states()` / `rates()` / `calculate()` APIs unchanged.

### Added

- **`OpenSalesTaxClient.capabilities()`** — fresh `GET /v1/capabilities`;
  returns a typed `CapabilitiesResponse`.
- **`OpenSalesTaxClient.capabilities_cached()`** — same as above but
  memoized per-Client-instance.
- **`CapabilitiesResponse` / `CapabilityEndpoint` / `CapabilityFeatures`**
  pydantic models exported from the package root.
- **`CapabilityFeatures.extras`** — preserves any future engine feature
  flags the SDK doesn't yet have typed slots for. Forward-compatible
  by design. Same shape as the PHP + JS SDKs.
- **`MIN_ENGINE_VERSION`** constant (`"0.59.0"`) — exposed for connector
  setup-time engine-version checks.
- New test module `tests/test_capabilities.py` + new fixture
  `tests/fixtures/capabilities.json` (captured from live engine VM 906
  on 2026-05-18). 7 new tests.

## [0.1.2] - 2026-05-06

### Fixed
- Add `eval_type_backport>=0.2` as a conditional dependency for
  Python 3.9 (`python_version < '3.10'`). Pydantic v2 evaluates
  type annotations at model-class-creation time even when
  `from __future__ import annotations` is in effect — and PEP 604
  `X | None` syntax is a runtime operator only on Python 3.10+. On
  3.9, pydantic needs the backport package to evaluate the strings.
  Without it, importing `opensalestax` on 3.9 raises a TypeError.
  v0.1.1 didn't catch this because it was only verified on the
  3.12 dev venv.

## [0.1.1] - 2026-05-06

### Changed
- **Lower Python floor from 3.10 to 3.9.** All source files already use
  `from __future__ import annotations`, so PEP 604 union syntax and
  PEP 585 generic syntax (used throughout) are deferred to strings at
  parse time and never evaluated at runtime. The runtime requirements
  (httpx + pydantic v2) both support Python 3.9. This unblocks
  installing on the official `odoo:16` Docker image (Debian 11, Python
  3.9.2) — needed for the `opensalestax-odoo` connector's 16.0 branch.
- CI matrix now includes Python 3.9 alongside 3.10/3.11/3.12/3.13.

## [0.1.0] - 2026-05-06

### Added
- `OpenSalesTaxClient` synchronous client wrapping the OpenSalesTax v1 HTTP API
- Pydantic v2 models for request and response types: `Address`, `LineItem`,
  `CalculationResult`, `JurisdictionBreakdown`, `HealthResponse`,
  `StateCoverage`, `RateStack`
- Flat error hierarchy: `OpenSalesTaxError`, `OpenSalesTaxNetworkError`,
  `OpenSalesTaxAPIError`, `OpenSalesTaxValidationError`, `NonUSDError`
- Methods: `health()`, `states()`, `rates()`, `calculate()`
- Optional Bearer auth, configurable timeout, custom User-Agent
- mypy --strict clean; pytest with respx mocks; ≥90% coverage
- CI matrix: Python 3.10/3.11/3.12/3.13 × ubuntu/macos/windows
- PEP 561 typed package marker

### Engine compatibility
- Tested against OpenSalesTax engine v0.54.1
- Pinned to v1 HTTP API (stable contract)
