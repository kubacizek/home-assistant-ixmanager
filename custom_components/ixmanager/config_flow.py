# config_flow.py
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
import voluptuous as vol

from .const import DOMAIN

class IXManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iXmanager."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            if self._validate_input(user_input):
                return self.async_create_entry(title="iXmanager", data=user_input)
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user", data_schema=self._build_schema(), errors=errors
        )

    @staticmethod
    @callback
    def _validate_input(data):
        """Validate the user input."""
        # Add logic to validate API key or other data here
        return True

    @staticmethod
    @callback
    def _build_schema():
        """Return the data schema for the user step."""
        return vol.Schema({
            vol.Required("api_key"): str,
            vol.Required("serial_number"): str,
        })
