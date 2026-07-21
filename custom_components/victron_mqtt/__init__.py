"""The victron_mqtt integration."""

import logging

from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv


from .const import (
    ATTR_DEVICE_ID,
    ATTR_METRIC_ID,
    ATTR_VALUE,
    CONF_SIMPLE_NAMING,
    CONF_UPDATE_FREQUENCY_MODE,
    CONF_UPDATE_FREQUENCY_SECONDS,
    DEFAULT_UPDATE_FREQUENCY_SECONDS,
    DOMAIN,
    SERVICE_PUBLISH,
    UPDATE_FREQUENCY_MODE_AUTO,
    UPDATE_FREQUENCY_MODE_MANUAL,
)
from .hub import Hub, VictronGxConfigEntry
from ._vendor import VICTRON_MQTT_VERSION

_LOGGER = logging.getLogger(__name__)
_VICTRON_MQTT_LOGGER = logging.getLogger("victron_mqtt")

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TIME,
]

async def async_setup_services(hass: HomeAssistant, entry: VictronGxConfigEntry) -> None:
    """Set up services for the Victron MQTT integration."""

    # Only register services once
    if hass.services.has_service(DOMAIN, SERVICE_PUBLISH):
        return

    async def handle_publish(call: ServiceCall) -> None:
        """Handle the set_value service call."""
        metric_id = call.data.get(ATTR_METRIC_ID)
        device_id = call.data.get(ATTR_DEVICE_ID)
        value = call.data.get(ATTR_VALUE)

        if not metric_id:
            raise HomeAssistantError("metric_id is required")
        if not device_id:
            raise HomeAssistantError("device_id is required")

        # Find the hub instance
        hub: Hub = entry.runtime_data
        if hub is None:
            raise HomeAssistantError("No Victron MQTT hub found")

        hub.publish(metric_id, device_id, value)

    # Register the service
    hass.services.async_register(
        DOMAIN,
        SERVICE_PUBLISH,
        handle_publish,
    )

    _LOGGER.info("Victron MQTT services registered")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration."""
    version = getattr(hass.data.get("integrations", {}).get(DOMAIN), "version", "unknown")
    _LOGGER.info(
        "Setting up victron_mqtt integration. Version: %s. victron_mqtt package version: %s",
        version,
        VICTRON_MQTT_VERSION,
    )

    return True


def _sync_library_logging() -> None:
    """Sync the log level of the library to match integration logging."""
    lib_level = _LOGGER.getEffectiveLevel()
    _VICTRON_MQTT_LOGGER.setLevel(lib_level)
    _VICTRON_MQTT_LOGGER.propagate = True  # Let it go through HA logging


async def async_migrate_entry(hass: HomeAssistant, config_entry: VictronGxConfigEntry) -> bool:
    """Migrate old entry to new version."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new_data = {**config_entry.data}
        if CONF_SIMPLE_NAMING not in new_data:
            new_data[CONF_SIMPLE_NAMING] = False
        hass.config_entries.async_update_entry(config_entry, data=new_data, version=2)
        _LOGGER.info("Migration to version 2 successful")

    if config_entry.version == 2:
        new_data = {**config_entry.data}
        # The old default update frequency was 30 seconds. Users who kept that
        # default (or never set one) are moved to the new "auto" mode. Any other
        # explicit interval is preserved as a manual setting.
        frequency = new_data.get(CONF_UPDATE_FREQUENCY_SECONDS)
        if frequency is None or frequency == DEFAULT_UPDATE_FREQUENCY_SECONDS:
            new_data[CONF_UPDATE_FREQUENCY_MODE] = UPDATE_FREQUENCY_MODE_AUTO
        else:
            new_data[CONF_UPDATE_FREQUENCY_MODE] = UPDATE_FREQUENCY_MODE_MANUAL
        hass.config_entries.async_update_entry(config_entry, data=new_data, version=3)
        _LOGGER.info("Migration to version 3 successful")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: VictronGxConfigEntry) -> bool:
    """Set up victronvenus from a config entry."""
    _sync_library_logging()
    _LOGGER.debug("async_setup_entry called for entry: %s", entry.entry_id)

    hub = Hub(hass, entry)
    entry.runtime_data = hub

    # All platforms should be set up before starting the hub
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await hub.start()

    # Register the update listener
    async def _update_listener(hass: HomeAssistant, entry: VictronGxConfigEntry) -> None:
        _LOGGER.info("Options have been updated - applying changes")
        # Reload the integration to apply changes
        await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(_update_listener))

    async def _async_stop(_: Event) -> None:
        await hub.stop()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )

    # Register services
    await async_setup_services(hass, entry)
    _LOGGER.debug("sync_setup_entry completed for entry: %s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VictronGxConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry called for entry: %s", entry.entry_id)
    hub: Hub = entry.runtime_data
    assert isinstance(hub, Hub)
    await hub.stop()

    # Unregister services if this is the last entry
    if len(hass.config_entries.async_entries(DOMAIN)) == 1:
        hass.services.async_remove(DOMAIN, SERVICE_PUBLISH)
        _LOGGER.info("Victron MQTT services unregistered")

    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hub.unregister_all_new_metric_callbacks()

    return True

async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: VictronGxConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    """Always allow removing a device from the config entry. Worse case it will be re-created on the next restart if it still exists in the hub."""
    return True
