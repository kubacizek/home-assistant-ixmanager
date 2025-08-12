"""The iXmanager integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

try:
    from typing import TypeAlias  # Python 3.10+
except ImportError:
    from typing_extensions import TypeAlias  # Python 3.9

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api_client import IXManagerApiClient
from .const import CONF_API_KEY
from .const import CONF_SERIAL_NUMBER
from .const import DOMAIN
from .const import PLATFORMS
from .coordinator import IXManagerDataUpdateCoordinator
from .exceptions import IXManagerConnectionError
from .exceptions import IXManagerError

if TYPE_CHECKING:
    from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

IXManagerConfigEntry: TypeAlias = ConfigEntry[IXManagerDataUpdateCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the iXmanager integration.

    Args:
        hass: Home Assistant instance
        config: Integration configuration

    Returns:
        True if setup was successful
    """
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: IXManagerConfigEntry) -> bool:
    """Set up iXmanager from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to set up

    Returns:
        True if setup was successful

    Raises:
        ConfigEntryNotReady: If setup fails due to connection issues
    """
    api_key = entry.data[CONF_API_KEY]
    controller_id = entry.data[CONF_SERIAL_NUMBER]

    # Create API client
    api_client = IXManagerApiClient(hass, api_key, controller_id)

    # Validate connection
    try:
        await api_client.async_validate_connection()
    except IXManagerConnectionError as err:
        _LOGGER.error("Failed to connect to iXmanager API: %s", err)
        raise ConfigEntryNotReady("Unable to connect to iXmanager API") from err
    except IXManagerError as err:
        _LOGGER.error("Authentication failed: %s", err)
        return False

    # Create coordinator
    coordinator = IXManagerDataUpdateCoordinator(hass, api_client)

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    entry.runtime_data = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: IXManagerConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to unload

    Returns:
        True if unload was successful
    """
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: IXManagerConfigEntry) -> None:
    """Reload config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to reload
    """
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
