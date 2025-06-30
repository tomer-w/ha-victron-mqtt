from homeassistant.helpers.device_registry import DeviceInfo

from victron_mqtt import Device as VictronVenusDevice

from .const import DOMAIN


def _map_device_info(device: VictronVenusDevice) -> DeviceInfo:
    info: DeviceInfo = {}
    info["identifiers"] = {(DOMAIN, device.unique_id)}
    info["manufacturer"] = device.manufacturer if device.manufacturer is not None else "Victron Energy"
    info["name"] = f"{device.name} (ID: {device.device_id})" if device.device_id != "0" else device.name
    info["model"] = device.model
    info["serial_number"] = device.serial_number

    return info
