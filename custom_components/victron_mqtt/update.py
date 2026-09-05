"""Firmware updates for Victron GX devices."""

import asyncio
import logging
from collections.abc import Callable
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

from ._vendor.victron_mqtt import FirmwareUpdateState
from .const import DOMAIN
from .hub import Hub, VictronGxConfigEntry

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

_FIRMWARE_UPDATE_URL = "https://www.victronenergy.com/blog/category/firmware-software/"
_INSTALL_POLL_INTERVAL = 1
_INSTALL_TIMEOUT = 2 * 60 * 60
_UPDATE_ERROR_REASONS = {
    FirmwareUpdateState.UPDATE_FILE_NOT_FOUND: "update_file_not_found",
    FirmwareUpdateState.ERROR_DURING_UPDATE: "error_during_update",
    FirmwareUpdateState.ERROR_DURING_CHECK: "error_during_check",
}


class FirmwareUpdateError(Exception):
    """Represent a firmware update failure shown by the GX device."""

    def __init__(self, reason: str) -> None:
        """Initialize a firmware update failure."""
        super().__init__(reason)
        self.reason = reason


async def _async_install_firmware_update(
    hub: Hub,
    available_version: str,
    update_progress: Callable[[int], None],
) -> None:
    """Install firmware and report progress until the target version is active."""
    hub_id = getattr(hub, "id", "unknown")
    _LOGGER.info(
        "Starting GX firmware installation for hub %s, target version %s",
        hub_id,
        available_version,
    )
    initial_state, _ = hub.firmware_update_status
    stale_failure_state = (
        initial_state if initial_state in _UPDATE_ERROR_REASONS else None
    )
    if stale_failure_state is not None:
        _LOGGER.debug(
            "Ignoring pre-existing GX firmware failure for hub %s until state "
            "changes: state=%s",
            hub_id,
            initial_state,
        )

    hub.install_firmware_update()
    last_progress: int | None = None
    last_state: FirmwareUpdateState | None = None

    try:
        async with asyncio.timeout(_INSTALL_TIMEOUT):
            while True:
                state, progress = hub.firmware_update_status
                if state is not last_state:
                    _LOGGER.debug(
                        "GX firmware installation state changed for hub %s: %s",
                        hub_id,
                        state,
                    )
                    last_state = state
                if stale_failure_state is not None:
                    if state is stale_failure_state:
                        _LOGGER.debug(
                            "GX firmware state %s still did not change for hub %s",
                            state,
                            hub_id,
                        )
                        await asyncio.sleep(_INSTALL_POLL_INTERVAL)
                        continue
                    _LOGGER.debug(
                        "GX firmware status changed for hub %s; subsequent "
                        "failures belong to the new installation attempt",
                        hub_id,
                    )
                    stale_failure_state = None
                if state in _UPDATE_ERROR_REASONS:
                    _LOGGER.warning(
                        "GX firmware installation failed for hub %s: state=%s",
                        hub_id,
                        state,
                    )
                    raise FirmwareUpdateError(_UPDATE_ERROR_REASONS[state])

                normalized_progress = (
                    min(max(progress, 0), 100) if progress is not None else None
                )
                if state is FirmwareUpdateState.REBOOTING:
                    normalized_progress = 100
                if (
                    normalized_progress is not None
                    and normalized_progress != last_progress
                ):
                    update_progress(normalized_progress)
                    _LOGGER.debug(
                        "GX firmware installation progress for hub %s: %.0f%%",
                        hub_id,
                        normalized_progress,
                    )
                    last_progress = normalized_progress

                installed_version, _ = hub.firmware_versions
                if installed_version == available_version:
                    if last_progress != 100:
                        update_progress(100)
                    _LOGGER.info(
                        "GX firmware installation completed for hub %s: "
                        "installed=%s, target=%s",
                        hub_id,
                        installed_version,
                        available_version,
                    )
                    return

                await asyncio.sleep(_INSTALL_POLL_INTERVAL)
    except TimeoutError as exc:
        _LOGGER.warning(
            "GX firmware installation timed out for hub %s after %s seconds",
            hub_id,
            _INSTALL_TIMEOUT,
        )
        raise FirmwareUpdateError("update_timed_out") from exc


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
        self._firmware_versions = self._hub.firmware_versions
        self._last_logged_versions: tuple[str | None, str | None] | None = None
        self._attr_unique_id = f"{entry.unique_id}_firmware"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.unique_id}_system_0")}
        )

    @property
    def installed_version(self) -> str | None:
        """Return the installed Venus OS version."""
        return self._firmware_versions[0]

    @property
    def latest_version(self) -> str | None:
        """Return the latest available Venus OS version."""
        installed, latest = self._firmware_versions
        return latest if latest is not None else installed

    @property
    def available(self) -> bool:
        """Return whether the installed firmware version is available."""
        return self.installed_version is not None

    def version_is_newer(self, latest_version: str, installed_version: str) -> bool:
        """Return whether Victron offers a different Venus OS version."""
        return latest_version != installed_version

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: object
    ) -> None:
        """Install the latest Venus OS firmware after Home Assistant confirms."""
        latest_version = self._firmware_versions[1]
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
                await _async_install_firmware_update(
                    self._hub, latest_version, _async_update_progress
                )
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
        versions = self._hub.firmware_versions
        if versions == self._last_logged_versions:
            return

        self._firmware_versions = versions
        self._last_logged_versions = versions
        installed, latest = versions
        entity_state = self.state
        update_expected = entity_state == STATE_ON
        _LOGGER.info(
            "GX firmware versions for hub %s: installed=%r, latest=%r, "
            "entity_available=%s, "
            "update_expected=%s, entity_state=%s",
            getattr(self._hub, "id", "unknown"),
            installed,
            latest,
            self.available,
            update_expected,
            entity_state,
        )
