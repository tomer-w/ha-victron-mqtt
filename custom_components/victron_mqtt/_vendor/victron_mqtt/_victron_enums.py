"""Victron Enums Module."""

from .constants import VictronDeviceEnum, VictronEnum

# Public sources for enum values and semantics include:
# https://github.com/victronenergy/venus/wiki/dbus
# https://github.com/victronenergy/dbus_modbustcp/blob/master/CCGX-Modbus-TCP-register-list.xlsx
# https://github.com/victronenergy/gui-v2/blob/master/src/enums.h
# https://github.com/victronenergy/dbus-systemcalc-py
# https://github.com/victronenergy/veutil/blob/master/inc/veutil/qt/firmware_updater_data.hpp


class DeviceType(VictronDeviceEnum):
    """Type of device."""

    # This is used to identify the type of device in the system.
    # BEWARE!!! The code is used for mapping from the victron topic, IT IS NOT RANDOM FREE TEXT. The string is used for display purposes.
    # For settings this will be used to identify the device type in the settings.
    SYSTEM = ("system", "system", "Victron Venus", "Identifies the Victron Venus MQTT and D-Bus service type.")
    SOLAR_CHARGER = (
        "solarcharger",
        "solar_charger",
        "Solar charger",
        "Identifies the Solar charger MQTT and D-Bus service type.",
    )
    INVERTER = ("inverter", "inverter", "Inverter", "Identifies the Inverter MQTT and D-Bus service type.")
    BATTERY = ("battery", "battery", "Battery", "Identifies the Battery MQTT and D-Bus service type.")
    GRID = ("grid", "grid", "Grid", "Identifies the Grid MQTT and D-Bus service type.")
    VEBUS = ("vebus", "vebus", "VE.Bus", "Identifies the VE.Bus MQTT and D-Bus service type.")
    EVCHARGER = (
        "evcharger",
        "evcharger",
        "EV charging station",
        "Identifies the EV charging station MQTT and D-Bus service type.",
    )
    EV = ("ev", "ev", "Electric vehicle", "Identifies the Electric vehicle MQTT and D-Bus service type.")
    PVINVERTER = ("pvinverter", "pvinverter", "PV inverter", "Identifies the PV inverter MQTT and D-Bus service type.")
    TEMPERATURE = (
        "temperature",
        "temperature",
        "Temperature",
        "Identifies the Temperature MQTT and D-Bus service type.",
    )
    GENERATOR = ("generator", "generator", "Generator", "Identifies the Generator MQTT and D-Bus service type.")
    GENERATOR0 = (
        "Generator0",
        "generator0",
        "Generator 0 settings",
        "Identifies the Generator 0 settings MQTT and D-Bus service type.",
    )
    GENERATOR1 = (
        "Generator1",
        "generator1",
        "Generator 1 settings",
        "Identifies the Generator 1 settings MQTT and D-Bus service type.",
    )
    TANK = ("tank", "tank", "Liquid tank", "Identifies the Liquid tank MQTT and D-Bus service type.")
    MULTI_RS_SOLAR = (
        "multi",
        "multi_rs_solar",
        "Multi RS Solar",
        "Identifies the Multi RS Solar MQTT and D-Bus service type.",
    )
    CGWACS = (
        "CGwacs",
        "cgwacs",
        "<Not used>",
        "Maps the CGwacs MQTT and D-Bus service namespace to the system device type.",
        "system",
    )  # Should be mapped to SYSTEM
    DC_LOAD = ("dcload", "dc_load", "DC load", "Identifies the DC load MQTT and D-Bus service type.")
    DC_SOURCE = ("dcsource", "dc_source", "DC source", "Identifies the DC source MQTT and D-Bus service type.")
    ALTERNATOR = (
        "alternator",
        "alternator",
        "Alternator charger",
        "Identifies the Alternator charger MQTT and D-Bus service type.",
    )  # Orion XS 1400 in alternator to battery charging mode.
    SWITCH = ("switch", "switch", "Switch", "Identifies the Switch MQTT and D-Bus service type.")
    GPS = ("gps", "gps", "GPS", "Identifies the GPS MQTT and D-Bus service type.")
    SYSTEM_SETUP = (
        "SystemSetup",
        "system_setup",
        "<Not used>",
        "Maps the SystemSetup MQTT and D-Bus service namespace to the system device type.",
        "system",
    )  # Should be mapped to SYSTEM
    SERVICES = (
        "Services",
        "services",
        "<Not used>",
        "Maps the Services MQTT and D-Bus service namespace to the system device type.",
        "system",
    )  # Should be mapped to SYSTEM
    TRANSFER_SWITCH = (
        "TransferSwitch",
        "transfer_switch",
        "Transfer switch",
        "Identifies the Transfer switch MQTT and D-Bus service type.",
    )
    DIGITAL_INPUT = (
        "digitalinput",
        "digital_input",
        "Digital input",
        "Identifies the Digital input MQTT and D-Bus service type.",
    )
    DC_SYSTEM = ("dcsystem", "dc_system", "DC system", "Identifies the DC system MQTT and D-Bus service type.")
    RELAY = (
        "Relay",
        "relay",
        "<Not used>",
        "Maps the Relay MQTT and D-Bus service namespace to the system device type.",
        "system",
    )  # Should be mapped to SYSTEM
    PLATFORM = (
        "platform",
        "platform",
        "Platform",
        "Maps the platform MQTT and D-Bus service namespace to the system device type.",
        "system",
    )  # For whatever reason some system topics are under platform
    HEATPUMP = ("heatpump", "heatpump", "Heat pump", "Identifies the Heat pump MQTT and D-Bus service type.")
    NETWORK = (
        "Network",
        "network",
        "<Not used>",
        "Maps the Network MQTT and D-Bus service namespace to the system device type.",
        "system",
    )  # Network settings are under system
    METEO = ("meteo", "meteo", "Irradiance sensor", "Identifies the Irradiance sensor MQTT and D-Bus service type.")
    DYNAMIC_ESS = (
        "DynamicEss",
        "dynamic_ess",
        "<Not used>",
        "Maps the DynamicEss MQTT and D-Bus service namespace to the system device type.",
        "system",
    )  # Dynamic ESS settings are under system
    ACLOAD = ("acload", "acload", "AC load", "Identifies the AC load MQTT and D-Bus service type.")
    CHARGER = ("charger", "charger", "Charger", "Identifies the Charger MQTT and D-Bus service type.")
    HUB4 = ("hub4", "hub4", "Hub4", "Identifies the Hub4 MQTT and D-Bus service type.")
    ACSYSTEM = (
        "acsystem",
        "acsystem",
        "<Not used>",
        "Maps the acsystem MQTT and D-Bus service namespace to the system device type.",
        "system",
    )  # Should be mapped to SYSTEM
    DCDC = (
        "dcdc",
        "dcdc",
        "DC/DC charger",
        "Identifies the DC/DC charger MQTT and D-Bus service type.",
    )  # Orion XS 1400 in battery to battery charging mode.


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
    BLUESOLAR_MPPT_75_15 = (
        0xA042,
        "bluesolar_mppt_75_15",
        "BlueSolar MPPT 75/15",
        "Identifies the BlueSolar MPPT 75/15 model from its published Victron product ID.",
    )
    BLUESOLAR_MPPT_100_15 = (
        0xA043,
        "bluesolar_mppt_100_15",
        "BlueSolar MPPT 100/15",
        "Identifies the BlueSolar MPPT 100/15 model from its published Victron product ID.",
    )
    BLUESOLAR_MPPT_100_30 = (
        0xA044,
        "bluesolar_mppt_100_30",
        "BlueSolar MPPT 100/30",
        "Identifies the BlueSolar MPPT 100/30 model from its published Victron product ID.",
    )
    BLUESOLAR_MPPT_100_50 = (
        0xA045,
        "bluesolar_mppt_100_50",
        "BlueSolar MPPT 100/50",
        "Identifies the BlueSolar MPPT 100/50 model from its published Victron product ID.",
    )
    BLUESOLAR_MPPT_150_70 = (
        0xA04A,
        "bluesolar_mppt_150_70",
        "BlueSolar MPPT 150/70",
        "Identifies the BlueSolar MPPT 150/70 model from its published Victron product ID.",
    )
    BLUESOLAR_MPPT_75_10 = (
        0xA04C,
        "bluesolar_mppt_75_10",
        "BlueSolar MPPT 75/10",
        "Identifies the BlueSolar MPPT 75/10 model from its published Victron product ID.",
    )
    BLUESOLAR_MPPT_150_45 = (
        0xA04D,
        "bluesolar_mppt_150_45",
        "BlueSolar MPPT 150/45",
        "Identifies the BlueSolar MPPT 150/45 model from its published Victron product ID.",
    )
    BLUESOLAR_MPPT_150_45_REV2 = (
        0xA06F,
        "bluesolar_mppt_150_45_rev2",
        "BlueSolar MPPT 150/45 rev2",
        "Identifies the BlueSolar MPPT 150/45 rev2 model from its published Victron product ID.",
    )
    BLUESOLAR_MPPT_150_45_REV3 = (
        0xA072,
        "bluesolar_mppt_150_45_rev3",
        "BlueSolar MPPT 150/45 rev3",
        "Identifies the BlueSolar MPPT 150/45 rev3 model from its published Victron product ID.",
    )
    BLUESOLAR_MPPT_150_60 = (
        0xA04E,
        "bluesolar_mppt_150_60",
        "BlueSolar MPPT 150/60",
        "Identifies the BlueSolar MPPT 150/60 model from its published Victron product ID.",
    )
    BLUESOLAR_MPPT_150_85 = (
        0xA04F,
        "bluesolar_mppt_150_85",
        "BlueSolar MPPT 150/85",
        "Identifies the BlueSolar MPPT 150/85 model from its published Victron product ID.",
    )
    # SmartSolar MPPT solar chargers
    SMARTSOLAR_MPPT_250_100 = (
        0xA050,
        "smartsolar_mppt_250_100",
        "SmartSolar MPPT 250/100",
        "Identifies the SmartSolar MPPT 250/100 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_150_100 = (
        0xA051,
        "smartsolar_mppt_150_100",
        "SmartSolar MPPT 150/100",
        "Identifies the SmartSolar MPPT 150/100 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_150_85 = (
        0xA052,
        "smartsolar_mppt_150_85",
        "SmartSolar MPPT 150/85",
        "Identifies the SmartSolar MPPT 150/85 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_75_15 = (
        0xA053,
        "smartsolar_mppt_75_15",
        "SmartSolar MPPT 75/15",
        "Identifies the SmartSolar MPPT 75/15 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_75_10 = (
        0xA054,
        "smartsolar_mppt_75_10",
        "SmartSolar MPPT 75/10",
        "Identifies the SmartSolar MPPT 75/10 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_100_15 = (
        0xA055,
        "smartsolar_mppt_100_15",
        "SmartSolar MPPT 100/15",
        "Identifies the SmartSolar MPPT 100/15 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_100_30 = (
        0xA056,
        "smartsolar_mppt_100_30",
        "SmartSolar MPPT 100/30",
        "Identifies the SmartSolar MPPT 100/30 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_100_50 = (
        0xA057,
        "smartsolar_mppt_100_50",
        "SmartSolar MPPT 100/50",
        "Identifies the SmartSolar MPPT 100/50 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_150_35 = (
        0xA058,
        "smartsolar_mppt_150_35",
        "SmartSolar MPPT 150/35",
        "Identifies the SmartSolar MPPT 150/35 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_150_100_REV2 = (
        0xA059,
        "smartsolar_mppt_150_100_rev2",
        "SmartSolar MPPT 150/100 rev2",
        "Identifies the SmartSolar MPPT 150/100 rev2 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_150_85_REV2 = (
        0xA05A,
        "smartsolar_mppt_150_85_rev2",
        "SmartSolar MPPT 150/85 rev2",
        "Identifies the SmartSolar MPPT 150/85 rev2 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_250_70 = (
        0xA05B,
        "smartsolar_mppt_250_70",
        "SmartSolar MPPT 250/70",
        "Identifies the SmartSolar MPPT 250/70 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_250_85 = (
        0xA05C,
        "smartsolar_mppt_250_85",
        "SmartSolar MPPT 250/85",
        "Identifies the SmartSolar MPPT 250/85 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_250_60 = (
        0xA05D,
        "smartsolar_mppt_250_60",
        "SmartSolar MPPT 250/60",
        "Identifies the SmartSolar MPPT 250/60 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_250_60_REV2 = (
        0xA068,
        "smartsolar_mppt_250_60_rev2",
        "SmartSolar MPPT 250/60 rev2",
        "Identifies the SmartSolar MPPT 250/60 rev2 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_250_45 = (
        0xA05E,
        "smartsolar_mppt_250_45",
        "SmartSolar MPPT 250/45",
        "Identifies the SmartSolar MPPT 250/45 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_100_20 = (
        0xA05F,
        "smartsolar_mppt_100_20",
        "SmartSolar MPPT 100/20",
        "Identifies the SmartSolar MPPT 100/20 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_100_20_48V = (
        0xA060,
        "smartsolar_mppt_100_20_48v",
        "SmartSolar MPPT 100/20 48V",
        "Identifies the SmartSolar MPPT 100/20 48V model from its published Victron product ID.",
    )
    BLUESOLAR_MPPT_100_20_48V = (
        0xA067,
        "bluesolar_mppt_100_20_48v",
        "BlueSolar MPPT 100/20 48V",
        "Identifies the BlueSolar MPPT 100/20 48V model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_150_45 = (
        0xA061,
        "smartsolar_mppt_150_45",
        "SmartSolar MPPT 150/45",
        "Identifies the SmartSolar MPPT 150/45 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_150_45_REV2 = (
        0xA06A,
        "smartsolar_mppt_150_45_rev2",
        "SmartSolar MPPT 150/45 rev2",
        "Identifies the SmartSolar MPPT 150/45 rev2 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_150_45_REV3 = (
        0xA073,
        "smartsolar_mppt_150_45_rev3",
        "SmartSolar MPPT 150/45 rev3",
        "Identifies the SmartSolar MPPT 150/45 rev3 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_150_60 = (
        0xA062,
        "smartsolar_mppt_150_60",
        "SmartSolar MPPT 150/60",
        "Identifies the SmartSolar MPPT 150/60 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_150_70 = (
        0xA063,
        "smartsolar_mppt_150_70",
        "SmartSolar MPPT 150/70",
        "Identifies the SmartSolar MPPT 150/70 model from its published Victron product ID.",
    )
    # SmartSolar MPPT VE.Can and RS series (CAN-bus interface variants).
    SMARTSOLAR_MPPT_VECAN_150_85_REV2 = (
        0xA10D,
        "smartsolar_mppt_vecan_150_85_rev2",
        "SmartSolar MPPT VE.Can 150/85 rev2",
        "Identifies the SmartSolar MPPT VE.Can 150/85 rev2 model from its published Victron product ID.",
    )
    SMARTSOLAR_MPPT_RS_450_100 = (
        0xA110,
        "smartsolar_mppt_rs_450_100",
        "SmartSolar MPPT RS 450/100",
        "Identifies the SmartSolar MPPT RS 450/100 model from its published Victron product ID.",
    )
    # Orion XS 1400 DC-DC charger (VE.Direct); reported under the alternator/dcdc device types.
    # Output current is settable up to 50 A across all output-voltage configs (1400 W ceiling at 28 V).
    ORION_XS_12V_12V_50A = (
        0xA3F0,
        "orion_xs_12v_12v_50a",
        "Orion XS 12V/12V-50A",
        "Identifies the Orion XS 12V/12V-50A model from its published Victron product ID.",
    )
    ORION_XS_12V_12V_70A = (
        0xA3F2,
        "orion_xs_12v_12v_70a",
        "Orion XS 12V/12V-70A",
        "Identifies the Orion XS 12V/12V-70A model from its published Victron product ID.",
    )
    ORION_XS_12V_24V_50A = (
        0xA3F1,
        "orion_xs_12v_24v_50a",
        "Orion XS 12V/24V-50A",
        "Identifies the Orion XS 12V/24V-50A model from its published Victron product ID.",
    )


