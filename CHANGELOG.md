# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
