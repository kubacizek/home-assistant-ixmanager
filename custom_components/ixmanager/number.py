import logging
import requests
import voluptuous as vol
from datetime import timedelta

from homeassistant.components.number import NumberEntity, PLATFORM_SCHEMA
from homeassistant.const import CONF_API_KEY, CONF_NAME
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "iXmanager Charging Current"
DEFAULT_MIN_VALUE = 6
DEFAULT_MAX_VALUE = 16
DEFAULT_STEP = 1
DEFAULT_SCAN_INTERVAL = timedelta(minutes=1)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up iXmanager sensors from a config entry."""
    api_key = config_entry.data["api_key"]
    controller_id = config_entry.data["serial_number"]

    sensors = [WallboxChargingCurrent(DEFAULT_NAME, api_key, controller_id)]
    async_add_entities(sensors, update_before_add=True)

class WallboxChargingCurrent(NumberEntity):
    """Representation of a Wallbox charging current."""

    def __init__(self, name, api_key, controller_id):
        """Initialize the number entity."""
        self._name = name
        self._state = None
        self._api_key = api_key
        self._controller_id = controller_id
        self._min_value = DEFAULT_MIN_VALUE
        self._max_value = DEFAULT_MAX_VALUE
        self._step = DEFAULT_STEP

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def value(self):
        """Return the current value."""
        return self._state

    @property
    def min_value(self):
        """Return the minimum value."""
        return self._min_value

    @property
    def max_value(self):
        """Return the maximum value."""
        return self._max_value

    @property
    def step(self):
        """Return the step value."""
        return self._step

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._controller_id}_charging_current"

    def set_value(self, value):
        """Set the charging current value."""
        headers = {"X-API-KEY": self._api_key}
        url = f"https://evcharger.ixcommand.com/api/v1/thing/{self._controller_id}/properties"
        payload = {"targetCurrent": value}
        
        response = requests.patch(url, json=payload, headers=headers)
        if response.status_code == 200:
            self._state = value
        else:
            _LOGGER.error("Failed to set charging current on Wallbox API")

    def update(self):
        """Fetch new state data for the number entity."""
        headers = {"X-API-KEY": self._api_key}
        url = f"https://evcharger.ixcommand.com/api/v1/thing/{self._controller_id}/properties?keys=targetCurrent"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self._state = data.get("targetCurrent")
        else:
            _LOGGER.error("Failed to fetch data from Wallbox API")
