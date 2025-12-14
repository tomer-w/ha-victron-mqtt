"""Support for Victron Venus number entities."""

import logging
from typing import Any

from victron_mqtt import (
    Device as VictronVenusDevice,
    Metric as VictronVenusMetric,
    MetricKind,
    WritableMetric as VictronVenusWritableMetric,
)

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

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
                VictronNumber(
                    device,
                    metric,
                    device_info,
                    hub.simple_naming,
                    installation_id,
                )
            ]
        )

    hub.register_new_metric_callback(MetricKind.NUMBER, on_new_metric)


class VictronNumber(VictronBaseEntity, NumberEntity):
    """Implementation of a Victron Venus number entity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        writable_metric: VictronVenusWritableMetric,
        device_info: DeviceInfo,
        simple_naming: bool,
        installation_id: str,
    ) -> None:
        """Initialize the number entity."""
        self._attr_native_value = writable_metric.value
        if isinstance(writable_metric.min_value, int | float):
            self._attr_native_min_value = writable_metric.min_value
        if isinstance(writable_metric.max_value, int | float):
            self._attr_native_max_value = writable_metric.max_value
        if isinstance(writable_metric.step, int | float):
            self._attr_native_step = writable_metric.step
        super().__init__(
            device,
            writable_metric,
            device_info,
            "number",
            simple_naming,
            installation_id,
        )

    @callback
    def _on_update_task(self, value: Any) -> None:
        if self._attr_native_value == value:
            return
        self._attr_native_value = value
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the current value."""
        return self._metric.value

    def set_native_value(self, value: float) -> None:
        """Set a new value."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        _LOGGER.info("Setting number %s on switch: %s", value, self._attr_unique_id)
        self._metric.set(value)