class DVCCMode(VictronEnum):
    """DVCC (Distributed Voltage and Current Control) mode.

    Bit 0: DVCC enabled (0=off, 1=on)
    Bit 1: Forced by system/BMS (0=user-controllable, 1=forced)
    See https://github.com/victronenergy/dbus-systemcalc-py delegates/dvcc.py
    """

    OFF = (0, "off", "Off", "DVCC is disabled and remains user-controllable.")
    ON = (1, "on", "On", "DVCC is enabled and remains user-controllable.")
    FORCED_OFF = (2, "forced_off", "Forced off", "DVCC is disabled and forced by the system or BMS.")
    FORCED_ON = (3, "forced_on", "Forced on", "DVCC is enabled and forced by the system or BMS.")


class GenericOnOff(VictronEnum):
    """On/Off Enum"""

    OFF = (0, "off", "Off", "The option is disabled.")
    ON = (1, "on", "On", "The option is enabled.")


class GenericOnOffInverted(VictronEnum):
    """Inverted On/Off Enum (0=On, 1=Off)"""

    ON = (0, "on", "On", "The option is enabled.")
    OFF = (1, "off", "Off", "The option is disabled.")


class FirmwareUpdateState(VictronEnum):
    """GX firmware update state."""

    UPDATE_FILE_NOT_FOUND = (
        997,
        "update_file_not_found",
        "Update file not found",
        "The GX device could not find the firmware update file.",
    )
    ERROR_DURING_UPDATE = (
        998,
        "error_during_update",
        "Error during update",
        "The firmware installation failed before it could complete.",
    )
    ERROR_DURING_CHECK = (
        999,
        "error_during_check",
        "Error during check",
        "The GX device could not complete the online firmware update check.",
    )
    IDLE = (1000, "idle", "Idle", "No firmware check or installation is currently running.")
    CHECKING = (1001, "checking", "Checking", "The GX device is checking online for an available firmware update.")
    DOWNLOADING_AND_INSTALLING = (
        1002,
        "downloading_and_installing",
        "Downloading and installing",
        "The GX device is downloading and installing the firmware update.",
    )
    REBOOTING = (1003, "rebooting", "Rebooting", "The GX device is rebooting to complete the firmware update.")


