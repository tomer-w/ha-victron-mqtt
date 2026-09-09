"""Victron GX firmware update lifecycle handling."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from ._victron_enums import FirmwareUpdateState

if TYPE_CHECKING:
    from collections.abc import Callable

    from .hub import Hub

_AVAILABLE_VERSION_METRIC = "system_0_platform_venus_firmware_available_version"
_INSTALLED_VERSION_METRIC = "system_0_platform_venus_firmware_installed_version"
_PROGRESS_METRIC = "system_0_platform_venus_firmware_progress"
_STATE_METRIC = "system_0_platform_venus_firmware_state"
_CHECK_SERVICE = "platform_service_venus_firmware_check"
_INSTALL_SERVICE = "platform_service_venus_firmware_install"

_ACTIVE_STATES = {
    FirmwareUpdateState.DOWNLOADING_AND_INSTALLING,
    FirmwareUpdateState.REBOOTING,
}


class FirmwareUpdateErrorReason(StrEnum):
    """Reason a GX firmware update failed."""

    UPDATE_FILE_NOT_FOUND = "update_file_not_found"
    ERROR_DURING_UPDATE = "error_during_update"
    ERROR_DURING_CHECK = "error_during_check"
    NO_UPDATE_AVAILABLE = "no_update_available"
    UPDATE_ALREADY_IN_PROGRESS = "update_already_in_progress"
    UPDATE_TIMED_OUT = "update_timed_out"


_ERROR_REASONS = {
    FirmwareUpdateState.UPDATE_FILE_NOT_FOUND: FirmwareUpdateErrorReason.UPDATE_FILE_NOT_FOUND,
    FirmwareUpdateState.ERROR_DURING_UPDATE: FirmwareUpdateErrorReason.ERROR_DURING_UPDATE,
    FirmwareUpdateState.ERROR_DURING_CHECK: FirmwareUpdateErrorReason.ERROR_DURING_CHECK,
}


class FirmwareUpdateError(Exception):
    """Represent a failure while installing GX firmware.

    Attributes
    ----------
    reason: FirmwareUpdateErrorReason
        Machine-readable reason suitable for mapping to an application-specific
        error or translated message.
    """

    def __init__(self, reason: FirmwareUpdateErrorReason) -> None:
        """Initialize the error."""
        super().__init__(reason.value)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class FirmwareUpdateInfo:
    """Current GX firmware update information.

    Attributes
    ----------
    installed_version: str | None
        Venus OS version currently installed, or None when it is unavailable.
    available_version: str | None
        Version offered by the GX online update service, or None when no update
        is offered or the metric is unavailable.
    state: FirmwareUpdateState | None
        Current state reported by the GX firmware service.
    progress: int | None
        Download and installation progress normalized to 0 through 100. The
        value is 100 while rebooting and None when progress is unavailable.
    """

    installed_version: str | None
    available_version: str | None
    state: FirmwareUpdateState | None
    progress: int | None

    @property
    def in_progress(self) -> bool:
        """Return whether the GX device is installing firmware."""
        return self.state in _ACTIVE_STATES

    @property
    def update_available(self) -> bool:
        """Return whether the GX device reports an available firmware build."""
        return self.available_version is not None


def get_firmware_update_info(hub: Hub) -> FirmwareUpdateInfo:
    """Return firmware update information from the latest MQTT values.

    This function does not perform network I/O. Missing, unavailable, or
    unexpectedly typed MQTT metrics are represented by None fields.
    """
    installed_metric = hub.get_metric(_INSTALLED_VERSION_METRIC)
    available_metric = hub.get_metric(_AVAILABLE_VERSION_METRIC)
    state_metric = hub.get_metric(_STATE_METRIC)
    progress_metric = hub.get_metric(_PROGRESS_METRIC)

    installed_version = (
        installed_metric.value
        if installed_metric is not None and installed_metric.available and isinstance(installed_metric.value, str)
        else None
    )
    available_version = (
        available_metric.value
        if available_metric is not None and available_metric.available and isinstance(available_metric.value, str)
        else None
    )
    state = (
        state_metric.value
        if state_metric is not None and state_metric.available and isinstance(state_metric.value, FirmwareUpdateState)
        else None
    )
    progress = (
        min(max(progress_metric.value, 0), 100)
        if progress_metric is not None and progress_metric.available and isinstance(progress_metric.value, int)
        else None
    )
    if state is FirmwareUpdateState.REBOOTING:
        progress = 100

    return FirmwareUpdateInfo(installed_version, available_version, state, progress)


async def _check_firmware_updates(  # pyright: ignore[reportUnusedFunction] - called by Hub
    hub: Hub, poll_interval: float
) -> None:
    """Periodically ask the GX device to check for firmware updates."""
    while True:
        hub.publish(_CHECK_SERVICE, "0", 1)
        await asyncio.sleep(poll_interval)


async def _install_firmware_update(  # pyright: ignore[reportUnusedFunction] - called by Hub
    hub: Hub,
    progress_callback: Callable[[int], None] | None,
    timeout: float,
    poll_interval: float,
) -> None:
    """Install available GX firmware and monitor it until completion."""
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    if poll_interval <= 0:
        raise ValueError("poll_interval must be greater than zero")

    initial_info = get_firmware_update_info(hub)
    target_version = initial_info.available_version
    if target_version is None:
        raise FirmwareUpdateError(FirmwareUpdateErrorReason.NO_UPDATE_AVAILABLE)

    stale_failure_state = initial_info.state if initial_info.state in _ERROR_REASONS else None
    if not initial_info.in_progress:
        hub.publish(_INSTALL_SERVICE, "0", 1)

    last_progress: int | None = None
    try:
        async with asyncio.timeout(timeout):
            while True:
                info = get_firmware_update_info(hub)
                if stale_failure_state is not None:
                    if info.state is stale_failure_state:
                        await asyncio.sleep(poll_interval)
                        continue
                    stale_failure_state = None

                if info.state in _ERROR_REASONS:
                    raise FirmwareUpdateError(_ERROR_REASONS[info.state])

                if info.progress is not None and info.progress != last_progress:
                    if progress_callback is not None:
                        progress_callback(info.progress)
                    last_progress = info.progress

                if info.installed_version == target_version:
                    if last_progress != 100 and progress_callback is not None:
                        progress_callback(100)
                    return

                await asyncio.sleep(poll_interval)
    except TimeoutError as error:
        raise FirmwareUpdateError(FirmwareUpdateErrorReason.UPDATE_TIMED_OUT) from error
