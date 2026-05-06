# SPDX-License-Identifier: Apache-2.0
"""Pydantic v2 models for OpenSalesTax v1 HTTP API requests and responses.

Money and rates are represented as :class:`decimal.Decimal` to preserve
precision. The wire format is always decimal strings; pydantic handles
the conversion both ways.

Rate values are stored as **percents** (e.g. ``Decimal("6.875")`` means
6.875%). Connectors that prefer fractional rates can divide by 100.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

JurisdictionType = Literal["state", "county", "city", "district"]


_FROZEN = ConfigDict(frozen=True, str_strip_whitespace=True)


class Address(BaseModel):
    """ZIP-based address. The engine's v1 API is ZIP-only (no street/city/state)."""

    model_config = _FROZEN

    zip5: str = Field(pattern=r"^\d{5}$", description="5-digit ZIP")
    zip4: str | None = Field(default=None, pattern=r"^\d{4}$", description="Optional ZIP+4")


class LineItem(BaseModel):
    """One taxable line in a calculate request."""

    model_config = _FROZEN

    amount: Decimal = Field(ge=Decimal("0"), description="Pre-tax amount, non-negative.")
    category: str = Field(default="general", description="Tax category (general, clothing, ...).")


class JurisdictionBreakdown(BaseModel):
    """One taxing authority contributing to a rate stack or calculated line.

    ``tax`` is ``None`` for ``/v1/rates`` responses (no calculation done) and
    a :class:`Decimal` dollar amount for ``/v1/calculate`` responses.
    """

    model_config = _FROZEN

    name: str
    type: JurisdictionType
    rate_pct: Decimal = Field(description="Rate expressed as a percent, e.g. Decimal('6.875').")
    tax: Decimal | None = Field(default=None, description="Dollar contribution; None on /rates.")


class HealthResponse(BaseModel):
    """Liveness + readiness signal from ``GET /v1/health``."""

    model_config = _FROZEN

    status: Literal["ok", "degraded"]
    version: str = Field(description="Engine package version (e.g. '0.54.1').")
    database_connected: bool


class StateCoverage(BaseModel):
    """One entry in the ``GET /v1/states`` coverage list."""

    model_config = _FROZEN

    abbrev: str = Field(pattern=r"^[A-Z]{2}$", description="USPS abbreviation")
    name: str
    has_sales_tax: bool
    sst_member: bool
    tier: Literal[0, 1, 2] = Field(
        description=(
            "0 = unsupported; 1 = fully maintained (taxability + tests); "
            "2 = rate-only via SST data."
        )
    )
    notes: str = ""


class StatesResponse(BaseModel):
    """``GET /v1/states`` response wrapper."""

    model_config = _FROZEN

    states: list[StateCoverage]
    total: int


class RateStack(BaseModel):
    """``GET /v1/rates`` response — rates only (no per-line tax amounts)."""

    model_config = _FROZEN

    input: dict[str, Any]
    jurisdictions: list[JurisdictionBreakdown]
    combined_rate_pct: Decimal
    disclaimer: str


class CalculatedLine(BaseModel):
    """One calculated line in a ``POST /v1/calculate`` response.

    Invariant: ``tax == sum(j.tax for j in jurisdictions)`` exactly. The
    engine quantizes per jurisdiction first, then sums, so the breakdown
    reconciles to the line total down to the cent.
    """

    model_config = _FROZEN

    amount: Decimal
    category: str
    tax: Decimal
    rate_pct: Decimal
    jurisdictions: list[JurisdictionBreakdown]
    note: str | None = None


class CalculationResult(BaseModel):
    """``POST /v1/calculate`` response body."""

    model_config = _FROZEN

    subtotal: Decimal
    tax_total: Decimal
    lines: list[CalculatedLine]
    disclaimer: str
