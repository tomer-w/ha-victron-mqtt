"""Support for Victron Venus switches with 4 states."""

import logging
from typing import Any

from victron_mqtt import (
    Device as VictronVenusDevice,
    Metric as VictronVenusMetric,
    MetricKind,
    WritableMetric as VictronVenusWritableMetric,
)

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

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
                VictronSelect(
                    device,
                    metric,
                    device_info,
                    hub.simple_naming,
                    installation_id,
                )
            ]
        )

    hub.register_new_metric_callback(MetricKind.SELECT, on_new_metric)


class VictronSelect(VictronBaseEntity, SelectEntity):
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
        assert writable_metric.enum_values is not None
        self._attr_options = writable_metric.enum_values
        self._attr_current_option = self._map_value_to_state(writable_metric.value)
        super().__init__(
            device,
            writable_metric,
            device_info,
            "select",
            simple_naming,
            installation_id,
        )

    @callback
    def _on_update_task(self, value: Any) -> None:
        new_val = self._map_value_to_state(value)
        if self._attr_current_option == new_val:
            return
        self._attr_current_option = new_val
        self.async_write_ha_state()

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        assert self._metric.enum_values is not None
        if option not in self._metric.enum_values:
            _LOGGER.info(
                "Setting switch %s to %s failed as option not supported. supported options are: %s",
                self._attr_unique_id,
                option,
                self._metric.enum_values,
            )
            return
        _LOGGER.info("Setting switch %s to %s", self._attr_unique_id, option)
        assert isinstance(self._metric, VictronVenusWritableMetric)
        self._metric.set(option)

    def _map_value_to_state(self, value) -> str:
        """Map metric value to switch state."""
        return str(value)
