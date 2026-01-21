"""Support for Victron Venus binary sensors."""

import logging
from typing import Any

from victron_mqtt import (
    Device as VictronVenusDevice,
    Metric as VictronVenusMetric,
    MetricKind,
)

from homeassistant.components.binary_sensor import BinarySensorEntity
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
        async_add_entities(
            [
                VictronBinarySensor(
                    device, metric, device_info, hub.simple_naming, installation_id
                )
            ]
        )

    hub.register_new_metric_callback(MetricKind.BINARY_SENSOR, on_new_metric)


class VictronBinarySensor(VictronBaseEntity, BinarySensorEntity):
    """Implementation of a Victron Venus binary sensor."""

    def __init__(
        self,
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
        simple_naming: bool,
        installation_id: str,
    ) -> None:
        """Initialize the binary sensor."""
        self._attr_is_on = self._is_on(metric.value)
        super().__init__(
            device, metric, device_info, "binary_sensor", simple_naming, installation_id
        )

    @staticmethod
    def _is_on(value: Any) -> bool:
        return str(value) == SWITCH_ON

    @callback
    def _on_update_task(self, value: Any) -> None:
        new_val = self._is_on(value)
        if self._attr_is_on == new_val:
            return
        self._attr_is_on = new_val
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return the current state of the binary sensor."""
        assert self._attr_is_on is not None
        return self._attr_is_on
