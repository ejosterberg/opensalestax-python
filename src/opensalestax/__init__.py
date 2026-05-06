# SPDX-License-Identifier: Apache-2.0
"""OpenSalesTax Python SDK — calculate US sales tax via the v1 HTTP API."""

from ._version import __version__
from .client import OpenSalesTaxClient
from .errors import (
    NonUSDError,
    OpenSalesTaxAPIError,
    OpenSalesTaxError,
    OpenSalesTaxNetworkError,
    OpenSalesTaxValidationError,
)
from .models import (
    Address,
    CalculatedLine,
    CalculationResult,
    HealthResponse,
    JurisdictionBreakdown,
    JurisdictionType,
    LineItem,
    RateStack,
    StateCoverage,
    StatesResponse,
)

__all__ = [
    "Address",
    "CalculatedLine",
    "CalculationResult",
    "HealthResponse",
    "JurisdictionBreakdown",
    "JurisdictionType",
    "LineItem",
    "NonUSDError",
    "OpenSalesTaxAPIError",
    "OpenSalesTaxClient",
    "OpenSalesTaxError",
    "OpenSalesTaxNetworkError",
    "OpenSalesTaxValidationError",
    "RateStack",
    "StateCoverage",
    "StatesResponse",
    "__version__",
]
