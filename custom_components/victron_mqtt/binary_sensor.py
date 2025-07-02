"""Support for Victron Venus binary sensors."""

import logging
from typing import List
from victron_mqtt import (
    Device as VictronVenusDevice,
    Hub,
    Metric as VictronVenusMetric,
    MetricKind,
    GenericOnOff,
)

from .common import VictronBaseEntity, _map_device_info
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Victron Venus binary sensors from a config entry."""

    hub: Hub = config_entry.runtime_data
    binary_sensors: List[VictronBinarySensor] = []
    for device in hub.devices:
        info = _map_device_info(device)

        # Filter metrics that represent binary sesnor controls
        binary_sensors_metrics = [m for m in device.metrics if m.metric_kind == MetricKind.BINARY_SENSOR]
        if not binary_sensors_metrics:
            continue

        _LOGGER.info("Setting up binary sensors for device: %s. info: %s", device, info)
        for metric in binary_sensors_metrics:
            binary_sensor = VictronBinarySensor(device, metric, info)
            binary_sensors.append(binary_sensor)

    if binary_sensors:
        async_add_entities(binary_sensors)
        for binary_sensor in binary_sensors:
            binary_sensor.mark_registered_with_homeassistant()


class VictronBinarySensor(VictronBaseEntity, BinarySensorEntity):
    """Implementation of a Victron Venus binary sensor."""

    def __init__(
        self,
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(device, metric, device_info, "binary_sensor")
        self._attr_is_on = bool(metric.value)
        _LOGGER.info("BinarySensor %s added", repr(self))

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronNumber({super().__repr__()}), is_on={self._attr_is_on})"

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_is_on = metric.value == GenericOnOff.On
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        return self._attr_is_on
