#!/usr/bin/env python3
"""Migrate Victron MQTT registry entries to Home Assistant's Victron GX integration.

This script is intentionally standalone. Run it against Home Assistant's
``.storage`` directory while Home Assistant Core is stopped.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CUSTOM_DOMAIN = "victron_mqtt"
CORE_DOMAIN = "victron_gx"
CONFIG_ENTRIES_FILE = "core.config_entries"
DEVICE_REGISTRY_FILE = "core.device_registry"
ENTITY_REGISTRY_FILE = "core.entity_registry"
STORAGE_FILES = (
    CONFIG_ENTRIES_FILE,
    DEVICE_REGISTRY_FILE,
    ENTITY_REGISTRY_FILE,
)

JsonObject = dict[str, Any]


class MigrationError(Exception):
    """Raised when the registry cannot be migrated safely."""


@dataclass
class InstallationPlan:
    """Migration counts and warnings for one Victron installation."""

    installation_id: str
    custom_config_entry_id: str
    core_config_entry_id: str
    migrated_devices: int = 0
    migrated_entities: int = 0
    unmatched_devices: list[str] = field(default_factory=list)
    unmatched_entities: list[str] = field(default_factory=list)


@dataclass
class MigrationPlan:
    """Complete migration plan and updated storage payloads."""

    payloads: dict[str, JsonObject]
    installations: list[InstallationPlan]

    @property
    def migrated_entities(self) -> int:
        """Return the total number of migrated entities."""
        return sum(item.migrated_entities for item in self.installations)


def _load_storage_file(path: Path) -> JsonObject:
    try:
        with path.open(encoding="utf-8") as storage_file:
            payload = json.load(storage_file)
    except FileNotFoundError as err:
        raise MigrationError(f"Required storage file does not exist: {path}") from err
    except json.JSONDecodeError as err:
        raise MigrationError(f"Invalid JSON in {path}: {err}") from err

    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise MigrationError(f"Unexpected Home Assistant storage format in {path}")
    return payload


def load_storage(storage_dir: Path) -> dict[str, JsonObject]:
    """Load the Home Assistant registries used by the migration."""
    return {
        filename: _load_storage_file(storage_dir / filename)
        for filename in STORAGE_FILES
    }


def _items(payload: JsonObject, key: str, filename: str) -> list[JsonObject]:
    items = payload["data"].get(key)
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise MigrationError(f"Unexpected {key!r} data in {filename}")
    return items


def _installation_id(entry: JsonObject) -> str | None:
    unique_id = entry.get("unique_id")
    if isinstance(unique_id, str) and unique_id:
        return unique_id
    data = entry.get("data")
    if isinstance(data, dict):
        installation_id = data.get("installation_id")
        if isinstance(installation_id, str) and installation_id:
            return installation_id
    return None


def _entry_id(entry: JsonObject) -> str:
    entry_id = entry.get("entry_id")
    if not isinstance(entry_id, str) or not entry_id:
        raise MigrationError("A Victron config entry has no valid entry_id")
    return entry_id


def _index_config_entries(
    entries: list[JsonObject], domain: str
) -> dict[str, JsonObject]:
    indexed: dict[str, JsonObject] = {}
    for entry in entries:
        if entry.get("domain") != domain:
            continue
        installation_id = _installation_id(entry)
        if installation_id is None:
            raise MigrationError(
                f"Config entry {_entry_id(entry)} for {domain} has no installation ID"
            )
        if installation_id in indexed:
            raise MigrationError(
                f"Multiple {domain} config entries use installation ID {installation_id}"
            )
        indexed[installation_id] = entry
    return indexed


def _config_entry_ids(item: JsonObject) -> set[str]:
    result: set[str] = set()
    config_entry_id = item.get("config_entry_id")
    if isinstance(config_entry_id, str):
        result.add(config_entry_id)
    config_entries = item.get("config_entries")
    if isinstance(config_entries, list):
        result.update(value for value in config_entries if isinstance(value, str))
    return result


def _move_to_config_entry(
    item: JsonObject, old_entry_id: str, new_entry_id: str
) -> None:
    if "config_entry_id" in item:
        item["config_entry_id"] = new_entry_id

    config_entries = item.get("config_entries")
    if isinstance(config_entries, list):
        item["config_entries"] = list(
            dict.fromkeys(
                new_entry_id if value == old_entry_id else value
                for value in config_entries
            )
        )

    subentries = item.get("config_entries_subentries")
    if isinstance(subentries, dict) and old_entry_id in subentries:
        subentries[new_entry_id] = subentries.pop(old_entry_id)


def _identifier_pairs(device: JsonObject) -> list[list[str]]:
    identifiers = device.get("identifiers")
    if not isinstance(identifiers, list):
        raise MigrationError(
            f"Device {device.get('id', '<unknown>')} has invalid identifiers"
        )
    return [
        value
        for value in identifiers
        if isinstance(value, list)
        and len(value) == 2
        and all(isinstance(part, str) for part in value)
    ]


def _integration_identifier(
    device: JsonObject, domain: str, installation_id: str
) -> str | None:
    prefix = f"{installation_id}_"
    matches = [
        value
        for identifier_domain, value in _identifier_pairs(device)
        if identifier_domain == domain and value.startswith(prefix)
    ]
    if len(matches) > 1:
        raise MigrationError(
            f"Device {device.get('id', '<unknown>')} has multiple {domain} identifiers"
        )
    return matches[0] if matches else None


def _replace_identifier_domain(
    device: JsonObject, old_domain: str, new_domain: str, identifier_value: str
) -> None:
    device["identifiers"] = [
        [new_domain, value]
        if domain == old_domain and value == identifier_value
        else [domain, value]
        for domain, value in _identifier_pairs(device)
    ]


def _core_unique_id(entity: JsonObject, installation_id: str) -> str | None:
    entity_id = entity.get("entity_id")
    unique_id = entity.get("unique_id")
    if not isinstance(entity_id, str) or "." not in entity_id:
        raise MigrationError("A custom Victron entity has no valid entity_id")
    if not isinstance(unique_id, str):
        raise MigrationError(f"Entity {entity_id} has no valid unique_id")

    entity_domain = entity_id.split(".", 1)[0]
    prefix = f"{entity_domain}.{CUSTOM_DOMAIN}_"
    if not unique_id.startswith(prefix):
        return None

    metric_unique_id = unique_id.removeprefix(prefix)
    installation_prefix = f"{installation_id}_"
    if metric_unique_id.startswith(installation_prefix):
        return metric_unique_id
    return f"{installation_prefix}{metric_unique_id}"


def _entity_key(entity: JsonObject) -> tuple[str, str] | None:
    entity_id = entity.get("entity_id")
    unique_id = entity.get("unique_id")
    if not isinstance(entity_id, str) or "." not in entity_id:
        return None
    if not isinstance(unique_id, str):
        return None
    return entity_id.split(".", 1)[0], unique_id


def _migrate_devices(
    devices: list[JsonObject],
    installation: InstallationPlan,
) -> dict[str, str]:
    old_entry_id = installation.custom_config_entry_id
    new_entry_id = installation.core_config_entry_id
    core_by_identifier: dict[str, JsonObject] = {}

    for device in devices:
        if new_entry_id not in _config_entry_ids(device):
            continue
        identifier = _integration_identifier(
            device, CORE_DOMAIN, installation.installation_id
        )
        if identifier is not None:
            if identifier in core_by_identifier:
                raise MigrationError(
                    f"Multiple {CORE_DOMAIN} devices use identifier {identifier}"
                )
            core_by_identifier[identifier] = device

    core_to_custom_device_id: dict[str, str] = {}
    devices_to_remove: set[str] = set()
    for device in devices:
        if old_entry_id not in _config_entry_ids(device):
            continue
        identifier = _integration_identifier(
            device, CUSTOM_DOMAIN, installation.installation_id
        )
        if identifier is None:
            continue

        core_device = core_by_identifier.get(identifier)
        if core_device is None:
            installation.unmatched_devices.append(
                str(device.get("name_by_user") or device.get("name") or identifier)
            )
            continue

        old_device_id = device.get("id")
        core_device_id = core_device.get("id")
        if not isinstance(old_device_id, str) or not isinstance(core_device_id, str):
            raise MigrationError(f"Device pair for {identifier} has an invalid ID")

        _replace_identifier_domain(device, CUSTOM_DOMAIN, CORE_DOMAIN, identifier)
        _move_to_config_entry(device, old_entry_id, new_entry_id)
        core_to_custom_device_id[core_device_id] = old_device_id
        devices_to_remove.add(core_device_id)
        installation.migrated_devices += 1

    if not devices_to_remove:
        return core_to_custom_device_id

    for device in devices:
        via_device_id = device.get("via_device_id")
        if via_device_id in core_to_custom_device_id:
            device["via_device_id"] = core_to_custom_device_id[via_device_id]

    devices[:] = [
        device for device in devices if device.get("id") not in devices_to_remove
    ]
    return core_to_custom_device_id


def _migrate_entities(
    entities: list[JsonObject],
    installation: InstallationPlan,
    core_to_custom_device_id: dict[str, str],
) -> None:
    old_entry_id = installation.custom_config_entry_id
    new_entry_id = installation.core_config_entry_id
    core_entities: dict[tuple[str, str], JsonObject] = {}

    for entity in entities:
        if (
            entity.get("platform") != CORE_DOMAIN
            or entity.get("config_entry_id") != new_entry_id
        ):
            continue
        key = _entity_key(entity)
        if key is None:
            continue
        if key in core_entities:
            raise MigrationError(
                f"Multiple {CORE_DOMAIN} entities use unique ID {key[1]}"
            )
        core_entities[key] = entity

    entities_to_remove: set[str] = set()
    for entity in entities:
        if (
            entity.get("platform") != CUSTOM_DOMAIN
            or entity.get("config_entry_id") != old_entry_id
        ):
            continue

        entity_id = str(entity.get("entity_id", "<unknown>"))
        core_unique_id = _core_unique_id(entity, installation.installation_id)
        if core_unique_id is None:
            installation.unmatched_entities.append(
                f"{entity_id} (unrecognized custom unique ID)"
            )
            continue

        entity_domain = entity_id.split(".", 1)[0]
        core_entity = core_entities.get((entity_domain, core_unique_id))
        if core_entity is None:
            installation.unmatched_entities.append(
                f"{entity_id} (not exposed by Victron GX)"
            )
            continue

        core_entity_id = core_entity.get("entity_id")
        if not isinstance(core_entity_id, str):
            raise MigrationError(
                f"Victron GX counterpart for {entity_id} has an invalid entity_id"
            )

        entity["platform"] = CORE_DOMAIN
        entity["unique_id"] = core_unique_id
        entity["config_entry_id"] = new_entry_id

        old_device_id = entity.get("device_id")
        core_device_id = core_entity.get("device_id")
        if isinstance(core_device_id, str):
            entity["device_id"] = core_to_custom_device_id.get(
                core_device_id, core_device_id
            )
        elif isinstance(old_device_id, str):
            entity["device_id"] = old_device_id

        entities_to_remove.add(core_entity_id)
        installation.migrated_entities += 1

    for entity in entities:
        device_id = entity.get("device_id")
        if device_id in core_to_custom_device_id:
            entity["device_id"] = core_to_custom_device_id[device_id]

    entities[:] = [
        entity
        for entity in entities
        if entity.get("entity_id") not in entities_to_remove
    ]


def build_migration_plan(
    source_payloads: dict[str, JsonObject],
    selected_installation_id: str | None = None,
) -> MigrationPlan:
    """Build and validate a migration without changing the source payloads."""
    payloads = copy.deepcopy(source_payloads)
    config_entries = _items(
        payloads[CONFIG_ENTRIES_FILE], "entries", CONFIG_ENTRIES_FILE
    )
    devices = _items(payloads[DEVICE_REGISTRY_FILE], "devices", DEVICE_REGISTRY_FILE)
    entities = _items(payloads[ENTITY_REGISTRY_FILE], "entities", ENTITY_REGISTRY_FILE)

    custom_entries = _index_config_entries(config_entries, CUSTOM_DOMAIN)
    core_entries = _index_config_entries(config_entries, CORE_DOMAIN)
    installation_ids = sorted(custom_entries.keys() & core_entries.keys())

    if selected_installation_id is not None:
        if selected_installation_id not in installation_ids:
            raise MigrationError(
                f"No matching {CUSTOM_DOMAIN} and {CORE_DOMAIN} config entries found "
                f"for installation {selected_installation_id}"
            )
        installation_ids = [selected_installation_id]

    if not installation_ids:
        raise MigrationError(
            f"No installations configured in both {CUSTOM_DOMAIN} and {CORE_DOMAIN}"
        )

    plans: list[InstallationPlan] = []
    for installation_id in installation_ids:
        custom_entry = custom_entries[installation_id]
        core_entry = core_entries[installation_id]
        installation = InstallationPlan(
            installation_id=installation_id,
            custom_config_entry_id=_entry_id(custom_entry),
            core_config_entry_id=_entry_id(core_entry),
        )

        device_id_map = _migrate_devices(devices, installation)
        _migrate_entities(entities, installation, device_id_map)
        if installation.migrated_entities == 0:
            raise MigrationError(
                f"No matching entity pairs found for installation {installation_id}"
            )

        custom_entry["disabled_by"] = "user"
        core_entry["disabled_by"] = None
        plans.append(installation)

    plan = MigrationPlan(payloads=payloads, installations=plans)
    if plan.migrated_entities == 0:
        raise MigrationError(
            "No matching entity pairs were found; no changes can be applied safely"
        )
    return plan


def _atomic_write_json(path: Path, payload: JsonObject) -> None:
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as output:
            json.dump(payload, output, ensure_ascii=False, separators=(",", ":"))
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def apply_migration(storage_dir: Path, plan: MigrationPlan) -> list[Path]:
    """Back up all touched files, then atomically write the migration."""
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_paths: list[Path] = []

    for filename in STORAGE_FILES:
        source = storage_dir / filename
        backup = storage_dir / f"{filename}.pre-victron-gx-{timestamp}.bak"
        if backup.exists():
            raise MigrationError(f"Backup path already exists: {backup}")
        shutil.copy2(source, backup)
        backup_paths.append(backup)

    try:
        for filename in STORAGE_FILES:
            _atomic_write_json(storage_dir / filename, plan.payloads[filename])
    except BaseException as err:
        for filename, backup in zip(STORAGE_FILES, backup_paths, strict=True):
            shutil.copy2(backup, storage_dir / filename)
        raise MigrationError(
            f"Writing the migration failed and the original files were restored: {err}"
        ) from err

    return backup_paths


def _print_plan(plan: MigrationPlan) -> None:
    for installation in plan.installations:
        print(f"Installation: {installation.installation_id}")
        print(f"  Devices to migrate:  {installation.migrated_devices}")
        print(f"  Entities to migrate: {installation.migrated_entities}")
        print(f"  Unmatched devices:    {len(installation.unmatched_devices)}")
        print(f"  Unmatched entities:   {len(installation.unmatched_entities)}")
        for device in installation.unmatched_devices:
            print(f"    - Device: {device}")
        for entity in installation.unmatched_entities:
            print(f"    - {entity}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preserve Victron MQTT entity/device IDs while handing their registry "
            "entries to Home Assistant's built-in Victron GX integration."
        )
    )
    parser.add_argument(
        "storage_dir",
        type=Path,
        help="Home Assistant's .storage directory (usually /config/.storage)",
    )
    parser.add_argument(
        "--installation-id",
        help="Migrate only this Victron installation ID",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the migration. Home Assistant Core MUST be stopped.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the registry migration CLI."""
    args = _parse_args()
    storage_dir = args.storage_dir.expanduser().resolve()

    try:
        payloads = load_storage(storage_dir)
        plan = build_migration_plan(payloads, args.installation_id)
        _print_plan(plan)

        if not args.apply:
            print("\nDry run only; no files were changed.")
            print("Stop Home Assistant Core, then rerun with --apply.")
            return 0

        backup_paths = apply_migration(storage_dir, plan)
    except (MigrationError, OSError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    print("\nMigration applied. Backups:")
    for path in backup_paths:
        print(f"  {path}")
    print("\nStart Home Assistant Core and verify the migrated entities.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
