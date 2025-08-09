"""API client for iXmanager integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_TIMEOUT, BASE_URL
from .exceptions import IXManagerConnectionError, IXManagerError

_LOGGER = logging.getLogger(__name__)


class IXManagerApiClient:
    """API client for iXmanager wallbox."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        api_key: str, 
        controller_id: str
    ) -> None:
        """Initialize the API client.
        
        Args:
            hass: Home Assistant instance
            api_key: API key for authentication
            controller_id: Device serial number/controller ID
        """
        self._hass = hass
        self._api_key = api_key
        self._controller_id = controller_id
        self._session = async_get_clientsession(hass)

    async def async_get_properties(self, keys: list[str]) -> dict[str, Any]:
        """Get device properties from the API.
        
        Args:
            keys: List of property keys to retrieve
            
        Returns:
            Dictionary containing property data
            
        Raises:
            IXManagerConnectionError: If connection to API fails
            IXManagerError: If API returns an error
        """
        url = f"{BASE_URL}/thing/{self._controller_id}/properties"
        headers = {"X-API-KEY": self._api_key}
        params = {"keys": keys}

        try:
            _LOGGER.debug("Fetching properties: %s", keys)
            async with asyncio.timeout(API_TIMEOUT):
                async with self._session.get(
                    url, headers=headers, params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.debug("Received data: %s", data)
                        return data
                    elif response.status == 401:
                        raise IXManagerError("Invalid API key")
                    elif response.status == 404:
                        raise IXManagerError("Controller not found")
                    else:
                        raise IXManagerError(
                            f"API returned status {response.status}"
                        )

        except asyncio.TimeoutError as err:
            raise IXManagerConnectionError(
                "Timeout connecting to iXmanager API"
            ) from err
        except aiohttp.ClientError as err:
            raise IXManagerConnectionError(
                f"Error connecting to iXmanager API: {err}"
            ) from err

    async def async_set_property(self, key: str, value: Any) -> bool:
        """Set a device property via the API.
        
        Args:
            key: Property key to set
            value: Value to set
            
        Returns:
            True if successful
            
        Raises:
            IXManagerConnectionError: If connection to API fails
            IXManagerError: If API returns an error
        """
        url = f"{BASE_URL}/thing/{self._controller_id}/properties"
        headers = {"X-API-KEY": self._api_key, "Content-Type": "application/json"}
        data = {key: value}

        try:
            _LOGGER.debug("Setting property %s to %s", key, value)
            async with asyncio.timeout(API_TIMEOUT):
                async with self._session.patch(
                    url, headers=headers, json=data
                ) as response:
                    if response.status in (200, 204):
                        _LOGGER.debug("Successfully set property %s", key)
                        return True
                    elif response.status == 401:
                        raise IXManagerError("Invalid API key")
                    elif response.status == 404:
                        raise IXManagerError("Controller or property not found")
                    else:
                        raise IXManagerError(
                            f"API returned status {response.status}"
                        )

        except asyncio.TimeoutError as err:
            raise IXManagerConnectionError(
                "Timeout connecting to iXmanager API"
            ) from err
        except aiohttp.ClientError as err:
            raise IXManagerConnectionError(
                f"Error connecting to iXmanager API: {err}"
            ) from err

    async def async_validate_connection(self) -> bool:
        """Validate the API connection and credentials.
        
        Returns:
            True if connection is valid
            
        Raises:
            IXManagerConnectionError: If connection fails
            IXManagerError: If credentials are invalid
        """
        try:
            await self.async_get_properties(["chargingEnable"])
            return True
        except (IXManagerConnectionError, IXManagerError):
            raise