class VrmPortalMode(VictronEnum):
    """VRM Portal access level enum."""

    OFF = (0, "off", "Off", "VRM Portal connectivity is disabled.")
    READ_ONLY = (1, "read_only", "Read-only", "VRM Portal may read system data but cannot issue remote commands.")
    FULL = (2, "full", "Full", "VRM Portal has full read and remote-control access.")


class PreferRenewableEnergyEnum(VictronEnum):
    """Prefer Renewable Energy state.

    See https://github.com/victronenergy/venus/issues/1052
    0 = One-time full charge in progress (override active, self-resets to 1)
    1 = Prefer renewable energy active (charge to float only)
    2 = Overridden by generator or Quattro on AC-in-1 (user cannot control)
    """

    FULL_CHARGE_ACTIVE = (
        0,
        "full_charge_active",
        "Full charge active",
        "A one-time full battery charge is in progress before renewable-energy priority resumes.",
    )
    RENEWABLE_PRIORITY = (
        1,
        "renewable_priority",
        "Renewable priority",
        "Charging prioritizes renewable energy and normally stops at float.",
    )
    OVERRIDDEN = (
        2,
        "overridden",
        "Overridden by generator",
        "Renewable-energy priority is unavailable because a generator or Quattro AC-in-1 overrides it.",
    )


class ACSystemMode(VictronEnum):
    """AC System Mode Enum"""

    CHARGER_ONLY = (
        1,
        "charger_only",
        "Charger only",
        "The AC system may charge batteries but does not invert DC power to AC.",
    )
    INVERTER_ONLY = (
        2,
        "inverter_only",
        "Inverter only",
        "The AC system may invert DC power to AC but does not charge from AC input.",
    )
    ON = (3, "on", "On", "Charging, inversion, and AC passthrough are enabled as conditions require.")
    OFF = (4, "off", "Off", "The AC system is disabled.")
    PASSTHROUGH = (251, "passthrough", "Passthrough", "AC input is passed to the output without charging or inverting.")


class ChargerMode(VictronEnum):
    """Charger Mode Enum"""

    ON = (1, "on", "On", "The charger is enabled and may charge when operating conditions permit.")
    OFF = (4, "off", "Off", "The charger is disabled.")


class BMSMode(VictronEnum):
    """BMS contactor mode enum."""

    ON = (3, "on", "On", "The BMS contactor is closed for normal battery operation.")
    OFF = (4, "off", "Off", "The BMS contactor is open and battery operation is disabled.")
    STANDBY = (252, "standby", "Standby", "The BMS is powered but waiting in standby.")


class InverterMode(VictronEnum):
    """Inverter Mode Enum"""

    CHARGER_ONLY = (
        1,
        "charger_only",
        "Charger only",
        "The inverter/charger may charge batteries but will not invert DC power to AC.",
    )
    INVERTER_ONLY = (
        2,
        "inverter_only",
        "Inverter only",
        "The inverter/charger may supply AC from the battery but will not charge from AC input.",
    )
    ON = (3, "on", "On", "Charging, inversion, and AC passthrough are enabled as conditions require.")
    OFF = (4, "off", "Off", "The inverter/charger is disabled.")


class PhoenixInverterMode(VictronEnum):
    """Phoenix Inverter Mode Enum"""

    INVERTER = (
        2,
        "inverter",
        "Inverter",
        "The Phoenix inverter continuously supplies AC power when sufficient DC power is available.",
    )
    OFF = (4, "off", "Off", "The Phoenix inverter output is disabled.")
    ECO = (
        5,
        "eco",
        "Eco",
        "The Phoenix inverter enters a low-power search mode when no significant AC load is detected.",
    )


class State(VictronEnum):
    """State Enum"""

    OFF = (0, "off", "Off", "The device is switched off.")
    LOW_POWER = (1, "low_power", "Low power", "The device is operating in a reduced-power state.")
    FAULT = (2, "fault", "Fault", "The device has stopped because of a fault.")
    BULK = (3, "bulk", "Bulk", "The charger is delivering maximum available current during bulk charging.")
    ABSORPTION = (
        4,
        "absorption",
        "Absorption",
        "The charger is holding the absorption voltage while charge current tapers.",
    )
    FLOAT = (5, "float", "Float", "The charger is maintaining the battery at its float voltage.")
    STORAGE = (6, "storage", "Storage", "The charger is maintaining the lower long-term storage voltage.")
    EQUALIZE = (7, "equalize", "Equalize", "The charger is performing a controlled equalization charge.")
    PASSTHROUGH = (8, "passthrough", "Passthrough", "AC input is being passed through to the AC output.")
    INVERTING = (9, "inverting", "Inverting", "The inverter is supplying AC power from the battery.")
    POWER_ASSIST = (
        10,
        "power_assist",
        "Power Assist",
        "The inverter is supplementing the AC input with battery power.",
    )
    POWER_SUPPLY = (11, "power_supply", "Power supply", "The charger is operating as a regulated DC power supply.")
    SUSTAIN = (
        244,
        "sustain",
        "Sustain",
        "Battery discharge is restricted while the system sustains a safe battery voltage.",
    )
    STARTING_UP = (245, "starting_up", "Starting up", "The device is completing its startup sequence.")
    REPEATED_ABSORPTION = (
        246,
        "repeated_absorption",
        "Repeated absorption",
        "The charger is performing a scheduled repeated absorption cycle.",
    )
    AUTO_EQUALIZE = (
        247,
        "auto_equalize",
        "Auto equalize / recondition",
        "The charger is performing an automatic equalization or reconditioning cycle.",
    )
    BATTERY_SAFE = (
        248,
        "battery_safe",
        "Battery Safe",
        "Charge current is limited to prevent excessive battery voltage rise.",
    )
    EXTERNAL_CONTROL = (
        252,
        "external_control",
        "External control",
        "An external controller determines the device operating state.",
    )
    DISCHARGING = (256, "discharging", "Discharging", "The battery is supplying power to the system.")
    SUSTAIN_ALT = (
        257,
        "sustain_alt",
        "Sustain alt",
        "ESS sustain is active because battery voltage reached the dynamic cutoff.",
    )
    RECHARGING = (
        258,
        "recharging",
        "Recharging",
        "The system is recharging after state of charge fell below its threshold.",
    )
    SCHEDULED_RECHARGING = (
        259,
        "scheduled_recharging",
        "Scheduled recharging",
        "The system is charging during an active scheduled-charge window.",
    )


class GenericAlarmEnum(VictronEnum):
    """Generic Alarm Enum"""

    NO_ALARM = (0, "no_alarm", "No alarm", "No alarm condition is active.")
    WARNING = (1, "warning", "Warning", "A warning condition is active.")
    ALARM = (2, "alarm", "Alarm", "An alarm condition is active.")


