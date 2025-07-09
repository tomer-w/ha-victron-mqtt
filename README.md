# Victron Venus MQTT Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-green.svg)](https://github.com/custom-components/hacs)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)
[![Validate](https://github.com/tomer-w/ha-victron-mqtt/actions/workflows/validate.yaml/badge.svg)](https://github.com/tomer-w/ha-victron-mqtt/actions/workflows/validate.yaml)

A Home Assistant integration that connects to Victron Energy devices using MQTT, providing real-time monitoring of your Victron system including inverters, solar chargers, and battery systems.

## Features

- 🔌 Auto-discovery of Victron devices via SSDP ([Cerbo GX](https://www.victronenergy.com/communication-centres/cerbo-gx), etc)
- 📊 Comprehensive sensor data including:
  - Battery metrics (voltage, current, power, temperature, state of charge)
  - Solar/PV metrics (voltage, current, power, yield)
  - Grid metrics (voltage, current, power, energy)
  - Inverter metrics (input/output power, frequency)
  - EV Charger metrics
- 🕹️ Two-way control over your Victron installation:  
   - inverter mode (On, Off, Charger Only, Inverter Only)  
   - EV Charger (On, Off, current limit)  
   - charger current limit
  - inverter mode (On, Off, Charger Only, Inverter Only)
  - EV Charger (On, Off, current limit)
- ⚡ Real-time updates via MQTT
- 🔒 Optional SSL and authentication support
- 🌐 Multi-phase system support
- All current supported entities are documented (here)[https://tomer-w.github.io/victron_mqtt/]

## Installation

### HACS Installation (Recommended)
1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS > Integrations
3. Click the "+" button and search for "Victron MQTT"
4. Click "Download"
5. Restart Home Assistant

### Manual Installation
1. Copy the `custom_components/victron-mqtt` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

### Script-Based Update (For Limited Bandwidth Environments)
If you prefer not to use HACS due to bandwidth constraints, especially in marine environments, you can use the provided update script to manually update the integration after it was installed for the first time.

1. Open the HA Terminal window.
2. For the first time only, you need to give the script execution permissions:
   ```bash
   chmod +x /config/custom_components/victron_mqtt/update_integration.sh
   ```
2. Run the script using a terminal:
   ```bash
   /config/custom_components/victron_mqtt/update_integration.sh
   ```
3. Optionally, use the `--restart` flag to restart Home Assistant after the update:
   ```bash
   /config/custom_components/victron_mqtt/update_integration.sh --restart
   ```
   This will validate the Home Assistant configuration and issue a restart command if the configuration is valid.

4. Restart Home Assistant manually if you did not use the `--restart` flag.

This script will fetch the latest version of the integration directly from the repository and replace the existing files.

## Configuration

The integration can be configured in two ways:

### Method 1: Automatic Discovery
1. Your Victron device should be automatically discovered if it has MQTT enabled
2. Go to Settings > Devices & Services
3. Look for the "Victron MQTT Integration" in the discovered section
4. Follow the configuration flow

### Method 2: Manual Configuration
1. Go to Settings > Devices & Services
2. Click "Add Integration"
3. Search for "Victron MQTT Integration"
4. Enter the following details:
   - Host: Your Victron device's hostname or IP (default: venus.local)
   - Port: MQTT port (default: 1883)
   - Username: (optional)
   - Password: (optional)
   - SSL: Enable/disable SSL connection

## Available entities (sensors, switches, lists, numbers)

The integration provides numerous entities depending on your Victron system configuration. Here are some key sensors:  
The full list is auto generated [here](https://tomer-w.github.io/victron_mqtt/)

### Battery Monitoring
- Battery Voltage
- Battery Current
- Battery Power
- Battery Level (State of Charge)
- Battery Temperature
- Battery Capacity
- Battery Energy (Charged/Discharged)

### Solar/PV Monitoring
- PV Voltage
- PV Current
- PV Power
- PV Yield
- PV Max Power Today

### Grid Monitoring
- Grid Voltage (per phase)
- Grid Current (per phase)
- Grid Power (per phase)
- Grid Consumption
- Grid Feed-in

### Inverter Monitoring
- Input/Output Power
- Input/Output Frequency
- Apparent Power

### System Monitoring
- AC Loads
- Critical Loads
- Grid Phases


## Adding entities
If you want to help the community and add more entities, please take a look at the [module](https://github.com/tomer-w/victron_mqtt) which drives this integration. It is very simple to extend this integration. I wrote a [document](https://github.com/tomer-w/victron_mqtt/blob/main/extending-victron-support.md) about it.


## Troubleshooting

### Common Issues

1. **Cannot Connect**
   - Verify your Victron device is powered on and connected to your network
   - Check that the hostname/IP is correct.
   - Ensure that MQTT is enabled on your Victron device.

2. **Authentication Failed**
   - Double-check username and password if authentication is enabled
   - Note: These are device credentials, not VRM portal credentials.

3. **No Sensors Appear**
   - Verify MQTT topics are being published by your Victron device
   - Check the Home Assistant logs for any error messages.

## Support

- For bugs and feature requests, open an issue on [GitHub](https://github.com/tomer-w/ha-victron-mqtt/issues)
- For questions and discussion, use the Home Assistant community forums

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to Johan du Plessis <johan@epicwin.co.za> who [submitted](https://github.com/home-assistant/core/pull/130505) the original code this custom integration is based on. Later he abandoned it and I revived it here.
- Thanks to Victron Energy for their excellent hardware and documentation
