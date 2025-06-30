"""Support for Victron Venus number entities."""

import logging
import asyncio
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

from .const import PLACEHOLDER_PHASE
from .common import _map_device_info

_LOGGER = logging.getLogger(__name__)

asyncio_event_loop: asyncio.AbstractEventLoop | None = None

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Victron Venus numbers from a config entry."""

    global asyncio_event_loop
    asyncio_event_loop = asyncio.get_event_loop()

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


class VictronNumber(NumberEntity):
    """Implementation of a Victron Venus number entity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        switch: Switch,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the number entity."""
        self._device = device
        self._switch = switch
        self._device_info = device_info
        self._attr_unique_id = f"{switch.unique_id}_number"
        self._attr_should_poll = False
        self._attr_has_entity_name = True
        self._attr_native_value = switch.value
        self._attr_native_min_value = switch.min_value
        self._attr_native_max_value = switch.max_value
        self._attr_native_step = 1 #TODO: Add support for different steps

        translation_key = switch.generic_short_id
        translation_key = translation_key.replace(
            PLACEHOLDER_PHASE, "lx"
        )
        self._attr_translation_key = translation_key
        if switch.phase is not None:
            self._attr_translation_placeholders = {"phase": switch.phase}

        _LOGGER.info("Number %s added", repr(self))

    def __repr__(self) -> str:
        """Return a string representation of the number entity."""
        return (
            f"VictronNumber(device={self._device.name}, "
            f"metric={self._switch.short_id}, "
            f"translation_key={self._attr_translation_key}, "
            f"value={self._attr_native_value})"
        )

    def _on_update(self, metric: VictronVenusMetric):
        assert asyncio_event_loop is not None
        asyncio.run_coroutine_threadsafe(self._on_update_task(metric), asyncio_event_loop)

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_native_value = metric.value
        self.async_write_ha_state()

    def mark_registered_with_homeassistant(self):
        """Mark the number as registered with Home Assistant."""
        self._switch.on_update = self._on_update

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about the number."""
        return self._device_info

    @property
    def native_value(self):
        """Return the current value."""
        return self._switch.value

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        self._switch.set(value)
        self.async_write_ha_state()