class EvChargerMode(VictronEnum):
    """EVCharger Mode Enum"""

    MANUAL = (0, "manual", "Manual", "Charging current and start or stop behavior are controlled manually.")
    AUTO = (1, "auto", "Auto", "The charging station automatically uses available excess solar power.")
    SCHEDULED_CHARGE = (2, "scheduled_charge", "Scheduled charge", "Charging follows the configured charging schedule.")


class EvChargingState(VictronEnum):
    """EV Charging State Enum"""

    NOT_CHARGING = (
        0,
        "not_charging",
        "Not charging",
        "The electric vehicle is connected but is not currently charging.",
    )
    LOW_POWER_MODE = (
        1,
        "low_power_mode",
        "Low power mode",
        "The electric vehicle is charging with power constrained to a low level.",
    )
    CHARGING = (3, "charging", "Charging", "Energy is actively flowing into the electric vehicle battery.")
    SUSTAIN = (
        244,
        "sustain",
        "Sustain",
        "Charging is limited to sustain the electric vehicle battery without increasing its state of charge.",
    )
    WAKE_UP = (245, "wake_up", "Wake up", "The charging station is waking the electric vehicle before charging starts.")
    BLOCKED = (
        250,
        "blocked",
        "Blocked",
        "Charging cannot start because the electric vehicle or charging station is blocking it.",
    )
    UNAVAILABLE = (255, "unavailable", "Unavailable", "The electric vehicle charging state is not available.")
    DISCHARGING = (
        256,
        "discharging",
        "Discharging",
        "Energy is flowing from the electric vehicle battery back to the connected system.",
    )
    SCHEDULED_CHARGING = (
        259,
        "scheduled_charging",
        "Scheduled charging",
        "The electric vehicle is charging during an active scheduled-charge window.",
    )


class EvChargerPosition(VictronEnum):
    """EVCharger Position Enum"""

    AC_OUT = (0, "ac_out", "AC out", "The charging station is connected to the inverter/charger AC output.")
    AC_INPUT = (
        1,
        "ac_input",
        "AC input",
        "The charging station is connected on the AC input side of the inverter/charger.",
    )


class EvChargerStatus(VictronEnum):
    """EVCharger Status Enum"""

    DISCONNECTED = (0, "disconnected", "Disconnected", "No electric vehicle is connected to the charging station.")
    CONNECTED = (1, "connected", "Connected", "An electric vehicle is connected and waiting for charging to start.")
    CHARGING = (
        2,
        "charging",
        "Charging",
        "The charging station is actively delivering energy to the electric vehicle.",
    )
    CHARGED = (3, "charged", "Charged", "The connected electric vehicle has completed charging.")
    WAITING_FOR_SUN = (
        4,
        "waiting_for_sun",
        "Waiting for sun",
        "Charging is paused until sufficient excess solar power is available.",
    )
    WAITING_FOR_RFID = (
        5,
        "waiting_for_rfid",
        "Waiting for RFID",
        "Charging is waiting for authorization from an RFID card.",
    )
    WAITING_FOR_START = (
        6,
        "waiting_for_start",
        "Waiting for start",
        "The vehicle is authorized and connected but charging has not started.",
    )
    LOW_SOC = (7, "low_soc", "Low SoC", "Charging behavior is constrained by a low system battery state of charge.")
    GROUND_TEST_ERROR = (8, "ground_test_error", "Ground test error", "The charging station ground safety test failed.")
    WELDED_CONTACTS_TEST_ERROR = (
        9,
        "welded_contacts_test_error",
        "Welded contacts test error",
        "The charging station detected welded power contacts during its safety test.",
    )
    CP_INPUT_TEST_ERROR = (
        10,
        "cp_input_test_error",
        "CP input test error",
        "The charging station detected an invalid control-pilot input during its safety test.",
    )
    RESIDUAL_CURRENT_DETECTED = (
        11,
        "residual_current_detected",
        "Residual current detected",
        "The charging station stopped because residual leakage current was detected.",
    )
    UNDERVOLTAGE_DETECTED = (
        12,
        "undervoltage_detected",
        "Undervoltage detected",
        "The charging station stopped because AC supply voltage was too low.",
    )
    OVERVOLTAGE_DETECTED = (
        13,
        "overvoltage_detected",
        "Overvoltage detected",
        "The charging station stopped because AC supply voltage was too high.",
    )
    OVERHEATING_DETECTED = (
        14,
        "overheating_detected",
        "Overheating detected",
        "The charging station stopped because its temperature was too high.",
    )
    RESERVED15 = (15, "reserved15", "Reserved", "Status code 15 is reserved for future EV charging station use.")
    RESERVED16 = (16, "reserved16", "Reserved", "Status code 16 is reserved for future EV charging station use.")
    RESERVED17 = (17, "reserved17", "Reserved", "Status code 17 is reserved for future EV charging station use.")
    RESERVED18 = (18, "reserved18", "Reserved", "Status code 18 is reserved for future EV charging station use.")
    RESERVED19 = (19, "reserved19", "Reserved", "Status code 19 is reserved for future EV charging station use.")
    CHARGING_LIMIT = (
        20,
        "charging_limit",
        "Charging limit",
        "Charging is constrained by an active current or power limit.",
    )
    START_CHARGING = (21, "start_charging", "Start charging", "The charging station is initiating a charging session.")
    SWITCHING_TO_3_PHASE = (
        22,
        "switching_to_3_phase",
        "Switching to 3 phase",
        "The charging station is changing from single-phase to three-phase charging.",
    )
    SWITCHING_TO_1_PHASE = (
        23,
        "switching_to_1_phase",
        "Switching to 1 phase",
        "The charging station is changing from three-phase to single-phase charging.",
    )


class TemperatureStatus(VictronEnum):
    """Temperature sensor status enum"""

    OK = (0, "ok", "Ok", "The temperature sensor reports this status: Ok.")
    DISCONNECTED = (1, "disconnected", "Disconnected", "The temperature sensor reports this status: Disconnected.")
    SHORT_CIRCUITED = (
        2,
        "short_circuited",
        "Short circuited",
        "The temperature sensor reports this status: Short circuited.",
    )
    REVERSE_POLARITY = (
        3,
        "reverse_polarity",
        "Reverse polarity",
        "The temperature sensor reports this status: Reverse polarity.",
    )
    UNKNOWN = (4, "unknown", "Unknown", "The temperature sensor reports this status: Unknown.")


class TemperatureType(VictronEnum):
    """Temperature sensor type enum"""

    BATTERY = (0, "battery", "Battery", "The temperature sensor is configured for this measurement type: Battery.")
    FRIDGE = (1, "fridge", "Fridge", "The temperature sensor is configured for this measurement type: Fridge.")
    GENERIC = (2, "generic", "Generic", "The temperature sensor is configured for this measurement type: Generic.")
    ROOM = (3, "room", "Room", "The temperature sensor is configured for this measurement type: Room.")
    OUTDOOR = (4, "outdoor", "Outdoor", "The temperature sensor is configured for this measurement type: Outdoor.")
    WATER_HEATER = (
        5,
        "water_heater",
        "Water heater",
        "The temperature sensor is configured for this measurement type: Water heater.",
    )
    FREEZER = (6, "freezer", "Freezer", "The temperature sensor is configured for this measurement type: Freezer.")


class FluidType(VictronEnum):
    """Fluid type enum"""

    FUEL = (0, "fuel", "Fuel", "The tank is configured for this fluid type: Fuel.")
    FRESH_WATER = (1, "fresh_water", "Fresh water", "The tank is configured for this fluid type: Fresh water.")
    WASTE_WATER = (2, "waste_water", "Waste water", "The tank is configured for this fluid type: Waste water.")
    LIVE_WELL = (3, "live_well", "Live well", "The tank is configured for this fluid type: Live well.")
    OIL = (4, "oil", "Oil", "The tank is configured for this fluid type: Oil.")
    BLACK_WATER = (
        5,
        "black_water",
        "Black water (sewage)",
        "The tank is configured for this fluid type: Black water (sewage).",
    )
    GASOLINE = (6, "gasoline", "Gasoline", "The tank is configured for this fluid type: Gasoline.")
    DIESEL = (7, "diesel", "Diesel", "The tank is configured for this fluid type: Diesel.")
    LPG = (
        8,
        "lpg",
        "Liquid petroleum gas (LPG)",
        "The tank is configured for this fluid type: Liquid petroleum gas (LPG).",
    )
    LNG = (
        9,
        "lng",
        "Liquid natural gas (LNG)",
        "The tank is configured for this fluid type: Liquid natural gas (LNG).",
    )
    HYDRAULIC_OIL = (10, "hydraulic_oil", "Hydraulic oil", "The tank is configured for this fluid type: Hydraulic oil.")
    RAW_WATER = (11, "raw_water", "Raw water", "The tank is configured for this fluid type: Raw water.")


