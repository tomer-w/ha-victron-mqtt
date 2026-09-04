"""Test firmware update repair monitoring."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.victron_mqtt.const import CONF_MODEL, DOMAIN
from custom_components.victron_mqtt.firmware import (
    _async_refresh_firmware_update,
    _parse_version,
    async_check_firmware_update,
    async_setup_firmware_monitor,
    firmware_issue_id,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("v3.70", (3, 70)),
        ("v3.70~15", (3, 70)),
        ("3.70.0", (3, 70)),
        ("V3.70.0-rc1", (3, 70)),
        ("not-a-version", None),
    ],
)
def test_parse_version(value: str, expected: tuple[int, ...] | None) -> None:
    """Test Venus OS version normalization."""
    assert _parse_version(value) == expected


def _create_entry(installed: str | None, available: str | None) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_MODEL: "Cerbo GX"},
    )
    hub = MagicMock()
    hub.firmware_versions = (installed, available)
    entry.runtime_data = hub
    return entry


async def test_outdated_firmware_creates_repair_issue(
    hass: HomeAssistant,
) -> None:
    """Test older installed firmware creates a warning repair issue."""
    entry = _create_entry("v3.60", "v3.70")

    async_check_firmware_update(hass, entry)

    issue = ir.async_get(hass).async_get_issue(DOMAIN, firmware_issue_id(entry))
    assert issue is not None
    assert issue.severity is ir.IssueSeverity.WARNING
    assert issue.is_fixable is True
    assert issue.translation_key == "firmware_update_available"
    assert issue.translation_placeholders == {
        "model": "Cerbo GX",
        "installed_version": "v3.60",
        "available_version": "v3.70",
    }


@pytest.mark.parametrize(
    ("installed", "available"),
    [
        ("v3.70", "v3.70"),
        ("v3.71", "v3.70"),
        ("v3.70~15", "v3.70"),
    ],
)
async def test_current_firmware_clears_repair_issue(
    hass: HomeAssistant, installed: str, available: str
) -> None:
    """Test current firmware clears an existing repair issue."""
    entry = _create_entry("v3.60", "v3.70")
    async_check_firmware_update(hass, entry)
    assert (
        ir.async_get(hass).async_get_issue(DOMAIN, firmware_issue_id(entry)) is not None
    )

    entry.runtime_data.firmware_versions = (installed, available)
    async_check_firmware_update(hass, entry)

    assert ir.async_get(hass).async_get_issue(DOMAIN, firmware_issue_id(entry)) is None


async def test_refresh_requests_online_check_before_updating_issue(
    hass: HomeAssistant,
) -> None:
    """Test periodic refresh asks the GX device to check Victron's cloud."""
    entry = _create_entry("v3.60", "v3.70")

    with patch(
        "custom_components.victron_mqtt.firmware.async_call_later"
    ) as call_later:
        _async_refresh_firmware_update(hass, entry)

    entry.runtime_data.check_firmware_update.assert_called_once_with()
    callback = call_later.call_args.args[2]
    callback(None)
    assert ir.async_get(hass).async_get_issue(DOMAIN, firmware_issue_id(entry))


async def test_monitor_checks_online_firmware_weekly(hass: HomeAssistant) -> None:
    """Test the monitor performs an initial check and schedules weekly checks."""
    entry = _create_entry("v3.70", "v3.70")

    with (
        patch("custom_components.victron_mqtt.firmware.async_call_later"),
        patch(
            "custom_components.victron_mqtt.firmware.async_track_time_interval"
        ) as track_interval,
    ):
        async_setup_firmware_monitor(hass, entry)

    entry.runtime_data.check_firmware_update.assert_called_once_with()
    assert track_interval.call_args.args[2] == timedelta(days=7)


async def test_monitor_replaces_existing_timers(hass: HomeAssistant) -> None:
    """Test re-initializing the monitor cancels stale scheduled callbacks."""
    entry = _create_entry("v3.70", "v3.70")
    cancel_refresh_1 = MagicMock()
    cancel_refresh_2 = MagicMock()
    cancel_interval_1 = MagicMock()
    cancel_interval_2 = MagicMock()

    with (
        patch(
            "custom_components.victron_mqtt.firmware.async_call_later",
            side_effect=[cancel_refresh_1, cancel_refresh_2],
        ),
        patch(
            "custom_components.victron_mqtt.firmware.async_track_time_interval",
            side_effect=[cancel_interval_1, cancel_interval_2],
        ),
    ):
        async_setup_firmware_monitor(hass, entry)
        async_setup_firmware_monitor(hass, entry)

    cancel_refresh_1.assert_called_once_with()
    cancel_interval_1.assert_called_once_with()


@pytest.mark.parametrize(
    ("installed", "available"),
    [(None, "v3.70"), ("v3.60", None), ("invalid", "v3.70")],
)
async def test_unknown_firmware_does_not_create_issue(
    hass: HomeAssistant, installed: str | None, available: str | None
) -> None:
    """Test missing or malformed firmware versions do not create an issue."""
    entry = _create_entry(installed, available)

    async_check_firmware_update(hass, entry)

    assert ir.async_get(hass).async_get_issue(DOMAIN, firmware_issue_id(entry)) is None
