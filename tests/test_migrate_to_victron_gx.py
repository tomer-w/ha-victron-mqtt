"""Tests for the standalone Victron GX registry migration script."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT_PATH = (
    Path(__file__).parent.parent
    / "custom_components"
    / "victron_mqtt"
    / "migrate_to_victron_gx.py"
)


@pytest.fixture(scope="module")
def migration_module() -> ModuleType:
    """Load the standalone script without importing the custom integration."""
    spec = importlib.util.spec_from_file_location("migrate_to_victron_gx", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def storage_payloads() -> dict[str, dict]:
    """Return representative Home Assistant storage payloads."""
    return {
        "core.config_entries": {
            "version": 1,
            "data": {
                "entries": [
                    {
                        "entry_id": "custom-entry",
                        "domain": "victron_mqtt",
                        "unique_id": "abc123",
                        "data": {"installation_id": "abc123"},
                        "disabled_by": None,
                    },
                    {
                        "entry_id": "core-entry",
                        "domain": "victron_gx",
                        "unique_id": "abc123",
                        "data": {"installation_id": "abc123"},
                        "disabled_by": "user",
                    },
                ]
            },
        },
        "core.device_registry": {
            "version": 1,
            "data": {
                "devices": [
                    {
                        "id": "old-device",
                        "config_entries": ["custom-entry"],
                        "identifiers": [["victron_mqtt", "abc123_system_0"]],
                        "name": "GX",
                        "via_device_id": None,
                    },
                    {
                        "id": "new-device",
                        "config_entries": ["core-entry"],
                        "identifiers": [["victron_gx", "abc123_system_0"]],
                        "name": "GX",
                        "via_device_id": None,
                    },
                    {
                        "id": "old-child",
                        "config_entry_id": "custom-entry",
                        "identifiers": [["victron_mqtt", "abc123_battery_1"]],
                        "name": "Battery",
                        "via_device_id": "old-device",
                    },
                    {
                        "id": "new-child",
                        "config_entry_id": "core-entry",
                        "identifiers": [["victron_gx", "abc123_battery_1"]],
                        "name": "Battery",
                        "via_device_id": "new-device",
                    },
                ]
            },
        },
        "core.entity_registry": {
            "version": 1,
            "data": {
                "entities": [
                    {
                        "id": "old-registry-id",
                        "entity_id": "sensor.boat_battery_power",
                        "platform": "victron_mqtt",
                        "unique_id": ("sensor.victron_mqtt_battery_1_power"),
                        "config_entry_id": "custom-entry",
                        "device_id": "old-child",
                        "name": "My custom name",
                    },
                    {
                        "id": "new-registry-id",
                        "entity_id": "sensor.victron_gx_battery_power",
                        "platform": "victron_gx",
                        "unique_id": "abc123_battery_1_power",
                        "config_entry_id": "core-entry",
                        "device_id": "new-child",
                        "name": None,
                    },
                    {
                        "id": "old-registry-id-2",
                        "entity_id": "sensor.boat_battery_voltage",
                        "platform": "victron_mqtt",
                        "unique_id": ("sensor.victron_mqtt_abc123_battery_1_voltage"),
                        "config_entry_id": "custom-entry",
                        "device_id": "old-child",
                        "name": None,
                    },
                    {
                        "id": "new-registry-id-2",
                        "entity_id": "sensor.victron_gx_battery_voltage",
                        "platform": "victron_gx",
                        "unique_id": "abc123_battery_1_voltage",
                        "config_entry_id": "core-entry",
                        "device_id": "new-child",
                        "name": None,
                    },
                    {
                        "id": "core-only-id",
                        "entity_id": "sensor.victron_gx_core_only",
                        "platform": "victron_gx",
                        "unique_id": "abc123_battery_1_core_only",
                        "config_entry_id": "core-entry",
                        "device_id": "new-child",
                        "name": None,
                    },
                    {
                        "id": "unmatched-id",
                        "entity_id": "update.boat_firmware",
                        "platform": "victron_mqtt",
                        "unique_id": "abc123_firmware",
                        "config_entry_id": "custom-entry",
                        "device_id": "old-device",
                        "name": None,
                    },
                ]
            },
        },
    }


def test_build_plan_preserves_old_ids_and_customizations(
    migration_module: ModuleType, storage_payloads: dict[str, dict]
) -> None:
    """The old registry rows should become the Core rows."""
    plan = migration_module.build_migration_plan(storage_payloads)

    entities = plan.payloads["core.entity_registry"]["data"]["entities"]
    migrated = next(
        entity
        for entity in entities
        if entity["entity_id"] == "sensor.boat_battery_power"
    )

    assert migrated["id"] == "old-registry-id"
    assert migrated["entity_id"] == "sensor.boat_battery_power"
    assert migrated["name"] == "My custom name"
    assert migrated["platform"] == "victron_gx"
    assert migrated["unique_id"] == "abc123_battery_1_power"
    assert migrated["config_entry_id"] == "core-entry"
    assert migrated["device_id"] == "old-child"
    assert not any(
        entity["entity_id"] == "sensor.victron_gx_battery_power" for entity in entities
    )


def test_build_plan_handles_non_simple_unique_ids(
    migration_module: ModuleType, storage_payloads: dict[str, dict]
) -> None:
    """An installation ID already in a custom unique ID is not duplicated."""
    plan = migration_module.build_migration_plan(storage_payloads)
    entities = plan.payloads["core.entity_registry"]["data"]["entities"]
    migrated = next(
        entity
        for entity in entities
        if entity["entity_id"] == "sensor.boat_battery_voltage"
    )

    assert migrated["unique_id"] == "abc123_battery_1_voltage"


def test_build_plan_preserves_device_ids_and_relinks_core_only_entities(
    migration_module: ModuleType, storage_payloads: dict[str, dict]
) -> None:
    """Existing device-target references remain valid after deduplication."""
    plan = migration_module.build_migration_plan(storage_payloads)
    devices = plan.payloads["core.device_registry"]["data"]["devices"]
    entities = plan.payloads["core.entity_registry"]["data"]["entities"]

    assert {device["id"] for device in devices} == {"old-device", "old-child"}
    old_device = next(device for device in devices if device["id"] == "old-device")
    old_child = next(device for device in devices if device["id"] == "old-child")
    core_only = next(
        entity
        for entity in entities
        if entity["entity_id"] == "sensor.victron_gx_core_only"
    )

    assert old_device["identifiers"] == [["victron_gx", "abc123_system_0"]]
    assert old_device["config_entries"] == ["core-entry"]
    assert old_child["identifiers"] == [["victron_gx", "abc123_battery_1"]]
    assert old_child["config_entry_id"] == "core-entry"
    assert old_child["via_device_id"] == "old-device"
    assert core_only["device_id"] == "old-child"


def test_build_plan_reports_unmatched_entities_and_switches_entries(
    migration_module: ModuleType, storage_payloads: dict[str, dict]
) -> None:
    """Unsupported entities remain attached to the disabled custom entry."""
    plan = migration_module.build_migration_plan(storage_payloads)
    entries = plan.payloads["core.config_entries"]["data"]["entries"]
    entities = plan.payloads["core.entity_registry"]["data"]["entities"]
    installation = plan.installations[0]

    custom_entry = next(
        entry for entry in entries if entry["entry_id"] == "custom-entry"
    )
    core_entry = next(entry for entry in entries if entry["entry_id"] == "core-entry")
    unmatched = next(
        entity for entity in entities if entity["entity_id"] == "update.boat_firmware"
    )

    assert custom_entry["disabled_by"] == "user"
    assert core_entry["disabled_by"] is None
    assert unmatched["platform"] == "victron_mqtt"
    assert installation.unmatched_entities == [
        "update.boat_firmware (unrecognized custom unique ID)"
    ]
