"""Victron Enums Module."""

from .constants import VictronDeviceEnum, VictronEnum


class DeviceType(VictronDeviceEnum):
    """Type of device."""

    # This is used to identify the type of device in the system.
    # BEWARE!!! The code is used for mapping from the victron topic, IT IS NOT RANDOM FREE TEXT. The string is used for display purposes.
    # For settings this will be used to identify the device type in the settings.
    SYSTEM = ("system", "system", "Victron Venus")
    SOLAR_CHARGER = ("solarcharger", "solar_charger", "Solar charger")
    INVERTER = ("inverter", "inverter", "Inverter")
    BATTERY = ("battery", "battery", "Battery")
    GRID = ("grid", "grid", "Grid")
    VEBUS = ("vebus", "vebus", "VE.Bus")
    EVCHARGER = ("evcharger", "evcharger", "EV charging station")
    EV = ("ev", "ev", "Electric vehicle")
    PVINVERTER = ("pvinverter", "pvinverter", "PV inverter")
    TEMPERATURE = ("temperature", "temperature", "Temperature")
    GENERATOR = ("generator", "generator", "Generator")
    GENERATOR0 = ("Generator0", "generator0", "Generator 0 settings")
    GENERATOR1 = ("Generator1", "generator1", "Generator 1 settings")
    TANK = ("tank", "tank", "Liquid tank")
    MULTI_RS_SOLAR = ("multi", "multi_rs_solar", "Multi RS Solar")
    CGWACS = ("CGwacs", "cgwacs", "<Not used>", "system")  # Should be mapped to SYSTEM
    DC_LOAD = ("dcload", "dc_load", "DC load")
    ALTERNATOR = (
        "alternator",
        "alternator",
        "Alternator charger",
    )  # Orion XS 1400 in alternator to battery charging mode.
    SWITCH = ("switch", "switch", "Switch")
    GPS = ("gps", "gps", "GPS")
    SYSTEM_SETUP = ("SystemSetup", "system_setup", "<Not used>", "system")  # Should be mapped to SYSTEM
    SERVICES = ("Services", "services", "<Not used>", "system")  # Should be mapped to SYSTEM
    TRANSFER_SWITCH = ("TransferSwitch", "transfer_switch", "Transfer switch")
    DIGITAL_INPUT = ("digitalinput", "digital_input", "Digital input")
    DC_SYSTEM = ("dcsystem", "dc_system", "DC system")
    RELAY = ("Relay", "relay", "<Not used>", "system")  # Should be mapped to SYSTEM
    PLATFORM = (
        "platform",
        "platform",
        "Platform",
        "system",
    )  # For whatever reason some system topics are under platform
    HEATPUMP = ("heatpump", "heatpump", "Heat pump")
    NETWORK = ("Network", "network", "<Not used>", "system")  # Network settings are under system
    METEO = ("meteo", "meteo", "Irradiance sensor")
    DYNAMIC_ESS = ("DynamicEss", "dynamic_ess", "<Not used>", "system")  # Dynamic ESS settings are under system
    ACLOAD = ("acload", "acload", "AC load")
    CHARGER = ("charger", "charger", "Charger")
    HUB4 = ("hub4", "hub4", "Hub4")
    ACSYSTEM = ("acsystem", "acsystem", "<Not used>", "system")  # Should be mapped to SYSTEM
    DCDC = ("dcdc", "dcdc", "DC/DC charger")  # Orion XS 1400 in battery to battery charging mode.


