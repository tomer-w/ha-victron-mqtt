"""Constants for the victron venus OS client."""

from dataclasses import dataclass
from enum import Enum
from typing import Self

TOPIC_INSTALLATION_ID = "N/+/system/0/Serial"


class MetricKind(Enum):
    """Type of MQTT message."""

    ATTRIBUTE = "attribute"
    SENSOR = "sensor"
    BINARY_SENSOR = "binary_sensor"
    SWITCH = "switch"
    SELECT = "select"
    NUMBER = "number"
    SERVICE = "service"
    BUTTON = "button"
    TIME = "time"
    DEVICE_TRACKER = "device_tracker"
    DYNAMIC = "dynamic"


class MetricNature(Enum):
    """Nature of the metric."""

    NONE = "none"
    MEASUREMENT = "measurement"
    TOTAL = "total"
    TOTAL_INCREASING = "total_increasing"


class MetricType(Enum):
    """The type of metric."""

    NONE = "none"
    ENUM = "enum"
    POWER = "power"
    APPARENT_POWER = "apparent_power"
    ENERGY = "energy"
    VOLTAGE = "voltage"
    CURRENT = "current"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    DISTANCE = "distance"
    FREQUENCY = "frequency"
    POWER_FACTOR = "power_factor"
    TIME = "time"
    DURATION = "duration"
    PERCENTAGE = "percentage"
    ELECTRIC_STORAGE_CAPACITY = "electric_storage_capacity"
    ELECTRIC_STORAGE_PERCENTAGE = "electric_storage_percentage"
    LIQUID_VOLUME = "liquid_volume"
    LOCATION = "location"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    ALTITUDE = "altitude"
    HEADING = "heading"
    SPEED = "speed"
    COST = "cost"
    IRRADIANCE = "irradiance"
    DYNAMIC = "dynamic"
    PROBLEM = "problem"
    CONNECTIVITY = "connectivity"
    RESTART = "restart"
    LOW_BATTERY = "low_battery"


class ValueType(Enum):
    """Value types."""

    INT = "int"
    INT_DEFAULT_0 = "int_0"
    FLOAT = "float"
    STRING = "str"
    ENUM = "enum"
    BITMASK = "bitmask"
    EPOCH = "epoch"
    INT_SECONDS_TO_HOURS = "int_seconds_to_hours"
    INT_SECONDS_TO_MINUTES = "int_seconds_to_minutes"
    FLOAT_M3_TO_LITERS = "float_m3_to_liters"
    GPS_LOCATION = "gps_location"


class RangeType(Enum):
    """Range types for numeric values."""

    STATIC = "static"  # Static range, e.g., fixed values
    DYNAMIC = "dynamic"  # Dynamic range, e.g., depends on device model


class OperationMode(Enum):
    """Enum for operation modes."""

    READ_ONLY = "read_only"
    FULL = "full"
    EXPERIMENTAL = "experimental"


@dataclass
class FormulaTransientState:
    """Transient state for formula metrics."""


PLACEHOLDER_PHASE = "{phase}"
PLACEHOLDER_NEXT_PHASE = "{next_phase}"

BITMASK_SEPARATOR = ","


class VictronEnum(Enum):
    """Base class for Victron Enums with code and string representation."""

    def __init__(self, code: int | str, enum_id: str, string: str):
        self._value_ = (code, string)
        self.code = code
        self.id = enum_id
        self.string = string

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}(code={self.code}, id={self.id}, string={self.string})"

    def __str__(self) -> str:
        return self.string

    @classmethod
    def _build_code_lookup(cls):
        if not hasattr(cls, "_lookup_by_code"):
            cls._lookup_by_code = {member.code: member for member in cls}
        return cls._lookup_by_code

    @classmethod
    def from_code(cls: type[Self], value: int | str, default_value: "VictronEnum | None" = None) -> Self | None:
        """Get enum member from its code representation."""
        lookup = cls._build_code_lookup()
        result = lookup.get(value, default_value)
        return result  # type: ignore[return-value]

    @classmethod
    def _build_string_lookup(cls):
        if not hasattr(cls, "_lookup_by_string"):
            cls._lookup_by_string = {member.string: member for member in cls}
        return cls._lookup_by_string

    @classmethod
    def from_string(cls: type[Self], value: str) -> Self:
        """Get enum member from its string representation."""
        lookup = cls._build_string_lookup()
        result = lookup.get(value)
        if result is None:
            raise ValueError(f"No enum member found with string={value}")
        return result

    @classmethod
    def _build_id_lookup(cls):
        if not hasattr(cls, "_lookup_by_id"):
            cls._lookup_by_id = {member.id: member for member in cls}
        return cls._lookup_by_id

    @classmethod
    def from_id(cls: type[Self], value: str) -> Self:
        """Get enum member from its ID representation."""
        lookup = cls._build_id_lookup()
        result = lookup.get(value)
        if result is None:
            raise ValueError(f"No enum member found with id={value}")
        return result

    @classmethod
    def from_id_or_string(cls: type[Self], value: str) -> Self:
        """Get enum member from its ID or string representation."""
        lookup = cls._build_id_lookup()
        result = lookup.get(value)
        if result is not None:
            return result
        lookup = cls._build_string_lookup()
        result = lookup.get(value)
        if result is not None:
            return result
        raise ValueError(f"No enum member found with id or string={value}")


class VictronDeviceEnum(VictronEnum):
    """Base class for Victron Enums that may map to other enum values."""

    def __init__(self, code: str, enum_id: str, string: str, mapped_to: str | None = None):
        super().__init__(code, enum_id, string)
        self.mapped_to = mapped_to

    @classmethod
    def from_code(cls: type[Self], value: int | str, default_value: "VictronEnum | None" = None) -> Self | None:
        """Get enum member from its device code representation, following mappings if necessary."""
        result = super().from_code(value, default_value)
        if result is None:
            return None
        assert isinstance(result, cls)
        if result.mapped_to:
            mapped_result = super().from_code(result.mapped_to, default_value)
            if mapped_result is None:
                return None
            assert isinstance(mapped_result, cls)
            result = mapped_result
        return result
