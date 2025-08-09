"""Sensor platform for iXmanager integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IXManagerConfigEntry
from .const import (
    CONF_SERIAL_NUMBER,
    DOMAIN,
    PROPERTY_CHARGING_ENABLE,
    PROPERTY_CHARGING_STATUS,
    PROPERTY_CURRENT_CHARGING_POWER,
    PROPERTY_MAXIMUM_CURRENT,
    PROPERTY_SIGNAL,
    PROPERTY_SINGLE_PHASE,
    PROPERTY_TOTAL_ENERGY,
)
from .coordinator import IXManagerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IXManagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up iXmanager sensor entities.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator = entry.runtime_data

    entities: list[IXManagerSensorBase] = [
        IXManagerChargingEnableSensor(coordinator, entry),
        IXManagerMaximumCurrentSensor(coordinator, entry),
        IXManagerCurrentChargingPowerSensor(coordinator, entry),
        IXManagerTotalEnergySensor(coordinator, entry),
        IXManagerSinglePhaseSensor(coordinator, entry),
        IXManagerSignalStrengthSensor(coordinator, entry),
        IXManagerChargingStatusSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class IXManagerSensorBase(CoordinatorEntity[IXManagerDataUpdateCoordinator], SensorEntity):
    """Base class for iXmanager sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IXManagerDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor.
        
        Args:
            coordinator: Data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator)
        self._serial_number = entry.data[CONF_SERIAL_NUMBER]
        self._attr_unique_id = f"{self._serial_number}_{self._property_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
            name=f"iXmanager {self._serial_number}",
            manufacturer="R-EVC",
            model="Wallbox EcoVolter",
            serial_number=self._serial_number,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available.
        
        Returns:
            True if coordinator has data and is available
        """
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._property_key in self.coordinator.data
            and self.coordinator.data[self._property_key] is not None
        )

    @property
    def _property_key(self) -> str:
        """Return the property key for this sensor.
        
        Returns:
            Property key string
        """
        raise NotImplementedError

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor.
        
        Returns:
            Sensor value or None if not available
        """
        if not self.available:
            return None
            
        property_data = self.coordinator.data.get(self._property_key)
        if property_data is not None:
            # Handle both dict format {'value': X} and direct value format
            if isinstance(property_data, dict) and "value" in property_data:
                return property_data["value"]
            else:
                return property_data
        return None


class IXManagerChargingEnableSensor(IXManagerSensorBase):
    """Sensor for charging enable status."""

    _attr_name = "Charging Enable"
    _attr_icon = "mdi:ev-station"

    @property
    def _property_key(self) -> str:
        """Return the property key for this sensor."""
        return PROPERTY_CHARGING_ENABLE

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        value = super().native_value
        if value is not None:
            # Handle boolean values directly
            if isinstance(value, bool):
                return "enabled" if value else "disabled"
            return "enabled" if str(value).lower() == "true" else "disabled"
        return None


class IXManagerMaximumCurrentSensor(IXManagerSensorBase):
    """Sensor for maximum current setting."""

    _attr_name = "Maximum Current"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:current-ac"

    @property
    def _property_key(self) -> str:
        """Return the property key for this sensor."""
        return PROPERTY_MAXIMUM_CURRENT

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        value = super().native_value
        if value is not None:
            try:
                return int(value)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid maximum current value: %s", value)
        return None


class IXManagerCurrentChargingPowerSensor(IXManagerSensorBase):
    """Sensor for current charging power."""

    _attr_name = "Current Charging Power"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:lightning-bolt"

    @property
    def _property_key(self) -> str:
        """Return the property key for this sensor."""
        return PROPERTY_CURRENT_CHARGING_POWER

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        value = super().native_value
        if value is not None:
            try:
                return int(value)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid charging power value: %s", value)
        return None


class IXManagerTotalEnergySensor(IXManagerSensorBase):
    """Sensor for total energy consumption."""

    _attr_name = "Total Energy"
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    @property
    def _property_key(self) -> str:
        """Return the property key for this sensor."""
        return PROPERTY_TOTAL_ENERGY

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        value = super().native_value
        if value is not None:
            try:
                return int(value)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid total energy value: %s", value)
        return None


class IXManagerSinglePhaseSensor(IXManagerSensorBase):
    """Sensor for single phase mode status."""

    _attr_name = "Single Phase Mode"
    _attr_icon = "mdi:sine-wave"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def _property_key(self) -> str:
        """Return the property key for this sensor."""
        return PROPERTY_SINGLE_PHASE

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        value = super().native_value
        if value is not None:
            # Handle boolean values directly
            if isinstance(value, bool):
                return "enabled" if value else "disabled"
            return "enabled" if str(value).lower() == "true" else "disabled"
        return None


class IXManagerSignalStrengthSensor(IXManagerSensorBase):
    """Sensor for WiFi signal strength percentage."""

    _attr_name = "WiFi Signal Strength"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:wifi"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def _property_key(self) -> str:
        """Return the property key for this sensor."""
        return PROPERTY_SIGNAL

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        value = super().native_value
        if value is not None:
            try:
                # Ensure the value is between 0 and 100
                signal_value = int(value)
                return max(0, min(100, signal_value))
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid signal strength value: %s", value)
        return None


class IXManagerChargingStatusSensor(IXManagerSensorBase):
    """Sensor for vehicle charging status following SAE J1772."""

    _attr_name = "Charging Status"
    _attr_icon = "mdi:ev-station"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def _property_key(self) -> str:
        """Return the property key for this sensor."""
        return PROPERTY_CHARGING_STATUS

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        value = super().native_value
        if value is not None:
            # Return the charging status directly as it's already a string
            return str(value)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        value = self.native_value
        if value is None:
            return None
            
        # Map charging status to descriptions
        status_descriptions = {
            "INIT": "Initialization state",
            "IDLE": "SAE J1772 Status A - No vehicle connected",
            "CONNECTED": "SAE J1772 Status B - Vehicle connected, not ready",
            "CHARGING": "SAE J1772 Status C - Vehicle charging",
            "CHARGING_WITH_VENTILATION": "SAE J1772 Status D - Vehicle charging with ventilation",
            "CONTROL_PILOT_ERROR": "SAE J1772 Status E - Control pilot error",
            "ERROR": "SAE J1772 Status F - Error state"
        }
        
        return {
            "description": status_descriptions.get(value, f"Unknown status: {value}"),
            "sae_j1772_standard": "https://en.wikipedia.org/wiki/SAE_J1772"
        }