class VictronProductId(VictronEnum):
    """Victron product identifiers, published on the ``.../ProductId`` topic.

    - ``code``   : numeric product ID as reported by the GX. Written as a hex
      literal so it matches Victron's published VE.Direct / VE.Can PID tables
      1:1 while remaining a plain ``int`` at runtime.
    - ``id``     : stable snake_case identifier.
    - ``string`` : human-readable model name.

    This table is seeded from the Victron VE.Direct PID lists and is intentionally
    not exhaustive. Unknown product IDs simply resolve to ``None`` (callers then
    fall back to their default), so entries can be added incrementally.
    """

    # BlueSolar MPPT solar chargers
    BLUESOLAR_MPPT_75_15 = (0xA042, "bluesolar_mppt_75_15", "BlueSolar MPPT 75/15")
    BLUESOLAR_MPPT_100_15 = (0xA043, "bluesolar_mppt_100_15", "BlueSolar MPPT 100/15")
    BLUESOLAR_MPPT_100_30 = (0xA044, "bluesolar_mppt_100_30", "BlueSolar MPPT 100/30")
    BLUESOLAR_MPPT_100_50 = (0xA045, "bluesolar_mppt_100_50", "BlueSolar MPPT 100/50")
    BLUESOLAR_MPPT_150_70 = (0xA04A, "bluesolar_mppt_150_70", "BlueSolar MPPT 150/70")
    BLUESOLAR_MPPT_75_10 = (0xA04C, "bluesolar_mppt_75_10", "BlueSolar MPPT 75/10")
    BLUESOLAR_MPPT_150_45 = (0xA04D, "bluesolar_mppt_150_45", "BlueSolar MPPT 150/45")
    BLUESOLAR_MPPT_150_60 = (0xA04E, "bluesolar_mppt_150_60", "BlueSolar MPPT 150/60")
    BLUESOLAR_MPPT_150_85 = (0xA04F, "bluesolar_mppt_150_85", "BlueSolar MPPT 150/85")
    # SmartSolar MPPT solar chargers
    SMARTSOLAR_MPPT_250_100 = (0xA050, "smartsolar_mppt_250_100", "SmartSolar MPPT 250/100")
    SMARTSOLAR_MPPT_150_100 = (0xA051, "smartsolar_mppt_150_100", "SmartSolar MPPT 150/100")
    SMARTSOLAR_MPPT_150_85 = (0xA052, "smartsolar_mppt_150_85", "SmartSolar MPPT 150/85")
    SMARTSOLAR_MPPT_75_15 = (0xA053, "smartsolar_mppt_75_15", "SmartSolar MPPT 75/15")
    SMARTSOLAR_MPPT_75_10 = (0xA054, "smartsolar_mppt_75_10", "SmartSolar MPPT 75/10")
    SMARTSOLAR_MPPT_100_15 = (0xA055, "smartsolar_mppt_100_15", "SmartSolar MPPT 100/15")
    SMARTSOLAR_MPPT_100_30 = (0xA056, "smartsolar_mppt_100_30", "SmartSolar MPPT 100/30")
    SMARTSOLAR_MPPT_100_50 = (0xA057, "smartsolar_mppt_100_50", "SmartSolar MPPT 100/50")
    SMARTSOLAR_MPPT_150_35 = (0xA058, "smartsolar_mppt_150_35", "SmartSolar MPPT 150/35")
    SMARTSOLAR_MPPT_150_100_REV2 = (0xA059, "smartsolar_mppt_150_100_rev2", "SmartSolar MPPT 150/100 rev2")
    SMARTSOLAR_MPPT_150_85_REV2 = (0xA05A, "smartsolar_mppt_150_85_rev2", "SmartSolar MPPT 150/85 rev2")
    SMARTSOLAR_MPPT_250_70 = (0xA05B, "smartsolar_mppt_250_70", "SmartSolar MPPT 250/70")
    SMARTSOLAR_MPPT_250_85 = (0xA05C, "smartsolar_mppt_250_85", "SmartSolar MPPT 250/85")
    SMARTSOLAR_MPPT_250_60 = (0xA05D, "smartsolar_mppt_250_60", "SmartSolar MPPT 250/60")
    SMARTSOLAR_MPPT_250_45 = (0xA05E, "smartsolar_mppt_250_45", "SmartSolar MPPT 250/45")
    SMARTSOLAR_MPPT_100_20 = (0xA05F, "smartsolar_mppt_100_20", "SmartSolar MPPT 100/20")
    SMARTSOLAR_MPPT_100_20_48V = (0xA060, "smartsolar_mppt_100_20_48v", "SmartSolar MPPT 100/20 48V")
    SMARTSOLAR_MPPT_150_45 = (0xA061, "smartsolar_mppt_150_45", "SmartSolar MPPT 150/45")
    SMARTSOLAR_MPPT_150_60 = (0xA062, "smartsolar_mppt_150_60", "SmartSolar MPPT 150/60")
    SMARTSOLAR_MPPT_150_70 = (0xA063, "smartsolar_mppt_150_70", "SmartSolar MPPT 150/70")


class DVCCMode(VictronEnum):
    """DVCC (Distributed Voltage and Current Control) mode.

    Bit 0: DVCC enabled (0=off, 1=on)
    Bit 1: Forced by system/BMS (0=user-controllable, 1=forced)
    See https://github.com/victronenergy/dbus-systemcalc-py delegates/dvcc.py
    """

    OFF = (0, "off", "Off")
    ON = (1, "on", "On")
    FORCED_OFF = (2, "forced_off", "Forced off")
    FORCED_ON = (3, "forced_on", "Forced on")


class GenericOnOff(VictronEnum):
    """On/Off Enum"""

    OFF = (0, "off", "Off")
    ON = (1, "on", "On")


class GenericOnOffInverted(VictronEnum):
    """Inverted On/Off Enum (0=On, 1=Off)"""

    ON = (0, "on", "On")
    OFF = (1, "off", "Off")


class VrmPortalMode(VictronEnum):
    """VRM Portal access level enum."""

    OFF = (0, "off", "Off")
    READ_ONLY = (1, "read_only", "Read-only")
    FULL = (2, "full", "Full")


