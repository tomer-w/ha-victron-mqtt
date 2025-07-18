"""Support for Victron Venus binary sensors."""

from victron_mqtt import MetricKind

from .hub import Hub
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Victron Venus binary sensors from a config entry."""

    hub: Hub = config_entry.runtime_data
    hub.add_entities(async_add_entities, MetricKind.BINARY_SENSOR)

