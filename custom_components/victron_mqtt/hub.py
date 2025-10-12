import logging
from typing import Any
from datetime import timedelta

from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.number import NumberEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
)

from victron_mqtt import (
    CannotConnectError,
    Hub as VictronVenusHub,
    Metric as VictronVenusMetric,
    WritableMetric as VictronVenusWritableMetric,
    Device as VictronVenusDevice,
    MetricKind,
    GenericOnOff,
    OperationMode,
    DeviceType
)

from .const import CONF_INSTALLATION_ID, CONF_MODEL, CONF_SERIAL, CONF_UPDATE_FREQUENCY_SECONDS, DEFAULT_UPDATE_FREQUENCY_SECONDS, DOMAIN, CONF_ROOT_TOPIC_PREFIX, CONF_OPERATION_MODE, CONF_EXCLUDED_DEVICES
from .common import VictronBaseEntity

_LOGGER = logging.getLogger(__name__)

class Hub:
    """Victron MQTT Hub for managing communication and sensors."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """
        Initialize Victron MQTT Hub.
                
        Args:
            hass: Home Assistant instance
            entry: ConfigEntry containing configuration
        """
        _LOGGER.info("Initializing hub. ConfigEntry: %s, data: %s", entry, entry.data)
        self.hass = hass
        self.entry = entry
        self.id = entry.unique_id

        config = entry.data
        op = config.get(CONF_OPERATION_MODE, OperationMode.FULL.value)
        operation_mode: OperationMode = OperationMode(op) if not isinstance(op, OperationMode) else op

        # Convert string device type exclusions to DeviceType instances
        excluded_device_strings = config.get(CONF_EXCLUDED_DEVICES, [])
        excluded_device_types = []
        for device_string in excluded_device_strings:
            excluded_device_types.append(DeviceType.from_code(device_string))
        _LOGGER.info("Final excluded device types: %s", [dt.code for dt in excluded_device_types])

        self._hub: VictronVenusHub = VictronVenusHub(
            host=config.get(CONF_HOST),
            port=config.get(CONF_PORT, 1883),
            username=config.get(CONF_USERNAME) or None,
            password=config.get(CONF_PASSWORD) or None,
            use_ssl=config.get(CONF_SSL, False),
            installation_id=config.get(CONF_INSTALLATION_ID) or None,
            model_name=config.get(CONF_MODEL) or None,
            serial=config.get(CONF_SERIAL, "noserial"),
            topic_prefix=config.get(CONF_ROOT_TOPIC_PREFIX) or None,
            operation_mode=operation_mode,
            device_type_exclude_filter=excluded_device_types,
            update_frequency_seconds=config.get(CONF_UPDATE_FREQUENCY_SECONDS, DEFAULT_UPDATE_FREQUENCY_SECONDS),
        )
        self._hub.on_new_metric = self.on_new_metric
        self.add_entities_map: dict[MetricKind, AddEntitiesCallback] = {}
        
        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.stop)

    async def start(self):
        _LOGGER.info("Starting hub.")
        try:
            await self._hub.connect()
        except CannotConnectError as connect_error:
            raise ConfigEntryNotReady(f"Cannot connect to the hub: {connect_error}") from connect_error

    @callback
    async def stop(self, event: Event):
        _LOGGER.info("Stopping hub")
        await self._hub.disconnect()

    def on_new_metric(self, hub: VictronVenusHub, device: VictronVenusDevice, metric: VictronVenusMetric):
        _LOGGER.info("New metric received. Device: %s, Metric: %s", device, metric)
        device_info = Hub._map_device_info(device)
        entity = self.creatre_entity(device, metric, device_info)
        
        # Add entity dynamically to the platform
        self.add_entities_map[metric.metric_kind]([entity])

    @staticmethod
    def _map_device_info(device: VictronVenusDevice) -> DeviceInfo:
        info: DeviceInfo = {}
        info["identifiers"] = {(DOMAIN, device.unique_id)}
        info["manufacturer"] = device.manufacturer if device.manufacturer is not None else "Victron Energy"
        info["name"] = f"{device.name} (ID: {device.device_id})" if device.device_id != "0" else device.name
        info["model"] = device.model
        info["serial_number"] = device.serial_number

        return info

    def register_add_entities_callback(self, async_add_entities: AddEntitiesCallback, kind: MetricKind):
        """Register a callback to add entities for a specific metric kind."""
        _LOGGER.info("Registering AddEntitiesCallback. kind: %s, AddEntitiesCallback: %s", kind, async_add_entities)
        self.add_entities_map[kind] = async_add_entities

    def creatre_entity(self, device: VictronVenusDevice, metric: VictronVenusMetric, info: DeviceInfo) -> VictronBaseEntity:
        """Create a VictronBaseEntity from a device and metric."""
        if metric.metric_kind == MetricKind.SENSOR:
            return VictronSensor(device, metric, info)
        elif metric.metric_kind == MetricKind.BINARY_SENSOR:
            return VictronBinarySensor(device, metric, info)
        assert isinstance(metric, VictronVenusWritableMetric), f"Expected metric to be a VictronVenusWritableMetric. Got {type(metric)}"
        if metric.metric_kind == MetricKind.SWITCH:
            return VictronSwitch(device, metric, info)
        elif metric.metric_kind == MetricKind.NUMBER:
            return VictronNumber(device, metric, info)
        elif metric.metric_kind == MetricKind.SELECT:
            return VictronSelect(device, metric, info)
        else:
            raise ValueError(f"Unsupported metric kind: {metric.metric_kind}")

    def publish(self, metric_id: str, device_id: str, value: str | float | int | None) -> None:
        """Publish a message to the Victron MQTT hub."""
        _LOGGER.info("Publish service called with: metric_id=%s, device_id=%s, value=%s",
                      metric_id, device_id, value)
        try:
            self._hub.publish(metric_id, device_id, value)
        except Exception:
            raise HomeAssistantError(f"Error publishing to Victron MQTT. metric_id: '{metric_id}'")


class VictronSensor(VictronBaseEntity, SensorEntity):
    """Implementation of a Victron Venus sensor."""

    def __init__(
        self,
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor based on detauls in the metric."""
        self._attr_native_value = metric.value
        super().__init__(device, metric, device_info, "sensor")

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronSensor({super().__repr__()})"

    def _on_update_task(self, value: Any) -> None:
        if self._attr_native_value == value:
            return
        self._attr_native_value = value
        self.schedule_update_ha_state()