class MppOperationMode(VictronEnum):
    """MPP Operation Mode Enum"""

    OFF = (0, "off", "Off", "The solar charger is not performing maximum power point tracking.")
    VOLTAGE_CURRENT_LIMITED = (
        1,
        "voltage_current_limited",
        "Voltage/current limited",
        "PV operation is limited by a voltage or current constraint.",
    )
    MPPT_ACTIVE = (
        2,
        "mppt_active",
        "MPPT active",
        "Maximum power point tracking is actively optimizing PV production.",
    )
    NOT_AVAILABLE = (255, "not_available", "Not available", "The device does not provide an MPPT operating mode.")


class ESSMode(VictronEnum):
    """ESS Mode Enum"""

    SELF_CONSUMPTION_BATTERYLIFE = (
        0,
        "self_consumption_batterylife",
        "Self-consumption (BatteryLife)",
        "ESS maximizes self-consumption while BatteryLife dynamically protects battery state of charge.",
    )
    SELF_CONSUMPTION = (
        1,
        "self_consumption",
        "Self-consumption",
        "ESS maximizes self-consumption using the configured minimum state of charge.",
    )
    KEEP_CHARGED = (
        2,
        "keep_charged",
        "Keep charged",
        "ESS keeps the battery charged and avoids normal battery discharge.",
    )
    EXTERNAL_CONTROL = (
        3,
        "external_control",
        "External control",
        "An external controller determines ESS charge and discharge behavior.",
    )


class GeneratorRunningByConditionCode(VictronEnum):
    """Generator Running By Condition Code Enum"""

    STOPPED = (0, "stopped", "Stopped", "The generator is stopped because no start condition is active.")
    MANUAL = (1, "manual", "Manual", "The generator is running because it was started manually.")
    TEST_RUN = (2, "test_run", "Test run", "The generator is running for a scheduled or manually requested test run.")
    LOST_COMMS = (
        3,
        "lost_comms",
        "Lost comms",
        "The generator is running because communication with its controller was lost.",
    )
    SOC = (4, "soc", "SoC", "The generator is running because this start condition is active: SoC.")
    AC_LOAD = (5, "ac_load", "AC load", "The generator is running because this start condition is active: AC load.")
    BATTERY_CURRENT = (
        6,
        "battery_current",
        "Battery current",
        "The generator is running because this start condition is active: Battery current.",
    )
    BATTERY_VOLTS = (
        7,
        "battery_volts",
        "Battery volts",
        "The generator is running because this start condition is active: Battery volts.",
    )
    INV_TEMP = (
        8,
        "inv_temp",
        "Inverter temperature",
        "The generator is running because this start condition is active: Inverter temperature.",
    )
    INV_OVERLOAD = (
        9,
        "inv_overload",
        "Inverter overload",
        "The generator is running because this start condition is active: Inverter overload.",
    )
    STOP_ON_AC1 = (10, "stop_on_ac1", "Stop on AC1", "The generator is stopping because AC input 1 became available.")


class DESSReactiveStrategy(VictronEnum):
    """DESS Reactive Strategy Enum"""

    SCHEDULED_SELFCONSUME = (
        1,
        "scheduled_selfconsume",
        "Scheduled self-consume",
        "Dynamic ESS follows the scheduled target while prioritizing local self-consumption.",
    )
    SCHEDULED_CHARGE_ALLOW_GRID = (
        2,
        "scheduled_charge_allow_grid",
        "Scheduled charge allow grid",
        "Dynamic ESS charges on schedule and may import the required power from the grid.",
    )
    SCHEDULED_CHARGE_ENHANCED = (
        3,
        "scheduled_charge_enhanced",
        "Scheduled charge enhanced",
        "Dynamic ESS increases scheduled charging to recover the target state of charge.",
    )
    SELFCONSUME_ACCEPT_CHARGE = (
        4,
        "selfconsume_accept_charge",
        "Self-consume accept charge",
        "Dynamic ESS accepts additional charging while operating in self-consumption mode.",
    )
    IDLE_SCHEDULED_FEEDIN = (
        5,
        "idle_scheduled_feedin",
        "Idle scheduled feed-in",
        "Dynamic ESS remains idle while scheduled energy is exported to the grid.",
    )
    SCHEDULED_DISCHARGE = (
        6,
        "scheduled_discharge",
        "Scheduled discharge",
        "Dynamic ESS discharges the battery to follow the active schedule.",
    )
    SELFCONSUME_ACCEPT_DISCHARGE = (
        7,
        "selfconsume_accept_discharge",
        "Self-consume accept discharge",
        "Dynamic ESS permits additional battery discharge for local self-consumption.",
    )
    IDLE_MAINTAIN_SURPLUS = (
        8,
        "idle_maintain_surplus",
        "Idle maintain surplus",
        "Dynamic ESS remains idle to preserve an available energy surplus.",
    )
    IDLE_MAINTAIN_TARGETSOC = (
        9,
        "idle_maintain_targetsoc",
        "Idle maintain target SoC",
        "Dynamic ESS remains idle because the battery is at its target state of charge.",
    )
    SCHEDULED_CHARGE_SMOOTH_TRANSITION = (
        10,
        "scheduled_charge_smooth_transition",
        "Scheduled charge smooth transition",
        "Dynamic ESS gradually transitions into scheduled charging.",
    )
    SCHEDULED_CHARGE_FEEDIN = (
        11,
        "scheduled_charge_feedin",
        "Scheduled charge feed-in",
        "Dynamic ESS charges on schedule while allowing permitted grid feed-in.",
    )
    SCHEDULED_CHARGE_NO_GRID = (
        12,
        "scheduled_charge_no_grid",
        "Scheduled charge no grid",
        "Dynamic ESS charges on schedule without importing energy from the grid.",
    )
    SCHEDULED_MINIMUM_DISCHARGE = (
        13,
        "scheduled_minimum_discharge",
        "Scheduled minimum discharge",
        "Dynamic ESS applies the minimum discharge needed to follow the schedule.",
    )
    SELFCONSUME_NO_GRID = (
        14,
        "selfconsume_no_grid",
        "Self-consume no grid",
        "Dynamic ESS serves local loads without importing energy from the grid.",
    )
    IDLE_NO_OPPORTUNITY = (
        15,
        "idle_no_opportunity",
        "Idle no opportunity",
        "Dynamic ESS remains idle because no profitable charge or discharge opportunity exists.",
    )
    UNSCHEDULED_CHARGE_CATCHUP_TARGETSOC = (
        16,
        "unscheduled_charge_catchup_targetsoc",
        "Unscheduled charge catch-up target SoC",
        "Dynamic ESS charges outside the schedule to catch up to the target state of charge.",
    )
    SELFCONSUME_INCREASED_DISCHARGE = (
        17,
        "selfconsume_increased_discharge",
        "Self-consume increased discharge",
        "Dynamic ESS increases battery discharge to cover local consumption.",
    )
    KEEP_BATTERY_CHARGED = (
        18,
        "keep_battery_charged",
        "Keep battery charged",
        "Dynamic ESS retains energy to keep the battery charged.",
    )
    SCHEDULED_DISCHARGE_SMOOTH_TRANSITION = (
        19,
        "scheduled_discharge_smooth_transition",
        "Scheduled discharge smooth transition",
        "Dynamic ESS gradually transitions into scheduled discharging.",
    )
    DESS_DISABLED = (
        92,
        "dess_disabled",
        "DESS disabled",
        "No reactive strategy is active because Dynamic ESS is disabled.",
    )
    SELFCONSUME_UNEXPECTED_EXCEPTION = (
        93,
        "selfconsume_unexpected_exception",
        "Self-consume unexpected exception",
        "Dynamic ESS fell back from self-consumption because of an unexpected internal exception.",
    )
    SELFCONSUME_FAULTY_CHARGERATE = (
        94,
        "selfconsume_faulty_chargerate",
        "Self-consume faulty charge rate",
        "Dynamic ESS cannot use the calculated charge rate for self-consumption.",
    )
    UNKNOWN_OPERATING_MODE = (
        95,
        "unknown_operating_mode",
        "Unknown operating mode",
        "Dynamic ESS cannot map the current system operating mode to a strategy.",
    )
    ESS_LOW_SOC = (
        96,
        "ess_low_soc",
        "ESS low SoC",
        "Dynamic ESS is constrained because ESS reports a low battery state of charge.",
    )
    SELFCONSUME_UNMAPPED_STATE = (
        97,
        "selfconsume_unmapped_state",
        "Self-consume unmapped state",
        "Dynamic ESS cannot map the current ESS state to self-consumption behavior.",
    )
    SELFCONSUME_UNPREDICTED = (
        98,
        "selfconsume_unpredicted",
        "Self-consume unpredicted",
        "Dynamic ESS is self-consuming because actual power flow differs from the schedule.",
    )
    NO_WINDOW = (99, "no_window", "No window", "Dynamic ESS has no applicable schedule window.")


