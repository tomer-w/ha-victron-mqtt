"""Support for Victron Venus switches with 4 states."""

import logging
from typing import Any

from victron_mqtt import (
    Device as VictronVenusDevice,
    Metric as VictronVenusMetric,
    MetricKind,
    WritableMetric as VictronVenusWritableMetric,
)

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import SWITCH_OFF, SWITCH_ON
from .entity import VictronBaseEntity
from .hub import Hub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Victron Venus sensors from a config entry."""
    hub: Hub = config_entry.runtime_data

    def on_new_metric(
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
        installation_id: str,
    ) -> None:
        """Handle new sensor metric discovery."""
        assert isinstance(metric, VictronVenusWritableMetric)
        async_add_entities(
            [
                VictronSwitch(
                    device,
                    metric,
                    device_info,
                    hub.simple_naming,
                    installation_id,
                )
            ]
        )

    hub.register_new_metric_callback(MetricKind.SWITCH, on_new_metric)



class VictronSwitch(VictronBaseEntity, SwitchEntity):
    """Implementation of a Victron Venus multiple state select using SelectEntity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        writable_metric: VictronVenusWritableMetric,
        device_info: DeviceInfo,
        simple_naming: bool,
        installation_id: str,
    ) -> None:
        """Initialize the switch."""
        self._attr_is_on = str(writable_metric.value) == SWITCH_ON
        super().__init__(
            device,
            writable_metric,
            device_info,
            "switch",
            simple_naming,
            installation_id,
        )

    @callback
    def _on_update_task(self, value: Any) -> None:
        new_val = str(value) == SWITCH_ON
        if self._attr_is_on == new_val:
            return
        self._attr_is_on = new_val
        self.async_write_ha_state()

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        _LOGGER.info("Turning on switch: %s", self._attr_unique_id)
        self._metric.set(SWITCH_ON)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        _LOGGER.info("Turning off switch: %s", self._attr_unique_id)
        self._metric.set(SWITCH_OFF)
