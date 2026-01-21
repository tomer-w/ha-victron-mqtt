"""Support for Victron Venus buttons."""

import logging
from typing import Any

from victron_mqtt import (
    Device as VictronVenusDevice,
    Metric as VictronVenusMetric,
    MetricKind,
    WritableMetric as VictronVenusWritableMetric,
)

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import SWITCH_ON
from .entity import VictronBaseEntity
from .hub import Hub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Victron Venus sensors from a config entry."""
    hub: Hub = config_entry.runtime_data

    def on_new_metric(
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
        installation_id: str,
    ) -> None:
        """Handle new sensor metric discovery."""
        assert isinstance(metric, VictronVenusWritableMetric)
        async_add_entities(
            [
                VictronButton(
                    device,
                    metric,
                    device_info,
                    hub.simple_naming,
                    installation_id,
                )
            ]
        )

    hub.register_new_metric_callback(MetricKind.BUTTON, on_new_metric)


class VictronButton(VictronBaseEntity, ButtonEntity):
    """Implementation of a Victron Venus button using ButtonEntity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        metric: VictronVenusWritableMetric,
        device_info: DeviceInfo,
        simple_naming: bool,
        installation_id: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(
            device, metric, device_info, "button", simple_naming, installation_id
        )

    @callback
    def _on_update_task(self, value: Any) -> None:
        pass

    def press(self) -> None:
        """Press the button."""
        _LOGGER.info("Pressing button: %s", self._attr_unique_id)
        assert isinstance(self._metric, VictronVenusWritableMetric)
        self._metric.set(SWITCH_ON)
