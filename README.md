# opensalestax-python

[![PyPI](https://img.shields.io/pypi/v/opensalestax)](https://pypi.org/project/opensalestax/)
[![License](https://img.shields.io/pypi/l/opensalestax)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/opensalestax)](https://pypi.org/project/opensalestax/)
[![CI](https://github.com/ejosterberg/opensalestax-python/actions/workflows/ci.yml/badge.svg)](https://github.com/ejosterberg/opensalestax-python/actions/workflows/ci.yml)

Python SDK for **[OpenSalesTax](https://github.com/ejosterberg/open-sales-tax)** —
calculate US sales tax via the engine's v1 HTTP API.

A thin, well-typed wrapper around the engine's four endpoints. Used by
the OpenSalesTax connectors for [Odoo](https://github.com/ejosterberg/opensalestax-odoo)
and ERPNext, and suitable for any Python application that needs
destination-based US sales-tax calculation.

## Install

```bash
pip install opensalestax
```

Requires Python 3.10+.

## Quickstart

```python
from decimal import Decimal
from opensalestax import OpenSalesTaxClient, Address, LineItem

with OpenSalesTaxClient(base_url="http://localhost:8080") as client:
    result = client.calculate(
        address=Address(zip5="55401"),  # Minneapolis, MN
        line_items=[
            LineItem(amount=Decimal("100.00"), category="general"),
        ],
    )

    print(f"Subtotal:  ${result.subtotal}")
    print(f"Tax:       ${result.tax_total}")
    for line in result.lines:
        for j in line.jurisdictions:
            print(f"  {j.name} ({j.type}) {j.rate_pct}%: ${j.tax}")
```

Output (against engine v0.54+):

```
Subtotal:  $100.00
Tax:       $9.0250
  Minneapolis (city) 0.50000%: $0.5000
  Hennepin County (county) 0.15000%: $0.1500
  Minnesota (state) 6.87500%: $6.8750
  Hennepin County Transit Sales Tax (district) 0.50000%: $0.5000
  Metro Area Transportation Sales Tax (district) 0.75000%: $0.7500
  Metro Area Sales and Use Tax for Housing (district) 0.25000%: $0.2500
```

## API

### `OpenSalesTaxClient`

```python
OpenSalesTaxClient(
    base_url: str,                    # engine URL, e.g. "http://localhost:8080"
    api_key: str | None = None,       # optional Bearer token
    timeout: float = 10.0,            # seconds
    user_agent: str | None = None,    # appended to default UA
    verify: bool = True,              # TLS verification
)
```

Use as a context manager (recommended) or call `client.close()` manually.

### Methods

| Method | Endpoint | Returns |
|---|---|---|
| `health()` | `GET /v1/health` | `HealthResponse` |
| `states()` | `GET /v1/states` | `list[StateCoverage]` |
| `rates(zip5, zip4=None)` | `GET /v1/rates` | `RateStack` |
| `calculate(address, line_items)` | `POST /v1/calculate` | `CalculationResult` |

### Models

All models are immutable (`frozen=True`) Pydantic v2. Money and rates use
`decimal.Decimal` to preserve precision; rates are expressed as percents
(e.g. `Decimal("6.875")` means 6.875%).

- `Address(zip5, zip4=None)` — engine v1 is ZIP-only
- `LineItem(amount, category="general")` — pre-tax amount as `Decimal`
- `JurisdictionBreakdown(name, type, rate_pct, tax)` — one taxing authority
- `CalculatedLine(amount, category, tax, rate_pct, jurisdictions, note)`
- `CalculationResult(subtotal, tax_total, lines, disclaimer)`
- `RateStack(input, jurisdictions, combined_rate_pct, disclaimer)`
- `HealthResponse(status, version, database_connected)`
- `StateCoverage(abbrev, name, has_sales_tax, sst_member, tier, notes)`

### Errors

Flat hierarchy — connectors typically catch one or two:

```python
from opensalestax import (
    OpenSalesTaxError,            # base class
    OpenSalesTaxNetworkError,     # timeout, connection refused, DNS, TLS
    OpenSalesTaxAPIError,         # non-2xx HTTP response (.status_code, .response_body)
    OpenSalesTaxValidationError,  # response shape didn't match SDK models
    NonUSDError,                  # non-USD or non-US address
)
```

Recommended pattern in a connector:

```python
try:
    result = client.calculate(address=addr, line_items=items)
except OpenSalesTaxNetworkError:
    fall_back_to_catalog_rate()      # engine unreachable
except OpenSalesTaxAPIError as e:
    if e.status_code >= 500:
        fall_back_to_catalog_rate()  # engine glitch
    else:
        surface_to_merchant(e)       # 4xx — config / data issue
```

## Compatibility

| SDK version | Engine version | Python |
|---|---|---|
| 0.1.x | 0.22+ (recommended 0.54+) | 3.10, 3.11, 3.12, 3.13 |

The engine's v1 HTTP API is the contract. Internal Python modules are
not — connectors must use this SDK or call the HTTP API directly.

## Calculation only

> Tax calculations are provided as-is for convenience. The merchant is
> solely responsible for tax-collection accuracy and remittance to the
> appropriate jurisdictions. Verify against your state Department of
> Revenue before remitting.

This SDK does **not**:

- File tax returns or remit collected tax (engine constitution §13)
- Validate addresses
- Cache calculations (caller's responsibility — caching policy is
  platform-specific)
- Retry transient errors (caller's responsibility)

## Connectors that use this SDK

- [`ejosterberg/opensalestax-odoo`](https://github.com/ejosterberg/opensalestax-odoo) — Odoo Community 16.0/17.0/18.0 connector
- *(ERPNext connector planned)*

## Development

```bash
git clone https://github.com/ejosterberg/opensalestax-python.git
cd opensalestax-python
uv venv
uv pip install -e ".[dev]"

# Quality gate
ruff check src tests
ruff format --check src tests
mypy --strict src/opensalestax
pytest --cov=opensalestax --cov-fail-under=90

# Live tests against an actual engine (skipped by default)
RUN_LIVE_TESTS=1 OST_BASE_URL=http://localhost:8080 pytest -m live -v
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). All commits must carry a DCO
sign-off (`git commit -s`). No AI co-author trailers.

## License

[Apache 2.0](LICENSE). Apache 2.0 + DCO sign-off + SPDX header on every
source file.
