"""Support for Victron Venus switches with 4 states."""

import logging
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

from .common import VictronBaseEntity, _map_device_info

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Victron Venus switches from a config entry."""
    
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


class VictronSwitch(VictronBaseEntity, SwitchEntity):
    """Implementation of a Victron Venus multiple state select using SelectEntity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        switch: Switch,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the switch."""
        super().__init__(device, switch, device_info, "switch")
        self._attr_is_on = switch.value 
        _LOGGER.info("switch %s added", repr(self))

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return (
            f"VictronSwitch(device={self._device.name}, "
            f"metric={self._switch.short_id}, "
            f"translation_key={self._attr_translation_key}, "
            f"value={self._attr_native_value})"
        )

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_is_on = metric.value == GenericOnOff.On
        self.async_write_ha_state()

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        assert isinstance(self._metric, Switch)
        self._metric.set(GenericOnOff.On)
        self.async_write_ha_state()

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        assert isinstance(self._metric, Switch)
        self._metric.set(GenericOnOff.On)
        self.async_write_ha_state()