class DESSStrategy(VictronEnum):
    """DESS Strategy Enum"""

    TARGETSOC = (0, "targetsoc", "Target SoC", "Dynamic ESS follows scheduled target state-of-charge values.")
    SELFCONSUME = (1, "selfconsume", "Self-consume", "Dynamic ESS prioritizes local self-consumption.")
    PROBATTERY = (
        2,
        "probattery",
        "Pro battery",
        "Dynamic ESS prioritizes protecting and retaining energy in the battery.",
    )
    PROGRID = (3, "progrid", "Pro grid", "Dynamic ESS prioritizes energy trading and grid interaction.")


class DESSErrorCode(VictronEnum):
    """DESS Error Code Enum"""

    NO_ERROR = (0, "no_error", "No error", "Dynamic ESS has no active configuration or scheduling error.")
    NO_ESS = (1, "no_ess", "No ESS", "Dynamic ESS cannot operate because ESS is unavailable.")
    ESS_MODE = (2, "ess_mode", "ESS mode", "Dynamic ESS cannot operate with the currently selected ESS mode.")
    NO_SCHEDULE = (3, "no_schedule", "No matching schedule", "Dynamic ESS has no schedule matching the current time.")
    SOC_LOW = (4, "soc_low", "SoC low", "Dynamic ESS is constrained because battery state of charge is too low.")
    BATTRY_CAPACITY_NOT_CONFIGURED = (
        5,
        "battry_capacity_not_configured",
        "Battery capacity not configured",
        "Dynamic ESS cannot calculate a schedule because battery capacity is not configured.",
    )


class DESSMode(VictronEnum):
    """DESS Mode Enum"""

    OFF = (0, "off", "Off", "Dynamic ESS is disabled.")
    AUTO_VRM = (1, "auto_vrm", "Auto / VRM", "Dynamic ESS follows schedules received automatically from VRM.")
    BUY = (2, "buy", "Buy", "Dynamic ESS is forced to buy energy from the grid.")
    SELL = (3, "sell", "Sell", "Dynamic ESS is forced to sell energy to the grid.")
    NODE_RED = (4, "node_red", "Node-RED", "Dynamic ESS is controlled locally, such as through Node-RED.")


class DESSRestrictions(VictronEnum):
    """DESS Restrictions Enum"""

    NO_RESTRICTIONS = (
        0,
        "no_restrictions",
        "No restrictions between battery and the grid",
        "Energy may flow in either direction between the battery and grid.",
    )
    BATTERY_TO_GRID_RESTRICTED = (
        1,
        "battery_to_grid_restricted",
        "Battery to grid energy flow restricted",
        "Exporting battery energy to the grid is prohibited.",
    )
    GRID_TO_BATTERY_RESTRICTED = (
        2,
        "grid_to_battery_restricted",
        "Grid to battery energy flow restricted",
        "Charging the battery from the grid is prohibited.",
    )
    NO_FLOW = (
        3,
        "no_flow",
        "No energy flow between battery and grid",
        "Energy flow between the battery and grid is prohibited in both directions.",
    )


class ErrorCode(VictronEnum):
    """Generic Error Code Enum"""

    NO_ERROR = (0, "no_error", "No error", "The device reports no active error.")
    BATTERY_VOLTAGE_TOO_HIGH = (
        2,
        "battery_voltage_too_high",
        "Battery voltage too high",
        "The device reports this active error condition: Battery voltage too high.",
    )
    CHARGER_TEMPERATURE_TOO_HIGH = (
        17,
        "charger_temperature_too_high",
        "Charger temperature too high",
        "The device reports this active error condition: Charger temperature too high.",
    )
    CHARGER_OVER_CURRENT = (
        18,
        "charger_over_current",
        "Charger over current",
        "The device reports this active error condition: Charger over current.",
    )
    CHARGER_CURRENT_REVERSED = (
        19,
        "charger_current_reversed",
        "Charger current reversed",
        "The device reports this active error condition: Charger current reversed.",
    )
    BULK_TIME_LIMIT_EXCEEDED = (
        20,
        "bulk_time_limit_exceeded",
        "Bulk time limit exceeded",
        "The device reports this active error condition: Bulk time limit exceeded.",
    )
    CURRENT_SENSOR_ISSUE = (
        21,
        "current_sensor_issue",
        "Current sensor issue",
        "The device reports this active error condition: Current sensor issue.",
    )
    TERMINALS_OVERHEATED = (
        26,
        "terminals_overheated",
        "Terminals overheated",
        "The device reports this active error condition: Terminals overheated.",
    )
    CONVERTER_ISSUE = (
        28,
        "converter_issue",
        "Converter issue",
        "The device reports this active error condition: Converter issue.",
    )
    INPUT_VOLTAGE_TOO_HIGH = (
        33,
        "input_voltage_too_high",
        "Input voltage too high (solar panel)",
        "The device reports this active error condition: Input voltage too high (solar panel).",
    )
    INPUT_CURRENT_TOO_HIGH = (
        34,
        "input_current_too_high",
        "Input current too high (solar panel)",
        "The device reports this active error condition: Input current too high (solar panel).",
    )
    INPUT_SHUTDOWN_BATTERY_VOLTAGE_TOO_HIGH = (
        38,
        "input_shutdown_battery_voltage_too_high",
        "Input shutdown (battery voltage too high)",
        "The device reports this active error condition: Input shutdown (battery voltage too high).",
    )
    INPUT_SHUTDOWN_REVERSE_CURRENT = (
        39,
        "input_shutdown_reverse_current",
        "Input shutdown (reverse current)",
        "The device reports this active error condition: Input shutdown (reverse current).",
    )
    LOST_COMMUNICATION_WITH_DEVICE = (
        65,
        "lost_communication_with_device",
        "Lost communication with device",
        "The device reports this active error condition: Lost communication with device.",
    )
    SYNCHRONIZED_CHARGING_CONFIG_ISSUE = (
        66,
        "synchronized_charging_config_issue",
        "Synchronized charging config issue",
        "The device reports this active error condition: Synchronized charging config issue.",
    )
    BMS_CONNECTION_LOST = (
        67,
        "bms_connection_lost",
        "BMS connection lost",
        "The device reports this active error condition: BMS connection lost.",
    )
    NETWORK_MISCONFIGURED = (
        68,
        "network_misconfigured",
        "Network misconfigured",
        "The device reports this active error condition: Network misconfigured.",
    )
    FACTORY_CALIBRATION_DATA_LOST = (
        116,
        "factory_calibration_data_lost",
        "Factory calibration data lost",
        "The device reports this active error condition: Factory calibration data lost.",
    )
    INVALID_INCOMPATIBLE_FIRMWARE = (
        117,
        "invalid_incompatible_firmware",
        "Invalid/incompatible firmware",
        "The device reports this active error condition: Invalid/incompatible firmware.",
    )
    USER_SETTINGS_INVALID = (
        119,
        "user_settings_invalid",
        "User settings invalid",
        "The device reports this active error condition: User settings invalid.",
    )


class DigitalInputInputState(VictronEnum):
    """Raw input state: High/Open (0) or Low/Closed (1)."""

    HIGH_OPEN = (0, "high_open", "High/open", "The raw digital input is electrically high or the contact is open.")
    LOW_CLOSED = (1, "low_closed", "Low/closed", "The raw digital input is electrically low or the contact is closed.")


