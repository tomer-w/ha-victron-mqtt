"""
Support for Victron Venus WritableMetric.
"""

import logging
from collections.abc import Callable
from typing import Any

from . import _victron_formulas as formulas
from .constants import VictronEnum
from .data_classes import TopicDescriptor
from .formula_metric import FormulaMetric
from .writable_metric import WritableMetric

_LOGGER = logging.getLogger(__name__)


class WritableFormulaMetric(WritableMetric, FormulaMetric):
    """Representation of a Victron Venus sensor."""

    def __init__(self, *, descriptor: TopicDescriptor, **kwargs: Any) -> None:
        """Initialize the FormulaMetric."""
        _LOGGER.debug(
            "Creating new FormulaMetric: unique_id=%s, type=%s, nature=%s",
            descriptor.short_id, descriptor.metric_type, descriptor.metric_nature
        )
        assert descriptor.topic.startswith("$$func")
        func_name = descriptor.topic.split('/')[-1]
        assert ":" in func_name
        write_func_name = func_name.split(":", 1)[1]
        self._write_func = getattr(formulas, write_func_name)

        super().__init__(descriptor = descriptor, **kwargs)


    def __str__(self) -> str:
        return f"WritableFormulaMetric({super().__str__()}, transient_state={self.transient_state})"

    def __repr__(self) -> str:
        return self.__str__()

    def _keepalive(self, force_invalidate: bool, log_debug: Callable[..., None]):
        log_debug("Metric is WritableFormulaMetric so no keepalive for now: %s", self.unique_id)

    def set(self, value: str | float | int | bool | VictronEnum) -> None:
        # Determine log level based on the substring
        is_info_level = self._hub._topic_log_info and self._hub._topic_log_info in self._descriptor.topic
        log_debug = _LOGGER.info if is_info_level else _LOGGER.debug
        log_debug("Formula %s set to: %s", self._func, value)

        # Formula functions may return None to indicate no value/update.
        result = self._write_func(value, self._depends_on, self.transient_state)
        if result is None:
            log_debug("Formula %s returned None", self._func)
            self._handle_message(None, log_debug)
            return

        try:
            value, self.transient_state = result
        except Exception:  # pragma: no cover - defensive logging for unexpected return shapes
            _LOGGER.error("Unexpected return value from formula %s: %r", self._func, result)
            return
        log_debug("Formula %s returned: value=%s, transient_state=%s", self._func, value, self.transient_state)

        self._handle_message(value, log_debug)
