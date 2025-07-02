"""Support for Victron Venus sensors.

This module is light-weight and only registers the sensors with Home Assistant. The sensor class is implemented in the victronvenus_sensor module.
"""

import logging
from typing import List
from victron_mqtt import (
    Device as VictronVenusDevice,
    Hub,
    Metric as VictronVenusMetric,
    MetricKind,
)

from .common import VictronBaseEntity, _map_device_info
from homeassistant.components.sensor import SensorEntity
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
    """Set up Victron Venus sensors from a config entry."""

    hub: Hub = config_entry.runtime_data
    sensors: List[VictronSensor] = []
    for device in hub.devices:
        info = _map_device_info(device)

        # Filter metrics that represent sensors controls
        sensor_metrics = [m for m in device.metrics if  m.metric_kind == MetricKind.SENSOR]      
        if not sensor_metrics:
            continue

        _LOGGER.info("Setting up sensors for device: %s. info: %s", device, info)
        for metric in sensor_metrics:
            _LOGGER.debug("Setting up sensor: %s", repr(metric))
            sensor = VictronSensor(device, metric, info)
            sensors.append(sensor)

    if sensors:
        async_add_entities(sensors)
        for sensor in sensors:
            sensor.mark_registered_with_homeassistant()


class VictronSensor(VictronBaseEntity, SensorEntity):
    """Implementation of a Victron Venus sensor."""

    def __init__(
        self,
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor based on detauls in the metric."""
        super().__init__(device, metric, device_info, "sensor")
        self._attr_native_value = metric.value

        _LOGGER.info("Sensor %s added", repr(self))

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronSensor({super().__repr__()})"


    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_native_value = metric.value
        self.async_write_ha_state()

