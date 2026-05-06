# SPDX-License-Identifier: Apache-2.0
"""OpenSalesTaxClient tests with respx-mocked HTTP."""

from __future__ import annotations

import warnings
from decimal import Decimal
from typing import Any

import httpx
import pytest
import respx

from opensalestax import (
    Address,
    LineItem,
    OpenSalesTaxAPIError,
    OpenSalesTaxClient,
    OpenSalesTaxNetworkError,
    OpenSalesTaxValidationError,
    __version__,
)


class TestConstruction:
    def test_strips_trailing_slash(self, base_url: str) -> None:
        client = OpenSalesTaxClient(base_url=base_url + "/")
        assert client._base_url == base_url
        client.close()

    def test_user_agent_default(self, base_url: str) -> None:
        client = OpenSalesTaxClient(base_url=base_url)
        ua = client._client.headers["User-Agent"]
        assert ua == f"opensalestax-python/{__version__}"
        client.close()

    def test_user_agent_custom_appended(self, base_url: str) -> None:
        client = OpenSalesTaxClient(base_url=base_url, user_agent="my-app/1.0")
        ua = client._client.headers["User-Agent"]
        assert ua == f"opensalestax-python/{__version__} my-app/1.0"
        client.close()

    def test_bearer_auth(self, base_url: str) -> None:
        client = OpenSalesTaxClient(base_url=base_url, api_key="secret-token")
        assert client._client.headers["Authorization"] == "Bearer secret-token"
        client.close()

    def test_no_auth_header_when_no_key(self, base_url: str) -> None:
        client = OpenSalesTaxClient(base_url=base_url)
        assert "Authorization" not in client._client.headers
        client.close()

    def test_verify_false_emits_warning(self, base_url: str) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            client = OpenSalesTaxClient(base_url=base_url, verify=False)
            client.close()
        assert any(issubclass(rec.category, RuntimeWarning) for rec in w)

    def test_context_manager(self, base_url: str) -> None:
        with OpenSalesTaxClient(base_url=base_url) as c:
            assert isinstance(c, OpenSalesTaxClient)


class TestHealth:
    @respx.mock
    def test_happy_path(self, base_url: str, health_payload: dict[str, Any]) -> None:
        respx.get(f"{base_url}/v1/health").mock(
            return_value=httpx.Response(200, json=health_payload)
        )
        with OpenSalesTaxClient(base_url=base_url) as c:
            r = c.health()
        assert r.status == "ok"
        assert r.database_connected is True

    @respx.mock
    def test_5xx_maps_to_api_error(self, base_url: str) -> None:
        respx.get(f"{base_url}/v1/health").mock(
            return_value=httpx.Response(503, json={"detail": "engine starting"})
        )
        with OpenSalesTaxClient(base_url=base_url) as c, pytest.raises(OpenSalesTaxAPIError) as exc:
            c.health()
        assert exc.value.status_code == 503
        assert "engine starting" in str(exc.value)


class TestStates:
    @respx.mock
    def test_unwraps_states_list(self, base_url: str, states_payload: dict[str, Any]) -> None:
        respx.get(f"{base_url}/v1/states").mock(
            return_value=httpx.Response(200, json=states_payload)
        )
        with OpenSalesTaxClient(base_url=base_url) as c:
            states = c.states()
        assert len(states) == states_payload["total"]
        assert any(s.abbrev == "MN" for s in states)


class TestRates:
    @respx.mock
    def test_zip5_only(self, base_url: str, rates_payload: dict[str, Any]) -> None:
        route = respx.get(f"{base_url}/v1/rates").mock(
            return_value=httpx.Response(200, json=rates_payload)
        )
        with OpenSalesTaxClient(base_url=base_url) as c:
            r = c.rates(zip5="55401")
        assert route.calls[0].request.url.params["zip5"] == "55401"
        assert "zip4" not in route.calls[0].request.url.params
        assert r.combined_rate_pct > Decimal("0")

    @respx.mock
    def test_with_zip4(self, base_url: str, rates_payload: dict[str, Any]) -> None:
        route = respx.get(f"{base_url}/v1/rates").mock(
            return_value=httpx.Response(200, json=rates_payload)
        )
        with OpenSalesTaxClient(base_url=base_url) as c:
            c.rates(zip5="55401", zip4="1234")
        assert route.calls[0].request.url.params["zip4"] == "1234"