class PreferRenewableEnergyEnum(VictronEnum):
    """Prefer Renewable Energy state.

    See https://github.com/victronenergy/venus/issues/1052
    0 = One-time full charge in progress (override active, self-resets to 1)
    1 = Prefer renewable energy active (charge to float only)
    2 = Overridden by generator or Quattro on AC-in-1 (user cannot control)
    """

    FULL_CHARGE_ACTIVE = (0, "full_charge_active", "Full charge active")
    RENEWABLE_PRIORITY = (1, "renewable_priority", "Renewable priority")
    OVERRIDDEN = (2, "overridden", "Overridden by generator")


class ACSystemMode(VictronEnum):
    """AC System Mode Enum"""

    CHARGER_ONLY = (1, "charger_only", "Charger only")
    INVERTER_ONLY = (2, "inverter_only", "Inverter only")
    ON = (3, "on", "On")
    OFF = (4, "off", "Off")
    PASSTHROUGH = (251, "passthrough", "Passthrough")


class ChargerMode(VictronEnum):
    """Charger Mode Enum"""

    ON = (1, "on", "On")
    OFF = (4, "off", "Off")


class BMSMode(VictronEnum):
    """BMS contactor mode enum."""

    ON = (3, "on", "On")
    OFF = (4, "off", "Off")
    STANDBY = (252, "standby", "Standby")


class InverterMode(VictronEnum):
    """Inverter Mode Enum"""

    CHARGER_ONLY = (1, "charger_only", "Charger only")
    INVERTER_ONLY = (2, "inverter_only", "Inverter only")
    ON = (3, "on", "On")
    OFF = (4, "off", "Off")


class PhoenixInverterMode(VictronEnum):
    """Phoenix Inverter Mode Enum"""

    INVERTER = (2, "inverter", "Inverter")
    OFF = (4, "off", "Off")
    ECO = (5, "eco", "Eco")


class State(VictronEnum):
    """State Enum"""

    OFF = (0, "off", "Off")
    LOW_POWER = (1, "low_power", "Low power")
    FAULT = (2, "fault", "Fault")
    BULK = (3, "bulk", "Bulk")
    ABSORPTION = (4, "absorption", "Absorption")
    FLOAT = (5, "float", "Float")
    STORAGE = (6, "storage", "Storage")
    EQUALIZE = (7, "equalize", "Equalize")
    PASSTHROUGH = (8, "passthrough", "Passthrough")
    INVERTING = (9, "inverting", "Inverting")
    POWER_ASSIST = (10, "power_assist", "Power Assist")
    POWER_SUPPLY = (11, "power_supply", "Power supply")
    SUSTAIN = (244, "sustain", "Sustain")
    STARTING_UP = (245, "starting_up", "Starting up")
    REPEATED_ABSORPTION = (246, "repeated_absorption", "Repeated absorption")
    AUTO_EQUALIZE = (247, "auto_equalize", "Auto equalize / recondition")
    BATTERY_SAFE = (248, "battery_safe", "Battery Safe")
    EXTERNAL_CONTROL = (252, "external_control", "External control")
    DISCHARGING = (256, "discharging", "Discharging")
    SUSTAIN_ALT = (257, "sustain_alt", "Sustain alt")
    RECHARGING = (258, "recharging", "Recharging")
    SCHEDULED_RECHARGING = (259, "scheduled_recharging", "Scheduled recharging")


class GenericAlarmEnum(VictronEnum):
    """Generic Alarm Enum"""

    NO_ALARM = (0, "no_alarm", "No alarm")
    WARNING = (1, "warning", "Warning")
    ALARM = (2, "alarm", "Alarm")


class EvChargerMode(VictronEnum):
    """EVCharger Mode Enum"""

    MANUAL = (0, "manual", "Manual")
    AUTO = (1, "auto", "Auto")
    SCHEDULED_CHARGE = (2, "scheduled_charge", "Scheduled charge")


class EvChargingState(VictronEnum):
    """EV Charging State Enum"""

    NOT_CHARGING = (0, "not_charging", "Not charging")
    LOW_POWER_MODE = (1, "low_power_mode", "Low power mode")
    CHARGING = (3, "charging", "Charging")
    SUSTAIN = (244, "sustain", "Sustain")
    WAKE_UP = (245, "wake_up", "Wake up")
    BLOCKED = (250, "blocked", "Blocked")
    UNAVAILABLE = (255, "unavailable", "Unavailable")
    DISCHARGING = (256, "discharging", "Discharging")
    SCHEDULED_CHARGING = (259, "scheduled_charging", "Scheduled charging")


class EvChargerPosition(VictronEnum):
    """EVCharger Position Enum"""

    AC_OUT = (0, "ac_out", "AC out")
    AC_INPUT = (1, "ac_input", "AC input")


