"""Number platform for iXmanager integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IXManagerConfigEntry
from .const import (
    CABLE_TYPES,
    CONF_CABLE_TYPE,
    CONF_SERIAL_NUMBER,
    DEFAULT_CABLE_TYPE,
    DOMAIN,
    PROPERTY_MAXIMUM_CURRENT,
)
from .coordinator import IXManagerDataUpdateCoordinator
from .exceptions import IXManagerError

_LOGGER = logging.getLogger(__name__)

# Constants for charging current limits
MIN_CHARGING_CURRENT = 6
MAX_CHARGING_CURRENT = 32
CHARGING_CURRENT_STEP = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IXManagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up iXmanager number entities.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator = entry.runtime_data

    entities: list[IXManagerNumberBase] = [
        IXManagerChargingCurrentNumber(coordinator, entry),
    ]

    async_add_entities(entities)


class IXManagerNumberBase(CoordinatorEntity[IXManagerDataUpdateCoordinator], NumberEntity):
    """Base class for iXmanager number entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IXManagerDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity.
        
        Args:
            coordinator: Data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator)
        self._serial_number = entry.data[CONF_SERIAL_NUMBER]
        self._cable_type = entry.data.get(CONF_CABLE_TYPE, DEFAULT_CABLE_TYPE)
        self._attr_unique_id = f"{self._serial_number}_{self._number_key}"
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
    def _number_key(self) -> str:
        """Return the number key for unique ID.
        
        Returns:
            Number key string
        """
        raise NotImplementedError

    @property
    def _property_key(self) -> str:
        """Return the property key for this number entity.
        
        Returns:
            Property key string
        """
        raise NotImplementedError

    @property
    def native_value(self) -> float | None:
        """Return the current value.
        
        Returns:
            Current value or None if not available
        """
        if not self.available:
            return None
            
        property_data = self.coordinator.data.get(self._property_key)
        if property_data is not None:
            # Handle both dict format {'value': X} and direct value format
            if isinstance(property_data, dict) and "value" in property_data:
                value = property_data["value"]
            else:
                value = property_data
                
            try:
                return float(value)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid value for %s: %s", self._property_key, value)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the number value using HA best practices for responsive UI.
        
        Args:
            value: Value to set
        """
        # Prevent multiple simultaneous API calls
        if self._api_call_in_progress:
            _LOGGER.debug("API call already in progress for %s, ignoring request", self._property_key)
            return
            
        # Validate against cable type limit
        cable_spec = CABLE_TYPES.get(self._cable_type, CABLE_TYPES[DEFAULT_CABLE_TYPE])
        max_current = cable_spec["max_current"]
        
        if value > max_current:
            _LOGGER.warning(
                "Requested current %sA exceeds cable limit %sA for %s",
                value, max_current, cable_spec["name"]
            )
            # Clamp to maximum allowed value
            value = float(max_current)
        
        try:
            self._api_call_in_progress = True
            _LOGGER.debug("Setting %s to %s", self._property_key, value)
            
            # Immediately update the coordinator data for responsive UI
            if self.coordinator.data:
                self.coordinator.data[self._property_key] = value
                self.async_write_ha_state()  # Update UI immediately
            
            # Make API call to set the property
            await self.coordinator.api_client.async_set_property(
                self._property_key, value
            )
            
            # Schedule a coordinator refresh to get the actual state
            # This happens in the background and will correct the value if needed
            self.hass.async_create_task(
                self._async_delayed_refresh()
            )
            
        except IXManagerError as err:
            _LOGGER.error("Failed to set %s to %s: %s", self._property_key, value, err)
            # On error, request immediate refresh to restore correct state
            await self.coordinator.async_request_refresh()
        finally:
            self._api_call_in_progress = False
            
    async def _async_delayed_refresh(self) -> None:
        """Refresh coordinator data after a short delay to verify state."""
        await asyncio.sleep(0.5)  # Give API time to process
        try:
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.debug("Delayed refresh failed: %s", err)
            


class IXManagerChargingCurrentNumber(IXManagerNumberBase):
    """Number entity for setting maximum charging current."""

    _attr_name = "Maximum Charging Current"
    _attr_native_min_value = MIN_CHARGING_CURRENT
    _attr_native_step = CHARGING_CURRENT_STEP
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_icon = "mdi:current-ac"
    _attr_mode = NumberMode.SLIDER
    
    def __init__(
        self,
        coordinator: IXManagerDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the charging current number entity.
        
        Args:
            coordinator: Data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator, entry)
        # Set max value based on cable type
        cable_spec = CABLE_TYPES.get(self._cable_type, CABLE_TYPES[DEFAULT_CABLE_TYPE])
        self._attr_native_max_value = cable_spec["max_current"]
        
        # Update entity name to include cable type info
        self._attr_name = f"Maximum Charging Current ({cable_spec['name']})"
        
        # Initialize state tracking
        self._api_call_in_progress = False

    @property
    def _number_key(self) -> str:
        """Return the number key for unique ID."""
        return "maximum_current"

    @property
    def _property_key(self) -> str:
        """Return the property key for this number entity."""
        return PROPERTY_MAXIMUM_CURRENT