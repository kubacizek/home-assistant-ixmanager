import logging
import requests
from datetime import timedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.const import POWER_WATT, ENERGY_KILO_WATT_HOUR

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "iXmanager"
SCAN_INTERVAL = timedelta(minutes=1)  # Adjust as needed

async def async_setup_entry(hass, config_entry, async_add_entities):
    api_key = config_entry.data["api_key"]
    controller_id = config_entry.data["serial_number"]

    # Initialize the coordinator
    coordinator = WallboxDataUpdateCoordinator(api_key, controller_id)

    # Create sensors for each attribute
    sensors = [
        WallboxChargingEnableSensor(coordinator),
        WallboxMaximumCurrentSensor(coordinator),
        WallboxCurrentChargingPowerSensor(coordinator),
        WallboxTotalEnergySensor(coordinator),
    ]
    async_add_entities(sensors, update_before_add=True)

class WallboxDataUpdateCoordinator:
    def __init__(self, api_key, controller_id):
        self._api_key = api_key
        self._controller_id = controller_id
        self.data = {}

    def update(self):
        headers = {"X-API-KEY": self._api_key}
        url = f"https://evcharger.ixcommand.com/api/v1/thing/{self._controller_id}/properties?keys=chargingEnable&keys=maximumCurrent&keys=currentChargingPower&keys=totalEnergy"

        _LOGGER.debug(url)
        response = requests.get(url, headers=headers)
        _LOGGER.debug(response.status_code)

        if response.status_code == 200:
            self.data = response.json()
        else:
            _LOGGER.error("Failed to update data from Wallbox API")

class WallboxSensorBase(Entity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._state = None

    @property
    def state(self):
        return self._state

    @property
    def should_poll(self):
        return True

    def update(self):
        self.coordinator.update()
        self._update_state()

    def _update_state(self):
        raise NotImplementedError

class WallboxChargingEnableSensor(WallboxSensorBase):
    @property
    def name(self):
        return "Charging Enable"

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return f"{self.coordinator._controller_id}_charging_enable"

    def _update_state(self):
        self._state = self.coordinator.data.get("chargingEnable")

class WallboxMaximumCurrentSensor(WallboxSensorBase):
    @property
    def name(self):
        return "Maximum Current"

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return f"{self.coordinator._controller_id}_maximum_current"

    def _update_state(self):
        self._state = self.coordinator.data.get("maximumCurrent")

class WallboxCurrentChargingPowerSensor(WallboxSensorBase):
    @property
    def name(self):
        return "Current Charging Power"

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return f"{self.coordinator._controller_id}_current_charging_power"

    @property
    def unit_of_measurement(self):
        return POWER_WATT  

    @property
    def device_class(self):
        return "power"

    def _update_state(self):
        self._state = self.coordinator.data.get("currentChargingPower")

class WallboxTotalEnergySensor(WallboxSensorBase):
    @property
    def name(self):
        return "Total Energy"

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return f"{self.coordinator._controller_id}_total_energy"

    @property
    def unit_of_measurement(self):
        return ENERGY_KILO_WATT_HOUR  

    @property
    def device_class(self):
        return "energy"

    def _update_state(self):
        self._state = self.coordinator.data.get("totalEnergy")
