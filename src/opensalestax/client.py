# SPDX-License-Identifier: Apache-2.0
"""Synchronous HTTP client for the OpenSalesTax v1 API."""

from __future__ import annotations

import warnings
from types import TracebackType
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from ._version import __version__
from .errors import (
    OpenSalesTaxAPIError,
    OpenSalesTaxNetworkError,
    OpenSalesTaxValidationError,
)
from .models import (
    Address,
    CalculationResult,
    HealthResponse,
    LineItem,
    RateStack,
    StateCoverage,
    StatesResponse,
)

_DEFAULT_TIMEOUT = 10.0
_TModel = TypeVar("_TModel", bound="BaseModel")


class OpenSalesTaxClient:
    """Synchronous client for the OpenSalesTax v1 HTTP API.

    Example::

        from opensalestax import OpenSalesTaxClient, Address, LineItem
        from decimal import Decimal

        with OpenSalesTaxClient(base_url="http://localhost:8080") as client:
            result = client.calculate(
                address=Address(zip5="55401"),
                line_items=[LineItem(amount=Decimal("100.00"))],
            )
            print(result.tax_total)  # Decimal("9.0250")
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        user_agent: str | None = None,
        verify: bool = True,
    ) -> None:
        if not verify:
            warnings.warn(
                "TLS verification disabled — only use for local development.",
                RuntimeWarning,
                stacklevel=2,
            )
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        ua = f"opensalestax-python/{__version__}"
        if user_agent:
            ua = f"{ua} {user_agent}"
        headers = {"User-Agent": ua, "Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(
            base_url=self._base_url,
            headers=headers,
            timeout=timeout,
            verify=verify,
        )

    def __enter__(self) -> OpenSalesTaxClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Release the underlying HTTP connection pool."""
        self._client.close()

    def health(self) -> HealthResponse:
        """``GET /v1/health`` — liveness and DB-connection check."""
        data = self._get("/v1/health")
        return self._parse(HealthResponse, data)

    def states(self) -> list[StateCoverage]:
        """``GET /v1/states`` — list of every state's coverage tier.

        Returns the unwrapped ``states`` list for ergonomic iteration. The
        ``total`` field on the wrapper is recomputable as ``len(...)``.
        """
        data = self._get("/v1/states")
        wrapper = self._parse(StatesResponse, data)
        return list(wrapper.states)

    def rates(self, zip5: str, zip4: str | None = None) -> RateStack:
        """``GET /v1/rates`` — rate stack for a ZIP, no calculation."""
        params: dict[str, str] = {"zip5": zip5}
        if zip4:
            params["zip4"] = zip4
        data = self._get("/v1/rates", params=params)
        return self._parse(RateStack, data)

    def calculate(
        self,
        address: Address,
        line_items: list[LineItem],
    ) -> CalculationResult:
        """``POST /v1/calculate`` — full per-line, per-jurisdiction calculation."""
        body: dict[str, Any] = {
            "address": address.model_dump(mode="json", exclude_none=True),
            "line_items": [li.model_dump(mode="json") for li in line_items],
        }
        data = self._post("/v1/calculate", json=body)
        return self._parse(CalculationResult, data)

    def _get(
        self,
        path: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            response = self._client.get(path, params=params)
        except httpx.TimeoutException as e:
            raise OpenSalesTaxNetworkError(f"Timeout calling {path}: {e}") from e
        except httpx.RequestError as e:
            raise OpenSalesTaxNetworkError(f"Network error calling {path}: {e}") from e
        return self._handle_response(response)

    def _post(self, path: str, json: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.post(path, json=json)
        except httpx.TimeoutException as e:
            raise OpenSalesTaxNetworkError(f"Timeout calling {path}: {e}") from e
        except httpx.RequestError as e:
            raise OpenSalesTaxNetworkError(f"Network error calling {path}: {e}") from e
        return self._handle_response(response)

    @staticmethod
    def _handle_response(response: httpx.Response) -> dict[str, Any]:
        if response.is_success:
            try:
                data = response.json()
            except ValueError as e:
                raise OpenSalesTaxValidationError(
                    f"Engine returned non-JSON response: {response.text[:200]}"
                ) from e
            if not isinstance(data, dict):
                raise OpenSalesTaxValidationError(
                    f"Engine returned non-object JSON: {type(data).__name__}"
                )
            return data
        body: dict[str, object] | None
        try:
            parsed = response.json()
            body = parsed if isinstance(parsed, dict) else {"raw": parsed}
        except ValueError:
            body = {"text": response.text[:500]}
        message = ""
        if isinstance(body, dict):
            detail = body.get("detail")
            if isinstance(detail, str):
                message = detail
            elif detail is not None:
                message = str(detail)
            else:
                message = response.reason_phrase or "(no body)"
        raise OpenSalesTaxAPIError(
            status_code=response.status_code,
            message=message,
            response_body=body,
        )

    @staticmethod
    def _parse(model: type[_TModel], data: dict[str, Any]) -> _TModel:
        try:
            return model.model_validate(data)
        except PydanticValidationError as e:
            raise OpenSalesTaxValidationError(
                f"Engine response failed validation against {model.__name__}: {e}"
            ) from e
