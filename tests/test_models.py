# SPDX-License-Identifier: Apache-2.0
"""Pydantic model tests — input validation + fixture round-trips."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from opensalestax import (
    Address,
    CalculatedLine,
    CalculationResult,
    HealthResponse,
    JurisdictionBreakdown,
    LineItem,
    RateStack,
    StatesResponse,
)


class TestAddress:
    def test_zip5_only(self) -> None:
        a = Address(zip5="55401")
        assert a.zip5 == "55401"
        assert a.zip4 is None

    def test_zip5_and_zip4(self) -> None:
        a = Address(zip5="55401", zip4="1234")
        assert a.zip4 == "1234"

    def test_zip5_pattern_rejects_non_digits(self) -> None:
        with pytest.raises(ValidationError):
            Address(zip5="ABCDE")

    def test_zip5_pattern_rejects_wrong_length(self) -> None:
        with pytest.raises(ValidationError):
            Address(zip5="1234")
        with pytest.raises(ValidationError):
            Address(zip5="123456")

    def test_zip4_pattern(self) -> None:
        with pytest.raises(ValidationError):
            Address(zip5="55401", zip4="ABCD")

    def test_frozen(self) -> None:
        a = Address(zip5="55401")
        with pytest.raises(ValidationError):
            a.zip5 = "12345"  # type: ignore[misc]


class TestLineItem:
    def test_default_category(self) -> None:
        li = LineItem(amount=Decimal("100.00"))
        assert li.category == "general"

    def test_explicit_category(self) -> None:
        li = LineItem(amount=Decimal("50.00"), category="clothing")
        assert li.category == "clothing"

    def test_amount_from_string(self) -> None:
        li = LineItem(amount="49.99")  # type: ignore[arg-type]
        assert li.amount == Decimal("49.99")

    def test_negative_amount_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LineItem(amount=Decimal("-1"))


class TestJurisdictionBreakdown:
    def test_rates_only(self) -> None:
        j = JurisdictionBreakdown(name="MN", type="state", rate_pct=Decimal("6.875"))
        assert j.tax is None

    def test_calculate_with_tax(self) -> None:
        j = JurisdictionBreakdown(
            name="MN",
            type="state",
            rate_pct=Decimal("6.875"),
            tax=Decimal("6.8750"),
        )
        assert j.tax == Decimal("6.8750")

    def test_invalid_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            JurisdictionBreakdown(name="X", type="federal", rate_pct=Decimal("1"))  # type: ignore[arg-type]


class TestHealthResponse:
    def test_from_fixture(self, health_payload: dict[str, Any]) -> None:
        h = HealthResponse.model_validate(health_payload)
        assert h.status == "ok"
        assert h.version
        assert h.database_connected is True

    def test_status_enum(self) -> None:
        with pytest.raises(ValidationError):
            HealthResponse(status="bad", version="0.0.0", database_connected=True)  # type: ignore[arg-type]


class TestStatesResponse:
    def test_from_fixture(self, states_payload: dict[str, Any]) -> None:
        s = StatesResponse.model_validate(states_payload)
        assert s.total > 0
        assert s.total == len(s.states)
        assert all(len(state.abbrev) == 2 for state in s.states)
        assert all(state.tier in (0, 1, 2) for state in s.states)


class TestRateStack:
    def test_from_fixture(self, rates_payload: dict[str, Any]) -> None:
        r = RateStack.model_validate(rates_payload)
        assert r.input["zip5"] == "55401"
        assert len(r.jurisdictions) > 0
        assert r.combined_rate_pct > Decimal("0")
        assert all(j.tax is None for j in r.jurisdictions)


class TestCalculationResult:
    def test_from_fixture(self, calculate_payload: dict[str, Any]) -> None:
        c = CalculationResult.model_validate(calculate_payload)
        assert c.subtotal == Decimal("100.00")
        assert c.tax_total == Decimal("9.0250")
        assert len(c.lines) == 1
        line = c.lines[0]
        assert isinstance(line, CalculatedLine)
        assert line.tax == Decimal("9.0250")
        # The breakdown must reconcile to the line total exactly.
        assert sum((j.tax or Decimal("0")) for j in line.jurisdictions) == line.tax

    def test_disclaimer_present(self, calculate_payload: dict[str, Any]) -> None:
        c = CalculationResult.model_validate(calculate_payload)
        assert "Calculation only" in c.disclaimer
