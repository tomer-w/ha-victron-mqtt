import logging
import asyncio
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass

from victron_mqtt import Device as VictronVenusDevice

from . import get_event_loop
from .const import DOMAIN
from victron_mqtt import (
    Device as VictronVenusDevice,
    Hub,
    Metric as VictronVenusMetric,
)
from victron_mqtt.constants import (
    PLACEHOLDER_PHASE,
    DeviceType,
    MetricNature,
    MetricType,
)

_LOGGER = logging.getLogger(__name__)

def _map_device_info(device: VictronVenusDevice) -> DeviceInfo:
    info: DeviceInfo = {}
    info["identifiers"] = {(DOMAIN, device.unique_id)}
    info["manufacturer"] = device.manufacturer if device.manufacturer is not None else "Victron Energy"
    info["name"] = f"{device.name} (ID: {device.device_id})" if device.device_id != "0" else device.name
    info["model"] = device.model
    info["serial_number"] = device.serial_number

    return info

class VictronBaseEntity(Entity):
    """Implementation of a Victron Venus base entity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
        type: str,
    ) -> None:
        """Initialize the sensor based on detauls in the metric."""
        self._device = device
        self._metric = metric
        self._device_info = device_info
        self._attr_name = metric.name
        self._attr_native_unit_of_measurement = metric.unit_of_measurement
        self._attr_device_class = self._map_metric_to_device_class(metric)
        self._attr_state_class = self._map_metric_to_stateclass(metric)
        self._attr_unique_id = f"{metric.unique_id}_{type}"
        self._attr_native_value = metric.value
        self._attr_should_poll = False
        self._attr_has_entity_name = True
        self._attr_suggested_display_precision = metric.precision
        _LOGGER.info("VictronBaseEntity %s added", repr(self))

    def __repr__(self) -> str:
        """Return a string representation of the entity."""
        return (
            f"VictronBaseEntity(device={self._device.name}, "
            f"metric={self._metric.short_id}, "
            f"value={self._attr_native_value})"
        )

    def _on_update(self, metric: VictronVenusMetric):
        asyncio.run_coroutine_threadsafe(self._on_update_task(metric), get_event_loop())

    def mark_registered_with_homeassistant(self):
        """Mark the sensor as registered with Home Assistant, so that updates can be propagated."""
        self._metric.on_update = self._on_update

    def _map_metric_to_device_class(
        self, metric: VictronVenusMetric
    ) -> SensorDeviceClass | None:
        match metric.metric_type:
            case MetricType.TEMPERATURE:
                return SensorDeviceClass.TEMPERATURE
            case MetricType.POWER:
                if metric.unit_of_measurement == "VA":
                    return SensorDeviceClass.APPARENT_POWER
                return SensorDeviceClass.POWER
            case MetricType.ENERGY:
                return SensorDeviceClass.ENERGY
            case MetricType.VOLTAGE:
                return SensorDeviceClass.VOLTAGE
            case MetricType.CURRENT:
                return SensorDeviceClass.CURRENT
            case MetricType.FREQUENCY:
                return SensorDeviceClass.FREQUENCY
            case MetricType.PERCENTAGE:
                if metric.device_type == DeviceType.BATTERY:
                    return SensorDeviceClass.BATTERY
                return None
            case _:
                return None

    def _map_metric_to_stateclass(
        self, metric: VictronVenusMetric
    ) -> SensorStateClass | None:
        if metric.metric_nature == MetricNature.CUMULATIVE:
            return SensorStateClass.TOTAL_INCREASING
        if metric.metric_nature == MetricNature.INSTANTANEOUS:
            return SensorStateClass.MEASUREMENT

        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about the sensor."""
        return self._device_info
