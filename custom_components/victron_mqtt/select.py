"""Support for Victron Venus switches with 4 states."""

import logging
import asyncio
from typing import List
from victron_mqtt import (
    Device as VictronVenusDevice,
    Hub,
    Metric as VictronVenusMetric,
    Switch,
    MetricKind,
)

from homeassistant.components.select import SelectEntity
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
    """Set up Victron Venus switches from a config entry."""
    
    global asyncio_event_loop
    asyncio_event_loop = asyncio.get_event_loop()

    hub: Hub = config_entry.runtime_data
    selects: List[VictronSelect] = []   
    for device in hub.devices:
        info = _map_device_info(device)
        
        # Filter metrics that represent select-like controls
        select_metrics = [m for m in device.metrics if m.metric_kind == MetricKind.SELECT]
        if not select_metrics:
            continue

        _LOGGER.debug("Setting up select switches for device: %s", device)

        for metric in select_metrics:
            _LOGGER.debug("Setting up switch: %s", repr(metric))
            assert  isinstance(metric, Switch)
            switch = VictronSelect(device, metric, info)
            selects.append(switch)

    if selects:
        async_add_entities(selects)
        for select in selects:
            select.mark_registered_with_homeassistant()


class VictronSelect(SelectEntity):
    """Implementation of a Victron Venus multiple state select using SelectEntity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        switch: Switch,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the switch."""
        self._device = device
        self._switch = switch
        self._device_info = device_info
        self._attr_unique_id = f"{switch.unique_id}_select"
        self._attr_should_poll = False
        self._attr_has_entity_name = True
        self._attr_options = switch.enum_values
        self._attr_current_option = self._map_value_to_state(switch.value)
        self._attr_translation_key = f"{switch.generic_short_id}_select"
        translation_key = switch.generic_short_id
        translation_key = translation_key.replace(
            PLACEHOLDER_PHASE, "lx"
        )  # for translation key we do generic replacement
        self._attr_translation_key = translation_key
        if switch.phase is not None:
            self._attr_translation_placeholders = {"phase": switch.phase}

        _LOGGER.info("Sensor %s added", repr(self))

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return (
            f"VictronSelect(device={self._device.name}, "
            f"metric={self._switch.short_id}, "
            f"translation_key={self._attr_translation_key}, "
            f"value={self._attr_current_option})"
        )

    def _on_update(self, metric: VictronVenusMetric):
        assert asyncio_event_loop is not None
        asyncio.run_coroutine_threadsafe(self._on_update_task(metric), asyncio_event_loop)

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_current_option = self._map_value_to_state(metric.value)
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        assert self._switch.enum_values is not None
        if option not in self._switch.enum_values:
            _LOGGER.info("Setting switch %s to %s failed as option not supported. supported options are: %s", self._attr_unique_id, option, self._switch.enum_values)
            return
        # Here you would implement the actual command to change the switch state
        # This depends on your victron_mqtt library's command interface
        _LOGGER.info("Setting switch %s to %s", self._attr_unique_id, option)
        self._switch.set(option)

    def mark_registered_with_homeassistant(self):
        """Mark the switch as registered with Home Assistant."""
        self._switch.on_update = self._on_update

    def _map_value_to_state(self, value) -> str:
        """Map metric value to switch state."""
        #for now jut return the same thing
        return str(value)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about the switch."""
        return self._device_info
