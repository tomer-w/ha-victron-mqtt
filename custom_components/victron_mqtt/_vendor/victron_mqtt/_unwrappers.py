"""Functions to unwrap the data from the JSON string."""

import json
from collections.abc import Iterable
from datetime import UTC, datetime

from .constants import BITMASK_SEPARATOR, ValueType, VictronEnum


def unwrap_bool(json_str: str) -> bool | None:
    """Unwrap a boolean value from a JSON string."""
    try:
        data = json.loads(json_str)
        if data["value"] is None:
            return None
        return bool(data["value"])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


def unwrap_int(json_str: str) -> int | None:
    """Unwrap an integer value from a JSON string."""
    try:
        data = json.loads(json_str)
        if data["value"] is None:
            return None
        return int(data["value"])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


def unwrap_int_default_0(json_str: str) -> int:
    """Unwrap an integer value from a JSON string, defaulting to 0."""
    try:
        data = json.loads(json_str)
        if data["value"] is None:
            return 0
        return int(data["value"])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return 0


def unwrap_int_seconds_to_hours(json_str: str, precision: int | None) -> float | None:
    """Convert seconds to hours."""
    seconds = unwrap_int(json_str)
    if seconds is None:
        return None
    hours = seconds / 3600
    return hours if precision is None else round(hours, precision)


def unwrap_int_seconds_to_minutes(json_str: str, precision: int | None) -> float | None:
    """Convert seconds to minutes."""
    seconds = unwrap_int(json_str)
    if seconds is None:
        return None
    minutes = seconds / 60
    return minutes if precision is None else round(minutes, precision)


def unwrap_float(json_str: str, precision: int | None, json_value: str = "value") -> float | None:
    """Unwrap a float value from a JSON string."""
    try:
        data = json.loads(json_str)
        if data.get(json_value) is None:
            return None
        value = float(data[json_value])
        return value if precision is None else round(value, precision)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


def unwrap_float_m3_to_liters(json_str: str, precision: int | None) -> float | None:
    """Convert cubic meters to liters."""
    value = unwrap_float(json_str, None)
    if value is None:
        return None
    liters = value * 1000
    return liters if precision is None else round(liters, precision)


def unwrap_string(json_str: str) -> str | None:
    """Unwrap a string value from a JSON string."""
    try:
        data = json.loads(json_str)
        if data["value"] is None:
            return None
        return str(data["value"])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


def unwrap_enum(json_str: str, enum: type[VictronEnum]) -> VictronEnum | None:
    """Unwrap a string value from a JSON string."""
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None
    val = data["value"]
    return enum.from_code(val) if val is not None else None


def unwrap_bitmask(json_str: str, enum: type[VictronEnum]) -> str | None:
    """Unwrap a bitmask value from a JSON string."""
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None
    val = data["value"]
    if val is None:
        return None
    vals = [2**idx for idx, bit in enumerate(bin(val)[:1:-1]) if int(bit)] if int(val) > 0 else [0]
    enums = [enum.from_code(v) for v in vals]
    return str.join(BITMASK_SEPARATOR, [e.string for e in enums if e is not None])


def unwrap_epoch(json_str: str) -> datetime | None:
    """Unwrap a timestamp value from a JSON string."""
    try:
        data = json.loads(json_str)
        if data["value"] is None:
            return None
        value = data["value"]
        return datetime.fromtimestamp(value, tz=UTC)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


def unwrap_epoch_default_na(json_str: str) -> datetime | str:
    """Unwrap an integer value from a JSON string, defaulting to 0."""
    try:
        data = json.loads(json_str)
        if data["value"] is None:
            return "N/A"
        return datetime.fromtimestamp(data["value"], tz=UTC)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return "N/A"


def wrap_enum(enum_val: VictronEnum | str, enum_expected: type[VictronEnum]) -> str:
    """Wrap an Enum value into a JSON string with a 'value' key."""
    if isinstance(enum_val, VictronEnum):
        return json.dumps({"value": enum_val.code})
    return json.dumps({"value": enum_expected.from_id_or_string(enum_val).code})


def wrap_bitmask(
    bitmask_val: VictronEnum | str | Iterable[VictronEnum] | Iterable[str], enum_expected: type[VictronEnum]
) -> str:
    """Wrap an bitmask value into a JSON string with a 'value' key."""
    if isinstance(bitmask_val, VictronEnum):
        bitmask_val = [bitmask_val]
    elif isinstance(bitmask_val, str):
        bitmask_val = bitmask_val.split(BITMASK_SEPARATOR)

    val: int = 0x00
    for v in bitmask_val:
        if isinstance(v, VictronEnum):
            val += int(v.code)
        else:
            val += int(enum_expected.from_id_or_string(v).code)
    return json.dumps({"value": val})


def wrap_int(value: int | float | None) -> str:
    """Wrap an integer value into a JSON string with a 'value' key."""
    return json.dumps({"value": int(value) if value is not None else None})


def wrap_int_hours_to_seconds(value: int | float | None) -> str:
    """Wrap an integer value into a JSON string with a 'value' key."""
    return json.dumps({"value": int(value) * 3600 if value is not None else None})


def wrap_int_minutes_to_seconds(value: int | float | None) -> str:
    """Wrap an integer value into a JSON string with a 'value' key."""
    return json.dumps({"value": int(value) * 60 if value is not None else None})


def wrap_int_default_0(value: int | float | None) -> str:
    """Wrap an integer value into a JSON string with a 'value' key, defaulting to 0 if None."""
    return json.dumps({"value": int(value) if value is not None else 0})


def wrap_float(value: float | None) -> str:
    """Wrap a float value into a JSON string with a 'value' key."""
    return json.dumps({"value": value})


def wrap_string(value: str | None) -> str:
    """Wrap a string value into a JSON string with a 'value' key."""
    return json.dumps({"value": value})


def wrap_epoch(value: datetime | None) -> str:
    """Wrap a datetime value into a JSON string with a 'value' key in the format of an epoch timestamp."""
    if value is None:
        return json.dumps({"value": None})
    return json.dumps({"value": datetime.timestamp(value)})


VALUE_TYPE_UNWRAPPER = {
    ValueType.INT: unwrap_int,
    ValueType.INT_DEFAULT_0: unwrap_int_default_0,
    ValueType.FLOAT: unwrap_float,
    ValueType.STRING: unwrap_string,
    ValueType.ENUM: unwrap_enum,
    ValueType.BITMASK: unwrap_bitmask,
    ValueType.EPOCH: unwrap_epoch,
    ValueType.EPOCH_DEFAULT_NA: unwrap_epoch_default_na,
    ValueType.INT_SECONDS_TO_HOURS: unwrap_int_seconds_to_hours,
    ValueType.INT_SECONDS_TO_MINUTES: unwrap_int_seconds_to_minutes,
    ValueType.FLOAT_M3_TO_LITERS: unwrap_float_m3_to_liters,
}

VALUE_TYPE_WRAPPER = {
    ValueType.INT: wrap_int,
    ValueType.INT_DEFAULT_0: wrap_int_default_0,
    ValueType.FLOAT: wrap_float,
    ValueType.STRING: wrap_string,
    ValueType.ENUM: wrap_enum,
    ValueType.BITMASK: wrap_bitmask,
    ValueType.EPOCH: wrap_epoch,
    ValueType.INT_SECONDS_TO_HOURS: wrap_int_hours_to_seconds,
    ValueType.INT_SECONDS_TO_MINUTES: wrap_int_minutes_to_seconds,
}
