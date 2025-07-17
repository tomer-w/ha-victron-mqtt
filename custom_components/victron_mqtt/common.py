import logging
import asyncio
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass

from victron_mqtt import (
    Device as VictronVenusDevice,
    Metric as VictronVenusMetric,
    DeviceType,
    MetricNature,
    MetricType,
)

_LOGGER = logging.getLogger(__name__)

asyncio_event_loop: asyncio.AbstractEventLoop | None = None

def init_event_loop():
    global asyncio_event_loop
    asyncio_event_loop = asyncio.get_event_loop()

def get_event_loop() -> asyncio.AbstractEventLoop:
    """Get the current asyncio event loop."""
    global asyncio_event_loop
    assert asyncio_event_loop is not None
    return asyncio_event_loop

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
        self._attr_unique_id = f"{type}.victron_mqtt_{metric.unique_id}"
        self.entity_id = self._attr_unique_id
        self._attr_native_unit_of_measurement = metric.unit_of_measurement
        self._attr_device_class = self._map_metric_to_device_class(metric)
        self._attr_state_class = self._map_metric_to_stateclass(metric)
        self._attr_native_value = metric.value
        self._attr_should_poll = False
        self._attr_has_entity_name = True
        self._attr_suggested_display_precision = metric.precision
        self._attr_translation_key = metric.generic_short_id.replace('{', '').replace('}', '') # same as in merge_topics.py
        self._attr_translation_placeholders = metric.key_values
        _LOGGER.info("%s %s added. Based on: %s", type, self, repr(metric))

    def __repr__(self) -> str:
        """Return a string representation of the entity."""
        return (
            f"VictronBaseEntity(device={self._device.name}, "
            f"unique_id={self._attr_unique_id}, "
            f"metric={self._metric.short_id}, "
            f"translation_key={self._attr_translation_key}, "
            f"translation_placeholders={self._attr_translation_placeholders}, "
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
            return SensorStateClass.TOTAL
        if metric.metric_nature == MetricNature.INSTANTANEOUS:
            return SensorStateClass.MEASUREMENT

        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about the sensor."""
        return self._device_info
