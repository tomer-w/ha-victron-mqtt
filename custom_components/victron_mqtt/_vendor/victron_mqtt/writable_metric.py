"""
Support for Victron Venus WritableMetric.
"""

import json
import logging
from collections.abc import Callable, Iterable
from enum import Enum
from typing import Any, cast

from ._unwrappers import VALUE_TYPE_WRAPPER, wrap_bitmask, wrap_enum
from ._victron_enums import SwitchableOutputType
from .constants import MetricKind, ValueType, VictronEnum
from .data_classes import ParsedTopic, TopicDescriptor
from .metric import Metric

_LOGGER = logging.getLogger(__name__)


class WritableMetric(Metric):
    """Representation of a Victron Venus sensor."""

    _min_value: int | float | None = None
    _max_value: int | float | None = None
    _step_value: int | float | None = None
    _unit_of_measurement: str | None = None
    _output_type: int | float | VictronEnum | None = None
    _labels: list[str] | None = None

    def __init__(self, *, descriptor: TopicDescriptor | None = None, topic: str | None = None, **kwargs: Any) -> None:
        """Initialize the WritableMetric."""
        assert descriptor is not None
        _LOGGER.debug(
            "Creating new WritableMetric: short_id=%s, type=%s, nature=%s",
            descriptor.short_id,
            descriptor.metric_type,
            descriptor.metric_nature,
        )
        self._write_topic: str | None = None
        if topic is not None:
            assert topic.startswith("N")
            self._write_topic = "W" + topic[1:]
        super().__init__(descriptor=descriptor, **kwargs)

    def __str__(self) -> str:
        return f"WritableMetric({super().__str__()}, write_topic = {self._write_topic})"

    def __repr__(self) -> str:
        return self.__str__()

    def phase2_init(self, device_id: str, all_metrics: dict[str, Metric]) -> None:
        """Phase 2 initialization of the WritableMetric."""
        super().phase2_init(device_id, all_metrics)
        self._min_value = self._resolve_range_value(self._descriptor.min, device_id, all_metrics)
        self._max_value = self._resolve_range_value(self._descriptor.max, device_id, all_metrics)
        self._step_value = self._resolve_range_value(self._descriptor.step, device_id, all_metrics)
        self._unit_of_measurement = self._resolve_string_value(
            self._descriptor.unit_of_measurement, device_id, all_metrics
        )
        self._output_type = self._resolve_range_value(self._descriptor.output_type, device_id, all_metrics)
        labels_str = self._resolve_string_value(self._descriptor.labels, device_id, all_metrics)
        if labels_str:
            try:
                parsed = json.loads(labels_str)
                self._labels = parsed if isinstance(parsed, list) else None
            except (json.JSONDecodeError, TypeError):
                self._labels = None
        else:
            self._labels = None

    def _resolve_range_value(
        self, range_value: int | float | str | None, device_id: str, all_metrics: dict[str, Metric]
    ) -> int | float | None:
        """Resolve a range value (min/max/step) that may be static or reference another metric."""
        if range_value is None:
            return None

        if not isinstance(range_value, str):
            # Static numeric value
            return range_value

        # Dynamic reference to another metric: "metric_id:default_value"
        parts = range_value.split(":")
        assert len(parts) == 2, f"Range reference must be in format 'metric_id:default_value'. Got: '{range_value}'"
        dependency_id: str = parts[0]
        default_value: int | float = float(parts[1]) if "." in parts[1] else int(parts[1])

        metric_unique_id = ParsedTopic.make_unique_id(device_id, dependency_id)
        metric_unique_id = ParsedTopic.replace_ids(metric_unique_id, self.key_values)
        ref_metric = all_metrics.get(metric_unique_id)

        if ref_metric is None:
            _LOGGER.debug(
                "Referenced metric '%s' not found for %s, using default value %s",
                metric_unique_id,
                self._descriptor.short_id,
                default_value,
            )
            return default_value

        return ref_metric.value

    def _resolve_string_value(self, value: str | None, device_id: str, all_metrics: dict[str, Metric]) -> str | None:
        """Resolve a string value that may be static or reference another metric (format: 'metric_id:default')."""
        if value is None:
            return None

        if ":" not in value:
            return value

        parts = value.split(":", 1)
        dependency_id: str = parts[0]
        default_value: str = parts[1]

        metric_unique_id = ParsedTopic.make_unique_id(device_id, dependency_id)
        metric_unique_id = ParsedTopic.replace_ids(metric_unique_id, self.key_values)
        ref_metric = all_metrics.get(metric_unique_id)

        if ref_metric is None or ref_metric.value is None:
            _LOGGER.debug(
                "Referenced metric '%s' not found for %s, using default value '%s'",
                metric_unique_id,
                self._descriptor.short_id,
                default_value,
            )
            return default_value

        return str(ref_metric.value)

    @property
    def unit_of_measurement(self) -> str | None:
        """Get the resolved unit of measurement for this metric."""
        return self._unit_of_measurement

    @property
    def min_value(self) -> int | float | None:
        """Get the minimum value for this metric, if defined."""
        return self._min_value

    @property
    def max_value(self) -> int | float | None:
        """Get the maximum value for this metric, if defined."""
        return self._max_value

    @property
    def step(self) -> float | int | None:
        """Get the step value for this metric, if defined."""
        return self._step_value

    @property
    def _is_dynamic_dropdown(self) -> bool:
        """Check if this is a DYNAMIC metric resolved to dropdown (SELECT) mode."""
        return (
            self._descriptor.message_type == MetricKind.DYNAMIC
            and self._output_type == SwitchableOutputType.DROPDOWN
            and self._labels is not None
        )

    @property
    def metric_kind(self) -> MetricKind:
        """Returns the metric kind, resolved dynamically when DYNAMIC.

        DYNAMIC is used for SwitchableOutput State, which is always on/off (0/1)
        regardless of output type. For dropdown outputs (Type=6 with labels),
        it resolves to SELECT; otherwise it stays SWITCH.

        Note: dimmable outputs (Type=2) have a separate Dimming topic that is
        hardcoded as MetricKind.NUMBER — State itself is still a switch.
        """
        if self._descriptor.message_type == MetricKind.DYNAMIC:
            if self._is_dynamic_dropdown:
                return MetricKind.SELECT
            return MetricKind.SWITCH
        return super().metric_kind

    @property
    def enum_values(self) -> list[str] | None:
        """Get the enum values. Returns labels when in dropdown mode."""
        if self._is_dynamic_dropdown:
            return self._labels
        return super().enum_values

    def set(self, value: str | float | int | bool | VictronEnum) -> None:
        """Set the value of this metric by publishing to the write topic."""
        assert self._write_topic is not None
        if self._is_dynamic_dropdown and isinstance(value, str):
            payload = json.dumps({"value": self._labels.index(value)})  # type: ignore[union-attr]
        else:
            payload = WritableMetric._wrap_payload(self._descriptor, value)
        self._hub._publish(self._write_topic, payload)

    @staticmethod
    def _wrap_payload(topic_desc: TopicDescriptor, value: str | float | int | bool | Enum) -> str:
        assert topic_desc.value_type is not None
        value_type = topic_desc.value_type

        if value_type is ValueType.ENUM:
            assert topic_desc.enum is not None, "Enum must be provided for enum value types"
            assert isinstance(value, VictronEnum | str), "Enum values must be VictronEnum or str"
            return wrap_enum(value, topic_desc.enum)

        if value_type is ValueType.BITMASK:
            assert topic_desc.enum is not None, "Enum must be provided for bitmask value types"
            assert isinstance(value, VictronEnum | str | Iterable), (
                "Bitmask values must be VictronEnum, str or iterable"
            )
            return wrap_bitmask(value, topic_desc.enum)

        wrapper = cast("Callable[[Any], str]", VALUE_TYPE_WRAPPER[value_type])
        return wrapper(value)

    @property
    def value(self):
        """Get the current value of this metric."""
        return self._value

    @value.setter
    def value(self, new_value: str | float | int | bool | VictronEnum) -> None:
        """Set a new value for this metric."""
        self.set(new_value)
