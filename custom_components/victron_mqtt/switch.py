"""Support for Victron Venus switches with 4 states."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .hub import Hub
from victron_mqtt import MetricKind

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Victron Venus switches from a config entry."""
    
    hub: Hub = config_entry.runtime_data
    hub.add_entities(async_add_entities, MetricKind.SWITCH)
