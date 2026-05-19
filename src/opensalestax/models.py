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


class Shipping(BaseModel):
    """Top-level shipping segment on ``POST /v1/calculate`` (engine v0.59.0+).

    Sent under the ``shipping`` key (NOT as a line item with
    ``category: "shipping"`` — that's the legacy shim that pre-dates the
    engine's first-class shipping support). Older engines silently
    ignore the field; the response's ``shipping`` will be ``None``.

    The engine applies per-state shipping-taxability rules internally
    (MN's "tax-if-items-taxable" rule, MO/VA's "separately-stated"
    rule, MD's shipping-vs-handling distinction, etc.). Connectors
    just pass the amount and optional flags; the engine decides
    whether to tax it and at what rate.
    """

    model_config = _FROZEN

    amount: Decimal = Field(ge=Decimal("0"), description="Pre-tax shipping amount.")
    method: str | None = Field(default=None, description="Optional carrier/method label.")
    separately_stated: bool = Field(
        default=True, description="Defaults True; relevant for MO/VA."
    )
    is_handling_charge: bool = Field(
        default=False, description="MD distinguishes shipping vs handling."
    )


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


class CapabilityEndpoint(BaseModel):
    """One entry in the ``endpoints`` map of :class:`CapabilitiesResponse`."""

    model_config = _FROZEN

    path: str
    version: int = 1


class CapabilityFeatures(BaseModel):
    """Feature flags returned by the engine on ``GET /v1/capabilities``.

    Known flags as of engine v0.59.0:

    * ``coverage_warning`` — engine emits a coverage-warning when a calc
      request hits a jurisdiction with incomplete rate data.
    * ``shipping_first_class`` — engine accepts the top-level ``shipping``
      field on ``POST /v1/calculate`` (vs. the legacy ``category:
      "shipping"`` line-item shim).
    * ``vendor_allocation`` — engine accepts per-line ``vendor_id`` and
      returns per-vendor allocation. v0.59.0 ships ``False`` (engine
      team direction: permanently deferred).
    * ``transaction_record_back`` — engine exposes ``POST /v1/transactions``
      for committed-sale record-back. v0.59.0 ships ``False`` (engine
      positioned as calculation-only).

    Additional flags emitted by future engine versions land in ``extras``
    (preserved verbatim) so connectors can flag-gate new functionality
    without an SDK bump.
    """

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True, extra="allow")

    coverage_warning: bool = False
    shipping_first_class: bool = False
    vendor_allocation: bool = False
    transaction_record_back: bool = False
    extras: dict[str, bool] = Field(default_factory=dict)

    @classmethod
    def from_engine(cls, raw: dict[str, Any]) -> CapabilityFeatures:
        """Build from the engine's snake_case wire dict, partitioning unknown
        flags into ``extras`` so the typed surface remains stable across
        engine versions."""
        known = {
            "coverage_warning",
            "shipping_first_class",
            "vendor_allocation",
            "transaction_record_back",
        }
        known_vals: dict[str, bool] = {}
        extras: dict[str, bool] = {}
        for k, v in raw.items():
            if not isinstance(v, bool):
                # Tolerate engine drift: silently coerce non-bool to False.
                v = False
            if k in known:
                known_vals[k] = v
            else:
                extras[k] = v
        return cls(extras=extras, **known_vals)


class CapabilitiesResponse(BaseModel):
    """Response from ``GET /v1/capabilities`` (engine v0.59.0+).

    Exposes the engine's version, endpoint manifest, and feature flags
    so SDK consumers can flag-gate code paths (first-class shipping,
    future record-back, etc.) and surface a clear "engine too old"
    error at setup time when the engine reports a version below
    :data:`MIN_ENGINE_VERSION`.

    Use :meth:`OpenSalesTaxClient.capabilities_cached` for setup-time
    checks; it memoizes per-Client-instance to avoid the per-request
    round-trip cost.
    """

    model_config = _FROZEN

    version: str
    endpoints: dict[str, CapabilityEndpoint] = Field(default_factory=dict)
    features: CapabilityFeatures = Field(default_factory=CapabilityFeatures)


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


class CalculatedShipping(BaseModel):
    """Calculated shipping segment in a ``POST /v1/calculate`` response.

    Present when the request included a top-level ``shipping`` field
    AND the engine supports first-class shipping (v0.59.0+).

    The engine returns this even when shipping ended up non-taxable —
    ``tax`` is ``Decimal("0.00")`` and ``taxable_reason`` explains why
    (e.g., "TX does not tax shipping when separately stated").
    """

    model_config = _FROZEN

    amount: Decimal
    tax: Decimal = Field(
        alias="tax_amount",
        validation_alias="tax_amount",
        description="Tax due on shipping; Decimal('0.00') when exempt.",
    )
    rate_pct: Decimal = Field(
        description="Effective shipping tax rate (combined across jurisdictions)."
    )
    taxable_reason: str | None = Field(
        default=None,
        description="Engine's explanation of why shipping was / wasn't taxed.",
    )


class CalculationResult(BaseModel):
    """``POST /v1/calculate`` response body."""

    model_config = _FROZEN

    subtotal: Decimal
    tax_total: Decimal
    lines: list[CalculatedLine]
    disclaimer: str
    shipping: CalculatedShipping | None = Field(
        default=None,
        description=(
            "Calculated shipping. None when the request omitted the top-level "
            "shipping field OR when the engine is older than v0.59.0 and "
            "ignored it."
        ),
    )
    coverage_warning: str | None = Field(
        default=None,
        description=(
            "Coverage warning text emitted by engine v0.59.0+ when a calc "
            "request hits a jurisdiction with incomplete rate data. None "
            "when no warning was emitted."
        ),
    )
