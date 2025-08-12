"""Config flow for iXmanager integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api_client import IXManagerApiClient
from .const import CABLE_TYPES
from .const import CONF_API_KEY
from .const import CONF_CABLE_TYPE
from .const import CONF_SERIAL_NUMBER
from .const import DEFAULT_CABLE_TYPE
from .const import DEFAULT_NAME
from .const import DOMAIN
from .exceptions import IXManagerAuthenticationError
from .exceptions import IXManagerConnectionError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_SERIAL_NUMBER): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_CABLE_TYPE, default=DEFAULT_CABLE_TYPE): vol.In(CABLE_TYPES),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Args:
        hass: Home Assistant instance
        data: User input data

    Returns:
        Dictionary with connection info

    Raises:
        IXManagerConnectionError: If we cannot connect
        IXManagerAuthenticationError: If credentials are invalid
    """
    api_client = IXManagerApiClient(hass, data[CONF_API_KEY], data[CONF_SERIAL_NUMBER])

    # Test the connection
    await api_client.async_validate_connection()

    # Return info that you want to store in the config entry
    cable_info = CABLE_TYPES[data[CONF_CABLE_TYPE]]
    return {
        "title": f"{data[CONF_NAME]} ({data[CONF_SERIAL_NUMBER]}) - {cable_info['name']}",
        "serial_number": data[CONF_SERIAL_NUMBER],
        "cable_type": data[CONF_CABLE_TYPE],
    }


class IXManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iXmanager."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step.

        Args:
            user_input: User provided configuration

        Returns:
            Flow result
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Set unique ID based on serial number
            await self.async_set_unique_id(user_input[CONF_SERIAL_NUMBER])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except IXManagerConnectionError:
                errors["base"] = "cannot_connect"
            except IXManagerAuthenticationError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauth flow.

        Args:
            entry_data: Existing entry data

        Returns:
            Flow result
        """
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauth confirm step.

        Args:
            user_input: User provided configuration

        Returns:
            Flow result
        """
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            # Use existing serial number and cable type, only update API key
            test_data = {
                CONF_API_KEY: user_input[CONF_API_KEY],
                CONF_SERIAL_NUMBER: reauth_entry.data[CONF_SERIAL_NUMBER],
                CONF_NAME: reauth_entry.data.get(CONF_NAME, DEFAULT_NAME),
                CONF_CABLE_TYPE: reauth_entry.data.get(
                    CONF_CABLE_TYPE, DEFAULT_CABLE_TYPE
                ),
            }

            try:
                await validate_input(self.hass, test_data)
            except IXManagerConnectionError:
                errors["base"] = "cannot_connect"
            except IXManagerAuthenticationError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data={**reauth_entry.data, **user_input},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow.

        Args:
            config_entry: Config entry to create options for

        Returns:
            Options flow instance
        """
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for iXmanager integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow.

        Args:
            config_entry: Config entry for this options flow
        """
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial options step.

        Args:
            user_input: User provided options

        Returns:
            Flow result
        """
        if user_input is not None:
            # Update the config entry with new cable type
            new_data = dict(self.config_entry.data)
            new_data[CONF_CABLE_TYPE] = user_input[CONF_CABLE_TYPE]

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )

            return self.async_create_entry(title="", data={})

        current_cable_type = self.config_entry.data.get(
            CONF_CABLE_TYPE, DEFAULT_CABLE_TYPE
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CABLE_TYPE, default=current_cable_type): vol.In(
                        CABLE_TYPES
                    ),
                }
            ),
        )
