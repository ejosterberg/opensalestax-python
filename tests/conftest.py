# SPDX-License-Identifier: Apache-2.0
"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _load(name: str) -> Any:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def health_payload() -> dict[str, Any]:
    return _load("health_ok.json")


@pytest.fixture
def states_payload() -> dict[str, Any]:
    return _load("states.json")


@pytest.fixture
def rates_payload() -> dict[str, Any]:
    return _load("rates_55401.json")


@pytest.fixture
def calculate_payload() -> dict[str, Any]:
    return _load("calculate_minneapolis.json")


@pytest.fixture
def base_url() -> str:
    return "http://test.local:8080"
