"""Support for Victron Venus number entities."""

import logging
from typing import List
from victron_mqtt import (
    Device as VictronVenusDevice,
    Hub,
    Metric as VictronVenusMetric,
    MetricKind,
    Switch,
)

from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .common import VictronBaseEntity, _map_device_info

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Victron Venus numbers from a config entry."""

    hub: Hub = config_entry.runtime_data
    numbers: List[VictronNumber] = []
    for device in hub.devices:
        info = _map_device_info(device)

        # Filter metrics that represent number-like controls
        number_metrics = [m for m in device.metrics if m.metric_kind == MetricKind.NUMBER]
        if not number_metrics:
            continue

        _LOGGER.debug("Setting up number entities for device: %s", device)

        for metric in number_metrics:
            assert  isinstance(metric, Switch)
            _LOGGER.debug("Setting up number: %s", repr(metric))
            number = VictronNumber(device, metric, info)
            numbers.append(number)

    if numbers:
        async_add_entities(numbers)
        for number in numbers:
            number.mark_registered_with_homeassistant()


class VictronNumber(VictronBaseEntity, NumberEntity):
    """Implementation of a Victron Venus number entity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        switch: Switch,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(device, switch, device_info, "number")
        self._attr_native_value = switch.value
        self._attr_native_min_value = switch.min_value
        self._attr_native_max_value = switch.max_value
        self._attr_native_step = 1 #TODO: Add support for different steps
        _LOGGER.info("Number %s added", repr(self))

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronNumber({super().__repr__()})"

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_native_value = metric.value
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the current value."""
        return self._metric.value

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        assert isinstance(self._metric, Switch)
        self._metric.set(value)
        self.async_write_ha_state()