class DigitalInputType(VictronEnum):
    """Type of digital input."""

    DISABLED = (0, "disabled", "Disabled", "The digital input is configured for this function: Disabled.")
    PULSE_METER = (1, "pulse_meter", "Pulse meter", "The digital input is configured for this function: Pulse meter.")
    DOOR_ALARM = (2, "door_alarm", "Door alarm", "The digital input is configured for this function: Door alarm.")
    BILGE_PUMP = (3, "bilge_pump", "Bilge pump", "The digital input is configured for this function: Bilge pump.")
    BILGE_ALARM = (4, "bilge_alarm", "Bilge alarm", "The digital input is configured for this function: Bilge alarm.")
    BURGLAR_ALARM = (
        5,
        "burglar_alarm",
        "Burglar alarm",
        "The digital input is configured for this function: Burglar alarm.",
    )
    SMOKE_ALARM = (6, "smoke_alarm", "Smoke alarm", "The digital input is configured for this function: Smoke alarm.")
    FIRE_ALARM = (7, "fire_alarm", "Fire alarm", "The digital input is configured for this function: Fire alarm.")
    CO2_ALARM = (8, "co2_alarm", "CO2 alarm", "The digital input is configured for this function: CO2 alarm.")
    GENERATOR = (9, "generator", "Generator", "The digital input is configured for this function: Generator.")
    TOUCH_INPUT_CONTROL = (
        10,
        "touch_input_control",
        "Touch input control",
        "The digital input is configured for this function: Touch input control.",
    )


class DigitalInputState(VictronEnum):
    """Translated input state (determined by input type)."""

    LOW = (0, "low", "Low", "The configured digital-input translation reports this state: Low.")
    HIGH = (1, "high", "High", "The configured digital-input translation reports this state: High.")
    OFF = (2, "off", "Off", "The configured digital-input translation reports this state: Off.")
    ON = (3, "on", "On", "The configured digital-input translation reports this state: On.")
    NO = (4, "no", "No", "The configured digital-input translation reports this state: No.")
    YES = (5, "yes", "Yes", "The configured digital-input translation reports this state: Yes.")
    OPEN = (6, "open", "Open", "The configured digital-input translation reports this state: Open.")
    CLOSED = (7, "closed", "Closed", "The configured digital-input translation reports this state: Closed.")
    OK = (8, "ok", "Ok", "The configured digital-input translation reports this state: Ok.")
    ALARM = (9, "alarm", "Alarm", "The configured digital-input translation reports this state: Alarm.")
    RUNNING = (10, "running", "Running", "The configured digital-input translation reports this state: Running.")
    STOPPED = (11, "stopped", "Stopped", "The configured digital-input translation reports this state: Stopped.")


class ESSState(VictronEnum):
    """ESS State Enum"""

    # Optimized mode with BatteryLife:
    # 1 is Value set by the GUI when BatteryLife is enabled. Hub4Control uses it to find the right BatteryLife state (values 2-7) based on system state
    WITH_BATTERY_LIFE = (
        1,
        "with_battery_life",
        "Optimized mode with BatteryLife",
        "ESS reports this BatteryLife operating condition: Optimized mode with BatteryLife.",
    )
    SELF_CONSUMPTION = (
        2,
        "self_consumption",
        "Self-consumption",
        "ESS reports this BatteryLife operating condition: Self-consumption.",
    )
    SELF_CONSUMPTION_SOC_EXCEEDS_85 = (
        3,
        "self_consumption_soc_exceeds_85",
        "Self-consumption, SoC exceeds 85%",
        "ESS reports this BatteryLife operating condition: Self-consumption, SoC exceeds 85%.",
    )
    SELF_CONSUMPTION_SOC_AT_100 = (
        4,
        "self_consumption_soc_at_100",
        "Self-consumption, SoC at 100%",
        "ESS reports this BatteryLife operating condition: Self-consumption, SoC at 100%.",
    )
    SOC_BELOW_BATTERY_LIFE_DYNAMIC_SOC_LIMIT = (
        5,
        "soc_below_battery_life_dynamic_soc_limit",
        "SoC below BatteryLife dynamic SoC limit",
        "ESS reports this BatteryLife operating condition: SoC below BatteryLife dynamic SoC limit.",
    )
    SOC_BELOW_SOC_LIMIT_24_HOURS = (
        6,
        "soc_below_soc_limit_24_hours",
        "SoC has been below SoC limit for more than 24 hours. Charging battery with 5 amps",
        "ESS reports this BatteryLife operating condition: SoC has been below SoC limit for more than 24 hours. Charging battery with 5 amps.",
    )
    SUSTAIN = (
        7,
        "sustain",
        "Multi/Quattro is in sustain",
        "ESS reports this BatteryLife operating condition: Multi/Quattro is in sustain.",
    )
    RECHARGE = (
        8,
        "recharge",
        "Recharge, SoC dropped 5% or more below minimum SoC",
        "ESS reports this BatteryLife operating condition: Recharge, SoC dropped 5% or more below minimum SoC.",
    )
    # Keep batteries charged mode:
    KEEP_BATTERIES_CHARGED = (
        9,
        "keep_batteries_charged",
        "'Keep batteries charged' mode enabled",
        "ESS reports this BatteryLife operating condition: 'Keep batteries charged' mode enabled.",
    )
    # Optimized mode without BatteryLife:
    SELF_CONSUMPTION_SOC_ABOVE_MIN = (
        10,
        "self_consumption_soc_above_min",
        "Self-consumption, SoC at or above minimum SoC",
        "ESS reports this BatteryLife operating condition: Self-consumption, SoC at or above minimum SoC.",
    )
    SELF_CONSUMPTION_SOC_BELOW_MIN = (
        11,
        "self_consumption_soc_below_min",
        "Self-consumption, SoC is below minimum SoC",
        "ESS reports this BatteryLife operating condition: Self-consumption, SoC is below minimum SoC.",
    )
    RECHARGE_NO_BATTERY_LIFE = (
        12,
        "recharge_no_battery_life",
        "Recharge, SoC dropped 5% or more below minimum SoC (No BatteryLife)",
        "ESS reports this BatteryLife operating condition: Recharge, SoC dropped 5% or more below minimum SoC (No BatteryLife).",
    )


class ESSUserMode(VictronEnum):
    """ESS User Mode Enum - matches the 4 user-facing modes shown in VRM."""

    OPTIMIZED_BATTERY_LIFE = (
        1,
        "optimized_battery_life",
        "Optimized (with BatteryLife)",
        "ESS optimizes self-consumption while BatteryLife dynamically adjusts the discharge floor.",
    )
    OPTIMIZED_NO_BATTERY_LIFE = (
        10,
        "optimized_no_battery_life",
        "Optimized (without BatteryLife)",
        "ESS optimizes self-consumption using a fixed minimum state of charge.",
    )
    KEEP_BATTERIES_CHARGED = (
        9,
        "keep_batteries_charged",
        "Keep batteries charged",
        "ESS uses available AC power to keep the batteries charged.",
    )
    EXTERNAL_CONTROL = (
        3,
        "external_control",
        "External control",
        "An external controller manages ESS charge and discharge behavior.",
    )


class ESSModeHub4(VictronEnum):
    """ESS Mode Enum for Hub4Control"""

    PHASE_COMPENSATION_ENABLED = (
        1,
        "phase_compensation_enabled",
        "Optimized mode or 'keep batteries charged' and phase compensation enabled",
        "ESS optimization or keep-charged mode is active with phase compensation enabled.",
    )
    PHASE_COMPENSATION_DISABLED = (
        2,
        "phase_compensation_disabled",
        "Optimized mode or 'keep batteries charged' and phase compensation disabled",
        "ESS optimization or keep-charged mode is active with phase compensation disabled.",
    )
    EXTERNAL_CONTROL = (3, "external_control", "External control", "An external controller manages Hub4 power flow.")


class ACActiveInputSource(VictronEnum):
    """AC Active Input Source Enum"""

    UNKNOWN = (
        0,
        "unknown",
        "Unknown",
        "The active AC input source cannot be identified from the system configuration.",
    )
    GRID = (1, "grid", "Grid", "The active AC input is configured as utility grid power.")
    GENERATOR = (2, "generator", "Generator", "The active AC input is configured as generator power.")
    SHORE_POWER = (3, "shore_power", "Shore power", "The active AC input is configured as shore power.")
    NOT_CONNECTED = (
        240,
        "not_connected",
        "Not connected",
        "No AC input is connected; the system is operating without an external AC source.",
    )


class AcInputTypeEnum(VictronEnum):
    """AC Input Type Enum"""

    NOT_USED = (0, "not_used", "Not used", "The AC input is configured as unused.")
    GRID = (1, "grid", "Grid", "The AC input is configured for utility grid power.")
    GENERATOR = (2, "generator", "Generator", "The AC input is configured for generator power.")
    SHORE = (3, "shore", "Shore", "The AC input is configured for shore power.")