class EvChargerStatus(VictronEnum):
    """EVCharger Status Enum"""

    DISCONNECTED = (0, "disconnected", "Disconnected")
    CONNECTED = (1, "connected", "Connected")
    CHARGING = (2, "charging", "Charging")
    CHARGED = (3, "charged", "Charged")
    WAITING_FOR_SUN = (4, "waiting_for_sun", "Waiting for sun")
    WAITING_FOR_RFID = (5, "waiting_for_rfid", "Waiting for RFID")
    WAITING_FOR_START = (6, "waiting_for_start", "Waiting for start")
    LOW_SOC = (7, "low_soc", "Low SoC")
    GROUND_TEST_ERROR = (8, "ground_test_error", "Ground test error")
    WELDED_CONTACTS_TEST_ERROR = (9, "welded_contacts_test_error", "Welded contacts test error")
    CP_INPUT_TEST_ERROR = (10, "cp_input_test_error", "CP input test error")
    RESIDUAL_CURRENT_DETECTED = (11, "residual_current_detected", "Residual current detected")
    UNDERVOLTAGE_DETECTED = (12, "undervoltage_detected", "Undervoltage detected")
    OVERVOLTAGE_DETECTED = (13, "overvoltage_detected", "Overvoltage detected")
    OVERHEATING_DETECTED = (14, "overheating_detected", "Overheating detected")
    RESERVED15 = (15, "reserved15", "Reserved")
    RESERVED16 = (16, "reserved16", "Reserved")
    RESERVED17 = (17, "reserved17", "Reserved")
    RESERVED18 = (18, "reserved18", "Reserved")
    RESERVED19 = (19, "reserved19", "Reserved")
    CHARGING_LIMIT = (20, "charging_limit", "Charging limit")
    START_CHARGING = (21, "start_charging", "Start charging")
    SWITCHING_TO_3_PHASE = (22, "switching_to_3_phase", "Switching to 3 phase")
    SWITCHING_TO_1_PHASE = (23, "switching_to_1_phase", "Switching to 1 phase")


class TemperatureStatus(VictronEnum):
    """Temperature sensor status enum"""

    OK = (0, "ok", "Ok")
    DISCONNECTED = (1, "disconnected", "Disconnected")
    SHORT_CIRCUITED = (2, "short_circuited", "Short circuited")
    REVERSE_POLARITY = (3, "reverse_polarity", "Reverse polarity")
    UNKNOWN = (4, "unknown", "Unknown")


class TemperatureType(VictronEnum):
    """Temperature sensor type enum"""

    BATTERY = (0, "battery", "Battery")
    FRIDGE = (1, "fridge", "Fridge")
    GENERIC = (2, "generic", "Generic")
    ROOM = (3, "room", "Room")
    OUTDOOR = (4, "outdoor", "Outdoor")
    WATER_HEATER = (5, "water_heater", "Water heater")
    FREEZER = (6, "freezer", "Freezer")


class FluidType(VictronEnum):
    """Fluid type enum"""

    FUEL = (0, "fuel", "Fuel")
    FRESH_WATER = (1, "fresh_water", "Fresh water")
    WASTE_WATER = (2, "waste_water", "Waste water")
    LIVE_WELL = (3, "live_well", "Live well")
    OIL = (4, "oil", "Oil")
    BLACK_WATER = (5, "black_water", "Black water (sewage)")
    GASOLINE = (6, "gasoline", "Gasoline")
    DIESEL = (7, "diesel", "Diesel")
    LPG = (8, "lpg", "Liquid petroleum gas (LPG)")
    LNG = (9, "lng", "Liquid natural gas (LNG)")
    HYDRAULIC_OIL = (10, "hydraulic_oil", "Hydraulic oil")
    RAW_WATER = (11, "raw_water", "Raw water")


class MppOperationMode(VictronEnum):
    """MPP Operation Mode Enum"""

    OFF = (0, "off", "Off")
    VOLTAGE_CURRENT_LIMITED = (1, "voltage_current_limited", "Voltage/current limited")
    MPPT_ACTIVE = (2, "mppt_active", "MPPT active")
    NOT_AVAILABLE = (255, "not_available", "Not available")


class ESSMode(VictronEnum):
    """ESS Mode Enum"""

    SELF_CONSUMPTION_BATTERYLIFE = (0, "self_consumption_batterylife", "Self-consumption (BatteryLife)")
    SELF_CONSUMPTION = (1, "self_consumption", "Self-consumption")
    KEEP_CHARGED = (2, "keep_charged", "Keep charged")
    EXTERNAL_CONTROL = (3, "external_control", "External control")


