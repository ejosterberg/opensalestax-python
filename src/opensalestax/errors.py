# SPDX-License-Identifier: Apache-2.0
"""Flat error hierarchy for the OpenSalesTax SDK.

Connectors typically catch:

* :class:`OpenSalesTaxNetworkError` — fail-soft (use catalog rates)
* :class:`OpenSalesTaxAPIError` 4xx — config / data issue, surface to merchant
* :class:`OpenSalesTaxAPIError` 5xx — fail-soft (engine glitch)
* :class:`NonUSDError` — opt out cleanly (non-US partner / non-US fiscal position)
"""

from __future__ import annotations

from typing import Any


class OpenSalesTaxError(Exception):
    """Base class for every SDK error."""


class OpenSalesTaxNetworkError(OpenSalesTaxError):
    """Timeout, connection refused, DNS failure, TLS handshake — anything below the HTTP layer."""


class OpenSalesTaxAPIError(OpenSalesTaxError):
    """The engine returned a non-2xx HTTP response."""

    def __init__(
        self,
        status_code: int,
        message: str,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"OpenSalesTax API {status_code}: {message}")


class OpenSalesTaxValidationError(OpenSalesTaxError):
    """The response shape didn't match the SDK's expected models — engine-version mismatch likely."""


class NonUSDError(OpenSalesTaxError):
    """Non-USD amount or non-US address. The engine is USD-only by design."""
