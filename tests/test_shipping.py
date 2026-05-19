# SPDX-License-Identifier: Apache-2.0
"""Tests for the engine v0.59.0 first-class shipping support.

Snapshot fixtures captured live from engine VM 906 on 2026-05-19
via ``POST http://10.32.161.126:8080/v1/calculate`` with body
``{"address":{"zip5":"55401"},"line_items":[{"amount":"100.00"}],
"shipping":{"amount":"12.50"}}``.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from opensalestax import (
    Address,
    CalculatedShipping,
    CalculationResult,
    LineItem,
    OpenSalesTaxClient,
    Shipping,
)

_FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def calculate_shipping_payload() -> dict[str, Any]:
    with (_FIXTURE_DIR / "calculate_minneapolis_shipping.json").open(encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


class TestShippingRequestModel:
    """The ``Shipping`` request-side model serializes to the engine's
    expected snake_case wire format."""

    def test_minimal_dump_emits_defaults_explicitly(self) -> None:
        # exclude_defaults=False because we want the wire body to be
        # deterministic — separately_stated=True and is_handling_charge=False
        # ride along even though they're the field defaults, matching
        # JS/PHP behavior.
        s = Shipping(amount=Decimal("12.50"))
        body = s.model_dump(mode="json", exclude_defaults=False, by_alias=False)
        assert body == {
            "amount": "12.50",
            "method": None,
            "separately_stated": True,
            "is_handling_charge": False,
        }

    def test_dump_with_all_fields(self) -> None:
        s = Shipping(
            amount=Decimal("7.25"),
            method="ups_ground",
            separately_stated=False,
            is_handling_charge=True,
        )
        body = s.model_dump(mode="json", exclude_defaults=False, by_alias=False)
        assert body == {
            "amount": "7.25",
            "method": "ups_ground",
            "separately_stated": False,
            "is_handling_charge": True,
        }

    def test_amount_must_be_non_negative(self) -> None:
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            Shipping(amount=Decimal("-1.00"))


class TestCalculatedShippingResponseModel:
    """The ``CalculatedShipping`` response-side model parses the
    engine's snake_case wire response (``tax_amount`` field maps to
    the ``tax`` attribute)."""

    def test_parses_engine_response_shape(self) -> None:
        raw = {
            "amount": "12.50",
            "tax_amount": "1.1281",
            "rate_pct": "9.02500",
            "taxable_reason": "MN taxes shipping when items are taxable.",
        }
        cs = CalculatedShipping.model_validate(raw)
        assert cs.amount == Decimal("12.50")
        assert cs.tax == Decimal("1.1281")
        assert cs.rate_pct == Decimal("9.02500")
        assert cs.taxable_reason == "MN taxes shipping when items are taxable."

    def test_omits_taxable_reason_when_engine_omits_it(self) -> None:
        raw = {"amount": "10.00", "tax_amount": "0.00", "rate_pct": "0.00000"}
        cs = CalculatedShipping.model_validate(raw)
        assert cs.taxable_reason is None


class TestCalculationResultShippingField:
    def test_parses_full_engine_snapshot(
        self, calculate_shipping_payload: dict[str, Any]
    ) -> None:
        result = CalculationResult.model_validate(calculate_shipping_payload)
        assert result.subtotal == Decimal("100.00")
        assert result.tax_total == Decimal("10.1531")
        assert result.coverage_warning is None
        assert result.shipping is not None
        assert result.shipping.amount == Decimal("12.50")
        assert result.shipping.tax == Decimal("1.1281")
        assert result.shipping.rate_pct == Decimal("9.02500")
        assert result.shipping.taxable_reason is not None
        assert "MN" in result.shipping.taxable_reason

    def test_shipping_none_when_engine_omits_field(
        self, calculate_payload: dict[str, Any]
    ) -> None:
        # The pre-v0.59.0 fixture omits the `shipping` and
        # `coverage_warning` keys entirely. Parse should succeed and
        # both fields should be None.
        result = CalculationResult.model_validate(calculate_payload)
        assert result.shipping is None
        assert result.coverage_warning is None

    def test_shipping_none_when_engine_explicitly_returns_null(self) -> None:
        raw = {
            "subtotal": "50.00",
            "tax_total": "0.00",
            "lines": [],
            "disclaimer": "x",
            "shipping": None,
            "coverage_warning": None,
        }
        result = CalculationResult.model_validate(raw)
        assert result.shipping is None
        assert result.coverage_warning is None

    def test_coverage_warning_parses_when_engine_emits_one(self) -> None:
        raw = {
            "subtotal": "50.00",
            "tax_total": "0.00",
            "lines": [],
            "disclaimer": "x",
            "shipping": None,
            "coverage_warning": "ZIP 99999 has incomplete rate data; calculation may be inaccurate.",
        }
        result = CalculationResult.model_validate(raw)
        assert result.coverage_warning is not None
        assert "incomplete rate data" in result.coverage_warning


class TestClientCalculateWithShipping:
    """End-to-end through the client with respx-mocked HTTP."""

    @respx.mock
    def test_request_body_includes_shipping_when_supplied(
        self, base_url: str, calculate_shipping_payload: dict[str, Any]
    ) -> None:
        route = respx.post(f"{base_url}/v1/calculate").mock(
            return_value=httpx.Response(200, json=calculate_shipping_payload)
        )
        with OpenSalesTaxClient(base_url=base_url) as c:
            c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
                shipping=Shipping(amount=Decimal("12.50")),
            )
        sent = json.loads(route.calls[0].request.read())
        assert "shipping" in sent
        assert sent["shipping"]["amount"] == "12.50"
        # Defaults travel explicitly on the wire for determinism.
        assert sent["shipping"]["separately_stated"] is True
        assert sent["shipping"]["is_handling_charge"] is False

    @respx.mock
    def test_request_body_omits_shipping_when_kwarg_unset(
        self, base_url: str, calculate_payload: dict[str, Any]
    ) -> None:
        route = respx.post(f"{base_url}/v1/calculate").mock(
            return_value=httpx.Response(200, json=calculate_payload)
        )
        with OpenSalesTaxClient(base_url=base_url) as c:
            c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
            )
        sent = json.loads(route.calls[0].request.read())
        assert "shipping" not in sent, "back-compat: no shipping key when caller omits kwarg"

    @respx.mock
    def test_response_exposes_calculated_shipping_and_coverage_warning(
        self, base_url: str, calculate_shipping_payload: dict[str, Any]
    ) -> None:
        respx.post(f"{base_url}/v1/calculate").mock(
            return_value=httpx.Response(200, json=calculate_shipping_payload)
        )
        with OpenSalesTaxClient(base_url=base_url) as c:
            result = c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
                shipping=Shipping(amount=Decimal("12.50")),
            )
        assert result.shipping is not None
        assert result.shipping.tax == Decimal("1.1281")
        assert result.coverage_warning is None

    @respx.mock
    def test_request_body_emits_all_shipping_fields(
        self, base_url: str, calculate_shipping_payload: dict[str, Any]
    ) -> None:
        route = respx.post(f"{base_url}/v1/calculate").mock(
            return_value=httpx.Response(200, json=calculate_shipping_payload)
        )
        with OpenSalesTaxClient(base_url=base_url) as c:
            c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
                shipping=Shipping(
                    amount=Decimal("12.50"),
                    method="ups_ground",
                    separately_stated=False,
                    is_handling_charge=True,
                ),
            )
        sent = json.loads(route.calls[0].request.read())
        assert sent["shipping"] == {
            "amount": "12.50",
            "method": "ups_ground",
            "separately_stated": False,
            "is_handling_charge": True,
        }
