"""Support for Time entities in Victron Venus devices."""

from datetime import time
import logging
from typing import Any

from victron_mqtt import (
    Device as VictronVenusDevice,
    Metric as VictronVenusMetric,
    MetricKind,
    WritableMetric as VictronVenusWritableMetric,
)

from homeassistant.components.time import TimeEntity
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
                VictronTime(
                    device,
                    metric,
                    device_info,
                    hub.simple_naming,
                    installation_id,
                )
            ]
        )

    hub.register_new_metric_callback(MetricKind.TIME, on_new_metric)



class VictronTime(VictronBaseEntity, TimeEntity):
    """Implementation of a Victron Venus time entity (represented as a sensor)."""

    @staticmethod
    def victron_time_to_time(value: int | None) -> time | None:
        """Convert minutes since midnight to time object."""
        if value is None:
            return None
        total_minutes = int(value)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return time(hour=hours, minute=minutes)

    @staticmethod
    def time_to_victorn_time(value: time) -> int:
        """Convert time object to minutes since midnight."""
        return value.hour * 60 + value.minute

    def __init__(
        self,
        device: VictronVenusDevice,
        writable_metric: VictronVenusWritableMetric,
        device_info: DeviceInfo,
        simple_naming: bool,
        installation_id: str,
    ) -> None:
        """Initialize the time entity based on details in the metric."""
        self._attr_native_value = VictronTime.victron_time_to_time(
            writable_metric.value
        )
        assert writable_metric.unit_of_measurement == "min"
        super().__init__(
            device, writable_metric, device_info, "time", simple_naming, installation_id
        )

    @callback
    def _on_update_task(self, value: Any) -> None:
        """Convert minutes since midnight to time object and update state."""
        time_value = VictronTime.victron_time_to_time(value)
        if self._attr_native_value == time_value:
            return

        self._attr_native_value = time_value
        self.async_write_ha_state()

    def set_value(self, value: time) -> None:
        """Convert time object to minutes since midnight and set the metric value."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        # Convert time object back to minutes since midnight
        total_minutes = VictronTime.time_to_victorn_time(value)
        _LOGGER.info(
            "Setting time %s (%d minutes) on entity: %s",
            value,
            total_minutes,
            self._attr_unique_id,
        )
        self._metric.set(total_minutes)
