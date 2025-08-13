"""Config flow for victronvenus integration."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from victron_mqtt import (
    CannotConnectError,
    Hub as VictronVenusHub,
)
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow, ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

from .const import (
    CONF_INSTALLATION_ID,
    CONF_MODEL,
    CONF_SERIAL,
    CONF_ROOT_TOPIC_PREFIX,
    CONF_UPDATE_FREQUENCY_SECONDS,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_UPDATE_FREQUENCY_SECONDS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _get_user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Get the user data schema with optional defaults."""
    if defaults is None:
        defaults = {}
    
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, DEFAULT_HOST)): str,
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): int,
            vol.Optional(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): str,
            vol.Optional(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")): str,
            vol.Required(CONF_SSL, default=defaults.get(CONF_SSL, False)): bool,
            vol.Optional(CONF_ROOT_TOPIC_PREFIX, default=defaults.get(CONF_ROOT_TOPIC_PREFIX, "")): str,
            vol.Optional(CONF_UPDATE_FREQUENCY_SECONDS, default=defaults.get(CONF_UPDATE_FREQUENCY_SECONDS, DEFAULT_UPDATE_FREQUENCY_SECONDS)): int,
        }
    )


STEP_USER_DATA_SCHEMA = _get_user_schema()

STEP_REAUTH_DATA_SCHEMA = vol.Schema(
    {vol.Optional(CONF_USERNAME): str, vol.Optional(CONF_PASSWORD): str}
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> str:
    """Validate the user input allows us to connect.

    Data has the keys from zeroconf values as well as user input.

    Returns the installation id upon success.
    """
    _LOGGER.info("Validating input: %s", data)
    hub = VictronVenusHub(
        host=data.get(CONF_HOST),
        port=data.get(CONF_PORT, DEFAULT_PORT),
        username=data.get(CONF_USERNAME) or None,
        password=data.get(CONF_PASSWORD) or None,
        use_ssl=data.get(CONF_SSL, False),
        installation_id=data.get(CONF_INSTALLATION_ID) or None,
        serial=data.get(CONF_SERIAL, "noserial"),
        topic_prefix=data.get(CONF_ROOT_TOPIC_PREFIX) or None,
        logger_level=logging.DEBUG,  # Set to DEBUG for detailed logs
    )

    await hub.connect()
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

    @staticmethod
    def async_get_options_flow(config_entry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return VictronMQTTOptionsFlow(config_entry)

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
                installation_id = await validate_input(self.hass, data)
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
            await validate_input(
                self.hass, {CONF_HOST: self.hostname, CONF_SERIAL: self.serial}
            )
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

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle options flow."""
        if user_input is not None:
            # Validate the input by combining current config data with user input
            data = dict(self.config_entry.data)
            data.update(user_input)
            try:
                await validate_input(self.hass, data)
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
            # Save options only, do not update config entry data or reload
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    def _get_options_schema(self) -> vol.Schema:
        """Get the options schema with current values as defaults."""
        return _get_user_schema(self.config_entry.data)