class GeneratorRunningByConditionCode(VictronEnum):
    """Generator Running By Condition Code Enum"""

    STOPPED = (0, "stopped", "Stopped")
    MANUAL = (1, "manual", "Manual")
    TEST_RUN = (2, "test_run", "Test run")
    LOST_COMMS = (3, "lost_comms", "Lost comms")
    SOC = (4, "soc", "SoC")
    AC_LOAD = (5, "ac_load", "AC load")
    BATTERY_CURRENT = (6, "battery_current", "Battery current")
    BATTERY_VOLTS = (7, "battery_volts", "Battery volts")
    INV_TEMP = (8, "inv_temp", "Inverter temperature")
    INV_OVERLOAD = (9, "inv_overload", "Inverter overload")
    STOP_ON_AC1 = (10, "stop_on_ac1", "Stop on AC1")


class DESSReactiveStrategy(VictronEnum):
    """DESS Reactive Strategy Enum"""

    SCHEDULED_SELFCONSUME = (1, "scheduled_selfconsume", "Scheduled self-consume")
    SCHEDULED_CHARGE_ALLOW_GRID = (2, "scheduled_charge_allow_grid", "Scheduled charge allow grid")
    SCHEDULED_CHARGE_ENHANCED = (3, "scheduled_charge_enhanced", "Scheduled charge enhanced")
    SELFCONSUME_ACCEPT_CHARGE = (4, "selfconsume_accept_charge", "Self-consume accept charge")
    IDLE_SCHEDULED_FEEDIN = (5, "idle_scheduled_feedin", "Idle scheduled feed-in")
    SCHEDULED_DISCHARGE = (6, "scheduled_discharge", "Scheduled discharge")
    SELFCONSUME_ACCEPT_DISCHARGE = (7, "selfconsume_accept_discharge", "Self-consume accept discharge")
    IDLE_MAINTAIN_SURPLUS = (8, "idle_maintain_surplus", "Idle maintain surplus")
    IDLE_MAINTAIN_TARGETSOC = (9, "idle_maintain_targetsoc", "Idle maintain target SoC")
    SCHEDULED_CHARGE_SMOOTH_TRANSITION = (
        10,
        "scheduled_charge_smooth_transition",
        "Scheduled charge smooth transition",
    )
    SCHEDULED_CHARGE_FEEDIN = (11, "scheduled_charge_feedin", "Scheduled charge feed-in")
    SCHEDULED_CHARGE_NO_GRID = (12, "scheduled_charge_no_grid", "Scheduled charge no grid")
    SCHEDULED_MINIMUM_DISCHARGE = (13, "scheduled_minimum_discharge", "Scheduled minimum discharge")
    SELFCONSUME_NO_GRID = (14, "selfconsume_no_grid", "Self-consume no grid")
    IDLE_NO_OPPORTUNITY = (15, "idle_no_opportunity", "Idle no opportunity")
    UNSCHEDULED_CHARGE_CATCHUP_TARGETSOC = (
        16,
        "unscheduled_charge_catchup_targetsoc",
        "Unscheduled charge catch-up target SoC",
    )
    SELFCONSUME_INCREASED_DISCHARGE = (17, "selfconsume_increased_discharge", "Self-consume increased discharge")
    KEEP_BATTERY_CHARGED = (18, "keep_battery_charged", "Keep battery charged")
    SCHEDULED_DISCHARGE_SMOOTH_TRANSITION = (
        19,
        "scheduled_discharge_smooth_transition",
        "Scheduled discharge smooth transition",
    )
    DESS_DISABLED = (92, "dess_disabled", "DESS disabled")
    SELFCONSUME_UNEXPECTED_EXCEPTION = (93, "selfconsume_unexpected_exception", "Self-consume unexpected exception")
    SELFCONSUME_FAULTY_CHARGERATE = (94, "selfconsume_faulty_chargerate", "Self-consume faulty charge rate")
    UNKNOWN_OPERATING_MODE = (95, "unknown_operating_mode", "Unknown operating mode")
    ESS_LOW_SOC = (96, "ess_low_soc", "ESS low SoC")
    SELFCONSUME_UNMAPPED_STATE = (97, "selfconsume_unmapped_state", "Self-consume unmapped state")
    SELFCONSUME_UNPREDICTED = (98, "selfconsume_unpredicted", "Self-consume unpredicted")
    NO_WINDOW = (99, "no_window", "No window")


class DESSStrategy(VictronEnum):
    """DESS Strategy Enum"""

    TARGETSOC = (0, "targetsoc", "Target SoC")
    SELFCONSUME = (1, "selfconsume", "Self-consume")
    PROBATTERY = (2, "probattery", "Pro battery")
    PROGRID = (3, "progrid", "Pro grid")


