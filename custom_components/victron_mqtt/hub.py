from typing import Any, List
import logging

from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.number import NumberEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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
    Switch as VictronVenusSwitch,
    Device as VictronVenusDevice,
    MetricKind,
    GenericOnOff
)

from .const import CONF_INSTALLATION_ID, CONF_MODEL, CONF_SERIAL, CONF_UPDATE_FREQUENCY_SECONDS, DEFAULT_UPDATE_FREQUENCY_SECONDS, DOMAIN, CONF_ROOT_TOPIC_PREFIX
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
        )
        self._hub.on_new_metric = self.on_new_metric
        self.update_frequency_seconds = config.get(CONF_UPDATE_FREQUENCY_SECONDS, DEFAULT_UPDATE_FREQUENCY_SECONDS)
        self.add_entities_map: dict[MetricKind, AddEntitiesCallback] = {}

        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.stop)

    async def start(self):
        _LOGGER.info("Starting hub. Update frequency: %s seconds", self.update_frequency_seconds)
        try:
            await self._hub.connect()
        except CannotConnectError as connect_error:
            _LOGGER.error("Cannot connect to the hub")
            raise ConfigEntryNotReady("Device is offline") from connect_error

    @callback
    async def stop(self, event: Event):
        _LOGGER.info("Stopping hub")
        await self._hub.disconnect()

    def on_new_metric(self, hub: VictronVenusHub, device: VictronVenusDevice, metric: VictronVenusMetric):
        _LOGGER.info("New metric received. Hub: %s, Device: %s, Metric: %s", hub, device, metric)
        device_info = Hub._map_device_info(device)
        entity = self.creatre_entity(device, metric, device_info)
        # Add entity dynamically to the platform
        self.add_entities_map[metric.metric_kind]([entity])
        entity.mark_registered_with_homeassistant()

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
            return VictronSensor(device, metric, info, self.update_frequency_seconds)
        elif metric.metric_kind == MetricKind.BINARY_SENSOR:
            return VictronBinarySensor(device, metric, info, self.update_frequency_seconds)
        assert isinstance(metric, VictronVenusSwitch), f"Expected metric to be a VictronVenusSwitch. Got {type(metric)}"
        if metric.metric_kind == MetricKind.SWITCH:
            return VictronSwitch(device, metric, info, self.update_frequency_seconds)
        elif metric.metric_kind == MetricKind.NUMBER:
            return VictronNumber(device, metric, info, self.update_frequency_seconds)
        elif metric.metric_kind == MetricKind.SELECT:
            return VictronSelect(device, metric, info, self.update_frequency_seconds)
        else:
            raise ValueError(f"Unsupported metric kind: {metric.metric_kind}")


class VictronSensor(VictronBaseEntity, SensorEntity):
    """Implementation of a Victron Venus sensor."""

    def __init__(
        self,
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
        update_frequency_seconds: int,
    ) -> None:
        """Initialize the sensor based on detauls in the metric."""
        self._attr_native_value = metric.value
        super().__init__(device, metric, device_info, "sensor", update_frequency_seconds)

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronSensor({super().__repr__()})"

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_native_value = metric.value
        self.async_write_ha_state()


class VictronSwitch(VictronBaseEntity, SwitchEntity):
    """Implementation of a Victron Venus multiple state select using SelectEntity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        switch: VictronVenusSwitch,
        device_info: DeviceInfo,
        update_frequency_seconds: int,
    ) -> None:
        """Initialize the switch."""
        self._attr_is_on = switch.value == GenericOnOff.On
        super().__init__(device, switch, device_info, "switch", update_frequency_seconds)

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return (
            f"VictronSwitch({super().__repr__()}, is_on={self._attr_is_on})"
        )

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_is_on = metric.value == GenericOnOff.On
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        assert isinstance(self._metric, VictronVenusSwitch)
        _LOGGER.info("Turning on switch: %s", self._attr_unique_id)
        self._metric.set(GenericOnOff.On)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        assert isinstance(self._metric, VictronVenusSwitch)
        _LOGGER.info("Turning off switch: %s", self._attr_unique_id)
        self._metric.set(GenericOnOff.Off)
        self.async_write_ha_state()

class VictronNumber(VictronBaseEntity, NumberEntity):
    """Implementation of a Victron Venus number entity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        switch: VictronVenusSwitch,
        device_info: DeviceInfo,
        update_frequency_seconds: int,
    ) -> None:
        """Initialize the number entity."""
        self._attr_native_value = switch.value
        if isinstance(switch.min_value, int) or isinstance(switch.min_value, float):
            self._attr_native_min_value = switch.min_value
        if isinstance(switch.max_value, int) or isinstance(switch.max_value, float):
            self._attr_native_max_value = switch.max_value
        self._attr_native_step = 1 #TODO: Add support for different steps
        super().__init__(device, switch, device_info, "number", update_frequency_seconds)

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronNumber({super().__repr__()}, native_value={self._attr_native_value})"

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_native_value = metric.value
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the current value."""
        return self._metric.value

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        assert isinstance(self._metric, VictronVenusSwitch)
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
        update_frequency_seconds: int,
    ) -> None:
        self._attr_is_on = bool(metric.value)
        super().__init__(device, metric, device_info, "binary_sensor", update_frequency_seconds)

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronBinarySensor({super().__repr__()}), is_on={self._attr_is_on})"

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_is_on = metric.value == GenericOnOff.On
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

class VictronSelect(VictronBaseEntity, SelectEntity):
    """Implementation of a Victron Venus multiple state select using SelectEntity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        switch: VictronVenusSwitch,
        device_info: DeviceInfo,
        update_frequency_seconds: int,
    ) -> None:
        """Initialize the switch."""
        self._attr_options = switch.enum_values
        self._attr_current_option = self._map_value_to_state(switch.value)
        super().__init__(device, switch, device_info, "select", update_frequency_seconds)

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return f"VictronSelect({super().__repr__()}, current_option={self._attr_current_option}, options={self._attr_options})"

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_current_option = self._map_value_to_state(metric.value)
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        assert self._metric.enum_values is not None
        if option not in self._metric.enum_values:
            _LOGGER.info("Setting switch %s to %s failed as option not supported. supported options are: %s", self._attr_unique_id, option, self._metric.enum_values)
            return
        _LOGGER.info("Setting switch %s to %s", self._attr_unique_id, option)
        assert isinstance(self._metric, VictronVenusSwitch)
        self._metric.set(option)
        self.async_write_ha_state()

    def _map_value_to_state(self, value) -> str:
        """Map metric value to switch state."""
        #for now jut return the same thing
        return str(value)
