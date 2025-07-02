"""Support for Victron Venus switches with 4 states."""

import logging
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

from .common import VictronBaseEntity, _map_device_info

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Victron Venus switches from a config entry."""
    
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


class VictronSelect(VictronBaseEntity, SelectEntity):
    """Implementation of a Victron Venus multiple state select using SelectEntity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        switch: Switch,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the switch."""
        super().__init__(device, switch, device_info, "select")
        self._attr_options = switch.enum_values
        self._attr_current_option = self._map_value_to_state(switch.value)
        _LOGGER.info("Sensor %s added", repr(self))

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronSelect({super().__repr__()})"

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_current_option = self._map_value_to_state(metric.value)
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        assert self._metric.enum_values is not None
        if option not in self._metric.enum_values:
            _LOGGER.info("Setting switch %s to %s failed as option not supported. supported options are: %s", self._attr_unique_id, option, self._metric.enum_values)
            return
        _LOGGER.info("Setting switch %s to %s", self._attr_unique_id, option)
        assert isinstance(self._metric, Switch)
        self._metric.set(option)

    def _map_value_to_state(self, value) -> str:
        """Map metric value to switch state."""
        #for now jut return the same thing
        return str(value)
