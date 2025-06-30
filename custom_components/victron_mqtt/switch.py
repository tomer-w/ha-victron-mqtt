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
    GenericOnOff,
)

from homeassistant.components.switch import SwitchEntity
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
    switches: List[VictronSwitch] = []   
    for device in hub.devices:
        info = _map_device_info(device)
        
        # Filter metrics that represent switch-like controls
        switch_metrics = [m for m in device.metrics if  m.metric_kind == MetricKind.SWITCH]      
        if not switch_metrics:
            continue

        _LOGGER.debug("Setting up select switches for device: %s", device)

        for metric in switch_metrics:
            assert  isinstance(metric, Switch)
            _LOGGER.debug("Setting up switch: %s", repr(metric))
            switch = VictronSwitch(device, metric, info)
            switches.append(switch)

    if switches:
        async_add_entities(switches)
        for switch in switches:
            switch.mark_registered_with_homeassistant()


class VictronSwitch(SwitchEntity):
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
        self._attr_unique_id = f"{switch.unique_id}_switch"
        self._attr_should_poll = False
        self._attr_has_entity_name = True
        self._attr_is_on = switch.value 

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
            f"VictronSwitch(device={self._device.name}, "
            f"metric={self._switch.short_id}, "
            f"translation_key={self._attr_translation_key}, "
            f"value={self._attr_native_value})"
        )

    def _on_update(self, metric: VictronVenusMetric):
        assert asyncio_event_loop is not None
        asyncio.run_coroutine_threadsafe(self._on_update_task(metric), asyncio_event_loop)

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_is_on = metric.value == GenericOnOff.On
        self.async_write_ha_state()

    def mark_registered_with_homeassistant(self):
        """Mark the switch as registered with Home Assistant."""
        self._switch.on_update = self._on_update

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about the switch."""
        return self._device_info

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        # Adjust this logic to match your switch's 'on' value
        return bool(self._switch.value)

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._switch.set(GenericOnOff.On)
        self.async_write_ha_state()

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self._switch.set(GenericOnOff.On)
        self.async_write_ha_state()
