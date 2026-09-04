"""Test the Victron firmware update entity."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from homeassistant.components.update import UpdateDeviceClass, UpdateEntityFeature
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.victron_mqtt._vendor.victron_mqtt import FirmwareUpdateState
from custom_components.victron_mqtt.const import DOMAIN
from custom_components.victron_mqtt.hub import Hub
from custom_components.victron_mqtt.update import (
    FirmwareUpdateError,
    VictronFirmwareUpdateEntity,
    _async_install_firmware_update,
    _parse_version,
)


def _create_entity(
    installed: str | None = "v3.60", latest: str | None = "v3.70"
) -> tuple[VictronFirmwareUpdateEntity, MagicMock]:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="123")
    hub = MagicMock()
    hub.firmware_versions = (installed, latest)
    entry.runtime_data = hub
    return VictronFirmwareUpdateEntity(entry), hub


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("v3.70", (3, 70)),
        ("v3.70~15", (3, 70, 15)),
        ("v2.62.1", (2, 62, 1)),
        ("V3.70.0", (3, 70)),
        ("v3.70-rc1", None),
        ("not-a-version", None),
    ],
)
def test_parse_version(value: str, expected: tuple[int, ...] | None) -> None:
    """Test Venus OS version normalization."""
    assert _parse_version(value) == expected


def test_firmware_update_details() -> None:
    """Test update details use the firmware metrics and Victron release link."""
    entity, _ = _create_entity()

    assert entity.device_class is UpdateDeviceClass.FIRMWARE
    assert entity.installed_version == "v3.60"
    assert entity.latest_version == "v3.70"
    assert entity.release_url == (
        "https://www.victronenergy.com/blog/category/firmware-software/"
    )
    assert entity.supported_features == (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )
    assert entity.available


async def test_install_only_starts_from_install_action() -> None:
    """Test entity creation does not install and the install action does."""
    entity, hub = _create_entity()
    entity.hass = MagicMock()

    hub.install_firmware_update.assert_not_called()
    with (
        patch.object(entity, "async_write_ha_state"),
        patch(
            "custom_components.victron_mqtt.update._async_install_firmware_update",
            new=AsyncMock(),
        ) as install,
    ):
        await entity.async_install(None, False)

    install.assert_awaited_once()
    assert install.await_args is not None
    assert install.await_args.args[:2] == (hub, "v3.70")
    assert entity.in_progress is False


async def test_expected_install_failure_does_not_escape_entity_service() -> None:
    """Test a GX update failure does not become a WebSocket API exception."""
    entity, _ = _create_entity()
    entity.hass = MagicMock()

    with (
        patch.object(entity, "async_write_ha_state"),
        patch(
            "custom_components.victron_mqtt.update._async_install_firmware_update",
            new=AsyncMock(side_effect=FirmwareUpdateError("error_during_update")),
        ),
    ):
        await entity.async_install(None, False)

    assert entity.in_progress is False
    assert entity.update_percentage is None


async def test_install_reports_progress_until_target_version() -> None:
    """Test firmware installation reports progress and survives reboot state."""
    hub = MagicMock(spec=Hub)
    type(hub).firmware_update_status = PropertyMock(
        side_effect=[
            (FirmwareUpdateState.IDLE, None),
            (FirmwareUpdateState.DOWNLOADING_AND_INSTALLING, 25),
            (FirmwareUpdateState.REBOOTING, 100),
        ]
    )
    type(hub).firmware_versions = PropertyMock(
        side_effect=[("v3.60", "v3.70"), ("v3.70", "v3.70")]
    )
    progress: list[float] = []

    with patch(
        "custom_components.victron_mqtt.update.asyncio.sleep", new=AsyncMock()
    ):
        await _async_install_firmware_update(hub, "v3.70", progress.append)

    hub.install_firmware_update.assert_called_once_with()
    assert progress == [0.25, 1.0]


async def test_install_waits_for_target_firmware_build() -> None:
    """Test an older build of the same Venus OS version does not complete."""
    hub = MagicMock(spec=Hub)
    type(hub).firmware_update_status = PropertyMock(
        side_effect=[
            (FirmwareUpdateState.IDLE, None),
            (FirmwareUpdateState.DOWNLOADING_AND_INSTALLING, 25),
            (FirmwareUpdateState.REBOOTING, 100),
        ]
    )
    versions = PropertyMock(
        side_effect=[
            ("v3.80~36", "v3.80~45"),
            ("v3.80~45", "v3.80~45"),
        ]
    )
    type(hub).firmware_versions = versions

    with patch(
        "custom_components.victron_mqtt.update.asyncio.sleep", new=AsyncMock()
    ):
        await _async_install_firmware_update(hub, "v3.80~45", MagicMock())

    assert versions.call_count == 2


async def test_install_ignores_stale_failure_until_status_changes() -> None:
    """Test a previous attempt's failure is not assigned to the new attempt."""
    hub = MagicMock(spec=Hub)
    update_status = PropertyMock(
        side_effect=[
            (FirmwareUpdateState.ERROR_DURING_UPDATE, None),
            (FirmwareUpdateState.ERROR_DURING_UPDATE, 10),
            (FirmwareUpdateState.DOWNLOADING_AND_INSTALLING, 10),
            (FirmwareUpdateState.ERROR_DURING_UPDATE, 10),
        ]
    )
    type(hub).firmware_update_status = update_status
    type(hub).firmware_versions = PropertyMock(return_value=("v3.60", "v3.70"))

    with (
        patch("custom_components.victron_mqtt.update.asyncio.sleep", new=AsyncMock()),
        pytest.raises(FirmwareUpdateError, match="error_during_update"),
    ):
        await _async_install_firmware_update(hub, "v3.70", MagicMock())

    assert update_status.call_count == 4


@pytest.mark.parametrize(
    ("state", "reason"),
    [
        (FirmwareUpdateState.UPDATE_FILE_NOT_FOUND, "update_file_not_found"),
        (FirmwareUpdateState.ERROR_DURING_UPDATE, "error_during_update"),
        (FirmwareUpdateState.ERROR_DURING_CHECK, "error_during_check"),
    ],
)
async def test_install_reports_device_error(
    state: FirmwareUpdateState, reason: str
) -> None:
    """Test GX firmware failures report specific reasons."""
    hub = MagicMock(spec=Hub)
    type(hub).firmware_update_status = PropertyMock(
        side_effect=[
            (FirmwareUpdateState.IDLE, None),
            (state, None),
        ]
    )
    type(hub).firmware_versions = PropertyMock(return_value=("v3.60", "v3.70"))

    with (
        patch("custom_components.victron_mqtt.update.asyncio.sleep", new=AsyncMock()),
        pytest.raises(FirmwareUpdateError, match=reason) as err,
    ):
        await _async_install_firmware_update(hub, "v3.70", MagicMock())

    assert err.value.reason == reason
