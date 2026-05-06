# SPDX-License-Identifier: Apache-2.0
"""Live integration tests against an actual engine.

Skipped by default. Enable with::

    RUN_LIVE_TESTS=1 OST_BASE_URL=http://10.32.161.126:8080 pytest -m live -v
"""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

from opensalestax import Address, LineItem, OpenSalesTaxClient

pytestmark = pytest.mark.live

if not os.getenv("RUN_LIVE_TESTS"):
    pytest.skip("set RUN_LIVE_TESTS=1 to enable", allow_module_level=True)

BASE_URL = os.getenv("OST_BASE_URL", "http://10.32.161.126:8080")


@pytest.fixture(scope="module")
def client() -> OpenSalesTaxClient:
    c = OpenSalesTaxClient(base_url=BASE_URL)
    yield c
    c.close()


def test_health(client: OpenSalesTaxClient) -> None:
    h = client.health()
    assert h.status in ("ok", "degraded")
    assert h.version


def test_states_returns_us_states(client: OpenSalesTaxClient) -> None:
    states = client.states()
    abbrevs = {s.abbrev for s in states}
    for expected in ("CA", "NY", "MN", "TX", "FL"):
        assert expected in abbrevs


def test_rates_minneapolis(client: OpenSalesTaxClient) -> None:
    r = client.rates(zip5="55401")
    assert r.combined_rate_pct > Decimal("0")
    assert any(j.type == "state" for j in r.jurisdictions)


def test_calculate_minneapolis_general(client: OpenSalesTaxClient) -> None:
    result = client.calculate(
        address=Address(zip5="55401"),
        line_items=[LineItem(amount=Decimal("100.00"))],
    )
    assert result.subtotal == Decimal("100.00")
    assert result.tax_total > Decimal("0")
    line = result.lines[0]
    assert sum((j.tax or Decimal("0")) for j in line.jurisdictions) == line.tax


def test_calculate_clothing_in_mn_is_zero(client: OpenSalesTaxClient) -> None:
    result = client.calculate(
        address=Address(zip5="55401"),
        line_items=[LineItem(amount=Decimal("50.00"), category="clothing")],
    )
    assert result.tax_total == Decimal("0")
