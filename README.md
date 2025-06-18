# Victron Venus MQTT Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)
<!-- [![Validate](https://github.com/tomer-w/ha-victron-mqtt/actions/workflows/validate.yaml/badge.svg)](https://github.com/tomer-w/ha-victron-mqtt/actions/workflows/validate.yaml) -->

A Home Assistant integration that connects to Victron Energy devices using MQTT, providing real-time monitoring of your Victron system including inverters, solar chargers, and battery systems.

## Features

- 🔌 Auto-discovery of Victron devices via SSDP ([Cerbo GX](https://www.victronenergy.com/communication-centres/cerbo-gx), etc)
- 📊 Comprehensive sensor data including:
  - Battery metrics (voltage, current, power, temperature, state of charge)
  - Solar/PV metrics (voltage, current, power, yield)
  - Grid metrics (voltage, current, power, energy)
  - Inverter metrics (input/output power, frequency)
  - System load monitoring
- ⚡ Real-time updates via MQTT
- 🔒 Optional SSL and authentication support
- 🌐 Multi-phase system support

## Installation

### HACS Installation (Recommended)
1. Make sure you have [HACS](https://hacs.xyz/) installed
2. In HACS, click on the 3 dots in the top right corner and select "Custom repositories"
3. Add `https://github.com/tomer-w/ha-victron-mqtt` as a custom repository with the category "Integration"
4. Click "Add"
5. Go to HACS > Integrations
6. Click the "+" button and search for "Victron MQTT"
7. Click "Download"
8. Restart Home Assistant

### Manual Installation
1. Copy the `custom_components/victron-mqtt` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

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

## Available Sensors

The integration provides numerous sensors depending on your Victron system configuration. Here are some key sensors:

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

## Troubleshooting

### Common Issues

1. **Cannot Connect**
   - Verify your Victron device is powered on and connected to your network
   - Check if the hostname/IP is correct
   - Ensure MQTT is enabled on your Victron device

2. **Authentication Failed**
   - Double-check username and password if authentication is enabled
   - Note: These are device credentials, not VRM portal credentials

3. **No Sensors Appear**
   - Verify MQTT topics are being published by your Victron device
   - Check Home Assistant logs for any error messages

## Support

- For bugs and feature requests, open an issue on [GitHub](https://github.com/tomer-w/ha-victron-mqtt/issues)
- For questions and discussion, use the Home Assistant community forums

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to Johan du Plessis <johan@epicwin.co.za> who [submitted](https://github.com/home-assistant/core/pull/130505) the original code this custom integration is based on. Later he abandoned it and I revived it here.
- Thanks to Victron Energy for their excellent hardware and documentation
