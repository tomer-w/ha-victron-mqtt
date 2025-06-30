"""Support for Victron Venus binary sensors."""

import logging
import asyncio
from typing import List
from victron_mqtt import (
    Device as VictronVenusDevice,
    Hub,
    Metric as VictronVenusMetric,
    MetricKind,
    GenericOnOff,
)

from .common import _map_device_info
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import PLACEHOLDER_PHASE
_LOGGER = logging.getLogger(__name__)

asyncio_event_loop: asyncio.AbstractEventLoop | None = None

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Victron Venus binary sensors from a config entry."""

    global asyncio_event_loop
    asyncio_event_loop = asyncio.get_event_loop()

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


class VictronBinarySensor(BinarySensorEntity):
    """Implementation of a Victron Venus binary sensor."""

    def __init__(
        self,
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
    ) -> None:
        self._device = device
        self._metric = metric
        self._device_info = device_info
        self._attr_unique_id = f"{metric.unique_id}_binary_sensor"
        self._attr_should_poll = False
        self._attr_has_entity_name = True
        translation_key = metric.generic_short_id
        translation_key = translation_key.replace(
            PLACEHOLDER_PHASE, "lx"
        )
        self._attr_translation_key = translation_key
        if metric.phase is not None:
            self._attr_translation_placeholders = {"phase": metric.phase}
        self._attr_is_on = bool(metric.value)
        _LOGGER.info("BinarySensor %s added", repr(self))

    def __repr__(self) -> str:
        return (
            f"VictronBinarySensor(device={self._device.name}, "
            f"metric={self._metric.short_id}, "
            f"translation_key={self._attr_translation_key}, "
            f"is_on={self._attr_is_on})"
        )

    def _on_update(self, metric: VictronVenusMetric):
        assert asyncio_event_loop is not None
        asyncio.run_coroutine_threadsafe(self._on_update_task(metric), asyncio_event_loop)

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_is_on = metric.value == GenericOnOff.On
        self.async_write_ha_state()

    def mark_registered_with_homeassistant(self):
        self._metric.on_update = self._on_update

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def is_on(self) -> bool:
        return self._attr_is_on
