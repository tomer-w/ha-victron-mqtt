"""Logic for handling Victron devices, and routing updates to the appropriate metrics."""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._unwrappers import (
    VALUE_TYPE_UNWRAPPER,
    unwrap_bitmask,
    unwrap_bool,
    unwrap_enum,
    unwrap_float,
    unwrap_float_m3_to_liters,
    unwrap_int_seconds_to_hours,
    unwrap_int_seconds_to_minutes,
)
from ._victron_enums import SwitchableOutputType
from .constants import MetricKind, OperationMode, RangeType, VictronEnum
from .data_classes import ParsedTopic, TopicDescriptor
from .formula_metric import FormulaMetric
from .metric import Metric
from .writable_formula_metric import WritableFormulaMetric
from .writable_metric import WritableMetric

if TYPE_CHECKING:
    from collections.abc import Callable

    from ._victron_enums import DeviceType
    from .hub import Hub

_LOGGER = logging.getLogger(__name__)


class Device:
    """Class to represent a Victron device."""

    def __init__(
        self,
        unique_id: str,
        parsed_topic: ParsedTopic,
        descriptor: TopicDescriptor,
        *,
        parent_device: Device | None = None,
    ) -> None:
        """Initialize."""
        self._descriptor = descriptor
        self._unique_id = unique_id
        self._metrics: dict[str, Metric] = {}
        self._device_type = parsed_topic.device_type
        self._device_id = parsed_topic.device_id
        self._installation_id = parsed_topic.installation_id
        self._model = None
        self._manufacturer = None
        self._serial_number = None
        self._firmware_version = None
        self._custom_name = None
        self._parent_device: Device | None = parent_device

        _LOGGER.debug(
            "Device %s initialized (parent=%s)", self._unique_id, parent_device.unique_id if parent_device else None
        )

    def __repr__(self) -> str:
        """Return a string representation of the device."""
        return (
            f"Device(full_unique_id={self.unique_id}, "
            f"name={self.name}, "
            f"model={self.model}, "
            f"manufacturer={self.manufacturer}, "
            f"serial_number={self.serial_number}, "
            f"device_type={self.device_type}, "
            f"device_id={self.device_id}, "
            f"firmware_version={self.firmware_version}, "
            f"custom_name={self.custom_name}, "
            f"parent_device={self._parent_device.unique_id if self._parent_device else None})"
        )

    def _set_device_property_from_topic(
        self,
        topic_desc: TopicDescriptor,
        payload: str,
    ) -> None:
        """Set a device property from a topic."""
        short_id = topic_desc.short_id
        value = Device._unwrap_payload(topic_desc, payload)

        if value is None:
            _LOGGER.debug("Ignoring empty/None payload for device %s property %s", self.unique_id, short_id)
            return
        value = str(value)

        _LOGGER.debug("Setting device %s property %s = %s", self.unique_id, short_id, value)

        if short_id == "victron_productid":
            return  # ignore for now

        if short_id == "model":
            self._model = value
        elif short_id == "serial_number":
            self._serial_number = value
        elif short_id == "manufacturer":
            self._manufacturer = value
        elif short_id == "firmware_version":
            self._firmware_version = value
        elif short_id == "custom_name":
            self._custom_name = value
        else:
            _LOGGER.warning("Unhandled device property %s for %s", short_id, self.unique_id)

    def handle_message(
        self,
        fallback_to_metric_topic: bool,
        topic: str,
        parsed_topic: ParsedTopic,
        topic_desc: TopicDescriptor,
        payload: str,
        log_debug: Callable[..., None],
    ) -> MetricPlaceholder | FallbackPlaceholder | None:
        """Handle a message."""
        log_debug("Handling message for device %s: topic=%s", self.unique_id, parsed_topic)

        if topic_desc.message_type == MetricKind.ATTRIBUTE:
            self._set_device_property_from_topic(topic_desc, payload)
            return None

        parsed_topic.finalize_topic_fields(topic_desc, device_unique_id=self._unique_id)
        if fallback_to_metric_topic:
            value = unwrap_bool(payload)
            if value is None:
                log_debug(
                    "Ignoring null fallback_to_metric_topic value for device %s metric %s",
                    self.unique_id,
                    topic_desc.short_id,
                )
                return None
            return FallbackPlaceholder(device=self, parsed_topic=parsed_topic, topic_descriptor=topic_desc, value=value)
        value = Device._unwrap_payload(topic_desc, payload)
        if value is None:
            log_debug("Ignoring null topic value for device %s metric %s", self.unique_id, topic_desc.short_id)
            return None

        metric = self._metrics.get(parsed_topic.short_id)
        if metric:
            metric._handle_message(value, log_debug)
            return None
        assert value is not None, f"Value must not be None. topic={topic}, payload={payload}"
        return MetricPlaceholder(self, parsed_topic, topic_desc, payload, value)

    @staticmethod
    def _unwrap_payload(topic_desc: TopicDescriptor, payload: str) -> str | float | int | bool | VictronEnum | None:
        assert topic_desc.value_type is not None
        unwrapper = VALUE_TYPE_UNWRAPPER[topic_desc.value_type]
        if unwrapper in [unwrap_enum, unwrap_bitmask]:
            return unwrapper(payload, topic_desc.enum)
        if unwrapper in [
            unwrap_float,
            unwrap_int_seconds_to_hours,
            unwrap_int_seconds_to_minutes,
            unwrap_float_m3_to_liters,
        ]:
            return unwrapper(payload, topic_desc.precision)
        return unwrapper(payload)

    @staticmethod
    def _is_same_adjustable_topics(topic: str, adjustable_topic: str) -> bool:
        """Check if two topics are the same, considering adjustable suffixes."""
        return topic.rsplit("/", 1)[0] == adjustable_topic.rsplit("/", 1)[0]

    def _create_metric_from_placeholder(
        self, metric_placeholder: MetricPlaceholder, fallback_placeholders: list[FallbackPlaceholder], hub: Hub
    ) -> Metric:
        _LOGGER.info("Creating new metric on device: %s", metric_placeholder)

        new_topic_desc = metric_placeholder.topic_descriptor

        if new_topic_desc.is_adjustable_suffix:
            # If the topic is adjustable, we need to decide if it should be writable or not.
            # If there is a fallback placeholder for the same adjustable topic, and its value is False,
            # then we switch the topic to read-only (sensor).
            _LOGGER.info("Topic %s is adjustable", new_topic_desc.topic)
            fallback_placeholder = next(
                (
                    fp
                    for fp in fallback_placeholders
                    if Device._is_same_adjustable_topics(
                        fp.parsed_topic.full_topic, metric_placeholder.parsed_topic.full_topic
                    )
                ),
                None,
            )
            if fallback_placeholder and not fallback_placeholder.value:
                _LOGGER.info("Switching topic from writable to read-only. topic=%s", new_topic_desc.topic)
                new_topic_desc = copy.deepcopy(new_topic_desc)  # Deep copy
                new_topic_desc.message_type = MetricKind.SENSOR

        # Handle READ_ONLY mode: resolve writable types to read-only equivalents
        if hub._operation_mode == OperationMode.READ_ONLY and new_topic_desc.message_type in [
            MetricKind.SWITCH,
            MetricKind.NUMBER,
            MetricKind.SELECT,
            MetricKind.BUTTON,
            MetricKind.TIME,
            MetricKind.DYNAMIC,
        ]:
            if new_topic_desc.message_type == MetricKind.DYNAMIC:
                # DYNAMIC resolves based on output_type:
                # DROPDOWN → SENSOR (read-only SELECT), DIMMABLE → SENSOR (read-only NUMBER), else → BINARY_SENSOR
                assert new_topic_desc.output_type is not None
                assert isinstance(new_topic_desc.output_type, str)
                parts = new_topic_desc.output_type.split(":")
                dep_id = ParsedTopic.replace_ids(parts[0], metric_placeholder.parsed_topic.key_values)
                type_metric_id = ParsedTopic.make_unique_id(self._unique_id, dep_id)
                type_metric = hub._all_metrics.get(type_metric_id)
                if type_metric and type_metric.value in (SwitchableOutputType.DROPDOWN, SwitchableOutputType.DIMMABLE):
                    resolved_kind = MetricKind.SENSOR
                else:
                    resolved_kind = MetricKind.BINARY_SENSOR
            elif new_topic_desc.message_type == MetricKind.SWITCH:
                resolved_kind = MetricKind.BINARY_SENSOR
            else:
                resolved_kind = MetricKind.SENSOR
            new_topic_desc = copy.deepcopy(new_topic_desc)
            new_topic_desc.message_type = resolved_kind

        # Handle dynamic min/max range
        if new_topic_desc.min_max_range == RangeType.DYNAMIC:
            max_value = unwrap_float(metric_placeholder.payload, new_topic_desc.precision, "max")
            if max_value is not None:
                _LOGGER.info("Setting dynamic max value to %s for %s", max_value, new_topic_desc)
                new_topic_desc = copy.deepcopy(new_topic_desc)  # Deep copy
                new_topic_desc.max = int(max_value)

            min_value = unwrap_float(metric_placeholder.payload, new_topic_desc.precision, "min")
            if min_value is not None:
                _LOGGER.info("Setting dynamic min value to %s for %s", min_value, new_topic_desc)
                new_topic_desc = copy.deepcopy(new_topic_desc)  # Deep copy
                new_topic_desc.min = int(min_value)

        assert metric_placeholder.topic_descriptor.name is not None
        name = ParsedTopic.replace_ids(
            metric_placeholder.topic_descriptor.name, metric_placeholder.parsed_topic.key_values
        )
        assert metric_placeholder.parsed_topic.device_type is not None, "device_type must be set for metric"

        if new_topic_desc.message_type in [
            MetricKind.SWITCH,
            MetricKind.NUMBER,
            MetricKind.SELECT,
            MetricKind.BUTTON,
            MetricKind.TIME,
            MetricKind.DYNAMIC,
        ]:
            metric = WritableMetric(
                device=self,
                name=name,
                descriptor=new_topic_desc,
                unique_id=metric_placeholder.parsed_topic.unique_id,
                display_id=metric_placeholder.parsed_topic.display_id,
                short_id=metric_placeholder.parsed_topic.short_id,
                key_values=metric_placeholder.parsed_topic.key_values,
                topic=metric_placeholder.parsed_topic.full_topic,
                hub=hub,
            )
        else:
            metric = Metric(
                device=self,
                name=name,
                descriptor=new_topic_desc,
                unique_id=metric_placeholder.parsed_topic.unique_id,
                display_id=metric_placeholder.parsed_topic.display_id,
                short_id=metric_placeholder.parsed_topic.short_id,
                key_values=metric_placeholder.parsed_topic.key_values,
                hub=hub,
            )
        metric._handle_message(metric_placeholder.value, _LOGGER.debug)
        self._metrics[metric.short_id] = metric
        return metric

    def _add_formula_metric(self, topic_desc: TopicDescriptor, hub: Hub, key_values: dict[str, str]) -> FormulaMetric:
        assert topic_desc.name is not None, "name must be set for topic"
        name = ParsedTopic.replace_ids(topic_desc.name, key_values)
        short_id = ParsedTopic.replace_ids(topic_desc.short_id, key_values)
        unique_id = ParsedTopic.make_unique_id(self.unique_id, short_id)
        if topic_desc.message_type in [
            MetricKind.SWITCH,
            MetricKind.NUMBER,
            MetricKind.SELECT,
            MetricKind.BUTTON,
            MetricKind.TIME,
        ]:
            metric = WritableFormulaMetric(
                device=self,
                name=name,
                descriptor=topic_desc,
                unique_id=unique_id,
                short_id=short_id,
                hub=hub,
                key_values=key_values,
            )
        else:
            metric = FormulaMetric(
                device=self,
                name=name,
                descriptor=topic_desc,
                unique_id=unique_id,
                short_id=short_id,
                hub=hub,
                key_values=key_values,
            )
        self._metrics[metric.short_id] = metric
        return metric

    def get_metric(self, short_id: str) -> Metric | WritableMetric | None:
        """Get a metric from a short id. Returns None for hidden metrics."""
        metric = self._metrics.get(short_id)
        if metric is not None and metric._descriptor.hidden:
            return None
        return metric

    @property
    def metrics(self) -> list[Metric | WritableMetric]:
        """Returns the list of visible metrics on this device."""
        return [m for m in self._metrics.values() if not m._descriptor.hidden]

    @property
    def unique_id(self) -> str:
        """Return the unique id of the device."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name of the device."""
        if self._custom_name:
            return self._custom_name

        name = self.model or self.device_type.string
        if self._device_id != "0":
            name += f" (ID: {self._device_id})"
        return name

    @property
    def model(self) -> str | None:
        """Return the model of the device."""
        return self._model

    @property
    def manufacturer(self) -> str | None:
        """Return the manufacturer of the device."""
        return self._manufacturer

    @property
    def serial_number(self) -> str | None:
        """Return the serial number of the device."""
        return self._serial_number

    @property
    def device_type(self) -> DeviceType:
        """Return the device type."""
        return self._device_type

    @property
    def firmware_version(self) -> str | None:
        """Return the firmware version of the device."""
        return self._firmware_version

    @property
    def device_id(self) -> str:
        """Return the device id of the device."""
        return self._device_id

    @property
    def custom_name(self) -> str | None:
        """Return the custom name for devices."""
        return self._custom_name

    @property
    def parent_device(self) -> Device | None:
        """Return the nearest ancestor with visible metrics.

        Skips empty intermediate parents (e.g. a switch device whose only
        purpose is to group SwitchableOutput sub-devices).  The root device
        (one with no parent itself) is never skipped.
        """
        parent = self._parent_device
        while parent is not None and not parent.metrics and parent._parent_device is not None:
            parent = parent._parent_device
        return parent


@dataclass
class MetricPlaceholder:
    """Placeholder for a metric that needs to be created."""

    device: Device
    parsed_topic: ParsedTopic
    topic_descriptor: TopicDescriptor
    payload: str
    value: str | float | int | bool | VictronEnum

    def __repr__(self) -> str:
        return f"MetricPlaceholder(device={self.device}, parsed_topic={self.parsed_topic}, topic_descriptor={self.topic_descriptor}, payload={self.payload}, value={self.value})"


@dataclass
class FallbackPlaceholder:
    """Placeholder for a fallback metric that needs to be created."""

    device: Device
    parsed_topic: ParsedTopic
    topic_descriptor: TopicDescriptor
    value: str | float | int | bool | VictronEnum

    def __repr__(self) -> str:
        return f"FallbackPlaceholder(device={self.device}, parsed_topic={self.parsed_topic}, topic_descriptor={self.topic_descriptor}, value={self.value})"
