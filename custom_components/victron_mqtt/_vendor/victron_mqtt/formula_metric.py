"""
Support for Victron Venus WritableMetric.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from . import _victron_formulas as formulas
from .metric import Metric

if TYPE_CHECKING:
    from collections.abc import Callable

    from .constants import FormulaTransientState
    from .data_classes import TopicDescriptor

_LOGGER = logging.getLogger(__name__)


class FormulaMetric(Metric):
    """Representation of a Victron Venus sensor."""

    def __init__(self, *, descriptor: TopicDescriptor, **kwargs: Any) -> None:
        """Initialize the FormulaMetric."""
        _LOGGER.debug(
            "Creating new FormulaMetric: unique_id=%s, type=%s, nature=%s",
            descriptor.short_id,
            descriptor.metric_type,
            descriptor.metric_nature,
        )
        assert descriptor.is_formula, f"Metric {descriptor.short_id} is not a formula"
        self._depends_on: dict[str, Metric] = {}
        self._required_dependency_short_ids: set[str] = set()
        for dependency in descriptor.depends_on:
            short_id, required = descriptor.dependency_parts(dependency)
            if required:
                self._required_dependency_short_ids.add(short_id)
        self.transient_state: FormulaTransientState | None = None
        assert descriptor.topic.startswith("$$func")
        func_name = descriptor.topic.split("/")[-1]
        if ":" in func_name:
            func_name = func_name.split(":", 1)[0]
        self._func = getattr(formulas, func_name)

        super().__init__(descriptor=descriptor, **kwargs)

    def init(self, depends_on: dict[str, Metric], log_debug: Callable[..., None]) -> None:
        """Initialize the FormulaMetric with its dependencies."""
        self._depends_on = depends_on
        self._handle_formula(log_debug)

    def __str__(self) -> str:
        return f"FormulaMetric({super().__str__()}, transient_state={self.transient_state})"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def value(self):
        return self._value

    def _handle_formula(self, log_debug: Callable[..., None]):
        if any(
            not metric.available and metric.generic_short_id in self._required_dependency_short_ids
            for metric in self._depends_on.values()
        ):
            log_debug("Formula %s has an unavailable required dependency", self._func)
            self._handle_message(self._value, log_debug, update_last_seen=False, available=False)
            return

        available_dependencies = {
            unique_id: metric for unique_id, metric in self._depends_on.items() if metric.available
        }
        # Formula functions may return None to indicate no value/update.
        result = self._func(available_dependencies, self.transient_state)
        if result is None:
            log_debug("Formula %s returned None", self._func)
            self._handle_message(None, log_debug)
            return

        try:
            value, self.transient_state = result
        except Exception:  # pragma: no cover - defensive logging for unexpected return shapes
            _LOGGER.error("Unexpected return value from formula %s: %r", self._func, result)
            return

        if self._descriptor.precision is not None:
            value = round(value, self._descriptor.precision)
        self._handle_message(value, log_debug)
