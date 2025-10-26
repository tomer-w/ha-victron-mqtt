"""Config flow for victronvenus integration."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from victron_mqtt import (
    CannotConnectError,
    Hub as VictronVenusHub,
    DeviceType,
    OperationMode
)
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode
from .const import (
    CONF_INSTALLATION_ID,
    CONF_MODEL,
    CONF_SERIAL,
    CONF_ROOT_TOPIC_PREFIX,
    CONF_UPDATE_FREQUENCY_SECONDS,
    CONF_EXCLUDED_DEVICES,
    CONF_SIMPLE_NAMING,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_UPDATE_FREQUENCY_SECONDS,
    DOMAIN,
    CONF_OPERATION_MODE,
    CONF_ELEVATED_TRACING,
)

_LOGGER = logging.getLogger(__name__)

DEVICE_CODES = [
    {"value": device_type.code, "label": device_type.string}
    for device_type in DeviceType
    if device_type.string != "<Not used>"
]

def _get_user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Get the user data schema with optional defaults."""
    if defaults is None:
        defaults = {}
    # Ensure operation_mode default is a string value (not an Enum instance)
    op_default = defaults.get(CONF_OPERATION_MODE, OperationMode.FULL.value)
    if isinstance(op_default, OperationMode):
        op_default = op_default.value
    
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, DEFAULT_HOST)): str,
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): int,
            vol.Optional(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): str,
            vol.Optional(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")): str,
            vol.Required(CONF_SSL, default=defaults.get(CONF_SSL, False)): bool,
            vol.Required(CONF_OPERATION_MODE, default=op_default): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": OperationMode.READ_ONLY.value, "label": "Read-only (sensors & binary sensors only)"},
                        {"value": OperationMode.FULL.value, "label": "Full (sensors + controllable entities)"},
                        {"value": OperationMode.EXPERIMENTAL.value, "label": "Experimental (may be unstable)"},
                    ]
                )
            ),
            vol.Optional(CONF_SIMPLE_NAMING, default=defaults.get(CONF_SIMPLE_NAMING, False)): bool,
            vol.Optional(CONF_ROOT_TOPIC_PREFIX, default=defaults.get(CONF_ROOT_TOPIC_PREFIX, "")): str,
            vol.Optional(CONF_UPDATE_FREQUENCY_SECONDS, default=defaults.get(CONF_UPDATE_FREQUENCY_SECONDS, DEFAULT_UPDATE_FREQUENCY_SECONDS)): int,
            vol.Optional(CONF_EXCLUDED_DEVICES, default=defaults.get(CONF_EXCLUDED_DEVICES, [])): SelectSelector(
                SelectSelectorConfig(
                    options=DEVICE_CODES,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_ELEVATED_TRACING, default=defaults.get(CONF_ELEVATED_TRACING, "")): str,
        }
    )


STEP_USER_DATA_SCHEMA = _get_user_schema()


async def validate_input(data: dict[str, Any]) -> str:
    """Validate the user input allows us to connect.

    Data has the keys from zeroconf values as well as user input.

    Returns the installation id upon success.
    """
    _LOGGER.info("Validating input: %s", data)
    host = data.get(CONF_HOST)
    assert host is not None
    hub = VictronVenusHub(
        host=host,
        port=data.get(CONF_PORT, DEFAULT_PORT),
        username=data.get(CONF_USERNAME) or None,
        password=data.get(CONF_PASSWORD) or None,
        use_ssl=data.get(CONF_SSL, False),
        installation_id=data.get(CONF_INSTALLATION_ID) or None,
        serial=data.get(CONF_SERIAL, "noserial"),
        topic_prefix=data.get(CONF_ROOT_TOPIC_PREFIX) or None,
        topic_log_info = data.get(CONF_ELEVATED_TRACING) or None,
    )

    await hub.connect()
    assert hub.installation_id is not None
    return hub.installation_id

class VictronMQTTConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for victronvenus."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self.hostname: str | None = None
        self.serial: str | None = None
        self.installation_id: str | None = None
        self.friendlyName: str | None = None
        self.modelName: str | None = None


    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            _LOGGER.info("User input received: %s", user_input)
            data = {**user_input, CONF_SERIAL: self.serial, CONF_MODEL: self.modelName}
            data = {
                k: v for k, v in data.items() if v is not None
            }  # remove None values.

            try:
                installation_id = await validate_input(data)
                _LOGGER.info("Successfully connected to Victron device: %s", installation_id)
            except CannotConnectError as e:
                _LOGGER.error("Cannot connect to Victron device: %s", e, exc_info=True)
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.error("General error connecting to Victron device: %s", e, exc_info=True)
                errors["base"] = "unknown"
            else:
                data[CONF_INSTALLATION_ID] = installation_id
                unique_id = installation_id
                await self.async_set_unique_id(unique_id)

                self._abort_if_unique_id_configured()

                if self.friendlyName:
                    title = self.friendlyName
                else:
                    title = f"Victron OS {unique_id}"
                return self.async_create_entry(title=title, data=data)
        
        if len(errors) > 0:
            _LOGGER.warning("showing form with errors: %s", errors)
        else:
            _LOGGER.info("showing form without errors")
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry) -> OptionsFlow:
        """Get the options flow for this handler."""
        _LOGGER.info("Getting options flow handler")
        return VictronMQTTOptionsFlow()

    async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle UPnP  discovery."""
        self.hostname = str(urlparse(discovery_info.ssdp_location).hostname)
        self.serial = discovery_info.upnp["serialNumber"]
        self.installation_id = discovery_info.upnp["X_VrmPortalId"]
        self.modelName = discovery_info.upnp["modelName"]
        self.friendlyName = discovery_info.upnp["friendlyName"]
        
        _LOGGER.info("SSDP: hostname=%s, serial=%s, installation_id=%s, modelName=%s, friendlyName=%s", self.hostname, self.serial, self.installation_id, self.modelName, self.friendlyName)

        await self.async_set_unique_id(self.installation_id)
        self._abort_if_unique_id_configured()

        try:
            sensed_installation_id = await validate_input({CONF_HOST: self.hostname, CONF_SERIAL: self.serial, CONF_INSTALLATION_ID: self.installation_id})
            assert sensed_installation_id == self.installation_id
        except CannotConnectError:
            return await self.async_step_user()

        return self.async_create_entry(
            title=str(self.friendlyName),
            data={
                CONF_HOST: self.hostname,
                CONF_SERIAL: self.serial,
                CONF_INSTALLATION_ID: self.installation_id,
                CONF_MODEL: self.modelName,
            },
        )


class VictronMQTTOptionsFlow(OptionsFlow):
    """Handle options flow for Victron MQTT."""
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle options flow."""
        _LOGGER.info("Initializing options flow. current config: %s", self.config_entry.data)
        if user_input is not None:
            _LOGGER.info("User input received: %s", user_input)
            # Validate the input by combining current config data with user input
            data = dict(self.config_entry.data)
            data.update(user_input)
            try:
                await validate_input(data)
            except CannotConnectError:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._get_options_schema(),
                    errors={"base": "cannot_connect"},
                )
            except Exception:
                return self.async_show_form(
                    step_id="init", 
                    data_schema=self._get_options_schema(),
                    errors={"base": "unknown"},
                )
            _LOGGER.info("Options flow completed successfully. new config: %s", data)
            # Update the config entry with new data.
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)
            # Reload the entry to apply the new options
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data=None)
        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    def _get_options_schema(self) -> vol.Schema:
        """Get the options schema with current values as defaults."""
        return _get_user_schema(self.config_entry.data)
