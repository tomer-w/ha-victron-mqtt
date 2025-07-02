"""The victron_mqtt integration."""

from __future__ import annotations

import logging
import importlib.metadata
import asyncio

from victron_mqtt import (
    CannotConnectError,
    Hub as VictronVenusHub
)

from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_INSTALLATION_ID, CONF_MODEL, CONF_SERIAL, DOMAIN


_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]

__all__ = ["DOMAIN"]

asyncio_event_loop: asyncio.AbstractEventLoop | None = None

def get_event_loop() -> asyncio.AbstractEventLoop:
    """Get the current asyncio event loop."""
    global asyncio_event_loop
    assert asyncio_event_loop is not None
    return asyncio_event_loop

async def get_package_version(package_name):
    loop = get_event_loop()
    version = await loop.run_in_executor(None, importlib.metadata.version, package_name)
    return version

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration."""
    global asyncio_event_loop
    asyncio_event_loop = asyncio.get_event_loop()
    version = getattr(hass.data["integrations"][DOMAIN], "version", 0)
    victron_mqtt_version = await get_package_version("victron_mqtt")
    _LOGGER.info("Setting up victron_mqtt integration. Version: %s. victron_mqtt package version: %s", version, victron_mqtt_version)

    return True

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up victronvenus from a config entry."""

    config = entry.data
    hub = VictronVenusHub(
        config.get(CONF_HOST),
        config.get(CONF_PORT, 1883),
        config.get(CONF_USERNAME),
        config.get(CONF_PASSWORD),
        config.get(CONF_SSL, False),
        config.get(CONF_INSTALLATION_ID),
        config.get(CONF_MODEL),
        config.get(CONF_SERIAL),
    )

    try:
        await hub.connect()
    except CannotConnectError as connect_error:
        _LOGGER.error("Cannot connect to the hub")
        raise ConfigEntryNotReady("Device is offline") from connect_error

    entry.runtime_data = hub
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload a config entry."""
    hub = entry.runtime_data
    if hub is not None:
        if isinstance(hub, VictronVenusHub):
            await hub.disconnect()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