class VictronSwitch(VictronBaseEntity, SwitchEntity):
    """Implementation of a Victron Venus multiple state select using SelectEntity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        writable_metric: VictronVenusWritableMetric,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the switch."""
        self._attr_is_on = writable_metric.value == GenericOnOff.On
        super().__init__(device, writable_metric, device_info, "switch")

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return (
            f"VictronSwitch({super().__repr__()}, is_on={self._attr_is_on})"
        )

    def _on_update_task(self, value: Any) -> None:
        new_val = value == GenericOnOff.On
        if self._attr_is_on == new_val:
            return
        self._attr_is_on = new_val
        self.schedule_update_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        _LOGGER.info("Turning on switch: %s", self._attr_unique_id)
        self._metric.set(GenericOnOff.On)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        _LOGGER.info("Turning off switch: %s", self._attr_unique_id)
        self._metric.set(GenericOnOff.Off)
        self.async_write_ha_state()

class VictronNumber(VictronBaseEntity, NumberEntity):
    """Implementation of a Victron Venus number entity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        writable_metric: VictronVenusWritableMetric,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the number entity."""
        self._attr_native_value = writable_metric.value
        if isinstance(writable_metric.min_value, int) or isinstance(writable_metric.min_value, float):
            self._attr_native_min_value = writable_metric.min_value
        if isinstance(writable_metric.max_value, int) or isinstance(writable_metric.max_value, float):
            self._attr_native_max_value = writable_metric.max_value
        if isinstance(writable_metric.step, int) or isinstance(writable_metric.step, float):
            self._attr_native_step = writable_metric.step
        super().__init__(device, writable_metric, device_info, "number")

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronNumber({super().__repr__()}, native_value={self._attr_native_value})"

    def _on_update_task(self, value: Any) -> None:
        if self._attr_native_value == value:
            return
        self._attr_native_value = value
        self.schedule_update_ha_state()

    @property
    def native_value(self):
        """Return the current value."""
        return self._metric.value

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        _LOGGER.info("Setting number %s on switch: %s", value, self._attr_unique_id)
        self._metric.set(value)
        self.async_write_ha_state()


class VictronBinarySensor(VictronBaseEntity, BinarySensorEntity):
    """Implementation of a Victron Venus binary sensor."""

    def __init__(
        self,
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
    ) -> None:
        self._attr_is_on = bool(metric.value)
        super().__init__(device, metric, device_info, "binary_sensor")

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronBinarySensor({super().__repr__()}), is_on={self._attr_is_on})"

    def _on_update_task(self, value: Any) -> None:
        new_val = value == GenericOnOff.On
        if self._attr_is_on == new_val:
            return
        self._attr_is_on = new_val
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

class VictronSelect(VictronBaseEntity, SelectEntity):
    """Implementation of a Victron Venus multiple state select using SelectEntity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        writable_metric: VictronVenusWritableMetric,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the switch."""
        self._attr_options = writable_metric.enum_values
        self._attr_current_option = self._map_value_to_state(writable_metric.value)
        super().__init__(device, writable_metric, device_info, "select")

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronSelect({super().__repr__()}, current_option={self._attr_current_option}, options={self._attr_options})"

    def _on_update_task(self, value: Any) -> None:
        new_val = self._map_value_to_state(value)
        if self._attr_current_option == new_val:
            return
        self._attr_current_option = new_val
        self.schedule_update_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        assert self._metric.enum_values is not None
        if option not in self._metric.enum_values:
            _LOGGER.info("Setting switch %s to %s failed as option not supported. supported options are: %s", self._attr_unique_id, option, self._metric.enum_values)
            return
        _LOGGER.info("Setting switch %s to %s", self._attr_unique_id, option)
        assert isinstance(self._metric, VictronVenusWritableMetric)
        self._metric.set(option)
        self.async_write_ha_state()

    def _map_value_to_state(self, value) -> str:
        """Map metric value to switch state."""
        #for now jut return the same thing
        return str(value)
