"""Support for Victron Venus sensors.

This module is light-weight and only registers the sensors with Home Assistant. The sensor class is implemented in the victronvenus_sensor module.
"""
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .hub import Hub
from victron_mqtt import MetricKind

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Victron Venus sensors from a config entry."""
    hub: Hub = config_entry.runtime_data
    hub.register_add_entities_callback(async_add_entities, MetricKind.SENSOR)
