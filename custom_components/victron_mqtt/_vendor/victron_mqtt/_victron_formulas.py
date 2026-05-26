"""Victron formula implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._victron_enums import ChargeSchedule, ESSModeHub4, ESSState, ESSUserMode, GenericOnOff, PreferRenewableEnergyEnum
from .data_classes import GpsLocation
from .formula_common import left_riemann_sum_internal
from .writable_metric import WritableMetric

if TYPE_CHECKING:
    from .constants import FormulaTransientState
    from .metric import Metric


def system_dc_battery_discharge_power(
    depends_on: dict[str, Metric], transient_state: FormulaTransientState | None
) -> tuple[float, FormulaTransientState] | None:
    """Calculate the system DC battery discharge power in kWh."""

    def adjust_power_for_discharging(current_power: float) -> float:
        return 0.0 if current_power > 0 else current_power * -1 / 1000

    return left_riemann_sum_internal(depends_on, adjust_power_for_discharging, transient_state)


def system_dc_battery_charge_power(
    depends_on: dict[str, Metric], transient_state: FormulaTransientState | None
) -> tuple[float, FormulaTransientState] | None:
    """Calculate the system DC battery charge power in kWh."""

    def adjust_power_for_charging(current_power: float) -> float:
        if current_power < 0:
            current_power = 0.0  # Only consider charging power for energy accumulation
        return current_power / 1000

    return left_riemann_sum_internal(depends_on, adjust_power_for_charging, transient_state)


def left_riemann_sum(
    depends_on: dict[str, Metric], transient_state: FormulaTransientState | None
) -> tuple[float, FormulaTransientState] | None:
    """Calculate the left Riemann sum in kWh."""

    def adjust(val: float) -> float:
        return val / 1000  # Convert to kW

    return left_riemann_sum_internal(depends_on, adjust, transient_state)


def schedule_charge_enabled(
    depends_on: dict[str, Metric], _transient_state: FormulaTransientState | None
) -> tuple[GenericOnOff | None, None]:
    """Determine if schedule charge is enabled."""

    assert len(depends_on) == 1, "Expected exactly one input metric for schedule_charge_enabled"
    metric = next(iter(depends_on.values()))
    if metric.value is None:
        return None, None

    ret_val = GenericOnOff.ON if metric.value.code >= 0 else GenericOnOff.OFF
    return ret_val, None


def schedule_charge_enabled_set(
    value: str, depends_on: dict[str, Metric], _transient_state: FormulaTransientState | None
) -> tuple[GenericOnOff, None]:
    """Set schedule charge enabled state."""

    assert len(depends_on) == 1, "Expected exactly one input metric for schedule_charge_enabled"
    enabled: GenericOnOff | None = (
        value if isinstance(value, GenericOnOff) else GenericOnOff.from_id_or_string(value)
    )  # Support both the int value and the enum itself
    assert enabled is not None, "Failed to determine enabled state"
    metric = next(iter(depends_on.values()))
    assert isinstance(metric, WritableMetric), "Expected WritableMetric for schedule_charge_enabled_set"
    assert isinstance(metric.value, ChargeSchedule), "Expected ChargeSchedule for schedule_charge_enabled_set.value"
    schedule_value = metric.value
    schedule_code = schedule_value.code
    assert isinstance(schedule_code, int), "Expected integer code for ChargeSchedule"
    if enabled == GenericOnOff.ON:
        if schedule_value == ChargeSchedule.DISABLED_SUNDAY:
            metric.set(ChargeSchedule.SUNDAY)  # No idea why they didnt choose non zero for Sunday
        elif schedule_code < 0:
            metric.set(ChargeSchedule.from_code(abs(schedule_code)))  # type: ignore[arg-type]
    elif schedule_value == ChargeSchedule.SUNDAY:
        metric.set(ChargeSchedule.DISABLED_SUNDAY)  # No idea why they didnt choose non zero for Sunday
    elif schedule_code >= 0:
        metric.set(ChargeSchedule.from_code(-abs(schedule_code)))  # type: ignore[arg-type]

    return enabled, None


def gps_location(
    depends_on: dict[str, Metric],
    _transient_state: FormulaTransientState | None,
) -> tuple[GpsLocation | None, None]:
    """Combine GPS metrics into a single GpsLocation. Returns None when there is no GPS fix."""
    lat_metric = None
    lon_metric = None
    fix_metric = None
    alt_metric = None
    course_metric = None
    speed_metric = None
    for metric in depends_on.values():
        if metric.generic_short_id == "gps_latitude":
            lat_metric = metric
        elif metric.generic_short_id == "gps_longitude":
            lon_metric = metric
        elif metric.generic_short_id == "gps_fix":
            fix_metric = metric
        elif metric.generic_short_id == "gps_altitude":
            alt_metric = metric
        elif metric.generic_short_id == "gps_course":
            course_metric = metric
        elif metric.generic_short_id == "gps_speed":
            speed_metric = metric

    if lat_metric is None or lon_metric is None:
        return None, None
    if lat_metric.value is None or lon_metric.value is None:
        return None, None

    # No fix means position is unreliable
    if fix_metric is not None and fix_metric.value == GenericOnOff.OFF:
        return None, None

    return GpsLocation(
        latitude=lat_metric.value,
        longitude=lon_metric.value,
        altitude=alt_metric.value if alt_metric else None,
        course=course_metric.value if course_metric else None,
        speed=speed_metric.value if speed_metric else None,
    ), None


def ess_user_mode(
    depends_on: dict[str, Metric], _transient_state: FormulaTransientState | None
) -> tuple[ESSUserMode | None, None]:
    """Derive the user-facing ESS mode from BatteryLife/State and Hub4Mode.

    Per Victron docs (https://github.com/victronenergy/venus/wiki/dbus#settings):
    - BatteryLife/State 1..8 = Optimized with BatteryLife
    - BatteryLife/State 9 = Keep batteries charged
    - BatteryLife/State 10..12 = Optimized without BatteryLife
    - Hub4Mode 3 = External control
    """
    state_metric = None
    hub4_metric = None
    for metric in depends_on.values():
        if metric.generic_short_id == "system_ess_batterylife_state_full":
            state_metric = metric
        elif metric.generic_short_id == "system_ess_mode":
            hub4_metric = metric

    if state_metric is None or state_metric.value is None:
        return None, None

    # External control is determined by Hub4Mode = 3
    if hub4_metric is not None and hub4_metric.value == ESSModeHub4.EXTERNAL_CONTROL:
        return ESSUserMode.EXTERNAL_CONTROL, None

    state_value = state_metric.value
    code = state_value.code if isinstance(state_value, ESSState) else int(state_value)

    if code == 9:
        return ESSUserMode.KEEP_BATTERIES_CHARGED, None
    if code >= 10:
        return ESSUserMode.OPTIMIZED_NO_BATTERY_LIFE, None
    # Values 1-8 are all sub-states of Optimized with BatteryLife
    return ESSUserMode.OPTIMIZED_BATTERY_LIFE, None


def ess_user_mode_set(
    value: str, depends_on: dict[str, Metric], _transient_state: FormulaTransientState | None
) -> tuple[ESSUserMode, None]:
    """Set the ESS user mode by writing to both BatteryLife/State and Hub4Mode.

    Per Victron docs:
    - Optimized (with BatteryLife): write 1 to BatteryLife/State, keep Hub4Mode at 1 or 2
    - Optimized (without BatteryLife): write 10 to BatteryLife/State, keep Hub4Mode at 1 or 2
    - Keep batteries charged: write 9 to BatteryLife/State, keep Hub4Mode at 1 or 2
    - External control: write 3 to Hub4Mode
    """
    mode: ESSUserMode | None = value if isinstance(value, ESSUserMode) else ESSUserMode.from_id_or_string(value)
    assert mode is not None, "Failed to determine ESS user mode"

    state_metric = None
    hub4_metric = None
    for metric in depends_on.values():
        if metric.generic_short_id == "system_ess_batterylife_state_full":
            state_metric = metric
        elif metric.generic_short_id == "system_ess_mode":
            hub4_metric = metric

    assert state_metric is not None, "BatteryLife/State metric not found"
    assert hub4_metric is not None, "Hub4Mode metric not found"
    assert isinstance(state_metric, WritableMetric), "BatteryLife/State must be writable"
    assert isinstance(hub4_metric, WritableMetric), "Hub4Mode must be writable"

    if mode == ESSUserMode.EXTERNAL_CONTROL:
        hub4_metric.set(ESSModeHub4.EXTERNAL_CONTROL)
    else:
        # Ensure Hub4Mode is not External control; preserve phase compensation setting
        if hub4_metric.value == ESSModeHub4.EXTERNAL_CONTROL:
            hub4_metric.set(ESSModeHub4.PHASE_COMPENSATION_ENABLED)

        if mode == ESSUserMode.OPTIMIZED_BATTERY_LIFE:
            state_metric.set(ESSState.WITH_BATTERY_LIFE)
        elif mode == ESSUserMode.OPTIMIZED_NO_BATTERY_LIFE:
            state_metric.set(ESSState.SELF_CONSUMPTION_SOC_ABOVE_MIN)
        elif mode == ESSUserMode.KEEP_BATTERIES_CHARGED:
            state_metric.set(ESSState.KEEP_BATTERIES_CHARGED)

    return mode, None


def prefer_renewable_energy(
    depends_on: dict[str, Metric], _transient_state: FormulaTransientState | None
) -> tuple[GenericOnOff | None, None]:
    """Derive a binary switch from the PreferRenewableEnergy raw state.

    See https://github.com/victronenergy/venus/issues/1052
    - 0 (Full charge active) → OFF (override in progress, charging fully)
    - 1 (Renewable priority) → ON (solar/wind priority active)
    - 2 (Overridden by generator) → None (unavailable, user cannot control)
    """
    assert len(depends_on) == 1, "Expected exactly one input metric for prefer_renewable_energy"
    metric = next(iter(depends_on.values()))
    if metric.value is None:
        return None, None

    if metric.value == PreferRenewableEnergyEnum.OVERRIDDEN:
        return None, None
    if metric.value == PreferRenewableEnergyEnum.RENEWABLE_PRIORITY:
        return GenericOnOff.ON, None
    return GenericOnOff.OFF, None


def prefer_renewable_energy_set(
    value: str, depends_on: dict[str, Metric], _transient_state: FormulaTransientState | None
) -> tuple[GenericOnOff, None]:
    """Set PreferRenewableEnergy by writing to the raw metric.

    - ON → write RENEWABLE_PRIORITY (1) to cancel full charge / keep renewable priority
    - OFF → write FULL_CHARGE_ACTIVE (0) to trigger a one-time full charge
    """
    assert len(depends_on) == 1, "Expected exactly one input metric for prefer_renewable_energy_set"
    enabled: GenericOnOff | None = value if isinstance(value, GenericOnOff) else GenericOnOff.from_id_or_string(value)
    assert enabled is not None, "Failed to determine enabled state"

    metric = next(iter(depends_on.values()))
    assert isinstance(metric, WritableMetric), "Expected WritableMetric for prefer_renewable_energy_set"

    if enabled == GenericOnOff.ON:
        metric.set(PreferRenewableEnergyEnum.RENEWABLE_PRIORITY)
    else:
        metric.set(PreferRenewableEnergyEnum.FULL_CHARGE_ACTIVE)

    return enabled, None
