# SPDX-License-Identifier: Apache-2.0
"""OpenSalesTax Python SDK — calculate US sales tax via the v1 HTTP API."""

from ._version import MIN_ENGINE_VERSION, __version__
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
    CalculatedShipping,
    CalculationResult,
    CapabilitiesResponse,
    CapabilityEndpoint,
    CapabilityFeatures,
    HealthResponse,
    JurisdictionBreakdown,
    JurisdictionType,
    LineItem,
    RateStack,
    Shipping,
    StateCoverage,
    StatesResponse,
)

__all__ = [
    "MIN_ENGINE_VERSION",
    "Address",
    "CalculatedLine",
    "CalculatedShipping",
    "CalculationResult",
    "CapabilitiesResponse",
    "CapabilityEndpoint",
    "CapabilityFeatures",
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
    "Shipping",
    "StateCoverage",
    "StatesResponse",
    "__version__",
]
