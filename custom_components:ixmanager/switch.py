import logging
import requests
import voluptuous as vol
from datetime import timedelta

from homeassistant.components.switch import SwitchEntity, PLATFORM_SCHEMA
from homeassistant.const import CONF_API_KEY, CONF_NAME
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "iXmanager Charging Switch"
SCAN_INTERVAL = timedelta(minutes=1)  # Adjust as needed

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up iXmanager sensors from a config entry."""
    name = DEFAULT_NAME
    api_key = config_entry.data["api_key"]
    controller_id = config_entry.data["serial_number"]

    charging_switch = WallboxChargingSwitch(name, api_key, controller_id)
    single_phase_switch = WallboxSinglePhaseSwitch(f"{name} Single Phase", api_key, controller_id)

    async_add_entities([charging_switch, single_phase_switch], update_before_add=True)

class WallboxChargingSwitch(SwitchEntity):
    def __init__(self, name, api_key, controller_id):
        self._name = name
        self._state = False
        self._api_key = api_key
        self._controller_id = controller_id

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._controller_id}_charging_switch"

    def turn_on(self, **kwargs):
        self.set_charging(True)

    def turn_off(self, **kwargs):
        self.set_charging(False)

    def set_charging(self, enable):
        headers = {"X-API-KEY": self._api_key}
        url = f"https://evcharger.ixcommand.com/api/v1/thing/{self._controller_id}/properties"
        payload = {"chargingEnable": enable}
        
        response = requests.patch(url, json=payload, headers=headers)
        if response.status_code == 200:
            self._state = enable
        else:
            _LOGGER.error("Failed to set charging state on Wallbox API")

    def update(self):
        headers = {"X-API-KEY": self._api_key}
        url = f"https://evcharger.ixcommand.com/api/v1/thing/{self._controller_id}/properties?keys=chargingEnable"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self._state = data.get("chargingEnable")
        else:
            _LOGGER.error("Failed to fetch data from Wallbox API")

class WallboxSinglePhaseSwitch(SwitchEntity):
    """Representation of a Wallbox single phase switch."""

    def __init__(self, name, api_key, controller_id):
        """Initialize the switch."""
        self._name = name
        self._state = False
        self._api_key = api_key
        self._controller_id = controller_id

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._controller_id}_single_phase_switch"

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self.set_single_phase(True)

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self.set_single_phase(False)

    def set_single_phase(self, enable):
        """Set the single phase state on the Wallbox API."""
        headers = {"X-API-KEY": self._api_key}
        url = f"https://evcharger.ixcommand.com/api/v1/thing/{self._controller_id}/properties"
        payload = {"singlePhase": enable}
        
        response = requests.patch(url, json=payload, headers=headers)
        if response.status_code == 200:
            self._state = enable
        else:
            _LOGGER.error("Failed to set single phase state on Wallbox API")

    def update(self):
        """Fetch new state data for the switch."""
        headers = {"X-API-KEY": self._api_key}
        url = f"https://evcharger.ixcommand.com/api/v1/thing/{self._controller_id}/properties?keys=singlePhase"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self._state = data.get("singlePhase")
        else:
            _LOGGER.error("Failed to fetch data from Wallbox API")