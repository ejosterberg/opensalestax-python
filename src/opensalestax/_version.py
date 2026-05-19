# SPDX-License-Identifier: Apache-2.0
__version__ = "0.3.1"

# Engine v0.59.0 introduced GET /v1/capabilities, which the SDK's
# OpenSalesTaxClient.capabilities() / .capabilities_cached() depend on.
# Older engines respond with 404. Not enforced automatically; exposed for
# connector code that wants to compare against client.capabilities().version
# at setup time and surface a clear "engine too old" error.
MIN_ENGINE_VERSION = "0.59.0"
