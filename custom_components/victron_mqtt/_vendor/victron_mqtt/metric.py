"""
Support for Victron Venus sensors. The sensor itself has no logic,
 it simply receives messages and updates its state.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .constants import MetricKind, MetricNature, MetricType, VictronEnum  # noqa: TC001
from .data_classes import ParsedTopic, TopicDescriptor
from .id_utils import replace_complex_ids

if TYPE_CHECKING:
    import re

    from .device import Device
    from .formula_metric import FormulaMetric
    from .hub import Hub

_LOGGER = logging.getLogger(__name__)

CallbackOnUpdate = Callable[["Metric", Any], None]


class Metric:
    """Representation of a Victron Venus sensor."""

    def __init__(
        self,
        *,
        device: Device | None = None,
        name: str | None = None,
        descriptor: TopicDescriptor | None = None,
        unique_id: str | None = None,
        short_id: str | None = None,
        key_values: dict[str, str] | None = None,
        hub: Hub | None = None,
    ) -> None:
        """Initialize the sensor."""
        assert device is not None
        assert name is not None
        assert descriptor is not None
        assert descriptor.name is not None, "name must be set for metric"
        assert unique_id is not None
        assert key_values is not None
        assert short_id is not None
        assert hub is not None
        _LOGGER.debug(
            "Creating new metric: short_id=%s, type=%s, nature=%s",
            short_id,
            descriptor.metric_type,
            descriptor.metric_nature,
        )
        self._device: Device = device
        self._descriptor: TopicDescriptor = descriptor
        self._unique_id: str = unique_id
        self._value: Any = None
        self._short_id: str = short_id
        self._name: str = name
        self._key_values: dict[str, str] = key_values
        self._on_update: CallbackOnUpdate | None = None
        self._depend_on_me: list[FormulaMetric] = []
        self._hub = hub
        self._last_notified: float = 0
        self._last_seen: float = 0
        self._generic_short_id = self._descriptor.short_id
        self._generic_name = self._descriptor.generic_name

        _LOGGER.debug("Metric %s initialized", repr(self))

    def __str__(self) -> str:
        """Return the string representation of the metric."""
        key_values_str = ", ".join(f"{k}={v}" for k, v in self._key_values.items())
        key_values_part = f"key_values={{{key_values_str}}}" if key_values_str else "key_values={}"
        return (
            f"Metric(unique_id={self.unique_id}, "
            f"descriptor={self._descriptor}, "
            f"value={self.value}, "
            f"short_id={self._short_id}, "
            f"name={self._name}, "
            f"{key_values_part})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def phase2_init(self, device_id: str, all_metrics: dict[str, Metric]) -> None:
        """Second phase of initializing the metric."""
        assert self._descriptor.name is not None, f"name must be set for topic: {self._descriptor.topic}"
        name_temp = ParsedTopic.replace_ids(self._descriptor.name, self._key_values)
        self._name = self._replace_ids(name_temp, device_id, all_metrics)

    def _replace_ids(self, orig_str: str, device_id: str, all_metrics: dict[str, Metric]) -> str:
        def replace_match(match: re.Match[str]) -> str:
            moniker = match.group("moniker")
            key, suffix = moniker.split(":", 1)
            assert key, f"Invalid moniker format: {moniker} in topic: {orig_str}"
            assert suffix, f"Invalid moniker format: {moniker} in topic: {orig_str}"
            metric = all_metrics.get(f"{device_id}_{suffix}")
            if metric:
                result = str(metric.value)
                self.key_values[key] = result
                return result
            return self.key_values[key]

        temp = replace_complex_ids(orig_str, replace_match)
        if temp != orig_str:
            _LOGGER.debug("Replaced complex placeholders in topic: %s", orig_str)
            return temp

        return ParsedTopic.replace_ids(orig_str, self.key_values)

    def add_dependency(self, formula_metric: FormulaMetric) -> None:
        """Add a dependency to the metric."""
        self._depend_on_me.append(formula_metric)

    def format_value(self, value: str | float | int | bool | VictronEnum | None) -> str:
        """Returns the formatted value of the metric."""
        if value is None:
            return ""
        if isinstance(value, float) and self._descriptor.precision is not None and self._descriptor.precision == 0:
            value = int(value)
        units = self.unit_of_measurement
        if units is None:
            return str(value)
        return f"{value} {units}"

    @property
    def formatted_value(self):
        """Returns the value of the metric."""
        return self.format_value(self._value)

    @property
    def value(self):
        """Returns the value of the metric."""
        return self._value

    @property
    def short_id(self) -> str:
        """Returns the short id of the metric."""
        return self._short_id

    @property
    def name(self) -> str:
        """Returns the short id of the metric."""
        assert self._name is not None, f"Metric name is None for metric: {self!r}"
        return self._name

    @property
    def generic_name(self) -> str:
        """Returns the generic name of the metric."""
        assert self._generic_name is not None, f"Metric generic_name is None for metric: {self!r}"
        return self._generic_name

    @property
    def generic_short_id(self) -> str:
        """Returns the generic short id of the metric."""
        assert self._generic_short_id is not None, f"Metric generic_short_id is None for metric: {self!r}"
        return self._generic_short_id

    @property
    def unit_of_measurement(self) -> str | None:
        """Returns the unit of measurement of the metric."""
        return self._descriptor.unit_of_measurement

    @property
    def metric_type(self) -> MetricType:
        """Returns the metric type."""
        return self._descriptor.metric_type

    @property
    def metric_nature(self) -> MetricNature:
        """Returns the metric nature."""
        return self._descriptor.metric_nature

    @property
    def metric_kind(self) -> MetricKind:
        """Returns the device type."""
        return self._descriptor.message_type

    @property
    def precision(self) -> int | None:
        """Returns the precision of the metric."""
        return self._descriptor.precision

    @property
    def main_topic(self) -> bool:
        """Returns whether the metric is the main topic for the device."""
        return self._descriptor.main_topic

    @property
    def unique_id(self) -> str:
        """Return the unique id of the metric."""
        return self._unique_id

    @property
    def key_values(self) -> dict[str, str]:
        """Return the key_values dictionary as read-only."""
        return self._key_values

    @property
    def enum_values(self) -> list[str] | None:
        """Get the enum string values for this metric, if defined."""
        return [e.id for e in self._descriptor.enum] if self._descriptor.enum else None

    @property
    def on_update(self) -> CallbackOnUpdate | None:
        """Returns the on_update callback."""
        return self._on_update

    @on_update.setter
    def on_update(self, value: CallbackOnUpdate | None) -> None:
        """Sets the on_update callback."""
        self._on_update = value

    def _keepalive(self, force_invalidate: bool, log_debug: Callable[..., None]):
        """Reset metrics value if no updates or send last values if they got skipped"""
        if force_invalidate and self._value is not None:
            log_debug("Metric %s is being forced reset", self.unique_id)
            self._handle_message(None, log_debug, update_last_seen=False)  # Dont update the last_seen as it wasnt seen
            return
        if self._last_seen > self._last_notified:
            log_debug(
                "Metric %s has been updated at %.2f but not published since %.2fs, re-publishing",
                self.unique_id,
                self._last_notified,
                self._last_seen,
            )
            self._handle_message(self._value, log_debug, update_last_seen=False, force=True)
            return
        log_debug("Metric is active and up-to-date: %s", self.unique_id)

    def _handle_message(
        self,
        value: str | float | int | bool | VictronEnum | None,
        log_debug: Callable[..., None],
        update_last_seen: bool = True,
        force: bool = False,
    ):
        """Handle a message."""
        now = time.monotonic()
        if update_last_seen:
            self._last_seen = now
        should_notify = False

        # In case of zero update frequency, always consider changed when MQTT message is received
        # also if this is the first time the metric is being notified
        if force or self._hub._update_frequency_seconds == 0 or self._last_notified == 0:
            should_notify = True
            force = True
        elif value != self._value:
            log_debug(
                "Metric %s value changed: %s -> %s %s",
                self.unique_id,
                self._value,
                value,
                self._descriptor.unit_of_measurement or "",
            )
            should_notify = True
            if self._value is None:
                log_debug("Metric updated to non-None value. forcing it. metric: %s", self.unique_id)
                force = True
        else:
            log_debug(
                "Metric %s value unchanged: %s %s", self.unique_id, value, self._descriptor.unit_of_measurement or ""
            )
        self._value = value

        # In case of non-zero update frequency, respect the update frequency limit only for numerical values
        if (
            not force
            and self._hub._update_frequency_seconds is not None
            and isinstance(value, float | int)
            and not isinstance(value, bool)  # bool is a subclass of int, but we only want real numeric sensor values.
        ):
            elapsed = now - self._last_notified
            if elapsed < self._hub._update_frequency_seconds:
                _LOGGER.debug(
                    "Update for %s skipped due to frequency limit (%.2fs < %ds)",
                    self.unique_id,
                    elapsed,
                    self._hub._update_frequency_seconds,
                )
                should_notify = False
            else:
                # This happens when the last time was before the update frequency passed so now we do really need to notify on it
                should_notify = True

        if should_notify and self._hub._loop and callable(self._on_update) and self._hub._loop.is_running():
            self._last_notified = now
            try:
                # If the event loop is running, schedule the callback
                self._hub._loop.call_soon_threadsafe(self._on_update, self, self.value)
            except Exception as exc:
                log_debug("Error calling callback %s", exc, exc_info=True)

        for dependency in self._depend_on_me:
            assert self != dependency, f"Circular dependency detected: {self}"
            dependency._handle_formula(log_debug)
