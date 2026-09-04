"""Firmware updates for Victron GX devices."""

import asyncio
import logging
import re
from collections.abc import Callable

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from ._vendor.victron_mqtt import FirmwareUpdateState
from .const import DOMAIN
from .hub import Hub, VictronGxConfigEntry

_LOGGER = logging.getLogger(__name__)

_FIRMWARE_UPDATE_URL = "https://www.victronenergy.com/blog/category/firmware-software/"
_INSTALL_POLL_INTERVAL = 1
_INSTALL_TIMEOUT = 2 * 60 * 60
_UPDATE_ERROR_REASONS = {
    FirmwareUpdateState.UPDATE_FILE_NOT_FOUND: "update_file_not_found",
    FirmwareUpdateState.ERROR_DURING_UPDATE: "error_during_update",
    FirmwareUpdateState.ERROR_DURING_CHECK: "error_during_check",
}
_VERSION_PATTERN = re.compile(
    r"^v?(?P<core>\d+(?:\.\d+)*)(?:~(?P<build>\d+))?$",
    re.IGNORECASE,
)


class FirmwareUpdateError(Exception):
    """Represent a firmware update failure shown by the GX device."""

    def __init__(self, reason: str) -> None:
        """Initialize a firmware update failure."""
        super().__init__(reason)
        self.reason = reason


def _parse_version(value: str) -> tuple[int, ...] | None:
    """Parse a Venus OS version into comparable numeric components."""
    match = _VERSION_PATTERN.fullmatch(value.strip())
    if match is None:
        return None

    parts = [int(part) for part in match.group("core").split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    if build := match.group("build"):
        parts.append(int(build))
    return tuple(parts)


async def _async_install_firmware_update(
    hub: Hub,
    available_version: str,
    update_progress: Callable[[float], None],
) -> None:
    """Install firmware and report progress until the target version is active."""
    hub_id = getattr(hub, "id", "unknown")
    target_version = _parse_version(available_version)
    if target_version is None:
        _LOGGER.warning(
            "Cannot install GX firmware for hub %s: invalid available version %r",
            hub_id,
            available_version,
        )
        raise FirmwareUpdateError("invalid_available_version")

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
    last_progress: float | None = None
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
                    min(max(progress, 0), 100) / 100 if progress is not None else None
                )
                if state is FirmwareUpdateState.REBOOTING:
                    normalized_progress = 1.0
                if (
                    normalized_progress is not None
                    and normalized_progress != last_progress
                ):
                    update_progress(normalized_progress)
                    _LOGGER.debug(
                        "GX firmware installation progress for hub %s: %.0f%%",
                        hub_id,
                        normalized_progress * 100,
                    )
                    last_progress = normalized_progress

                installed_version, _ = hub.firmware_versions
                parsed_installed = (
                    _parse_version(installed_version)
                    if installed_version is not None
                    else None
                )
                if parsed_installed is not None and parsed_installed >= target_version:
                    if last_progress != 1.0:
                        update_progress(1.0)
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
    async_add_entities([VictronFirmwareUpdateEntity(config_entry)])


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
        self._attr_unique_id = f"{entry.unique_id}_firmware"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.unique_id}_system_0")}
        )

    @property
    def installed_version(self) -> str | None:
        """Return the installed Venus OS version."""
        return self._hub.firmware_versions[0]

    @property
    def latest_version(self) -> str | None:
        """Return the latest available Venus OS version."""
        return self._hub.firmware_versions[1]

    @property
    def available(self) -> bool:
        """Return whether both firmware version metrics are available."""
        installed, latest = self._hub.firmware_versions
        return installed is not None and latest is not None

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: object
    ) -> None:
        """Install the latest Venus OS firmware after Home Assistant confirms."""
        latest_version = self.latest_version
        if latest_version is None:
            return

        self._attr_in_progress = True
        self.async_write_ha_state()

        @callback
        def _async_update_progress(progress: float) -> None:
            self._attr_update_percentage = round(progress * 100)
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