class DESSErrorCode(VictronEnum):
    """DESS Error Code Enum"""

    NO_ERROR = (0, "no_error", "No error")
    NO_ESS = (1, "no_ess", "No ESS")
    ESS_MODE = (2, "ess_mode", "ESS mode")  # ???
    NO_SCHEDULE = (3, "no_schedule", "No matching schedule")
    SOC_LOW = (4, "soc_low", "SoC low")
    BATTRY_CAPACITY_NOT_CONFIGURED = (5, "battry_capacity_not_configured", "Battery capacity not configured")


class DESSMode(VictronEnum):
    """DESS Mode Enum"""

    OFF = (0, "off", "Off")
    AUTO_VRM = (1, "auto_vrm", "Auto / VRM")
    BUY = (2, "buy", "Buy")
    SELL = (3, "sell", "Sell")
    NODE_RED = (4, "node_red", "Node-RED")


class DESSRestrictions(VictronEnum):
    """DESS Restrictions Enum"""

    NO_RESTRICTIONS = (0, "no_restrictions", "No restrictions between battery and the grid")
    BATTERY_TO_GRID_RESTRICTED = (1, "battery_to_grid_restricted", "Battery to grid energy flow restricted")
    GRID_TO_BATTERY_RESTRICTED = (2, "grid_to_battery_restricted", "Grid to battery energy flow restricted")
    NO_FLOW = (3, "no_flow", "No energy flow between battery and grid")


class ErrorCode(VictronEnum):
    """Generic Error Code Enum"""

    NO_ERROR = (0, "no_error", "No error")
    BATTERY_VOLTAGE_TOO_HIGH = (2, "battery_voltage_too_high", "Battery voltage too high")
    CHARGER_TEMPERATURE_TOO_HIGH = (17, "charger_temperature_too_high", "Charger temperature too high")
    CHARGER_OVER_CURRENT = (18, "charger_over_current", "Charger over current")
    CHARGER_CURRENT_REVERSED = (19, "charger_current_reversed", "Charger current reversed")
    BULK_TIME_LIMIT_EXCEEDED = (20, "bulk_time_limit_exceeded", "Bulk time limit exceeded")
    CURRENT_SENSOR_ISSUE = (21, "current_sensor_issue", "Current sensor issue")
    TERMINALS_OVERHEATED = (26, "terminals_overheated", "Terminals overheated")
    CONVERTER_ISSUE = (28, "converter_issue", "Converter issue")
    INPUT_VOLTAGE_TOO_HIGH = (33, "input_voltage_too_high", "Input voltage too high (solar panel)")
    INPUT_CURRENT_TOO_HIGH = (34, "input_current_too_high", "Input current too high (solar panel)")
    INPUT_SHUTDOWN_BATTERY_VOLTAGE_TOO_HIGH = (
        38,
        "input_shutdown_battery_voltage_too_high",
        "Input shutdown (battery voltage too high)",
    )
    INPUT_SHUTDOWN_REVERSE_CURRENT = (39, "input_shutdown_reverse_current", "Input shutdown (reverse current)")
    LOST_COMMUNICATION_WITH_DEVICE = (65, "lost_communication_with_device", "Lost communication with device")
    SYNCHRONIZED_CHARGING_CONFIG_ISSUE = (
        66,
        "synchronized_charging_config_issue",
        "Synchronized charging config issue",
    )
    BMS_CONNECTION_LOST = (67, "bms_connection_lost", "BMS connection lost")
    NETWORK_MISCONFIGURED = (68, "network_misconfigured", "Network misconfigured")
    FACTORY_CALIBRATION_DATA_LOST = (116, "factory_calibration_data_lost", "Factory calibration data lost")
    INVALID_INCOMPATIBLE_FIRMWARE = (117, "invalid_incompatible_firmware", "Invalid/incompatible firmware")
    USER_SETTINGS_INVALID = (119, "user_settings_invalid", "User settings invalid")


class DigitalInputInputState(VictronEnum):
    """Raw input state: High/Open (0) or Low/Closed (1)."""

    HIGH_OPEN = (0, "high_open", "High/open")
    LOW_CLOSED = (1, "low_closed", "Low/closed")


class DigitalInputType(VictronEnum):
    """Type of digital input."""

    DISABLED = (0, "disabled", "Disabled")
    PULSE_METER = (1, "pulse_meter", "Pulse meter")
    DOOR_ALARM = (2, "door_alarm", "Door alarm")
    BILGE_PUMP = (3, "bilge_pump", "Bilge pump")
    BILGE_ALARM = (4, "bilge_alarm", "Bilge alarm")
    BURGLAR_ALARM = (5, "burglar_alarm", "Burglar alarm")
    SMOKE_ALARM = (6, "smoke_alarm", "Smoke alarm")
    FIRE_ALARM = (7, "fire_alarm", "Fire alarm")
    CO2_ALARM = (8, "co2_alarm", "CO2 alarm")
    GENERATOR = (9, "generator", "Generator")
    TOUCH_INPUT_CONTROL = (10, "touch_input_control", "Touch input control")


