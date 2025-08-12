"""Switch platform for iXmanager integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IXManagerConfigEntry
from .const import CONF_SERIAL_NUMBER
from .const import DOMAIN
from .const import PROPERTY_CHARGING_ENABLE
from .const import PROPERTY_SINGLE_PHASE
from .coordinator import IXManagerDataUpdateCoordinator
from .exceptions import IXManagerError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IXManagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up iXmanager switch entities.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator = entry.runtime_data

    entities: list[IXManagerSwitchBase] = [
        IXManagerChargingSwitch(coordinator, entry),
        IXManagerSinglePhaseSwitch(coordinator, entry),
    ]

    async_add_entities(entities)


class IXManagerSwitchBase(
    CoordinatorEntity[IXManagerDataUpdateCoordinator], SwitchEntity
):
    """Base class for iXmanager switches."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IXManagerDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator)
        self._serial_number = entry.data[CONF_SERIAL_NUMBER]
        self._attr_unique_id = f"{self._serial_number}_{self._switch_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
            name=f"iXmanager {self._serial_number}",
            manufacturer="R-EVC",
            model="Wallbox EcoVolter",
            serial_number=self._serial_number,
        )
        self._api_call_in_progress = False
        self._attr_assumed_state = True

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
    def _switch_key(self) -> str:
        """Return the switch key for unique ID.

        Returns:
            Switch key string
        """
        raise NotImplementedError

    @property
    def _property_key(self) -> str:
        """Return the property key for this switch.

        Returns:
            Property key string
        """
        raise NotImplementedError

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on.

        Returns:
            Switch state or None if not available
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
            # Handle boolean values directly
            if isinstance(value, bool):
                return value
            return str(value).lower() == "true"
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on.

        Args:
            **kwargs: Additional arguments
        """
        _LOGGER.debug(
            "%s: Turn ON requested (current state: %s, available: %s)",
            self._property_key,
            self.is_on,
            self.available,
        )
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off.

        Args:
            **kwargs: Additional arguments
        """
        _LOGGER.debug(
            "%s: Turn OFF requested (current state: %s, available: %s)",
            self._property_key,
            self.is_on,
            self.available,
        )
        await self._async_set_state(False)

    async def _async_set_state(self, state: bool) -> None:
        """Set the switch state using HA best practices for assumed state entities.

        Args:
            state: Desired state
        """
        # Prevent multiple simultaneous API calls
        if self._api_call_in_progress:
            _LOGGER.debug(
                "API call already in progress for %s, ignoring request",
                self._property_key,
            )
            return

        try:
            self._api_call_in_progress = True
            _LOGGER.debug("Setting %s to %s", self._property_key, state)

            # For assumed_state entities, we immediately update the state
            # and let the coordinator update correct it later if needed
            if self.coordinator.data:
                self.coordinator.data[self._property_key] = state
                self.async_write_ha_state()  # Update UI immediately

            # Make API call to set the property
            await self.coordinator.api_client.async_set_property(
                self._property_key, state
            )

            # Schedule a coordinator refresh to get the actual state
            # This happens in the background and will correct the state if needed
            self.hass.async_create_task(self._async_delayed_refresh())

        except IXManagerError as err:
            _LOGGER.error("Failed to set %s to %s: %s", self._property_key, state, err)
            # On error, request immediate refresh to restore correct state
            await self.coordinator.async_request_refresh()
        finally:
            self._api_call_in_progress = False

    async def _async_delayed_refresh(self) -> None:
        """Refresh coordinator data after a short delay to verify state."""
        await asyncio.sleep(0.1)  # Give API time to process
        try:
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.debug("Delayed refresh failed: %s", err)


class IXManagerChargingSwitch(IXManagerSwitchBase):
    """Switch for enabling/disabling charging."""

    _attr_name = "Charging Enable"
    _attr_icon = "mdi:ev-station"

    @property
    def _switch_key(self) -> str:
        """Return the switch key for unique ID."""
        return "charging_enable"

    @property
    def _property_key(self) -> str:
        """Return the property key for this switch."""
        return PROPERTY_CHARGING_ENABLE


class IXManagerSinglePhaseSwitch(IXManagerSwitchBase):
    """Switch for enabling/disabling single phase operation."""

    _attr_name = "Single Phase Mode"
    _attr_icon = "mdi:sine-wave"

    @property
    def _switch_key(self) -> str:
        """Return the switch key for unique ID."""
        return "single_phase"

    @property
    def _property_key(self) -> str:
        """Return the property key for this switch."""
        return PROPERTY_SINGLE_PHASE