class TestCalculate:
    @respx.mock
    def test_happy_path(self, base_url: str, calculate_payload: dict[str, Any]) -> None:
        respx.post(f"{base_url}/v1/calculate").mock(
            return_value=httpx.Response(200, json=calculate_payload)
        )
        with OpenSalesTaxClient(base_url=base_url) as c:
            result = c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
            )
        assert result.subtotal == Decimal("100.00")
        assert result.tax_total == Decimal("9.0250")
        assert len(result.lines[0].jurisdictions) > 0

    @respx.mock
    def test_request_body_serialization(
        self, base_url: str, calculate_payload: dict[str, Any]
    ) -> None:
        route = respx.post(f"{base_url}/v1/calculate").mock(
            return_value=httpx.Response(200, json=calculate_payload)
        )
        with OpenSalesTaxClient(base_url=base_url) as c:
            c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"), category="general")],
            )
        sent = route.calls[0].request.read().decode()
        assert "55401" in sent
        assert "100.00" in sent
        assert "general" in sent

    @respx.mock
    def test_4xx_maps_to_api_error(self, base_url: str, calculate_payload: dict[str, Any]) -> None:
        respx.post(f"{base_url}/v1/calculate").mock(
            return_value=httpx.Response(422, json={"detail": "bad zip"})
        )
        with OpenSalesTaxClient(base_url=base_url) as c, pytest.raises(OpenSalesTaxAPIError) as exc:
            c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
            )
        assert exc.value.status_code == 422

    @respx.mock
    def test_network_timeout_maps(self, base_url: str) -> None:
        respx.post(f"{base_url}/v1/calculate").mock(side_effect=httpx.TimeoutException("timed out"))
        with OpenSalesTaxClient(base_url=base_url) as c, pytest.raises(OpenSalesTaxNetworkError):
            c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
            )

    @respx.mock
    def test_connection_error_maps(self, base_url: str) -> None:
        respx.post(f"{base_url}/v1/calculate").mock(side_effect=httpx.ConnectError("refused"))
        with OpenSalesTaxClient(base_url=base_url) as c, pytest.raises(OpenSalesTaxNetworkError):
            c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
            )

    @respx.mock
    def test_malformed_json_response(self, base_url: str) -> None:
        respx.post(f"{base_url}/v1/calculate").mock(
            return_value=httpx.Response(200, content=b"not json")
        )
        with OpenSalesTaxClient(base_url=base_url) as c, pytest.raises(OpenSalesTaxValidationError):
            c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
            )

    @respx.mock
    def test_response_shape_mismatch(self, base_url: str) -> None:
        respx.post(f"{base_url}/v1/calculate").mock(
            return_value=httpx.Response(200, json={"unexpected": "shape"})
        )
        with OpenSalesTaxClient(base_url=base_url) as c, pytest.raises(OpenSalesTaxValidationError):
            c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
            )

    @respx.mock
    def test_4xx_with_non_dict_body(self, base_url: str) -> None:
        respx.post(f"{base_url}/v1/calculate").mock(
            return_value=httpx.Response(400, json=["plain", "list"])
        )
        with OpenSalesTaxClient(base_url=base_url) as c, pytest.raises(OpenSalesTaxAPIError) as exc:
            c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
            )
        assert exc.value.status_code == 400

    @respx.mock
    def test_4xx_with_non_json_body(self, base_url: str) -> None:
        respx.post(f"{base_url}/v1/calculate").mock(
            return_value=httpx.Response(500, content=b"<html>error</html>")
        )
        with OpenSalesTaxClient(base_url=base_url) as c, pytest.raises(OpenSalesTaxAPIError) as exc:
            c.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
            )
        assert exc.value.status_code == 500
