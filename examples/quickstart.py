# SPDX-License-Identifier: Apache-2.0
"""Minimal end-to-end example for opensalestax-python.

Run with::

    pip install opensalestax
    OST_BASE_URL=http://localhost:8080 python examples/quickstart.py
"""

from __future__ import annotations

import os
from decimal import Decimal

from opensalestax import (
    Address,
    LineItem,
    OpenSalesTaxAPIError,
    OpenSalesTaxClient,
    OpenSalesTaxNetworkError,
)


def main() -> None:
    base_url = os.environ.get("OST_BASE_URL", "http://localhost:8080")
    api_key = os.environ.get("OST_API_KEY")  # optional

    with OpenSalesTaxClient(base_url=base_url, api_key=api_key) as client:
        health = client.health()
        print(f"Engine v{health.version} — status={health.status}, db={health.database_connected}")

        try:
            result = client.calculate(
                address=Address(zip5="55401"),  # Minneapolis, MN
                line_items=[
                    LineItem(amount=Decimal("100.00"), category="general"),
                    LineItem(amount=Decimal("50.00"), category="clothing"),
                ],
            )
        except OpenSalesTaxNetworkError as e:
            print(f"Engine unreachable: {e}")
            return
        except OpenSalesTaxAPIError as e:
            print(f"Engine returned {e.status_code}: {e}")
            return

        print(f"Subtotal: ${result.subtotal}")
        print(f"Tax:      ${result.tax_total}")
        for line in result.lines:
            print(f"  {line.category} ${line.amount} -> tax ${line.tax}")
            for j in line.jurisdictions:
                tax = j.tax if j.tax is not None else Decimal("0")
                print(f"    {j.name} ({j.type}) {j.rate_pct}% = ${tax}")
            if line.note:
                print(f"    note: {line.note}")
        print()
        print(result.disclaimer)


if __name__ == "__main__":
    main()
