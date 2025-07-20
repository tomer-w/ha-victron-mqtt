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

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
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
    DEFAULT_HOST,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_USERNAME): str,
        vol.Optional(CONF_PASSWORD): str,
        vol.Required(CONF_SSL): bool,
        vol.Optional(CONF_ROOT_TOPIC_PREFIX): str,
    }
)

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
        username=data.get(CONF_USERNAME),
        password=data.get(CONF_PASSWORD),
        use_ssl=data.get(CONF_SSL, False),
        installation_id=data.get(CONF_INSTALLATION_ID),
        serial=data.get(CONF_SERIAL, "noserial"),
        topic_prefix=data.get(CONF_ROOT_TOPIC_PREFIX),
    )

    await hub.connect()
    return hub.installation_id


class VictronMQTTConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for victronvenus."""

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
