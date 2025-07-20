from typing import List
import logging

from homeassistant.core import HomeAssistant
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

from .const import CONF_INSTALLATION_ID, CONF_MODEL, CONF_SERIAL, DOMAIN, CONF_ROOT_TOPIC_PREFIX
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
        _LOGGER.info("Initializing hub. ConfigEntry: %s", entry)
        self.hass = hass
        self.entry = entry
        self.id = entry.unique_id

        config = entry.data
        self._hub = VictronVenusHub(
            host=config.get(CONF_HOST),
            port=config.get(CONF_PORT, 1883),
            username=config.get(CONF_USERNAME),
            password=config.get(CONF_PASSWORD),
            use_ssl=config.get(CONF_SSL),
            installation_id=config.get(CONF_INSTALLATION_ID),
            model_name = config.get(CONF_MODEL),
            serial = config.get(CONF_SERIAL),
            topic_prefix = config.get(CONF_ROOT_TOPIC_PREFIX),
        )

    async def start(self):
        try:
            await self._hub.connect()
        except CannotConnectError as connect_error:
            _LOGGER.error("Cannot connect to the hub")
            raise ConfigEntryNotReady("Device is offline") from connect_error

    async def stop(self):
        await self._hub.disconnect()

    @staticmethod
    def _map_device_info(device: VictronVenusDevice) -> DeviceInfo:
        info: DeviceInfo = {}
        info["identifiers"] = {(DOMAIN, device.unique_id)}
        info["manufacturer"] = device.manufacturer if device.manufacturer is not None else "Victron Energy"
        info["name"] = f"{device.name} (ID: {device.device_id})" if device.device_id != "0" else device.name
        info["model"] = device.model
        info["serial_number"] = device.serial_number

        return info

    def add_entities(self, async_add_entities: AddEntitiesCallback, kind: MetricKind):
        """Get all entities from the hub."""
        _LOGGER.info("Adding entities of kind: %s", kind)
        entities: List[VictronBaseEntity] = []
        for device in self._hub.devices:
            info = Hub._map_device_info(device)

            # Filter metrics that represent sensors controls
            sensor_metrics = [m for m in device.metrics if m.metric_kind == kind]
            if not sensor_metrics:
                continue

            _LOGGER.info("Setting up entities for device: %s. info: %s", device, info)
            for metric in sensor_metrics:
                _LOGGER.debug("Setting up entity: %s", repr(metric))
                sensor = self.creatre_entity(device, metric, info)
                entities.append(sensor)

        if entities:
            async_add_entities(entities)
            for entity in entities:
                entity.mark_registered_with_homeassistant()


    def creatre_entity(self, device: VictronVenusDevice, metric: VictronVenusMetric, info: DeviceInfo) -> VictronBaseEntity:
        """Create a VictronBaseEntity from a device and metric."""
        if metric.metric_kind == MetricKind.SENSOR:
            return VictronSensor(device, metric, info)
        elif metric.metric_kind == MetricKind.BINARY_SENSOR:
            return VictronBinarySensor(device, metric, info)
        assert isinstance(metric, VictronVenusSwitch), f"Expected metric to be a VictronVenusSwitch. Got {type(metric)}"
        if metric.metric_kind == MetricKind.SWITCH:
            return VictronSwitch(device, metric, info)
        elif metric.metric_kind == MetricKind.NUMBER:
            return VictronNumber( device, metric, info)
        elif metric.metric_kind == MetricKind.SELECT:
            return VictronSelect(device, metric, info)
        else:
            raise ValueError(f"Unsupported metric kind: {metric.metric_kind}")


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
    ) -> None:
        """Initialize the switch."""
        self._attr_is_on = switch.value 
        super().__init__(device, switch, device_info, "switch")

    def __repr__(self) -> str:
        """Return a string representation of the sensor."""
        return (
            f"VictronSwitch({super().__repr__()}, is_on={self._attr_is_on})"
        )

    async def _on_update_task(self, metric: VictronVenusMetric):
        self._attr_is_on = metric.value == GenericOnOff.On
        self.async_write_ha_state()

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        assert isinstance(self._metric, VictronVenusSwitch)
        self._metric.set(GenericOnOff.On)
        self.async_write_ha_state()

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        assert isinstance(self._metric, VictronVenusSwitch)
        self._metric.set(GenericOnOff.On)
        self.async_write_ha_state()

class VictronNumber(VictronBaseEntity, NumberEntity):
    """Implementation of a Victron Venus number entity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        switch: VictronVenusSwitch,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the number entity."""
        self._attr_native_value = switch.value
        if isinstance(switch.min_value, int) or isinstance(switch.min_value, float):
            self._attr_native_min_value = switch.min_value
        if isinstance(switch.max_value, int) or isinstance(switch.max_value, float):
            self._attr_native_max_value = switch.max_value
        self._attr_native_step = 1 #TODO: Add support for different steps
        super().__init__(device, switch, device_info, "number")

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
    ) -> None:
        """Initialize the switch."""
        self._attr_options = switch.enum_values
        self._attr_current_option = self._map_value_to_state(switch.value)
        super().__init__(device, switch, device_info, "select")

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

    def _map_value_to_state(self, value) -> str:
        """Map metric value to switch state."""
        #for now jut return the same thing
        return str(value)
