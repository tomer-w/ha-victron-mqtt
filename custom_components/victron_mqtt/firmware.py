"""Firmware update repair monitoring for Victron GX devices."""

import logging
import re
from datetime import timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_call_later, async_track_time_interval

from .const import CONF_MODEL, DOMAIN
from .hub import VictronGxConfigEntry

_LOGGER = logging.getLogger(__name__)

_CHECK_INTERVAL = timedelta(days=7)
_CHECK_RESULT_DELAY = 30
_FIRMWARE_UPDATE_URL = "https://www.victronenergy.com/support-and-download/software"
_VERSION_PATTERN = re.compile(
    r"^v?(?P<core>\d+(?:\.\d+)*)(?:[.-]?rc\d+)?$", re.IGNORECASE
)


def _parse_version(value: str) -> tuple[int, ...] | None:
    """Parse a Venus OS version into comparable numeric components."""
    normalized = value.strip().split("~", 1)[0]
    match = _VERSION_PATTERN.fullmatch(normalized)
    if match is None:
        return None

    parts = [int(part) for part in match.group("core").split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def firmware_issue_id(entry: VictronGxConfigEntry) -> str:
    """Return the repair issue ID for a config entry."""
    return f"firmware_update_available_{entry.entry_id}"


@callback
def async_check_firmware_update(
    hass: HomeAssistant, entry: VictronGxConfigEntry
) -> None:
    """Create or clear the firmware update repair issue."""
    installed, available = entry.runtime_data.firmware_versions
    if installed is None or available is None:
        return

    installed_version = _parse_version(installed)
    available_version = _parse_version(available)
    if installed_version is None or available_version is None:
        _LOGGER.warning(
            "Could not compare GX firmware versions: installed=%r, available=%r",
            installed,
            available,
        )
        return

    issue_id = firmware_issue_id(entry)
    if installed_version < available_version:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            data={
                "config_entry_id": entry.entry_id,
                "installed_version": installed,
                "available_version": available,
            },
            is_fixable=True,
            is_persistent=False,
            learn_more_url=_FIRMWARE_UPDATE_URL,
            severity=ir.IssueSeverity.WARNING,
            translation_key="firmware_update_available",
            translation_placeholders={
                "model": entry.data.get(CONF_MODEL, "GX device"),
                "installed_version": installed,
                "available_version": available,
            },
        )
        return

    ir.async_delete_issue(hass, DOMAIN, issue_id)


@callback
def _cancel_pending_refresh(entry: VictronGxConfigEntry) -> None:
    """Cancel any pending delayed firmware refresh for this entry."""
    refresh_unsub = getattr(entry, "_firmware_refresh_unsub", None)
    if refresh_unsub is not None:
        refresh_unsub()
        delattr(entry, "_firmware_refresh_unsub")


@callback
def _schedule_firmware_refresh(
    hass: HomeAssistant, entry: VictronGxConfigEntry
) -> None:
    """Schedule a delayed firmware availability check and cancel stale ones."""
    _cancel_pending_refresh(entry)
    entry._firmware_refresh_unsub = async_call_later(
        hass,
        _CHECK_RESULT_DELAY,
        lambda _now: async_check_firmware_update(hass, entry),
    )


@callback
def _async_refresh_firmware_update(
    hass: HomeAssistant, entry: VictronGxConfigEntry
) -> None:
    """Ask the GX device to refresh online firmware availability."""
    entry.runtime_data.check_firmware_update()
    _schedule_firmware_refresh(hass, entry)


def async_setup_firmware_monitor(
    hass: HomeAssistant, entry: VictronGxConfigEntry
) -> None:
    """Set up immediate comparison and weekly online firmware checks."""
    previous_unsub = getattr(entry, "_firmware_monitor_unsub", None)
    if previous_unsub is not None:
        previous_unsub()

    async_check_firmware_update(hass, entry)
    _async_refresh_firmware_update(hass, entry)

    interval_unsub = async_track_time_interval(
        hass,
        lambda _now: _async_refresh_firmware_update(hass, entry),
        _CHECK_INTERVAL,
    )

    entry._firmware_monitor_unsub = lambda: (
        _cancel_pending_refresh(entry),
        interval_unsub(),
    )


@callback
def async_delete_firmware_issue(
    hass: HomeAssistant, entry: VictronGxConfigEntry
) -> None:
    """Delete a config entry's firmware update issue."""
    ir.async_delete_issue(hass, DOMAIN, firmware_issue_id(entry))
