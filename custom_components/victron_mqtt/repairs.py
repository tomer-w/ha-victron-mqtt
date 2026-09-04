"""Repair flows for Victron MQTT."""

import asyncio
from collections.abc import Callable

import voluptuous as vol

from homeassistant import data_entry_flow
from homeassistant.components.repairs import RepairsFlow
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._vendor.victron_mqtt import FirmwareUpdateState
from .firmware import _parse_version
from .hub import Hub, VictronGxConfigEntry

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
    update_progress: Callable[[float], None],
) -> None:
    """Install firmware and report progress until the target version is active."""
    target_version = _parse_version(available_version)
    if target_version is None:
        raise FirmwareUpdateError("invalid_available_version")

    hub.install_firmware_update()
    last_progress: float | None = None

    try:
        async with asyncio.timeout(_INSTALL_TIMEOUT):
            while True:
                state, progress = hub.firmware_update_status
                if state in _UPDATE_ERROR_REASONS:
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
                    last_progress = normalized_progress

                installed_version, _ = hub.firmware_versions
                parsed_installed = (
                    _parse_version(installed_version)
                    if installed_version is not None
                    else None
                )
                if (
                    parsed_installed is not None
                    and parsed_installed >= target_version
                ):
                    if last_progress != 1.0:
                        update_progress(1.0)
                    return

                await asyncio.sleep(_INSTALL_POLL_INTERVAL)
    except TimeoutError as exc:
        raise FirmwareUpdateError("update_timed_out") from exc


class FirmwareUpdateRepairFlow(RepairsFlow):
    """Guide the user through installing a Venus OS firmware update."""

    def __init__(
        self,
        entry: VictronGxConfigEntry | None,
        available_version: str | None,
    ) -> None:
        """Initialize the repair flow."""
        self._entry = entry
        self._available_version = available_version
        self._install_task: asyncio.Task[None] | None = None

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Confirm firmware installation."""
        if self._entry is None or self._entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")
        if self._available_version is None:
            return self.async_abort(reason="invalid_available_version")
        if user_input is not None:
            return await self.async_step_install()

        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))

    async def async_step_install(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Install firmware while reporting progress."""
        assert self._entry is not None
        assert self._available_version is not None
        if self._install_task is None:
            self._install_task = self.hass.async_create_task(
                _async_install_firmware_update(
                    self._entry.runtime_data,
                    self._available_version,
                    self.async_update_progress,
                ),
                "Install Victron GX firmware update",
            )

        if not self._install_task.done():
            return self.async_show_progress(
                step_id="install",
                progress_action="installing_firmware",
                progress_task=self._install_task,
            )

        try:
            self._install_task.result()
        except FirmwareUpdateError as err:
            return self.async_abort(reason=err.reason)

        return self.async_show_progress_done(next_step_id="finish")

    async def async_step_finish(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Finish a successful firmware update repair."""
        return self.async_create_entry(title="", data={})


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create the firmware update repair flow."""
    config_entry_id = data.get("config_entry_id") if data is not None else None
    available_version = data.get("available_version") if data is not None else None
    entry = (
        hass.config_entries.async_get_entry(config_entry_id)
        if isinstance(config_entry_id, str)
        else None
    )
    typed_entry = (
        entry
        if entry is not None
        and entry.state is ConfigEntryState.LOADED
        and isinstance(entry.runtime_data, Hub)
        else None
    )
    return FirmwareUpdateRepairFlow(
        typed_entry,
        available_version if isinstance(available_version, str) else None,
    )