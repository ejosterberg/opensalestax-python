# SPDX-License-Identifier: Apache-2.0
"""Tests for the engine v0.59.0 /v1/capabilities adoption."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from opensalestax import (
    MIN_ENGINE_VERSION,
    CapabilitiesResponse,
    CapabilityEndpoint,
    CapabilityFeatures,
    OpenSalesTaxClient,
)

_FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def capabilities_payload() -> dict[str, Any]:
    with (_FIXTURE_DIR / "capabilities.json").open(encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


class TestCapabilitiesResponseDecoding:
    """Live-fixture decoding — captured from engine VM 906 on 2026-05-18."""

    def test_decodes_engine_v059_fixture(self, capabilities_payload: dict[str, Any]) -> None:
        features = CapabilityFeatures.from_engine(capabilities_payload["features"])
        endpoints = {
            name: CapabilityEndpoint.model_validate(meta)
            for name, meta in capabilities_payload["endpoints"].items()
        }
        caps = CapabilitiesResponse.model_construct(
            version=capabilities_payload["version"],
            endpoints=endpoints,
            features=features,
        )

        assert caps.version == "0.59.0"
        assert "calculate" in caps.endpoints
        assert caps.endpoints["calculate"].path == "/v1/calculate"
        assert caps.endpoints["calculate"].version == 1

        # Known feature flags surface as typed bool attributes.
        assert caps.features.coverage_warning is True
        assert caps.features.shipping_first_class is True
        assert caps.features.vendor_allocation is False
        assert caps.features.transaction_record_back is False
        # No unknown flags in v0.59.0 — extras should be empty.
        assert caps.features.extras == {}

    def test_features_forward_compat_preserves_unknown_flags(self) -> None:
        future = {
            "shipping_first_class": True,
            "some_future_flag": True,
            "another_one": False,
        }
        features = CapabilityFeatures.from_engine(future)
        assert features.shipping_first_class is True
        assert features.extras == {"some_future_flag": True, "another_one": False}
        # Flags omitted by engine default to False (stable typed surface).
        assert features.coverage_warning is False
        assert features.vendor_allocation is False
        assert features.transaction_record_back is False

    def test_features_tolerates_non_bool_engine_drift(self) -> None:
        # Engine drift: a string slipped through where a bool should be.
        # SDK silently coerces to False rather than throwing — consistent
        # with PHP/JS SDK behavior on the same case.
        drift = {"coverage_warning": "yes"}
        features = CapabilityFeatures.from_engine(drift)
        assert features.coverage_warning is False


class TestClientCapabilities:
    """Round-trip via respx-mocked HTTP."""

    def test_capabilities_fetches_fresh_each_call(
        self, base_url: str, capabilities_payload: dict[str, Any]
    ) -> None:
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            route = router.get("/v1/capabilities").mock(
                return_value=httpx.Response(200, json=capabilities_payload)
            )
            client = OpenSalesTaxClient(base_url=base_url)
            try:
                client.capabilities()
                client.capabilities()
                client.capabilities()
                assert route.call_count == 3, "capabilities() should NOT memoize"
            finally:
                client.close()

    def test_capabilities_cached_only_hits_engine_once(
        self, base_url: str, capabilities_payload: dict[str, Any]
    ) -> None:
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            route = router.get("/v1/capabilities").mock(
                return_value=httpx.Response(200, json=capabilities_payload)
            )
            client = OpenSalesTaxClient(base_url=base_url)
            try:
                a = client.capabilities_cached()
                b = client.capabilities_cached()
                c = client.capabilities_cached()
                assert route.call_count == 1, "capabilities_cached() should memoize"
                assert a is b
                assert b is c
                assert a.version == "0.59.0"
            finally:
                client.close()

    def test_capabilities_cached_does_not_share_across_instances(
        self, base_url: str, capabilities_payload: dict[str, Any]
    ) -> None:
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            route = router.get("/v1/capabilities").mock(
                return_value=httpx.Response(200, json=capabilities_payload)
            )
            client_a = OpenSalesTaxClient(base_url=base_url)
            client_b = OpenSalesTaxClient(base_url=base_url)
            try:
                client_a.capabilities_cached()
                client_b.capabilities_cached()
                assert route.call_count == 2, "separate instances must not share cache"
            finally:
                client_a.close()
                client_b.close()


class TestMinEngineVersionConstant:
    def test_min_engine_version_is_059(self) -> None:
        assert MIN_ENGINE_VERSION == "0.59.0"
