"""Per-product capability lookup for Victron devices.

Maps a Victron product (identified by the ``.../ProductId`` topic) to a set of
static, model-specific capabilities that the GX does not always publish over
MQTT. The first use case is the maximum charge current of VE.Direct solar
chargers and alternators, whose sliders would otherwise default to an
oversized static range.

The registry is intentionally generic: add fields to :class:`ProductCapabilities`
and rows to ``_PRODUCT_CAPABILITIES`` to expose new model-specific facts, and
reuse :func:`get_product_capabilities` wherever a device-dependent value is
needed.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._victron_enums import VictronProductId


@dataclass(frozen=True)
class ProductCapabilities:
    """Static, model-specific capabilities for a Victron product."""

    max_charge_current: float | None = None
    # Extend with further model-specific capabilities as needed, e.g.:
    # max_discharge_current: float | None = None


# Keyed by the readable VictronProductId constant (never raw hex).
# For MPPT solar chargers the max charge current is the second number in the
# model name (e.g. "100/50" -> 50 A).
_PRODUCT_CAPABILITIES: dict[VictronProductId, ProductCapabilities] = {
    # BlueSolar MPPT
    VictronProductId.BLUESOLAR_MPPT_75_15: ProductCapabilities(max_charge_current=15),
    VictronProductId.BLUESOLAR_MPPT_100_15: ProductCapabilities(max_charge_current=15),
    VictronProductId.BLUESOLAR_MPPT_100_30: ProductCapabilities(max_charge_current=30),
    VictronProductId.BLUESOLAR_MPPT_100_50: ProductCapabilities(max_charge_current=50),
    VictronProductId.BLUESOLAR_MPPT_150_70: ProductCapabilities(max_charge_current=70),
    VictronProductId.BLUESOLAR_MPPT_75_10: ProductCapabilities(max_charge_current=10),
    VictronProductId.BLUESOLAR_MPPT_150_45: ProductCapabilities(max_charge_current=45),
    VictronProductId.BLUESOLAR_MPPT_150_60: ProductCapabilities(max_charge_current=60),
    VictronProductId.BLUESOLAR_MPPT_150_85: ProductCapabilities(max_charge_current=85),
    # SmartSolar MPPT
    VictronProductId.SMARTSOLAR_MPPT_250_100: ProductCapabilities(max_charge_current=100),
    VictronProductId.SMARTSOLAR_MPPT_150_100: ProductCapabilities(max_charge_current=100),
    VictronProductId.SMARTSOLAR_MPPT_150_85: ProductCapabilities(max_charge_current=85),
    VictronProductId.SMARTSOLAR_MPPT_75_15: ProductCapabilities(max_charge_current=15),
    VictronProductId.SMARTSOLAR_MPPT_75_10: ProductCapabilities(max_charge_current=10),
    VictronProductId.SMARTSOLAR_MPPT_100_15: ProductCapabilities(max_charge_current=15),
    VictronProductId.SMARTSOLAR_MPPT_100_30: ProductCapabilities(max_charge_current=30),
    VictronProductId.SMARTSOLAR_MPPT_100_50: ProductCapabilities(max_charge_current=50),
    VictronProductId.SMARTSOLAR_MPPT_150_35: ProductCapabilities(max_charge_current=35),
    VictronProductId.SMARTSOLAR_MPPT_150_100_REV2: ProductCapabilities(max_charge_current=100),
    VictronProductId.SMARTSOLAR_MPPT_150_85_REV2: ProductCapabilities(max_charge_current=85),
    VictronProductId.SMARTSOLAR_MPPT_250_70: ProductCapabilities(max_charge_current=70),
    VictronProductId.SMARTSOLAR_MPPT_250_85: ProductCapabilities(max_charge_current=85),
    VictronProductId.SMARTSOLAR_MPPT_250_60: ProductCapabilities(max_charge_current=60),
    VictronProductId.SMARTSOLAR_MPPT_250_45: ProductCapabilities(max_charge_current=45),
    VictronProductId.SMARTSOLAR_MPPT_100_20: ProductCapabilities(max_charge_current=20),
    VictronProductId.SMARTSOLAR_MPPT_100_20_48V: ProductCapabilities(max_charge_current=20),
    VictronProductId.SMARTSOLAR_MPPT_150_45: ProductCapabilities(max_charge_current=45),
    VictronProductId.SMARTSOLAR_MPPT_150_60: ProductCapabilities(max_charge_current=60),
    VictronProductId.SMARTSOLAR_MPPT_150_70: ProductCapabilities(max_charge_current=70),
}


def get_product_capabilities(product_id: int | None) -> ProductCapabilities | None:
    """Return the capabilities for a product ID, or ``None`` if unknown."""
    if product_id is None:
        return None
    member = VictronProductId.from_code(product_id)
    if member is None:
        return None
    return _PRODUCT_CAPABILITIES.get(member)
