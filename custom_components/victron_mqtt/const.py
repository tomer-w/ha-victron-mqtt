"""Constants for the victron_mqtt integration."""
from __future__ import annotations

import logging

from victron_mqtt import MetricNature

from homeassistant.components.sensor import SensorStateClass

_LOGGER = logging.getLogger(__name__)

# Integration specific values (custom / builtin Home Assistant)
DOMAIN = "victron_mqtt"
DEFAULT_SIMPLE_NAMING = True

# generic config values
CONF_INSTALLATION_ID = "installation_id"
CONF_MODEL = "model"
CONF_SERIAL = "serial"
CONF_ROOT_TOPIC_PREFIX = "root_topic_prefix"
CONF_UPDATE_FREQUENCY_SECONDS = "update_frequency"
CONF_UPDATE_FREQUENCY_OVERRIDES = "update_frequency_overrides"
CONF_OPERATION_MODE = "operation_mode"
CONF_EXCLUDED_DEVICES = "excluded_devices"
CONF_SIMPLE_NAMING = "simple_naming"
CONF_ELEVATED_TRACING = "elevated_tracing"

DEVICE_MESSAGE = "device"
SENSOR_MESSAGE = "sensor"

DEFAULT_HOST = "venus.local."
DEFAULT_PORT = 1883
DEFAULT_UPDATE_FREQUENCY_SECONDS = 30

# Service names
SERVICE_PUBLISH = "publish"

# Service data attributes
ATTR_METRIC_ID = "metric_id"
ATTR_DEVICE_ID = "device_id"
ATTR_VALUE = "value"

# Binary sensor enum ids must be "on" for on and "off" for off.
BINARY_SENSOR_ON_ID = "on"
BINARY_SENSOR_OFF_ID = "off"

# Known HA entity platform prefixes to strip from override keys
_ENTITY_PREFIXES = (
    "sensor.victron_mqtt_",
    "binary_sensor.victron_mqtt_",
    "number.victron_mqtt_",
    "select.victron_mqtt_",
    "switch.victron_mqtt_",
    "button.victron_mqtt_",
    "time.victron_mqtt_",
    "device_tracker.victron_mqtt_",
    "victron_mqtt_",
)


def parse_frequency_overrides(text: str | None, installation_id: str | None = None) -> dict[str, int]:
    """Parse a comma-separated list of short_id:seconds pairs.

    Accepts entries like:
        grid_power_l1:3,inverter_power:5
        sensor.victron_mqtt_grid_power_l1:3
        sensor.victron_mqtt_c0619ab48793_grid_power_l1:3  (with installation_id)

    Known HA entity prefixes are stripped automatically so users can paste
    either the library short_id or the full HA entity_id. When simple_naming
    is disabled, the installation_id is embedded in the entity ID and will
    also be stripped.

    Returns a dict mapping short_id to frequency in seconds.
    Invalid entries are logged and skipped.
    """
    if not text or not text.strip():
        return {}

    result: dict[str, int] = {}
    for entry in text.split(","):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(":")
        if len(parts) != 2:
            _LOGGER.warning("Ignoring invalid frequency override entry: '%s'", entry)
            continue
        key, value_str = parts[0].strip(), parts[1].strip()
        if not key or not value_str:
            _LOGGER.warning("Ignoring empty key or value in frequency override: '%s'", entry)
            continue

        # Strip known HA entity prefixes
        for prefix in _ENTITY_PREFIXES:
            if key.startswith(prefix):
                key = key[len(prefix):]
                break

        # Strip installation_id prefix (used when simple_naming is disabled)
        if installation_id and key.startswith(f"{installation_id}_"):
            key = key[len(installation_id) + 1:]

        try:
            freq = int(value_str)
        except ValueError:
            _LOGGER.warning("Ignoring non-integer frequency value in override: '%s'", entry)
            continue

        if freq < 0:
            _LOGGER.warning("Ignoring negative frequency value in override: '%s'", entry)
            continue

        result[key] = freq

    return result
