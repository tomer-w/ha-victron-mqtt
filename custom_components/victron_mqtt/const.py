"""Constants for the victron_mqtt integration."""
from ._vendor.victron_mqtt import MetricNature

from homeassistant.components.sensor import SensorStateClass

# Integration specific values (custom / builtin Home Assistant)
DOMAIN = "victron_mqtt"
DEFAULT_SIMPLE_NAMING = True

# generic config values
CONF_INSTALLATION_ID = "installation_id"
CONF_MODEL = "model"
CONF_SERIAL = "serial"
CONF_ROOT_TOPIC_PREFIX = "root_topic_prefix"
CONF_UPDATE_FREQUENCY_SECONDS = "update_frequency"
CONF_UPDATE_FREQUENCY_MODE = "update_frequency_mode"
CONF_OPERATION_MODE = "operation_mode"
CONF_EXCLUDED_DEVICES = "excluded_devices"
CONF_SIMPLE_NAMING = "simple_naming"
CONF_ELEVATED_TRACING = "elevated_tracing"

DEVICE_MESSAGE = "device"
SENSOR_MESSAGE = "sensor"

DEFAULT_HOST = "venus.local."
DEFAULT_PORT = 1883
DEFAULT_UPDATE_FREQUENCY_SECONDS = 30

# Update frequency mode: either the library-driven "auto" profile or a fixed
# manual interval (in seconds).
UPDATE_FREQUENCY_MODE_AUTO = "auto"
UPDATE_FREQUENCY_MODE_MANUAL = "manual"
DEFAULT_UPDATE_FREQUENCY_MODE = UPDATE_FREQUENCY_MODE_AUTO

# Service names
SERVICE_PUBLISH = "publish"

# Service data attributes
ATTR_METRIC_ID = "metric_id"
ATTR_DEVICE_ID = "device_id"
ATTR_VALUE = "value"

# Binary sensor enum ids must be "on" for on and "off" for off.
BINARY_SENSOR_ON_ID = "on"
BINARY_SENSOR_OFF_ID = "off"
