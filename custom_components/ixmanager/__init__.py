from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iXmanager from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Use async_forward_entry_setups instead of async_setup_platforms
    await hass.config_entries.async_forward_entry_setups(entry, ['sensor', 'switch', 'number'])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload iXmanager config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ['sensor', 'switch', 'number'])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
