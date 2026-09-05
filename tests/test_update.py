"""Test the Victron firmware update entity."""

import logging
from collections.abc import Callable
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from homeassistant.components.update import UpdateDeviceClass, UpdateEntityFeature
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.victron_mqtt._vendor.victron_mqtt import FirmwareUpdateState
from custom_components.victron_mqtt.const import DOMAIN
from custom_components.victron_mqtt.hub import Hub
from custom_components.victron_mqtt.update import (
    SCAN_INTERVAL,
    FirmwareUpdateError,
    VictronFirmwareUpdateEntity,
    _async_install_firmware_update,
    async_setup_entry,
)


def _create_entity(
    installed: str | None = "v3.60", latest: str | None = "v3.70"
) -> tuple[VictronFirmwareUpdateEntity, MagicMock]:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="123")
    hub = MagicMock()
    hub.firmware_versions = (installed, latest)
    entry.runtime_data = hub
    return VictronFirmwareUpdateEntity(entry), hub


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
    assert timedelta(seconds=30) == SCAN_INTERVAL


async def test_setup_refreshes_firmware_versions_before_add() -> None:
    """Test setup refreshes the firmware entity immediately."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="123")
    entry.runtime_data = MagicMock()
    async_add_entities = MagicMock()

    await async_setup_entry(MagicMock(), entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities, update_before_add = async_add_entities.call_args.args
    assert len(entities) == 1
    assert isinstance(entities[0], VictronFirmwareUpdateEntity)
    assert update_before_add is True


@pytest.mark.parametrize(
    ("installed", "latest", "expected_state"),
    [
        ("v3.80~36", "v3.80~45", "on"),
        ("v3.80~45", "v3.80~36", "on"),
        ("v3.80~46", "v3.80", "on"),
        ("v3.80", "v3.80~46", "on"),
        ("v3.80", "v3.80.1", "on"),
        ("v3.80~45", None, "off"),
    ],
)
def test_firmware_update_uses_victron_offered_version(
    installed: str, latest: str, expected_state: str
) -> None:
    """Test any different version offered by Victron is an available update."""
    entity, _ = _create_entity(installed, latest)

    assert entity.state == expected_state


async def test_update_logs_firmware_versions_when_they_change(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test polling traces version comparison decisions without duplicate logs."""
    entity, hub = _create_entity("v3.80~36", "v3.80~45")
    hub.id = "test-hub"

    with caplog.at_level(logging.INFO):
        await entity.async_update()
        await entity.async_update()
        hub.firmware_versions = ("v3.80~45", "v3.80~45")
        await entity.async_update()

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "custom_components.victron_mqtt.update"
        and record.getMessage().startswith("GX firmware versions")
    ]
    assert len(messages) == 2
    assert "installed='v3.80~36', latest='v3.80~45'" in messages[0]
    assert "entity_available=True, update_expected=True, entity_state=on" in messages[0]
    assert "update_expected=False, entity_state=off" in messages[1]


async def test_update_caches_consistent_firmware_version_snapshot() -> None:
    """Test entity properties use the version pair captured during polling."""
    entity, hub = _create_entity("v3.80~36", None)

    hub.firmware_versions = ("v3.80~36", "v3.80~45")
    assert entity.installed_version == "v3.80~36"
    assert entity.latest_version == "v3.80~36"
    assert entity.available

    await entity.async_update()

    assert entity.installed_version == "v3.80~36"
    assert entity.latest_version == "v3.80~45"
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


async def test_install_exposes_progress_after_state_was_read() -> None:
    """Test Home Assistant refreshes cached properties when `_attr_*` changes."""
    entity, _ = _create_entity()
    entity.hass = MagicMock()
    states: list[tuple[bool | None, int | float | None]] = []

    async def install(
        hub: Hub, version: str, update_progress: Callable[[int], None]
    ) -> None:
        update_progress(25)

    # Home Assistant reads state attributes before an install is requested.
    state_attributes = entity.state_attributes
    assert state_attributes is not None
    assert state_attributes["in_progress"] is False
    with (
        patch.object(
            entity,
            "async_write_ha_state",
            side_effect=lambda: states.append(
                (entity.in_progress, entity.update_percentage)
            ),
        ),
        patch(
            "custom_components.victron_mqtt.update._async_install_firmware_update",
            side_effect=install,
        ),
    ):
        await entity.async_install(None, False)

    assert states == [(True, None), (True, 25), (False, None)]


async def test_install_does_not_start_without_available_version() -> None:
    """Test no firmware install starts when no online version is advertised."""
    entity, hub = _create_entity("v3.80~46", None)
    entity.hass = MagicMock()

    with patch(
        "custom_components.victron_mqtt.update._async_install_firmware_update",
        new=AsyncMock(),
    ) as install:
        await entity.async_install(None, False)

    install.assert_not_awaited()
    hub.install_firmware_update.assert_not_called()


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
    progress: list[int] = []

    with patch("custom_components.victron_mqtt.update.asyncio.sleep", new=AsyncMock()):
        await _async_install_firmware_update(hub, "v3.70", progress.append)

    hub.install_firmware_update.assert_called_once_with()
    assert progress == [25, 100]


@pytest.mark.parametrize(
    ("initial_version", "target_version"),
    [
        ("v3.80~36", "v3.80~45"),
        ("v3.80~45", "v3.80~36"),
    ],
)
async def test_install_waits_for_exact_target_version(
    initial_version: str, target_version: str
) -> None:
    """Test upgrades and downgrades wait for the exact target version."""
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
            (initial_version, target_version),
            (target_version, target_version),
        ]
    )
    type(hub).firmware_versions = versions

    with patch("custom_components.victron_mqtt.update.asyncio.sleep", new=AsyncMock()):
        await _async_install_firmware_update(hub, target_version, MagicMock())

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
    progress: list[int] = []

    with (
        patch("custom_components.victron_mqtt.update.asyncio.sleep", new=AsyncMock()),
        pytest.raises(FirmwareUpdateError, match="error_during_update"),
    ):
        await _async_install_firmware_update(hub, "v3.70", progress.append)

    assert update_status.call_count == 4
    assert progress == [10]


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