class DigitalInputState(VictronEnum):
    """Translated input state (determined by input type)."""

    LOW = (0, "low", "Low")
    HIGH = (1, "high", "High")
    OFF = (2, "off", "Off")
    ON = (3, "on", "On")
    NO = (4, "no", "No")
    YES = (5, "yes", "Yes")
    OPEN = (6, "open", "Open")
    CLOSED = (7, "closed", "Closed")
    OK = (8, "ok", "Ok")
    ALARM = (9, "alarm", "Alarm")
    RUNNING = (10, "running", "Running")
    STOPPED = (11, "stopped", "Stopped")


class ESSState(VictronEnum):
    """ESS State Enum"""

    # Optimized mode with BatteryLife:
    # 1 is Value set by the GUI when BatteryLife is enabled. Hub4Control uses it to find the right BatteryLife state (values 2-7) based on system state
    WITH_BATTERY_LIFE = (1, "with_battery_life", "Optimized mode with BatteryLife")
    SELF_CONSUMPTION = (2, "self_consumption", "Self-consumption")
    SELF_CONSUMPTION_SOC_EXCEEDS_85 = (3, "self_consumption_soc_exceeds_85", "Self-consumption, SoC exceeds 85%")
    SELF_CONSUMPTION_SOC_AT_100 = (4, "self_consumption_soc_at_100", "Self-consumption, SoC at 100%")
    SOC_BELOW_BATTERY_LIFE_DYNAMIC_SOC_LIMIT = (
        5,
        "soc_below_battery_life_dynamic_soc_limit",
        "SoC below BatteryLife dynamic SoC limit",
    )
    SOC_BELOW_SOC_LIMIT_24_HOURS = (
        6,
        "soc_below_soc_limit_24_hours",
        "SoC has been below SoC limit for more than 24 hours. Charging battery with 5 amps",
    )
    SUSTAIN = (7, "sustain", "Multi/Quattro is in sustain")
    RECHARGE = (8, "recharge", "Recharge, SoC dropped 5% or more below minimum SoC")
    # Keep batteries charged mode:
    KEEP_BATTERIES_CHARGED = (9, "keep_batteries_charged", "'Keep batteries charged' mode enabled")
    # Optimized mode without BatteryLife:
    SELF_CONSUMPTION_SOC_ABOVE_MIN = (
        10,
        "self_consumption_soc_above_min",
        "Self-consumption, SoC at or above minimum SoC",
    )
    SELF_CONSUMPTION_SOC_BELOW_MIN = (
        11,
        "self_consumption_soc_below_min",
        "Self-consumption, SoC is below minimum SoC",
    )
    RECHARGE_NO_BATTERY_LIFE = (
        12,
        "recharge_no_battery_life",
        "Recharge, SoC dropped 5% or more below minimum SoC (No BatteryLife)",
    )


class ESSUserMode(VictronEnum):
    """ESS User Mode Enum - matches the 4 user-facing modes shown in VRM."""

    OPTIMIZED_BATTERY_LIFE = (1, "optimized_battery_life", "Optimized (with BatteryLife)")
    OPTIMIZED_NO_BATTERY_LIFE = (10, "optimized_no_battery_life", "Optimized (without BatteryLife)")
    KEEP_BATTERIES_CHARGED = (9, "keep_batteries_charged", "Keep batteries charged")
    EXTERNAL_CONTROL = (3, "external_control", "External control")


class ESSModeHub4(VictronEnum):
    """ESS Mode Enum for Hub4Control"""

    PHASE_COMPENSATION_ENABLED = (
        1,
        "phase_compensation_enabled",
        "Optimized mode or 'keep batteries charged' and phase compensation enabled",
    )
    PHASE_COMPENSATION_DISABLED = (
        2,
        "phase_compensation_disabled",
        "Optimized mode or 'keep batteries charged' and phase compensation disabled",
    )
    EXTERNAL_CONTROL = (3, "external_control", "External control")


class ACActiveInputSource(VictronEnum):
    """AC Active Input Source Enum"""

    UNKNOWN = (0, "unknown", "Unknown")
    GRID = (1, "grid", "Grid")
    GENERATOR = (2, "generator", "Generator")
    SHORE_POWER = (3, "shore_power", "Shore power")
    NOT_CONNECTED = (240, "not_connected", "Not connected")


class AcInputTypeEnum(VictronEnum):
    """AC Input Type Enum"""

    NOT_USED = (0, "not_used", "Not used")
    GRID = (1, "grid", "Grid")
    GENERATOR = (2, "generator", "Generator")
    SHORE = (3, "shore", "Shore")


