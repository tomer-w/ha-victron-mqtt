"""The victron_mqtt integration."""

from __future__ import annotations

import logging
import importlib.metadata

from .hub import Hub
from .common import get_event_loop, init_event_loop
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]

__all__ = ["DOMAIN"]

async def get_package_version(package_name):
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

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up victronvenus from a config entry."""

    hub = Hub(hass, entry)
    await hub.start()
    entry.runtime_data = hub
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload a config entry."""
    hub: Hub = entry.runtime_data
    if hub is not None:
        await hub.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
