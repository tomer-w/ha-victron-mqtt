"""Test firmware update repair flows."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from custom_components.victron_mqtt._vendor.victron_mqtt import FirmwareUpdateState
from custom_components.victron_mqtt.hub import Hub
from custom_components.victron_mqtt.repairs import (
    FirmwareUpdateError,
    _async_install_firmware_update,
)


async def test_install_reports_progress_until_target_version() -> None:
    """Test firmware installation reports progress and survives reboot state."""
    hub = MagicMock(spec=Hub)
    type(hub).firmware_update_status = PropertyMock(
        side_effect=[
            (FirmwareUpdateState.DOWNLOADING_AND_INSTALLING, 25),
            (FirmwareUpdateState.REBOOTING, 100),
        ]
    )
    type(hub).firmware_versions = PropertyMock(
        side_effect=[("v3.60", "v3.70"), ("v3.70", "v3.70")]
    )
    progress: list[float] = []

    with patch(
        "custom_components.victron_mqtt.repairs.asyncio.sleep",
        new=AsyncMock(),
    ):
        await _async_install_firmware_update(hub, "v3.70", progress.append)

    hub.install_firmware_update.assert_called_once_with()
    assert progress == [0.25, 1.0]


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
    """Test GX firmware failures become specific Repair abort reasons."""
    hub = MagicMock(spec=Hub)
    type(hub).firmware_update_status = PropertyMock(return_value=(state, None))

    with pytest.raises(FirmwareUpdateError, match=reason) as err:
        await _async_install_firmware_update(hub, "v3.70", MagicMock())

    assert err.value.reason == reason