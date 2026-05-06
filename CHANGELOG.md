# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