class ChargeSchedule(VictronEnum):
    """Charge Schedule Enum"""

    DISABLED_SUNDAY = (-10, "disabled_sunday", "Disabled (Sunday)")
    DISABLED_WEEKEND = (-9, "disabled_weekend", "Disabled (Weekends)")
    DISABLED_WEEKDAYS = (-8, "disabled_weekdays", "Disabled (Weekdays)")
    DISABLED_EVERY_DAY = (-7, "disabled_every_day", "Disabled (Every day)")
    DISABLED_SATURDAY = (-6, "disabled_saturday", "Disabled (Saturday)")
    DISABLED_FRIDAY = (-5, "disabled_friday", "Disabled (Friday)")
    DISABLED_THURSDAY = (-4, "disabled_thursday", "Disabled (Thursday)")
    DISABLED_WEDNESDAY = (-3, "disabled_wednesday", "Disabled (Wednesday)")
    DISABLED_TUESDAY = (-2, "disabled_tuesday", "Disabled (Tuesday)")
    DISABLED_MONDAY = (-1, "disabled_monday", "Disabled (Monday)")
    SUNDAY = (0, "sunday", "Sunday")
    MONDAY = (1, "monday", "Monday")
    TUESDAY = (2, "tuesday", "Tuesday")
    WEDNESDAY = (3, "wednesday", "Wednesday")
    THURSDAY = (4, "thursday", "Thursday")
    FRIDAY = (5, "friday", "Friday")
    SATURDAY = (6, "saturday", "Saturday")
    EVERY_DAY = (7, "every_day", "Every day")
    WEEKDAYS = (8, "weekdays", "Weekdays")
    WEEKENDS = (9, "weekends", "Weekends")


class ActiveInputEnum(VictronEnum):
    """Active Input Enum"""

    AC_INPUT_1 = (0, "ac_input_1", "AC input 1")
    AC_INPUT_2 = (1, "ac_input_2", "AC input 2")
    DISCONNECTED = (240, "disconnected", "Disconnected")


class SolarChargerDeviceOffReason(VictronEnum):
    """Solar Charger Device Off Reason Enum"""

    NONE = (0x00, "none", "-")
    NO_INPUT_POWER = (0x01, "no_input_power", "No/low input power")
    SWITCHED_OFF_POWER_SWITCH = (0x02, "switched_off_power_switch", "Switched off (power switch)")
    SWITCHED_OFF_DEVICE_MODE_REGISTER = (
        0x04,
        "switched_off_device_mode_register",
        "Switched off (device mode register)",
    )
    REMOTE_INPUT = (0x08, "remote_input", "Remote input")
    PROTECTIVE_ACTION = (0x10, "protective_action", "Protection active")
    NEED_TOKEN = (0x20, "need_token", "Need token for operation")
    SIGNAL_FROM_BMS = (0x40, "signal_from_bms", "Signal from BMS")
    ENGINE_SHUTDOWN = (0x80, "engine_shutdown", "Engine shutdown on low input voltage")
    ANALYSING_INPUT_VOLTAGE = (0x100, "analysing_input_voltage", "Analysing input voltage")
    LOW_TEMPERATURE = (0x200, "low_temperature", "Low temperature")
    NO_PANEL_POWER = (0x400, "no_panel_power", "No/low panel power")
    NO_BATTERY_POWER = (0x800, "no_battery_power", "No/low battery power")
    ACTIVE_ALARM = (0x8000, "active_alarm", "Active alarm")


class BatteryState(VictronEnum):
    """Battery state Enum"""

    IDLE = (0, "idle", "Idle")
    CHARGING = (1, "charging", "Charging")
    DISCHARGING = (2, "discharging", "Discharging")


class SwitchableOutputType(VictronEnum):
    """SwitchableOutput type Enum"""

    MOMENTARY = (0, "momentary", "Momentary")
    TOGGLE = (1, "toggle", "Toggle")
    DIMMABLE = (2, "dimmable", "Dimmable")
    TEMPERATURE_SETPOINT = (3, "temperature_setpoint", "Temperature setpoint")
    STEPPED_SWITCH = (4, "stepped_switch", "Stepped switch")
    SLAVE_MODE = (5, "slave_mode", "Slave mode")
    DROPDOWN = (6, "dropdown", "Dropdown")
    BASIC_SLIDER = (7, "basic_slider", "Basic slider")
    NUMERIC_INPUT = (8, "numeric_input", "Numeric input")
    THREE_STATE_SWITCH = (9, "three_state_switch", "Three-state switch")
    BILGE_PUMP_CONTROL = (10, "bilge_pump_control", "Bilge pump control")
    RGB_COLOR_WHEEL = (11, "rgb_color_wheel", "RGB color wheel")
    CCT_COLOR_WHEEL = (12, "cct_color_wheel", "CCT color wheel")
    RGBW_COLOR_WHEEL = (13, "rgbw_color_wheel", "RGBW color wheel")
