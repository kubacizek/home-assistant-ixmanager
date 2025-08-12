"""Data update coordinator for iXmanager integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api_client import IXManagerApiClient
from .const import DOMAIN
from .const import PROPERTY_CHARGING_CURRENT
from .const import PROPERTY_CHARGING_CURRENT_L2
from .const import PROPERTY_CHARGING_CURRENT_L3
from .const import PROPERTY_CHARGING_ENABLE
from .const import PROPERTY_CHARGING_STATUS
from .const import PROPERTY_CURRENT_CHARGING_POWER
from .const import PROPERTY_MAXIMUM_CURRENT
from .const import PROPERTY_SIGNAL
from .const import PROPERTY_SINGLE_PHASE
from .const import PROPERTY_TARGET_CURRENT
from .const import PROPERTY_TOTAL_ENERGY
from .const import UPDATE_INTERVAL
from .exceptions import IXManagerConnectionError
from .exceptions import IXManagerError

_LOGGER = logging.getLogger(__name__)


class IXManagerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the iXmanager API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: IXManagerApiClient,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            api_client: API client instance
        """
        self.api_client = api_client
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library.

        Returns:
            Dictionary containing all device properties

        Raises:
            UpdateFailed: If update fails
        """
        try:
            properties_to_fetch = [
                PROPERTY_CHARGING_ENABLE,
                PROPERTY_MAXIMUM_CURRENT,
                PROPERTY_TARGET_CURRENT,
                PROPERTY_CURRENT_CHARGING_POWER,
                PROPERTY_CHARGING_CURRENT,
                PROPERTY_CHARGING_CURRENT_L2,
                PROPERTY_CHARGING_CURRENT_L3,
                PROPERTY_TOTAL_ENERGY,
                PROPERTY_SINGLE_PHASE,
                PROPERTY_SIGNAL,
                PROPERTY_CHARGING_STATUS,
            ]

            data = await self.api_client.async_get_properties(properties_to_fetch)
            _LOGGER.debug("Coordinator updated data: %s", data)
            return data

        except IXManagerConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except IXManagerError as err:
            raise UpdateFailed(f"Invalid response from API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_update_single_property(
        self, property_key: str
    ) -> dict[str, Any] | None:
        """Update a single property for targeted refresh.

        Args:
            property_key: The property to update

        Returns:
            Updated property data or None if failed
        """
        try:
            data = await self.api_client.async_get_properties([property_key])

            if self.data and property_key in data:
                self.data[property_key] = data[property_key]
                _LOGGER.debug(
                    "Single property update for %s: %s",
                    property_key,
                    data[property_key],
                )

            return data

        except Exception as err:
            _LOGGER.warning(
                "Failed to update single property %s: %s", property_key, err
            )
            return None
