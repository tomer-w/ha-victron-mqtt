"""Firmware updates for Victron GX devices."""

import logging
from datetime import timedelta

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from ._vendor.victron_mqtt import FirmwareUpdateError
from .const import DOMAIN
from .hub import VictronGxConfigEntry

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

_FIRMWARE_UPDATE_URL = "https://www.victronenergy.com/blog/category/firmware-software/"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VictronGxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the GX firmware update entity."""
    async_add_entities([VictronFirmwareUpdateEntity(config_entry)], True)


class VictronFirmwareUpdateEntity(UpdateEntity):
    """Represent the Venus OS firmware installed on a GX device."""

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_has_entity_name = True
    _attr_name = "Venus OS firmware"
    _attr_release_url = _FIRMWARE_UPDATE_URL
    _attr_should_poll = True
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )

    def __init__(self, entry: VictronGxConfigEntry) -> None:
        """Initialize the firmware update entity."""
        self._entry = entry
        self._hub = entry.runtime_data
        info = self._hub.firmware_update_info
        self._installed_version = info.installed_version
        self._online_version = info.available_version
        self._last_logged_versions: tuple[str | None, str | None] | None = None
        self._attr_unique_id = f"{entry.unique_id}_firmware"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.unique_id}_system_0")}
        )

    @property
    def installed_version(self) -> str | None:
        """Return the installed Venus OS version."""
        return self._installed_version

    @property
    def latest_version(self) -> str | None:
        """Return the latest available Venus OS version."""
        return (
            self._online_version
            if self._online_version is not None
            else self._installed_version
        )

    @property
    def available(self) -> bool:
        """Return whether the installed firmware version is available."""
        return self.installed_version is not None

    def version_is_newer(self, latest_version: str, installed_version: str) -> bool:
        """Return whether Victron offers a Venus OS firmware build."""
        return self._online_version is not None

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: object
    ) -> None:
        """Install the latest Venus OS firmware after Home Assistant confirms."""
        latest_version = self._online_version
        if latest_version is None:
            return

        self._attr_in_progress = True
        self.async_write_ha_state()

        @callback
        def _async_update_progress(progress: int) -> None:
            self._attr_update_percentage = progress
            self.async_write_ha_state()

        try:
            try:
                await self._hub.install_firmware_update(_async_update_progress)
            except FirmwareUpdateError as err:
                _LOGGER.debug(
                    "Handled GX firmware installation failure for hub %s: %s",
                    getattr(self._hub, "id", "unknown"),
                    err.reason,
                )
        finally:
            self._attr_in_progress = False
            self._attr_update_percentage = None
            self.async_write_ha_state()

    async def async_update(self) -> None:
        """Refresh the entity from the latest in-memory MQTT values."""
        info = self._hub.firmware_update_info
        versions = (info.installed_version, info.available_version)
        self._attr_in_progress = info.in_progress
        self._attr_update_percentage = info.progress if info.in_progress else None
        if versions == self._last_logged_versions:
            return

        self._installed_version, self._online_version = versions
        self._last_logged_versions = versions
        entity_state = self.state
        update_expected = entity_state == STATE_ON
        _LOGGER.info(
            "GX firmware versions for hub %s: installed=%r, latest=%r, "
            "entity_available=%s, "
            "update_expected=%s, entity_state=%s",
            getattr(self._hub, "id", "unknown"),
            self._installed_version,
            self._online_version,
            self.available,
            update_expected,
            entity_state,
        )