class ChargeSchedule(VictronEnum):
    """Charge Schedule Enum"""

    DISABLED_SUNDAY = (-10, "disabled_sunday", "Disabled (Sunday)", "Disables this scheduled-charge slot on sunday.")
    DISABLED_WEEKEND = (
        -9,
        "disabled_weekend",
        "Disabled (Weekends)",
        "Disables this scheduled-charge slot on weekends.",
    )
    DISABLED_WEEKDAYS = (
        -8,
        "disabled_weekdays",
        "Disabled (Weekdays)",
        "Disables this scheduled-charge slot on weekdays.",
    )
    DISABLED_EVERY_DAY = (
        -7,
        "disabled_every_day",
        "Disabled (Every day)",
        "Disables this scheduled-charge slot on every day.",
    )
    DISABLED_SATURDAY = (
        -6,
        "disabled_saturday",
        "Disabled (Saturday)",
        "Disables this scheduled-charge slot on saturday.",
    )
    DISABLED_FRIDAY = (-5, "disabled_friday", "Disabled (Friday)", "Disables this scheduled-charge slot on friday.")
    DISABLED_THURSDAY = (
        -4,
        "disabled_thursday",
        "Disabled (Thursday)",
        "Disables this scheduled-charge slot on thursday.",
    )
    DISABLED_WEDNESDAY = (
        -3,
        "disabled_wednesday",
        "Disabled (Wednesday)",
        "Disables this scheduled-charge slot on wednesday.",
    )
    DISABLED_TUESDAY = (-2, "disabled_tuesday", "Disabled (Tuesday)", "Disables this scheduled-charge slot on tuesday.")
    DISABLED_MONDAY = (-1, "disabled_monday", "Disabled (Monday)", "Disables this scheduled-charge slot on monday.")
    SUNDAY = (0, "sunday", "Sunday", "Runs this scheduled-charge slot on sunday.")
    MONDAY = (1, "monday", "Monday", "Runs this scheduled-charge slot on monday.")
    TUESDAY = (2, "tuesday", "Tuesday", "Runs this scheduled-charge slot on tuesday.")
    WEDNESDAY = (3, "wednesday", "Wednesday", "Runs this scheduled-charge slot on wednesday.")
    THURSDAY = (4, "thursday", "Thursday", "Runs this scheduled-charge slot on thursday.")
    FRIDAY = (5, "friday", "Friday", "Runs this scheduled-charge slot on friday.")
    SATURDAY = (6, "saturday", "Saturday", "Runs this scheduled-charge slot on saturday.")
    EVERY_DAY = (7, "every_day", "Every day", "Runs this scheduled-charge slot on every day.")
    WEEKDAYS = (8, "weekdays", "Weekdays", "Runs this scheduled-charge slot on weekdays.")
    WEEKENDS = (9, "weekends", "Weekends", "Runs this scheduled-charge slot on weekends.")


class ActiveInputEnum(VictronEnum):
    """Active Input Enum"""

    AC_INPUT_1 = (0, "ac_input_1", "AC input 1", "AC input 1 is the active source.")
    AC_INPUT_2 = (1, "ac_input_2", "AC input 2", "AC input 2 is the active source.")
    DISCONNECTED = (240, "disconnected", "Disconnected", "Neither AC input is currently connected.")


class SolarChargerDeviceOffReason(VictronEnum):
    """Solar Charger Device Off Reason Enum"""

    NONE = (0x00, "none", "-", "No device-off reason is active.")
    NO_INPUT_POWER = (
        0x01,
        "no_input_power",
        "No/low input power",
        "Solar charger operation is prevented for this reason: No/low input power.",
    )
    SWITCHED_OFF_POWER_SWITCH = (
        0x02,
        "switched_off_power_switch",
        "Switched off (power switch)",
        "Solar charger operation is prevented for this reason: Switched off (power switch).",
    )
    SWITCHED_OFF_DEVICE_MODE_REGISTER = (
        0x04,
        "switched_off_device_mode_register",
        "Switched off (device mode register)",
        "Solar charger operation is prevented for this reason: Switched off (device mode register).",
    )
    REMOTE_INPUT = (
        0x08,
        "remote_input",
        "Remote input",
        "Solar charger operation is prevented for this reason: Remote input.",
    )
    PROTECTIVE_ACTION = (
        0x10,
        "protective_action",
        "Protection active",
        "Solar charger operation is prevented for this reason: Protection active.",
    )
    NEED_TOKEN = (
        0x20,
        "need_token",
        "Need token for operation",
        "Solar charger operation is prevented for this reason: Need token for operation.",
    )
    SIGNAL_FROM_BMS = (
        0x40,
        "signal_from_bms",
        "Signal from BMS",
        "Solar charger operation is prevented for this reason: Signal from BMS.",
    )
    ENGINE_SHUTDOWN = (
        0x80,
        "engine_shutdown",
        "Engine shutdown on low input voltage",
        "Solar charger operation is prevented for this reason: Engine shutdown on low input voltage.",
    )
    ANALYSING_INPUT_VOLTAGE = (
        0x100,
        "analysing_input_voltage",
        "Analysing input voltage",
        "Solar charger operation is prevented for this reason: Analysing input voltage.",
    )
    LOW_TEMPERATURE = (
        0x200,
        "low_temperature",
        "Low temperature",
        "Solar charger operation is prevented for this reason: Low temperature.",
    )
    NO_PANEL_POWER = (
        0x400,
        "no_panel_power",
        "No/low panel power",
        "Solar charger operation is prevented for this reason: No/low panel power.",
    )
    NO_BATTERY_POWER = (
        0x800,
        "no_battery_power",
        "No/low battery power",
        "Solar charger operation is prevented for this reason: No/low battery power.",
    )
    ACTIVE_ALARM = (
        0x8000,
        "active_alarm",
        "Active alarm",
        "Solar charger operation is prevented for this reason: Active alarm.",
    )


class BatteryState(VictronEnum):
    """Battery state Enum"""

    IDLE = (0, "idle", "Idle", "The battery is neither charging nor discharging significantly.")
    CHARGING = (1, "charging", "Charging", "Net current is flowing into the battery.")
    DISCHARGING = (2, "discharging", "Discharging", "Net current is flowing out of the battery.")


class SwitchableOutputType(VictronEnum):
    """SwitchableOutput type Enum"""

    MOMENTARY = (0, "momentary", "Momentary", "The switchable output uses this control interface: Momentary.")
    TOGGLE = (1, "toggle", "Toggle", "The switchable output uses this control interface: Toggle.")
    DIMMABLE = (2, "dimmable", "Dimmable", "The switchable output uses this control interface: Dimmable.")
    TEMPERATURE_SETPOINT = (
        3,
        "temperature_setpoint",
        "Temperature setpoint",
        "The switchable output uses this control interface: Temperature setpoint.",
    )
    STEPPED_SWITCH = (
        4,
        "stepped_switch",
        "Stepped switch",
        "The switchable output uses this control interface: Stepped switch.",
    )
    SLAVE_MODE = (5, "slave_mode", "Slave mode", "The switchable output uses this control interface: Slave mode.")
    DROPDOWN = (6, "dropdown", "Dropdown", "The switchable output uses this control interface: Dropdown.")
    BASIC_SLIDER = (
        7,
        "basic_slider",
        "Basic slider",
        "The switchable output uses this control interface: Basic slider.",
    )
    NUMERIC_INPUT = (
        8,
        "numeric_input",
        "Numeric input",
        "The switchable output uses this control interface: Numeric input.",
    )
    THREE_STATE_SWITCH = (
        9,
        "three_state_switch",
        "Three-state switch",
        "The switchable output uses this control interface: Three-state switch.",
    )
    BILGE_PUMP_CONTROL = (
        10,
        "bilge_pump_control",
        "Bilge pump control",
        "The switchable output uses this control interface: Bilge pump control.",
    )
    RGB_COLOR_WHEEL = (
        11,
        "rgb_color_wheel",
        "RGB color wheel",
        "The switchable output uses this control interface: RGB color wheel.",
    )
    CCT_COLOR_WHEEL = (
        12,
        "cct_color_wheel",
        "CCT color wheel",
        "The switchable output uses this control interface: CCT color wheel.",
    )
    RGBW_COLOR_WHEEL = (
        13,
        "rgbw_color_wheel",
        "RGBW color wheel",
        "The switchable output uses this control interface: RGBW color wheel.",
    )
