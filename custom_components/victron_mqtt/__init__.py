"""The victron_mqtt integration."""

from __future__ import annotations

import logging
import importlib.metadata

from .hub import Hub
from .common import get_event_loop, init_event_loop
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)
_VICTRON_MQTT_LOGGER = logging.getLogger("victron_mqtt")

# Config schema - this integration is config entry only
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]

__all__ = ["DOMAIN"]

async def _update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    _LOGGER.info("Options for victron_mqtt have been updated - applying changes")
    # Reload the integration to apply changes
    await hass.config_entries.async_reload(entry.entry_id)


async def get_package_version(package_name) -> str:
    asyncio_event_loop = get_event_loop()
    version = await asyncio_event_loop.run_in_executor(None, importlib.metadata.version, package_name)
    return version

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration."""
    init_event_loop()
    version = getattr(hass.data["integrations"][DOMAIN], "version", 0)
    victron_mqtt_version = await get_package_version("victron_mqtt")
    _LOGGER.info("Setting up victron_mqtt integration. Version: %s. victron_mqtt package version: %s", version, victron_mqtt_version)

    return True

def _sync_library_logging():
    """Sync the log level of the library to match integration logging."""
    lib_level = _LOGGER.getEffectiveLevel()
    _VICTRON_MQTT_LOGGER.setLevel(lib_level)
    _VICTRON_MQTT_LOGGER.propagate = True  # Let it go through HA logging

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up victronvenus from a config entry."""
    _sync_library_logging()
    _LOGGER.info("async_setup_entry called for entry: %s", entry.entry_id)

    hub = Hub(hass, entry)
    entry.runtime_data = hub

    # Register the update listener
    entry.async_on_unload(entry.add_update_listener(_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # All platforms should be set up before starting the hub
    await hub.start()
    _LOGGER.info("async_setup_entry completed for entry: %s", entry.entry_id)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload a config entry."""
    _LOGGER.info("async_unload_entry called for entry: %s", entry.entry_id)
    hub: Hub = entry.runtime_data
    if hub is not None:
        await hub.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
