# SPDX-License-Identifier: Apache-2.0
"""Error class hierarchy tests."""

from __future__ import annotations

import pytest

from opensalestax import (
    NonUSDError,
    OpenSalesTaxAPIError,
    OpenSalesTaxError,
    OpenSalesTaxNetworkError,
    OpenSalesTaxValidationError,
)


def test_base_class() -> None:
    assert issubclass(OpenSalesTaxError, Exception)


@pytest.mark.parametrize(
    "subclass",
    [
        OpenSalesTaxNetworkError,
        OpenSalesTaxAPIError,
        OpenSalesTaxValidationError,
        NonUSDError,
    ],
)
def test_subclass_inherits_base(subclass: type[Exception]) -> None:
    assert issubclass(subclass, OpenSalesTaxError)


def test_api_error_carries_context() -> None:
    body = {"detail": "bad zip"}
    err = OpenSalesTaxAPIError(status_code=400, message="bad zip", response_body=body)
    assert err.status_code == 400
    assert err.response_body == body
    assert "400" in str(err)
    assert "bad zip" in str(err)


def test_api_error_no_body() -> None:
    err = OpenSalesTaxAPIError(status_code=500, message="upstream")
    assert err.response_body is None
    assert err.status_code == 500


def test_network_error_chains_cause() -> None:
    src = TimeoutError("connect timed out")
    with pytest.raises(OpenSalesTaxNetworkError) as exc:
        raise OpenSalesTaxNetworkError("timeout") from src
    assert exc.value.__cause__ is src
