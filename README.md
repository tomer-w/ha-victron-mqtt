# Victron Venus MQTT Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-green.svg)](https://github.com/custom-components/hacs)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)
[![Validate](https://github.com/tomer-w/ha-victron-mqtt/actions/workflows/validate.yaml/badge.svg)](https://github.com/tomer-w/ha-victron-mqtt/actions/workflows/validate.yaml)

A Home Assistant integration that connects to Victron Energy devices using MQTT, providing real-time monitoring of your Victron system including inverters, solar chargers, EV chargers, generators, and battery systems. Over 400 entities in total!!

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
- ⚡ Real-time updates via MQTT
- 🔒 Optional SSL and authentication support
- 🌐 Multi-phase system support
- All current supported entities are auto-documented [here](https://tomer-w.github.io/victron_mqtt/)

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
3. Run the script using a terminal to update to the latest release:
   ```bash
   /config/custom_components/victron_mqtt/update_integration.sh
   ```

#### Script Options

- **`--restart`**: Automatically restart Home Assistant after the update (validates configuration first)
  ```bash
  /config/custom_components/victron_mqtt/update_integration.sh --restart
  ```

- **`--main`**: Force download from the main development branch instead of the latest release
  ```bash
  /config/custom_components/victron_mqtt/update_integration.sh --main
  ```

- **`--version <tag>`**: Download a specific version (e.g., `v1.0.0`)
  ```bash
  /config/custom_components/victron_mqtt/update_integration.sh --version v1.0.0
  /config/custom_components/victron_mqtt/update_integration.sh --version v1.0.0 --restart
  ```

- **`--list-versions`**: List all available versions
  ```bash
  /config/custom_components/victron_mqtt/update_integration.sh --list-versions
  ```

This script will fetch the specified version of the integration directly from the repository and replace the existing files.

Note: Restart Home Assistant manually if you did not use the `--restart` flag.


## Configuration

The integration can be configured in three ways:

### Method 1: Automatic Discovery (Recommended)

Your Victron GX device is automatically discovered on the local network. Go to **Settings > Devices & Services** and look for the integration in the "Discovered" section, then confirm to set it up.

> **TL;DR:** On Venus OS v3.80 or newer, just follow the discovery flow — no preparation needed. On older versions, enable MQTT access on the GX device first (*Settings > Integrations > MQTT Access*) — otherwise the device will not be discovered.

#### Details per security profile and Venus OS version

The configuration flow depends on the configured **Local Network Security Profile** of your GX device (under *Settings > General > Access & Security > Local Network Security Profile*) and the Venus OS version:

| Security Profile | Venus OS v3.80 or newer | Venus OS older than v3.80 |
|---|---|---|
| **Unsecured** | If MQTT access was not turned on manually, uses **MQTT pairing mode** (see below) and connects via SSL on port 8883 (recommended). If MQTT is already on, connects automatically without credentials on port 1883. | MQTT must be enabled manually on the GX device beforehand (*Settings > Integrations > MQTT Access*). Connects automatically without credentials on port 1883. |
| **Weak** | Asks you to activate **MQTT pairing mode** on the GX device before pressing Submit (see below). No need to manually enable MQTT — token pairing takes care of it automatically. Connects via SSL on port 8883. | MQTT must be enabled manually on the GX device beforehand (*Settings > Integrations > MQTT Access*). Asks for the **GX Password**¹. Connects via SSL on port 8883. |
| **Secured** | Same as above. | Same as above. |

¹ The GX Password is printed on the sticker on the GX device, or it is what was set when configuring the Local Network Security Profile (*Settings > General > Access & Security*).

**Activating MQTT pairing mode (v3.80+ only):** Via the GX user interface under *Settings > Integrations > MQTT Devices > Pairing mode*, or by quickly double-pressing the built-in button on GX devices without a screen. Pairing mode stays active for 120 seconds.

### Method 2: Manual Configuration (Direct Connection)
1. Go to **Settings > Devices & Services**
2. Click **Add Integration** and search for "Victron MQTT Integration"
3. Enter the connection details (host, port, credentials, SSL, etc.)

The recommended settings use SSL on port 8883, `remoteconsole` as username and the *GX Password* as password. If your security profile is "Unsecured", use port 1883 with SSL disabled and leave credentials blank.

### Method 3: Using Home Assistant MQTT Broker (Bridged Configuration)
Some users prefer to reduce the direct load on their Victron server and use bridge from the Venus device to a local mosquitto server running as add-on on the HAOS.

#### Prerequisites
1. Install the [Mosquitto broker add-on](https://github.com/home-assistant/addons/tree/master/mosquitto) from the Home Assistant Add-on Store
2. Configure a user and password for the MQTT broker in the add-on configuration

#### Configuration Steps
1. **Configure the Mosquitto Bridge**: Edit the Mosquitto configuration file at `/share/mosquitto/mosquitto.conf` (accessible via File Editor add-on or SSH) and add:
   ```
   connection victron
   address <YOUR_VENUS_IP>:1883
   topic N/# in 0
   # TO CHANGE settings via MQTT, one has to write to the "W/" topic!!
   topic W/# out 0
   topic R/# out 0
   start_type automatic
   allow_anonymous true
   ```
   Replace `<YOUR_VENUS_IP>` with your Victron device's IP address.

2. **Restart the Mosquitto Add-on** to apply the bridge configuration

3. **Configure the Integration**: When setting up the Victron MQTT Integration:
   - Host: `core-mosquitto` (the internal hostname for the HA MQTT broker)
   - Port: `1883`
   - Username: Your MQTT broker username
   - Password: Your MQTT broker password
   - SSL: Disable (internal connection doesn't require SSL)

#### Benefits of Bridged Configuration
- Reduces load on the Venus MQTT server
- Provides a single MQTT broker for all your Home Assistant MQTT devices
- Allows for better network traffic management

## Adding entities
If you want to help the community and add more entities, please take a look at the [module](https://github.com/tomer-w/victron_mqtt) which drives this integration. It is very simple to extend this integration. I wrote a [document](https://github.com/tomer-w/victron_mqtt/blob/main/CONTRIBUTING.md) about it.

## Troubleshooting

### Common Issues

1. **Cannot Connect**
   - Verify your Victron device is powered on and connected to your network
   - Check that the hostname/IP is correct.
   - Ensure that MQTT is enabled on your Victron device.
   - On your HA device, open Terminal window using one of the addons and run the following command:
   ```
   nc -zv <Cerbo IP address> <Cerbo mqtt port, usually 8883>
   ```
   if you are getting timeout or other errors there is real connectivity issue and it is not integration issue.
   - in case venus OS is rooted (i.e. with ssh access enabled):
     - use port 8883
     - enable SSL/TLS
     - use user root
     - use password that you have defined to protect the instance
   - **Alternative**: Consider using the bridged configuration (Method 3) if you're experiencing frequent connectivity issues or want to reduce load on your Venus device.

2. **Authentication Failed**
   - Double-check the username and password if authentication is enabled.
   - Note: These are device credentials, not VRM portal credentials.

3. **No Sensors Appear**
   - Verify that MQTT topics are being published by your Victron device.
   - Check the Home Assistant logs for any error messages.

## Support

- For bugs and feature requests, open an issue on [GitHub](https://github.com/tomer-w/ha-victron-mqtt/issues)
- For questions and discussion, use the Home Assistant community forums

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to Johan du Plessis <johan@epicwin.co.za>, who [submitted](https://github.com/home-assistant/core/pull/130505) the original code this custom integration is based on. He later abandoned it, and I revived it here.
- Thanks to Victron Energy for their excellent hardware and documentation.
