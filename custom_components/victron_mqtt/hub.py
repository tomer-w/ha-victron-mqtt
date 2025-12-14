"""Main Hub class."""

from collections.abc import Callable
import logging


from victron_mqtt import (
    AuthenticationError,
    CannotConnectError,
    Device as VictronVenusDevice,
    DeviceType,
    Hub as VictronVenusHub,
    Metric as VictronVenusMetric,
    MetricKind,
    OperationMode,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    CONF_ELEVATED_TRACING,
    CONF_EXCLUDED_DEVICES,
    CONF_INSTALLATION_ID,
    CONF_MODEL,
    CONF_OPERATION_MODE,
    CONF_ROOT_TOPIC_PREFIX,
    CONF_SERIAL,
    CONF_SIMPLE_NAMING,
    CONF_UPDATE_FREQUENCY_SECONDS,
    DEFAULT_UPDATE_FREQUENCY_SECONDS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

NewMetricCallback = Callable[[VictronVenusDevice, VictronVenusMetric, DeviceInfo, str], None]

class Hub:
    """Victron MQTT Hub for managing communication and sensors."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize Victron MQTT Hub.

        Args:
            hass: Home Assistant instance
            entry: ConfigEntry containing configuration

        """

        _LOGGER.info("Initializing hub. ConfigEntry: %s, data: %s", entry, entry.data)
        config = entry.data
        self.hass = hass
        self.host = config[CONF_HOST]
        self.id = entry.unique_id

        op = config.get(CONF_OPERATION_MODE, OperationMode.FULL.value)
        operation_mode: OperationMode = (
            OperationMode(op) if not isinstance(op, OperationMode) else op
        )
        self.simple_naming = config.get(CONF_SIMPLE_NAMING, False)

        # Convert string device type exclusions to DeviceType instances
        excluded_device_strings = config.get(CONF_EXCLUDED_DEVICES, [])
        excluded_device_types: list[DeviceType] = [
            dt
            for device_string in excluded_device_strings
            if (dt := DeviceType.from_code(device_string)) is not None
        ]

        _LOGGER.info(
            "Final excluded device types: %s", [dt.code for dt in excluded_device_types]
        )


        self._hub: VictronVenusHub = VictronVenusHub(
            host=self.host,
            port=config.get(CONF_PORT, 1883),
            username=config.get(CONF_USERNAME) or None,
            password=config.get(CONF_PASSWORD) or None,
            use_ssl=config.get(CONF_SSL, False),
            installation_id=config.get(CONF_INSTALLATION_ID) or None,
            model_name=config.get(CONF_MODEL) or None,
            serial=config.get(CONF_SERIAL, "noserial"),
            topic_prefix=config.get(CONF_ROOT_TOPIC_PREFIX) or None,
            topic_log_info=config.get(CONF_ELEVATED_TRACING) or None,
            operation_mode=operation_mode,
            device_type_exclude_filter=excluded_device_types,
            update_frequency_seconds=config.get(
                CONF_UPDATE_FREQUENCY_SECONDS, DEFAULT_UPDATE_FREQUENCY_SECONDS
            ),
        )
        self._hub.on_new_metric = self._on_new_metric
        self.new_metric_callbacks: dict[MetricKind, NewMetricCallback] = {}

    async def start(self) -> None:
        """Start the Victron MQTT hub."""
        _LOGGER.info("Starting hub")
        try:
            await self._hub.connect()
        except AuthenticationError as auth_error:
            raise ConfigEntryAuthFailed(
                f"Authentication failed for {self.host}: {auth_error}"
            ) from auth_error
        except CannotConnectError as connect_error:
            raise ConfigEntryNotReady(
                f"Cannot connect to the hub: {connect_error}"
            ) from connect_error
        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.stop)

    async def stop(self, event: Event | None = None) -> None:
        """Stop the Victron MQTT hub."""
        _LOGGER.info("Stopping hub")
        await self._hub.disconnect()

    def _on_new_metric(
        self,
        hub: VictronVenusHub,
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
    ) -> None:
        _LOGGER.info("New metric received. Device: %s, Metric: %s", device, metric)
        assert hub.installation_id is not None
        device_info = Hub._map_device_info(device, hub.installation_id)
        callback = self.new_metric_callbacks.get(metric.metric_kind)
        if callback is not None:
            callback(device, metric, device_info, hub.installation_id)

    @staticmethod
    def _map_device_info(
        device: VictronVenusDevice, installation_id: str
    ) -> DeviceInfo:
        info: DeviceInfo = {}
        info["identifiers"] = {(DOMAIN, f"{installation_id}_{device.unique_id}")}
        info["manufacturer"] = (
            device.manufacturer if device.manufacturer is not None else "Victron Energy"
        )
        info["name"] = (
            f"{device.name} (ID: {device.device_id})"
            if device.device_id != "0"
            else device.name
        )
        info["model"] = device.model
        info["serial_number"] = device.serial_number

        return info

    def register_new_metric_callback(
        self, kind: MetricKind, new_metric_callback: NewMetricCallback
    ) -> None:
        """Register a callback to add entities for a specific metric kind."""
        _LOGGER.info(
            "Registering AddEntitiesCallback. kind: %s, AddEntitiesCallback: %s",
            kind,
            new_metric_callback,
        )
        assert kind not in self.add_entities_map, (
            f"AddEntitiesCallback for kind {kind} is already registered"
        )
        self.add_entities_map[kind] = new_metric_callback

    def unregister_all_new_metric_callbacks(self) -> None:
        """Unregister all callbacks to add entities for all metric kinds."""
        _LOGGER.info("Unregistering AddEntitiesCallback")
        self.add_entities_map.clear()

    def publish(
        self, metric_id: str, device_id: str, value: str | float | None
    ) -> None:
        """Publish a message to the Victron MQTT hub."""
        _LOGGER.info(
            "Publish service called with: metric_id=%s, device_id=%s, value=%s",
            metric_id,
            device_id,
            value,
        )
        self._hub.publish(metric_id, device_id, value)
